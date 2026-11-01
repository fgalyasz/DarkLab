from __future__ import annotations

import numpy as np
from PIL import Image

from src.imaging.color_grade import ColorGrade, apply_grade
from src.imaging.preview_tone import tone_channel


def tone_pil(image: Image.Image, exposure: float, contrast: float) -> Image.Image:
    if exposure == 0 and contrast == 0:
        return image
    table = [tone_channel(level, exposure, contrast) for level in range(256)]
    return image.point(table * len(image.getbands()))


def grade_pil(image: Image.Image, grade: ColorGrade) -> Image.Image:
    if grade.is_neutral:
        return image
    rgb = image.convert("RGB")
    return Image.fromarray(apply_grade(np.asarray(rgb), grade), "RGB")
