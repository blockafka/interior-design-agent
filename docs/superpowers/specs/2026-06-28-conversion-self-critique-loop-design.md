# StyleDNA · 转化力自我修正闭环（Conversion Self-Critique Loop）设计文档

> 日期：2026-06-28
> 状态：设计待评审
> 作者：kafka（产品方向） + Claude（方案）

## 1. 背景与问题

当前 StyleDNA 是一条**开环单向流水线**：

```
analyzer → prompter → generator → copywriter → FinalPost
```

`core/orchestrator.py` 只是 4 行顺序 `await`，**没有任何一步会回头评估上一步产出的好坏、决定要不要重做**。这导致三个对外可感知的硬伤：

1. **没有质量闭环**：生成的图文出来什么就是什么，没有 agent 评估它"能不能带来生意"。
2. **流程写死、缺乏 agentic 决策**：没有规划、没有条件分支、没有重试改写——"多 Agent"实为"多函数"。
3. **真实互动数据被浪费**：采集样本带有真实 `liked_count` / `collect_count`（见 `collect_loader.py`），但 `analyzer._select_top_posts` 仅用它排序取 Top5 后即丢弃。

### 商业价值定位

- **付费客户**：家装公司 / 独立设计师 / 家装内容代运营。
- **核心痛点**：小红书获客——需要持续产出**能带来真实咨询**的笔记，而不只是"好看的图文"。
- **本次创新的价值主张**：让 Agent 不止"生成内容"，而是像投手 / 操盘手一样**对获客转化力负责**——评估这篇笔记的爆款潜力，不达标就自我修正重写，直到达标。

## 2. 目标与非目标

### 目标

- 在现有流水线**末尾插入评估能力**，对成品图文输出可信的"转化力评分卡"。
- 把死流水线**掰成闭环**：评估不达标 → 自动带改进意见重写文案 → 再评估，直到达标或到迭代上限。
- 评分**有真实数据背书**：评分标尺从对标账号**真实高/低互动笔记**中反推，而非 LLM 主观拍脑袋。
- 现场可视化：通过 SSE 让评委**肉眼看到 Agent 自我否定 → 重写 → 分数提升**的迭代过程。

### 非目标（YAGNI）

- **不**接入小红书官方 / 第三方实时数据 API（合规风险 + 时间不够）。
- **不**在闭环中重新生成图片（生图最慢最烧钱，转化力主要由文案/钩子承载）。
- **不**做多账号批量内容日历（属另一个方向，本 spec 不含）。
- **不**改动采集（collector）链路——本 skill 只消费其输出。
- **不**做 A/B 双版本对决（已在方案讨论中淘汰）。

## 3. 核心机制：GrowthDNA（爆款基因）

这是整套设计的差异化资产，也是评分可信度的来源。

**做法**：现有 `_select_top_posts` 把真实 `likes/collects` 只拿来排序取 Top5 就丢弃。新增一步，让 Agent **对比该账号的"高互动笔记 vs 低互动笔记"**，反推出"这个账号靠什么火"——例如：

- "带『前后对比』结构的笔记，平均点赞高 3 倍"
- "标题含具体数字（如『180㎡』『3 个细节』）的笔记收藏更高"
- "正文第一句就抛痛点的笔记互动显著更好"

这套规律（GrowthDNA）从**真实数据**学出，有两个用途：

1. **评分标尺**：evaluator 用它给新笔记打分时，依据是"该账号自己的爆款规律"，可信、可解释。
2.（可选增强，本期默认开启）**指导生成**：copywriter 重写时参考 GrowthDNA，让改写有的放矢。

**应对评委质疑**：当被问"凭什么准"，回答是——"评分标准是从这个账号的真实点赞收藏数据里学出来的，不是我编的"。

## 4. 架构设计

### 4.1 数据流（闭环）

