from __future__ import annotations

import json
from pathlib import Path

from src.catalog.locations import settings_file


def read_catalog_setting(catalog: Path, key: str) -> str | None:
    return read_catalog_settings(catalog).get(key)


def read_catalog_settings(catalog: Path) -> dict[str, str]:
    path = settings_file(catalog)
    if not path.is_file():
        return {}
    return _load_settings(path)


def write_catalog_setting(catalog: Path, key: str, value: str) -> None:
    if key.strip() == "":
        raise ValueError("Setting name is empty")
    current = read_catalog_settings(catalog)
    current[key] = value
    _store_settings(settings_file(catalog), current)


def _load_settings(path: Path) -> dict[str, str]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Catalog settings are not valid JSON: {path}") from error
    return _string_map(loaded)


def _string_map(loaded: object) -> dict[str, str]:
    if not isinstance(loaded, dict):
        raise ValueError("Catalog settings must be a JSON object")
    return {str(key): str(value) for key, value in loaded.items()}


def _store_settings(path: Path, values: dict[str, str]) -> None:
    text = json.dumps(values, indent=2, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")
