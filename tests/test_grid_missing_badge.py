import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.ui.widgets.grid_image_widget import GridImageWidget

BADGE_RED = 190
PHOTO = Path("1.jpg")


def _rendered_pixel_reds(grid: GridImageWidget) -> list[int]:
    grid.resize(600, 400)
    image = grid.grab().toImage()
    return [image.pixelColor(x, y).red() for x in range(10, 60, 4) for y in range(10, 22, 2)]


class GridMissingBadgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.grid = GridImageWidget()
        self.grid.set_images([PHOTO])

    def test_missing_photo_is_painted_with_the_badge(self) -> None:
        self.grid.set_missing_images({PHOTO})
        self.assertIn(BADGE_RED, _rendered_pixel_reds(self.grid))

    def test_present_photo_has_no_badge(self) -> None:
        self.grid.set_missing_images(set())
        self.assertNotIn(BADGE_RED, _rendered_pixel_reds(self.grid))

    def test_badge_follows_the_missing_set(self) -> None:
        self.grid.set_missing_images({PHOTO})
        self.grid.set_missing_images(set())
        self.assertEqual(self.grid.missing_images, set())


if __name__ == "__main__":
    unittest.main()