```
collected_content ─┬─► analyzer ────────► StyleDNA
                   └─► growth_analyzer ─► GrowthDNA      （二者并行，各跑一次）
                                              │
StyleDNA + UserRequest ─► prompter ─► generator ─► copywriter(v1)
                                                        │
                                   ┌────────────────────┘
                                   ▼
                              evaluator ──► ConversionScore(v1)
                                   │
                   ┌───────────────┴───────────────┐
          分数 ≥ 阈值 或 已达迭代上限          分数 < 阈值 且 未达上限
                   │                               │
                   ▼                               ▼
               FinalPost                  copywriter(v2)  ◄── 带 evaluator 改进意见
            （含最终分 + 迭代轨迹）                 │
                                                   ▼
                                              evaluator ──► ConversionScore(v2)
                                                   │
                                          （回到上面的判断，循环）
```

### 4.2 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 闭环重写范围 | **只重写文案，不重新生图** | 生图是最慢最烧钱环节（1–3 分钟/次）；转化力主要由标题/钩子/文案承载，重生图性价比极低，循环成本失控。 |
| GrowthDNA 与 StyleDNA 关系 | **两个独立 schema** | StyleDNA 管"像不像"（视觉/文案风格），GrowthDNA 管"火不火"（转化规律）。关注点分离，互不污染。 |
| growth_analyzer 是否进循环 | **不进循环，只跑一次** | 账号的爆款规律在一次会话内是稳定的；与 analyzer 并行跑，不增加循环时延。 |
| 迭代上限 | **默认 2 轮重写**（v1 + 最多 2 次改写 = 最多 3 个版本） | 平衡现场时延与改进效果；可配置。 |
| 达标阈值 | **默认 75 分**（满分 100） | 经验阈值，可配置；低于此触发重写。 |
| 评分失败兜底 | **沿用现有 3 级兜底范式**（解析失败→带错重试→mock 兜底） | 与 analyzer 一致，主链路永不挂；兜底时视为"已达标"直接出稿，避免死循环。 |
| 数据契约改动 | **只在 `schemas.py` 新增类型，不破坏现有字段** | 现有 schema 被多人依赖（文件头有"修改需群里通知"约定）；只做加法。 |

## 5. 数据契约（schemas.py 增量）

只新增，不修改现有类型。

```python
# ============================================================
# 新增 · 爆款基因（growth_analyzer 输出）
# ============================================================
class GrowthDNA(BaseModel):
    target_account_id: str
    # 从真实高/低互动对比中反推的爆款规律，每条可解释
    patterns: list[str]          # 如 ["带前后对比的笔记赞高 3 倍", ...]
    high_performers: list[str]   # 高互动样本 post_id（评分依据可追溯）
    low_performers: list[str]    # 低互动样本 post_id
    # 可量化的统计锚点（用于评分时引用真实数字）
    stats: dict                  # 如 {"avg_likes": 1200, "top_likes": 8800, ...}


# ============================================================
# 新增 · 转化力评分卡（evaluator 输出）
# ============================================================
class ConversionScore(BaseModel):
    total: int                   # 0–100 综合爆款分
    sub_scores: dict             # {"hook": 0-100, "visual_appeal": 0-100, "cta": 0-100}
    rationale: str               # 为什么这么打（引用 GrowthDNA / 真实数据）
    suggestions: list[str]       # 给 copywriter 的具体改进意见（不达标时使用）
    passed: bool                 # total >= 阈值


# ============================================================
# 新增 · 单轮迭代记录（用于可视化迭代轨迹）
# ============================================================
class IterationRecord(BaseModel):
    round: int                   # 第几版（1 = 初版）
    copy_content: CopyContent
    score: ConversionScore


# ============================================================
# 修改 · FinalPost 增加可选字段（向后兼容，默认 None / 空）
# ============================================================
# growth_dna: Optional[GrowthDNA] = None
# conversion_score: Optional[ConversionScore] = None      # 最终采用版的分
# iterations: list[IterationRecord] = Field(default_factory=list)  # 完整迭代轨迹
```

> `FinalPost` 的新增字段全部可选 / 有默认值，**不破坏**现有调用方与前端。

## 6. 组件设计

