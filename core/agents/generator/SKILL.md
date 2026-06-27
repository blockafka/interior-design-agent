---
name: generator
description: 用 ImagePromptBundle 调用文生图 API（Gemini Image），生成 1-3 张家装设计效果图
order: 4
input_schema: ImagePromptBundle
output_schema: GeneratedImages
tools:
  - tools.image_gen.text_to_image
owner: A · Agent 工程师
status: in_progress
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

## 文生图选型：Gemini Image

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `IMAGE_GEN_PROVIDER` | `mock` | 设 `gemini_image` 走真实调用 |
| `GEMINI_API_KEY` | —— | 文本和图片复用同一个 key |
| `GEMINI_IMAGE_MODEL` | `gemini-2.5-flash-image` | 也可设 `gemini-3.1-flash-image` |

- `provider=mock` → 返回 `https://placehold.co/600x800?...` 占位
- `provider=gemini_image` → 调 `google.genai.Client.models.generate_content`，base64 落盘到 `<project_root>/data/generated/{uuid}.png`，返回 `/static/generated/{uuid}.png`
- 任何失败都回退 placeholder，**绝不**抛异常阻塞主链路

## 3 张变体策略
循环调 `text_to_image()`，在 `positive_prompt` 末尾追加变体提示：
1. **封面主图** —— 完整空间视角，强调整体氛围
2. **空间细节图** —— 突出材质质感与软装陈设
3. **生活氛围图** —— 突出自然光与居住感

`num_images > 3` 时循环复用上述变体；`num_images < 3` 时取前 N。
单张失败用 placeholder 补齐，**保证至少返回 1 张图**。

## 联调约定
- **上游**（prompter）：拿到 `ImagePromptBundle` 不修改
- **下游**（copywriter）：可以读 `image_urls` 但通常不读图（用 StyleDNA 已足够）

> **联调备忘（给 server 队友 Y）**：
> 当 `IMAGE_GEN_PROVIDER=gemini_image` 时，返回的 URL 形如 `/static/generated/{uuid}.png`。
> 需要在 `server/main.py` 挂载 StaticFiles：
> ```python
> from fastapi.staticfiles import StaticFiles
> app.mount("/static/generated", StaticFiles(directory="data/generated"), name="generated")
> ```
> （`data/generated/` 目录会在首张图生成时自动创建。）
