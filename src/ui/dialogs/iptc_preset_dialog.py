"""IPTC preset management dialog."""

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QGroupBox,
)

from src.models.iptc_data import IPTCData, IPTCPreset, get_default_iptc_preset

logger = logging.getLogger(__name__)


class IPTCPresetDialog(QDialog):
    """Dialog for managing IPTC presets."""

    def __init__(
        self,
        presets: dict[str, IPTCPreset],
        active_preset_name: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("IPTC Presets")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self.presets = dict(presets)  # Copy to avoid modifying original
        self.active_preset_name = active_preset_name
        self.selected_preset_name: Optional[str] = None

        self._setup_ui()
        self._load_presets_list()

        # Select active preset
        if active_preset_name in self.presets:
            items = self.preset_list.findItems(active_preset_name, Qt.MatchFlag.MatchExactly)
            if items:
                self.preset_list.setCurrentItem(items[0])

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        # Left side - Preset list
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        preset_label = QLabel("Presets:")
        left_layout.addWidget(preset_label)

        self.preset_list = QListWidget()
        self.preset_list.currentItemChanged.connect(self._on_preset_selected)
        left_layout.addWidget(self.preset_list)

        # Preset buttons
        preset_btn_layout = QHBoxLayout()

        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self._on_new_preset)
        preset_btn_layout.addWidget(self.new_btn)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._on_rename_preset)
        preset_btn_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_preset)
        preset_btn_layout.addWidget(self.delete_btn)

        left_layout.addLayout(preset_btn_layout)

        layout.addLayout(left_layout, 1)

        # Right side - IPTC data editor
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # Preset name label
        self.name_label = QLabel("No preset selected")
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(self.name_label)

        # IPTC fields
        iptc_group = QGroupBox("IPTC Metadata")
        iptc_layout = QVBoxLayout(iptc_group)
        iptc_layout.setSpacing(8)

        # Creator (Photographer)
        creator_layout = QHBoxLayout()
        creator_layout.addWidget(QLabel("Creator:"))
        self.creator_input = QLineEdit()
        self.creator_input.textChanged.connect(self._on_field_changed)
        creator_layout.addWidget(self.creator_input)
        iptc_layout.addLayout(creator_layout)

        # Copyright
        copyright_layout = QHBoxLayout()
        copyright_layout.addWidget(QLabel("Copyright:"))
        self.copyright_input = QLineEdit()
        self.copyright_input.textChanged.connect(self._on_field_changed)
        copyright_layout.addWidget(self.copyright_input)
        iptc_layout.addLayout(copyright_layout)

        # Credit
        credit_layout = QHBoxLayout()
        credit_layout.addWidget(QLabel("Credit:"))
        self.credit_input = QLineEdit()
        self.credit_input.textChanged.connect(self._on_field_changed)
        credit_layout.addWidget(self.credit_input)
        iptc_layout.addLayout(credit_layout)

        # Source
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))
        self.source_input = QLineEdit()
        self.source_input.textChanged.connect(self._on_field_changed)
        source_layout.addWidget(self.source_input)
        iptc_layout.addLayout(source_layout)

        # Keywords
        keywords_label = QLabel("Keywords (one per line):")
        iptc_layout.addWidget(keywords_label)

        self.keywords_input = QTextEdit()
        self.keywords_input.setMaximumHeight(120)
        self.keywords_input.textChanged.connect(self._on_field_changed)
        iptc_layout.addWidget(self.keywords_input)

        right_layout.addWidget(iptc_group)

        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        right_layout.addLayout(btn_layout)
        right_layout.addStretch()

        layout.addLayout(right_layout, 2)

    def _load_presets_list(self) -> None:
        """Load presets into the list widget."""
        self.preset_list.clear()
        for name in sorted(self.presets.keys()):
            item = QListWidgetItem(name)
            self.preset_list.addItem(item)
            if name == self.active_preset_name:
                item.setSelected(True)
                self.preset_list.setCurrentItem(item)

    def _on_preset_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]) -> None:
        """Handle preset selection change."""
        if current is None:
            self.name_label.setText("No preset selected")
            self._set_inputs_enabled(False)
            return

        preset_name = current.text()
        preset = self.presets.get(preset_name)

        if preset is None:
            return

        self.name_label.setText(f"Preset: {preset_name}")
        self._set_inputs_enabled(True)

        # Load data into fields (block signals to avoid marking as modified)
        self.creator_input.blockSignals(True)
        self.copyright_input.blockSignals(True)
        self.credit_input.blockSignals(True)
        self.source_input.blockSignals(True)
        self.keywords_input.blockSignals(True)

        self.creator_input.setText(preset.data.creator)
        self.copyright_input.setText(preset.data.copyright)
        self.credit_input.setText(preset.data.credit)
        self.source_input.setText(preset.data.source)
        self.keywords_input.setPlainText(preset.data.get_keywords_text())

        self.creator_input.blockSignals(False)
        self.copyright_input.blockSignals(False)
        self.credit_input.blockSignals(False)
        self.source_input.blockSignals(False)
        self.keywords_input.blockSignals(False)

        # Update button states
        is_default = preset.is_default
        self.rename_btn.setEnabled(not is_default)
        self.delete_btn.setEnabled(not is_default)

    def _set_inputs_enabled(self, enabled: bool) -> None:
        """Enable or disable input fields."""
        self.creator_input.setEnabled(enabled)
        self.copyright_input.setEnabled(enabled)
        self.credit_input.setEnabled(enabled)
        self.source_input.setEnabled(enabled)
        self.keywords_input.setEnabled(enabled)

    def _on_field_changed(self) -> None:
        """Handle field value change."""
        current_item = self.preset_list.currentItem()
        if current_item is None:
            return

        preset_name = current_item.text()
        preset = self.presets.get(preset_name)
        if preset is None:
            return

        # Update preset data from fields
        preset.data.creator = self.creator_input.text()
        preset.data.copyright = self.copyright_input.text()
        preset.data.credit = self.credit_input.text()
        preset.data.source = self.source_input.text()
        preset.data.set_keywords_from_text(self.keywords_input.toPlainText())

    def _on_new_preset(self) -> None:
        """Create a new preset."""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "New Preset", "Enter preset name:")
        if not ok or not name.strip():
            return

        name = name.strip()
        if name in self.presets:
            QMessageBox.warning(self, "Duplicate Name", f"A preset named '{name}' already exists.")
            return

        # Create new preset with empty data
        new_preset = IPTCPreset(name=name, data=IPTCData())
        self.presets[name] = new_preset

        # Add to list and select
        item = QListWidgetItem(name)
        self.preset_list.addItem(item)
        self.preset_list.setCurrentItem(item)

    def _on_rename_preset(self) -> None:
        """Rename the selected preset."""
        from PyQt6.QtWidgets import QInputDialog

        current_item = self.preset_list.currentItem()
        if current_item is None:
            return

        old_name = current_item.text()
        preset = self.presets.get(old_name)
        if preset is None or preset.is_default:
            return

        new_name, ok = QInputDialog.getText(
            self, "Rename Preset", "Enter new name:", text=old_name
        )
        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()
        if new_name == old_name:
            return
        if new_name in self.presets:
            QMessageBox.warning(self, "Duplicate Name", f"A preset named '{new_name}' already exists.")
            return

        # Update preset name and move in dict
        preset.name = new_name
        self.presets[new_name] = self.presets.pop(old_name)

        # Update active preset name if needed
        if self.active_preset_name == old_name:
            self.active_preset_name = new_name

        # Update list item
        current_item.setText(new_name)

    def _on_delete_preset(self) -> None:
        """Delete the selected preset."""
        current_item = self.preset_list.currentItem()
        if current_item is None:
            return

        preset_name = current_item.text()
        preset = self.presets.get(preset_name)
        if preset is None or preset.is_default:
            return

        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to delete the preset '{preset_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.presets[preset_name]
            self.preset_list.takeItem(self.preset_list.row(current_item))

            # Update active preset name if needed
            if self.active_preset_name == preset_name:
                self.active_preset_name = "Default"

    def _on_save(self) -> None:
        """Save presets and return."""
        current_item = self.preset_list.currentItem()
        if current_item:
            self.selected_preset_name = current_item.text()
        else:
            self.selected_preset_name = "Default"

        self.accept()

    def get_presets(self) -> dict[str, IPTCPreset]:
        """Get the updated presets dictionary."""
        return self.presets

    def get_selected_preset_name(self) -> str:
        """Get the name of the selected preset."""
        return self.selected_preset_name or "Default"
