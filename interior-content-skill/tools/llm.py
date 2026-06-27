"""统一 LLM 调用层（OpenAI 兼容协议 / 走 doubao-seed-2-0-pro-260215）

全队共用：analyzer / prompter / copywriter 等 Agent 通过此模块调 LLM，
避免每个 Agent 自建 client / 各自维护 retry & auth。

约定：
- chat()              纯文本对话
- chat_with_images()  多模态：user 同时含 text + image_url（http URL 或 data:URI 均可）
- 仅做单次 HTTP 调用，重试由调用方（analyzer 的 3 级兜底链）负责

环境变量：
- OPENAI_API_KEY     必填
- OPENAI_BASE_URL    可选，默认 https://api.openai-next.com/v1
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_BASE_URL = "https://api.openai-next.com/v1"
_DEFAULT_MODEL = "doubao-seed-2-0-pro-260215"


async def chat(
    *,
    system: str | None = None,
    user: str,
    model: str = _DEFAULT_MODEL,
    temperature: float = 0.7,
    timeout: float = 30.0,
) -> str:
    """纯文本对话，返回 assistant 的文本回复。"""
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    return await _call(messages, model, temperature, timeout)


async def chat_with_images(
    *,
    system: str | None = None,
    user_text: str,
    image_urls: list[str],
    model: str = _DEFAULT_MODEL,
    temperature: float = 0.7,
    timeout: float = 90.0,
) -> str:
    """多模态对话。image_urls 元素可同时为 http URL 或 'data:image/...;base64,...'。"""
    user_content: list[dict] = [{"type": "text", "text": user_text}]
    for url in image_urls:
        user_content.append({"type": "image_url", "image_url": {"url": url}})
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_content})
    return await _call(messages, model, temperature, timeout)


async def _call(messages: list[dict], model: str, temperature: float, timeout: float) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 未设置，请检查 .env")
    base_url = os.getenv("OPENAI_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")

    async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
