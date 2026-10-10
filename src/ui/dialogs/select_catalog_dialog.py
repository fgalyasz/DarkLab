from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from src.catalog.database import create_catalog, open_catalog
from src.ui.catalog_filter import CATALOG_FILTER


class SelectCatalogDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Select Catalog")
        self._chosen: Path | None = None
        self._error = QLabel("")
        self._build()

    @classmethod
    def pick(cls) -> Path | None:
        dialog = cls()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog._chosen

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("DarkLab needs a catalog before it can open."))
        layout.addWidget(self._error)
        self._add_buttons(layout)

    def _add_buttons(self, layout: QVBoxLayout) -> None:
        row = QHBoxLayout()
        self._add_button(row, "Open Catalog...", self._open_existing)
        self._add_button(row, "New Catalog...", self._create_new)
        self._add_button(row, "Quit", self._quit)
        layout.addLayout(row)

    def _add_button(self, row: QHBoxLayout, label: str, slot: object) -> None:
        button = QPushButton(label)
        button.clicked.connect(slot)
        row.addWidget(button)

    def _open_existing(self) -> None:
        selected, _chosen = QFileDialog.getOpenFileName(self, "Open Catalog", "", CATALOG_FILTER)
        if selected == "":
            return
        self._try_open(Path(selected))

    def _create_new(self) -> None:
        selected, _chosen = QFileDialog.getSaveFileName(self, "New Catalog", "", CATALOG_FILTER)
        if selected == "":
            return
        self._try_create(Path(selected))

    def _try_open(self, path: Path) -> None:
        try:
            self._choose(open_catalog(path))
        except (OSError, ValueError, FileNotFoundError) as error:
            self._error.setText(str(error))

    def _try_create(self, path: Path) -> None:
        try:
            self._choose(create_catalog(path))
        except OSError as error:
            self._error.setText(str(error))

    def _choose(self, path: Path) -> None:
        self._chosen = path
        self._error.setText("")
        self.accept()

    def _quit(self) -> None:
        self._chosen = None
        self.reject()
