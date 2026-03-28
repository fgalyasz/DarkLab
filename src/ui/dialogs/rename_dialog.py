"""Rename pattern dialog for import settings."""
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class RenamePatternDialog(QDialog):
    """Dialog for managing rename patterns/templates."""

    TOKEN_DESCRIPTIONS = (
        ("{filename}", "Original file name without extension"),
        ("{sequence}", "Running index during import using the default 3 digits"),
        ("{sequence:5}", "Running index during import padded to 5 digits"),
        ("{capture_time}", "Capture date and time in yymmdd_HHMMSS format"),
        ("{date}", "Date folder format based on the selected date format"),
    )

    DEFAULT_PATTERN_NAMES = {
        "{filename}": "Original filename",
        "CustomName_{sequence}": "Custom filename + index",
        "{capture_time}": "Capture time + index",
    }

    def __init__(
        self,
        parent: Optional[QWidget],
        templates: dict[str, str],
        current_template_name: str,
        sample_filename: str = "IMG_0001",
        sample_sequence: str = "001",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("File Renaming Pattern")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setMinimumHeight(480)

        self._templates = dict(templates)
        self._current_template_name = current_template_name
        self._sample_filename = sample_filename
        self._sample_sequence = sample_sequence
        self._selected_template_name = current_template_name
        self._selected_pattern = templates.get(current_template_name, "{filename}")

        self._build_ui()
        self._load_templates_into_combo()
        self._update_sample_preview()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Template selection
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Select Pattern:"))
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(280)
        self.template_combo.currentTextChanged.connect(self._on_template_selected)
        template_layout.addWidget(self.template_combo)
        template_layout.addStretch()
        layout.addLayout(template_layout)

        # Pattern editor
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Pattern:"))
        self.pattern_edit = QLineEdit()
        self.pattern_edit.textChanged.connect(self._on_pattern_changed)
        pattern_layout.addWidget(self.pattern_edit)
        layout.addLayout(pattern_layout)

        # Sample preview
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("Preview:"))
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet(
            "color: rgb(100, 200, 100); font-weight: bold; font-size: 13px;"
        )
        preview_layout.addWidget(self.preview_label)
        preview_layout.addStretch()
        layout.addLayout(preview_layout)

        # Token buttons
        layout.addWidget(QLabel("Insert Tokens:"))
        tokens_widget = self._create_tokens_widget()
        layout.addWidget(tokens_widget)

        # Action buttons
        button_layout = QHBoxLayout()
        self.new_button = QPushButton("New Pattern...")
        self.new_button.clicked.connect(self._create_new_pattern)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_current_pattern)
        self.rename_button = QPushButton("Rename...")
        self.rename_button.clicked.connect(self._rename_current_pattern)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._delete_current_pattern)
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

    def _create_tokens_widget(self) -> QWidget:
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMaximumHeight(180)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        tokens_content = QWidget()
        tokens_layout = QVBoxLayout(tokens_content)
        tokens_layout.setContentsMargins(4, 4, 4, 4)
        tokens_layout.setSpacing(6)

        for token, description in self.TOKEN_DESCRIPTIONS:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(12)

            token_btn = QPushButton(token)
            token_btn.setFixedWidth(100)
            token_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            token_btn.clicked.connect(lambda _checked=False, t=token: self._insert_token(t))
            token_btn.setStyleSheet(
                "QPushButton { color: rgb(250, 250, 252); background-color: rgb(86, 96, 112); "
                "border: 1px solid rgb(140, 150, 168); border-radius: 10px; "
                "padding: 4px 10px; font-size: 11px; font-weight: bold; }"
                "QPushButton:hover { background-color: rgb(104, 116, 136); border: 1px solid rgb(176, 186, 204); }"
            )

            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: rgb(210, 210, 214); font-size: 11px;")

            row.addWidget(token_btn)
            row.addWidget(desc_label, 1)
            tokens_layout.addLayout(row)

        tokens_layout.addStretch()
        scroll.setWidget(tokens_content)
        container_layout.addWidget(scroll)

        return container

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
        )

    def _load_templates_into_combo(self) -> None:
        self.template_combo.clear()
        sorted_names = sorted(self._templates.keys())
        self.template_combo.addItems(sorted_names)
        if self._current_template_name in sorted_names:
            self.template_combo.setCurrentText(self._current_template_name)
        elif sorted_names:
            self._current_template_name = sorted_names[0]
            self.template_combo.setCurrentIndex(0)

        pattern = self._templates.get(self._current_template_name, "{filename}")
        self.pattern_edit.setText(pattern)

    def _on_template_selected(self, template_name: str) -> None:
        if not template_name or template_name == self._selected_template_name:
            return
        self._selected_template_name = template_name
        self._selected_pattern = self._templates.get(template_name, "{filename}")
        self.pattern_edit.setText(self._selected_pattern)
        self._update_sample_preview()

    def _on_pattern_changed(self, pattern: str) -> None:
        self._selected_pattern = pattern
        self._update_sample_preview()

    def _insert_token(self, token: str) -> None:
        cursor_pos = self.pattern_edit.cursorPosition()
        text = self.pattern_edit.text()
        new_text = text[:cursor_pos] + token + text[cursor_pos:]
        self.pattern_edit.setText(new_text)
        self.pattern_edit.setCursorPosition(cursor_pos + len(token))

    def _update_sample_preview(self) -> None:
        from datetime import datetime

        pattern = self._selected_pattern or "{filename}"
        sample_date = datetime.now().strftime("%Y.%m.%d")
        sample_capture = datetime.now().strftime("%y%m%d_%H%M%S")

        preview = pattern.replace("{date}", sample_date)
        preview = preview.replace("{capture_time}", sample_capture)
        preview = preview.replace("{filename}", Path(self._sample_filename).stem)
        preview = preview.replace("{sequence}", self._sample_sequence)
        preview = preview.replace("{sequence:5}", "00001")

        self.preview_label.setText(preview)

    def _create_new_pattern(self) -> None:
        name, ok = QInputDialog.getText(self, "New Pattern", "Enter pattern name:")
        if not ok or not name.strip():
            return

        clean_name = name.strip()
        if clean_name in self._templates:
            QMessageBox.warning(self, "Duplicate Name", f"A pattern named '{clean_name}' already exists.")
            return

        self._templates[clean_name] = "{filename}"
        self._selected_template_name = clean_name
        self._selected_pattern = "{filename}"
        self._load_templates_into_combo()
        self.template_combo.setCurrentText(clean_name)
        self.pattern_edit.setText("{filename}")

    def _save_current_pattern(self) -> None:
        self._templates[self._selected_template_name] = self._selected_pattern
        QMessageBox.information(self, "Saved", f"Pattern '{self._selected_template_name}' saved.")

    def _rename_current_pattern(self) -> None:
        old_name = self._selected_template_name
        if old_name in self.DEFAULT_PATTERN_NAMES.values():
            QMessageBox.warning(self, "Cannot Rename", "Default patterns cannot be renamed.")
            return

        new_name, ok = QInputDialog.getText(
            self, "Rename Pattern", "Enter new name:", text=old_name
        )
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return

        clean_name = new_name.strip()
        if clean_name in self._templates and clean_name != old_name:
            QMessageBox.warning(self, "Duplicate Name", f"A pattern named '{clean_name}' already exists.")
            return

        pattern = self._templates.pop(old_name)
        self._templates[clean_name] = pattern
        self._selected_template_name = clean_name
        self._load_templates_into_combo()
        self.template_combo.setCurrentText(clean_name)

    def _delete_current_pattern(self) -> None:
        name = self._selected_template_name
        if name in self.DEFAULT_PATTERN_NAMES.values():
            QMessageBox.warning(self, "Cannot Delete", "Default patterns cannot be deleted.")
            return

        if len(self._templates) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "At least one pattern must remain.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete pattern '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        del self._templates[name]
        self._selected_template_name = sorted(self._templates.keys())[0]
        self._selected_pattern = self._templates[self._selected_template_name]
        self._load_templates_into_combo()

    def get_result(self) -> tuple[str, str, dict[str, str]]:
        """Return selected template name, pattern, and all templates."""
        return self._selected_template_name, self._selected_pattern, dict(self._templates)
