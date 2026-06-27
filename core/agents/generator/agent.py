"""
Agent 4 · 图片生成 Agent · 实现

负责人：A · Agent 工程师
契约 / 行为说明：见同目录 SKILL.md

输入：ImagePromptBundle
输出：GeneratedImages(image_urls, prompts_used)

实现：
- 默认生成 3 张图片（封面主图 / 空间细节 / 生活氛围）；
- 单张失败回退 placeholder，保证至少返回 1 张；
- 通过 tools.image_gen.text_to_image 调用文生图，由 IMAGE_GEN_PROVIDER 决定真实/mock。
"""

from __future__ import annotations

import logging

from core.schemas import GeneratedImages, ImagePromptBundle
from tools.image_gen import text_to_image

logger = logging.getLogger(__name__)


# 3 张变体的拍摄侧重（追加在 prompt 末尾，引导模型出不同视角）
VARIANT_HINTS: list[str] = [
    "封面主图，完整空间视角，强调整体氛围",
    "空间细节图，突出材质质感与软装陈设",
    "生活氛围图，突出自然光与居住感，让画面有真实生活气息",
]

_PLACEHOLDER_URL = "https://placehold.co/600x800?text=Generated+Image"


async def run(prompts: ImagePromptBundle, num_images: int = 3) -> GeneratedImages:
    n = max(1, int(num_images or 1))

    image_urls: list[str] = []
    for i in range(n):
        hint = VARIANT_HINTS[i % len(VARIANT_HINTS)]
        variant_prompt = f"{prompts.positive_prompt}\n\n本张图侧重：{hint}"
        try:
            url = await text_to_image(
                prompt=variant_prompt,
                negative_prompt=prompts.negative_prompt,
                aspect_ratio=prompts.aspect_ratio or "3:4",
            )
        except Exception as exc:
            logger.error("generator: text_to_image 抛异常，回退 placeholder：%s", exc)
            url = _PLACEHOLDER_URL

        image_urls.append(url or _PLACEHOLDER_URL)

    # 双重保险：哪怕循环出错也至少返回 1 张
    if not image_urls:
        image_urls = [_PLACEHOLDER_URL]

    return GeneratedImages(image_urls=image_urls, prompts_used=prompts)
