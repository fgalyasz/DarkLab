import shutil
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThreadPool, pyqtSignal
from PyQt6.QtGui import QImage, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QPushButton, QScrollArea, QSlider, QSplitter, QStackedWidget,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from src.config.config_manager import ConfigManager
from src.catalog.index_images import list_index_images
from src.catalog.removal import photo_id_of_index, remove_indexes
from src.ui.dialogs.removal_choice_dialog import RemovalChoiceDialog
from src.ui.dialogs.import_dialog import ImageDiscoveryThread, ImageProcessorRunnable
from src.ui.import_summary import byte_total, format_byte_count
from src.ui.library_catalog import (
    filter_paths, keyword_tokens, matches_rating, pictures_directory, sort_paths,
)
from src.ui.panels.base_panel import BasePanel
from src.ui.themes import StyleSheet
from src.ui.preview_image import tone_image
from src.ui.widgets.collapsible_section import CollapsibleSection, PanelColumn
from src.ui.widgets.filmstrip_widget import FilmstripWidget
from src.ui.widgets.grid_image_widget import GridImageWidget
from src.ui.widgets.histogram_widget import HistogramWidget


class ThumbRelay(QObject):
    def __init__(self, panel: "LibraryBrowserPanel", session: int) -> None:
        super().__init__()
        self._panel = panel
        self._session = session

    def receive(self, path: str, _name: str, image: QImage) -> None:
        self._panel._on_thumb(path, image, self._session)


class SourceFolderTree(QTreeWidget):
    folder_chosen = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setHeaderHidden(True)
        self.itemClicked.connect(self._choose)
        self.itemExpanded.connect(self._expand)

    def add_root(self, path: Path) -> None:
        item = make_folder_item(path)
        if item is not None:
            self.addTopLevelItem(item)

    def _choose(self, item: QTreeWidgetItem) -> None:
        folder = item.data(0, Qt.ItemDataRole.UserRole)
        if folder:
            self.folder_chosen.emit(str(folder))

    def _expand(self, item: QTreeWidgetItem) -> None:
        if not _remove_placeholder(item):
            return
        folder = item.data(0, Qt.ItemDataRole.UserRole)
        if folder:
            _append_children(item, Path(str(folder)))


