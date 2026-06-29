---
name: generator
description: 用 ImagePromptBundle 调用文生图 API，生成 1-3 张家装设计效果图
order: 4
input_schema: ImagePromptBundle
output_schema: GeneratedImages
tools:
  - tools.image_gen.text_to_image
owner: TBD
status: implemented
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

## 实现步骤
1. 通过 `tools.image_gen.text_to_image` 调文生图（默认 `IMAGE_GEN_PROVIDER=openai_image`，走中转平台；设为 `mock` 返回占位图）
2. 3 张并发生成；单张失败 → 回退占位图（`PLACEHOLDER_IMAGE_URL`），保证返回 `num_images` 张

## 联调约定
- **上游**（prompter）：拿到 `ImagePromptBundle` 不修改
- **下游**（copywriter）：多模态读取生成的效果图（`chat_with_images`），结合 StyleDNA 写文案
