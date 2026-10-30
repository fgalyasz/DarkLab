from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import rawpy

from src.catalog.develop_settings import read_develop_settings
from src.catalog.photos import photo_original
from src.exporting.preset import ExportPreset
from src.exporting.render import render_photo, save_render

logger = logging.getLogger(__name__)


@dataclass
class ExportReport:
    written: list[Path] = field(default_factory=list)
    missing: list[Path] = field(default_factory=list)
    failed: list[tuple[Path, str]] = field(default_factory=list)


def renderable_count(catalog: Path, photo_ids: list[int]) -> int:
    return sum(1 for photo_id in photo_ids if _existing_original(catalog, photo_id) is not None)


def export_photos(catalog: Path, photo_ids: list[int], folder: Path, preset: ExportPreset) -> ExportReport:
    folder.mkdir(parents=True, exist_ok=True)
    report = ExportReport()
    for photo_id in photo_ids:
        _export_into(report, catalog, photo_id, folder, preset)
    return report


def _existing_original(catalog: Path, photo_id: int) -> Path | None:
    original = photo_original(catalog, photo_id)
    if original is None or not original.is_file():
        return None
    return original


def _export_into(report: ExportReport, catalog: Path, photo_id: int, folder: Path, preset: ExportPreset) -> None:
    original = _existing_original(catalog, photo_id)
    if original is None:
        report.missing.append(photo_original(catalog, photo_id) or Path(f"photo {photo_id}"))
        return
    try:
        report.written.append(_render_to_folder(catalog, photo_id, original, folder, preset))
    except (OSError, ValueError, rawpy.LibRawError) as error:
        logger.error("Export failed for %s: %s", original, error)
        report.failed.append((original, str(error)))


def _render_to_folder(catalog: Path, photo_id: int, original: Path, folder: Path, preset: ExportPreset) -> Path:
    image = render_photo(original, read_develop_settings(catalog, photo_id), preset)
    target = _free_target(folder, original.stem, preset.extension)
    save_render(image, target, preset)
    return target


def _free_target(folder: Path, stem: str, extension: str) -> Path:
    target = folder / f"{stem}{extension}"
    counter = 1
    while target.exists():
        target = folder / f"{stem}-{counter}{extension}"
        counter += 1
    return target
