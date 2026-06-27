"""
Agent 4 · 图片生成 Agent · 实现

负责人：A · Agent 工程师
契约 / 行为说明：见同目录 SKILL.md
"""

from core.schemas import GeneratedImages, ImagePromptBundle


async def run(prompts: ImagePromptBundle, num_images: int = 3) -> GeneratedImages:
    """
    TODO 真实实现：
      1. 调用文生图 API（待选型：奇绩本地 SD / 即梦 / DALL-E）
      2. 拿到 num_images 张图的 URL
    """
    return GeneratedImages(
        image_urls=[f"https://placehold.co/600x800?text=Generated+{i+1}" for i in range(num_images)],
        prompts_used=prompts,
    )
