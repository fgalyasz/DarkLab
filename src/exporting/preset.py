from __future__ import annotations

from dataclasses import asdict, dataclass

FORMATS = ("JPEG", "TIFF")
COLOR_SPACES = ("sRGB",)
BUILT_IN_NAME = "JPEG sRGB 2048"


@dataclass(frozen=True)
class ExportPreset:
    name: str
    format: str = "JPEG"
    long_edge: int = 2048
    color_space: str = "sRGB"
    sharpen: bool = False
    watermark: str = ""

    @property
    def extension(self) -> str:
        return ".tif" if self.format == "TIFF" else ".jpg"


BUILT_IN_PRESET = ExportPreset(BUILT_IN_NAME)


def encode_preset(preset: ExportPreset) -> dict[str, object]:
    return asdict(preset)


def decode_preset(raw: object) -> ExportPreset | None:
    if not isinstance(raw, dict):
        return None
    try:
        preset = ExportPreset(**raw)
    except TypeError:
        return None
    return preset if _is_valid(preset) else None


def _is_valid(preset: ExportPreset) -> bool:
    return (
        bool(preset.name)
        and preset.format in FORMATS
        and preset.color_space in COLOR_SPACES
        and isinstance(preset.long_edge, int)
        and preset.long_edge >= 0
        and isinstance(preset.sharpen, bool)
        and isinstance(preset.watermark, str)
    )
