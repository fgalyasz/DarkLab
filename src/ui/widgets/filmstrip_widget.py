from pathlib import Path

from PyQt6.QtCore import QAbstractListModel, QModelIndex, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QListView

CELL_SIZE = QSize(110, 88)


class FilmstripModel(QAbstractListModel):
    def __init__(self) -> None:
        super().__init__()
        self._paths: list[Path] = []
        self._rows: dict[Path, int] | None = None
        self._icons: dict[Path, QIcon] = {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._paths)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        path = self._paths[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return path.name
        if role == Qt.ItemDataRole.DecorationRole:
            return self._icons.get(path, QIcon())
        if role == Qt.ItemDataRole.UserRole:
            return str(path)
        return None

    def set_photos(self, paths: list[Path]) -> None:
        self.beginResetModel()
        self._paths = list(paths)
        self._rows = None
        self._icons = {}
        self.endResetModel()

    def row_of(self, path: Path) -> int | None:
        if self._rows is None:
            self._rows = {known: row for row, known in enumerate(self._paths)}
        return self._rows.get(path)

    def has_icon(self, path: Path) -> bool:
        return path in self._icons

    def set_icon(self, path: Path, pixmap: QPixmap) -> None:
        row = self.row_of(path)
        if row is None:
            return
        self._icons[path] = QIcon(pixmap)
        self.dataChanged.emit(self.index(row), self.index(row), [Qt.ItemDataRole.DecorationRole])

    def clear_icon(self, path: Path) -> None:
        row = self.row_of(path)
        if row is not None and self._icons.pop(path, None) is not None:
            self.dataChanged.emit(self.index(row), self.index(row), [Qt.ItemDataRole.DecorationRole])


class FilmstripWidget(QListView):
    photo_selected = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._model = FilmstripModel()
        self.setModel(self._model)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(False)
        self.setMovement(QListView.Movement.Static)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setUniformItemSizes(True)
        self.setGridSize(CELL_SIZE)
        self.setIconSize(QSize(96, 64))
        self.setSpacing(6)
        self.setFixedHeight(104)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.selectionModel().currentChanged.connect(self._emit_current)

    def count(self) -> int:
        return self._model.rowCount()

    def set_photos(self, paths: list[Path]) -> None:
        self._model.set_photos(paths)

    def has_thumbnail(self, path: Path) -> bool:
        return self._model.has_icon(path)

    def set_thumbnail(self, path: Path, pixmap: QPixmap) -> None:
        self._model.set_icon(path, pixmap)

    def clear_thumbnail(self, path: Path) -> None:
        self._model.clear_icon(path)

    def select_photo(self, path: Path) -> None:
        row = self._model.row_of(path)
        if row is not None:
            self.setCurrentIndex(self._model.index(row))

    def _emit_current(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if current.isValid():
            self.photo_selected.emit(str(current.data(Qt.ItemDataRole.UserRole)))
