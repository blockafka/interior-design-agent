"""
Agent 2 · 风格分析 Agent

职责：从 CollectedContent 提取「风格 DNA」（StyleDNA）。
      包括视觉风格（色调 / 材质 / 构图 / 光线）+ 文案风格（语气 / 句式 / Hashtag）。

输入：CollectedContent
输出：StyleDNA
依赖工具：tools/llm.py（视觉模型 + 文本模型）

负责人：A · Agent 工程师
"""

from core.schemas import CollectedContent, StyleDNA


async def analyze(content: CollectedContent) -> StyleDNA:
    """
    TODO 真实实现：
      1. 视觉通道：GPT-4V / Claude Vision 分析 image_urls
      2. 文案通道：LLM 分析 body 提取语气 / 关键词 / Hashtag 模式
      3. 合并输出结构化 JSON
    """
    return StyleDNA(
        target_account_id=content.target_account_id,
        visual={
            "color_palette": ["#F5E6D3", "#8B6F47", "#E8DCC4"],
            "material": ["实木", "亚麻", "棉布"],
            "composition": "对称构图，黄金分割",
            "lighting": "暖色自然光，柔和漫射",
        },
        copy={
            "voice": "治愈系，温暖叙事",
            "keywords": ["居家", "温暖", "治愈", "日系"],
            "hashtag_pattern": ["#家装日记", "#日系装修", "#治愈系家居"],
        },
        sample_post_ids=[p.post_id for p in content.posts],
    )
