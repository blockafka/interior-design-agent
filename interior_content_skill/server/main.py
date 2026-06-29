"""FastAPI server: 封装 interior-content-skill pipeline，提供 SSE 流式进度推送。

启动方式：
    cd interior-content-skill
    python -m server.main
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

SKILL_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(SKILL_ROOT / ".env")

from ..core.agents.analyzer.agent import run as analyzer_run
from ..core.agents.copywriter.agent import run as copywriter_run
from ..core.agents.generator.agent import run as generator_run
from ..core.agents.prompter.agent import run as prompter_run
from ..core.collect_loader import load_collected_content
from ..core.schemas import FinalPost, UserRequest

app = FastAPI(title="Interior Content Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GENERATED_DIR = SKILL_ROOT / "data" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")

# 对标账号素材根目录：优先读环境变量 COLLECT_ROOT（指向采集器实时产物，
# 如 ../data/xhs_collected），未设置时回退到内置示例样本。
_collect_root_env = os.getenv("COLLECT_ROOT", "").strip()
if _collect_root_env:
    COLLECT_SAMPLE_DIR = Path(_collect_root_env).expanduser().resolve()
    # 验证目录存在，不存在则回退到示例样本
    if not COLLECT_SAMPLE_DIR.exists() or not COLLECT_SAMPLE_DIR.is_dir():
        print(f"WARNING: COLLECT_ROOT path {COLLECT_SAMPLE_DIR} does not exist, falling back to sample data")
        COLLECT_SAMPLE_DIR = SKILL_ROOT / "examples" / "collect-sample"
else:
    COLLECT_SAMPLE_DIR = SKILL_ROOT / "examples" / "collect-sample"

import re as _re

def _scan_accounts() -> list[dict]:
    """扫描 collect-sample 目录，返回所有对标账号的摘要信息。"""
    results = []
    if not COLLECT_SAMPLE_DIR.exists():
        return results
    for acct_dir in sorted(COLLECT_SAMPLE_DIR.iterdir()):
        if not acct_dir.is_dir():
            continue
        post_dirs = sorted([p for p in acct_dir.iterdir() if p.is_dir()])
        total_liked = 0
        total_collected = 0
        sample_title = ""
        for post_dir in post_dirs:
            meta_path = post_dir / "metadata.json"
            if meta_path.exists():
                try:
                    raw = meta_path.read_bytes().decode("utf-8")
                    raw = _re.sub(r"\\\\", "/", raw)
                    d = json.loads(raw)
                    try:
                        total_liked += int(d.get("liked_count") if d.get("liked_count") is not None else d.get("like_count") or 0)
                    except (TypeError, ValueError):
                        pass
                    try:
                        total_collected += int(d.get("collect_count") or 0)
                    except (TypeError, ValueError):
                        pass
                    if not sample_title:
                        sample_title = d.get("title", "")
                except Exception:
                    pass
        results.append({
            "id": acct_dir.name,
            "name": acct_dir.name,
            "post_count": len(post_dirs),
            "total_liked": total_liked,
            "total_collected": total_collected,
            "sample_title": sample_title,
        })
    return results


class GenerateRequest(BaseModel):
    target_account_id: str = "厚来设计"
    area_sqm: float | None = None
    layout: str | None = None
    orientation: str | None = None
    space_type: str | None = None
    target_customer: str | None = None
    pain_points: str | None = None
    notes: str = ""


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


async def _run_pipeline(req: GenerateRequest) -> AsyncGenerator[str, None]:
    floorplan_meta: dict = {}
    for key in ("area_sqm", "layout", "orientation", "space_type", "target_customer", "pain_points"):
        val = getattr(req, key, None)
        if val is not None:
            floorplan_meta[key] = val

    request = UserRequest(
        target_account_id=req.target_account_id,
        floorplan_image_url="",
        floorplan_meta=floorplan_meta,
        user_notes=req.notes,
    )

    try:
        yield _sse_event("step_start", {"step": "collector", "message": "正在加载对标账号素材..."})
        await asyncio.sleep(0.3)
        account_dir = COLLECT_SAMPLE_DIR / req.target_account_id
        content = load_collected_content(account_dir, target_account_id=req.target_account_id)
        yield _sse_event("step_done", {"step": "collector", "message": f"已加载 {len(content.posts)} 篇笔记素材"})

        yield _sse_event("step_start", {"step": "analyzer", "message": "正在分析对标账号视觉与文案风格..."})
        style = await analyzer_run(content)
        style_data = style.model_dump(mode="json")
        yield _sse_event("step_done", {"step": "analyzer", "result": style_data})

        yield _sse_event("step_start", {"step": "prompter", "message": "正在生成图片提示词..."})
        prompts = await prompter_run(style, request)
        prompts_data = prompts.model_dump(mode="json")
        yield _sse_event("step_done", {"step": "prompter", "result": prompts_data})

        yield _sse_event("step_start", {"step": "generator", "message": "正在生成设计效果图（约1-2分钟）..."})
        images = await generator_run(prompts)
        images_data = images.model_dump(mode="json")
        yield _sse_event("step_done", {"step": "generator", "result": images_data})

        yield _sse_event("step_start", {"step": "copywriter", "message": "正在撰写小红书营销文案..."})
        copy = await copywriter_run(style, images, request)
        copy_data = copy.model_dump(mode="json")
        yield _sse_event("step_done", {"step": "copywriter", "result": copy_data})

        final = FinalPost(
            request_id=uuid.uuid4().hex,
            style_dna=style,
            images=images,
            copy_content=copy,
            generated_at=datetime.now(),
        )
        yield _sse_event("complete", final.model_dump(mode="json"))
    except Exception as e:
        yield _sse_event("error", {"message": f"{type(e).__name__}: {e}"})


@app.get("/api/accounts")
async def list_accounts():
    return _scan_accounts()


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    return StreamingResponse(
        _run_pipeline(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
