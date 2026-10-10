def clamp_channel(value: float) -> int:
    if value < 0:
        return 0
    if value > 255:
        return 255
    return int(value)


def tone_channel(channel: int, exposure: float, contrast: float) -> int:
    scaled = (channel / 255.0) * (2 ** (exposure / 50.0))
    shaped = (scaled - 0.5) * (1.0 + contrast / 100.0) + 0.5
    return clamp_channel(shaped * 255.0)
