import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtWidgets import QApplication

from src.catalog.catalog_folders import catalog_folders, folder_photo_ids, relink_folder
from src.catalog.database import create_catalog
from src.catalog.develop_settings import read_develop_settings, write_develop_settings
from src.catalog.file_hash import content_hash
from src.catalog.index_images import list_index_images
from src.catalog.locations import database_file
from src.catalog.missing import RelinkError, is_missing
from src.catalog.removal import remove_catalog_photo
from src.importing.originals import import_originals
from src.ui.widgets.catalog_folder_panel import CatalogFolderPanel, folder_text

APP = QApplication.instance() or QApplication([])
SETTINGS = {"Exposure": "7"}


def _original(folder: Path, name: str, shade: int) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    Image.new("RGB", (16, 16), (shade, shade, shade)).save(path)
    return path


class CatalogFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.card = self.root / "card"
        self.studio = self.root / "studio"
        originals = [
            _original(self.card, "a.jpg", 30),
            _original(self.card, "b.jpg", 90),
            _original(self.studio, "c.jpg", 150),
        ]
        self.catalog = create_catalog(self.root / "shoot")
        import_originals(self.catalog, originals)
        write_develop_settings(self.catalog, 1, SETTINGS)


class CatalogFoldersDomainTests(CatalogFixture):
    def test_each_directory_of_originals_is_a_folder_with_its_photos(self) -> None:
        folders = catalog_folders(self.catalog)
        self.assertEqual([folder.path for folder in folders], [self.card, self.studio])
        self.assertEqual([folder.photo_ids for folder in folders], [(1, 2), (3,)])
        self.assertFalse(any(folder.is_missing for folder in folders))

    def test_folder_photo_ids_selects_one_directory(self) -> None:
        self.assertEqual(folder_photo_ids(self.catalog, self.studio), (3,))
        self.assertEqual(folder_photo_ids(self.catalog, self.root / "none"), ())

    def test_empty_catalog_has_no_folders(self) -> None:
        self.assertEqual(catalog_folders(create_catalog(self.root / "empty")), [])

    def test_folders_do_not_copy_or_write_files(self) -> None:
        before = sorted(path.name for path in self.card.iterdir())
        catalog_folders(self.catalog)
        self.assertEqual(sorted(path.name for path in self.card.iterdir()), before)

    def test_renamed_directory_is_missing(self) -> None:
        self.card.rename(self.root / "card_renamed")
        missing = [folder for folder in catalog_folders(self.catalog) if folder.is_missing]
        self.assertEqual([folder.path for folder in missing], [self.card])


class RelinkFolderTests(CatalogFixture):
    def setUp(self) -> None:
        super().setUp()
        self.moved = self.root / "card_renamed"
        self.card.rename(self.moved)

    def test_relink_points_every_photo_at_the_replacement(self) -> None:
        self.assertEqual(relink_folder(self.catalog, self.card, self.moved), 2)
        self.assertFalse(is_missing(self.catalog, 1))
        self.assertFalse(is_missing(self.catalog, 2))
        self.assertEqual([folder.path for folder in catalog_folders(self.catalog)], [self.moved, self.studio])

    def test_relink_keeps_settings_and_previews(self) -> None:
        previews = list_index_images(self.catalog)
        relink_folder(self.catalog, self.card, self.moved)
        self.assertEqual(read_develop_settings(self.catalog, 1), SETTINGS)
        self.assertEqual(list_index_images(self.catalog), previews)

    def test_relink_leaves_the_originals_unchanged(self) -> None:
        before = content_hash(self.moved / "a.jpg")
        relink_folder(self.catalog, self.card, self.moved)
        self.assertEqual(content_hash(self.moved / "a.jpg"), before)

    def test_replacement_that_is_not_a_directory_is_rejected(self) -> None:
        with self.assertRaises(RelinkError):
            relink_folder(self.catalog, self.card, self.moved / "a.jpg")

    def test_folder_without_photos_is_rejected(self) -> None:
        with self.assertRaises(RelinkError):
            relink_folder(self.catalog, self.root / "none", self.moved)

    def test_missing_file_writes_nothing(self) -> None:
        (self.moved / "b.jpg").unlink()
        with self.assertRaises(RelinkError):
            relink_folder(self.catalog, self.card, self.moved)
        self.assertTrue(is_missing(self.catalog, 1))

    def test_different_content_is_refused_until_confirmed(self) -> None:
        _original(self.moved, "b.jpg", 200)
        with self.assertRaises(RelinkError):
            relink_folder(self.catalog, self.card, self.moved)
        self.assertTrue(is_missing(self.catalog, 1))
        self.assertEqual(relink_folder(self.catalog, self.card, self.moved, confirm_different=True), 2)

    def test_photo_without_stored_hash_is_accepted(self) -> None:
        connection = sqlite3.connect(database_file(self.catalog))
        connection.execute("UPDATE photos SET content_hash = NULL")
        connection.commit()
        connection.close()
        self.assertEqual(relink_folder(self.catalog, self.card, self.moved), 2)


