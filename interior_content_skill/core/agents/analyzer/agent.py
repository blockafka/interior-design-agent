"""Agent 2 · 风格分析 · 实现

负责人：kafka
契约：core/agents/analyzer/SKILL.md
开发笔记：docs/analyzer_dev_plan.md

实现要点：
- 样本筛选：按互动量降序取 Top 5（粉丝喜欢的笔记定义风格）
- 视觉 + 文案双通道并行调 LLM（asyncio.gather）
- 3 级兜底链：1st 调用 → 失败带错误反馈再调一次 → 仍失败用 _mocks 兜底
- image_url 同时接受 http URL 和 data:URI（生产/开发期切换零修改）
"""

import asyncio
import json
from typing import Any, Awaitable, Callable

from ...schemas import CollectedContent, CollectedPost, StyleDNA
from ....tools.llm import chat, chat_with_images

from ._mocks import MOCK_COPY, MOCK_VISUAL
from ._prompts import (
    COPY_SYSTEM_PROMPT,
    COPY_USER_PROMPT_TEMPLATE,
    VISUAL_SYSTEM_PROMPT,
    VISUAL_USER_PROMPT,
)

_TOP_K = 5
_MAX_IMAGES = 8
_BODY_TRUNCATE = 500


async def run(content: CollectedContent) -> StyleDNA:
    """analyzer 主入口（被 orchestrator / skill_loader 调用）。"""
    samples = _select_top_posts(content.posts, k=_TOP_K)
    visual, copy_dna = await asyncio.gather(
        _analyze_visual(samples),
        _analyze_copy(samples),
    )
    return StyleDNA(
        target_account_id=content.target_account_id,
        visual=visual,
        copy_dna=copy_dna,
        sample_post_ids=[p.post_id for p in samples],
    )


def _select_top_posts(posts: list[CollectedPost], k: int = _TOP_K) -> list[CollectedPost]:
    """按互动量降序取 Top K。score = likes + collects * 2（收藏含金量高于点赞）。"""

    def score(p: CollectedPost) -> int:
        m = p.metadata or {}
        return int(m.get("likes", 0) or 0) + int(m.get("collects", 0) or 0) * 2

    return sorted(posts, key=score, reverse=True)[:k]


async def _analyze_visual(posts: list[CollectedPost]) -> dict:
    """视觉通道：把 Top 5 篇的去重图片喂给多模态 LLM，提取风格 DNA。"""
    image_urls: list[str] = []
    seen: set[str] = set()
    for p in posts:
        for url in p.image_urls or []:
            if url in seen:
                continue
            seen.add(url)
            image_urls.append(url)
            if len(image_urls) >= _MAX_IMAGES:
                break
        if len(image_urls) >= _MAX_IMAGES:
            break

    if not image_urls:
        return MOCK_VISUAL

    async def call(error_hint: str | None = None) -> str:
        user_text = VISUAL_USER_PROMPT
        if error_hint:
            user_text += (
                f"\n\n【上一次输出格式错误】\n{error_hint}\n"
                "请严格按上方 JSON schema 重新输出，且不要带任何 markdown 代码块包裹。"
            )
        return await chat_with_images(
            system=VISUAL_SYSTEM_PROMPT,
            user_text=user_text,
            image_urls=image_urls,
        )

    return await _call_with_retry(call, _parse_visual_json, MOCK_VISUAL)


async def _analyze_copy(posts: list[CollectedPost]) -> dict:
    """文案通道：把 Top 5 篇的 title+body 拼起来给文本 LLM。"""
    if not posts:
        return MOCK_COPY

    packed_text = _pack_text(posts)
    user_prompt = COPY_USER_PROMPT_TEMPLATE.format(text=packed_text)

    async def call(error_hint: str | None = None) -> str:
        prompt = user_prompt
        if error_hint:
            prompt += (
                f"\n\n【上一次输出格式错误】\n{error_hint}\n"
                "请严格按上方 JSON schema 重新输出。"
            )
        return await chat(system=COPY_SYSTEM_PROMPT, user=prompt)

    return await _call_with_retry(call, _parse_copy_json, MOCK_COPY)


def _pack_text(posts: list[CollectedPost]) -> str:
    """把 Top 5 篇拼成单一文本块，body 截断防 token 爆炸。"""
    chunks: list[str] = []
    for i, p in enumerate(posts, 1):
        body = (p.body or "")[:_BODY_TRUNCATE]
        chunks.append(f"【笔记 {i}】\n标题：{p.title}\n正文：{body}")
    return "\n\n---\n\n".join(chunks)


def _strip_markdown_fence(text: str) -> str:
    """剥掉 LLM 可能加的 ```json ... ``` 包裹。"""
    s = text.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        s = s[first_nl + 1 :] if first_nl != -1 else s[3:]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


def _parse_visual_json(text: str) -> dict:
    data = json.loads(_strip_markdown_fence(text))
    required: dict[str, type] = {
        "color_palette": list,
        "material": list,
        "composition": str,
        "lighting": str,
    }
    for key, typ in required.items():
        if key not in data:
            raise ValueError(f"visual: 缺少字段 {key}")
        if not isinstance(data[key], typ):
            raise ValueError(f"visual: {key} 类型应为 {typ.__name__}")
    return data


def _parse_copy_json(text: str) -> dict:
    data = json.loads(_strip_markdown_fence(text))
    required: dict[str, type] = {
        "voice": str,
        "keywords": list,
        "sentence_pattern": str,
        "hashtag_pattern": list,
    }
    for key, typ in required.items():
        if key not in data:
            raise ValueError(f"copy: 缺少字段 {key}")
        if not isinstance(data[key], typ):
            raise ValueError(f"copy: {key} 类型应为 {typ.__name__}")
    return data


async def _call_with_retry(
    call_fn: Callable[..., Awaitable[str]],
    parse_fn: Callable[[str], dict],
    mock_fallback: dict,
) -> dict:
    """3 级兜底链：
    - JSON 解析错 → 带错误反馈再调一次（让 LLM 自纠）
    - HTTP / 网络错（429 限流、5xx、ReadError 等）→ sleep 5s 后纯重试一次
    - 仍失败 → MOCK 兜底（主链路永不挂）
    """
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
