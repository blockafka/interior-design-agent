"""
文生图 API 封装

通过环境变量 IMAGE_GEN_PROVIDER 切换：
    mock / gemini_image / sd_local / jimeng / dalle
当前仅实现 mock + gemini_image，其余 provider 走 mock 兜底。

提供：
- text_to_image(prompt, negative_prompt, aspect_ratio) → str
    返回前端可直接 <img src> 的 URL。
    gemini_image: 落盘到 <project_root>/data/generated/{uuid}.png，
                  并返回 /static/generated/{uuid}.png
    联调备忘：server 队友需要在 FastAPI 中
        app.mount("/static/generated", StaticFiles(directory="data/generated"))

负责人：A · Agent 工程师
"""

from __future__ import annotations

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

    if provider == "gemini_image":
        return await _gemini_image(prompt, negative_prompt, aspect_ratio)

    if provider != "mock":
        logger.warning("IMAGE_GEN_PROVIDER=%s 尚未实现，降级到 mock", provider)
    return _PLACEHOLDER_URL


# ---------------------------------------------------------------
# Gemini Image 实现
# ---------------------------------------------------------------
def _compose_image_prompt(
    prompt: str, negative_prompt: str, aspect_ratio: str
) -> str:
    """把正向+负向+比例合成 Gemini Image 可接受的单条 prompt。"""
    sections = [prompt.strip()]
    if negative_prompt.strip():
        sections.append(f"避免以下问题：{negative_prompt.strip()}")
    sections.append(
        f"输出 {aspect_ratio} 竖版家居室内设计效果图，"
        f"真实住宅实拍质感，室内建筑摄影，自然光影，photorealistic，4K，sharp focus，"
        f"无人物，无文字，无 logo，无水印"
    )
    return "\n\n".join(sections)


async def _gemini_image(
    prompt: str, negative_prompt: str, aspect_ratio: str
) -> str:
    try:
        from google import genai  # type: ignore
    except Exception as exc:
        logger.error("google-genai 未安装，降级到 placeholder：%s", exc)
        return _PLACEHOLDER_URL

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning("GEMINI_API_KEY 未配置，降级到 placeholder")
        return _PLACEHOLDER_URL

    model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    composed_prompt = _compose_image_prompt(prompt, negative_prompt, aspect_ratio)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=composed_prompt,
        )
        image_bytes = _extract_image_bytes(response)
        if not image_bytes:
            logger.warning("Gemini Image 未返回 inline_data，降级到 placeholder")
            return _PLACEHOLDER_URL

        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.png"
        file_path = GENERATED_DIR / filename
        file_path.write_bytes(image_bytes)
        return f"{HTTP_PREFIX}/{filename}"
    except Exception as exc:
        logger.error("Gemini Image 调用失败，降级到 placeholder：%s", exc)
        return _PLACEHOLDER_URL


def _extract_image_bytes(response) -> bytes | None:
    """从 google-genai 返回里提取第一段 inline 图片数据。"""
    candidates = getattr(response, "candidates", None) or []
    for cand in candidates:
        content = getattr(cand, "content", None)
        if content is None:
            continue
        parts = getattr(content, "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None)
            if inline is None:
                continue
            data = getattr(inline, "data", None)
            if isinstance(data, bytes) and data:
                return data
            if isinstance(data, str) and data:
                # 兜底：若 SDK 给的是 base64 字符串，尝试解码
                import base64
                try:
                    return base64.b64decode(data)
                except Exception:
                    continue
    return None
