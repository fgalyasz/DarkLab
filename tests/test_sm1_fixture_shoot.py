import tempfile
import unittest
from pathlib import Path

from src.smoke.sm1_fixture_shoot import run_sm1_fixture_shoot

SM1_TEST_COUNT = 24


class Sm1FixtureShootTests(unittest.TestCase):
    def test_sm1_fixture_import_cull_develop_export(self) -> None:
        root = Path(tempfile.mkdtemp())
        run_sm1_fixture_shoot(root, SM1_TEST_COUNT)


if __name__ == "__main__":
    unittest.main()
