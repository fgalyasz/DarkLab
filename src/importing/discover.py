from __future__ import annotations

from pathlib import Path

IMAGE_SUFFIXES = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp",
    ".cr2", ".cr3", ".nef", ".arw", ".raf", ".orf", ".rw2", ".dng",
}
MAX_DEPTH = 3


def discover_images(folder: Path, recursive: bool = False) -> list[Path]:
    if not folder.is_dir():
        return []
    if recursive:
        return _sorted(_walk(folder, 0))
    return _sorted(_files_in(folder))


def _sorted(paths: list[Path]) -> list[Path]:
    return sorted(paths, key=_sort_key)


def _sort_key(path: Path) -> tuple[str, str, str]:
    return (path.stem.lower(), path.suffix.lower(), path.name.lower())


def _walk(folder: Path, depth: int) -> list[Path]:
    if depth >= MAX_DEPTH:
        return []
    found = _files_in(folder)
    found.extend(_child_walks(folder, depth))
    return found


def _child_walks(folder: Path, depth: int) -> list[Path]:
    found: list[Path] = []
    for child in _directories(folder):
        found.extend(_walk(child, depth + 1))
    return found


def _files_in(folder: Path) -> list[Path]:
    return [path for path in _children(folder) if _is_image(path)]


def _directories(folder: Path) -> list[Path]:
    return [path for path in _children(folder) if path.is_dir()]


def _children(folder: Path) -> list[Path]:
    try:
        return list(folder.iterdir())
    except OSError:
        return []


def _is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
