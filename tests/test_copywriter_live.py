"""真实跑 copywriter（吃真 doubao 多模态），打印 CopyContent。

开发期数据：手写 STYLE_DNA_MOCKS（风格）+ material/<style>/ 设计图（视觉）+ 编的户型。
三者风格严格联动，验证「文案复刻账号语气 + 描述了图里真实元素 + 服务获客营销」。
"""

import asyncio
import base64
import io
import os
from pathlib import Path

from PIL import Image

from core.agents.copywriter.agent import run
from core.schemas import GeneratedImages, ImagePromptBundle, StyleDNA, UserRequest

MATERIAL_DIR = Path(
    "/Users/kafka/Desktop/files/bussiness_test/Hackathon/Beyond Prompt: Agents in Action/material"
)
TEST_STYLE = os.getenv("TEST_STYLE", "日式原木")

STYLE_DNA_MOCKS = {
    "日式原木": StyleDNA(
        target_account_id="xhs_yuanmuwu",
        visual={
            "color_palette": ["原木棕", "米白", "浅灰"],
            "material": ["橡木", "白蜡木", "亚麻", "藤编"],
            "composition": "大面积留白，绿植点缀，对称弱",
            "lighting": "漫射柔光为主，无主灯",
        },
        copy={
            "voice": "治愈系第一人称温暖叙事，强调被治愈的日常感",
            "keywords": ["原木", "藤编", "亚麻", "治愈", "漫射光", "绿植", "温润"],
            "sentence_pattern": "短句为主，感叹号适度，emoji 点缀（🌿✨）",
            "hashtag_pattern": ["#日式原木", "#家装日记", "#治愈系家居", "#原木风装修", "#无印良品风"],
        },
        sample_post_ids=["xhs_001_riyuan", "xhs_002_riyuan", "xhs_003_riyuan"],
    ),
    "新中式": StyleDNA(
        target_account_id="xhs_dongfangyun",
        visual={
            "color_palette": ["深胡桃棕", "月白", "黄铜金"],
            "material": ["黑胡桃木", "绒布", "黄铜", "岩板"],
            "composition": "留白为主，对称构图，水墨点缀",
            "lighting": "暖光为主，铜灯营造仪式感",
        },
        copy={
            "voice": "雅致内敛，讲分寸感与留白的艺术",
            "keywords": ["黑胡桃", "月白", "黄铜", "茶室", "留白", "分寸感", "新中式"],
            "sentence_pattern": "长短句结合，文气偏重，少 emoji",
            "hashtag_pattern": ["#新中式", "#茶室", "#黑胡桃", "#中式美学", "#家装日记"],
        },
        sample_post_ids=["xhs_001_zhongshi", "xhs_002_zhongshi", "xhs_003_zhongshi"],
    ),
    "极简自然风": StyleDNA(
        target_account_id="xhs_qingjianjia",
        visual={
            "color_palette": ["雾灰白", "燕麦", "卡其", "冷灰"],
            "material": ["微水泥", "原木", "棉麻"],
            "composition": "极致留白，少即是多，单点聚焦",
            "lighting": "无主灯，线性光",
        },
        copy={
            "voice": "克制理性，讲少即是多的生活方式",
            "keywords": ["极简", "雾灰白", "微水泥", "留白", "少即是多", "高级灰"],
            "sentence_pattern": "短句果断，少感叹号，几乎无 emoji",
            "hashtag_pattern": ["#极简风", "#微水泥", "#少即是多", "#极简主义", "#家装日记"],
        },
        sample_post_ids=["xhs_001_jijian", "xhs_002_jijian", "xhs_003_jijian"],
    ),
    "法式中古风": StyleDNA(
        target_account_id="xhs_zhongguyou",
        visual={
            "color_palette": ["奶油白", "脏粉", "胡桃棕", "湖蓝"],
            "material": ["天鹅绒", "橡木人字拼", "黄铜", "石膏线条"],
            "composition": "氛围感构图，复古单品为 C 位",
            "lighting": "暖黄光，铜烛台/壁灯营造氛围",
        },
        copy={
            "voice": "浪漫叙事，讲氛围感与时间痕迹的故事",
            "keywords": ["法式中古", "人字拼", "脏粉", "天鹅绒", "氛围感", "复古"],
            "sentence_pattern": "长句铺陈，感叹号多，emoji 偏浪漫（🤎🕯️）",
            "hashtag_pattern": ["#法式中古", "#复古风", "#人字拼", "#氛围感", "#家装日记"],
        },
        sample_post_ids=["xhs_001_fashi", "xhs_002_fashi", "xhs_003_fashi"],
    ),
}


def _build_mock_request(style: str) -> UserRequest:
    return UserRequest(
        target_account_id=STYLE_DNA_MOCKS[style].target_account_id,
        floorplan_image_url="",
        floorplan_meta={"area_sqm": 89, "layout": "两室一厅", "orientation": "南向"},
        user_notes=(
            "89㎡ 两室一厅，南北通透，南向主卧。"
            "常住一对年轻夫妻 + 一只猫，近一两年准备要小孩。"
            "希望整体温馨治愈、收纳充足、给猫留活动空间，预算 12-15 万。"
        ),
    )


def _local_image_to_data_uri(path: Path) -> str:
    """本地图 → base64 data URI；预压缩避免 doubao 网关拒收大 payload。"""
    img = Image.open(path).convert("RGB")
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def _build_mock_design_images(style: str) -> GeneratedImages:
    style_dir = MATERIAL_DIR / style
    urls = [
        _local_image_to_data_uri(p)
        for p in sorted(style_dir.iterdir())
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    ]
    return GeneratedImages(
        image_urls=urls,
        prompts_used=ImagePromptBundle(positive_prompt="[mock]", negative_prompt="[mock]"),
    )


async def main() -> None:
    if TEST_STYLE not in STYLE_DNA_MOCKS:
        raise ValueError(f"TEST_STYLE 不支持：{TEST_STYLE}")

    style_dna = STYLE_DNA_MOCKS[TEST_STYLE]
    images = _build_mock_design_images(TEST_STYLE)
    request = _build_mock_request(TEST_STYLE)

    copy = await run(style_dna, images, request)
    print(f"=== 测试风格：{TEST_STYLE} ===")
    print(f"标题：{copy.title}")
    print(f"\n正文：\n{copy.body}")
    print(f"\n话题：{' '.join(copy.hashtags)}")


if __name__ == "__main__":
    asyncio.run(main())
