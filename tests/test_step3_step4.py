"""
Step 3 + Step 4 独立测试

直接用 mock 的 StyleDNA 和 UserRequest 喂入 prompter → generator，
验证 LLM 提示词生成 + 文生图调用是否跑通。

用法：在项目根目录执行
  python tests/test_step3_step4.py
"""

import asyncio
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from core.schemas import StyleDNA, UserRequest
from core.agents.prompter.agent import run as prompter_run
from core.agents.generator.agent import run as generator_run


async def main() -> None:
    # 模拟上游输入（和 analyzer_output_sample.json 一致）
    style = StyleDNA(
        target_account_id="xhs_jingyisuo",
        visual={
            "color_palette": ["奶油白", "原木色", "雾霾蓝"],
            "material": ["实木", "亚麻", "藤编", "陶瓷"],
            "composition": "对称构图为主，远近景结合，多用 45° 视角",
            "lighting": "自然光为主，下午斜光，无主灯设计",
        },
        copy={
            "voice": "治愈系，第一人称温暖叙事",
            "keywords": ["奶油风", "无主灯", "原木", "亚麻", "氛围感"],
            "sentence_pattern": "短句为主，emoji 点缀",
            "hashtag_pattern": ["#家装日记", "#奶油风", "#治愈系家居"],
        },
        sample_post_ids=["mock_001", "mock_002", "mock_003"],
    )

    request = UserRequest(
        target_account_id="xhs_jingyisuo",
        floorplan_image_url="",
        floorplan_meta={
            "area_sqm": 95,
            "rooms": "两室一厅",
            "space_type": "客厅",
            "orientation": "南北通透",
        },
        user_notes="想要温暖治愈的日系风格，预算有限但追求质感",
    )

    print("=" * 60)
    print("🚀 开始测试 Step 3（提示词工程）...")
    print("=" * 60)

    prompts = await prompter_run(style, request)

    print(f"\n✅ Step 3 完成！")
    print(f"  positive_prompt（前100字）: {prompts.positive_prompt[:100]}...")
    print(f"  negative_prompt（前50字）: {prompts.negative_prompt[:50]}...")
    print(f"  aspect_ratio: {prompts.aspect_ratio}")
    print(f"  prompt 总长度: {len(prompts.positive_prompt)} 字")

    print("\n" + "=" * 60)
    print("🚀 开始测试 Step 4（图片生成）... 这可能需要 30-60 秒")
    print("=" * 60)

    # 测试只生成 1 张图，节省时间和额度
    images = await generator_run(prompts, num_images=1)

    print(f"\n✅ Step 4 完成！")
    print(f"  生成图片数: {len(images.image_urls)}")
    for i, url in enumerate(images.image_urls):
        print(f"  图片 {i+1}: {url}")

    print("\n" + "=" * 60)
    print("🎉 Step 3 + Step 4 全部测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
