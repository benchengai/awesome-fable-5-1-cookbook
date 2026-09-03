#!/usr/bin/env python3
"""Cost arithmetic for Claude Fable 5.1 and its neighbors.

Prices come from data/facts.json (never hard-coded). The script answers three
questions:

  1. What does one request cost?                          -> request
  2. What does an N-turn agent loop cost, with and
     without prompt caching?                               -> loop
  3. How much cached context per turn does Fable 5.1
     need before it costs less per turn than Opus 5?       -> breakeven

Run it with no arguments to print the tables used in the README.

Examples:
  python examples/cost_calculator.py
  python examples/cost_calculator.py request --model claude-fable-5-1 --input 20000 --output 2000
  python examples/cost_calculator.py request --model claude-fable-5-1 --cached 200000 --input 2000 --output 1000
  python examples/cost_calculator.py loop --turns 40 --prefix 20000 --new-input 2000 --output 1000
  python examples/cost_calculator.py breakeven --new-input 2000 --output 1000

Standard library only. Python 3.11 or newer.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

FACTS_PATH = Path(__file__).resolve().parent.parent / "data" / "facts.json"
MTOK = 1_000_000


@dataclass(frozen=True)
class Price:
    """Per-million-token prices in USD for one model."""

    model_id: str
    display_name: str
    input: float
    output: float
    cache_write_5m: float
    cache_write_1h: float
    cache_read: float

    def batch(self) -> "Price":
        """Batch API pricing: 50% off every token, cache reads and writes included."""
        return Price(
            self.model_id,
            f"{self.display_name} (batch)",
            self.input / 2,
            self.output / 2,
            self.cache_write_5m / 2,
            self.cache_write_1h / 2,
            self.cache_read / 2,
        )


def load_prices(path: Path = FACTS_PATH) -> dict[str, Price]:
    data = json.loads(path.read_text(encoding="utf-8"))
    prices: dict[str, Price] = {}
    for model_id, model in data["models"].items():
        p = model["pricing_usd_per_mtok"]
        prices[model_id] = Price(
            model_id,
            model["display_name"],
            p["input"],
            p["output"],
            p["cache_write_5m"],
            p["cache_write_1h"],
            p["cache_read"],
        )
    return prices


def request_cost(
    price: Price,
    *,
    uncached_input: int = 0,
    cache_write_5m: int = 0,
    cache_write_1h: int = 0,
    cache_read: int = 0,
    output: int = 0,
) -> float:
    """Cost of one request in USD from the five billed token counts."""
    return (
        uncached_input * price.input
        + cache_write_5m * price.cache_write_5m
        + cache_write_1h * price.cache_write_1h
        + cache_read * price.cache_read
        + output * price.output
    ) / MTOK


@dataclass
class LoopCost:
    total: float
    uncached_input: float
    cache_write: float
    cache_read: float
    output: float
    input_tokens_sent: int


def loop_cost(
    price: Price,
    *,
    prefix: int,
    turns: int,
    new_input: int,
    output: int,
    caching: bool = True,
) -> LoopCost:
    """Cost of an agent loop that resends its whole history every turn.

    Model of the loop:
      turn t (1-indexed) starts with context_before = prefix + (t - 1) * (new_input + output)
      then adds new_input fresh tokens (the tool result) and generates `output` tokens.

    Without caching every turn bills context_before + new_input at the base input price.

    With caching (5-minute TTL, turns start less than 5 minutes apart, one automatic
    breakpoint at the tail):
      turn 1 writes prefix + new_input to the cache;
      turn t >= 2 reads everything sent last turn and writes the previous output
      plus this turn's new input.
    """
    uncached = write = read = out = 0.0
    sent = 0
    for t in range(1, turns + 1):
        context_before = prefix + (t - 1) * (new_input + output)
        sent += context_before + new_input
        out += output * price.output
        if not caching:
            uncached += (context_before + new_input) * price.input
        elif t == 1:
            write += (prefix + new_input) * price.cache_write_5m
        else:
            read += (context_before - output) * price.cache_read
            write += (output + new_input) * price.cache_write_5m
    return LoopCost(
        total=(uncached + write + read + out) / MTOK,
        uncached_input=uncached / MTOK,
        cache_write=write / MTOK,
        cache_read=read / MTOK,
        output=out / MTOK,
        input_tokens_sent=sent,
    )


def per_turn_cost(price: Price, cached: int, new_input: int, output: int, include_writes: bool) -> float:
    """One turn: cached context read from cache, plus the new tail, plus output."""
    if include_writes:
        fixed = (new_input + output) * price.cache_write_5m + output * price.output
    else:
        fixed = new_input * price.input + output * price.output
    return (cached * price.cache_read + fixed) / MTOK


def break_even_cached_tokens(
    a: Price, b: Price, *, new_input: int, output: int, include_writes: bool = False
) -> float | None:
    """Cached tokens per turn at which model a costs the same per turn as model b.

    Simple model (include_writes=False): the new tail is billed at base input.
    Write model (include_writes=True): the new tail (this turn's input and the previous
    turn's output) is written to the cache at the 5-minute rate.
    Returns None when a never catches up (its cache read is not cheaper than b's).
    """
    fixed_a = per_turn_cost(a, 0, new_input, output, include_writes)
    fixed_b = per_turn_cost(b, 0, new_input, output, include_writes)
    delta_read = (b.cache_read - a.cache_read) / MTOK
    if delta_read <= 0:
        return None
    return (fixed_a - fixed_b) / delta_read


def cost_per_success(cost_per_attempt: float, pass_rate: float) -> float:
    """Expected cost per successful task when failures are retried until success."""
    return cost_per_attempt / pass_rate


def usd(x: float) -> str:
    """Two decimals from one dollar up, three below, so per-turn cents stay readable."""
    return f"${x:,.2f}" if x >= 1 else f"${x:.3f}"


def print_price_table(prices: dict[str, Price]) -> None:
    print("Prices, USD per million tokens (data/facts.json)")
    print(f"{'Model':<18}{'Input':>8}{'Output':>8}{'5m write':>10}{'1h write':>10}{'Cache read':>12}")
    for p in prices.values():
        print(f"{p.display_name:<18}{p.input:>8.2f}{p.output:>8.2f}{p.cache_write_5m:>10.2f}{p.cache_write_1h:>10.2f}{p.cache_read:>12.3f}")
    print()


def print_loop_table(prices: dict[str, Price], prefix: int, turns: int, new_input: int, output: int) -> None:
    print(
        f"Agent loop: {turns} turns, {prefix:,}-token prefix, {new_input:,} new input and {output:,} output tokens per turn"
    )
    print(f"{'Model':<18}{'Caching':<10}{'Uncached in':>12}{'Cache write':>12}{'Cache read':>12}{'Output':>10}{'Total':>10}")
    for model_id in ("claude-fable-5-1", "claude-opus-5", "claude-sonnet-5"):
        p = prices[model_id]
        for caching in (False, True):
            c = loop_cost(p, prefix=prefix, turns=turns, new_input=new_input, output=output, caching=caching)
            print(
                f"{p.display_name:<18}{('yes' if caching else 'no'):<10}"
                f"{usd(c.uncached_input):>12}{usd(c.cache_write):>12}{usd(c.cache_read):>12}{usd(c.output):>10}{usd(c.total):>10}"
            )
    total_sent = loop_cost(prices["claude-fable-5-1"], prefix=prefix, turns=turns, new_input=new_input, output=output).input_tokens_sent
    print(f"Input tokens sent over the loop: {total_sent:,} (the same history is resent every turn)")
    print()


def print_breakeven_table(prices: dict[str, Price], new_input: int, output: int) -> None:
    a, b = prices["claude-fable-5-1"], prices["claude-opus-5"]
    simple = break_even_cached_tokens(a, b, new_input=new_input, output=output)
    with_writes = break_even_cached_tokens(a, b, new_input=new_input, output=output, include_writes=True)
    print(f"Break-even, Fable 5.1 vs Opus 5, per turn with {new_input:,} new input and {output:,} output tokens")
    print(f"  new tail billed at base input:        {simple:,.0f} cached tokens per turn")
    print(f"  new tail written to the 5-minute cache: {with_writes:,.0f} cached tokens per turn")
    print()
    print(f"{'Cached tokens/turn':>20}{'Fable 5.1':>12}{'Opus 5':>12}{'Fable vs Opus':>16}")
    for cached in (0, 50_000, 100_000, 140_000, 200_000, 300_000, 600_000, 1_000_000):
        ca = per_turn_cost(a, cached, new_input, output, False)
        cb = per_turn_cost(b, cached, new_input, output, False)
        rel = (ca - cb) / cb
        sign = "+" if rel >= 0 else "-"
        print(f"{cached:>20,}{usd(ca):>12}{usd(cb):>12}{sign + f'{abs(rel):.0%}':>16}")
    print("  (simple model: new tail at base input, every cached token a hit, equal output on both models)")
    print()


def print_success_table() -> None:
    rows = [
        ("Fable 5.1 low", 0.54, 0.886),
        ("Fable 5.1 default", 1.19, 0.921),
        ("Opus 5 low", 0.25, 0.840),
        ("Opus 5 default", 1.01, 0.917),
        ("Sonnet 5 default", 0.84, 0.774),
    ]
    print("SWE-bench Pro subset (Anthropic cost guide): pass rate and cost per solved task as published")
    print(f"{'Setting':<20}{'Pass':>8}{'$/solved':>10}")
    for name, cost, rate in rows:
        print(f"{name:<20}{rate:>8.1%}{usd(cost):>10}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd")

    r = sub.add_parser("request", help="cost of one request")
    r.add_argument("--model", default="claude-fable-5-1")
    r.add_argument("--input", type=int, default=0, help="uncached input tokens")
    r.add_argument("--cached", type=int, default=0, help="cache read tokens")
    r.add_argument("--write-5m", type=int, default=0, help="5-minute cache write tokens")
    r.add_argument("--write-1h", type=int, default=0, help="1-hour cache write tokens")
    r.add_argument("--output", type=int, default=0, help="output tokens")
    r.add_argument("--batch", action="store_true", help="apply the Batch API discount")

    lp = sub.add_parser("loop", help="cost of an N-turn agent loop")
    lp.add_argument("--prefix", type=int, default=20_000)
    lp.add_argument("--turns", type=int, default=40)
    lp.add_argument("--new-input", type=int, default=2_000)
    lp.add_argument("--output", type=int, default=1_000)

    be = sub.add_parser("breakeven", help="cached tokens per turn where Fable 5.1 matches Opus 5")
    be.add_argument("--new-input", type=int, default=2_000)
    be.add_argument("--output", type=int, default=1_000)

    args = parser.parse_args()
    prices = load_prices()

    if args.cmd == "request":
        p = prices[args.model]
        if args.batch:
            p = p.batch()
        cost = request_cost(
            p,
            uncached_input=args.input,
            cache_write_5m=args.write_5m,
            cache_write_1h=args.write_1h,
            cache_read=args.cached,
            output=args.output,
        )
        print(f"{p.display_name}: {usd(cost)}")
    elif args.cmd == "loop":
        print_loop_table(prices, args.prefix, args.turns, args.new_input, args.output)
    elif args.cmd == "breakeven":
        print_breakeven_table(prices, args.new_input, args.output)
    else:
        print_price_table(prices)
        print_loop_table(prices, 20_000, 40, 2_000, 1_000)
        print_breakeven_table(prices, 2_000, 1_000)
        print_success_table()


if __name__ == "__main__":
    main()
