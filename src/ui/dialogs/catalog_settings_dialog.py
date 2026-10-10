from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QVBoxLayout, QWidget,
)

from src.catalog.startup_policy import ASK, FIXED, RECENT, fixed_catalog_error, normalize_mode
from src.ui.catalog_filter import CATALOG_FILTER


class CatalogSettingsDialog(QDialog):
    def __init__(self, settings: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Catalog Settings")
        self._create_fields()
        self._build()
        self._apply_settings(settings)
        self._fixed.toggled.connect(self._sync_path_enabled)

    def chosen_mode(self) -> str:
        if self._ask.isChecked():
            return ASK
        if self._fixed.isChecked():
            return FIXED
        return RECENT

    def chosen_fixed_path(self) -> str:
        return self._path.text().strip()

    def _create_fields(self) -> None:
        self._ask = QRadioButton("Always ask which catalog to open")
        self._recent = QRadioButton("Open the most recent catalog")
        self._fixed = QRadioButton("Always open this catalog")
        self._path = QLineEdit()
        self._path.setReadOnly(True)
        self._error = QLabel("")

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        self._add_modes(layout)
        self._add_path(layout)
        layout.addWidget(self._error)
        self._add_buttons(layout)

    def _add_modes(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._ask)
        layout.addWidget(self._recent)
        layout.addWidget(self._fixed)

    def _add_path(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._path)

    def _add_buttons(self, layout: QVBoxLayout) -> None:
        row = QHBoxLayout()
        self._add_browse(row)
        row.addStretch()
        self._add_dismiss(row)
        layout.addLayout(row)

    def _add_browse(self, row: QHBoxLayout) -> None:
        self._browse = QPushButton("Choose...")
        self._browse.clicked.connect(self._browse_catalog)
        row.addWidget(self._browse)

    def _add_dismiss(self, row: QHBoxLayout) -> None:
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("OK")
        ok.clicked.connect(self._accept_if_valid)
        row.addWidget(cancel)
        row.addWidget(ok)

    def _apply_settings(self, settings: dict[str, str]) -> None:
        mode = normalize_mode(settings.get("startup_mode", ""))
        self._button_for(mode).setChecked(True)
        self._path.setText(settings.get("fixed_catalog", ""))
        self._sync_path_enabled()

    def _button_for(self, mode: str) -> QRadioButton:
        if mode == ASK:
            return self._ask
        if mode == FIXED:
            return self._fixed
        return self._recent

    def _sync_path_enabled(self) -> None:
        enabled = self._fixed.isChecked()
        self._path.setEnabled(enabled)
        self._browse.setEnabled(enabled)

    def _browse_catalog(self) -> None:
        selected, _chosen = QFileDialog.getOpenFileName(self, "Catalog", self._path.text(), CATALOG_FILTER)
        if selected == "":
            return
        self._path.setText(selected)
        self._fixed.setChecked(True)

    def _accept_if_valid(self) -> None:
        if self.chosen_mode() != FIXED:
            self._error.setText("")
            self.accept()
            return
        self._accept_fixed_path()

    def _accept_fixed_path(self) -> None:
        message = fixed_catalog_error(self.chosen_fixed_path())
        if message is None:
            self._error.setText("")
            self.accept()
            return
        self._error.setText(message)
