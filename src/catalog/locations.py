from __future__ import annotations

from pathlib import Path

DATABASE_NAME = "catalog.sqlite"
PREVIEWS_NAME = "previews"
SETTINGS_NAME = "settings.json"


def database_file(catalog: Path) -> Path:
    if catalog.is_dir():
        return catalog / DATABASE_NAME
    return catalog


def package_root(path: Path) -> Path:
    if path.name == DATABASE_NAME and path.parent.is_dir():
        return path.parent
    return path


def preview_directory(catalog: Path) -> Path:
    root = package_root(catalog)
    if root.is_dir() or not root.exists():
        return root / PREVIEWS_NAME
    return Path(f"{root}.previews")


def settings_file(catalog: Path) -> Path:
    return package_root(catalog) / SETTINGS_NAME


def prepare_package(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    preview_directory(destination).mkdir(exist_ok=True)
    _ensure_settings(settings_file(destination))


def _ensure_settings(path: Path) -> None:
    if path.is_file():
        return
    path.write_text("{}\n", encoding="utf-8")
