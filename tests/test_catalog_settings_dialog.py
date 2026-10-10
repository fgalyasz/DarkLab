import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog

from src.catalog.database import create_catalog
from src.catalog.startup_policy import ASK, FIXED, RECENT
from src.ui.dialogs.catalog_settings_dialog import CatalogSettingsDialog


class CatalogSettingsDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_empty_settings_select_recent(self) -> None:
        dialog = CatalogSettingsDialog({})
        self.assertEqual(dialog.chosen_mode(), RECENT)
        self.assertFalse(dialog._path.isEnabled())

    def test_ask_can_be_saved(self) -> None:
        dialog = CatalogSettingsDialog({"startup_mode": ASK, "fixed_catalog": "/keep.darklab"})
        dialog._accept_if_valid()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(dialog.chosen_mode(), ASK)
        self.assertEqual(dialog.chosen_fixed_path(), "/keep.darklab")

    def test_fixed_without_a_file_stays_open(self) -> None:
        dialog = CatalogSettingsDialog({"startup_mode": FIXED})
        dialog._accept_if_valid()
        self.assertNotEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(dialog._error.text(), "Choose a catalog file.")

    def test_fixed_saves_an_existing_file(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        dialog = CatalogSettingsDialog({"startup_mode": FIXED, "fixed_catalog": str(catalog)})
        dialog._accept_if_valid()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(dialog.chosen_fixed_path(), str(catalog))

    def test_browse_cancel_leaves_recent(self) -> None:
        dialog = CatalogSettingsDialog({})
        with patch.object(QFileDialog, "getOpenFileName", return_value=("", "")):
            dialog._browse_catalog()
        self.assertEqual(dialog.chosen_mode(), RECENT)

    def test_browse_selects_fixed_mode(self) -> None:
        dialog = CatalogSettingsDialog({})
        with patch.object(QFileDialog, "getOpenFileName", return_value=("/tmp/wedding.darklab", "")):
            dialog._browse_catalog()
        self.assertTrue(dialog._fixed.isChecked())
        self.assertEqual(dialog._path.text(), "/tmp/wedding.darklab")
        self.assertTrue(dialog._browse.isEnabled())
