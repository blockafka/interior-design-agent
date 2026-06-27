"""
Agent 2 · 风格分析 Agent · 实现

负责人：kafka
契约 / 行为说明 / 实现思路：见同目录 SKILL.md
对接 JSON 样例：见 examples/analyzer_input_sample.json / analyzer_output_sample.json
"""

from core.schemas import CollectedContent, StyleDNA


async def run(content: CollectedContent) -> StyleDNA:
    """
    TODO（kafka 负责实现）：
      1. 视觉通道：GPT-4V / Claude Vision 分析 image_urls
      2. 文案通道：LLM 分析 body 提取语气 / 关键词 / Hashtag 模式
      3. 合并输出结构化 JSON
    """
    # === MOCK 实现：暂时返回硬编码 DNA，让主流程能跑通 ===
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
            "sentence_pattern": "短句为主，emoji 点缀",
            "hashtag_pattern": ["#家装日记", "#日系装修", "#治愈系家居"],
        },
        sample_post_ids=[p.post_id for p in content.posts],
    )
