"""
Agent 5 · 文案 Agent · 实现

负责人：A · Agent 工程师
契约 / 行为说明：见同目录 SKILL.md
"""

from core.schemas import CopyContent, GeneratedImages, StyleDNA, UserRequest


async def run(
    style: StyleDNA,
    images: GeneratedImages,
    request: UserRequest,
) -> CopyContent:
    """
    TODO 真实实现：
      1. 用 StyleDNA.copy 作为风格指令（voice / keywords / hashtag_pattern）
      2. 让 LLM 生成符合该账号语气的标题 / 正文
      3. 套上该账号常用的 Hashtag 模式
    """
    return CopyContent(
        title="我家这间小客厅，被设计师改成了梦里的样子",
        body=(
            "120 平复式，原本只想做个简单装修。\n"
            "没想到设计师把它做成了一首温柔的诗。\n"
            "实木 + 亚麻 + 暖光，治愈系日常感拉满。"
        ),
        hashtags=style.copy.get("hashtag_pattern", ["#家装日记", "#日系装修"]),
    )
