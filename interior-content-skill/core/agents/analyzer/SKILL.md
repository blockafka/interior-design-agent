---
name: analyzer
description: 从对标账号的笔记内容中提取「风格 DNA」—— 视觉风格（色调/材质/构图/光线）+ 文案风格（语气/句式/关键词/Hashtag）
order: 2
input_schema: CollectedContent
output_schema: StyleDNA
tools:
  - tools.llm.chat_with_images
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

**完整输入样例**（collector 输出目录）：`examples/collect-sample/`

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

### `copy_dna` (dict) —— 文案风格档案
| key | 类型 | 含义 | 示例 |
|-----|------|------|------|
| `voice` | str | 整体语气（一句话） | `"治愈系，第一人称温暖叙事"` |
| `keywords` | list[str] | 高频关键词（5-10 个） | `["奶油风", "无主灯", "氛围感"]` |
| `sentence_pattern` | str | 句式特点（一句话） | `"短句为主，emoji 点缀，多用感叹号"` |
| `hashtag_pattern` | list[str] | Hashtag 习惯（5-8 个） | `["#家装日记", "#奶油风"]` |

**完整输出样例**：运行后见 `data/runs/<request_id>/style_dna.json`

## 实现步骤（kafka 填实现）

1. **样本筛选**：按 `likes + collects * 2`（收藏含金量高于点赞）加权排序，取 Top 5 篇进入分析
2. **视觉通道**：
   - 把样本去重后的图片（最多 8 张）合并成一次 `tools.llm.chat_with_images` 多模态调用
   - Prompt 让 LLM 输出 JSON：`{color_palette, material, composition, lighting}`
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
- LLM 返回非合法 JSON → 带错误反馈再调一次 → 仍失败回退 `_mocks`（MOCK_VISUAL / MOCK_COPY），主链路永不挂
- 无图片时视觉通道直接用 MOCK_VISUAL；无 posts 时文案通道用 MOCK_COPY

## 联调约定
- **上游**（collector）：建议 posts ≥ 3 效果更好，但 1 篇也能跑（无硬性下限）
- **下游**（prompter）：拿到 `StyleDNA` 只能读，不能改

## 负责人
**kafka**
