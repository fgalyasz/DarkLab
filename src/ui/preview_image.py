import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QTransform

from src.develop.crop_settings import CropSettings, crop_box

from src.imaging.clipping import clipping_color
from src.imaging.color_grade import ColorGrade, apply_grade
from src.imaging.preview_tone import tone_channel


def tone_image(image: QImage, exposure: float, contrast: float) -> QImage:
    if image.isNull() or (exposure == 0 and contrast == 0):
        return image
    result = image.convertToFormat(QImage.Format.Format_RGB32)
    _rewrite_pixels(result, exposure, contrast)
    return result


def _rewrite_pixels(image: QImage, exposure: float, contrast: float) -> None:
    for y in range(image.height()):
        _rewrite_row(image, y, exposure, contrast)


def _rewrite_row(image: QImage, y: int, exposure: float, contrast: float) -> None:
    for x in range(image.width()):
        image.setPixelColor(x, y, _toned_color(image.pixelColor(x, y), exposure, contrast))


def _toned_color(color: QColor, exposure: float, contrast: float) -> QColor:
    return QColor(
        tone_channel(color.red(), exposure, contrast),
        tone_channel(color.green(), exposure, contrast),
        tone_channel(color.blue(), exposure, contrast),
    )


def crop_preview(image: QImage, crop: CropSettings) -> QImage:
    if image.isNull() or crop.is_empty:
        return image
    rotated = _straightened(image, crop.angle)
    left, top, right, bottom = crop_box((rotated.width(), rotated.height()), crop)
    return rotated.copy(left, top, right - left, bottom - top)


def _straightened(image: QImage, angle: int) -> QImage:
    if angle == 0:
        return image
    return image.transformed(QTransform().rotate(-angle), Qt.TransformationMode.SmoothTransformation)


def clipping_overlay(image: QImage) -> QImage:
    if image.isNull():
        return image
    result = image.convertToFormat(QImage.Format.Format_RGB32)
    for y in range(result.height()):
        _paint_clipped_row(result, y)
    return result


def _paint_clipped_row(image: QImage, y: int) -> None:
    for x in range(image.width()):
        color = image.pixelColor(x, y)
        clipped = clipping_color(color.red(), color.green(), color.blue())
        if clipped is not None:
            image.setPixelColor(x, y, QColor(*clipped))


def grade_image(image: QImage, grade: ColorGrade) -> QImage:
    if image.isNull() or grade.is_neutral:
        return image
    graded = apply_grade(_pixel_array(image), grade)
    return _image_from_array(graded)


def average_rgb(image: QImage) -> tuple[float, float, float]:
    if image.isNull():
        return (1.0, 1.0, 1.0)
    red, green, blue = _pixel_array(image).reshape(-1, 3).mean(axis=0)
    return (float(red), float(green), float(blue))


def _pixel_array(image: QImage) -> np.ndarray:
    plain = image.convertToFormat(QImage.Format.Format_RGB888)
    buffer = plain.constBits()
    buffer.setsize(plain.sizeInBytes())
    rows = np.frombuffer(buffer, dtype=np.uint8).reshape(plain.height(), plain.bytesPerLine())
    return rows[:, : plain.width() * 3].reshape(plain.height(), plain.width(), 3).copy()


def _image_from_array(pixels: np.ndarray) -> QImage:
    height, width = pixels.shape[:2]
    data = np.ascontiguousarray(pixels)
    return QImage(data.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
