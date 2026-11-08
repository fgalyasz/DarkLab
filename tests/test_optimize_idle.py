import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication, QWidget

from src.catalog.database import create_catalog
from src.catalog.optimize_policy import OptimizePolicy, store_optimize_policy
from src.ui.optimize_idle import (
    OptimizeIdleWatcher,
    idle_timeout_ms,
    resets_idle_timer,
)

APP = QApplication.instance() or QApplication([])


class OptimizeIdleHelpersTests(unittest.TestCase):
    def test_idle_timeout_scales_minutes(self) -> None:
        self.assertEqual(idle_timeout_ms(0), 0)
        self.assertEqual(idle_timeout_ms(2), 120_000)

    def test_mouse_move_does_not_reset_timer(self) -> None:
        self.assertFalse(resets_idle_timer(QEvent.Type.MouseMove))

    def test_keypress_resets_timer(self) -> None:
        self.assertTrue(resets_idle_timer(QEvent.Type.KeyPress))


class OptimizeIdleWatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.host = QWidget()
        self.addCleanup(self.host.close)
        self.watcher = OptimizeIdleWatcher(self.host)

    def test_apply_with_zero_idle_stops_timer(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "demo")
        self.watcher.apply(catalog, OptimizePolicy(False, 0))
        self.assertFalse(self.watcher._timer.isActive())

    def test_apply_with_idle_starts_timer(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "demo")
        store_optimize_policy(catalog, OptimizePolicy(False, 1))
        self.watcher.apply(catalog, OptimizePolicy(False, 1))
        self.assertTrue(self.watcher._timer.isActive())

    def test_idle_runs_optimize_when_timer_fires(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "demo")
        store_optimize_policy(catalog, OptimizePolicy(False, 1))
        self.watcher.apply(catalog, OptimizePolicy(False, 1))
        with patch("src.ui.optimize_idle.run_optimize_catalog", return_value=True) as run:
            self.watcher._on_idle()
            run.assert_called_once_with(self.host, catalog)


if __name__ == "__main__":
    unittest.main()
