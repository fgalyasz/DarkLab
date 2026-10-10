from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    _feed_hash(digest, path)
    return digest.hexdigest()


def _feed_hash(digest: hashlib._Hash, path: Path) -> None:
    handle = path.open("rb")
    try:
        _read_chunks(digest, handle)
    finally:
        handle.close()


def _read_chunks(digest: hashlib._Hash, handle: object) -> None:
    while _update_chunk(digest, handle):
        continue


def _update_chunk(digest: hashlib._Hash, handle: object) -> bool:
    chunk = handle.read(CHUNK_SIZE)
    if chunk == b"":
        return False
    digest.update(chunk)
    return True
