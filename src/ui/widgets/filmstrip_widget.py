from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QListWidget, QListWidgetItem


class FilmstripWidget(QListWidget):
    photo_selected = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(False)
        self.setMovement(QListWidget.Movement.Static)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setIconSize(QSize(96, 64))
        self.setSpacing(6)
        self.setFixedHeight(104)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.currentItemChanged.connect(self._emit_current)

    def set_photos(self, paths: list[Path]) -> None:
        self.clear()
        for path in paths:
            self.addItem(self._item(path))

    def set_thumbnail(self, path: Path, pixmap: QPixmap) -> None:
        item = self._find(path)
        if item is not None:
            item.setIcon(QIcon(pixmap))

    def select_photo(self, path: Path) -> None:
        item = self._find(path)
        if item is not None:
            self.setCurrentItem(item)

    def _item(self, path: Path) -> QListWidgetItem:
        item = QListWidgetItem(path.name)
        item.setData(Qt.ItemDataRole.UserRole, str(path))
        item.setSizeHint(QSize(110, 88))
        return item

    def _find(self, path: Path) -> QListWidgetItem | None:
        for index in range(self.count()):
            item = self.item(index)
            if item and item.data(Qt.ItemDataRole.UserRole) == str(path):
                return item
        return None

    def _emit_current(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is not None:
            self.photo_selected.emit(str(current.data(Qt.ItemDataRole.UserRole)))
