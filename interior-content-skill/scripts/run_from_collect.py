"""从 collector 输出目录运行完整非采集内容生成链路。

示例：
python -m scripts.run_from_collect \
  --collect-dir examples/collect-sample/厚来设计 \
  --target-account-id 厚来设计 \
  --notes "180㎡四室两厅，三代同堂改善住宅，希望静奢老钱风，高级但不要冰冷。"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from core.agents.analyzer.agent import run as analyzer_run
from core.agents.copywriter.agent import run as copywriter_run
from core.agents.generator.agent import run as generator_run
from core.agents.prompter.agent import run as prompter_run
from core.collect_loader import load_collected_content
from core.schemas import FinalPost, UserRequest

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_DIR = SKILL_ROOT / "data" / "runs"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run interior content pipeline from a collector output directory.")
    parser.add_argument("--collect-dir", required=True, help="Collector output directory, e.g. data/collect/厚来设计")
    parser.add_argument("--target-account-id", help="Target account id. Defaults to collect-dir basename.")
    parser.add_argument("--notes", required=True, help="Floorplan/user requirement text used by prompter and copywriter.")
    parser.add_argument("--floorplan-image-url", default="", help="Optional floorplan image URL.")
    parser.add_argument("--area-sqm", type=float, help="Optional area in square meters.")
    parser.add_argument("--layout", help="Optional layout, e.g. 四室两厅.")
    parser.add_argument("--orientation", help="Optional orientation, e.g. 南北通透.")
    parser.add_argument("--space-type", help="Optional target space, e.g. 客餐厅.")
    parser.add_argument("--target-customer", help="Optional target customer profile.")
    parser.add_argument("--pain-points", help="Optional pain points.")
    parser.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR), help="Directory where run artifacts are written.")
    parser.add_argument("--env-file", default=str(SKILL_ROOT / ".env"), help="Optional .env path.")
    return parser.parse_args()


def _build_request(args: argparse.Namespace, target_account_id: str) -> UserRequest:
    floorplan_meta: dict[str, Any] = {}
    for key, value in {
        "area_sqm": args.area_sqm,
        "layout": args.layout,
        "orientation": args.orientation,
        "space_type": args.space_type,
        "target_customer": args.target_customer,
        "pain_points": args.pain_points,
    }.items():
        if value is not None:
            floorplan_meta[key] = value

    return UserRequest(
        target_account_id=target_account_id,
        floorplan_image_url=args.floorplan_image_url,
        floorplan_meta=floorplan_meta,
        user_notes=args.notes,
    )


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _write_xiaohongshu_post(path: Path, final: FinalPost) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    hashtags = " ".join(final.copy.hashtags)
    images = "\n".join(f"- {url}" for url in final.images.image_urls)
    content = (
        f"# {final.copy.title}\n\n"
        f"{final.copy.body}\n\n"
        f"{hashtags}\n\n"
        "## 图片\n\n"
        f"{images}\n"
    )
    path.write_text(content, encoding="utf-8")


async def _run(args: argparse.Namespace) -> Path:
    env_path = Path(args.env_file).expanduser().resolve()
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv(SKILL_ROOT / ".env")
        load_dotenv(Path.cwd() / ".env")

    collect_dir = Path(args.collect_dir).expanduser().resolve()
    target_account_id = args.target_account_id or collect_dir.name
    request = _build_request(args, target_account_id)

    content = load_collected_content(collect_dir, target_account_id=target_account_id)
    style = await analyzer_run(content)
    prompts = await prompter_run(style, request)
    images = await generator_run(prompts)
    copy = await copywriter_run(style, images, request)

    from datetime import datetime

    final = FinalPost(
        request_id=os.urandom(16).hex(),
        style_dna=style,
        images=images,
        copy=copy,
        generated_at=datetime.now(),
    )

    run_dir = Path(args.runs_dir).expanduser().resolve() / final.request_id
    _write_json(run_dir / "request.json", request)
    _write_json(run_dir / "collected_content.json", content)
    _write_json(run_dir / "style_dna.json", style)
    _write_json(run_dir / "prompt_bundle.json", prompts)
    _write_json(run_dir / "generated_images.json", images)
    _write_json(run_dir / "copy_content.json", copy)
    _write_json(run_dir / "final_post.json", final)
    _write_xiaohongshu_post(run_dir / "xiaohongshu_post.md", final)

    print("=" * 60)
    print("Interior content pipeline finished")
    print("=" * 60)
    print(f"Run directory     : {run_dir}")
    print(f"Markdown Post     : {run_dir / 'xiaohongshu_post.md'}")
    print(f"Request ID        : {final.request_id}")
    print(f"Target Account    : {style.target_account_id}")
    print("-" * 60)
    print("小红书成稿")
    print("-" * 60)
    print(f"标题：{copy.title}")
    print()
    print("正文：")
    print(copy.body)
    print()
    print(f"话题：{' '.join(copy.hashtags)}")
    print()
    print("图片：")
    for url in images.image_urls:
        print(f"- {url}")
    print("=" * 60)
    return run_dir


def main() -> None:
    asyncio.run(_run(_parse_args()))


if __name__ == "__main__":
    main()
