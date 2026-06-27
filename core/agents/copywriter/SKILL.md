---
name: copywriter
description: 基于 StyleDNA + 图片 + 户型，生成符合对标账号语气的小红书图文（标题 / 正文 / Hashtag）
order: 5
input_schema: StyleDNA + GeneratedImages + UserRequest
output_schema: CopyContent
tools:
  - tools.llm.chat
owner: TBD
status: skeleton
---

# Step 5 · 文案 Agent

## 一句话职责
吃进风格档案 + 生成的图 + 户型信息，吐出对标该账号语气的小红书图文。

## 输入
- `StyleDNA` —— 主要用 `copy` 字段（voice / keywords / sentence_pattern / hashtag_pattern）
- `GeneratedImages` —— 可读 image_urls
- `UserRequest` —— 户型背景

## 输出：CopyContent
schema 见 `core/schemas.py::CopyContent`。字段：
- `title`: str —— 标题（≤ 20 字）
- `body`: str —— 正文（150-300 字）
- `hashtags`: list[str] —— 5-8 个 hashtag

## 实现步骤（TODO 填实现）
1. 用 `StyleDNA.copy.voice` + `sentence_pattern` 作为风格指令
2. 让 LLM 按户型背景生成标题 + 正文
3. hashtags 直接复用 `StyleDNA.copy.hashtag_pattern`（或 LLM 微调）

## 联调约定
- 所有输入只读
- 输出直接进 `FinalPost` 返回前端
