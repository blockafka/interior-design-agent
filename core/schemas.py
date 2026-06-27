"""
接口契约 (Pydantic Schemas)

【极其重要】所有 Agent / 模块之间的数据传递必须使用这里定义的类型。
任何对本文件的修改必须先在群里通知所有人，避免破坏他人的代码。

数据流：
    UserRequest
        → 采集 Agent       → CollectedContent
        → 风格分析 Agent   → StyleDNA
        → 提示词 Agent     → ImagePromptBundle
        → 图片生成 Agent   → GeneratedImages
        → 文案 Agent       → CopyContent
        → 主编排器         → FinalPost
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# 用户输入（前端 → 后端入口）
# ============================================================
class UserRequest(BaseModel):
    target_account_id: str
    floorplan_image_url: str
    floorplan_meta: dict = Field(default_factory=dict)
    user_notes: Optional[str] = None


# ============================================================
# Agent 1 · 采集
# ============================================================
class CollectedPost(BaseModel):
    post_id: str
    title: str
    body: str
    image_urls: list[str]
    metadata: dict = Field(default_factory=dict)


class CollectedContent(BaseModel):
    target_account_id: str
    posts: list[CollectedPost]
    collected_at: datetime


# ============================================================
# Agent 2 · 风格分析
# ============================================================
class StyleDNA(BaseModel):
    target_account_id: str
    visual: dict  # color_palette / material / composition / lighting
    copy: dict    # voice / keywords / hashtag_pattern
    sample_post_ids: list[str]


# ============================================================
# Agent 3 · 提示词工程
# ============================================================
class ImagePromptBundle(BaseModel):
    positive_prompt: str
    negative_prompt: str
    aspect_ratio: str = "3:4"


# ============================================================
# Agent 4 · 图片生成
# ============================================================
class GeneratedImages(BaseModel):
    image_urls: list[str]
    prompts_used: ImagePromptBundle


# ============================================================
# Agent 5 · 文案
# ============================================================
class CopyContent(BaseModel):
    title: str
    body: str
    hashtags: list[str]


# ============================================================
# 最终输出（后端 → 前端响应）
# ============================================================
class FinalPost(BaseModel):
    request_id: str
    style_dna: StyleDNA
    images: GeneratedImages
    copy: CopyContent
    generated_at: datetime
