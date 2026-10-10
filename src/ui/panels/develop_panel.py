from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThreadPool
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QSplitter, QVBoxLayout, QWidget, QCheckBox,
)

from src.ui.develop_info import read_exposure_text
from src.ui.develop_sections import (
    DevelopControls, basic_panel, calibration_panel, collections_tree, color_grading_panel,
    color_mixer_panel, detail_panel, effects_panel, history_list, lens_panel, presets_panel,
    tone_curve_panel, transform_panel,
)
from src.catalog.index_images import list_index_images
from src.ui.dialogs.import_dialog import ImageDiscoveryThread, ImageProcessorRunnable
from src.ui.panels.base_panel import BasePanel
from src.ui.themes import StyleSheet
from src.ui.preview_image import tone_image
from src.ui.widgets.collapsible_section import CollapsibleSection, PanelColumn
from src.ui.widgets.filmstrip_widget import FilmstripWidget
from src.ui.widgets.histogram_widget import HistogramWidget


class ThumbRelay(QObject):
    def __init__(self, panel: "DevelopPanel", session: int) -> None:
        super().__init__()
        self._panel = panel
        self._session = session

    def receive(self, path: str, _name: str, image: QImage) -> None:
        self._panel._on_thumb(path, image, self._session)


class DevelopPanel(BasePanel):
    def __init__(self) -> None:
        self._catalog: Path | None = None
        self._controls = DevelopControls()
        self._baseline: list[int] = []
        self._photos: list[Path] = []
        self._current: Path | None = None
        self._source_image = QImage()
        self._session = 0
        self._relays: list[ThumbRelay] = []
        self._discovery: ImageDiscoveryThread | None = None
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(4)
        super().__init__("develop")

    def _setup_ui(self) -> None:
        self.setStyleSheet(_develop_style())
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._workspace(), 1)
        root.addWidget(self._build_filmstrip())
        self._load_photos()

    def _workspace(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._left_column())
        splitter.addWidget(self._center_column())
        splitter.addWidget(self._right_column())
        splitter.setSizes([250, 860, 300])
        return splitter

    def _left_column(self) -> PanelColumn:
        column = PanelColumn()
        self.navigator = _empty_preview("No photo")
        self.navigator.setMinimumHeight(140)
        column.add_section(CollapsibleSection("Navigator", self.navigator))
        column.add_section(CollapsibleSection("Presets", presets_panel(self._controls), fill=True), 1)
        column.add_section(CollapsibleSection("Snapshots", _note("No snapshots"), expanded=False))
        column.add_section(CollapsibleSection("History", history_list()))
        column.add_section(CollapsibleSection("Collections", collections_tree(), expanded=False))
        return column

    def _center_column(self) -> QWidget:
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(12, 8, 12, 4)
        layout.setSpacing(4)
        self.filename_label = _info_label(16)
        self.exposure_label = _info_label(11)
        self.preview = _empty_preview("Select a photo.")
        layout.addWidget(self.filename_label)
        layout.addWidget(self.exposure_label)
        layout.addWidget(self.preview, 1)
        layout.addWidget(self._center_toolbar())
        return column

    def _right_column(self) -> QWidget:
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(_scroll(self._tool_stack()), 1)
        layout.addWidget(self._previous_reset())
        return column

    def _tool_stack(self) -> QWidget:
        stack = QWidget()
        layout = QVBoxLayout(stack)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.histogram = HistogramWidget()
        layout.addWidget(CollapsibleSection("Histogram", self.histogram))
        layout.addWidget(_tool_row())
        self._add_tool_sections(layout)
        layout.addStretch()
        return stack

    def _add_tool_sections(self, layout: QVBoxLayout) -> None:
        sections = (
            ("Basic", basic_panel(self._controls), True),
            ("Tone Curve", tone_curve_panel(self._controls), False),
            ("Color Mixer", color_mixer_panel(self._controls), False),
            ("Color Grading", color_grading_panel(self._controls), False),
            ("Detail", detail_panel(self._controls), False),
            ("Lens Corrections", lens_panel(self._controls), False),
            ("Transform", transform_panel(self._controls), False),
            ("Effects", effects_panel(self._controls), False),
            ("Calibration", calibration_panel(self._controls), False),
        )
        for title, content, expanded in sections:
            layout.addWidget(CollapsibleSection(title, content, expanded=expanded))
        self._bind_preview_sliders()

    def _center_toolbar(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QPushButton("Copy..."))
        row.addWidget(QPushButton("Paste"))
        row.addStretch()
        proofing = QCheckBox("Soft Proofing")
        row.addWidget(proofing)
        return bar

    def _previous_reset(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        previous = QPushButton("Previous")
        reset = QPushButton("Reset")
        previous.clicked.connect(self._restore_previous)
        reset.clicked.connect(self._reset_controls)
        row.addWidget(previous)
        row.addWidget(reset)
        return bar

    def _build_filmstrip(self) -> FilmstripWidget:
        self.filmstrip = FilmstripWidget()
        self.filmstrip.photo_selected.connect(self._on_filmstrip)
        return self.filmstrip

    def _bind_preview_sliders(self) -> None:
        for row in self._controls.sliders:
            if row.title in ("Exposure", "Contrast"):
                row.changed.connect(self._paint_preview)

    def show_catalog(self, catalog: Path | None) -> None:
        self._catalog = catalog
        self._load_photos()

    def _load_photos(self) -> None:
        self._cancel_load()
        self._show_paths(self._catalog_indexes())

    def _catalog_indexes(self) -> list[Path]:
        if self._catalog is None:
            return []
        return list_index_images(self._catalog)

    def _load_folder(self, folder: str) -> None:
        self._cancel_load()
        self._discovery = ImageDiscoveryThread(folder, recursive=False)
        self._discovery.discovery_finished.connect(self._on_discovered)
        self._discovery.start()

    def _on_discovered(self, paths: list[str]) -> None:
        self._show_paths([Path(path) for path in paths])

    def _show_paths(self, paths: list[Path]) -> None:
        self._photos = list(paths)
        self.filmstrip.set_photos(self._photos)
        self._start_thumbs()
        photo = _first_visible(self._photos)
        if photo is not None:
            self.filmstrip.select_photo(photo)

    def _start_thumbs(self) -> None:
        self._session += 1
        session = self._session
        self._relays.clear()
        for index, path in enumerate(self._photos):
            self._queue_thumb(path, index, session)

    def _queue_thumb(self, path: Path, index: int, session: int) -> None:
        relay = ThumbRelay(self, session)
        runnable = ImageProcessorRunnable([str(path)], index, 360)
        runnable.signals.image_found.connect(relay.receive)
        self._relays.append(relay)
        self._pool.start(runnable)

    def _on_thumb(self, path: str, image: QImage, session: int) -> None:
        if session != self._session or image.isNull():
            return
        photo = Path(path)
        self.filmstrip.set_thumbnail(photo, QPixmap.fromImage(image))
        if self._current == photo:
            self._set_source(image)

    def _on_filmstrip(self, path: str) -> None:
        self._show_photo(Path(path))

    def _show_photo(self, path: Path) -> None:
        self._current = path
        self.filename_label.setText(path.name)
        self.exposure_label.setText(read_exposure_text(path))
        image = QImage(str(path))
        self._set_source(image)
        self._baseline = self._controls.values()

    def _set_source(self, image: QImage) -> None:
        self._source_image = image
        self.preview.setVisible(True)
        self._paint_preview()

    def _paint_preview(self) -> None:
        image = tone_image(self._source_image, self._slider_value("Exposure"), self._slider_value("Contrast"))
        self.histogram.set_image(image)
        _show_pixmap(self.navigator, image, self.navigator.size())
        _show_pixmap(self.preview, image, self.preview.size())

    def _slider_value(self, title: str) -> int:
        for row in self._controls.sliders:
            if row.title == title:
                return row.value()
        return 0

    def _reset_controls(self) -> None:
        self._controls.reset()
        self._paint_preview()

    def _restore_previous(self) -> None:
        self._controls.restore(self._baseline)
        self._paint_preview()

    def _cancel_load(self) -> None:
        self._session += 1
        self._relays.clear()
        if self._discovery and self._discovery.isRunning():
            self._discovery.cancel()
            self._discovery.wait(300)
        self._pool.clear()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "preview"):
            self._paint_preview()


