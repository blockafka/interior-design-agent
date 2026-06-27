"""
主编排器：5 Agent 状态机

职责：把 5 个 Agent 按顺序串起来，统一处理异常 / 重试 / 日志。

输入：UserRequest
输出：FinalPost
"""

import uuid
from datetime import datetime

from core.agents import analyzer, collector, copywriter, generator, prompter
from core.schemas import FinalPost, UserRequest


async def run(request: UserRequest) -> FinalPost:
    """5 Agent 串行编排（先跑通，后续再加并行 / 重试 / 回退）"""
    request_id = str(uuid.uuid4())

    # Step 1 · 采集
    content = await collector.collect(request)

    # Step 2 · 风格分析
    style = await analyzer.analyze(content)

    # Step 3 · 提示词工程
    prompts = await prompter.build_prompt(style, request)

    # Step 4 · 图片生成
    images = await generator.generate(prompts)

    # Step 5 · 文案
    copy = await copywriter.write_copy(style, images, request)

    return FinalPost(
        request_id=request_id,
        style_dna=style,
        images=images,
        copy=copy,
        generated_at=datetime.now(),
    )
