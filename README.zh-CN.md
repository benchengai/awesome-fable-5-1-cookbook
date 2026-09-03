[![Last updated](https://img.shields.io/badge/last%20updated-2026--09--03-2a78d6)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-1baf7a)](LICENSE)
[![Continuously updated](https://img.shields.io/badge/status-continuously%20updated-eb6834)](CHANGELOG.md)
[![English](https://img.shields.io/badge/README-English-0b0b0b)](README.md)

# Awesome Fable 5.1 Cookbook

Fable 5.1 每 token 贵一倍,每任务贵 1.6 倍。这本手册讲它什么时候仍然值得,以及怎么把账单砍下来。

[English README](README.md)

<img src="assets/cost-comparison.zh-CN.svg" alt="三个面板:Fable 5.1 缓存读取每百万 token $0.25,Fable 5 是 $1.00,Opus 5 是 $0.50;max effort 下每任务成本 Opus 5 $2.34、Fable 5 $3.14、Fable 5.1 $3.76、xhigh $2.72;Terminal-Bench-Science 上 Fable 5.1 low 得分 26.3% 每任务 $11.1,Fable 5 max 得分 24.7% 每任务 $44.1。" width="100%">

本手册持续更新。新模型发布和定价变化会跟进收录,见 [CHANGELOG](CHANGELOG.md)。每个数字都标注来源等级:**official**(Anthropic 定价页或文档页原文)、**measured**(Anthropic 或具名第三方公布的 benchmark 或成本测量)、**derived**(由前两类算出,附算式)、**estimate**(有假设、无来源)。所有数字、来源和算式都在 [`data/facts.json`](data/facts.json)。价格单位是美元/百万 token(MTok),2026-09-03 核对。

## 目录

- [TL;DR:五条规则](#tldr五条规则)
- [参数速查](#参数速查)
- [1. 五档 effort 怎么选](#1-五档-effort-怎么选)
- [2. 缓存降价 75% 后的 prompt 组织](#2-缓存降价-75-后的-prompt-组织)
- [3. Fable 5.1 还是 Opus 5:临界点在哪](#3-fable-51-还是-opus-5临界点在哪)
- [4. 1M 上下文的实际用法](#4-1m-上下文的实际用法)(v0.2)
- [5. 从 Fable 5 迁移](#5-从-fable-5-迁移)(v0.2)
- [6. 常见浪费模式 checklist](#6-常见浪费模式-checklist)(v0.2)
- [更新策略与贡献](#更新策略与贡献)

## TL;DR:五条规则

1. **agent loop 从 `low` 起步,不要用默认档。** Anthropic 的 SWE-bench Pro 子集上,Fable 5.1 的 `low` 解决 88.6% 的任务,每个解决任务 $0.54;默认档(`high`)解决 92.1%,每个 $1.19。eval 哪里失手再往上调。(measured)
2. **重复的内容全部缓存,然后验证命中率。** Fable 5.1 缓存读取每 MTok $0.25,未缓存 $10。缓存把 Anthropic 的 agent loop 成本降为 1/2.7 到 1/5.3;生产环境的 loop 中位数有 84% 的输入来自缓存。低于 80% 说明有东西在破坏缓存。(official, measured)
3. **Fable 5.1 只在缓存上下文占主体时比 Opus 5 便宜。** 每轮 2,000 新输入加 1,000 输出 token 的条件下,两个模型在每轮约 140,000 缓存 token 处持平。低于这个数 Opus 5 每轮更便宜;缓存 token 到 600,000 时 Fable 5.1 便宜 34%。(derived)
4. **新模型的低档位打赢旧模型的最高档位。** Terminal-Bench-Science 上,Fable 5.1 的 `low` 得 26.3%,每任务 $11.1;Fable 5 的 `max` 得 24.7%,每任务 $44.1。只有实测曲线过了 `xhigh` 还在往上走时才用 `max`。(measured)
5. **不要靠压低 `max_tokens` 省钱。** 内部 coding benchmark 上,16,384 的上限截断了 Fable 5.1 43% 的尝试,每个解决任务的成本没变(16K 是 $21,64K 是 $22)。省钱靠 `effort` 和 task budget,这两个模型看得见。(measured)

## 参数速查

| 项目 | Claude Fable 5.1 | 来源 |
|---|---|---|
| API 模型 ID | `claude-fable-5-1` | official |
| 发布日期 | 2026-09-01 | official |
| 价格,输入 / 输出 | $10 / $50 每 MTok | official |
| 价格,缓存写入 5 分钟 / 1 小时 | $12.50 / $20 每 MTok | official |
| 价格,缓存读取 | $0.25 每 MTok(输入价的 0.025 倍;其他模型都是 0.1 倍) | official |
| 价格,Batch API | $5 / $25 每 MTok,所有 token 半价,含缓存读写 | official |
| 上下文窗口 | 1M token,默认即最大,无长上下文加价 | official |
| 最大输出 | 128K token(超过 16K 要用 streaming) | official |
| effort 档位 | `low`、`medium`、`high`(默认)、`xhigh`、`max` | official |
| Thinking | 自适应,常驻。`thinking.type: "disabled"` 和 `budget_tokens` 都返回 400 | official |
| 可靠知识截止 | 2026 年 6 月 | official |
| 最小可缓存前缀 | 512 token | official |
| 退役 | 不早于 2027-09-01 | official |
| 数据保留 | 要求 30 天保留;零保留(ZDR)组织收到 400 | official |
| Intelligence Index 每任务成本,`max` | $3.76(Opus 5 $2.34;Fable 5 $3.14) | measured,Artificial Analysis |
| 发布 benchmark,Fable 5 到 5.1,`max` | Terminal-Bench-Science 24.7% 到 52.6%;Terminal-Bench 4.0 42.0% 到 55.8%;CursorBench 70.5% 到 73.4%;GDPval-AA 1723 到 1853 Elo | measured,Anthropic 发布文 |

## 1. 五档 effort 怎么选

这一章砍的是你直接能控制的最大一笔:输出 token,effort 直接决定它的量。Artificial Analysis 跑完整个 Intelligence Index,Fable 5.1 在 `low` 下输出 13.1M token,在 `max` 下输出 143.7M,同样的任务差 11 倍。(measured)

### 1.1 每一档是干什么的

effort 作用于全部输出 token:正文、tool call 及其参数、thinking。低档位的 tool call 也更少更简。`high` 是默认值,和不传参数完全一样。(official)

| 档位 | Anthropic 的定义 | 注意 |
|---|---|---|
| `low` | 需要最快速度和最低成本的简单任务,例如 subagent | Fable 5.1 在 `low` 下更常凭记忆作答,搜索工具调得更少;需要新数据的轮次加一句核实指令 |
| `medium` | 需要平衡速度、成本和效果的 agentic 任务 | eval 证明质量守得住之后的降本档 |
| `high` | 复杂推理、难 coding、agentic 任务。默认值 | `max_tokens` 要设大,它同时限制 thinking 和正文 |
| `xhigh` | 30 分钟以上、token 预算百万级的长 agentic 和 coding 任务 | token 用量明显高于 `high` |
| `max` | 最深推理,不限制 token 消耗 | 多数工作负载上加价换来的提升很小;结构化任务上可能过度思考 |

来源:Anthropic effort 文档。(official)

### 1.2 每一档的实测成本

发布文的图表画了四个 benchmark 上每一档的位置。下面的数据点取自那张图的嵌入数据:每任务平均成本(美元)和得分。(measured)

| effort | Terminal-Bench-Science 0.1 | Terminal-Bench 4.0 | CursorBench 3.2.0 | Humanity's Last Exam,带工具 |
|---|---|---|---|---|
| `low` | 26.3%,$11.1 | 40.2%,$5.7 | 66.2,$2.90 | 60.0,$0.52 |
| `medium` | 35.7%,$14.9 | 43.4%,$7.8 | 68.0,$3.53 | 63.0,$0.67 |
| `high` | 40.0%,$20.3 | 49.4%,$10.5 | 69.4,$4.80 | 64.8,$1.05 |
| `xhigh` | 49.5%,$31.8 | 51.3%,$15.8 | 72.8,$6.96 | 65.1,$2.28 |
| `max` | 52.6%,$37.9 | 55.8%,$19.5 | 73.4,$9.64 | 65.0,$3.20 |

怎么读(由上表推算):

- 从 `low` 到 `max`,成本在 Terminal-Bench-Science 上乘 3.4,Terminal-Bench 4.0 上乘 3.4,CursorBench 上乘 3.3,Humanity's Last Exam 上乘 6.2。
- 换来的分数相差一个数量级:Terminal-Bench-Science 26 分,Terminal-Bench 4.0 16 分,CursorBench 7 分,Humanity's Last Exam 5 分,而且后者 `high` 以上是平的,`max` 比 `xhigh` 低 0.1 分还贵 40%。
- Terminal-Bench-Science 每个模型的标准误差是 3.5 到 4.5 分,所以 `xhigh` 以下相邻两档的差距在噪声里;`low` 到 `max` 的差距不在。

Anthropic 成本指南里是同样的形状(measured):DeepResearch Bench II 上,Fable 5.1 在 `low`、`medium`、`high` 得分几乎一样,每任务成本却从 $4.66 涨到 $7.12。Fable 5 在四个 research benchmark 上,`low` 少 1 到 3 分,每任务省三分之一到一半;`medium` 和默认档准确率一样,成本是它的 70% 到 87%。长程 coding 是例外:SWE-bench Pro 上 Opus 5 用 `medium` 少约 2 分省一半,用 `low` 少约 8 分省四分之三。

### 1.3 决策树

```mermaid
flowchart TD
    A["Fable 5.1 上的新工作负载"] --> B{"有测试、校验器或 schema 能检查输出吗?"}
    B -- "有" --> C["全部跑 low。<br/>只把失败的用 high 重跑。"]
    B -- "没有" --> D{"是跑很多分钟的<br/>长程 agent 或 coding 任务吗?"}
    D -- "是" --> E["从默认档 high 起步。<br/>eval 还有余量再试 xhigh。"]
    D -- "不是" --> F{"研究、抽取、聊天、<br/>读图表或文档?"}
    F -- "是" --> G["从 low 或 medium 起步。<br/>实测的研究曲线几乎是平的。"]
    F -- "不是" --> H["从 high 起步。<br/>用 20 到 30 条真实请求测过再动。"]
    C --> I["max:只在实测曲线<br/>过了 xhigh 还在涨时用"]
    E --> I
    H --> I
```

### 1.4 场景对照表

| 场景 | 起步档位 | 依据 |
|---|---|---|
| subagent 做限定范围的查找或批量读取 | `low` | Anthropic 把 subagent 列为 `low` 的用例;低档位的 tool call 更少更简(official) |
| 分类、抽取、带 schema 的打标 | `low`,配 `strict: true` 的工具或 structured outputs | 研究和知识工作的曲线几乎是平的:`low` 省三分之一到一半,只少 1 到 3 分(measured,Fable 5) |
| 延迟敏感的聊天 | `low` | DeepWideSearch 上 `low` 每题 4.5 分钟,默认档 7.9 分钟(measured,Fable 5) |
| 读图表或文档 | `low` | Chartography:Fable 5.1 `low` 得 62.5,每图 $0.15;Opus 5 `low` 得 49,每图 $0.38(measured) |
| 深度研究报告 | `low` | DeepResearch Bench II:`low` 66% 花 $4.66,`high` 65% 花 $7.12(measured) |
| 有测试能判分的 coding | `low`,失败的用 `high` 重跑 | Opus 5 在 SWE-bench Pro 上:约 93% 通过,每任务约 $0.45;全程默认档 91.7%,$0.93(measured) |
| 没有自动检查的 coding | `high` | SWE-bench Pro:Fable 5.1 默认档 92.1% 花 $1.19,`low` 88.6% 花 $0.54;那 3.5 分要花 2.2 倍(measured) |
| 30 分钟以上的长 agent loop | `high`,eval 有余量再 `xhigh` | Terminal-Bench 4.0:`high` 49.4% 花 $10.5,`xhigh` 51.3% 花 $15.8,`max` 55.8% 花 $19.5(measured) |
| 每一分都要的 agentic 科研 | `xhigh` 或 `max` | Terminal-Bench-Science:`xhigh` 49.5% 花 $31.8,`max` 52.6% 花 $37.9,多 3.1 分贵 19%(measured) |
| 跨 session 的多文件重构或迁移 | `high` | Anthropic 说明 Fable 5 到 5.1 的提升集中在长程 agentic coding,且档位越高差距越大(official) |
| eval 评审或打分 | `low` 或 `medium` | 可检查的结构化输出;上面的研究曲线适用 |
| 任何要跑 10,000 次的 prompt | 先做 sweep | Anthropic 的做法:20 到 30 条真实请求,每次只换一档,成本和分数并排记(official) |

### 1.5 反直觉的结果:新模型的 `low` 打赢旧模型的 `max`

Terminal-Bench-Science 上,Fable 5.1 的 `low` 得 26.3%,每任务 $11.1;Fable 5 的 `max` 得 24.7%,每任务 $44.1:分数更高,成本是 25%(measured;比值 11.1 / 44.1 = 0.25 为 derived)。分数差在 benchmark 的误差范围内,成本差不在。

低一级也是同样的规律。SWE-bench Pro 上 Opus 5 的 `low` 打赢 Opus 4.8 的默认档,每个解决任务的成本约为其 30%;Fable 5.1 和 Fable 5 在 SWE-bench Pro 上分数持平,每个解决任务便宜 43%,大头来自缓存读取降价(measured)。最便宜的升级路径通常是新模型加低档位,不是旧模型加高档位。

这不是定律。DeepResearch Bench II 上,Fable 5 换 5.1 在 `high` 下每任务贵 41%,在 `low` 下贵 79%,只多 2 到 3 分,因为新模型的研究循环跑得更长(measured)。先在自己的工作负载上量过,再假设升级会省钱。

### 1.6 先跑 `low`,失败的用 `high` 重跑

只要任务有可用的失败信号,最便宜的策略就不是固定某一档。Anthropic 用 Opus 5 在 SWE-bench Pro 上逐题算过(measured):

| 策略 | 通过率 | 每任务成本 |
|---|---|---|
| 全程默认档(`high`) | 91.7% | $0.93 |
| 全程 `low`,失败的用默认档重跑 | 约 93% | 约 $0.45 |
| 全程 `medium`,失败的用默认档重跑 | 约 94% | 约 $0.61 |

$0.45 已经算进了失败的廉价尝试。这个策略是用来省钱的,不是用来提分的:把默认档自己的失败再用默认档跑一遍,分数差不多,钱更多。要预留检查器的成本,以及首轮失败的那 16% 任务翻倍的墙上时间。

### 1.7 在一段对话中途改 effort

在两次请求之间改顶层 `effort` 会让 prompt 缓存从那一点起失效,而且 Fable 5.1 会因为前面的回复是在旧档位下写的而不太听从新档位(official)。Anthropic 在 triage agent 上量过缓存代价:没有中途改动的 session 花 $0.81;中途改了一次 effort 又加了一个工具的同一 session 花 $0.95,因为这两处改动重写了 39,000 和 60,000 个缓存 token(measured)。

Fable 5.1 和 Opus 5 支持逐消息改 effort,缓存不失效(beta header `mid-conversation-output-config-2026-07-01`)。加一条 `system` 消息,内容为空,带上新档位,从下一个 user 轮次起生效。Fable 5 对此返回 400(official)。

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-fable-5-1",
    max_tokens=16000,
    output_config={"effort": "high"},
    messages=[
        {"role": "user", "content": "分三步规划这次迁移。"},
        {"role": "assistant", "content": "1. 导出。2. 建 schema。3. 导入并核对行数。"},
        # 只带 effort 的 system 消息:从下一个 user 轮次起生效,缓存保持有效。
        {"role": "system", "content": [], "output_config": {"effort": "low"}},
        {"role": "user", "content": "把方案总结成一句话。"},
    ],
    betas=["mid-conversation-output-config-2026-07-01"],
)
```

### 1.8 三个不是 effort 的旋钮

- **`max_tokens` 是模型看不见的安全上限。** 内部仓库任务 benchmark 上,16,384 的上限截断了 Opus 5 15% 的尝试和 Fable 5.1 43% 的尝试;被截断的 117 次 Fable 尝试只有 9 次仍然通过,每个解决任务的成本和 64,000 时差不多($21 对 $22)。64,000 时 Fable 5.1 解决 58.5% 而不是 36.3%;128,000 时 60.0%(measured)。agentic 工作设 64,000,`xhigh` 或 `max` 设 128,000,用 streaming,把 `stop_reason: "max_tokens"` 当作失败的尝试。
- **task budget 才是能省钱的预算控制**,因为模型看得见倒计时。SWE-bench Pro 上 Fable 5.1 用宽松预算每任务省 44%,通过率少约 3 分;最紧的预算省 58%,少 6 分(measured,beta `task-budgets-2026-03-13`,下限 20,000 token,首次请求设一次)。
- **要你会读的那种答案。** triage agent 上,一行式答案每次 $0.49,原来的两行式 $0.57,备忘录式 $1.40,输出 token 是六倍。三种格式的正确率都在 78% 到 85%(measured)。

## 2. 缓存降价 75% 后的 prompt 组织

这一章砍的是 agent loop 账单上最大的一笔。生产环境的 agent loop 中位数有 84% 的输入来自缓存,而 Fable 5.1 上这些读取现在每 MTok $0.25,不再是 $1.00。(measured, official)

### 2.1 相关价格

| 操作 | Fable 5.1 | Fable 5 | Opus 5 | 相对基础输入价的倍率 |
|---|---|---|---|---|
| 未缓存输入 | $10.00 | $10.00 | $5.00 | 1 倍 |
| 缓存写入,5 分钟 TTL | $12.50 | $12.50 | $6.25 | 1.25 倍 |
| 缓存写入,1 小时 TTL | $20.00 | $20.00 | $10.00 | 2 倍 |
| 缓存读取(命中或刷新) | $0.25 | $1.00 | $0.50 | Fable 5.1 为 0.025 倍,其他 0.1 倍 |
| 输出 | $50.00 | $50.00 | $25.00 | |
| Batch API | 以上每一行半价,含缓存读写 | 同 | 同 | |

来源:Anthropic 定价页。(official)

### 2.2 降价改变了什么

- **回本是即时的。** Fable 5.1 上一条 5 分钟缓存写一次 1.25 倍,读一次 0.025 倍,合计 1.275 倍,对比不缓存发两次的 2 倍,所以第一次读取就回本。1 小时缓存(2 倍加 0.05 倍)第二次读取回本。(derived)
- **整张账单在动。** Fable 5.1 在 SWE-bench Pro 上和 Fable 5 分数持平,每个解决任务便宜 43%,大头是缓存读取价。Anthropic 的发布图以 Fable 5 为 100,典型工作负载 Fable 5.1 是 75,高度 agentic 的是 55。Artificial Analysis 算出每个 Intelligence Index 任务省约 $1.40,从约 $5.16 降到 $3.76。(measured)
- **旧账单里缓存读取占大头。** 把发布图倒过来读,Fable 5 上缓存读取约占典型工作负载成本的 44%,高度 agentic 工作负载的 68%(derived:Fable 5.1 的读取条 11 和 17 个指数点是旧价的四分之一)。
- **未命中相对更贵了。** 现在一个未缓存 token 等于 40 个缓存 token 的价钱,以前是 10 个,所以 2.6 节里每一种静默破坏缓存的方式,伤害是 Fable 5 时代的四倍。(derived)

### 2.3 一个算例

`examples/cost_calculator.py` 给一个每轮重发全部历史的 loop 算账:20,000 token 的前缀(system prompt、工具、参考资料),40 轮,每轮 2,000 个新输入 token(工具结果)和 1,000 个输出 token。整个过程发送 3,220,000 个输入 token(derived;假设写在脚本里)。

| 模型 | 缓存 | 未缓存输入 | 缓存写入 | 缓存读取 | 输出 | 合计 |
|---|---|---|---|---|---|---|
| Fable 5.1 | 无 | $32.20 | | | $2.00 | $34.20 |
| Fable 5.1 | 有 | | $1.74 | $0.77 | $2.00 | $4.51 |
| Opus 5 | 无 | $16.10 | | | $1.00 | $17.10 |
| Opus 5 | 有 | | $0.87 | $1.54 | $1.00 | $3.41 |
| Sonnet 5 | 无 | $6.44 | | | $0.40 | $6.84 |
| Sonnet 5 | 有 | | $0.35 | $0.62 | $0.40 | $1.36 |

两点值得注意。缓存把这个 loop 在 Fable 5.1 上降为 1/7.6;Anthropic 在真实 benchmark 上量到的是 1/2.7 到 1/5.3,因为工具结果和输出更大。开了缓存之后,Fable 5.1 最大的一笔是输出($4.51 里的 $2.00),Opus 5 最大的一笔是缓存读取($3.41 里的 $1.54)。这就是为什么 effort 在 Fable 5.1 上更重要,也是两个模型随缓存上下文增长而交叉的原因(第 3 章)。

```bash
python examples/cost_calculator.py loop --prefix 20000 --turns 40 --new-input 2000 --output 1000
```

### 2.4 排列规则

缓存是对请求按顺序做字节级前缀匹配:先 `tools`,再 `system`,再 `messages`。任何改动都让它之后的部分失效。(official)

1. **稳定内容在前,易变内容在后。** 冻结的 system prompt、顺序固定的工具列表、参考文档;然后是对话;最后是每次请求都不同的材料(检索结果、问题、任何带时间戳的东西)。
2. **静态前缀末尾放一个显式断点,尾部用自动缓存。** 显式标记保证昂贵的共享部分无论 `messages` 后面发生什么都有一个读取点;顶层的 `cache_control` 字段随对话增长往前推断点。这是 agent loop 最稳的写法。
3. **遵守硬限制。** Fable 5.1 最小可缓存前缀 512 token(更短的前缀静默不缓存);每次请求最多 4 个断点;系统从每个断点往回看 20 个 block,所以一轮追加很多 block 时要加第二个断点才能找到上一条缓存(official)。
4. **多段对话共享一个前缀时必须用显式标记。** 自动缓存只在一段对话内摊销;一队共享 system prompt 的独立任务,只有共享部分自带断点才能读回来。

```python
import anthropic

client = anthropic.Anthropic()

with client.messages.stream(
    model="claude-fable-5-1",
    max_tokens=64000,
    output_config={"effort": "low"},
    tools=TOOLS,  # 每次请求都是同一个列表、同一个顺序
    system=[
        {"type": "text", "text": SYSTEM_PROMPT},
        {"type": "text", "text": REFERENCE_DOCS, "cache_control": {"type": "ephemeral"}},
    ],
    messages=history + [{"role": "user", "content": new_tool_result_or_question}],
    cache_control={"type": "ephemeral"},  # 跟着尾部走的自动断点
) as stream:
    response = stream.get_final_message()

u = response.usage
print(u.cache_read_input_tokens, u.cache_creation_input_tokens, u.input_tokens)
```

### 2.5 TTL 和保活

缓存寿命从写入或读取它的那次请求开始算,生成时间也算在内:一次 4 分钟的响应之后,下一次请求要在大约 1 分钟内开始,5 分钟的缓存才不会过期。(official)

| 共享前缀的两次请求的起始间隔 | Fable 5.1 的选择 | 原因 |
|---|---|---|
| 5 分钟以内(连续 loop) | 5 分钟 TTL | 每次请求都刷新它;没有停顿时,5 分钟默认档比 1 小时 TTL 在 Sonnet 5 上便宜 15%,在 Opus 5 上便宜 11%(measured) |
| 几分钟到几十分钟(用户过一会儿再回复,或一次很长的生成) | 5 分钟 TTL 加保活 | 在上一次请求开始后 4 分钟内、之后每 4 分钟,把上一次请求原样再发一遍,`max_tokens: 0`,关掉 `stream`;只计一次便宜的缓存读取,并刷新计时。Anthropic 实测在 Fable 5.1 上,停顿以分钟计时这比 1 小时 TTL 便宜(measured) |
| 停顿接近一小时 | 1 小时 TTL | 只有保活要持续大半个小时时,1 小时的写入加价才成为更小的一笔(measured) |
| 超过一小时 | 都不用;接受未命中,或按计划预热 | |

保活背后的算术(derived):200,000 token 的前缀,一次保活读取花 200,000 x $0.25 / 1M = $0.05;1 小时 TTL 让每次写入每 MTok 多花 $7.50,这个前缀就是 $1.50。十五次保活覆盖一小时,花 $0.75。保活不能和 structured outputs 一起用,也不能走 Batch API;那两种情况用 1 小时 TTL。

### 2.6 静默破坏缓存的东西

下面每一条都会让 `cache_read_input_tokens` 变成 0,而且没有报错(official,出自 prompt caching 文档):

- system prompt 里或断点之前出现时间戳、日期、请求 ID、用户名
- 工具列表在两次请求之间变了,或序列化顺序变了
- 渲染进前缀的 JSON 或字典没有排序
- 两次请求之间改了顶层 `effort` 或 thinking 配置(用 1.7 节的逐消息写法)
- 对话中途换模型:缓存按模型、按 workspace 隔离
- 首次请求之后改 task budget
- 每一次 context editing,都会从清除点起重写前缀
- 前缀不足 512 token
- 每次请求都不同的内容放在静态块上面而不是下面

破坏一次的代价(measured):triage agent 上,中途改一次 effort 加一个工具,session 从 $0.81 涨到 $0.95。同样的改动放在 compaction 之后的第一次请求上只花 $0.75,因为那次重写搭上了本来就要发生的重写。

### 2.7 用 `usage` 验证,不要靠看代码

一个健康的、已经预热的 loop,`cache_read_input_tokens` 远高于 `input_tokens`,`cache_creation_input_tokens` 大约是一轮的量,不是整段对话。生产环境的 agent loop 中位数 84% 的输入来自缓存;前 10% 达到 94% 以上;低于约 80% 就去找破坏点(measured)。最便宜的检查是探针:同一条有代表性的请求字节相同地发两次,第二次响应的 `cache_read_input_tokens` 为 0 就让构建失败。

### 2.8 Batch 和缓存叠加

Batch API 让每个 token 都半价,含缓存读写(official)。Fable 5.1 走 batch 端点时缓存读取每 MTok $0.125,batch 输入和输出是 $5 和 $25(derived, official)。结果在 24 小时内返回,请求是单发的,所以适合 eval、回填和定时任务,不适合面向用户的 loop。DeepResearch Bench II 上光靠缓存就把 Fable 5.1 从每任务 $37.94 降到 $7.12(measured);离线跑再叠 batch 折扣还能减半。

## 3. Fable 5.1 还是 Opus 5:临界点在哪

这一章决定账单上最大的一笔:用哪个模型。Anthropic 自己的文档指向两个方向,价格表能解释为什么两个都对。

### 3.1 两个官方立场

- 模型总览页:大多数工作负载从 Claude Opus 5 起步;Fable 5.1 用于高要求推理和长程 agentic 工作,或者 Opus 5 在更高 effort 下 eval 仍不达标的时候。(official)
- 成本指南:"对大多数 agent 工作负载,从 Claude Fable 5.1 的 `low` effort 起步,哪里失手再往上调。每 token 它的未缓存输入是 Claude Opus 5 的两倍,缓存输入却只有一半($0.25 对 $0.50 每百万),而在 agent loop 里缓存输入是最大的一项。"(official)

第一条讲能力,适用于一切。第二条讲一种特定的账单形状:每轮都重读一大段缓存前缀的 loop。3.3 节给出区分两者的那个数字。

### 3.2 价格表

| 每 MTok | Fable 5.1 | Opus 5 | Fable 5.1 / Opus 5 |
|---|---|---|---|
| 输入,未缓存 | $10.00 | $5.00 | 2 倍 |
| 输出 | $50.00 | $25.00 | 2 倍 |
| 缓存写入,5 分钟 | $12.50 | $6.25 | 2 倍 |
| 缓存写入,1 小时 | $20.00 | $10.00 | 2 倍 |
| 缓存读取 | $0.25 | $0.50 | 0.5 倍 |
| Batch 输入 / 输出 | $5 / $25 | $2.50 / $12.50 | 2 倍 |

来源:Anthropic 定价页(official);比值为 derived。

### 3.3 缓存读取的价格倒挂

表里有一行是反着的。Fable 5.1 的缓存读取只有 Opus 5 的一半,而长 agent loop 里缓存输入是大部分 token。所以两个模型的每轮成本会随缓存上下文的增长交叉。

每轮在 C 个缓存 token(C 以百万计)之上加 2,000 个新输入 token 和 1,000 个输出 token,按标价(derived):

- Fable 5.1:0.25 x C + 2,000 x $10 / 1M + 1,000 x $50 / 1M = 0.25C + $0.070
- Opus 5:0.50 x C + 2,000 x $5 / 1M + 1,000 x $25 / 1M = 0.50C + $0.035
- 相等于 C = 0.035 / 0.25 = 0.14M,即**每轮约 140,000 个缓存 token**

| 每轮缓存 token | Fable 5.1 每轮 | Opus 5 每轮 | Fable 5.1 相对 Opus 5 |
|---|---|---|---|
| 0 | $0.070 | $0.035 | +100% |
| 50,000 | $0.083 | $0.060 | +38% |
| 100,000 | $0.095 | $0.085 | +12% |
| 140,000 | $0.105 | $0.105 | 0% |
| 200,000 | $0.120 | $0.135 | -11% |
| 300,000 | $0.145 | $0.185 | -22% |
| 600,000 | $0.220 | $0.335 | -34% |
| 1,000,000 | $0.320 | $0.535 | -40% |

三个假设,都偏向 Fable 5.1:每个缓存 token 都命中,新尾部按基础输入价计费而不是写入缓存,两个模型输出一样多。把尾部写进 5 分钟缓存,临界点移到约 175,000(derived;算式在 `data/facts.json`)。而且 Fable 5.1 每个任务往往干更多活:Intelligence Index 上它的输出 token 约是 Fable 5 的 1.7 倍,DeepResearch Bench II 上它默认档比 Opus 5 默认档更贵、分更低(measured)。把 140,000 当作 Fable 5.1 有可能赢的区间的下限,不是保证。临界点的框架来自 Digital Applied 的测算;这里的算术按 Anthropic 标价重算。

```bash
python examples/cost_calculator.py breakeven --new-input 2000 --output 1000
```

### 3.4 每任务成本,整套平均

Artificial Analysis 给 Intelligence Index 的每次运行按任务计价(measured,第三方;Artificial Analysis 参与了 Anthropic 对该模型的发布前评估):

| 模型和 effort | Intelligence Index | 每任务成本 |
|---|---|---|
| Opus 5,`max` | 63 | $2.34 |
| Fable 5,`max` | 62 | $3.14 |
| Fable 5.1,`xhigh` | 65 | $2.72 |
| Fable 5.1,`max` | 66 | $3.76 |

Fable 5.1 的 `max` 是 Opus 5 的 1.6 倍(3.76 / 2.34 = 1.61),比 Fable 5 贵 20%(3.76 / 3.14 = 1.20),因为每 token 价格相同而输出 token 约是 1.7 倍(derived, measured)。降一档到 `xhigh` 少 1 个指数点,每任务省 $1.04。有些二手来源报 $3.69 并算出"比 Opus 5 贵 57%";本手册以 Artificial Analysis 原文的 $3.76 为准。

### 3.5 每个解决任务的成本,逐个 benchmark

价目表按 token 算,你付的是完成的任务。Anthropic 按客户实际计费方式给自己的运行定价(measured):

| Benchmark | Fable 5.1 | Opus 5 | 按结果算谁便宜 |
|---|---|---|---|
| SWE-bench Pro 子集,每个解决任务 | `low` 88.6% 花 $0.54;默认档 92.1% 花 $1.19 | `low` 84.0% 花 $0.25;默认档 91.7% 花 $1.01 | 冲最高分 Opus 5 默认档更便宜(少 15%);要 88% 的话 Fable 5.1 的 `low` 更便宜 |
| 内部 agentic coding benchmark,每次尝试 | `medium` $2.91 | 默认档 $8.50,分数相同 | Fable 5.1 的 `medium`,约三分之一的成本 |
| DeepResearch Bench II,每任务 | `low` 66% 花 $4.66;默认档 65% 花 $7.12 | 默认档 71% 花 $6.71 | 冲最高分 Opus 5 默认档;Fable 5.1 只在 `low` 下划算 |
| Chartography,每图 | `low` 62.5 花 $0.15 | `low` 49 花 $0.38 | Fable 5.1,分更高价格 40% |
| Terminal-Bench-Science,每任务 | `low` 26.3% 花 $11.1;`max` 52.6% 花 $37.9 | 未公布 | 只能和 Fable 5 比 |

表背后的公式:每次成功的成本 = 每次尝试的成本 / 通过率。它惩罚会失败的便宜模型,因为失败的尝试照样计费,然后是重试,然后是失败带来的下游代价。要给长尾定价,不是中位数:20 道 WideSearch 题里,最贵的两道占 43% 的花费,最便宜的一半只占 10%(measured)。

### 3.6 决策矩阵

| 工作负载 | 选 | 数字 |
|---|---|---|
| 共享上下文很少的请求,不论量多大 | Opus 5 | 每轮缓存 token 低于 140,000 时 Opus 5 每轮更便宜,零缓存时便宜到 2 倍(derived) |
| 有测试的 coding agent | Fable 5.1 的 `low`,或 Opus 5 的 `low` 加失败重跑 `high` | Fable 5.1 `low` 88.6% 花 $0.54;Opus 5 重跑策略约 93% 花约 $0.45(measured) |
| 没有测试、必须冲最高分的 coding agent | Opus 5 默认档 | 91.7% 花 $1.01,对 Fable 5.1 的 92.1% 花 $1.19,差距在运行噪声内(measured) |
| 在一大段固定上下文上跑的长 loop(每轮 200,000 缓存 token 以上) | Fable 5.1,从 `low` 起步 | 每轮 300,000 缓存 token 时 Fable 5.1 便宜 22%,600,000 时便宜 34%(derived);也是成本指南自己的建议(official) |
| 深度研究报告 | Opus 5 默认档;预算更紧就 Fable 5.1 的 `low` | 71% 花 $6.71,对 66% 花 $4.66(measured) |
| 读图表和文档 | Fable 5.1 的 `low` | 62.5 花 $0.15,对 Opus 5 的 49 花 $0.38(measured) |
| Opus 5 在 `xhigh` 或 `max` 下仍不达标的工作 | Fable 5.1 的 `xhigh` 或 `max` | 官方的升级触发条件;Intelligence Index 66 对 63(measured) |
| 有检查器的高频简单任务 | Haiku 4.5 或 Sonnet 5 | Haiku 4.5 答 GPQA Diamond 每题成本约是 Opus 5 的十分之一,63% 对 92%(measured) |

### 3.7 订阅用户

Claude Pro 用户使用 Fable 5.1 需要额外付费;Opus 5 是订阅内包含的最强模型(estimate:维护者报告,来源链接待补;补上支持文章链接后重新定级)。

### 3.8 会改变结论的因素

- **重试和人工复核。** 如果一次失败要人来看,先把复核成本加进每次尝试的成本,再除以通过率;每次尝试 $1 时 4 个百分点的通过率差距值 $0.18,复核一次 $5 时就不止了。
- **拒答和回退。** Fable 5.1 带安全分类器,可能返回 `stop_reason: "refusal"`;服务端回退会在 Opus 5 或 Opus 4.8 上重试,fallback credit 退还换模型的 prompt 缓存成本(official)。经常触发拒答的工作负载在为两个模型付钱。
- **限流和层级。** Fable 5.1 和 Fable 5 共用限流池,没有 Priority Tier;fast mode 只有 Opus 5 和 Opus 4.8 有,$10 / $50(official)。
- **数据保留。** Fable 5.1 要求 30 天保留;零保留组织每次请求都收到 400(official)。
- **仅美国推理** 在两个模型上都让每个 token 乘 1.1(official)。

## 4. 1M 上下文的实际用法

计划在 v0.2 发布(目标 2026-09-05)。先记两个数:1M 窗口没有长上下文加价;把它塞满一次,未缓存输入 $10.00,5 分钟缓存写入 $12.50,缓存读取 $0.25(official, derived)。

## 5. 从 Fable 5 迁移

计划在 v0.2 发布(目标 2026-09-06)。三个 breaking change 已经在 [`data/facts.json`](data/facts.json) 里:forced `tool_choice` 返回 400,thinking block 绑定生成它的模型,2026-08-31 及之后创建的账号编辑历史会让 thinking block 失效(official)。

## 6. 常见浪费模式 checklist

计划在 v0.2 发布(目标 2026-09-07)。每一条都会带实测成本和暴露它的 `usage` 字段。

## 更新策略与贡献

- Anthropic 新模型发布和定价变化会跟进收录;先改 `data/facts.json`,再改两份 README 和信息图,最后改 [CHANGELOG](CHANGELOG.md) 和 badge 日期。
- 贡献的数字必须带来源 URL、核对日期和来源等级。三者缺一不合并。
- 来源之间的分歧记录在 `data/facts.json` 的 `discrepancies` 下,写明采用哪个值和理由。
- 过时的建议标日期,不删除。

## 来源

- Anthropic 定价:https://platform.claude.com/docs/en/about-claude/pricing
- Anthropic 模型总览:https://platform.claude.com/docs/en/about-claude/models/overview
- Claude Fable 5.1 模型页与 what's new:https://platform.claude.com/docs/en/models/fable-5-1/overview
- Effort:https://platform.claude.com/docs/en/build-with-claude/effort
- Prompt caching:https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Optimizing for cost and intelligence(上文所有 Anthropic 实测):https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence
- 发布文,含各档 effort 的图表数据:https://www.anthropic.com/claude-fable-and-mythos-5-1
- Artificial Analysis:https://artificialanalysis.ai/articles/claude-fable-5-1

## 许可

MIT,版权 2026 Ben Cheng。见 [LICENSE](LICENSE)。
