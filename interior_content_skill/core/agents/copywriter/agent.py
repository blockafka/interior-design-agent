"""Agent 5 · 文案 Agent · 实现

负责人：kafka
契约：core/agents/copywriter/SKILL.md
开发笔记：docs/copywriter_dev_plan.md

实现要点：
- 单次多模态调用：StyleDNA + 户型 query + 设计图一起输入
- 核心目标：展示针对客户 query 生成的效果图多好，帮家装公司营销获客
- 3 级兜底链：1st 调用 → JSON 错误反馈重试 → MOCK 兜底
"""

import asyncio
import base64
import io
import json
import mimetypes
from pathlib import Path
from typing import Awaitable, Callable

from ...schemas import CopyContent, GeneratedImages, StyleDNA, UserRequest
from ....tools.llm import chat_with_images

from ._mocks import MOCK_COPY
from ._prompts import COPYWRITER_SYSTEM_PROMPT, COPYWRITER_USER_PROMPT_TEMPLATE

_MAX_IMAGES = 4
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_PLACEHOLDER_PREFIXES = (
    "https://placehold.co/",
    "http://placehold.co/",
)


async def run(
    style: StyleDNA,
    images: GeneratedImages,
    request: UserRequest,
) -> CopyContent:
    """copywriter 主入口（被 orchestrator / skill_loader 调用）。"""
    style_brief = _build_style_brief(style)
    floorplan_text = _extract_floorplan_text(request)
    image_urls = _select_image_urls(images)

    async def call(error_hint: str | None = None) -> str:
        hint = ""
        if error_hint:
            hint = f"【上一次输出格式错误】\n{error_hint}\n请严格按上方 JSON schema 重新输出完整 JSON。"
        return await chat_with_images(
            system=COPYWRITER_SYSTEM_PROMPT,
            user_text=COPYWRITER_USER_PROMPT_TEMPLATE.format(
                style_brief=style_brief,
                floorplan=floorplan_text,
                error_hint=hint,
            ),
            image_urls=image_urls,
            temperature=0.8,
            timeout=90.0,
        )

    raw = await _call_with_retry(call, _parse_copy_json, MOCK_COPY)
    return CopyContent(
        title=raw["title"],
        body=raw["body"],
        hashtags=raw["hashtags"],
    )


def _select_image_urls(images: GeneratedImages) -> list[str]:
    """优先给多模态模型真实效果图；生成器 mock 时退回本地 generated 样例。"""
    image_urls = [
        _normalize_generated_image_url(url)
        for url in images.image_urls or []
        if not _is_placeholder_url(url)
    ]
    image_urls = [url for url in image_urls if url]
    if image_urls:
        return image_urls[:_MAX_IMAGES]
    return _load_generated_fallback_images(_MAX_IMAGES)


def _normalize_generated_image_url(url: str) -> str:
    """把生成器返回的 /static/generated 本地路径转成 data URI，方便多模态模型读取。"""
    if str(url).startswith("/static/generated/"):
        filename = str(url).removeprefix("/static/generated/")
        path = _PROJECT_ROOT / "data" / "generated" / filename
        if path.exists() and path.is_file():
            return _local_image_to_data_uri(path)
    return str(url)


def _is_placeholder_url(url: str) -> bool:
    return any(str(url).startswith(prefix) for prefix in _PLACEHOLDER_PREFIXES)


