"""
Agent 3 · 提示词工程 Agent · 实现

负责人：A · Agent 工程师
契约 / 行为说明：见同目录 SKILL.md

输入：StyleDNA + UserRequest（重点用 floorplan_meta、user_notes）
输出：ImagePromptBundle(positive_prompt, negative_prompt, aspect_ratio)

LLM：Gemini 2.5 Pro（通过 tools.llm.chat）
失败兜底：JSON 解析失败 → 本地模板组装 positive_prompt
"""

from __future__ import annotations

import json
import logging
import re

from core.schemas import ImagePromptBundle, StyleDNA, UserRequest
from tools.llm import chat

logger = logging.getLogger(__name__)


# 项目固定的 negative_prompt（产品规范要求"固定包含"）
NEGATIVE_PROMPT_FIXED = (
    "低清晰度，模糊，卡通，动漫，插画，CG感，塑料质感，过度渲染，"
    "样板间感过强，完全对称构图，空间空旷，过度整洁，过度杂乱，"
    "曝光过度，曝光不足，光影不自然，家具变形，沙发畸形，茶几变形，"
    "窗框变形，柜体变形，墙面扭曲，透视错误，鱼眼畸变，物品重复，"
    "植物畸形，文字，logo，水印，人物"
)


async def run(style: StyleDNA, request: UserRequest) -> ImagePromptBundle:
    visual = style.visual or {}
    meta = request.floorplan_meta or {}
    user_notes = (request.user_notes or "").strip()

    ctx = {
        "color_palette": _fmt_list(visual.get("color_palette")),
        "material": _fmt_list(visual.get("material")),
        "composition": (visual.get("composition") or "").strip(),
        "lighting": (visual.get("lighting") or "").strip(),
        "area_sqm": _fmt_value(meta.get("area_sqm")),
        "rooms": _fmt_value(meta.get("rooms")),
        "space_type": (meta.get("space_type") or "客厅").strip() or "客厅",
        "orientation": _fmt_value(meta.get("orientation")),
        "target_customer": _fmt_value(meta.get("target_customer")),
        "pain_points": _fmt_value(meta.get("pain_points")),
        "user_notes": user_notes or "（无）",
    }

    try:
        raw = await chat(_build_messages(ctx))
    except Exception as exc:
        logger.error("prompter: LLM 调用异常，走本地兜底：%s", exc)
        raw = ""

    parsed = _extract_json(raw)
    positive_prompt = ""
    aspect_ratio = "3:4"

    if isinstance(parsed, dict):
        pp = parsed.get("positive_prompt")
        if isinstance(pp, str) and pp.strip():
            positive_prompt = pp.strip()
        ar = parsed.get("aspect_ratio")
        if isinstance(ar, str) and ar.strip():
            aspect_ratio = ar.strip()

    if not positive_prompt:
        logger.warning("prompter: LLM 输出不可用，使用本地模板兜底")
        positive_prompt = _fallback_positive_prompt(ctx)
        aspect_ratio = "3:4"

    return ImagePromptBundle(
        positive_prompt=positive_prompt,
        negative_prompt=NEGATIVE_PROMPT_FIXED,
        aspect_ratio=aspect_ratio,
    )


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def _fmt_list(value) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return "、".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip()


def _fmt_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return _fmt_list(value)
    return str(value).strip()


