from __future__ import annotations

from pathlib import Path

from src.catalog.locations import database_file


def remember_catalog(settings: dict[str, str], path: Path) -> dict[str, str]:
    updated = dict(settings)
    updated["catalog_path"] = str(path)
    return updated


def catalog_to_reopen(settings: dict[str, str]) -> Path | None:
    raw = settings.get("catalog_path", "")
    if raw == "":
        return None
    return _existing_catalog(Path(raw))


def _existing_catalog(path: Path) -> Path | None:
    if _is_saved_catalog(path):
        return path
    return None


def _is_saved_catalog(path: Path) -> bool:
    if path.is_dir():
        return database_file(path).is_file()
    return path.is_file()
