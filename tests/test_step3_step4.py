"""
Step 3 + Step 4 独立测试

直接用 mock 的 StyleDNA 和 UserRequest 喂入 prompter → generator，
验证 LLM 提示词生成 + 文生图调用是否跑通。

用法：
  pytest tests/test_step3_step4.py -v
  或手动：python tests/test_step3_step4.py
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from core.schemas import StyleDNA, UserRequest
from core.agents.prompter.agent import run as prompter_run
from core.agents.generator.agent import run as generator_run


@pytest.fixture
def sample_style() -> StyleDNA:
    return StyleDNA(
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


@pytest.fixture
def sample_request() -> UserRequest:
    return UserRequest(
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


@pytest.mark.asyncio
async def test_step3_prompter(sample_style, sample_request):
    """Step 3：提示词工程 Agent 应返回有效的 ImagePromptBundle。"""
    prompts = await prompter_run(sample_style, sample_request)

    assert prompts.positive_prompt, "positive_prompt 不应为空"
    assert len(prompts.positive_prompt) > 50, "positive_prompt 长度应 > 50 字"
    assert prompts.negative_prompt, "negative_prompt 不应为空"
    assert prompts.aspect_ratio in ("3:4", "4:3", "1:1", "16:9", "9:16")


@pytest.mark.asyncio
async def test_step4_generator(sample_style, sample_request):
    """Step 4：图片生成 Agent 应返回至少 1 张图片 URL。"""
    prompts = await prompter_run(sample_style, sample_request)
    images = await generator_run(prompts, num_images=1)

    assert len(images.image_urls) == 1, "应生成 1 张图"
    assert images.image_urls[0].startswith(("http", "/static/")), "URL 格式不合法"
    assert images.prompts_used == prompts, "prompts_used 应原样回传"


@pytest.mark.asyncio
async def test_step3_step4_full_pipeline(sample_style, sample_request):
    """Step 3 → Step 4 完整链路：3 张图并发生成。"""
    prompts = await prompter_run(sample_style, sample_request)
    images = await generator_run(prompts, num_images=3)

    assert len(images.image_urls) == 3, "应生成 3 张图"
    for url in images.image_urls:
        assert url, "图片 URL 不应为空"


if __name__ == "__main__":
    import asyncio

    async def main():
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
            floorplan_meta={"area_sqm": 95, "rooms": "两室一厅", "space_type": "客厅", "orientation": "南北通透"},
            user_notes="想要温暖治愈的日系风格，预算有限但追求质感",
        )

        print("=" * 60)
        print("Step 3: 提示词工程...")
        prompts = await prompter_run(style, request)
        print(f"  positive_prompt（前100字）: {prompts.positive_prompt[:100]}...")
        print(f"  prompt 总长度: {len(prompts.positive_prompt)} 字")

        print("\nStep 4: 图片生成（1 张）...")
        images = await generator_run(prompts, num_images=1)
        print(f"  生成图片数: {len(images.image_urls)}")
        for i, url in enumerate(images.image_urls):
            print(f"  图片 {i+1}: {url}")
        print("=" * 60)

    asyncio.run(main())
