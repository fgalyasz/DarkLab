from __future__ import annotations

NEUTRAL_TEMPERATURE = 5500
BASIC_KEYS = ("Exposure", "Contrast", "Highlights", "Shadows", "Whites", "Blacks")
PRESENCE_KEYS = ("Texture", "Clarity", "Dehaze", "Vibrance", "Saturation")
BALANCE_KEYS = ("Temp", "Tint")
TONE_KEYS = BALANCE_KEYS + BASIC_KEYS + PRESENCE_KEYS
TONE_DEFAULTS = {key: 0 for key in TONE_KEYS} | {"Temp": NEUTRAL_TEMPERATURE}


def encode_tone(values: dict[str, int]) -> dict[str, str]:
    return {key: str(values[key]) for key in TONE_KEYS if key in values}


def decode_tone(settings: dict[str, str]) -> dict[str, int]:
    decoded = {key: _whole_number(settings.get(key)) for key in TONE_KEYS}
    return {key: value for key, value in decoded.items() if value is not None}


def _whole_number(raw: str | None) -> int | None:
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None
