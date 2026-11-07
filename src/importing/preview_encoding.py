from __future__ import annotations

import io
from pathlib import Path

import rawpy
from PIL import Image, UnidentifiedImageError

from src.exporting.render import resize_long_edge


def encode_standard_jpeg(original: Path, long_edge: int, quality: int) -> bytes:
    image = _opened_image(original)
    image.thumbnail((long_edge, long_edge))
    return _jpeg_bytes(image.convert("RGB"), quality)


def encode_full_jpeg(original: Path, long_edge: int, quality: int) -> bytes:
    image = _opened_image(original)
    if long_edge > 0:
        image = resize_long_edge(image, long_edge)
    return _jpeg_bytes(image.convert("RGB"), quality)


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
    return _jpeg_bytes(image.convert("RGB"), 80)


def _jpeg_bytes(image: Image.Image, quality: int) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()