class CatalogFolderPanelTests(CatalogFixture):
    def setUp(self) -> None:
        super().setUp()
        self.widget = CatalogFolderPanel()
        self.widget.set_folders(catalog_folders(self.catalog))

    def test_rows_show_name_and_count(self) -> None:
        self.assertEqual([self.widget.list.item(row).text() for row in range(2)], ["card (2)", "studio (1)"])

    def test_missing_folder_text_says_so(self) -> None:
        self.card.rename(self.root / "gone")
        folders = catalog_folders(self.catalog)
        self.assertEqual(folder_text(folders[0]), "card (2) - MISSING")

    def test_choosing_a_row_emits_its_path(self) -> None:
        chosen: list[Path] = []
        self.widget.folder_chosen.connect(chosen.append)
        self.widget.list.setCurrentRow(1)
        self.assertEqual(chosen, [self.studio])
        self.assertEqual(self.widget.selected_folder(), self.studio)

    def test_relink_is_only_enabled_for_a_missing_folder(self) -> None:
        self.widget.list.setCurrentRow(0)
        self.assertFalse(self.widget.relink_button.isEnabled())
        self.card.rename(self.root / "gone")
        self.widget.set_folders(catalog_folders(self.catalog), self.card)
        self.assertTrue(self.widget.relink_button.isEnabled())

    def test_relink_button_emits_the_selected_folder(self) -> None:
        requested: list[Path] = []
        self.widget.relink_requested.connect(requested.append)
        self.card.rename(self.root / "gone")
        self.widget.set_folders(catalog_folders(self.catalog), self.card)
        self.widget.relink_button.click()
        self.assertEqual(requested, [self.card])

    def test_relink_request_without_selection_emits_nothing(self) -> None:
        requested: list[Path] = []
        self.widget.relink_requested.connect(requested.append)
        self.widget._request_relink()
        self.assertEqual(requested, [])

    def test_refresh_selects_the_given_folder(self) -> None:
        self.widget.set_folders(catalog_folders(self.catalog), self.studio)
        self.assertEqual(self.widget.selected_folder(), self.studio)

    def test_clear_selection_selects_nothing(self) -> None:
        self.widget.list.setCurrentRow(1)
        self.widget.clear_selection()
        self.assertIsNone(self.widget.selected_folder())
        self.assertFalse(self.widget.relink_button.isEnabled())