def _build_messages(ctx: dict) -> list[dict]:
    system = (
        "你是一位资深的家居室内设计 AI 文生图提示词工程师。"
        "你专门为小红书图文营销场景生成可直接喂给文生图模型的中文 prompt。"
    )
    user = f"""请基于下方信息，生成一份用于文生图模型的提示词套件。

【风格 DNA（对标账号分析所得）】
- 主色调：{ctx['color_palette'] or '（未指定，按整体氛围合理推断）'}
- 主材质：{ctx['material'] or '（未指定，按整体氛围合理推断）'}
- 构图：{ctx['composition'] or '（未指定）'}
- 光线：{ctx['lighting'] or '（未指定）'}

【户型与空间信息】
- 空间类型：{ctx['space_type']}
- 面积：{ctx['area_sqm'] or '（未提供）'} 平米
- 户型：{ctx['rooms'] or '（未提供）'}
- 朝向：{ctx['orientation'] or '（未提供）'}
- 目标客户：{ctx['target_customer'] or '（未提供）'}
- 痛点 / 诉求：{ctx['pain_points'] or '（未提供）'}

【用户备注】
{ctx['user_notes']}

输出要求：
1. positive_prompt 必须融合上述全部维度，描述一个具体的家居室内设计场景；
2. 必须明确强调：真实住宅实拍摄影质感、室内建筑摄影视角、自然光影、生活感、3:4 竖版构图、photorealistic、4K、sharp focus、high detail；
3. 严禁出现：人物、文字、logo、水印；
4. positive_prompt 长度建议 200-400 字中文；
5. aspect_ratio 固定为 "3:4"；
6. negative_prompt 留空字符串即可（项目使用固定列表，无需你生成）。

严格按下面 JSON 格式输出，禁止输出任何 markdown 围栏或解释文字：
{{
  "positive_prompt": "中文长描述...",
  "negative_prompt": "",
  "aspect_ratio": "3:4"
}}
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _extract_json(text: str) -> dict | None:
    """尽量从 LLM 文本中提取一个 JSON 对象。"""
    if not text:
        return None
    text = text.strip()
    # 1) 直接解析
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    # 2) ```json ... ``` 围栏
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        try:
            obj = json.loads(fence.group(1))
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass
    # 3) 首个 {...} 大括号块
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            obj = json.loads(brace.group(0))
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass
    return None


def _fallback_positive_prompt(ctx: dict) -> str:
    """LLM 不可用时的本地模板兜底。"""
    style_bits = []
    if ctx["color_palette"]:
        style_bits.append(f"主色调：{ctx['color_palette']}")
    if ctx["material"]:
        style_bits.append(f"主要材质：{ctx['material']}")
    if ctx["composition"]:
        style_bits.append(f"构图：{ctx['composition']}")
    if ctx["lighting"]:
        style_bits.append(f"光线：{ctx['lighting']}")
    style_line = "；".join(style_bits) if style_bits else "现代自然风格"

    space_bits = []
    if ctx["rooms"]:
        space_bits.append(ctx["rooms"])
    if ctx["area_sqm"]:
        space_bits.append(f"{ctx['area_sqm']}㎡")
    if ctx["orientation"]:
        space_bits.append(f"朝向{ctx['orientation']}")
    space_line = "，".join(space_bits) if space_bits else "标准户型"

    extra_bits = []
    if ctx["target_customer"]:
        extra_bits.append(f"面向{ctx['target_customer']}")
    if ctx["pain_points"]:
        extra_bits.append(f"重点回应「{ctx['pain_points']}」")
    if ctx["user_notes"] and ctx["user_notes"] != "（无）":
        extra_bits.append(f"用户备注：{ctx['user_notes']}")
    extra_line = "；".join(extra_bits)

    parts = [
        f"{ctx['space_type']} 家居室内设计效果图，真实住宅实拍摄影质感，"
        f"高端家装广告图，3:4 竖版构图，纵向海报画幅，室内建筑摄影视角。",
        f"风格档案——{style_line}。",
        f"空间——{space_line}。",
    ]
    if extra_line:
        parts.append(f"诉求——{extra_line}。")
    parts.append(
        "整体氛围温暖、松弛、自然、高级，有真实居住感，材质细节丰富，"
        "真实自然光与柔和阴影，室内绿植有生命感，专业室内建筑摄影，"
        "杂志级家居广告大片，photorealistic，ultra realistic，4K 高清画质，"
        "sharp focus，high detail，无人物，无文字，无 logo，无水印。"
    )
    return "\n".join(parts)
