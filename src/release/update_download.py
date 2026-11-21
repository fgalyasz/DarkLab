from __future__ import annotations

from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.release.update_check import UpdateCheckError


def download_release_asset(
    url: str,
    destination: Path,
    on_progress: Callable[[int, int], None] | None = None,
    opener: Callable = urlopen,
    chunk_size: int = 65536,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "DarkLab-Updater"})
    try:
        with opener(request, timeout=60) as response:
            _stream_to_file(response, destination, on_progress, chunk_size)
    except (URLError, TimeoutError, OSError) as error:
        raise UpdateCheckError(f"Download failed: {error}") from error
    return destination


def _stream_to_file(
    response,
    destination: Path,
    on_progress: Callable[[int, int], None] | None,
    chunk_size: int,
) -> None:
    total = int(response.headers.get("Content-Length", "0") or "0")
    done = 0
    with destination.open("wb") as handle:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            handle.write(chunk)
            done += len(chunk)
            if on_progress is not None:
                on_progress(done, total)
