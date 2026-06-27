---
name: analyzer
description: 从对标账号的笔记内容中提取「风格 DNA」—— 视觉风格（色调/材质/构图/光线）+ 文案风格（语气/句式/关键词/Hashtag）
order: 2
input_schema: CollectedContent
output_schema: StyleDNA
tools:
  - tools.llm.vision
  - tools.llm.chat
owner: kafka
status: in_progress
---

# Step 2 · 风格分析 Agent

## 一句话职责
吃进 N 篇笔记（文本 + 图片 URL），用多模态 LLM 提取「风格 DNA」JSON，直接喂给下游提示词 Agent。

## 输入：CollectedContent
schema 见 `core/schemas.py::CollectedContent`（line 44）。

关键字段：
- `posts[*].body` —— 文案分析的素材
- `posts[*].image_urls` —— 视觉分析的素材
- `posts[*].metadata` —— 互动数据（可用来加权重要样本）

**完整输入 JSON 样例**：`examples/analyzer_input_sample.json`

## 输出：StyleDNA
schema 见 `core/schemas.py::StyleDNA`（line 53）。

两个一级字段，全部以 dict 形式存：

### `visual` (dict) —— 视觉风格档案
| key | 类型 | 含义 | 示例 |
|-----|------|------|------|
| `color_palette` | list[str] | 主色调（3-5 个，颜色名 或 HEX） | `["奶油白", "原木色", "#F5E6D3"]` |
| `material` | list[str] | 主要材质（3-5 个） | `["实木", "亚麻", "藤编", "陶瓷"]` |
| `composition` | str | 构图特点（一句话） | `"对称构图为主，远近景结合"` |
| `lighting` | str | 光线风格（一句话） | `"自然光为主，下午斜光，无主灯氛围"` |

### `copy` (dict) —— 文案风格档案
| key | 类型 | 含义 | 示例 |
|-----|------|------|------|
| `voice` | str | 整体语气（一句话） | `"治愈系，第一人称温暖叙事"` |
| `keywords` | list[str] | 高频关键词（5-10 个） | `["奶油风", "无主灯", "氛围感"]` |
| `sentence_pattern` | str | 句式特点（一句话） | `"短句为主，emoji 点缀，多用感叹号"` |
| `hashtag_pattern` | list[str] | Hashtag 习惯（5-8 个） | `["#家装日记", "#奶油风"]` |

**完整输出 JSON 样例**：`examples/analyzer_output_sample.json`

## 实现步骤（kafka 填实现）

1. **样本筛选**：按 `(likes * 1 + comments * 3)` 加权排序，取 Top 5 篇笔记进入分析（节省 token）
2. **视觉通道**：
   - 对每篇的 `image_urls` 并发调 `tools.llm.vision`
   - Prompt 让多模态 LLM 输出 JSON：`{color_palette, material, composition, lighting}`
   - 跨 5 篇取众数（color/material 取 Top-K，composition/lighting 取代表性的一条）
3. **文案通道**：
   - 把 5 篇的 `body` 拼成一个上下文，调 `tools.llm.chat`
   - Prompt 让 LLM 输出 JSON：`{voice, keywords, sentence_pattern, hashtag_pattern}`
4. **合并 + 校验**：
   - 组装 `StyleDNA(target_account_id, visual, copy_dna, sample_post_ids)`
   - `sample_post_ids` = 进入分析的 5 篇 post_id
   - 用 Pydantic 校验一遍 schema

## 关键 Prompt 思路（初版，可迭代）

**视觉 Prompt 草稿**：
```
你是一位家装风格分析师。
看下面这 3 张图，提取它们共同的视觉风格特征。
严格按 JSON 输出（不要有任何其他文字）：
{
  "color_palette": [3-5 个主色，可以是颜色名或 HEX],
  "material": [3-5 个主要材质],
  "composition": "构图特点，一句话",
  "lighting": "光线风格，一句话"
}
```

**文案 Prompt 草稿**：
```
你是一位小红书内容运营专家。
下面是某账号的 5 篇笔记正文（用 --- 分隔）。
分析这个账号的统一文案风格，严格按 JSON 输出：
{
  "voice": "整体语气，一句话",
  "keywords": [5-10 个高频关键词],
  "sentence_pattern": "句式特点，一句话",
  "hashtag_pattern": [5-8 个常用 hashtag]
}
```

## 失败兜底
- 若 LLM 返回非合法 JSON，重试一次；仍失败则回退到 `data/style_dna/<account>.json` 预生成档案
- 若 `posts` 长度 < 3，直接 raise（上游 collector 的责任）

## 联调约定
- **上游**（collector）：必须保证 `posts` 数组长度 ≥ 3
- **下游**（prompter）：拿到 `StyleDNA` 只能读，不能改

## 负责人
**kafka**
