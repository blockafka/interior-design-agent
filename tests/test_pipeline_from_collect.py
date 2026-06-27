"""从本地采集样例开始，跑通 analyzer → prompter → generator → copywriter。

用途：采集 Agent 尚未接入时，用 data/collect/<账号> 的文件夹作为 Step 1 输出。
跑法：python -m tests.test_pipeline_from_collect
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from core.agents.analyzer.agent import run as analyzer_run
from core.agents.copywriter.agent import run as copywriter_run
from core.agents.generator.agent import run as generator_run
from core.agents.prompter.agent import run as prompter_run
from core.collect_loader import load_collected_content
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
            "pain_points": "想要高级感但不能冰冷，要兼顾长辈、孩子和年轻夫妻的互动",
        },
        user_notes=(
            "180㎡四室两厅，三代同堂改善住宅。客户希望有静奢老钱风的高级感，"
            "但不要酒店样板间式的冰冷；需要开放客餐厨、充足收纳、儿童活动空间，"
            "并照顾长辈日常动线。"
        ),
    )

    content = load_collected_content(COLLECT_DIR, target_account_id=request.target_account_id)
    style = await analyzer_run(content)
    prompts = await prompter_run(style, request)
    images = await generator_run(prompts, num_images=1)
    copy = await copywriter_run(style, images, request)

    print("=" * 60)
    print("✅ 非采集链路跑通：collect folder → analyzer → prompter → generator → copywriter")
    print("=" * 60)
    print(f"Target Account : {style.target_account_id}")
    print(f"Sample Posts   : {style.sample_post_ids}")
    print(f"Visual DNA     : {style.visual}")
    print(f"Copy Voice     : {style.copy.get('voice')}")
    print(f"Prompt Length  : {len(prompts.positive_prompt)}")
    print(f"Images         : {images.image_urls}")
    print(f"Title          : {copy.title}")
    print(f"Hashtags       : {copy.hashtags}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
