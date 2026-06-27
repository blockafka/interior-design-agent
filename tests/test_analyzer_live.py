"""真实跑 analyzer（吃真 LLM），打印 StyleDNA。

开发期数据：本地维护的 STYLE_FIXTURES（文案）+ material/<style>/ 本地图（视觉），
两者风格严格配对，保证 analyzer 拿到的输入不打架。

跑法：
    cd interior-design-agent
    python -m tests.test_analyzer_live
    TEST_STYLE=新中式 python -m tests.test_analyzer_live   # 切风格

切换风格：改文件底部 TEST_STYLE 常量，或用 TEST_STYLE 环境变量覆盖。
"""

import asyncio
import base64
import io
import os
from datetime import datetime
from pathlib import Path

from PIL import Image

from core.agents.analyzer.agent import run
from core.schemas import CollectedContent, CollectedPost


MATERIAL_DIR = Path(
    "/Users/kafka/Desktop/files/bussiness_test/Hackathon/Beyond Prompt: Agents in Action/material"
)
TEST_STYLE = os.environ.get("TEST_STYLE", "日式原木")  # 可切换：新中式 / 极简自然风 / 法式中古风


# ============================================================
# 4 套配对 fixture —— 文案描述的色彩 / 材质 / 氛围词与 material/<style>/ 图视觉一致
# ============================================================
STYLE_FIXTURES: dict[str, dict] = {
    "新中式": {
        "target_account_id": "xhs_dongfangyun",
        "posts": [
            {
                "post_id": "xhs_001_zhongshi",
                "title": "100㎡新中式，黑胡桃 + 月白绒布把家做成了茶室",
                "body": "终于装完啦！新中式最难的就是分寸感，多一分老气、少一分单薄。我家选了黑胡桃木做主调，月白色绒布沙发压住调子，黄铜把手做点缀。客厅墙面留白只挂了一幅水墨，地面铺哑光大理石。最爱玄关那盏铜灯，傍晚开起来整个家都暖了。新中式不是堆元素，是留白的艺术。",
                "metadata": {"likes": 9821, "comments": 312, "collects": 4502, "publish_time": "2026-04-12"},
            },
            {
                "post_id": "xhs_002_zhongshi",
                "title": "茶室角一平米，把日子过出诗意",
                "body": "家里硬挤出来的茶室角，黑胡桃矮几 + 月白蒲团 + 一盏铜壶。墙上挂水墨小品，旁边搁支白瓷瓶。每天泡杯茶坐这里读半小时书，整个人都松了。新中式真的是中国人骨子里的审美，不需要懂多少，喜欢就够了。",
                "metadata": {"likes": 6234, "comments": 198, "collects": 3210, "publish_time": "2026-05-03"},
            },
            {
                "post_id": "xhs_003_zhongshi",
                "title": "玄关黄铜把手细节，新中式的灵魂在五金件",
                "body": "全屋装修最值的就是把柜门把手全换成黄铜。一开始觉得只是细节，住进来发现真不一样——每次开柜门都有点小仪式感。新中式的灵魂从来不在大件家具，而在五金、灯具、画轴这些不起眼的地方。",
                "metadata": {"likes": 5872, "comments": 145, "collects": 2891, "publish_time": "2026-05-28"},
            },
        ],
    },
    "日式原木": {
        "target_account_id": "xhs_yuanmuwu",
        "posts": [
            {
                "post_id": "xhs_001_riyuan",
                "title": "85㎡日式原木风，全屋都是治愈感",
                "body": "日式原木风装下来真的太爱了。全屋大量原木：橡木餐桌、白蜡木衣柜、藤编置物架。墙面统一刷白，地板浅色橡木复合地板。窗帘亚麻材质，下午阳光透过来是漫射的柔和感。家里几乎没有装饰画，但每个角落都摆了绿植——龟背竹、琴叶榕、玉露。极简但不冷，住进来每天心情都好。",
                "metadata": {"likes": 8765, "comments": 234, "collects": 4123, "publish_time": "2026-04-20"},
            },
            {
                "post_id": "xhs_002_riyuan",
                "title": "客厅藤编 + 漫射光，下班回来瘫一晚",
                "body": "客厅最爱的两样：藤编沙发椅 + 一盏纸灯。纸灯的漫射光特别治愈，亮但不刺眼。沙发椅藤编面坐久不闷，软垫是亚麻面料。日式风的精髓就是材质——原木、藤、亚麻、纸，全是温润的天然材质，呆久了真的会有种被治愈的感觉。无印良品风没有错。",
                "metadata": {"likes": 6543, "comments": 167, "collects": 3287, "publish_time": "2026-05-10"},
            },
            {
                "post_id": "xhs_003_riyuan",
                "title": "卧室白蜡木衣柜定制完，温柔感拉满",
                "body": "纠结很久最后选了白蜡木做衣柜，价格比板材贵一倍但真的值。木纹清晰、颜色温润，跟整屋原木调完全融为一体。柜门是无把手设计，干净利落。床头摆一盏小台灯，亚麻床品，墙上贴一幅暖色挂画。日式不是性冷淡，是温暖的克制。",
                "metadata": {"likes": 5421, "comments": 132, "collects": 2654, "publish_time": "2026-05-25"},
            },
        ],
    },
    "极简自然风": {
        "target_account_id": "xhs_qingjianjia",
        "posts": [
            {
                "post_id": "xhs_001_jijian",
                "title": "极简控的全屋自然色系，每天都像在度假",
                "body": "极简自然风，不堆砌不复杂。墙面雾灰白乳胶漆，地板灰咖色微水泥。家具走 less is more 路线：一张大沙发、一张长餐桌、一盏垂吊灯。色彩控制在米白、灰、卡其、燕麦色 4 个色域里。最重要的是大量留白，让空间自己呼吸。住进来才明白，少即是多不是口号，是生活方式。",
                "metadata": {"likes": 11234, "comments": 421, "collects": 5872, "publish_time": "2026-04-05"},
            },
            {
                "post_id": "xhs_002_jijian",
                "title": "雾灰白墙 + 微水泥地，高级感从基础开始",
                "body": "整屋只用两种基础色：墙面雾灰白、地面微水泥灰咖。看似单调，住进来才知道是高级感的基础。没有花花绿绿的硬装、没有复杂线条、没有过度装饰。家具家电的色彩都自动收敛进这个体系。极简风的难点不在加什么，而在敢减什么。",
                "metadata": {"likes": 7892, "comments": 256, "collects": 3654, "publish_time": "2026-05-08"},
            },
            {
                "post_id": "xhs_003_jijian",
                "title": "高级灰客厅，留白才是真奢华",
                "body": "客厅整体高级灰调，沙发燕麦色，地毯卡其色。墙上没有挂画，留了大面积空白。茶几上只放一本书 + 一支花瓶。极简从来不是空，是精挑细选每一件物品。每个出现在视野里的东西都必须有理由。住进来三个月，反而越来越不想买东西了。",
                "metadata": {"likes": 6321, "comments": 187, "collects": 3012, "publish_time": "2026-06-01"},
            },
        ],
    },
    "法式中古风": {
        "target_account_id": "xhs_zhongguyou",
        "posts": [
            {
                "post_id": "xhs_001_fashi",
                "title": "复古法式中古风改造完工！每个角落都像油画",
                "body": "法式中古风真的让家有了灵魂。墙面用脏粉色 + 法式护墙板线条，地板做人字拼鱼骨地板，颜色偏暗的橡木。家具全部是中古单品：复古天鹅绒沙发、雕花木桌、铜质烛台。配上几幅油画和老式挂钟。每个细节都在讲故事，氛围感无敌。法式中古最迷人的就是时间的痕迹，新东西做不出来。",
                "metadata": {"likes": 14523, "comments": 587, "collects": 7234, "publish_time": "2026-03-28"},
            },
            {
                "post_id": "xhs_002_fashi",
                "title": "人字拼鱼骨地板 + 脏粉色墙，复古感的关键",
                "body": "整屋装修最贵也最值的就是人字拼地板。深色橡木做人字拼，配脏粉色护墙板，复古感瞬间到位。法式中古不是法式简约，要的就是这种带年代感的色调和工艺。再加一盏老式黄铜吊灯，氛围感拉满。新房做出旧时光的感觉，这就是法式中古的魅力。",
                "metadata": {"likes": 9876, "comments": 342, "collects": 4587, "publish_time": "2026-04-25"},
            },
            {
                "post_id": "xhs_003_fashi",
                "title": "复古天鹅绒沙发 + 铜烛台，氛围感全靠它们",
                "body": "客厅 C 位是一张墨绿色天鹅绒沙发，配一对铜质烛台 + 大理石茶几。墙上挂几幅小油画，旁边搁一台老式留声机（装饰用）。最近又淘了一对中古黄铜壁灯，晚上点起来整个客厅都柔了。法式中古就是不断淘宝、不断完善，享受这个过程。",
                "metadata": {"likes": 8234, "comments": 271, "collects": 3987, "publish_time": "2026-05-20"},
            },
        ],
    },
}


