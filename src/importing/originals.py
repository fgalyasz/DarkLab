from __future__ import annotations

import io
import logging
from pathlib import Path

import rawpy
from PIL import Image, UnidentifiedImageError

from src.catalog.database import apply_schema
from src.catalog.folders import add_imported_folder
from src.catalog.index_images import write_index_image
from src.catalog.locations import database_file
from src.catalog.photos import remember_photo

logger = logging.getLogger(__name__)
INDEX_EDGE = 360


def import_originals(catalog: Path, originals: list[Path]) -> int:
    apply_schema(database_file(catalog))
    return sum(_import_one(catalog, path) for path in originals)


def import_original(catalog: Path, original: Path) -> Path:
    if not original.is_file():
        raise FileNotFoundError(original)
    photo_id = remember_photo(catalog, original)
    add_imported_folder(catalog, original.parent)
    return write_index_image(catalog, photo_id, index_jpeg(original))


def index_jpeg(original: Path) -> bytes:
    image = _opened_image(original)
    image.thumbnail((INDEX_EDGE, INDEX_EDGE))
    return _jpeg_bytes(image.convert("RGB"))


def _import_one(catalog: Path, original: Path) -> int:
    try:
        import_original(catalog, original)
    except (OSError, ValueError, rawpy.LibRawError) as error:
        logger.error("Import failed for %s: %s", original, error)
        return 0
    return 1


def _opened_image(original: Path) -> Image.Image:
    try:
        return Image.open(original)
    except UnidentifiedImageError:
        return _raw_preview(original)


def _raw_preview(original: Path) -> Image.Image:
    return Image.open(io.BytesIO(_raw_thumb_bytes(original)))


def _raw_thumb_bytes(original: Path) -> bytes:
    with rawpy.imread(str(original)) as raw:
        thumb = raw.extract_thumb()
    if thumb.format == rawpy.ThumbFormat.JPEG:
        return bytes(thumb.data)
    image = Image.fromarray(thumb.data)
    return _jpeg_bytes(image.convert("RGB"))


def _jpeg_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=80)
    return buffer.getvalue()