每个 agent 单一职责、通过上面的 schema 通信、可独立测试。

### 6.1 growth_analyzer（新增 `core/agents/growth_analyzer/`）

- **输入**：`CollectedContent`（含真实互动数 metadata）。
- **做什么**：
  1. 用互动分把笔记切成高互动组 / 低互动组（复用现有 score 逻辑：`likes + collects*2`）。
  2. 把两组的标题/正文/互动数对比喂给 LLM，要求反推"高互动组相对低互动组的共性特征"。
  3. 产出 `GrowthDNA`（patterns + 可追溯的样本 id + 统计锚点）。
- **输出**：`GrowthDNA`。
- **依赖**：`tools.llm.chat`。
- **兜底**：样本不足（如全部笔记互动数缺失或样本 < 4）→ 退化为 mock GrowthDNA（通用家装爆款常识），并在 rationale 标注"样本不足，使用通用规律"。
- **目录结构**：对齐 analyzer——`agent.py` / `_prompts.py` / `_mocks.py`。

### 6.2 evaluator（新增 `core/agents/evaluator/`）

- **输入**：`CopyContent`（当前版文案）+ `GeneratedImages` + `GrowthDNA` + `UserRequest`。
- **做什么**：以 GrowthDNA 为标尺，对当前图文打 `ConversionScore`，并在不达标时给出**具体、可执行**的改进意见（指向钩子/标题/CTA）。
- **输出**：`ConversionScore`。
- **依赖**：`tools.llm.chat`（图片可选传入多模态，本期默认仅用文案+prompt 文本评估以省时；多模态评估为后续增强）。
- **兜底**：解析失败→带错重试→mock 兜底；兜底时 `passed=True` 直接出稿，避免死循环。

### 6.3 copywriter（改造 `core/agents/copywriter/`）

- **新增可选入参**：`growth_dna: GrowthDNA | None`、`feedback: ConversionScore | None`。
- **行为**：
  - 首版（v1）：行为与现状一致，可额外参考 GrowthDNA。
  - 重写版（v2+）：在原 prompt 基础上**注入上一版评分的 `suggestions`**，要求针对性改写以提升转化力。
- **向后兼容**：新参数默认 `None`，不传时行为完全等同现状。

### 6.4 orchestrator（改造 `core/orchestrator.py`）

核心：把末尾改成带阈值的循环。伪代码：

```python
style, growth = await asyncio.gather(
    analyzer_run(content),
    growth_analyzer_run(content),
)
prompts = await prompter_run(style, request)
images = await generator_run(prompts)           # 生图只跑一次

iterations: list[IterationRecord] = []
feedback = None
MAX_ROUNDS = 3          # v1 + 最多 2 次重写
THRESHOLD = 75

for round_no in range(1, MAX_ROUNDS + 1):
    copy = await copywriter_run(
        style, images, request,
        growth_dna=growth,
        feedback=feedback,          # 第 1 轮为 None
    )
    score = await evaluator_run(copy, images, growth, request)
    iterations.append(IterationRecord(round=round_no, copy_content=copy, score=score))
    if score.passed:
        break
    feedback = score                # 不达标，把意见带入下一轮

best = max(iterations, key=lambda it: it.score.total)   # 兜底取最高分版
return FinalPost(
    request_id=request_id,
    style_dna=style,
    growth_dna=growth,
    images=images,
    copy_content=best.copy_content,
    conversion_score=best.score,
    iterations=iterations,
    generated_at=datetime.now(),
)
```

> 即使始终不达标，也取**迭代中最高分版**作为最终稿，绝不空手而归。

## 7. SSE 事件协议（server/main.py 增量）

现有事件：`step_start` / `step_done` / `complete` / `error`。新增/扩展以可视化闭环：

| 事件 | 时机 | payload 关键字段 |
|------|------|------------------|
| `step_start` / `step_done` | 复用，新增 `growth_analyzer`、`evaluator` 两个 step | `step` 名称 + 中间结果 |
| `iteration` | 每完成一轮"重写+评分" | `round`、`total`、`sub_scores`、`passed`、`suggestions` |
| `complete` | 全部完成 | `FinalPost`（含 `conversion_score` 与 `iterations`） |
| `error` | 异常 | 错误信息 |

