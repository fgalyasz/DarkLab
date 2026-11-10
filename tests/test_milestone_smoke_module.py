import unittest

from src.smoke import milestone_one_shoot


class MilestoneSmokeModuleTests(unittest.TestCase):
    def test_module_exports_runner(self) -> None:
        self.assertTrue(callable(milestone_one_shoot.run_milestone_one_shoot))
        self.assertTrue(callable(milestone_one_shoot.assert_adr2_catalog_layout))


if __name__ == "__main__":
    unittest.main()
