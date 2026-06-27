---
name: generator
description: 用 ImagePromptBundle 调用文生图 API，生成 1-3 张家装设计效果图
order: 4
input_schema: ImagePromptBundle
output_schema: GeneratedImages
tools:
  - tools.image_gen.text_to_image
owner: TBD
status: skeleton
---

# Step 4 · 图片生成 Agent

## 一句话职责
吃进 prompt 套件，调文生图 API，吐出 1-3 张设计效果图 URL。

## 输入：ImagePromptBundle
schema 见 `core/schemas.py::ImagePromptBundle`。

## 输出：GeneratedImages
schema 见 `core/schemas.py::GeneratedImages`。字段：
- `image_urls`: list[str] —— 1-3 张图的 URL
- `prompts_used`: ImagePromptBundle —— 原样回传方便溯源

## 实现步骤（TODO 填实现）
1. 调用文生图 API（待选型：奇绩本地 SD / 即梦 / DALL-E）
2. 失败 → 重试 1 次 → 回退到 `data/samples/` 兜底图

## 联调约定
- **上游**（prompter）：拿到 `ImagePromptBundle` 不修改
- **下游**（copywriter）：可以读 image_urls 但通常不读图（用 StyleDNA 已足够）
