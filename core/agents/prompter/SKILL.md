---
name: prompter
description: 把 StyleDNA + 户型信息反推为文生图的 prompt 套件（正向 + 负向）
order: 3
input_schema: StyleDNA + UserRequest
output_schema: ImagePromptBundle
tools:
  - tools.llm.chat
owner: TBD
status: skeleton
---

# Step 3 · 提示词工程 Agent

## 一句话职责
吃进 `StyleDNA`（上游风格档案）+ `UserRequest`（含户型信息），吐出可直接喂给文生图模型的 prompt 套件。

## 输入
- `StyleDNA` —— 见 `core/schemas.py::StyleDNA`
- `UserRequest` —— 主要用 `floorplan_meta`（户型 / 面积 / 朝向）和 `user_notes`

## 输出：ImagePromptBundle
schema 见 `core/schemas.py::ImagePromptBundle`。字段：
- `positive_prompt`: str —— 正向 prompt
- `negative_prompt`: str —— 负向 prompt
- `aspect_ratio`: str —— 默认 `"3:4"`

## 实现步骤（TODO 填实现）
1. 把 `StyleDNA.visual` 的 4 个维度翻译成自然语言描述
2. 拼上户型信息（户型 / 面积 / 朝向）
3. 套上通用模板：`photorealistic / 4K / 无人物 / 无文字 / 无 logo`
4. 负向 prompt 模板基本固定

## 联调约定
- **上游**（analyzer）：拿到 `StyleDNA` 只读
- **下游**（generator）：拿到 prompt 直接喂模型
