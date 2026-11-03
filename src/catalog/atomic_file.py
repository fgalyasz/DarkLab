from __future__ import annotations

import os
from pathlib import Path


def write_text_atomic(path: Path, text: str) -> None:
    write_bytes_atomic(path, text.encode("utf-8"))


def write_bytes_atomic(path: Path, content: bytes) -> None:
    staged = path.with_name(f".{path.name}.tmp")
    try:
        _write_and_sync(staged, content)
        os.replace(staged, path)
    except OSError:
        staged.unlink(missing_ok=True)
        raise


def _write_and_sync(path: Path, content: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
