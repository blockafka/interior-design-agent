---
name: copywriter
description: 基于 StyleDNA + 设计效果图 + 户型 query，生成帮助家装公司获客的小红书营销图文（标题 / 正文 / Hashtag）
order: 5
input_schema: StyleDNA + GeneratedImages + UserRequest
output_schema: CopyContent
tools:
  - tools.llm.chat_with_images
owner: kafka
status: live
---

# Step 5 · 文案 Agent

## 一句话职责
吃进风格档案 + 生成的设计效果图 + 户型 query，吐出复刻对标账号语气、展示这套定制效果图亮点、帮助家装公司获客的小红书营销图文。

## 输入
- `StyleDNA` —— 主要用 `copy` 字段（voice / keywords / sentence_pattern / hashtag_pattern）
- `GeneratedImages` —— 可读 image_urls
- `UserRequest` —— 户型背景

## 输出：CopyContent
schema 见 `core/schemas.py::CopyContent`。字段：
- `title`: str —— 标题（≤ 20 字）
- `body`: str —— 正文（150-300 字）
- `hashtags`: list[str] —— 5-8 个 hashtag

## 实现步骤
1. 用 `StyleDNA.copy.voice` + `sentence_pattern` + `hashtag_pattern` 作为风格指令
2. 让多模态 LLM 观察设计效果图，围绕 `UserRequest.user_notes` 的客户 query 写营销文案
3. 输出 JSON 并解析为 `CopyContent`，失败时走兜底文案，保证主链路不断

## 联调约定
- 所有输入只读
- 输出直接进 `FinalPost` 返回前端
