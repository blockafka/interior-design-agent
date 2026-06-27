"""用本地采集样例走主编排器，跳过尚未接入的 collector。

跑法：python -m tests.smoke_from_collect
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from core.orchestrator import run
from core.schemas import UserRequest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COLLECT_DIR = PROJECT_ROOT / "data" / "collect" / "厚来设计"

load_dotenv(PROJECT_ROOT / ".env")


async def main() -> None:
    request = UserRequest(
        target_account_id="厚来设计",
        floorplan_image_url="",
        floorplan_meta={
            "area_sqm": 180,
            "rooms": "四室两厅",
            "space_type": "客餐厅",
            "orientation": "南北通透",
            "target_customer": "三代同堂改善型家庭",
            "pain_points": "高级感不能冰冷，要兼顾长辈、孩子和年轻夫妻的互动",
        },
        user_notes=(
            "180㎡四室两厅，三代同堂改善住宅。客户希望有静奢老钱风的高级感，"
            "但不要酒店样板间式的冰冷；需要开放客餐厨、充足收纳、儿童活动空间，"
            "并照顾长辈日常动线。"
        ),
    )

    result = await run(request, collect_dir=str(COLLECT_DIR))

    print("=" * 60)
    print("✅ 主编排器非采集链路跑通！")
    print("=" * 60)
    print(f"Request ID     : {result.request_id}")
    print(f"Target Account : {result.style_dna.target_account_id}")
    print(f"Title          : {result.copy.title}")
    print(f"Hashtags       : {result.copy.hashtags}")
    print(f"Images         : {result.images.image_urls}")
    print(f"Generated At   : {result.generated_at}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
