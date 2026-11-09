import unittest

import numpy as np

from src.imaging.presence import PresenceSettings, apply_presence


class PresenceTests(unittest.TestCase):
    def test_neutral_presence_leaves_pixels(self) -> None:
        pixels = np.full((2, 2, 3), 128, dtype=np.uint8)
        neutral = PresenceSettings()
        self.assertIs(apply_presence(pixels, neutral), pixels)

    def test_clarity_raises_local_contrast(self) -> None:
        pixels = np.zeros((4, 4, 3), dtype=np.uint8)
        pixels[2, 2] = (255, 255, 255)
        settings = PresenceSettings(clarity=40)
        result = apply_presence(pixels, settings)
        self.assertGreater(int(result[2, 2, 0]), 200)
        self.assertLess(int(result[0, 0, 0]), 30)

    def test_from_tone_reads_presence_keys(self) -> None:
        settings = PresenceSettings.from_tone({"Texture": 5, "Clarity": -10, "Dehaze": 20})
        self.assertEqual(settings, PresenceSettings(5, -10, 20))
