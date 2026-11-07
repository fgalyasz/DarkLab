import tempfile
import unittest
from pathlib import Path

from src.catalog.database import create_catalog
from src.catalog.optimize import CatalogOptimizeError, optimize_catalog
from src.catalog.optimize_policy import OptimizePolicy, read_optimize_policy, store_optimize_policy


class OptimizePolicyTests(unittest.TestCase):
    def test_defaults_are_off(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "demo")
        policy = read_optimize_policy(catalog)
        self.assertFalse(policy.on_quit_enabled)
        self.assertEqual(policy.on_idle_minutes, 0)

    def test_round_trip(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "demo")
        wanted = OptimizePolicy(True, 30)
        store_optimize_policy(catalog, wanted)
        self.assertEqual(read_optimize_policy(catalog), wanted)


class OptimizeCancelTests(unittest.TestCase):
    def test_cancel_stops_between_steps(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "demo")
        calls = {"n": 0}

        def progress(done: int, total: int, label: str) -> None:
            calls["n"] = done

        def cancel() -> bool:
            return calls["n"] >= 2

        with self.assertRaises(CatalogOptimizeError):
            optimize_catalog(catalog, progress, cancel)


if __name__ == "__main__":
    unittest.main()
