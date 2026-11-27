POINTER_HALF_WIDTH = 5
POINTER_SHOULDER_Y = 4
POINTER_BOTTOM_Y = 9


def value_ratio(value: int, minimum: int, maximum: int) -> float:
    span = maximum - minimum
    if span <= 0:
        return 0.0
    clamped = max(minimum, min(maximum, value))
    return (clamped - minimum) / span


def handle_center_x(ratio: float, left: int, right: int) -> int:
    clamped = max(0.0, min(1.0, ratio))
    if right <= left:
        return left
    return round(left + clamped * (right - left))


def tick_positions(left: int, right: int, count: int = 9) -> tuple[tuple[int, bool], ...]:
    if count < 2 or right <= left:
        return ()
    last = count - 1
    mid = last // 2
    return tuple((round(left + i * (right - left) / last), i in (0, mid, last)) for i in range(count))


def pointer_polygon(center_x: int, top_y: int) -> tuple[tuple[int, int], ...]:
    left = center_x - POINTER_HALF_WIDTH
    right = center_x + POINTER_HALF_WIDTH
    shoulder = top_y + POINTER_SHOULDER_Y
    bottom = top_y + POINTER_BOTTOM_Y
    return (
        (center_x, top_y),
        (right, shoulder),
        (right, bottom),
        (left, bottom),
        (left, shoulder),
    )


def format_slider_value(title: str, value: int, minimum: int) -> str:
    if title == "Exposure":
        if value == 0:
            return "0.00"
        return f"{value / 100:+.2f}"
    if title == "Temp":
        return f"{value:,}".replace(",", " ")
    if minimum < 0 and value > 0:
        return f"+{value}"
    return str(value)
