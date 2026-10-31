HIGHLIGHT_COLOR = (255, 0, 0)
SHADOW_COLOR = (0, 0, 255)
TOP_CHANNEL = 255
BOTTOM_CHANNEL = 0


def is_highlight_clipped(red: int, green: int, blue: int) -> bool:
    return max(red, green, blue) >= TOP_CHANNEL


def is_shadow_clipped(red: int, green: int, blue: int) -> bool:
    return min(red, green, blue) <= BOTTOM_CHANNEL


def clipping_color(red: int, green: int, blue: int) -> tuple[int, int, int] | None:
    if is_highlight_clipped(red, green, blue):
        return HIGHLIGHT_COLOR
    if is_shadow_clipped(red, green, blue):
        return SHADOW_COLOR
    return None
