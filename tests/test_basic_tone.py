import unittest

import numpy as np

from src.imaging.basic_tone import BasicTone, apply_basic_tone


class BasicToneTests(unittest.TestCase):
    def test_neutral_returns_same_array(self) -> None:
        pixels = np.full((4, 4, 3), 120, dtype=np.uint8)
        self.assertIs(apply_basic_tone(pixels, BasicTone()), pixels)

    def test_shadows_lift_dark_pixels(self) -> None:
        pixels = np.full((8, 8, 3), 40, dtype=np.uint8)
        lifted = apply_basic_tone(pixels, BasicTone(shadows=80))
        self.assertGreater(int(lifted.mean()), int(pixels.mean()))

    def test_highlights_lower_bright_pixels_when_negative(self) -> None:
        pixels = np.full((8, 8, 3), 220, dtype=np.uint8)
        reduced = apply_basic_tone(pixels, BasicTone(highlights=-80))
        self.assertLess(int(reduced.mean()), int(pixels.mean()))

    def test_from_tone_reads_zone_keys(self) -> None:
        tone = BasicTone.from_tone({"Highlights": 1, "Shadows": 2, "Whites": 3, "Blacks": 4})
        self.assertEqual(tone, BasicTone(1, 2, 3, 4))


if __name__ == "__main__":
    unittest.main()
