from __future__ import annotations

from PIL import Image

from src.develop.crop_settings import CropSettings, crop_box


def crop_image(image: Image.Image, crop: CropSettings) -> Image.Image:
    if crop.is_empty:
        return image
    rotated = _straightened(image, crop.angle)
    return rotated.crop(crop_box(rotated.size, crop))


def _straightened(image: Image.Image, angle: int) -> Image.Image:
    if angle == 0:
        return image
    return image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
