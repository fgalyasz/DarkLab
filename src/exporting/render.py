from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.develop.crop_settings import decode_crop
from src.develop.tone_settings import decode_tone
from src.exporting.preset import ExportPreset
from src.imaging.crop import crop_image
from src.imaging.original_image import load_original, srgb_profile_bytes
from src.imaging.tone import tone_pil

JPEG_QUALITY = 92
WATERMARK_MARGIN = 12


def render_photo(original: Path, settings: dict[str, str], preset: ExportPreset) -> Image.Image:
    cropped = crop_image(load_original(original), decode_crop(settings))
    tone = decode_tone(settings)
    toned = tone_pil(cropped, tone.get("Exposure", 0), tone.get("Contrast", 0))
    resized = resize_long_edge(toned, preset.long_edge)
    return _watermarked(_sharpened(resized, preset.sharpen), preset.watermark)


def save_render(image: Image.Image, target: Path, preset: ExportPreset) -> None:
    profile = srgb_profile_bytes()
    if preset.format == "TIFF":
        image.save(target, format="TIFF", compression="tiff_adobe_deflate", icc_profile=profile)
        return
    image.save(target, format="JPEG", quality=JPEG_QUALITY, icc_profile=profile)


def resize_long_edge(image: Image.Image, long_edge: int) -> Image.Image:
    if long_edge == 0 or max(image.size) == long_edge:
        return image
    scale = long_edge / max(image.size)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def _sharpened(image: Image.Image, enabled: bool) -> Image.Image:
    if not enabled:
        return image
    return image.filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=2))


def _watermarked(image: Image.Image, text: str) -> Image.Image:
    if not text:
        return image
    stamped = image.copy()
    draw = ImageDraw.Draw(stamped)
    font = ImageFont.load_default(size=max(12, max(image.size) // 40))
    box = draw.textbbox((0, 0), text, font=font)
    position = (image.width - box[2] - WATERMARK_MARGIN, image.height - box[3] - WATERMARK_MARGIN)
    draw.text(position, text, font=font, fill=(255, 255, 255))
    return stamped
