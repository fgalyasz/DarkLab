from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from src.catalog.catalog_folders import CatalogFolder

MISSING_SUFFIX = "MISSING"


def folder_text(folder: CatalogFolder) -> str:
    name = folder.path.name or str(folder.path)
    text = f"{name} ({len(folder.photo_ids)})"
    return f"{text} - {MISSING_SUFFIX}" if folder.is_missing else text


class CatalogFolderPanel(QWidget):
    folder_chosen = pyqtSignal(object)
    relink_requested = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self._folders: dict[Path, CatalogFolder] = {}
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._on_current)
        self.relink_button = QPushButton("Relink Folder...")
        self.relink_button.setEnabled(False)
        self.relink_button.clicked.connect(self._request_relink)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.relink_button)

    def set_folders(self, folders: list[CatalogFolder], chosen: Path | None = None) -> None:
        self._folders = {folder.path: folder for folder in folders}
        self.list.blockSignals(True)
        self._fill_list(folders, chosen)
        self.list.blockSignals(False)
        self._sync_relink_button()

    def selected_folder(self) -> Path | None:
        item = self.list.currentItem()
        return None if item is None else item.data(Qt.ItemDataRole.UserRole)

    def clear_selection(self) -> None:
        self.list.blockSignals(True)
        self.list.setCurrentItem(None)
        self.list.blockSignals(False)
        self._sync_relink_button()

    def _fill_list(self, folders: list[CatalogFolder], chosen: Path | None) -> None:
        self.list.clear()
        for folder in folders:
            self.list.addItem(_folder_item(folder))
        self._restore_selection(chosen)

    def _restore_selection(self, chosen: Path | None) -> None:
        for row in range(self.list.count()):
            if self.list.item(row).data(Qt.ItemDataRole.UserRole) == chosen:
                self.list.setCurrentRow(row)

    def _on_current(self, item: QListWidgetItem | None) -> None:
        self._sync_relink_button()
        if item is not None:
            self.folder_chosen.emit(item.data(Qt.ItemDataRole.UserRole))

    def _sync_relink_button(self) -> None:
        chosen = self._folders.get(self.selected_folder())
        self.relink_button.setEnabled(chosen is not None and chosen.is_missing)

    def _request_relink(self) -> None:
        chosen = self.selected_folder()
        if chosen is not None:
            self.relink_requested.emit(chosen)


def _folder_item(folder: CatalogFolder) -> QListWidgetItem:
    item = QListWidgetItem(folder_text(folder))
    item.setData(Qt.ItemDataRole.UserRole, folder.path)
    item.setToolTip(str(folder.path))
    return item
