"""Model for representing image thumbnails in a QListView."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QStandardItem, QStandardItemModel


class ImageListModel(QStandardItemModel):
    """Stores image thumbnails with path metadata."""

    PATH_ROLE = Qt.ItemDataRole.UserRole + 1
    PIXMAP_ROLE = Qt.ItemDataRole.UserRole + 2

    def __init__(self) -> None:
        super().__init__()
        self._items_by_path: Dict[str, QStandardItem] = {}

    def add_image(self, image_path: Path, pixmap: QPixmap) -> QStandardItem:
        """Add a thumbnail entry to the model."""
        item = QStandardItem()
        item.setData(str(image_path), self.PATH_ROLE)
        item.setData(pixmap, self.PIXMAP_ROLE)
        item.setData(image_path.name, Qt.ItemDataRole.DisplayRole)
        item.setEditable(False)
        item.setSelectable(True)
        self.appendRow(item)
        self._items_by_path[str(image_path)] = item
        return item

    def clear_images(self) -> None:
        """Clear all thumbnails from the model."""
        self._items_by_path.clear()
        self.clear()

    def get_item(self, image_path: Path) -> Optional[QStandardItem]:
        """Return the stored item for the provided path."""
        return self._items_by_path.get(str(image_path))
