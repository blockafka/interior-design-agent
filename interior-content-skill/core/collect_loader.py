"""把本地采集文件夹转换为标准 CollectedContent。

用于采集 Agent 尚未接入时的联调入口。
目录结构（按账号组织，--collect-dir 指到「账号目录」，其下每个子目录是一篇笔记）：
    <账号目录>/<单篇笔记>/{metadata.json, body.txt, image_urls.txt, images/*}
例如：examples/collect-sample/厚来设计/<单篇笔记>/
"""

from __future__ import annotations

import base64
import io
import json
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any

from core.schemas import CollectedContent, CollectedPost

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def load_collected_content(account_dir: str | Path, target_account_id: str | None = None) -> CollectedContent:
    """读取本地采集账号目录，返回 analyzer 可直接消费的 CollectedContent。"""
    root = Path(account_dir).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"采集目录不存在：{root}")
    if not root.is_dir():
        raise NotADirectoryError(f"采集路径不是目录：{root}")

    post_dirs = _find_post_dirs(root)
    posts = [_load_post(post_dir) for post_dir in post_dirs]
    posts = [p for p in posts if p.body or p.image_urls]
    if not posts:
        raise ValueError(f"采集目录没有可用笔记：{root}")

    return CollectedContent(
        target_account_id=target_account_id or root.name,
        posts=posts,
        collected_at=datetime.now(),
    )


def _find_post_dirs(root: Path) -> list[Path]:
    if (root / "metadata.json").exists() or (root / "body.txt").exists():
        return [root]
    return sorted(p for p in root.iterdir() if p.is_dir())


def _load_post(post_dir: Path) -> CollectedPost:
    metadata = _read_json(post_dir / "metadata.json")
    title = str(metadata.get("title") or post_dir.name)
    body = _read_text(post_dir / "body.txt") or _read_text(post_dir / "full_text_snapshot.txt")
    image_urls = _load_local_images(post_dir / "images") or _read_lines(post_dir / "image_urls.txt")

    return CollectedPost(
        post_id=str(metadata.get("note_id") or post_dir.name),
        title=title,
        body=body,
        image_urls=image_urls,
        metadata={
            **metadata,
            "likes": _to_int(metadata.get("liked_count") or metadata.get("like_count")),
            "collects": _to_int(metadata.get("collect_count")),
            "source_dir": str(post_dir),
        },
    )


def _load_local_images(images_dir: Path) -> list[str]:
    if not images_dir.exists():
        return []
    return [
        _local_image_to_data_uri(path)
        for path in sorted(images_dir.iterdir())
        if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES
    ]


def _local_image_to_data_uri(path: Path) -> str:
    compressed = _try_compress_image(path)
    if compressed is not None:
        mime_type, data = compressed
    else:
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
    return f"data:{mime_type};base64,{base64.b64encode(data).decode()}"


def _try_compress_image(path: Path) -> tuple[str, bytes] | None:
    """有 Pillow 时压成 JPEG，降低多模态网关 payload；没有则用原文件。"""
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return "image/jpeg", buf.getvalue()
    except Exception:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
