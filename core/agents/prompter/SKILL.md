---
name: prompter
description: 把 StyleDNA + 户型信息反推为文生图的 prompt 套件（正向 + 负向）
order: 3
input_schema: StyleDNA + UserRequest
output_schema: ImagePromptBundle
tools:
  - tools.llm.chat
owner: A · Agent 工程师
status: in_progress
---

# Step 3 · 提示词工程 Agent

## 一句话职责
吃进 `StyleDNA`（上游风格档案）+ `UserRequest`（含户型描述），调 Gemini 2.5 Pro 吐出可直接喂给文生图模型的 prompt 套件。

## 输入
- `StyleDNA` —— 见 `core/schemas.py::StyleDNA`
- `UserRequest` —— 主要用 `floorplan_meta` 和 `user_notes`

> **当前 MVP 已降级**：用户**可以不上传户型图**。
> `floorplan_image_url` 允许传空字符串 `""`，本 Skill **不依赖**该字段。
> 空间描述**只**来自 `floorplan_meta` + `user_notes`。

### `floorplan_meta` 约定字段（全部 optional，缺省按合理推断）
| key | 含义 | 示例 |
|-----|------|------|
| `area_sqm` | 面积（平米） | `120` |
| `rooms` | 户型 | `"三室两厅"` |
| `space_type` | 空间类型（默认 `"客厅"`） | `"客厅"` / `"主卧"` / `"厨房"` |
| `orientation` | 朝向 | `"南北通透"` |
| `target_customer` | 目标客户 | `"二胎家庭"` |
| `pain_points` | 痛点 / 诉求 | `"采光差，想要明亮温暖"` |

## 输出：ImagePromptBundle
schema 见 `core/schemas.py::ImagePromptBundle`。字段：
- `positive_prompt`: str —— Gemini 2.5 Pro 生成的中文长描述（200-400 字）
- `negative_prompt`: str —— 项目固定模板（见 agent.py `NEGATIVE_PROMPT_FIXED`）
- `aspect_ratio`: str —— 固定 `"3:4"`

## 实现要点

1. 抽取 `style.visual` 的 4 个维度（color_palette / material / composition / lighting）+ `floorplan_meta` 6 字段 + `user_notes`，组装上下文 ctx；
2. 调 `tools.llm.chat(messages)`（LLM_PROVIDER=gemini → Gemini 2.5 Pro），让其严格输出 JSON：
   ```json
   {"positive_prompt": "...", "negative_prompt": "", "aspect_ratio": "3:4"}
   ```
3. 解析 JSON（支持直接解析 / ```json``` 围栏 / 首个 `{...}` 块三层兜底）；
4. `positive_prompt` 取 LLM 输出，**`negative_prompt` 始终用项目固定列表**（覆盖 LLM 返回）；
5. 解析失败 → 走 `_fallback_positive_prompt()` 本地模板拼接 ctx，保证不阻塞主链路。

## 关键 Prompt 思路（已在 agent.py 内置）

system + user 两段 messages，明确要求：
- 融合风格 DNA 4 维 + 户型 6 字段 + 用户备注；
- 强调真实住宅实拍质感、室内建筑摄影、自然光影、3:4 竖版、photorealistic、4K；
- 严禁人物、文字、logo、水印；
- 严格 JSON 输出，禁止 markdown 围栏。

## 联调约定
- **上游**（analyzer）：拿到 `StyleDNA` 只读；`visual` 字段尽量完整。
- **下游**（generator）：拿到 prompt 直接喂模型，不改 `negative_prompt`。