class LibraryBrowserPanel(BasePanel):
    import_requested = pyqtSignal()
    catalog_changed = pyqtSignal()

    def __init__(self) -> None:
        self._config = ConfigManager()
        self._catalog: Path | None = None
        self._images: list[Path] = []
        self._selected: list[Path] = []
        self._thumbs: dict[Path, QPixmap] = {}
        self._keywords: dict[str, str] = {}
        self._comments: dict[str, str] = {}
        self._active_path = ""
        self._navigator_image = QImage()
        self._exposure = 0
        self._contrast = 0
        self._view = "grid"
        self._session = 0
        self._syncing = False
        self._notes_locked = False
        self._discovery: ImageDiscoveryThread | None = None
        self._relays: list[ThumbRelay] = []
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(4)
        super().__init__("library")

    def _setup_ui(self) -> None:
        self.setStyleSheet(_library_style())
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._workspace(), 1)
        root.addWidget(self._build_filmstrip())
        root.addWidget(self._build_toolbar())
        self._bind_removal_keys()
        self._populate_folders()
        self._load_all_photographs()

    def _workspace(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._left_column())
        splitter.addWidget(self._center_column())
        splitter.addWidget(self._right_column())
        splitter.setSizes([250, 860, 280])
        return splitter

    def _left_column(self) -> PanelColumn:
        column = PanelColumn()
        self.navigator = self._navigator_label()
        self.catalog = self._catalog_list()
        self.folders = SourceFolderTree()
        self.folders.folder_chosen.connect(self._load_folder)
        self.collections = self._static_list(["Quick Collection"])
        self.publish = self._static_list(["Hard Drive", "Flickr"])
        column.add_section(CollapsibleSection("Navigator", self.navigator))
        column.add_section(CollapsibleSection("Catalog", self.catalog))
        column.add_section(CollapsibleSection("Folders", self.folders, fill=True), 1)
        column.add_section(CollapsibleSection("Collections", self.collections))
        column.add_section(CollapsibleSection("Publish Services", self.publish))
        return column

    def _center_column(self) -> QWidget:
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._filter_bar())
        layout.addWidget(self._center_stack(), 1)
        return column

    def _right_column(self) -> PanelColumn:
        column = PanelColumn()
        self.histogram = HistogramWidget()
        column.add_section(CollapsibleSection("Histogram", self.histogram))
        column.add_section(CollapsibleSection("Quick Develop", self._quick_develop()))
        column.add_section(CollapsibleSection("Keywording", self._keyword_editor()))
        column.add_section(CollapsibleSection("Keyword List", self._keyword_list(), fill=True), 1)
        column.add_section(CollapsibleSection("Metadata", self._metadata_form()))
        column.add_section(CollapsibleSection("Comments", self._comments_editor()))
        return column

    def _navigator_label(self) -> QLabel:
        label = QLabel("No photo selected")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMinimumHeight(150)
        label.setStyleSheet("background-color: rgb(28, 28, 28); color: rgb(160, 160, 160);")
        return label

    def _catalog_list(self) -> QListWidget:
        catalog = QListWidget()
        catalog.addItem("All Photographs")
        catalog.addItem("Previous Import")
        catalog.setFixedHeight(72)
        catalog.currentRowChanged.connect(self._on_catalog)
        return catalog

    def _static_list(self, names: list[str]) -> QListWidget:
        widget = QListWidget()
        for name in names:
            widget.addItem(name)
        widget.setFixedHeight(28 * max(1, len(names)) + 8)
        return widget

    def _filter_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(36)
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 4, 8, 4)
        row.addWidget(QLabel("Library Filter"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filename")
        self.filter_edit.textChanged.connect(self._refresh_grid)
        self.rating_combo = self._rating_combo()
        row.addWidget(self.filter_edit, 1)
        row.addWidget(self.rating_combo)
        return bar

    def _rating_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.addItem("Rating: Any", "any")
        for stars in range(1, 6):
            combo.addItem(f"{stars}+ stars", str(stars))
        combo.currentIndexChanged.connect(self._refresh_grid)
        return combo

    def _center_stack(self) -> QStackedWidget:
        self.center_stack = QStackedWidget()
        self.grid_scroll = _scroll(self._build_grid())
        self.loupe = QLabel("Select a photo.")
        self.loupe.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_stack.addWidget(self.grid_scroll)
        self.center_stack.addWidget(self.loupe)
        return self.center_stack

    def _build_grid(self) -> GridImageWidget:
        self.grid = GridImageWidget()
        self.grid.selection_changed.connect(self._on_grid_selection)
        return self.grid

    def _quick_develop(self) -> QWidget:
        panel = QWidget()
        form = QFormLayout(panel)
        self.exposure_slider = self._tone_slider()
        self.contrast_slider = self._tone_slider()
        reset = QPushButton("Reset")
        reset.clicked.connect(self._reset_tone)
        form.addRow("Exposure", self.exposure_slider)
        form.addRow("Contrast", self.contrast_slider)
        form.addRow("", reset)
        return panel

    def _tone_slider(self) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(-100, 100)
        slider.setValue(0)
        slider.valueChanged.connect(self._apply_tone)
        return slider

    def _keyword_editor(self) -> QTextEdit:
        self.keywords_edit = QTextEdit()
        self.keywords_edit.setFixedHeight(70)
        self.keywords_edit.setPlaceholderText("Keywords, one per line")
        self.keywords_edit.textChanged.connect(self._on_keywords_changed)
        return self.keywords_edit

    def _keyword_list(self) -> QListWidget:
        self.keyword_list = QListWidget()
        self.keyword_list.setFixedHeight(90)
        return self.keyword_list

    def _metadata_form(self) -> QWidget:
        panel = QWidget()
        form = QFormLayout(panel)
        self.meta_name = QLabel("-")
        self.meta_folder = QLabel("-")
        self.meta_dimensions = QLabel("-")
        self.meta_size = QLabel("-")
        self.meta_modified = QLabel("-")
        form.addRow("File Name", self.meta_name)
        form.addRow("Folder", self.meta_folder)
        form.addRow("Dimensions", self.meta_dimensions)
        form.addRow("Size", self.meta_size)
        form.addRow("Modified", self.meta_modified)
        return panel

    def _comments_editor(self) -> QTextEdit:
        self.comments_edit = QTextEdit()
        self.comments_edit.setFixedHeight(70)
        self.comments_edit.textChanged.connect(self._remember_notes)
        return self.comments_edit

    def _build_filmstrip(self) -> FilmstripWidget:
        self.filmstrip = FilmstripWidget()
        self.filmstrip.photo_selected.connect(self._on_filmstrip)
        return self.filmstrip

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(40)
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 4, 8, 4)
        self.status_label = QLabel("0 photos")
        row.addWidget(self.status_label)
        row.addWidget(self._tool_button("Import...", self._request_import))
        self.remove_button = self._tool_button("Remove...", self._ask_removal)
        self.remove_button.setEnabled(False)
        row.addWidget(self.remove_button)
        row.addWidget(self._tool_button("Export...", self._export_selected))
        self.grid_button = self._view_button("Grid", "grid")
        self.loupe_button = self._view_button("Loupe", "loupe")
        self.grid_button.setChecked(True)
        row.addWidget(self.grid_button)
        row.addWidget(self.loupe_button)
        row.addStretch()
        row.addWidget(QLabel("Sort"))
        self.sort_combo = self._sort_combo()
        self.thumb_slider = self._thumb_slider()
        row.addWidget(self.sort_combo)
        row.addWidget(QLabel("Thumbnails"))
        row.addWidget(self.thumb_slider)
        return bar

    def _tool_button(self, title: str, handler) -> QPushButton:
        button = QPushButton(title)
        button.clicked.connect(handler)
        return button

    def _view_button(self, title: str, view: str) -> QPushButton:
        button = QPushButton(title)
        button.setCheckable(True)
        button.setProperty("view", view)
        button.clicked.connect(self._on_view_clicked)
        return button

    def _sort_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.addItem("Capture Time", "time")
        combo.addItem("File Name", "name")
        combo.currentIndexChanged.connect(self._refresh_grid)
        return combo

    def _thumb_slider(self) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(2, 10)
        slider.setValue(6)
        slider.setFixedWidth(120)
        slider.valueChanged.connect(self._apply_grid)
        return slider

    def _populate_folders(self) -> None:
        self.folders.add_root(pictures_directory())
        if Path.home() != pictures_directory():
            self.folders.add_root(Path.home())
        if Path("/Volumes").is_dir():
            self.folders.add_root(Path("/Volumes"))

    def _on_catalog(self, row: int) -> None:
        if row == 0:
            self._load_all_photographs()
        if row == 1:
            self._load_previous_import()

    def show_catalog(self, catalog: Path | None) -> None:
        self._catalog = catalog
        self._load_all_photographs()

    def _load_all_photographs(self) -> None:
        self._cancel_load()
        self._show_paths(self._catalog_indexes())

    def _catalog_indexes(self) -> list[Path]:
        if self._catalog is None:
            return []
        return list_index_images(self._catalog)

    def _load_previous_import(self) -> None:
        self._load_all_photographs()

    def _load_folder(self, _folder: str) -> None:
        self._load_all_photographs()

    def _show_paths(self, paths: list[Path]) -> None:
        self._images = list(paths)
        self._selected = []
        self._refresh_grid()
        self._start_thumbs()

    def _refresh_grid(self) -> None:
        if not hasattr(self, "grid"):
            return
        visible = self._visible_images()
        self.grid.set_images(visible)
        self.filmstrip.set_photos(visible)
        self._restore_thumbs(visible)
        self._apply_grid()
        self._update_status()

    def _visible_images(self) -> list[Path]:
        named = filter_paths(self._images, self.filter_edit.text())
        rated = [path for path in named if self._rating_ok(path)]
        return sort_paths(rated, str(self.sort_combo.currentData()))

    def _rating_ok(self, path: Path) -> bool:
        marker = self.grid.image_markers.get(path, {}).get("rating", "0")
        return matches_rating(str(marker), str(self.rating_combo.currentData()))

    def _restore_thumbs(self, paths: list[Path]) -> None:
        for path in paths:
            pixmap = self._thumbs.get(path)
            if pixmap is not None:
                self.grid.set_thumbnail(path, pixmap)
                self.filmstrip.set_thumbnail(path, pixmap)

    def _start_thumbs(self) -> None:
        self._session += 1
        session = self._session
        self._relays.clear()
        for index, path in enumerate(self.grid.images):
            self._queue_thumb(path, index, session)

    def _queue_thumb(self, path: Path, index: int, session: int) -> None:
        relay = ThumbRelay(self, session)
        runnable = ImageProcessorRunnable([str(path)], index, 280)
        runnable.signals.image_found.connect(relay.receive)
        self._relays.append(relay)
        self._pool.start(runnable)

    def _on_thumb(self, path: str, image: QImage, session: int) -> None:
        if session != self._session or image.isNull():
            return
        photo = Path(path)
        pixmap = QPixmap.fromImage(image)
        self._thumbs[photo] = pixmap
        self.grid.set_thumbnail(photo, pixmap)
        self.filmstrip.set_thumbnail(photo, pixmap)
        if self._selected and self._selected[-1] == photo:
            self._set_navigator(image)

    def _cancel_load(self) -> None:
        self._session += 1
        self._relays.clear()
        if self._discovery and self._discovery.isRunning():
            self._discovery.cancel()
            self._discovery.wait(300)
        self._pool.clear()

    def _on_grid_selection(self, paths: list) -> None:
        self._remember_notes()
        self._selected = [Path(path) for path in paths]
        self._sync_filmstrip()
        self._show_selection()
        self._update_status()

    def _on_filmstrip(self, path: str) -> None:
        if self._syncing:
            return
        photo = Path(path)
        self.grid.set_selected_images([photo])
        self._on_grid_selection([photo])

    def _sync_filmstrip(self) -> None:
        if not self._selected:
            return
        self._syncing = True
        self.filmstrip.select_photo(self._selected[-1])
        self._syncing = False

    def _show_selection(self) -> None:
        if not self._selected:
            self._clear_selection_panels()
            return
        path = self._selected[-1]
        self._active_path = str(path)
        self._load_notes(self._active_path)
        self._fill_metadata(path)
        self._set_navigator(self._image_for(path))

    def _clear_selection_panels(self) -> None:
        self._active_path = ""
        self._navigator_image = QImage()
        self.navigator.setText("No photo selected")
        self.histogram.clear_histogram()
        self.meta_name.setText("-")
        self.meta_folder.setText("-")

    def _image_for(self, path: Path) -> QImage:
        pixmap = self._thumbs.get(path)
        if pixmap is None:
            return QImage()
        return pixmap.toImage()

    def _set_navigator(self, image: QImage) -> None:
        self._navigator_image = image
        self._paint_previews()
        if self._selected:
            self.meta_dimensions.setText(f"{image.width()} x {image.height()}")

    def _apply_tone(self) -> None:
        self._exposure = self.exposure_slider.value()
        self._contrast = self.contrast_slider.value()
        self._paint_previews()

    def _reset_tone(self) -> None:
        self.exposure_slider.setValue(0)
        self.contrast_slider.setValue(0)

    def _paint_previews(self) -> None:
        image = tone_image(self._navigator_image, self._exposure, self._contrast)
        _show_pixmap(self.navigator, image, self.navigator.size())
        self.histogram.set_image(image)
        if self._view == "loupe":
            _show_pixmap(self.loupe, image, self.loupe.size())

    def _fill_metadata(self, path: Path) -> None:
        self.meta_name.setText(path.name)
        self.meta_folder.setText(str(path.parent))
        self.meta_size.setText(format_byte_count(byte_total([path])))
        self.meta_modified.setText(_modified_text(path))

    def _load_notes(self, path: str) -> None:
        self._notes_locked = True
        self.keywords_edit.setPlainText(self._keywords.get(path, ""))
        self.comments_edit.setPlainText(self._comments.get(path, ""))
        self._fill_keyword_list(self.keywords_edit.toPlainText())
        self._notes_locked = False

    def _remember_notes(self) -> None:
        if self._notes_locked or not self._active_path:
            return
        self._keywords[self._active_path] = self.keywords_edit.toPlainText()
        self._comments[self._active_path] = self.comments_edit.toPlainText()

    def _on_keywords_changed(self) -> None:
        self._remember_notes()
        if not self._notes_locked:
            self._fill_keyword_list(self.keywords_edit.toPlainText())

    def _fill_keyword_list(self, text: str) -> None:
        self.keyword_list.clear()
        for token in keyword_tokens(text):
            self.keyword_list.addItem(token)

    def _on_view_clicked(self) -> None:
        button = self.sender()
        if isinstance(button, QPushButton):
            self._show_view(str(button.property("view")))

    def _show_view(self, view: str) -> None:
        self._view = view
        self.center_stack.setCurrentIndex(0 if view == "grid" else 1)
        self.grid_button.setChecked(view == "grid")
        self.loupe_button.setChecked(view == "loupe")
        self._paint_previews()

    def _apply_grid(self) -> None:
        columns = max(2, 12 - self.thumb_slider.value())
        width = max(240, self.grid_scroll.viewport().width())
        cell = max(90, (width - (columns - 1) * 8) // columns)
        self.grid.set_grid_layout(columns, cell, int(cell * 1.08) + 42, 8, 0, 0)

    def _update_status(self) -> None:
        visible = len(self.grid.images)
        selected = len(self._selected)
        self._sync_remove_button()
        if selected:
            self.status_label.setText(f"{selected} of {visible} photos")
            return
        self.status_label.setText(f"{visible} photos")

    def _sync_remove_button(self) -> None:
        if hasattr(self, "remove_button"):
            self.remove_button.setEnabled(bool(self._selected) and self._catalog is not None)

    def _bind_removal_keys(self) -> None:
        self._removal_key(Qt.Key.Key_Delete)
        self._removal_key(Qt.Key.Key_Backspace)

    def _removal_key(self, key: Qt.Key) -> None:
        shortcut = QShortcut(QKeySequence(key), self.grid)
        shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        shortcut.activated.connect(self._ask_removal)

    def _ask_removal(self) -> None:
        if self._catalog is None or not self._selected:
            return
        dialog = RemovalChoiceDialog(self, len(self._selected))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._remove_selected(dialog.deletes_original())

    def _remove_selected(self, delete_original: bool) -> None:
        if self._catalog is None:
            return
        remove_indexes(self._catalog, _photo_ids(self._selected), delete_original)
        self._load_all_photographs()
        self.catalog_changed.emit()

    def _request_import(self) -> None:
        self.import_requested.emit()

    def _export_selected(self) -> None:
        if not self._selected:
            self.status_label.setText("Select photos to export.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Export")
        if folder:
            self._copy_export(Path(folder))

    def _copy_export(self, folder: Path) -> None:
        copied = sum(self._copy_one(path, folder) for path in self._selected)
        self.status_label.setText(f"Exported {copied} photos.")

    def _copy_one(self, path: Path, folder: Path) -> int:
        try:
            shutil.copy2(path, folder / path.name)
        except OSError:
            return 0
        return 1

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "grid"):
            self._apply_grid()
            self._paint_previews()


def make_folder_item(path: Path) -> QTreeWidgetItem | None:
    try:
        return _folder_item(path)
    except OSError:
        return None


def _folder_item(path: Path) -> QTreeWidgetItem | None:
    if not path.is_dir():
        return None
    item = QTreeWidgetItem([path.name or str(path)])
    item.setData(0, Qt.ItemDataRole.UserRole, str(path))
    _add_placeholder(item, path)
    return item


def _add_placeholder(item: QTreeWidgetItem, path: Path) -> None:
    try:
        if _has_subfolders(path):
            QTreeWidgetItem(item, ["Loading..."])
    except OSError:
        return


def _has_subfolders(path: Path) -> bool:
    return any(child.is_dir() and not child.name.startswith(".") for child in path.iterdir())


def _photo_ids(paths: list[Path]) -> list[int]:
    found = [photo_id_of_index(path) for path in paths]
    return [photo_id for photo_id in found if photo_id is not None]


def _remove_placeholder(item: QTreeWidgetItem) -> bool:
    if item.childCount() == 0:
        return False
    child = item.child(0)
    if child and child.text(0) == "Loading...":
        item.removeChild(child)
        return True
    return False


def _append_children(item: QTreeWidgetItem, path: Path) -> None:
    try:
        folders = _subfolders(path)
    except OSError:
        return
    for folder in folders:
        child = make_folder_item(folder)
        if child is not None:
            item.addChild(child)


def _folder_name(path: Path) -> str:
    return path.name.lower()


def _subfolders(path: Path) -> list[Path]:
    folders = [entry for entry in path.iterdir() if entry.is_dir() and not entry.name.startswith(".")]
    return sorted(folders, key=_folder_name)


def _scroll(widget: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    area.setWidget(widget)
    return area


def _show_pixmap(label: QLabel, image: QImage, size) -> None:
    if image.isNull() or size.width() < 2 or size.height() < 2:
        label.setText("No photo selected")
        return
    pixmap = QPixmap.fromImage(image)
    label.setPixmap(pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


def _modified_text(path: Path) -> str:
    try:
        stamp = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return ""
    return stamp.strftime("%Y-%m-%d %H:%M")


def _library_style() -> str:
    return StyleSheet.LIGHTROOM
