from __future__ import annotations

import logging
import time
from pathlib import Path

from src.catalog.atomic_file import write_bytes_atomic
from src.catalog.locations import preview_directory
from src.catalog.preview_policy import PreviewPolicy

logger = logging.getLogger(__name__)

FULL_FOLDER = "full"


def full_preview_directory(catalog: Path) -> Path:
    return preview_directory(catalog) / FULL_FOLDER


def full_preview_path(catalog: Path, photo_id: int, settings_hash: str) -> Path:
    _require_photo_id(photo_id)
    safe_hash = _safe_hash_segment(settings_hash)
    return full_preview_directory(catalog) / f"{photo_id}_{safe_hash}.jpg"


def write_full_preview(
    catalog: Path, photo_id: int, settings_hash: str, content: bytes,
) -> Path:
    destination = full_preview_path(catalog, photo_id, settings_hash)
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_bytes_atomic(destination, content)
    return destination


def discard_stale_full_previews(catalog: Path, policy: PreviewPolicy) -> int:
    if not policy.discard_full_enabled:
        return 0
    folder = full_preview_directory(catalog)
    if not folder.is_dir():
        return 0
    cutoff = time.time() - policy.discard_full_days * 86_400
    return _remove_older_than(folder, cutoff)


def _remove_older_than(folder: Path, cutoff: float) -> int:
    removed = 0
    for path in folder.iterdir():
        if not _is_full_file(path):
            continue
        if path.stat().st_mtime >= cutoff:
            continue
        path.unlink()
        removed += 1
    return removed


def _is_full_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".jpg" and "_" in path.stem


def _require_photo_id(photo_id: int) -> None:
    if photo_id < 1:
        raise ValueError("Photo id must be positive")


def _safe_hash_segment(settings_hash: str) -> str:
    stripped = settings_hash.strip()
    if stripped == "":
        raise ValueError("Settings hash is empty")
    safe = "".join(ch for ch in stripped if ch.isalnum() or ch in "-_")
    if safe == "":
        raise ValueError("Settings hash has no safe characters")
    return safe[:64]
