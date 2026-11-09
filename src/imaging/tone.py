from __future__ import annotations

import numpy as np
from PIL import Image

from src.imaging.color_grade import ColorGrade, apply_grade
from src.imaging.presence import PresenceSettings, apply_presence
from src.imaging.preview_tone import tone_channel


def tone_pil(image: Image.Image, exposure: float, contrast: float) -> Image.Image:
    if exposure == 0 and contrast == 0:
        return image
    table = [tone_channel(level, exposure, contrast) for level in range(256)]
    return image.point(table * len(image.getbands()))


def grade_pil(
    image: Image.Image,
    grade: ColorGrade,
    presence: PresenceSettings | None = None,
) -> Image.Image:
    rgb = image.convert("RGB")
    pixels = np.asarray(rgb)
    if not grade.is_neutral:
        pixels = apply_grade(pixels, grade)
    if presence is not None and not presence.is_neutral:
        pixels = apply_presence(pixels, presence)
    if grade.is_neutral and (presence is None or presence.is_neutral):
        return image
    return Image.fromarray(pixels, "RGB")
