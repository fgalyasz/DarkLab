import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog

from src.catalog.database import create_catalog
from src.ui.dialogs.select_catalog_dialog import SelectCatalogDialog


class SelectCatalogDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_quit_rejects(self) -> None:
        dialog = SelectCatalogDialog()
        dialog._quit()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        self.assertIsNone(dialog._chosen)

    def test_open_accepts_a_catalog(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        dialog = SelectCatalogDialog()
        dialog._try_open(catalog)
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(dialog._chosen, catalog)

    def test_open_rejects_a_missing_file(self) -> None:
        dialog = SelectCatalogDialog()
        dialog._try_open(Path("/missing.darklab"))
        self.assertNotEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertNotEqual(dialog._error.text(), "")

    def test_cancelled_file_dialog_stays_open(self) -> None:
        dialog = SelectCatalogDialog()
        with patch.object(QFileDialog, "getOpenFileName", return_value=("", "")):
            dialog._open_existing()
        self.assertIsNone(dialog._chosen)

    def test_create_accepts_a_new_file(self) -> None:
        folder = Path(tempfile.mkdtemp())
        dialog = SelectCatalogDialog()
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(folder / "new"), "")):
            dialog._create_new()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(dialog._chosen, folder / "new.darklab")
