from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from src.exporting.batch import renderable_count
from src.exporting.messages import export_blocker, skip_note
from src.exporting.preset import BUILT_IN_NAME, COLOR_SPACES, FORMATS, ExportPreset
from src.exporting.preset_store import list_presets, save_preset


class ExportDialog(QDialog):
    def __init__(self, parent: QWidget | None, catalog: Path, photo_ids: list[int]) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._selected = len(photo_ids)
        self._renderable = renderable_count(catalog, photo_ids)
        self._folder: Path | None = None
        self.setWindowTitle("Export")
        self._build()
        self._apply_preset(list_presets(catalog)[0])
        self._refresh_commit()

    def preset(self) -> ExportPreset:
        return ExportPreset(
            self._preset_name(), self.format_combo.currentText(), self.long_edge_spin.value(),
            self.color_combo.currentText(), self.sharpen_check.isChecked(), self.watermark_edit.text().strip(),
        )

    def destination(self) -> Path | None:
        return self._folder

    def set_destination(self, folder: Path | None) -> None:
        self._folder = folder
        self.folder_label.setText(str(folder) if folder else "No folder chosen")
        self._refresh_commit()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{self._selected} photo(s) selected."))
        layout.addLayout(self._form())
        layout.addLayout(self._folder_row())
        self.reason_label = QLabel()
        self.reason_label.setWordWrap(True)
        layout.addWidget(self.reason_label)
        layout.addLayout(self._buttons())

    def _form(self) -> QFormLayout:
        form = QFormLayout()
        self.preset_combo = QComboBox()
        self._fill_presets(BUILT_IN_NAME)
        self.preset_combo.activated.connect(self._on_preset_chosen)
        self.format_combo = _combo(FORMATS)
        self.color_combo = _combo(COLOR_SPACES)
        self.long_edge_spin = _long_edge_spin()
        self.sharpen_check = QCheckBox("Sharpen for output")
        self.watermark_edit = QLineEdit()
        for title, widget in self._form_rows():
            form.addRow(title, widget)
        return form

    def _form_rows(self) -> list[tuple[str, QWidget]]:
        return [
            ("Preset", self.preset_combo), ("Format", self.format_combo), ("Color space", self.color_combo),
            ("Long edge (px, 0 = full size)", self.long_edge_spin), ("", self.sharpen_check),
            ("Watermark text", self.watermark_edit),
        ]

    def _folder_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        button = QPushButton("Choose folder...")
        button.clicked.connect(self._choose_folder)
        self.folder_label = QLabel("No folder chosen")
        row.addWidget(button)
        row.addWidget(self.folder_label, 1)
        return row

    def _buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.save_preset_button = _button("Save Preset...", self._save_preset)
        self.commit_button = _button("Export", self.accept)
        row.addWidget(self.save_preset_button)
        row.addStretch()
        row.addWidget(_button("Cancel", self.reject))
        row.addWidget(self.commit_button)
        return row

    def _fill_presets(self, current: str) -> None:
        self.preset_combo.clear()
        for preset in list_presets(self._catalog):
            self.preset_combo.addItem(preset.name)
        self.preset_combo.setCurrentText(current)

    def _preset_name(self) -> str:
        return self.preset_combo.currentText() or BUILT_IN_NAME

    def _on_preset_chosen(self, _row: int) -> None:
        chosen = next(item for item in list_presets(self._catalog) if item.name == self._preset_name())
        self._apply_preset(chosen)

    def _apply_preset(self, preset: ExportPreset) -> None:
        self.format_combo.setCurrentText(preset.format)
        self.color_combo.setCurrentText(preset.color_space)
        self.long_edge_spin.setValue(preset.long_edge)
        self.sharpen_check.setChecked(preset.sharpen)
        self.watermark_edit.setText(preset.watermark)

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Export to")
        if folder:
            self.set_destination(Path(folder))

    def _save_preset(self) -> None:
        name, accepted = QInputDialog.getText(self, "Save Preset", "Preset name")
        if accepted and name.strip():
            self.save_named_preset(name.strip())

    def save_named_preset(self, name: str) -> None:
        try:
            save_preset(self._catalog, replace(self.preset(), name=name))
        except ValueError as error:
            self.reason_label.setText(str(error))
            return
        self._fill_presets(name)

    def _refresh_commit(self) -> None:
        blocker = export_blocker(self._selected, self._renderable, self._folder)
        self.commit_button.setEnabled(blocker is None)
        self.reason_label.setText(blocker or skip_note(self._selected, self._renderable))


def _combo(items: tuple[str, ...]) -> QComboBox:
    combo = QComboBox()
    combo.addItems(items)
    return combo


def _long_edge_spin() -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(0, 20000)
    return spin


def _button(title: str, handler) -> QPushButton:
    button = QPushButton(title)
    button.clicked.connect(handler)
    return button
