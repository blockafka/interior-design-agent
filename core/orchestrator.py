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
from core.collect_loader import load_collected_content
from core.schemas import CollectedContent, FinalPost, UserRequest


async def run(
    request: UserRequest,
    collected_content: CollectedContent | None = None,
    collect_dir: str | None = None,
) -> FinalPost:
    """5 Agent 串行编排；联调期可用 collect_dir 跳过真实采集 Agent。"""
    request_id = str(uuid.uuid4())

    # Step 1 · 采集（采集 Agent 未接入时，可传 collect_dir 读取本地采集样例）
    if collected_content is not None:
        content = collected_content
    elif collect_dir:
        content = load_collected_content(collect_dir, target_account_id=request.target_account_id)
    else:
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
