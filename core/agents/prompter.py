"""
Agent 3 · 提示词工程 Agent

职责：把 StyleDNA + 户型信息反推为可用于文生图的 prompt 套件（正向 + 负向）。

输入：StyleDNA + UserRequest（含 floorplan_meta）
输出：ImagePromptBundle
依赖工具：tools/llm.py

负责人：A · Agent 工程师
"""

from core.schemas import ImagePromptBundle, StyleDNA, UserRequest


async def build_prompt(style: StyleDNA, request: UserRequest) -> ImagePromptBundle:
    """
    TODO 真实实现：
      1. 把 StyleDNA.visual 翻译成自然语言描述
      2. 拼上户型信息（户型类型 / 面积 / 朝向）
      3. 套上通用模板（photorealistic / 4K / 无人物 / 无文字 / 无 logo）
    """
    return ImagePromptBundle(
        positive_prompt=(
            "现代自然木质风复式客厅家居室内设计，真实住宅实拍摄影质感，"
            "高端家装广告图，3:4 竖版构图，photorealistic，4K，sharp focus，"
            "无人物，无文字，无 logo"
        ),
        negative_prompt=(
            "低清晰度，模糊，卡通，动漫，CG感，塑料质感，过度渲染，"
            "曝光过度，家具变形，透视错误，鱼眼畸变，噪点，文字，logo，水印，人物"
        ),
        aspect_ratio="3:4",
    )