# ============================================================
# helper: 本地图 → 预压缩 + base64 data URI （仅测试期使用，不进 analyzer 业务代码）
#
# 预压缩原因：doubao API 网关拒收 ~3MB 以上 base64 payload（ReadError）。
# 长边压到 1024 + JPEG 75，单张 base64 ~150-200KB，3 张总 ~500-600KB，稳定通过。
# 生产期 collector 给的是公网 URL，不走这条路径，业务代码零修改。
# ============================================================
_MAX_EDGE = 1024
_JPEG_QUALITY = 75


def _local_image_to_data_uri(path: Path) -> str:
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((_MAX_EDGE, _MAX_EDGE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def _build_mock_image_urls(style: str) -> list[str]:
    style_dir = MATERIAL_DIR / style
    return [
        _local_image_to_data_uri(p)
        for p in sorted(style_dir.iterdir())
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    ]


# ============================================================
# 主入口：从 STYLE_FIXTURES + material/ 构造 CollectedContent
# ============================================================
async def main() -> None:
    fixture = STYLE_FIXTURES[TEST_STYLE]
    mock_urls = _build_mock_image_urls(TEST_STYLE)

    content = CollectedContent(
        target_account_id=fixture["target_account_id"],
        collected_at=datetime.now(),
        posts=[
            CollectedPost(
                post_id=p["post_id"],
                title=p["title"],
                body=p["body"],
                metadata=p["metadata"],
                image_urls=[mock_urls[i]] if i < len(mock_urls) else [],
            )
            for i, p in enumerate(fixture["posts"])
        ],
    )

    style = await run(content)
    print(f"=== 测试风格：{TEST_STYLE} ===")
    print(style.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
