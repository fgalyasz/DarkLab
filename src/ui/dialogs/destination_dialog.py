"""Destination settings dialog for import configuration."""
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DestinationSettingsDialog(QDialog):
    """Dialog for managing destination settings presets."""

    ORGANIZE_OPTIONS = (
        ("by_date", "Organize by date into subfolders"),
        ("one_folder", "Copy into one folder (flat)"),
    )

    DATE_FORMAT_OPTIONS = (
        ("%Y.%m.%d", "2026.03.08"),
        ("%Y-%m-%d", "2026-03-08"),
        ("%Y/%m/%d", "2026/03/08"),
        ("%Y\\%m\\%d", "2026\\03\\08"),
        ("%d.%m.%Y", "08.03.2026"),
        ("%d-%m-%Y", "08-03-2026"),
        ("%Y %b %d", "2026 Mar 08"),
        ("%d-%m-%Y", "08-03-2026"),
    )

    def __init__(
        self,
        parent: Optional[QWidget],
        presets: dict[str, dict],
        current_preset_name: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Destination Settings")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setMinimumHeight(380)

        self._presets = {name: dict(settings) for name, settings in presets.items()}
        self._current_preset_name = current_preset_name
        self._selected_preset_name = current_preset_name
        self._selected_settings = dict(self._presets.get(current_preset_name, self._default_settings()))

        self._build_ui()
        self._load_presets_into_combo()
        self._sync_ui_from_settings()

    def _default_settings(self) -> dict:
        return {
            "target_root": "",
            "organize_mode": self.ORGANIZE_OPTIONS[0][0],
            "date_format": self.DATE_FORMAT_OPTIONS[0][0],
            "delete_after_import": False,
        }

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Preset selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Select Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(280)
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # Settings form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Target root
        root_layout = QHBoxLayout()
        self.target_root_edit = QLineEdit()
        self.target_root_edit.textChanged.connect(self._on_settings_changed)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_target_root)
        root_layout.addWidget(self.target_root_edit)
        root_layout.addWidget(browse_btn)
        form_layout.addRow("Target Folder:", root_layout)

        # Organize mode
        self.organize_combo = QComboBox()
        for value, label in self.ORGANIZE_OPTIONS:
            self.organize_combo.addItem(label, value)
        self.organize_combo.currentIndexChanged.connect(self._on_settings_changed)
        form_layout.addRow("Organization:", self.organize_combo)

        # Date format
        self.date_format_combo = QComboBox()
        for value, label in self.DATE_FORMAT_OPTIONS:
            self.date_format_combo.addItem(label, value)
        self.date_format_combo.currentIndexChanged.connect(self._on_settings_changed)
        form_layout.addRow("Date Format:", self.date_format_combo)

        # Delete after import
        self.delete_checkbox = QCheckBox("Delete source files after successful import")
        self.delete_checkbox.setChecked(False)
        self.delete_checkbox.toggled.connect(self._on_settings_changed)
        form_layout.addRow("", self.delete_checkbox)

        layout.addLayout(form_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        self.new_button = QPushButton("New Preset...")
        self.new_button.clicked.connect(self._create_new_preset)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_current_preset)
        self.rename_button = QPushButton("Rename...")
        self.rename_button.clicked.connect(self._rename_current_preset)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._delete_current_preset)
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.rename_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addStretch()
        layout.addWidget(dialog_buttons)

        self._style_widgets()

    def _style_widgets(self) -> None:
        self.setStyleSheet(
            "QDialog { background-color: rgb(40, 40, 45); }"
            "QLabel { color: white; font-size: 12px; }"
            "QLineEdit { color: white; background-color: rgb(68, 68, 74); "
            "border: 1px solid rgb(60, 60, 65); border-radius: 4px; padding: 6px; font-size: 12px; }"
            "QComboBox { color: white; background-color: rgb(68, 68, 74); "
            "border: 1px solid rgb(90, 90, 96); border-radius: 4px; padding: 4px; "
            "min-height: 28px; }"
            "QComboBox::drop-down { border: none; width: 24px; }"
            "QComboBox QAbstractItemView { color: white; background-color: rgb(52, 52, 58); "
            "selection-background-color: rgb(0, 122, 255); }"
            "QPushButton { background-color: rgb(62, 62, 68); color: white; "
            "border: 1px solid rgb(80, 80, 85); border-radius: 4px; padding: 6px 12px; "
            "font-size: 12px; }"
            "QPushButton:hover { background-color: rgb(74, 74, 80); }"
            "QPushButton:disabled { background-color: rgb(50, 50, 55); color: rgb(130, 130, 135); }"
            "QCheckBox { color: white; font-size: 12px; }"
            "QCheckBox::indicator { width: 16px; height: 16px; }"
        )

    def _load_presets_into_combo(self) -> None:
        self.preset_combo.clear()
        sorted_names = sorted(self._presets.keys())
        self.preset_combo.addItems(sorted_names)
        if self._current_preset_name in sorted_names:
            self.preset_combo.setCurrentText(self._current_preset_name)
        elif sorted_names:
            self._current_preset_name = sorted_names[0]
            self.preset_combo.setCurrentIndex(0)
            self._selected_settings = dict(self._presets[self._current_preset_name])

    def _sync_ui_from_settings(self) -> None:
        settings = self._selected_settings
        self.target_root_edit.setText(str(settings.get("target_root", "")))

        organize_mode = str(settings.get("organize_mode", self.ORGANIZE_OPTIONS[0][0]))
        for idx in range(self.organize_combo.count()):
            if self.organize_combo.itemData(idx) == organize_mode:
                self.organize_combo.setCurrentIndex(idx)
                break

        date_format = str(settings.get("date_format", self.DATE_FORMAT_OPTIONS[0][0]))
        for idx in range(self.date_format_combo.count()):
            if self.date_format_combo.itemData(idx) == date_format:
                self.date_format_combo.setCurrentIndex(idx)
                break

        self.delete_checkbox.setChecked(bool(settings.get("delete_after_import", False)))

    def _sync_settings_from_ui(self) -> None:
        self._selected_settings["target_root"] = self.target_root_edit.text().strip()
        self._selected_settings["organize_mode"] = str(self.organize_combo.currentData())
        self._selected_settings["date_format"] = str(self.date_format_combo.currentData())
        self._selected_settings["delete_after_import"] = self.delete_checkbox.isChecked()

    def _on_preset_selected(self, preset_name: str) -> None:
        if not preset_name or preset_name == self._selected_preset_name:
            return
        self._selected_preset_name = preset_name
        self._selected_settings = dict(self._presets.get(preset_name, self._default_settings()))
        self._sync_ui_from_settings()

    def _on_settings_changed(self) -> None:
        self._sync_settings_from_ui()

    def _browse_target_root(self) -> None:
        current = self.target_root_edit.text().strip() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Select Target Folder", current)
        if selected:
            self.target_root_edit.setText(selected)

    def _create_new_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "New Preset", "Enter preset name:")
        if not ok or not name.strip():
            return

        clean_name = name.strip()
        if clean_name in self._presets:
            QMessageBox.warning(self, "Duplicate Name", f"A preset named '{clean_name}' already exists.")
            return

        self._sync_settings_from_ui()
        self._presets[clean_name] = dict(self._selected_settings)
        self._selected_preset_name = clean_name
        self._load_presets_into_combo()
        self.preset_combo.setCurrentText(clean_name)

    def _save_current_preset(self) -> None:
        self._sync_settings_from_ui()
        self._presets[self._selected_preset_name] = dict(self._selected_settings)
        QMessageBox.information(self, "Saved", f"Preset '{self._selected_preset_name}' saved.")

    def _rename_current_preset(self) -> None:
        old_name = self._selected_preset_name
        new_name, ok = QInputDialog.getText(
            self, "Rename Preset", "Enter new name:", text=old_name
        )
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return

        clean_name = new_name.strip()
        if clean_name in self._presets and clean_name != old_name:
            QMessageBox.warning(self, "Duplicate Name", f"A preset named '{clean_name}' already exists.")
            return

        settings = self._presets.pop(old_name)
        self._presets[clean_name] = settings
        self._selected_preset_name = clean_name
        self._load_presets_into_combo()
        self.preset_combo.setCurrentText(clean_name)

    def _delete_current_preset(self) -> None:
        name = self._selected_preset_name
        if len(self._presets) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "At least one preset must remain.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete preset '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        del self._presets[name]
        self._selected_preset_name = sorted(self._presets.keys())[0]
        self._selected_settings = dict(self._presets[self._selected_preset_name])
        self._load_presets_into_combo()
        self._sync_ui_from_settings()

    def get_result(self) -> tuple[str, dict, dict[str, dict]]:
        """Return selected preset name, settings, and all presets."""
        return self._selected_preset_name, dict(self._selected_settings), {k: dict(v) for k, v in self._presets.items()}
