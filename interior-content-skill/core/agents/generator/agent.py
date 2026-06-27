"""
Agent 4 · 图片生成 Agent · 实现

负责人：A · Agent 工程师
契约 / 行为说明：见同目录 SKILL.md

输入：ImagePromptBundle
输出：GeneratedImages(image_urls, prompts_used)

实现：
- 默认生成 3 张图片（封面主图 / 空间细节 / 生活氛围）；
- 并发调用文生图 API，单张失败回退 placeholder；
- 通过 tools.image_gen.text_to_image 调用文生图。
"""

from __future__ import annotations

import asyncio
import logging

from core.constants import PLACEHOLDER_IMAGE_URL
from core.schemas import GeneratedImages, ImagePromptBundle
from tools.image_gen import text_to_image

logger = logging.getLogger(__name__)

VARIANT_HINTS: list[str] = [
    "封面主图，完整空间视角，强调整体氛围",
    "空间细节图，突出材质质感与软装陈设",
    "生活氛围图，突出自然光与居住感，让画面有真实生活气息",
]


async def run(prompts: ImagePromptBundle, num_images: int = 3) -> GeneratedImages:
    n = max(1, int(num_images or 1))

    tasks = [_generate_one(prompts, i) for i in range(n)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    image_urls: list[str] = []
    for r in results:
        if isinstance(r, Exception):
            logger.error("generator: 并发生成失败，回退 placeholder：%s", r)
            image_urls.append(PLACEHOLDER_IMAGE_URL)
        else:
            image_urls.append(r or PLACEHOLDER_IMAGE_URL)

    if not image_urls:
        image_urls = [PLACEHOLDER_IMAGE_URL]

    return GeneratedImages(image_urls=image_urls, prompts_used=prompts)


async def _generate_one(prompts: ImagePromptBundle, index: int) -> str:
    hint = VARIANT_HINTS[index % len(VARIANT_HINTS)]
    variant_prompt = f"{prompts.positive_prompt}\n\n本张图侧重：{hint}"
    url = await text_to_image(
        prompt=variant_prompt,
        negative_prompt=prompts.negative_prompt,
        aspect_ratio=prompts.aspect_ratio or "3:4",
    )
    return url or PLACEHOLDER_IMAGE_URL
