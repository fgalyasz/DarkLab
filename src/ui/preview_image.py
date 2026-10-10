from PyQt6.QtGui import QColor, QImage

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
