from __future__ import annotations

from PIL import Image

from src.imaging.preview_tone import tone_channel


def tone_pil(image: Image.Image, exposure: float, contrast: float) -> Image.Image:
    if exposure == 0 and contrast == 0:
        return image
    table = [tone_channel(level, exposure, contrast) for level in range(256)]
    return image.point(table * len(image.getbands()))
