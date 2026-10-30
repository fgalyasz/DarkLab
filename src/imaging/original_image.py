from __future__ import annotations

import io
import logging
from pathlib import Path

import rawpy
from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)


def load_original(path: Path) -> Image.Image:
    try:
        return _opened_upright(path)
    except UnidentifiedImageError:
        return _developed_raw(path)


def srgb_profile_bytes() -> bytes:
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def _opened_upright(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        embedded = opened.info.get("icc_profile")
        upright = ImageOps.exif_transpose(opened).convert("RGB")
    return _converted_to_srgb(upright, embedded)


def _converted_to_srgb(image: Image.Image, embedded: bytes | None) -> Image.Image:
    if not embedded:
        return image
    try:
        source = ImageCms.ImageCmsProfile(io.BytesIO(embedded))
        return ImageCms.profileToProfile(image, source, ImageCms.createProfile("sRGB"), outputMode="RGB")
    except (ImageCms.PyCMSError, OSError) as error:
        logger.warning("Embedded color profile could not be converted to sRGB: %s", error)
        return image


def _developed_raw(path: Path) -> Image.Image:
    with rawpy.imread(str(path)) as raw:
        pixels = raw.postprocess(use_camera_wb=True)
    return Image.fromarray(pixels)
