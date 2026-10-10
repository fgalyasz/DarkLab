from __future__ import annotations

import shutil
from pathlib import Path


def copy_original(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def move_original(source: Path, destination: Path) -> Path:
    copied = copy_original(source, destination)
    _remove_source_after_copy(source, copied)
    return copied


def _remove_source_after_copy(source: Path, destination: Path) -> None:
    if not _sizes_match(source, destination):
        return
    source.unlink()


def _sizes_match(source: Path, destination: Path) -> bool:
    if not destination.is_file() or not source.is_file():
        return False
    return destination.stat().st_size == source.stat().st_size