前端据此实时渲染"第 1 版 68 分 → 自评意见 → 第 2 版 81 分 ✅"的迭代轨迹。

## 8. 前端设计（web/ 增量）

- **GeneratingView**：Pipeline 节点增加 `growth_analyzer`、`evaluator`；evaluator 命中循环时，展示"重写中（第 N 轮）"的动态轨迹（消费 `iteration` 事件）。
- **ResultView**：新增**转化力评分卡**区块——综合爆款分（大字）、3 个子维度条、评分依据（引用真实数据规律），以及一条可折叠的"迭代轨迹"（v1→v2 分数变化 + 每轮改进意见）。
- 评分卡是现场商业价值的视觉锤，应醒目。

## 9. 演示脚本（路演用）

1. 选对标账号 + 填户型 → 生成。
2. Pipeline 亮灯，`growth_analyzer` 先点亮："正在从该账号真实点赞/收藏数据反推爆款基因"。
3. 首版文案生成 → evaluator 打分：**68 分，未达标**，自评"钩子太弱、缺行动引导"。
4. **Agent 自动重写** → 第 2 版：**81 分，达标 ✅**。
5. ResultView 展示最终图文 + 评分卡 + 迭代轨迹。
6. 一句话收尾："它不是生成一篇就完事，而是对获客转化负责——不达标自己重做，评分标准来自这个账号的真实爆款数据。"

## 10. 实现工作量与文件清单

| 模块 | 改动类型 | 文件 | 量级 |
|------|----------|------|------|
| 数据契约 | 加类型 | `core/schemas.py` | 小 |
| 爆款基因 | 新 agent | `core/agents/growth_analyzer/{agent,_prompts,_mocks}.py` | 中 |
| 转化力评估 | 新 agent | `core/agents/evaluator/{agent,_prompts,_mocks}.py` | 中 |
| 文案重写 | 改造 | `core/agents/copywriter/agent.py`、`_prompts.py` | 小 |
| 闭环编排 | 改造 | `core/orchestrator.py` | 小 |
| SSE 推送 | 加事件 | `server/main.py` | 小 |
| 前端评分卡 + 轨迹 | 加 UI | `web/src/components/*`、`App.jsx` | 中 |
| CLI 输出 | 加打印 | `scripts/run_from_collect.py` | 小 |

**整体量级：中。** 复用最大化——evaluator/growth_analyzer 沿用 analyzer 的双段 prompt + 3 级兜底范式；copywriter 改写是已有能力延展；不新增生图负担。

## 11. 风险与应对

| 风险 | 应对 |
|------|------|
| 闭环导致现场时延过长 | 只重写文案不重生图；迭代上限默认 2 轮；evaluator 默认纯文本评估。 |
| LLM 评分前后不一致 / 抖动 | 评分锚定 GrowthDNA 真实数据；同一会话内 GrowthDNA 固定，减少漂移。 |
| 始终不达标导致死循环 | 硬性 `MAX_ROUNDS` 上限 + 取最高分版兜底 + 评分异常时视为达标。 |
| 样本互动数据缺失 | growth_analyzer 退化为通用规律并明确标注，不阻断主链路。 |
| 破坏现有契约 | schema 只加不改；新参数全部可选默认 None；前端字段可选。 |

## 12. 验收标准

- 跑通一个真实账号，`FinalPost` 含非空 `growth_dna`、`conversion_score`、且 `iterations` 至少 1 条。
- 构造一个明显弱文案场景，能观测到"首版不达标 → 自动重写 → 分数提升"至少发生一次。
- 评分 `rationale` 能引用该账号真实互动数据 / GrowthDNA 规律（非空泛套话）。
- 全程任一 agent 失败都不导致主链路崩溃（兜底生效）。
- 前端能展示评分卡 + 迭代轨迹；CLI 能打印最终分。
