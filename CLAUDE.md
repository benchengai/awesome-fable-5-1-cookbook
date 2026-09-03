# awesome-fable-5-1-cookbook: working conventions

Talk to the maintainer (Ben) in Chinese; keep technical terms in English. Give the next executable step first, with little preamble. Everything committed to this repository is written in English except `README.zh-CN.md` and the Chinese infographic.

## What this repository is

A bilingual, continuously updated practical guide to Claude Fable 5.1 (`claude-fable-5-1`, released 2026-09-01). The selling point is cost. Fable 5.1 costs twice as much per token as Claude Opus 5 and about 1.6 times as much per task. The guide explains when it is still worth it and how to cut the bill.

Tagline, English: "Fable 5.1 costs twice as much per token and 1.6x as much per task. This guide covers when it is still worth it, and how to cut the bill."

Tagline, Chinese: "Fable 5.1 每 token 贵一倍,每任务贵 1.6 倍。这本手册讲它什么时候仍然值得,以及怎么把账单砍下来。"

Never promise that Fable 5.1 ends up cheaper than Opus 5 per task in general. Anthropic's model page says to start with Opus 5 and move to Fable 5.1 only when Opus 5 at higher effort still falls short. Fable 5.1 wins on cost only in specific shapes (chapter 3 names them with numbers).

Public repository: https://github.com/benchengai/awesome-fable-5-1-cookbook. License: MIT, copyright Ben Cheng.

## Release plan

- v0.1, ship within 2 to 3 days of 2026-09-03: infographic, chapters 1 to 3, `examples/cost_calculator.py`, both READMEs, CHANGELOG, LICENSE. Chapters 4 to 6 appear in the README as short placeholders with a target date.
- v0.2 and later: one chapter per day (4, 5, 6), then `effort_selector.py` and `cache_layout.py`. Commit every working session; commit history is part of the product.
- After any new Anthropic model launch or price change: update `data/facts.json` first, then both READMEs and the SVGs, then CHANGELOG and the badge date.

## Chapters (fixed order, identical in both READMEs)

1. Choosing among the five effort levels (decision tree and scenario table)
2. Prompt organization after the 75% cache-read price cut
3. When Fable 5.1 is worth it and when Opus 5 is the better buy (explicit break-even points)
4. Using the 1M context window
5. Migrating from Fable 5
6. Common waste patterns checklist

README top, fixed order: badge row, title, tagline, infographic, TL;DR (five rules, each with a number), fact sheet table, then the chapters.

## Numbers discipline (the most important rule)

- Every recommendation carries a number. Never write "may be faster" or "significantly cheaper" without a figure.
- Every number carries a grade, shown in the README as a tag in brackets or a footnote:
  - `official`: printed on an Anthropic pricing, model, or API documentation page.
  - `measured`: a benchmark or cost measurement published by Anthropic or a named third party. Name the benchmark and the model.
  - `derived`: computed from official or measured numbers. Show the arithmetic.
  - `estimate`: a rule of thumb with no source. State the assumption. Avoid where possible.
- `data/facts.json` is the single source of truth. Every number in either README, in the SVGs, or in `examples/` must exist there with `source`, `verified` date, and `grade`. Change the JSON and the prose together.
- Never write a price, benchmark score, or parameter name from memory. Check the claude-api skill reference or the official page. If it cannot be found, tag it `estimate` and state the assumption.
- Read raw pages, not summaries. On 2026-09-03 a summarizer produced two errors that a raw read caught: the $3.20 to $1.20 caching example is Sonnet 5, not Opus 5; and on Anthropic's internal coding benchmark $2.91 is Fable 5.1 at medium while $8.50 is Opus 5 at default, not the other way round. Use `curl` on the `.md` URL and grep the sentence.
- Third-party numbers carry their disclosure. Artificial Analysis supported Anthropic's pre-release evaluation of Fable 5.1; say so wherever its numbers appear, including the infographic footer.
- Record disagreements between sources in `data/facts.json` under `discrepancies` and pick one canonical value with the reason.

## Fact base (verified 2026-09-03; details, sources, and formulas in data/facts.json)

Official prices, USD per million tokens (platform.claude.com pricing page):

