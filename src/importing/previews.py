from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import rawpy

from src.catalog.index_images import write_index_image
from src.catalog.photos import photo_original
from src.catalog.preview_index import missing_preview_ids
from src.catalog.preview_policy import read_preview_policy
from src.importing.originals import index_jpeg

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RebuildReport:
    rebuilt: int
    unavailable: int

    def describe(self) -> str:
        if self.rebuilt == 0 and self.unavailable == 0:
            return "All previews are present."
        text = f"Rebuilt {self.rebuilt} preview(s)."
        if self.unavailable:
            text += f" {self.unavailable} could not be rebuilt because the original is missing or unreadable."
        return text


def rebuild_previews(catalog: Path) -> RebuildReport:
    results = [_rebuild_one(catalog, photo_id) for photo_id in missing_preview_ids(catalog)]
    return RebuildReport(rebuilt=results.count(True), unavailable=results.count(False))


def _rebuild_one(catalog: Path, photo_id: int) -> bool:
    original = photo_original(catalog, photo_id)
    if original is None or not original.is_file():
        logger.debug("Preview of photo %s stays missing: original %s not found", photo_id, original)
        return False
    try:
        policy = read_preview_policy(catalog)
        write_index_image(catalog, photo_id, index_jpeg(original, policy))
    except (OSError, ValueError, rawpy.LibRawError) as error:
        logger.error("Could not rebuild preview of photo %s from %s: %s", photo_id, original, error)
        return False
    return True
