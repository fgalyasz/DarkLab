from pathlib import Path


def format_byte_count(total_bytes: int) -> str:
    size = float(max(0, total_bytes))
    for unit in ("bytes", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return _format_size(size, unit)
        size /= 1024
    return f"{max(0, total_bytes)} bytes"


def byte_total(paths: list[Path]) -> int:
    return sum(_file_size(path) for path in paths)


def import_status_text(photo_count: int, selected_count: int, total_bytes: int) -> str:
    size_text = format_byte_count(total_bytes)
    if selected_count:
        return f"{selected_count} of {photo_count} photos / {size_text}"
    return f"{photo_count} photos / {size_text}"


def _format_size(size: float, unit: str) -> str:
    if unit == "bytes":
        return f"{int(size)} {unit}"
    return f"{size:.1f} {unit}"


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0