| Model | Input | Output | 5-min cache write | 1-hour cache write | Cache read | Batch input / output |
|---|---|---|---|---|---|---|
| Fable 5.1 `claude-fable-5-1` | 10 | 50 | 12.50 | 20 | 0.25 | 5 / 25 |
| Fable 5 `claude-fable-5` | 10 | 50 | 12.50 | 20 | 1.00 | 5 / 25 |
| Opus 5 `claude-opus-5` | 5 | 25 | 6.25 | 10 | 0.50 | 2.50 / 12.50 |
| Sonnet 5 `claude-sonnet-5` | 2 | 10 | 2.50 | 4 | 0.20 | 1 / 5 |
| Haiku 4.5 `claude-haiku-4-5` | 1 | 5 | 1.25 | 2 | 0.10 | 0.50 / 2.50 |

Other official facts: 1M context (default and maximum) with no long-context premium; 128K max output; five effort levels with `high` as default; adaptive thinking always on (`disabled` and `budget_tokens` return 400); reliable knowledge cutoff June 2026; released 2026-09-01; retirement not before 2027-09-01; 512-token minimum cacheable prefix; 4 breakpoints per request; 20-block lookback; cache lifetime counts from the request start; Batch API 50% off every token including cache reads and writes; no Priority Tier; 30-day data retention required; same tokenizer as Fable 5 (about 30% more tokens than pre-Opus-4.7 tokenizers).

Fable 5 to 5.1 breaking changes: forced `tool_choice` (`any`, `tool`) returns 400; thinking blocks are bound to the producing model; editing earlier turns invalidates thinking blocks (enforced for accounts created on or after 2026-08-31). Additive: per-message effort (beta header `mid-conversation-output-config-2026-07-01`, preserves the cache; Fable 5 returns 400), turn-scoped system messages (`clear_at: "next_user_message"`, beta `mid-conversation-system-clear-at-2026-08-21`), `thinking.display: "updates"` (beta `thinking-display-updates-2026-08-18`).

Launch post (anthropic.com/claude-fable-and-mythos-5-1), Fable 5 to Fable 5.1 at max effort: Terminal-Bench-Science 0.1 24.7% to 52.6% (standard error 3.5 to 4.5 points); Terminal-Bench 4.0 42.0% to 55.8%; CursorBench 3.2.0 70.5% to 73.4%; GDPval-AA v2 1723 to 1853 Elo; OSWorld 2.0 72.9% to 77.9%; Humanity's Last Exam with tools 63.8% to 65.0%. Cost per task by effort, read from the post's embedded chart data (Terminal-Bench-Science, USD per task / score): Fable 5.1 low 11.1 / 26.3, medium 14.9 / 35.7, high 20.3 / 40.0, xhigh 31.8 / 49.5, max 37.9 / 52.6; Fable 5 low 17.1 / 12.3, medium 25.0 / 21.4, high 34.3 / 25.0, xhigh 36.0 / 23.4, max 44.1 / 24.7. Anthropic's indexed cost chart: with Fable 5 at 100, Fable 5.1 costs 75 on a typical workload and 55 on a highly agentic one.

