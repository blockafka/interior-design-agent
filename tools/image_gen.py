"""
文生图 API 封装

待 kafka 选型：
  - A. 奇绩算力本地 SD / Flux / HiDream
  - B. 云端 API（火山即梦 / Doubao Image）
  - C. 微软 credits（DALL-E / Sora-Image）

通过环境变量 IMAGE_GEN_PROVIDER 切换：
  mock / sd_local / jimeng / dalle

提供：
- text_to_image(prompt, negative_prompt, aspect_ratio) → image_url

负责人：A · Agent 工程师
"""

import os


async def text_to_image(
    prompt: str,
    negative_prompt: str = "",
    aspect_ratio: str = "3:4",
) -> str:
    """
    TODO 真实实现：
      provider = os.getenv("IMAGE_GEN_PROVIDER", "mock")
      if provider == "sd_local":   ...
      elif provider == "jimeng":   ...
      elif provider == "dalle":    ...
      else:                        return mock placeholder
    """
    return "https://placehold.co/600x800?text=Generated+Image"  # MOCK