def _empty_preview(text: str) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("background-color: rgb(28, 28, 28); color: rgb(170, 170, 170);")
    return label


def _info_label(size: int) -> QLabel:
    label = QLabel("")
    label.setStyleSheet(f"color: rgb(230, 230, 230); font-size: {size}px; background: transparent;")
    return label


def _first_visible(paths: list[Path]) -> Path | None:
    raw_suffixes = {".arw", ".cr2", ".cr3", ".nef", ".raf", ".orf", ".rw2", ".dng"}
    for path in paths:
        if path.suffix.lower() not in raw_suffixes:
            return path
    if paths:
        return paths[0]
    return None


def _tool_row() -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(6, 4, 6, 4)
    for title in ("Crop", "Spot", "Red Eye", "Mask"):
        layout.addWidget(QPushButton(title))
    return row


def _scroll(widget: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    area.setWidget(widget)
    return area


def _show_pixmap(label: QLabel, image: QImage, size) -> None:
    if image.isNull() or size.width() < 2 or size.height() < 2:
        label.setText("The file is offline or missing.")
        return
    pixmap = QPixmap.fromImage(image)
    label.setPixmap(pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


def _note(text: str) -> QLabel:
    label = QLabel(text)
    label.setContentsMargins(8, 6, 8, 6)
    return label


def _develop_style() -> str:
    return StyleSheet.LIGHTROOM
