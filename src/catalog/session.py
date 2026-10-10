from __future__ import annotations

from pathlib import Path


def remember_catalog(settings: dict[str, str], path: Path) -> dict[str, str]:
    updated = dict(settings)
    updated["catalog_path"] = str(path)
    return updated


def catalog_to_reopen(settings: dict[str, str]) -> Path | None:
    raw = settings.get("catalog_path", "")
    if raw == "":
        return None
    path = Path(raw)
    if path.is_file():
        return path
    return None
