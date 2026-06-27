"""
文生图 API 封装

通过环境变量 IMAGE_GEN_PROVIDER 切换：
    mock / openai_image
当前实现 mock + openai_image（中转平台 gpt-image-1）。

提供：
- text_to_image(prompt, negative_prompt, aspect_ratio) → str
    返回前端可直接 <img src> 的 URL 或本地路径。
    openai_image: 落盘到 <project_root>/data/generated/{uuid}.png，
                  返回 /static/generated/{uuid}.png

负责人：A · Agent 工程师
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
HTTP_PREFIX = "/static/generated"

_PLACEHOLDER_URL = "https://placehold.co/600x800?text=Generated+Image"


# ---------------------------------------------------------------
# 对外 API
# ---------------------------------------------------------------
async def text_to_image(
    prompt: str,
    negative_prompt: str = "",
    aspect_ratio: str = "3:4",
) -> str:
    """
    文生图入口。出错或未配置时返回 placeholder URL，不抛异常。
    """
    provider = (os.getenv("IMAGE_GEN_PROVIDER", "mock") or "mock").lower()

    if provider == "openai_image":
        return await _openai_image(prompt, negative_prompt, aspect_ratio)

    if provider != "mock":
        logger.warning("IMAGE_GEN_PROVIDER=%s 尚未实现，降级到 mock", provider)
    return _PLACEHOLDER_URL


# ---------------------------------------------------------------
# OpenAI Image 实现（gpt-image-1 via 中转平台）
# ---------------------------------------------------------------
async def _openai_image(
    prompt: str, negative_prompt: str, aspect_ratio: str
) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        logger.error("openai 包未安装，降级到 placeholder：%s", exc)
        return _PLACEHOLDER_URL

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai-next.com/v1").strip()

    if not api_key:
        logger.warning("OPENAI_API_KEY 未配置，降级到 placeholder")
        return _PLACEHOLDER_URL

    model = os.getenv("IMAGE_GEN_MODEL", "gpt-image-1")

    full_prompt = prompt.strip()
    if negative_prompt.strip():
        full_prompt += f"\n\n避免以下问题：{negative_prompt.strip()}"

    size = _aspect_ratio_to_size(aspect_ratio)

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.images.generate(
            model=model,
            prompt=full_prompt,
            n=1,
            size=size,
        )

        image_data = response.data[0]

        if hasattr(image_data, "b64_json") and image_data.b64_json:
            image_bytes = base64.b64decode(image_data.b64_json)
            GENERATED_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"{uuid.uuid4().hex}.png"
            file_path = GENERATED_DIR / filename
            file_path.write_bytes(image_bytes)
            return f"{HTTP_PREFIX}/{filename}"
        elif hasattr(image_data, "url") and image_data.url:
            return image_data.url
        else:
            logger.warning("OpenAI Image 未返回有效数据，降级到 placeholder")
            return _PLACEHOLDER_URL

    except Exception as exc:
        logger.error("OpenAI Image 调用失败，降级到 placeholder：%s", exc)
        return _PLACEHOLDER_URL


def _aspect_ratio_to_size(aspect_ratio: str) -> str:
    """把 aspect_ratio 映射为 OpenAI images API 支持的 size 参数。"""
    mapping = {
        "3:4": "768x1024",
        "4:3": "1024x768",
        "1:1": "1024x1024",
        "16:9": "1792x1024",
        "9:16": "1024x1792",
    }
    return mapping.get(aspect_ratio, "1024x1024")
