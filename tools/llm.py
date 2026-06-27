"""
LLM 统一 client（屏蔽 Gemini / Claude / GPT / Doubao 差异）

提供：
- chat(messages, model=None)       → 文本回复
- vision(image_url, prompt, ...)   → 多模态视觉理解（占位 mock）

provider 通过环境变量 LLM_PROVIDER 切换：
    mock / gemini / anthropic / openai / doubao
当前仅实现 mock + gemini，其它 provider 走 mock 兜底。

负责人：A · Agent 工程师
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------
def _messages_to_prompt(messages: list[dict]) -> str:
    """把 OpenAI 风格 messages 拍平为单个 prompt 字符串（喂给 Gemini）。"""
    parts: list[str] = []
    for msg in messages:
        role = (msg.get("role") or "user").lower()
        content = msg.get("content") or ""
        if not content:
            continue
        if role == "system":
            parts.append(f"[系统指令]\n{content}")
        elif role == "assistant":
            parts.append(f"[助手历史回复]\n{content}")
        else:
            parts.append(f"[用户输入]\n{content}")
    return "\n\n".join(parts) if parts else ""


def _mock_chat() -> str:
    """所有 provider 调用失败 / 未配置时的兜底返回。"""
    return "MOCK LLM 输出"


# ---------------------------------------------------------------
# 对外 API
# ---------------------------------------------------------------
async def chat(messages: list[dict], model: str | None = None) -> str:
    """
    统一文本对话接口。

    Args:
        messages: OpenAI 风格的消息列表，每项形如 {"role": "system|user|assistant", "content": "..."}
        model:    可选模型 override；不传则读环境变量默认值。

    Returns:
        模型回复纯文本。出错或未配置时返回 mock 文本，不抛异常。
    """
    provider = (os.getenv("LLM_PROVIDER", "mock") or "mock").lower()

    if provider == "gemini":
        return await _gemini_chat(messages, model)

    # 其它 provider（anthropic / openai / doubao）暂未接入，统一走 mock
    if provider != "mock":
        logger.warning("LLM_PROVIDER=%s 尚未实现，降级到 mock", provider)
    return _mock_chat()


async def vision(image_url: str, prompt: str, model: str | None = None) -> str:
    """
    多模态视觉理解（kafka 的 analyzer 后续会接入）。当前保持 mock。
    """
    return "MOCK 视觉分析"


# ---------------------------------------------------------------
# Gemini 实现
# ---------------------------------------------------------------
async def _gemini_chat(messages: list[dict], model: str | None) -> str:
    try:
        from google import genai  # type: ignore
    except Exception as exc:  # ImportError 或环境问题
        logger.error("google-genai 未安装，降级到 mock：%s", exc)
        return _mock_chat()

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning("GEMINI_API_KEY 未配置，降级到 mock")
        return _mock_chat()

    target_model = model or os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-pro")
    prompt = _messages_to_prompt(messages)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=target_model,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if not text:
            logger.warning("Gemini 返回空文本，降级到 mock")
            return _mock_chat()
        return text
    except Exception as exc:
        logger.error("Gemini chat 调用失败，降级到 mock：%s", exc)
        return _mock_chat()
