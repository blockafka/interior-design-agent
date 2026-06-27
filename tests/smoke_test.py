"""
端到端 Mock 冒烟测试

目的：验证从 UserRequest 到 FinalPost 的整条主链路骨架可跑通。
跑法：在项目根目录执行 `make smoke` 或 `python -m tests.smoke_test`
"""

import asyncio

from core.orchestrator import run
from core.schemas import UserRequest


async def main() -> None:
    request = UserRequest(
        target_account_id="境一所",
        floorplan_image_url="https://example.com/floorplan.jpg",
        floorplan_meta={"area_sqm": 120, "rooms": "三室两厅", "orientation": "南北通透"},
        user_notes="想要日系治愈风",
    )

    result = await run(request)

    print("=" * 60)
    print("✅ 端到端 Mock 跑通！")
    print("=" * 60)
    print(f"Request ID    : {result.request_id}")
    print(f"Target Account: {result.style_dna.target_account_id}")
    print(f"Title         : {result.copy.title}")
    print(f"Hashtags      : {result.copy.hashtags}")
    print(f"Images        : {result.images.image_urls}")
    print(f"Generated At  : {result.generated_at}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
