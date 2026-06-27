"""
主编排器：5 Agent 状态机

【过渡期实现】
当前用硬编码 import 串联 5 个 Agent。
等 skill_loader 实现完毕，整体替换为动态加载（见 docs/SKILL_PROTOCOL.md §4）。

输入：UserRequest
输出：FinalPost
"""

import uuid
from datetime import datetime

from core.agents.analyzer.agent import run as analyzer_run
from core.agents.collector.agent import run as collector_run
from core.agents.copywriter.agent import run as copywriter_run
from core.agents.generator.agent import run as generator_run
from core.agents.prompter.agent import run as prompter_run
from core.schemas import FinalPost, UserRequest


async def run(request: UserRequest) -> FinalPost:
    """5 Agent 串行编排（先跑通，后续再加并行 / 重试 / 回退）"""
    request_id = str(uuid.uuid4())

    # Step 1 · 采集
    content = await collector_run(request)

    # Step 2 · 风格分析（kafka 负责的 Skill）
    style = await analyzer_run(content)

    # Step 3 · 提示词工程
    prompts = await prompter_run(style, request)

    # Step 4 · 图片生成
    images = await generator_run(prompts)

    # Step 5 · 文案
    copy = await copywriter_run(style, images, request)

    return FinalPost(
        request_id=request_id,
        style_dna=style,
        images=images,
        copy=copy,
        generated_at=datetime.now(),
    )
