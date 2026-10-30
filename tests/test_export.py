import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import rawpy
from PIL import Image, ImageCms
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.develop_settings import write_develop_settings
from src.catalog.file_hash import content_hash
from src.catalog.locations import database_file, presets_file
from src.develop.crop_settings import CropSettings, encode_crop
from src.develop.tone_settings import encode_tone
from src.exporting.batch import ExportReport, export_photos, renderable_count
from src.exporting.messages import export_blocker, report_summary, skip_note
from src.exporting.preset import BUILT_IN_NAME, BUILT_IN_PRESET, ExportPreset, decode_preset, encode_preset
from src.exporting.preset_store import list_presets, save_preset
from src.exporting.render import render_photo, resize_long_edge, save_render
from src.imaging.original_image import load_original, srgb_profile_bytes
from src.imaging.tone import tone_pil
from src.importing.originals import import_originals

APP = QApplication.instance() or QApplication([])
RENDER_ERROR = "src.exporting.batch.render_photo"
TIFF_PRESET = ExportPreset("Print", "TIFF", 300, "sRGB", True, "(c) me")


def _catalog_with_photos(*sizes: tuple[int, int]) -> tuple[Path, list[Path]]:
    folder = Path(tempfile.mkdtemp())
    catalog = create_catalog(folder / "shoot")
    originals = []
    for number, size in enumerate(sizes):
        original = folder / f"frame{number}.jpg"
        Image.new("RGB", size, (100 + number, 90, 80)).save(original)
        originals.append(original)
    import_originals(catalog, originals, allow_duplicate=True)
    return catalog, originals


def _photo_count(catalog: Path) -> int:
    connection = sqlite3.connect(database_file(catalog))
    try:
        return int(connection.execute("SELECT COUNT(*) FROM photos").fetchone()[0])
    finally:
        connection.close()


class PresetTests(unittest.TestCase):
    def test_built_in_preset_is_jpeg_srgb_2048_plain(self) -> None:
        self.assertEqual(
            (BUILT_IN_PRESET.format, BUILT_IN_PRESET.color_space, BUILT_IN_PRESET.long_edge),
            ("JPEG", "sRGB", 2048),
        )
        self.assertFalse(BUILT_IN_PRESET.sharpen)
        self.assertEqual(BUILT_IN_PRESET.watermark, "")

    def test_extension_follows_the_format(self) -> None:
        self.assertEqual(BUILT_IN_PRESET.extension, ".jpg")
        self.assertEqual(TIFF_PRESET.extension, ".tif")

    def test_encode_round_trips(self) -> None:
        self.assertEqual(decode_preset(encode_preset(TIFF_PRESET)), TIFF_PRESET)

    def test_decode_rejects_bad_values(self) -> None:
        bad = [None, "x", {"name": ""}, {"name": "a", "format": "PNG"}, {"name": "a", "color_space": "ProPhoto"},
               {"name": "a", "long_edge": -1}, {"name": "a", "sharpen": 1}, {"name": "a", "extra": 1}]
        self.assertTrue(all(decode_preset(raw) is None for raw in bad))


class PresetStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, _originals = _catalog_with_photos((8, 8))

    def test_built_in_is_always_first(self) -> None:
        self.assertEqual(list_presets(self.catalog), [BUILT_IN_PRESET])

    def test_saved_preset_survives_a_reload(self) -> None:
        save_preset(self.catalog, TIFF_PRESET)
        self.assertEqual(list_presets(self.catalog), [BUILT_IN_PRESET, TIFF_PRESET])

    def test_same_name_replaces(self) -> None:
        save_preset(self.catalog, TIFF_PRESET)
        save_preset(self.catalog, ExportPreset("Print", "JPEG", 100))
        self.assertEqual(list_presets(self.catalog)[1].format, "JPEG")
        self.assertEqual(len(list_presets(self.catalog)), 2)

    def test_built_in_name_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            save_preset(self.catalog, ExportPreset(BUILT_IN_NAME, "TIFF"))

    def test_unreadable_or_foreign_file_is_ignored(self) -> None:
        presets_file(self.catalog).write_text("not json", encoding="utf-8")
        self.assertEqual(list_presets(self.catalog), [BUILT_IN_PRESET])
        presets_file(self.catalog).write_text('{"a": 1}', encoding="utf-8")
        self.assertEqual(list_presets(self.catalog), [BUILT_IN_PRESET])

    def test_stored_built_in_name_and_invalid_entries_are_dropped(self) -> None:
        entries = [encode_preset(ExportPreset(BUILT_IN_NAME, "TIFF")), {"name": "x", "color_space": "AdobeRGB"}]
        presets_file(self.catalog).write_text(json.dumps(entries), encoding="utf-8")
        self.assertEqual(list_presets(self.catalog), [BUILT_IN_PRESET])


class RenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.originals = _catalog_with_photos((400, 200))

    def test_long_edge_is_the_preset_long_edge(self) -> None:
        self.assertEqual(render_photo(self.originals[0], {}, ExportPreset("a", long_edge=100)).size, (100, 50))

    def test_zero_long_edge_keeps_full_size(self) -> None:
        self.assertEqual(render_photo(self.originals[0], {}, ExportPreset("a", long_edge=0)).size, (400, 200))

    def test_crop_is_in_the_render(self) -> None:
        settings = encode_crop(CropSettings(left=25, right=25))
        image = render_photo(self.originals[0], settings, ExportPreset("a", long_edge=0))
        self.assertEqual(image.size, (200, 200))

    def test_tone_is_in_the_render(self) -> None:
        plain = render_photo(self.originals[0], {}, ExportPreset("a", long_edge=0)).getpixel((5, 5))
        bright = render_photo(self.originals[0], encode_tone({"Exposure": 100}), ExportPreset("a", long_edge=0))
        self.assertGreater(bright.getpixel((5, 5))[0], plain[0])

    def test_watermark_and_sharpen_change_pixels(self) -> None:
        plain = render_photo(self.originals[0], {}, ExportPreset("a", long_edge=0))
        marked = render_photo(self.originals[0], {}, ExportPreset("a", long_edge=0, sharpen=True, watermark="mine"))
        self.assertNotEqual(plain.tobytes(), marked.tobytes())

    def test_resize_leaves_matching_size_alone(self) -> None:
        image = Image.new("RGB", (50, 20))
        self.assertIs(resize_long_edge(image, 50), image)

    def test_tone_with_no_change_returns_same_image(self) -> None:
        image = Image.new("RGB", (4, 4))
        self.assertIs(tone_pil(image, 0, 0), image)

    def test_saved_files_open_with_srgb_profile(self) -> None:
        folder = Path(tempfile.mkdtemp())
        for preset in (BUILT_IN_PRESET, TIFF_PRESET):
            target = folder / f"out{preset.extension}"
            save_render(Image.new("RGB", (20, 10)), target, preset)
            with Image.open(target) as opened:
                self.assertEqual(opened.format, preset.format)
                self.assertTrue(opened.info.get("icc_profile"))


class OriginalImageTests(unittest.TestCase):
    def test_exif_orientation_is_applied(self) -> None:
        path = Path(tempfile.mkdtemp()) / "turned.jpg"
        exif = Image.Exif()
        exif[274] = 6
        Image.new("RGB", (40, 20)).save(path, exif=exif)
        self.assertEqual(load_original(path).size, (20, 40))

    def test_embedded_srgb_profile_keeps_the_color(self) -> None:
        path = Path(tempfile.mkdtemp()) / "profiled.jpg"
        Image.new("RGB", (8, 8), (10, 20, 30)).save(path, icc_profile=srgb_profile_bytes())
        pixel = load_original(path).getpixel((0, 0))
        self.assertTrue(all(abs(got - want) <= 3 for got, want in zip(pixel, (10, 20, 30))))

    def test_unusable_profile_type_keeps_the_pixels(self) -> None:
        path = Path(tempfile.mkdtemp()) / "lab.jpg"
        lab = ImageCms.ImageCmsProfile(ImageCms.createProfile("LAB")).tobytes()
        Image.new("RGB", (8, 8), (10, 20, 30)).save(path, icc_profile=lab)
        self.assertEqual(load_original(path).getpixel((0, 0)), (10, 20, 30))

    def test_broken_profile_keeps_the_pixels(self) -> None:
        path = Path(tempfile.mkdtemp()) / "broken.jpg"
        Image.new("RGB", (8, 8), (10, 20, 30)).save(path, icc_profile=b"garbage")
        self.assertEqual(load_original(path).getpixel((0, 0)), (10, 20, 30))

    def test_raw_files_are_developed(self) -> None:
        class FakeRaw:
            def __enter__(self):
                return self

            def __exit__(self, *_args) -> None:
                return None

            def postprocess(self, **_options):
                import numpy
                return numpy.zeros((6, 4, 3), dtype="uint8")

        path = Path(tempfile.mkdtemp()) / "shot.cr2"
        path.write_bytes(b"not an image")
        with patch("src.imaging.original_image.rawpy.imread", return_value=FakeRaw()):
            self.assertEqual(load_original(path).size, (4, 6))


class ExportBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.originals = _catalog_with_photos((400, 200), (300, 300))
        self.folder = Path(tempfile.mkdtemp()) / "out"

    def test_output_count_matches_the_selection(self) -> None:
        report = export_photos(self.catalog, [1, 2], self.folder, ExportPreset("a", long_edge=64))
        self.assertEqual(len(report.written), 2)
        self.assertEqual(len(list(self.folder.iterdir())), 2)

    def test_missing_original_is_skipped_and_named(self) -> None:
        self.originals[0].unlink()
        report = export_photos(self.catalog, [1, 2], self.folder, BUILT_IN_PRESET)
        self.assertEqual((len(report.written), report.missing), (1, [self.originals[0]]))

    def test_unknown_photo_is_reported_missing(self) -> None:
        report = export_photos(self.catalog, [99], self.folder, BUILT_IN_PRESET)
        self.assertEqual(report.missing, [Path("photo 99")])

    def test_render_failure_is_named_and_others_continue(self) -> None:
        with patch(RENDER_ERROR, side_effect=[OSError("disk"), Image.new("RGB", (4, 4))]):
            report = export_photos(self.catalog, [1, 2], self.folder, BUILT_IN_PRESET)
        self.assertEqual((len(report.written), report.failed), (1, [(self.originals[0], "disk")]))

    def test_same_name_is_not_overwritten(self) -> None:
        export_photos(self.catalog, [1], self.folder, BUILT_IN_PRESET)
        report = export_photos(self.catalog, [1], self.folder, BUILT_IN_PRESET)
        self.assertEqual(report.written[0].name, "frame0-1.jpg")

    def test_renderable_count_ignores_missing_originals(self) -> None:
        self.originals[1].unlink()
        self.assertEqual(renderable_count(self.catalog, [1, 2, 77]), 1)

    def test_export_applies_stored_develop_settings(self) -> None:
        write_develop_settings(self.catalog, 1, encode_crop(CropSettings(left=50)))
        report = export_photos(self.catalog, [1], self.folder, ExportPreset("a", long_edge=0))
        with Image.open(report.written[0]) as opened:
            self.assertEqual(opened.size, (200, 200))

    def test_export_does_not_ingest_or_touch_originals(self) -> None:
        hashes = [content_hash(path) for path in self.originals]
        before = _photo_count(self.catalog)
        export_photos(self.catalog, [1, 2], self.folder, BUILT_IN_PRESET)
        self.assertEqual([content_hash(path) for path in self.originals], hashes)
        self.assertEqual(_photo_count(self.catalog), before)

    def test_libraw_error_is_a_failure_not_a_crash(self) -> None:
        with patch(RENDER_ERROR, side_effect=rawpy.LibRawError("bad")):
            report = export_photos(self.catalog, [1], self.folder, BUILT_IN_PRESET)
        self.assertEqual(len(report.failed), 1)


class MessageTests(unittest.TestCase):
    def test_blockers_are_plain_and_ordered(self) -> None:
        self.assertIn("Select", export_blocker(0, 0, None))
        self.assertIn("original", export_blocker(2, 0, Path("x")))
        self.assertIn("folder", export_blocker(2, 2, None))
        self.assertIsNone(export_blocker(2, 1, Path("x")))

    def test_skip_note(self) -> None:
        self.assertEqual(skip_note(3, 3), "")
        self.assertIn("2 selected", skip_note(3, 1))

    def test_summary_names_missing_and_failed(self) -> None:
        report = ExportReport([Path("a.jpg")], [Path("gone.cr2")], [(Path("bad.cr2"), "oops")])
        text = report_summary(report)
        self.assertIn("Exported 1", text)
        self.assertIn("gone.cr2", text)
        self.assertIn("bad.cr2 (oops)", text)

    def test_summary_of_clean_run(self) -> None:
        self.assertEqual(report_summary(ExportReport([Path("a.jpg")])), "Exported 1 photo(s).")