def _load_generated_fallback_images(limit: int) -> list[str]:
    generated_dir = _PROJECT_ROOT / "data" / "generated"
    if not generated_dir.exists():
        return []
    paths = sorted(
        p
        for p in generated_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    return [_local_image_to_data_uri(path) for path in paths[:limit]]


def _local_image_to_data_uri(path: Path) -> str:
    compressed = _try_compress_image(path)
    if compressed is not None:
        mime_type, data = compressed
    else:
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
    return f"data:{mime_type};base64,{base64.b64encode(data).decode()}"


def _try_compress_image(path: Path) -> tuple[str, bytes] | None:
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return "image/jpeg", buf.getvalue()
    except Exception:
        return None


def _build_style_brief(style: StyleDNA) -> str:
    """把 StyleDNA 的视觉/文案 dict 拼成 LLM 更容易执行的人话简报。"""
    copy = style.copy_dna or {}
    visual = style.visual or {}

    voice = copy.get("voice", "治愈系温暖叙事")
    keywords = copy.get("keywords", [])
    sentence = copy.get("sentence_pattern", "短句为主，适度 emoji")
    hashtags = copy.get("hashtag_pattern", [])
    colors = visual.get("color_palette", [])
    materials = visual.get("material", [])
    lighting = visual.get("lighting", "")

    kw = "、".join(str(k) for k in keywords[:8]) if keywords else "（无）"
    ht = " ".join(str(h) for h in hashtags[:6]) if hashtags else "（无）"
    color_text = "、".join(str(c) for c in colors[:5]) if colors else "（无）"
    material_text = "、".join(str(m) for m in materials[:6]) if materials else "（无）"

    return (
        "【该账号文案风格 DNA —— 必须严格复刻】\n"
        f"- 整体语气：{voice}\n"
        f"- 高频关键词：{kw}\n"
        f"- 句式特点：{sentence}\n"
        f"- 惯用话题：{ht}\n\n"
        "【该账号视觉风格 DNA —— 用于校准图片描述】\n"
        f"- 主色：{color_text}\n"
        f"- 常见材质：{material_text}\n"
        f"- 光线：{lighting or '（无）'}\n"
    )


def _extract_floorplan_text(request: UserRequest) -> str:
    """优先用 user_notes；缺失时从 floorplan_meta 拼出最小可用户型 query。"""
    if request.user_notes and request.user_notes.strip():
        return request.user_notes.strip()

    meta = request.floorplan_meta or {}
    parts: list[str] = []
    if meta.get("area_sqm"):
        parts.append(f"面积约 {meta['area_sqm']}㎡")
    if meta.get("layout"):
        parts.append(f"户型为 {meta['layout']}")
    if meta.get("orientation"):
        parts.append(f"朝向 {meta['orientation']}")
    if not parts:
        return "客户希望获得一套兼顾美观、实用和收纳的家装设计方案。"
    return "，".join(parts) + "，希望获得一套兼顾美观、实用和收纳的家装设计方案。"


def _strip_markdown_fence(text: str) -> str:
    """剥掉 LLM 可能加的 ```json ... ``` 包裹。"""
    s = text.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        s = s[first_nl + 1 :] if first_nl != -1 else s[3:]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


def _parse_copy_json(text: str) -> dict:
    """LLM 输出 → CopyContent 兼容 dict，做字段和基础类型校验。"""
    data = json.loads(_strip_markdown_fence(text))

    if "title" not in data:
        raise ValueError("copy: 缺少字段 title")
    if "body" not in data:
        raise ValueError("copy: 缺少字段 body")
    if "hashtags" not in data:
        raise ValueError("copy: 缺少字段 hashtags")

    if not isinstance(data["title"], str) or not data["title"].strip():
        raise ValueError("copy: title 必须是非空字符串")
    if not isinstance(data["body"], str) or len(data["body"].strip()) < 20:
        raise ValueError("copy: body 必须是 ≥20 字的字符串")
    if not isinstance(data["hashtags"], list) or not data["hashtags"]:
        raise ValueError("copy: hashtags 必须是非空列表")

    hashtags = [str(h).strip() for h in data["hashtags"] if str(h).strip()]
    if not hashtags:
        raise ValueError("copy: hashtags 不能全为空")

    return {
        "title": data["title"].strip(),
        "body": data["body"].strip(),
        "hashtags": hashtags,
    }


async def _call_with_retry(
    call_fn: Callable[..., Awaitable[str]],
    parse_fn: Callable[[str], dict],
    mock_fallback: dict,
) -> dict:
    """3 级兜底链：JSON 错误让 LLM 自纠，HTTP/网络错误纯重试一次。"""
    try:
        return parse_fn(await call_fn())
    except (json.JSONDecodeError, ValueError) as e:
        try:
            return parse_fn(await call_fn(error_hint=str(e)))
        except Exception:
            return mock_fallback
    except Exception:
        await asyncio.sleep(5)
        try:
            return parse_fn(await call_fn())
        except Exception:
            return mock_fallback
