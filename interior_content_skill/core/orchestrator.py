"""非采集链路主编排器。

这个厚 Claude Code Skill 不包含 collector。它只读取 collector skill 产出的
本地采集目录，然后串联 analyzer -> prompter -> generator -> copywriter。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from .agents.analyzer.agent import run as analyzer_run
from .agents.copywriter.agent import run as copywriter_run
from .agents.generator.agent import run as generator_run
from .agents.prompter.agent import run as prompter_run
from .collect_loader import load_collected_content
from .schemas import CollectedContent, FinalPost, UserRequest


async def run(
    request: UserRequest,
    collected_content: CollectedContent | None = None,
    collect_dir: str | Path | None = None,
) -> FinalPost:
    """串联非采集链路；必须传 collected_content 或 collect_dir。"""
    request_id = str(uuid.uuid4())

    if collected_content is not None:
        content = collected_content
    elif collect_dir:
        content = load_collected_content(collect_dir, target_account_id=request.target_account_id)
    else:
        raise ValueError("interior-content-skill 不包含 collector，请传入 collect_dir 或 collected_content")

    style = await analyzer_run(content)
    prompts = await prompter_run(style, request)
    images = await generator_run(prompts)
    copy = await copywriter_run(style, images, request)

    return FinalPost(
        request_id=request_id,
        style_dna=style,
        images=images,
        copy_content=copy,
        generated_at=datetime.now(),
    )
