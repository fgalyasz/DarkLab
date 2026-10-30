from __future__ import annotations

import json
import logging
from pathlib import Path

from src.catalog.locations import presets_file
from src.exporting.preset import BUILT_IN_NAME, BUILT_IN_PRESET, ExportPreset, decode_preset, encode_preset

logger = logging.getLogger(__name__)


def list_presets(catalog: Path) -> list[ExportPreset]:
    return [BUILT_IN_PRESET, *saved_presets(catalog)]


def saved_presets(catalog: Path) -> list[ExportPreset]:
    decoded = [decode_preset(raw) for raw in _stored_entries(presets_file(catalog))]
    return [preset for preset in decoded if preset is not None and preset.name != BUILT_IN_NAME]


def save_preset(catalog: Path, preset: ExportPreset) -> None:
    if preset.name == BUILT_IN_NAME:
        raise ValueError(f"The built-in Preset {BUILT_IN_NAME!r} cannot be replaced")
    kept = [saved for saved in saved_presets(catalog) if saved.name != preset.name]
    _write_entries(presets_file(catalog), [*kept, preset])


def _stored_entries(path: Path) -> list[object]:
    if not path.is_file():
        return []
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        logger.warning("Export Presets unreadable at %s: %s", path, error)
        return []
    return entries if isinstance(entries, list) else []


def _write_entries(path: Path, presets: list[ExportPreset]) -> None:
    text = json.dumps([encode_preset(preset) for preset in presets], indent=2)
    path.write_text(text + "\n", encoding="utf-8")
