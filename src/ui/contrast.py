import re

RGB_PATTERN = re.compile(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)")
BODY_RULE = re.compile(r"QWidget\s*\{([^}]*)\}")
LABEL_RULE = re.compile(r"QLabel\s*\{([^}]*)\}")
FOREGROUND = re.compile(r"(?<![-\w])color:\s*(rgb\([^)]*\))")
BACKGROUND = re.compile(r"background-color:\s*(rgb\([^)]*\))")
MINIMUM_BODY_CONTRAST = 4.5


def parse_rgb(text: str) -> tuple[int, int, int]:
    match = RGB_PATTERN.search(text)
    if match is None:
        raise ValueError(f"No rgb() color in {text!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def contrast_ratio(foreground: tuple[int, int, int], background: tuple[int, int, int]) -> float:
    lighter, darker = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def body_label_contrast(stylesheet: str) -> float:
    background = parse_rgb(_first(BACKGROUND, _rule(BODY_RULE, stylesheet)))
    foreground = parse_rgb(_first(FOREGROUND, _rule(LABEL_RULE, stylesheet)))
    return contrast_ratio(foreground, background)


def _rule(pattern: re.Pattern[str], stylesheet: str) -> str:
    match = pattern.search(stylesheet)
    if match is None:
        raise ValueError(f"Stylesheet has no rule for {pattern.pattern}")
    return match.group(1)


def _first(pattern: re.Pattern[str], rule: str) -> str:
    match = pattern.search(rule)
    if match is None:
        raise ValueError(f"Rule has no value for {pattern.pattern}")
    return match.group(1)


def _luminance(color: tuple[int, int, int]) -> float:
    red, green, blue = (_linear(channel) for channel in color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _linear(channel: int) -> float:
    value = channel / 255
    if value <= 0.03928:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4