class LibraryFolderTests(CatalogFixture):
    def setUp(self) -> None:
        super().setUp()
        from src.ui.panels.library_browser_panel import LibraryBrowserPanel
        self.panel = LibraryBrowserPanel()
        self.panel.show_catalog(self.catalog)
        self.panel._cancel_load()

    def _names(self) -> list[str]:
        return sorted(path.stem for path in self.panel.grid.images)

    def test_library_starts_with_every_photo_and_both_folders(self) -> None:
        self.assertEqual(len(self.panel.grid.images), 3)
        self.assertEqual(self.panel.folders.list.count(), 2)

    def test_selecting_a_folder_shows_only_its_photos(self) -> None:
        self.panel.folders.list.setCurrentRow(0)
        self.assertEqual(self._names(), ["1", "2"])
        self.assertEqual(self.panel.status_label.text(), "2 photos")

    def test_all_photographs_clears_the_folder(self) -> None:
        self.panel.folders.list.setCurrentRow(0)
        self.panel.catalog.setCurrentRow(1)
        self.panel.catalog.setCurrentRow(0)
        self.assertEqual(len(self.panel.grid.images), 3)
        self.assertIsNone(self.panel.folders.selected_folder())

    def test_a_new_import_adds_its_folder_on_reload(self) -> None:
        import_originals(self.catalog, [_original(self.root / "extra", "d.jpg", 220)])
        self.panel._load_all_photographs()
        self.assertEqual(self.panel.folders.list.count(), 3)

    def test_folder_that_lost_its_photos_is_dropped(self) -> None:
        self.panel.folders.list.setCurrentRow(1)
        remove_catalog_photo(self.catalog, 3, delete_original=False)
        self.panel._load_all_photographs()
        self.assertEqual(len(self.panel.grid.images), 2)
        self.assertIsNone(self.panel.folders.selected_folder())

    def test_renamed_directory_is_marked_missing_on_refresh(self) -> None:
        self.card.rename(self.root / "gone")
        self.panel._load_all_photographs()
        self.assertEqual(self.panel.folders.list.item(0).text(), "card (2) - MISSING")

    def test_relink_through_the_panel_restores_the_folder(self) -> None:
        moved = self.root / "gone"
        self.card.rename(moved)
        self.panel._load_all_photographs()
        self.assertTrue(self.panel.relink_folder_to(self.card, moved))
        self.assertEqual(self.panel.folders.selected_folder(), moved)
        self.assertEqual(self._names(), ["1", "2"])
        self.assertEqual(self.panel.folders.list.item(0).text(), "gone (2)")

    def test_failed_relink_warns_and_keeps_the_folder_missing(self) -> None:
        self.card.rename(self.root / "gone")
        self.panel._load_all_photographs()
        with patch("src.ui.panels.library_browser_panel.QMessageBox.warning") as warning:
            self.assertFalse(self.panel.relink_folder_to(self.card, self.root / "nowhere"))
        warning.assert_called_once()
        self.assertTrue(self.panel.folders.list.item(0).text().endswith("MISSING"))

    def test_relink_without_a_catalog_is_refused(self) -> None:
        self.panel.show_catalog(None)
        self.assertFalse(self.panel.relink_folder_to(self.card, self.root))

    def test_relink_dialog_passes_the_chosen_directory(self) -> None:
        moved = self.root / "gone"
        self.card.rename(moved)
        self.panel._load_all_photographs()
        with patch("src.ui.panels.library_browser_panel.QFileDialog.getExistingDirectory", return_value=str(moved)):
            self.panel._relink_folder(self.card)
        self.assertEqual(self.panel.folders.selected_folder(), moved)

    def test_cancelled_relink_dialog_changes_nothing(self) -> None:
        self.card.rename(self.root / "gone")
        self.panel._load_all_photographs()
        with patch("src.ui.panels.library_browser_panel.QFileDialog.getExistingDirectory", return_value=""):
            self.panel._relink_folder(self.card)
        self.assertTrue(self.panel.folders.list.item(0).text().endswith("MISSING"))

    def test_folder_selection_never_touches_originals(self) -> None:
        before = content_hash(self.card / "a.jpg")
        self.panel.folders.list.setCurrentRow(0)
        shutil.rmtree(self.root / "studio")
        self.assertEqual(content_hash(self.card / "a.jpg"), before)


if __name__ == "__main__":
    unittest.main()
