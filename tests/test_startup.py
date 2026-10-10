import unittest

from src.startup import launch_is_allowed


class StartupTests(unittest.TestCase):
    def test_small_display_can_launch(self) -> None:
        self.assertTrue(launch_is_allowed(1280, 800))

    def test_missing_display_cannot_launch(self) -> None:
        self.assertFalse(launch_is_allowed(0, 800))
        self.assertFalse(launch_is_allowed(1280, 0))
