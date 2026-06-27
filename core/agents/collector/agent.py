"""
Agent 1 · 采集 Agent · 实现

负责人：A · Agent 工程师
契约 / 行为说明：见同目录 SKILL.md
"""

from datetime import datetime

from core.schemas import CollectedContent, CollectedPost, UserRequest


async def run(request: UserRequest) -> CollectedContent:
    """
    TODO 真实实现：
      1. 用 Smart Search 找该账号的 5-10 篇代表作 URL
      2. 对每个 URL 调 Reader API 拿 markdown + image_list
      3. 包装成 CollectedPost 列表
    """
    # === MOCK 实现：先保证主流程能跑通 ===
    return CollectedContent(
        target_account_id=request.target_account_id,
        posts=[
            CollectedPost(
                post_id="mock_001",
                title="Mock 标题：120 平复式改造",
                body="Mock 正文：原本只想做个简单装修...",
                image_urls=["https://placehold.co/600x800"],
                metadata={"source": "mock"},
            )
        ],
        collected_at=datetime.now(),
    )