Artificial Analysis (artificialanalysis.ai/articles/claude-fable-5-1; supported Anthropic's pre-release evaluation): Intelligence Index Fable 5.1 max 66, xhigh 65; Opus 5 max 63; Fable 5 max 62. Cost per Index task: Fable 5.1 max $3.76, xhigh $2.72; Fable 5 max $3.14; Opus 5 max $2.34. Fable 5.1 emits about 1.7x Fable 5's output tokens. The cache-read cut saves about $1.40 per task (about $5.16 without it). Terminal-Bench v2.1 91.4%, SciCode 62.0%, tau3-Banking 9 points above Fable 5. Discrepancy: some secondary sources quote $3.69 and "57% more than Opus 5"; this repository uses $3.76 and 1.6x.

Anthropic cost guide (platform.claude.com, "Optimizing for cost and intelligence"), all measured:

- SWE-bench Pro subset (482 problems, not comparable to the public leaderboard), cost per solved task: Fable 5.1 low 88.6% / $0.54; Fable 5.1 default 92.1% / $1.19; Opus 5 low 84.0% / $0.25; Opus 5 default 91.7% / $1.01; Sonnet 5 default 77.4% / $0.84. Opus 5 gives up about 2 points at medium for half the cost and about 8 at low for a quarter. Run low and re-run failures at default: about 93% pass for about $0.45 per task versus 91.7% for $0.93 at default throughout; start at medium: about 94% for about $0.61.
- Fable 5 to Fable 5.1 on SWE-bench Pro: same score for 43% less per solved task, most of it the cache-read price. On DeepResearch Bench II the same upgrade costs 41% more per task at high (79% more at low) for 2 to 3 extra points.
- DeepResearch Bench II: Fable 5.1 low 66% / $4.66, high 65% / $7.12 (medium in between, same score); Opus 5 default 71% / $6.71; Sonnet 5 low 56% / $1.20. Caching: Fable 5.1 $37.94 to $7.12 per task, Sonnet 5 $3.20 to $1.20.
- Internal agentic-coding benchmark: Fable 5.1 medium matched Opus 5 default for about a third of the cost per attempt ($2.91 vs $8.50). Opus 5 executor with a Fable 5.1 advisor: $7.69 per attempt, 3.5 points over Opus 5 alone.
- Chartography: Fable 5.1 low 62.5 / $0.15 per chart; Opus 5 low 49 / $0.38.
- Research benchmarks with Fable 5 (WideSearch, DeepWideSearch, BrowseComp, GDPval): low gives up 1 to 3 points for a third to a half off; medium matches default at 70% to 87% of cost; DeepWideSearch low 4.5 minutes per problem versus 7.9 at default.
- Caching cut agent-loop cost by 2.7x to 5.3x; triage agent bill down 83%, 88% with input trimming; production agent loops read a median 84% of input from cache, the top 10% at 94% or more; below 80% look for a cache breaker.
- Triage session cost: $0.81 with no mid-session changes; $0.95 when an effort change and an added tool rewrote 39,000 and 60,000 cached tokens; $0.75 when the same changes ride on the compaction request.
- Long triage run: pruning stale tool results saved 39%, compaction 32%; context editing saved nothing there and added 74% on the short run.
- Keep-alive on Fable 5.1: resend the previous request with `max_tokens: 0` within 4 minutes of the previous request's start, every 4 minutes, `stream` off; cheaper than the 1-hour TTL while pauses run minutes; the 1-hour TTL wins when pauses approach an hour. With no pauses the 5-minute default cost 15% less than 1-hour on Sonnet 5 and 11% less on Opus 5.
- `max_tokens`: a 16,384 cap ended 15% of Opus 5 attempts and 43% of Fable 5.1's; only 9 of 117 capped Fable attempts still passed; cost per solved task about the same as at 64,000 ($21 vs $22); at 64,000 Fable 5.1 solved 58.5% instead of 36.3%, at 128,000 60.0%; 64,000 covered all but 2 of about 14,000 turns.
- Task budgets on Fable 5.1 (SWE-bench Pro): a generous budget cut cost 44% for about 3 points; the tightest cut 58% for 6 points.
- Output format on the triage agent: one-line answer $0.49 per run, two-line $0.57, memo $1.40 (2.8x, six times the output tokens), all 78% to 85% correct.
- Prompt audit: prompts written for Opus 4.8 cost 36% more per ticket on Opus 5; audited prompts 14% cheaper and more accurate (97% vs 92%).
- Tail: on 20 WideSearch problems the two most expensive carried 43% of spend, the cheapest half 10%.
- Terminal-Bench 3 Opus ladder: $183, $63, $28 per solved task for Opus 4.7, 4.8, 5 (7%, 15%, 41% solved).
- Haiku 4.5 on GPQA Diamond: about a tenth of Opus 5's cost per question, 63% vs 92%.
- The cost guide's own recommendation: "For most agent workloads, start with Claude Fable 5.1 at low effort and raise effort where it misses." The models overview says to start with Opus 5. Quote both; they answer different questions (agent loops with large cached context versus everything else).

Derived numbers used in the README (formulas in data/facts.json): per task, Fable 5.1 max is 1.6x Opus 5 max (3.76 / 2.34 = 1.61) and 20% above Fable 5 max (3.76 / 3.14 = 1.20). Break-even against Opus 5 with 2,000 new input and 1,000 output tokens per turn on top of a cached context: 140,000 cached tokens per turn when new tokens are billed at the base input price (0.035 / 0.25 per million); 175,000 when the new tail is written to cache at 1.25x. At 300,000 cached tokens per turn Fable 5.1 is 22% cheaper, at 600,000 34% cheaper (simple model). Framing credited to Digital Applied; arithmetic reproduced in `examples/cost_calculator.py`.

## Bilingual sync

- `README.md` (English) is the primary version. `README.zh-CN.md` mirrors it section by section with the same numbering, tables, and numbers.
- Change both in the same commit. The Chinese version is written as Chinese, not as a translation; terms and numbers stay identical.
- Each README links to the other at the top.
- Code, comments, JSON keys, and commit messages are English.

## Badges, dates, changelog

- Badge row: last updated (static shields.io badge, date edited by hand), MIT license, "continuously updated", language switch. Add the GitHub last-commit badge once the remote exists.
- Every content change: bump the last-updated date in both READMEs and add a dated CHANGELOG entry with what changed and the source.
- Dates are YYYY-MM-DD.
- The README states near the top that the guide is continuously updated and tracks new model releases, and links to the CHANGELOG.

## Writing style

- Plain, complete sentences. No em-dash rhetoric, no stacked adjectives, no marketing language. The Chinese README follows the same rules.
- Lead with the conclusion and the number, then the explanation. Each chapter opens with one sentence saying which bill it cuts.
- Tables over paragraphs. Decision trees in Mermaid (GitHub renders it in both themes).
- No decorative emoji outside badges.
- Report unfavorable numbers plainly: Fable 5.1 at max costs 20% more per task than Fable 5, and Opus 5 at default is the cheaper way to the top SWE-bench Pro score.

## Infographic

- `assets/cost-comparison.svg` (English) and `assets/cost-comparison.zh-CN.svg` (Chinese), referenced from the READMEs with `<img>`.
- Plain SVG, system font stack, no external fonts or images, fixed light surface so it reads in both GitHub themes.
- 1200 px wide. Three panels: cache-read price, cost per task at max effort, Terminal-Bench-Science score against cost by effort level.
- Colors follow the dataviz skill's reference palette: Fable 5.1 blue `#2a78d6`, Opus 5 orange `#eb6834`, Fable 5 neutral gray `#898781`. Validated with the skill's `validate_palette.js` on 2026-09-03. Text never wears the series color.
- Any number change updates the SVGs and `data/facts.json` together.
- Load the dataviz skill before editing chart code.

## Code examples (`examples/`)

- Python 3.11, standard library only for the calculator; the official `anthropic` SDK for API examples. No hand-written HTTP.
- Exact model IDs: `claude-fable-5-1`, `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5`. No date suffixes.
- No `thinking` parameter on Fable 5.1 (always on). Control depth with `output_config={"effort": ...}`.
- No `tool_choice` of type `any` or `tool`.
- Prices are read from `data/facts.json`, never hard-coded.
- Scripts must run without an API key where possible; API examples must at least pass `python -m py_compile`.

## Files

```
awesome-fable-5-1-cookbook/
├── README.md                  English, primary version, infographic at the top
├── README.zh-CN.md            Chinese, mirrors README.md section by section
├── CLAUDE.md                  this file
├── LICENSE                    MIT, Ben Cheng
├── CHANGELOG.md               dated entries, feeds the last-updated badge
├── assets/
│   ├── cost-comparison.svg
│   └── cost-comparison.zh-CN.svg
├── data/
│   └── facts.json             single source of truth for every number
└── examples/
    ├── cost_calculator.py     request, agent-loop, and break-even arithmetic (v0.1)
    ├── effort_selector.py     the decision tree as code (v0.2 or later)
    └── cache_layout.py        minimal SDK call with correct cache_control placement (v0.2 or later)
```

All six chapters live in the README. Split a chapter into `docs/` only if it passes about 150 lines.

## Environment

- Windows 10, PowerShell or Git Bash. Line endings are normalized to LF by `.gitattributes`.
- Python: conda environment `LLMPython311` (`C:\Users\Admin\anaconda3\envs\LLMPython311\python.exe`). Install `anthropic` before running API examples.
- Git identity for this repository: Ben Cheng <ben546070853@gmail.com>, branch `main`. No remote yet.

## Open items

- [ ] Add the source URL for the Claude Pro subscription note (Fable 5.1 costs extra on Pro; Opus 5 is the strongest model included). Until then it is tagged `estimate` in the README.
- [ ] Add the Digital Applied URL to `data/facts.json`.
- [ ] Create the GitHub remote and push; then add the last-commit badge.
