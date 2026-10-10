from pathlib import Path

import exifread


def read_exposure_text(path: Path) -> str:
    tags = _read_tags(path)
    head = " at ".join(part for part in (_shutter(_tag(tags, "EXIF ExposureTime")), _aperture(_tag(tags, "EXIF FNumber"))) if part)
    tail = ", ".join(part for part in (_iso(_tag(tags, "EXIF ISOSpeedRatings")), _focal(_tag(tags, "EXIF FocalLength"), _tag(tags, "EXIF LensModel"))) if part)
    if head and tail:
        return f"{head}, {tail}"
    return head or tail


def _read_tags(path: Path) -> dict:
    try:
        with path.open("rb") as handle:
            return exifread.process_file(handle, details=False)
    except OSError:
        return {}


def _tag(tags: dict, name: str) -> str:
    value = tags.get(name)
    if value is None:
        return ""
    return str(value)


def _shutter(value: str) -> str:
    if not value:
        return ""
    return f"{value} sec"


def _aperture(value: str) -> str:
    if not value:
        return ""
    return f"f / {_decimal(value)}"


def _iso(value: str) -> str:
    if not value:
        return ""
    return f"ISO {value}"


def _focal(focal: str, lens: str) -> str:
    focal_text = _decimal(focal)
    if focal_text and lens:
        return f"{focal_text} mm ({lens})"
    if focal_text:
        return f"{focal_text} mm"
    return lens


def _decimal(value: str) -> str:
    if "/" not in value:
        return value
    left, right = value.split("/", 1)
    try:
        number = float(left) / float(right)
    except ValueError:
        return value
    return f"{number:.1f}".rstrip("0").rstrip(".")
