import tempfile
import unittest
from pathlib import Path

from src.smoke.milestone_one_shoot import assert_adr2_catalog_layout, run_milestone_one_shoot


class MilestoneShootTests(unittest.TestCase):
    def test_import_flag_develop_export_keeps_original_hashes(self) -> None:
        root = Path(tempfile.mkdtemp())
        catalog = run_milestone_one_shoot(root)
        assert_adr2_catalog_layout(catalog)


if __name__ == "__main__":
    unittest.main()
