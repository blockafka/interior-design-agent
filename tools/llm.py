"""
LLM 统一 client（屏蔽 Claude / GPT / Doubao 差异）

提供：
- chat(messages, model=None)       → 文本回复
- vision(image_url, prompt, ...)   → 多模态视觉理解

负责人：A · Agent 工程师
"""

import os


async def chat(messages: list[dict], model: str | None = None) -> str:
    """
    TODO 真实实现：
      根据 LLM_PROVIDER 环境变量选择 Anthropic / OpenAI / Doubao SDK
      统一返回 assistant 的文本回复
    """
    return "MOCK LLM 输出"


async def vision(image_url: str, prompt: str, model: str | None = None) -> str:
    """
    TODO 真实实现：
      调用支持多模态的模型（GPT-4V / Claude Vision / Gemini Vision）
      返回模型对图片的描述 / 分析结果
    """
    return "MOCK 视觉分析"