class ExportDialogTests(unittest.TestCase):
    def setUp(self) -> None:
        from src.ui.dialogs.export_dialog import ExportDialog
        self.dialog_type = ExportDialog
        self.catalog, self.originals = _catalog_with_photos((40, 20), (30, 30))

    def _dialog(self, ids: list[int]):
        return self.dialog_type(None, self.catalog, ids)

    def test_no_selection_disables_commit_with_a_reason(self) -> None:
        dialog = self._dialog([])
        dialog.set_destination(Path("/tmp"))
        self.assertFalse(dialog.commit_button.isEnabled())
        self.assertIn("Select", dialog.reason_label.text())

    def test_no_folder_disables_commit_with_a_reason(self) -> None:
        dialog = self._dialog([1])
        self.assertFalse(dialog.commit_button.isEnabled())
        self.assertIn("folder", dialog.reason_label.text())

    def test_no_renderable_photo_disables_commit(self) -> None:
        self.originals[0].unlink()
        dialog = self._dialog([1])
        dialog.set_destination(Path("/tmp"))
        self.assertFalse(dialog.commit_button.isEnabled())

    def test_ready_dialog_enables_commit_and_notes_skips(self) -> None:
        self.originals[1].unlink()
        dialog = self._dialog([1, 2])
        dialog.set_destination(Path("/tmp"))
        self.assertTrue(dialog.commit_button.isEnabled())
        self.assertIn("1 selected", dialog.reason_label.text())

    def test_dialog_starts_on_the_built_in_preset(self) -> None:
        dialog = self._dialog([1])
        self.assertEqual(dialog.preset(), BUILT_IN_PRESET)

    def test_saved_preset_values_fill_the_form(self) -> None:
        save_preset(self.catalog, TIFF_PRESET)
        dialog = self._dialog([1])
        dialog.preset_combo.setCurrentText("Print")
        dialog._on_preset_chosen(1)
        self.assertEqual(dialog.preset(), TIFF_PRESET)

    def test_save_named_preset_adds_it_and_selects_it(self) -> None:
        dialog = self._dialog([1])
        dialog.long_edge_spin.setValue(777)
        dialog.save_named_preset("Web")
        self.assertEqual(dialog.preset().name, "Web")
        self.assertEqual(list_presets(self.catalog)[1].long_edge, 777)

    def test_saving_over_the_built_in_name_shows_the_reason(self) -> None:
        dialog = self._dialog([1])
        dialog.save_named_preset(BUILT_IN_NAME)
        self.assertIn("built-in", dialog.reason_label.text())

    def test_choose_folder_sets_the_destination(self) -> None:
        dialog = self._dialog([1])
        with patch("src.ui.dialogs.export_dialog.QFileDialog.getExistingDirectory", return_value="/tmp"):
            dialog._choose_folder()
        self.assertEqual(dialog.destination(), Path("/tmp"))
        with patch("src.ui.dialogs.export_dialog.QFileDialog.getExistingDirectory", return_value=""):
            dialog._choose_folder()
        self.assertEqual(dialog.destination(), Path("/tmp"))

    def test_save_preset_asks_for_a_name(self) -> None:
        dialog = self._dialog([1])
        with patch("src.ui.dialogs.export_dialog.QInputDialog.getText", return_value=("Mine", True)):
            dialog._save_preset()
        self.assertEqual(dialog.preset().name, "Mine")
        with patch("src.ui.dialogs.export_dialog.QInputDialog.getText", return_value=("", True)):
            dialog._save_preset()
        self.assertEqual(dialog.preset().name, "Mine")


class LibraryExportTests(unittest.TestCase):
    def _panel(self, catalog: Path):
        from src.ui.panels.library_browser_panel import LibraryBrowserPanel
        panel = LibraryBrowserPanel()
        panel.show_catalog(catalog)
        return panel

    def test_export_without_a_catalog_says_so(self) -> None:
        from src.ui.panels.library_browser_panel import LibraryBrowserPanel
        panel = LibraryBrowserPanel()
        panel._export_selected()
        self.assertIn("catalog", panel.status_label.text())

    def test_accepted_dialog_renders_the_selection(self) -> None:
        from PyQt6.QtWidgets import QDialog
        catalog, _originals = _catalog_with_photos((40, 20))
        panel = self._panel(catalog)
        panel._selected = [Path(f"{1}.jpg")]
        folder = Path(tempfile.mkdtemp())
        with patch("src.ui.panels.library_browser_panel.ExportDialog") as dialog_type:
            dialog = dialog_type.return_value
            dialog.exec.return_value = QDialog.DialogCode.Accepted
            dialog.destination.return_value = folder
            dialog.preset.return_value = BUILT_IN_PRESET
            panel._export_selected()
        self.assertEqual(len(list(folder.iterdir())), 1)
        self.assertIn("Exported 1", panel.status_label.text())

    def test_cancelled_dialog_renders_nothing(self) -> None:
        from PyQt6.QtWidgets import QDialog
        catalog, _originals = _catalog_with_photos((40, 20))
        panel = self._panel(catalog)
        with patch("src.ui.panels.library_browser_panel.ExportDialog") as dialog_type:
            dialog_type.return_value.exec.return_value = QDialog.DialogCode.Rejected
            with patch("src.ui.panels.library_browser_panel.export_photos") as export:
                panel._export_selected()
        export.assert_not_called()


if __name__ == "__main__":
    unittest.main()
