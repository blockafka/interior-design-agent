"""
Step 3 + Step 4 多场景批量测试

测试多种风格，每种生成 3 张图，结果存入 data/generated/ 和 examples/generated_samples/
"""

import asyncio
import io
import json
import shutil
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from core.schemas import StyleDNA, UserRequest
from core.agents.prompter.agent import run as prompter_run
from core.agents.generator.agent import run as generator_run

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples" / "generated_samples"


SCENARIOS = [
    {
        "name": "日系治愈风_客厅",
        "style": StyleDNA(
            target_account_id="xhs_jingyisuo",
            visual={
                "color_palette": ["奶油白", "原木色", "雾霾蓝"],
                "material": ["实木", "亚麻", "藤编", "陶瓷"],
                "composition": "对称构图为主，远近景结合，多用 45 度视角",
                "lighting": "自然光为主，下午斜光，无主灯设计",
            },
            copy={
                "voice": "治愈系，第一人称温暖叙事",
                "keywords": ["奶油风", "无主灯", "原木", "亚麻", "氛围感"],
                "sentence_pattern": "短句为主，emoji 点缀",
                "hashtag_pattern": ["#家装日记", "#奶油风", "#治愈系家居"],
            },
            sample_post_ids=["mock_001", "mock_002", "mock_003"],
        ),
        "request": UserRequest(
            target_account_id="xhs_jingyisuo",
            floorplan_image_url="",
            floorplan_meta={"area_sqm": 95, "rooms": "两室一厅", "space_type": "客厅", "orientation": "南北通透"},
            user_notes="想要温暖治愈的日系风格，预算有限但追求质感",
        ),
    },
    {
        "name": "现代极简风_主卧",
        "style": StyleDNA(
            target_account_id="xhs_mofa",
            visual={
                "color_palette": ["高级灰", "纯白", "黑色", "金属色"],
                "material": ["大理石", "金属", "玻璃", "皮革"],
                "composition": "极简线条，大面积留白，低角度视角",
                "lighting": "大面积落地窗自然光，线性灯带辅助",
            },
            copy={
                "voice": "克制冷静，专业设计师视角",
                "keywords": ["极简", "高级灰", "大理石", "线条感", "轻奢"],
                "sentence_pattern": "长句描述细节，专业术语",
                "hashtag_pattern": ["#极简主义", "#现代风", "#轻奢设计"],
            },
            sample_post_ids=["mock_004", "mock_005", "mock_006"],
        ),
        "request": UserRequest(
            target_account_id="xhs_mofa",
            floorplan_image_url="",
            floorplan_meta={"area_sqm": 140, "rooms": "三室两厅", "space_type": "主卧", "orientation": "朝南"},
            user_notes="追求极简高级感，不要过多装饰，要有酒店套房的感觉",
        ),
    },
    {
        "name": "法式复古风_餐厅",
        "style": StyleDNA(
            target_account_id="xhs_houlaishili",
            visual={
                "color_palette": ["脏粉", "墨绿", "鹅黄", "复古金"],
                "material": ["丝绒", "黄铜", "石膏线", "实木雕花"],
                "composition": "中心对称，强调纵深感，仰角拍摄突出层高",
                "lighting": "复古吊灯为主光源，烛光氛围，暖黄调",
            },
            copy={
                "voice": "浪漫优雅，带故事感的描述",
                "keywords": ["法式", "复古", "丝绒", "黄铜", "石膏线", "vintage"],
                "sentence_pattern": "诗意长句，比喻修辞丰富",
                "hashtag_pattern": ["#法式装修", "#复古风", "#浪漫家居", "#vintage"],
            },
            sample_post_ids=["mock_007", "mock_008", "mock_009"],
        ),
        "request": UserRequest(
            target_account_id="xhs_houlaishili",
            floorplan_image_url="",
            floorplan_meta={"area_sqm": 120, "rooms": "三室一厅", "space_type": "餐厅", "orientation": "朝西", "target_customer": "年轻夫妻"},
            user_notes="喜欢法式复古，想要有仪式感的用餐空间，层高 3.2 米",
        ),
    },
]


async def run_scenario(scenario: dict, index: int) -> dict:
    name = scenario["name"]
    print(f"\n{'='*60}")
    print(f"[场景 {index+1}] {name}")
    print(f"{'='*60}")

    # Step 3
    print(f"  Step 3: 生成提示词中...")
    prompts = await prompter_run(scenario["style"], scenario["request"])
    print(f"  Step 3 完成! prompt 长度: {len(prompts.positive_prompt)} 字")
    print(f"  prompt 前80字: {prompts.positive_prompt[:80]}...")

    # Step 4 (3 张图)
    print(f"  Step 4: 生成 3 张图中（预计 1-2 分钟）...")
    images = await generator_run(prompts, num_images=3)
    print(f"  Step 4 完成! 生成 {len(images.image_urls)} 张图")
    for i, url in enumerate(images.image_urls):
        print(f"    图 {i+1}: {url}")

    return {
        "scenario_name": name,
        "positive_prompt": prompts.positive_prompt,
        "negative_prompt": prompts.negative_prompt,
        "aspect_ratio": prompts.aspect_ratio,
        "image_urls": images.image_urls,
    }


async def main() -> None:
    print("=" * 60)
    print("Step 3 + Step 4 多场景批量测试")
    print(f"共 {len(SCENARIOS)} 个场景，每个生成 3 张图")
    print("=" * 60)

    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    for i, scenario in enumerate(SCENARIOS):
        result = await run_scenario(scenario, i)
        all_results.append(result)

        # 把生成的图片复制到 examples/generated_samples/
        for j, url in enumerate(result["image_urls"]):
            if url.startswith("/static/generated/"):
                filename = url.split("/")[-1]
                src = PROJECT_ROOT / "data" / "generated" / filename
                if src.exists():
                    dst_name = f"{scenario['name']}_{j+1}.png"
                    dst = EXAMPLES_DIR / dst_name
                    shutil.copy2(src, dst)
                    print(f"  -> 已复制到 examples/generated_samples/{dst_name}")

    # 保存完整结果 JSON
    results_file = EXAMPLES_DIR / "test_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n{'='*60}")
    print(f"全部完成! 结果汇总: examples/generated_samples/test_results.json")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
