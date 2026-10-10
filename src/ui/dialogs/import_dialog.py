"""
Import Dialog for Photo Editor
Provides a standalone dialog for importing photos with full functionality.
"""

import logging
import os
import platform
import re
import shutil
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime
from fractions import Fraction
from hashlib import sha1
from pathlib import Path
from typing import List, Optional, Set

from PyQt6.QtCore import Qt, QDir, QFileSystemWatcher, QSize, QTimer, QThread, pyqtSignal, QThreadPool, QObject, QRunnable
from PyQt6.QtGui import QPixmap, QIcon, QImage, QImageReader, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QWidget, QFrame, QSplitter, QLineEdit, QFormLayout,
    QGroupBox, QCheckBox, QGridLayout, QTextEdit, QSizePolicy,
    QPushButton, QProgressBar, QAbstractItemView, QSlider, QComboBox,
    QFileDialog, QMessageBox, QInputDialog, QDialog, QDialogButtonBox,
    QApplication, QListView, QSpinBox, QStackedWidget
)

from src.config.config_manager import ConfigManager
from src.ui.import_summary import byte_total, import_status_text
from src.importing.discover import discover_images
from src.importing.originals import import_originals
from src.importing.transfer import copy_original, move_original
from src.ui.themes import StyleSheet
from src.ui.widgets.collapsible_section import CollapsibleSection
from src.ui.widgets.grid_image_widget import GridImageWidget
from src.ui.dialogs import RenamePatternDialog, DestinationSettingsDialog
from src.ui.dialogs.iptc_preset_dialog import IPTCPresetDialog
from src.models.iptc_data import (
    IPTCData, IPTCPreset, get_default_iptc_preset, 
    apply_iptc_to_image, read_iptc_from_image, merge_iptc_data
)

logger = logging.getLogger(__name__)

# Ensure file-based logging for this module
_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, "import_dialog.log")

_file_handler_exists = False
for _h in logger.handlers:
    if isinstance(_h, logging.FileHandler) and getattr(_h, "baseFilename", None) == _log_path:
        _file_handler_exists = True
        break

if not _file_handler_exists:
    _fh = logging.FileHandler(_log_path, encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(_fh)

logger.setLevel(logging.DEBUG)


class ImageProcessorSignals(QObject):
    """Signals for image processing"""
    image_found = pyqtSignal(str, str, QImage)
    batch_finished = pyqtSignal(int)
    # Simple cooperative cancellation flag, read/write from worker
    cancelled: bool = False


class ImageProcessorRunnable(QRunnable):
    """Runnable for processing a batch of images"""

    RAW_IMAGE_SUFFIXES = (".cr2", ".cr3", ".nef", ".arw", ".raf", ".orf", ".rw2", ".dng")

    def __init__(self, image_paths: List[str], batch_id: int, target_size: int):
        super().__init__()
        self.image_paths = image_paths
        self.batch_id = batch_id
        self.target_size = max(32, int(target_size))
        self.signals = ImageProcessorSignals()

    def _load_raw_thumbnail(self, image_path: str) -> QImage:
        """Load RAW image thumbnail using rawpy with proper scaling"""
        try:
            import rawpy

            with rawpy.imread(image_path) as raw_file:
                rgb_data = raw_file.postprocess(use_camera_wb=True, half_size=True, no_auto_bright=True, output_bps=8)

            # Create QImage from numpy array data
            height, width = rgb_data.shape[0], rgb_data.shape[1]
            image = QImage(rgb_data.data, width, height, rgb_data.strides[0], QImage.Format.Format_RGB888)
            image = image.copy()  # Detach from numpy buffer

            # Scale to target size (like Qt thumbnails)
            if image.isNull():
                return QImage()

            original_size = image.size()
            if original_size.isValid() and original_size.width() > 0 and original_size.height() > 0:
                max_side = max(original_size.width(), original_size.height())
                if max_side > self.target_size:
                    scale = self.target_size / max_side
                    scaled_size = QSize(max(1, int(original_size.width() * scale)), max(1, int(original_size.height() * scale)))
                    image = image.scaled(scaled_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            return image
        except Exception as error:
            logger.error("Error loading RAW thumbnail %s: %s", image_path, error)
            return QImage()

    def _load_qt_thumbnail(self, image_path: str) -> QImage:
        reader = QImageReader(str(image_path))
        reader.setAutoTransform(True)
        original_size = reader.size()
        if original_size.isValid() and original_size.width() > 0 and original_size.height() > 0:
            max_side = max(original_size.width(), original_size.height())
            scale = self.target_size / max_side
            scaled_size = QSize(max(1, int(original_size.width() * scale)), max(1, int(original_size.height() * scale)))
            reader.setScaledSize(scaled_size)
        else:
            reader.setScaledSize(QSize(self.target_size, self.target_size))
        return reader.read()

    def _load_thumbnail(self, image_path: str) -> QImage:
        suffix = Path(image_path).suffix.lower()
        if suffix in self.RAW_IMAGE_SUFFIXES:
            return self._load_raw_thumbnail(image_path)
        return self._load_qt_thumbnail(image_path)

    def run(self):
        """Process a batch of images: load files into QImage in worker thread"""
        try:
            for index, image_path in enumerate(self.image_paths):
                if self.signals.cancelled:
                    break

                try:
                    image = self._load_thumbnail(image_path)
                except Exception as error:
                    image = QImage()

                self.signals.image_found.emit(image_path, Path(image_path).name, image)

                if self.signals.cancelled:
                    break

                if index % 3 == 0:
                    import time
                    time.sleep(0.0001)
                    if self.signals.cancelled:
                        break

            self.signals.batch_finished.emit(self.batch_id)
        except Exception as error:
            logger.error("Error in batch %s: %s", self.batch_id, error)
            self.signals.batch_finished.emit(self.batch_id)


class ImageDiscoveryThread(QThread):
    """Thread for discovering image files"""

    STANDARD_IMAGE_SUFFIXES = (
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp",
    )
    RAW_IMAGE_SUFFIXES = (
        ".cr2", ".cr3", ".nef", ".arw", ".raf", ".orf", ".rw2", ".dng",
    )
    SUPPORTED_IMAGE_SUFFIXES = STANDARD_IMAGE_SUFFIXES + RAW_IMAGE_SUFFIXES

    discovery_finished = pyqtSignal(list)
    progress_updated = pyqtSignal(int, int)

    def __init__(self, folder_path: str, recursive: bool = False):
        super().__init__()
        self.folder_path = folder_path
        self.recursive = recursive
        self._is_cancelled = False
        self.image_files = []

    def run(self) -> None:
        try:
            found = discover_images(Path(self.folder_path), self.recursive)
            self.image_files = [str(path) for path in found]
            if not self._is_cancelled:
                self.discovery_finished.emit(self.image_files)
        except Exception as error:
            logger.error("Error in image discovery thread: %s", error)

    def cancel(self):
        self._is_cancelled = True

    def _find_images_recursive(self, folder_path: Path, max_depth: int = 3, current_depth: int = 0) -> List[Path]:
        if current_depth >= max_depth:
            return []
        image_files = []
        try:
            for item in sorted(folder_path.iterdir()):
                if self._is_cancelled:
                    break
                if item.is_file() and self._is_image_file(item):
                    image_files.append(item)
                elif item.is_dir() and not item.name.startswith('.'):
                    image_files.extend(self._find_images_recursive(item, max_depth, current_depth + 1))
        except (PermissionError, OSError):
            pass
        return image_files

    def _find_images_non_recursive(self, folder_path: Path) -> List[Path]:
        image_files = []
        try:
            for item in sorted(folder_path.iterdir()):
                if self._is_cancelled:
                    break
                if item.is_file() and self._is_image_file(item):
                    image_files.append(item)
        except (PermissionError, OSError):
            pass
        return image_files

    def _is_image_file(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_IMAGE_SUFFIXES


class ImportDialog(QDialog):
    """Standalone dialog for importing photos with full Library functionality"""

    DEFAULT_IMPORT_PRESET_NAME = "Default"
    ORGANIZE_OPTIONS = (
        ("by_date", "by date"),
        ("one_folder", "into one folder"),
    )
    DATE_FORMAT_OPTIONS = (
        ("%Y/%m/%d", "2026/03/08"),
        ("%Y-%m-%d", "2026-03-08"),
        ("%Y/%B/%d", "2026/March/08"),
        ("%Y %B %d", "2026 March 08"),
        ("%Y %b %d", "2026 Mar 08"),
        ("%d-%m-%Y", "08-03-2026"),
    )
    RENAME_TEMPLATE_OPTIONS = (
        "{filename}",
        "CustomName_{sequence}",
        "{capture_time}",
    )
    DEFAULT_RENAME_TEMPLATE_NAMES = {
        "{filename}": "Original filename",
        "CustomName_{sequence}": "Custom filename + index",
        "{capture_time}": "Capture time + index",
    }
    RENAME_TOKEN_DESCRIPTIONS = (
        ("{filename}", "Original file name without extension"),
        ("{sequence}", "Running index during import using the default 3 digits"),
        ("{sequence:5}", "Running index during import padded to 5 digits"),
        ("{capture_time}", "Capture date and time in yymmdd_HHMMSS format"),
        ("{date}", "Date folder format based on the selected date format"),
    )
    IMPORT_PRESET_CONFIG_KEY = "panels.import.import_settings"
    IMPORT_PRESET_LIST_KEY = "presets"
    IMPORT_PRESET_ACTIVE_KEY = "active_preset"
    IMPORT_SETTINGS_KEY = "current"
    RENAME_TEMPLATE_LIST_KEY = "rename_templates"
    DESTINATION_PRESET_LIST_KEY = "destination_presets"
    DESTINATION_PRESET_ACTIVE_KEY = "active_destination_preset"
    DEFAULT_DESTINATION_PRESET_NAME = "Default"
    SAMPLE_FILENAME = "IMG_0001"
    SAMPLE_SEQUENCE = "001"
    DEFAULT_SEQUENCE_DIGITS = 3
    SAMPLE_CAPTURE_TIME = datetime(2026, 3, 8, 12, 34, 56)
    CAPTURE_TIME_FORMAT = "%y%m%d_%H%M%S"

    # IPTC constants
    IPTC_PRESET_LIST_KEY = "iptc_presets"
    IPTC_PRESET_ACTIVE_KEY = "active_iptc_preset"
    DEFAULT_IPTC_PRESET_NAME = "Default"

    # Filter constants
    PICK_OPTIONS = (("Any", "any"), ("Accepted (✓)", "accepted"), ("Rejected (✕)", "rejected"), ("None", "none"))
    RATING_OPTIONS = (
        ("Any", "any"),
        ("★ 5 only", "exact_5"),
        ("★ 4+", "4"),
        ("★ 4 only", "exact_4"),
        ("★ 3+", "3"),
        ("★ 3 only", "exact_3"),
        ("★ 2+", "2"),
        ("★ 2 only", "exact_2"),
        ("★ 1+", "1"),
        ("★ 1 only", "exact_1"),
        ("No stars", "0"),
    )
    COLOR_OPTIONS = (("Any", "any"), ("None", "none"), ("Red", "red"), ("Orange", "orange"), ("Yellow", "yellow"), ("Green", "green"), ("Blue", "blue"), ("Purple", "purple"))
    SORT_OPTIONS = (("None", "none"), ("Rating ↑", "rating_asc"), ("Rating ↓", "rating_desc"))

    # Grid constants
    DEFAULT_GRID_COLUMNS = 5
    MIN_GRID_COLUMNS = 1
    MAX_GRID_COLUMNS = 10
    FILTER_DAYS_MIN = 0
    FILTER_DAYS_MAX = 36500
    FILTER_DAYS_DEFAULT = 36500

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Photos")
        self.setMinimumSize(1600, 800)  # Increased minimum to ensure panels fit
        self.resize(1800, 900)  # Larger default size

        self.config_manager = ConfigManager()
        self.current_folder: Optional[Path] = None
        self.image_files: List[Path] = []
        self.discovered_image_files: List[Path] = []
        self.selected_images: List[Path] = []
        self.grid_columns = self.DEFAULT_GRID_COLUMNS
        self.thumbnail_cache: dict[Path, QPixmap] = {}
        self.recursive_loading = True  # Default to True to match checkbox state

        # Filter state
        self.media_filter_state: dict[str, object] = {
            "pick": "any",
            "rating": "any",
            "color": "any",
            "days": self.FILTER_DAYS_DEFAULT,
            "sort_by": "none",
        }

        # Import UI widgets
        self.import_panel_widgets: dict[str, QWidget] = {}
        self.preset_combo: Optional[QComboBox] = None
        self.preset_feedback_label: Optional[QLabel] = None
        self.rename_preset_label: Optional[QLabel] = None
        self.destination_preset_label: Optional[QLabel] = None
        self.iptc_preset_label: Optional[QLabel] = None
        # IPTC field widgets
        self.iptc_creator_input: Optional[QLineEdit] = None
        self.iptc_copyright_input: Optional[QLineEdit] = None
        self.iptc_credit_input: Optional[QLineEdit] = None
        self.iptc_source_input: Optional[QLineEdit] = None
        self.iptc_keywords_input: Optional[QTextEdit] = None
        # Track existing values from images (with asterisks)
        self._iptc_existing_data: dict[str, str] = {}  # field -> value with asterisk
        self._iptc_original_keywords: set[str] = set()  # original keywords from images
        self._iptc_removed_keywords: set[str] = set()  # keywords marked for removal
        self._iptc_removed_fields: set[str] = set()  # single fields marked for removal
        self._updating_import_ui = False
        self.import_status_label: Optional[QLabel] = None
        self.import_button: Optional[QPushButton] = None
        self.import_cancel_button: Optional[QPushButton] = None
        self.is_importing = False
        self.import_cancel_requested = False
        self._import_mode = "import"
        self._mode_buttons: dict[str, QPushButton] = {}
        self._bound_catalog: Path | None = None

        # Threading
        self.discovery_thread: Optional[ImageDiscoveryThread] = None
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(4)
        self.is_loading = False
        self._loading_session_id = 0  # Incremented on each new load to ignore stale signals
        self.total_images = 0
        self.processed_images = 0

        # Volume monitoring
        self.volume_root_path = Path("/Volumes")
        self.volume_watcher: Optional[QFileSystemWatcher] = None
        self.volume_refresh_timer: Optional[QTimer] = None

        # Grid resize handling
        self.resize_timer: Optional[QTimer] = None
        self.main_splitter: Optional[QSplitter] = None
        self._splitter_sizes: List[int] = []  # Store user-set splitter sizes

        self._setup_ui()
        self._setup_volume_monitoring()
        self._load_import_settings_into_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("DarkLab Catalog - Import")
        self.setStyleSheet(StyleSheet.IMPORT_DIALOG)
        self._prepare_resize_timer()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_import_top_bar())
        layout.addWidget(self._build_import_splitter(), 1)
        layout.addWidget(self._build_import_bottom_bar())
        self._set_import_mode("import")
        self._setup_selection_shortcuts()
        self._sync_center_view()
        self._refresh_import_summary()

    def _setup_selection_shortcuts(self) -> None:
        select_all = QShortcut(QKeySequence.StandardKey.SelectAll, self)
        select_all.activated.connect(self._select_all_images)
        deselect_all = QShortcut(QKeySequence("Ctrl+D"), self)
        deselect_all.activated.connect(self._clear_selected_images)
        if platform.system() == "Darwin":
            deselect_mac = QShortcut(QKeySequence("Meta+D"), self)
            deselect_mac.activated.connect(self._clear_selected_images)

    def _prepare_resize_timer(self) -> None:
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._apply_grid_layout)

    def _build_import_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter = splitter
        self._setup_folder_tree(splitter)
        self._setup_image_grid(splitter)
        self._setup_import_settings(splitter)
        splitter.setHandleWidth(4)
        splitter.setSizes([240, 980, 300])
        return splitter

    def _build_import_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        row = QHBoxLayout(bar)
        row.setContentsMargins(10, 4, 12, 4)
        self.source_button = QPushButton("Select a source")
        self.source_button.clicked.connect(self._focus_source_tree)
        row.addWidget(self.source_button)
        row.addWidget(self._plain_button("→", self._advance_source))
        row.addStretch()
        row.addWidget(self._mode_button("import", "Copy"))
        row.addWidget(self._mode_button("move", "Move"))
        row.addWidget(self._mode_button("culling", "Assisted Culling"))
        row.addWidget(self._add_mode_box())
        row.addStretch()
        row.addWidget(QLabel("DarkLab Catalog"))
        return bar

    def _add_mode_box(self) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._mode_button("add", "Add"))
        self.add_hint = QLabel("Add photos to catalog without moving them")
        self.add_hint.setStyleSheet("color: rgb(150, 150, 150); font-size: 10px;")
        layout.addWidget(self.add_hint)
        return box

    def _mode_button(self, mode: str, title: str) -> QPushButton:
        button = QPushButton(title)
        button.setObjectName("importMode")
        button.setCheckable(True)
        button.setProperty("import_mode", mode)
        button.clicked.connect(self._on_mode_clicked)
        self._mode_buttons[mode] = button
        return button

    def _on_mode_clicked(self) -> None:
        button = self.sender()
        if isinstance(button, QPushButton):
            self._set_import_mode(str(button.property("import_mode")))

    def _set_import_mode(self, mode: str) -> None:
        self._import_mode = mode
        for key, button in self._mode_buttons.items():
            button.setChecked(key == mode)
        if hasattr(self, "culling_bar"):
            self.culling_bar.setVisible(mode == "culling")
        if self.import_button is not None:
            self.import_button.setText(self._commit_label())

    def _build_import_bottom_bar(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 6, 8, 6)
        self._add_import_status(row)
        self._add_import_tools(row)
        self._add_import_actions(row)
        return bar

    def _add_import_status(self, row: QHBoxLayout) -> None:
        self.import_status_label = QLabel("0 photos / 0 bytes")
        row.addWidget(self.import_status_label)
        row.addWidget(self._plain_button("Check All", self._select_all_images))
        row.addWidget(self._plain_button("Uncheck All", self._clear_selected_images))
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(140)
        self.cancel_button = self._loading_cancel_button()
        row.addWidget(self.progress_bar)
        row.addWidget(self.cancel_button)

    def _add_import_tools(self, row: QHBoxLayout) -> None:
        row.addStretch()
        row.addWidget(QLabel("Sort"))
        self.sort_combo = self._create_marker_combo(self.SORT_OPTIONS)
        self.sort_combo.currentIndexChanged.connect(self._on_media_filter_changed)
        self.columns_slider = self._thumbnail_slider()
        self.columns_value_label = QLabel(str(self.grid_columns))
        row.addWidget(self.sort_combo)
        row.addWidget(QLabel("Thumbnails"))
        row.addWidget(self.columns_slider)
        row.addWidget(self.columns_value_label)

    def _add_import_actions(self, row: QHBoxLayout) -> None:
        row.addWidget(self._create_import_preset_widget())
        self.import_button = self._import_action_button()
        row.addWidget(self._plain_button("Done", self.reject))
        row.addWidget(self._plain_button("Cancel", self.reject))
        row.addWidget(self.import_button)

    def _thumbnail_slider(self) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(self.MIN_GRID_COLUMNS, self.MAX_GRID_COLUMNS)
        slider.setValue(self.grid_columns)
        slider.setFixedWidth(120)
        slider.valueChanged.connect(self._on_columns_changed)
        return slider

    def _loading_cancel_button(self) -> QPushButton:
        button = QPushButton("Cancel")
        button.setVisible(False)
        button.clicked.connect(self._cancel_loading)
        return button

    def _import_action_button(self) -> QPushButton:
        button = QPushButton("Import")
        button.setObjectName("importAction")
        button.clicked.connect(self._start_import)
        return button

    def _plain_button(self, title: str, handler) -> QPushButton:
        button = QPushButton(title)
        button.clicked.connect(handler)
        return button

    def _focus_source_tree(self) -> None:
        self.folder_tree.setFocus()

    def _advance_source(self) -> None:
        item = self.folder_tree.currentItem()
        if item is None:
            return
        parent = item.parent() or self.folder_tree.invisibleRootItem()
        nxt = parent.child(parent.indexOfChild(item) + 1)
        if nxt is not None:
            self.folder_tree.setCurrentItem(nxt)
            self._on_folder_selected(nxt)

    def _sync_center_view(self) -> None:
        if hasattr(self, "center_stack"):
            self.center_stack.setCurrentIndex(1 if self.current_folder else 0)

    def _refresh_import_summary(self) -> None:
        if self.import_status_label is None:
            return
        selected = self.selected_images
        text = import_status_text(len(self.image_files), len(selected), byte_total(selected))
        self.import_status_label.setText(text)
        self._sync_import_button()

    def bind_catalog(self, catalog: Path | None) -> None:
        self._bound_catalog = catalog

    def _commit_label(self) -> str:
        if self._import_mode == "add":
            return "Add"
        if self._import_mode == "move":
            return "Move"
        return "Copy"

    def _sync_import_button(self) -> None:
        if self.import_button is None:
            return
        self.import_button.setEnabled(bool(self.selected_images) and not self.is_importing)

    def _add_selection_to_catalog(self) -> None:
        if not self.selected_images:
            return
        if self._bound_catalog is None:
            QMessageBox.warning(self, "Add", "Open a catalog before importing.")
            return
        self._add_each()

    def _add_each(self) -> None:
        total = len(self.selected_images)
        done = 0
        for path in list(self.selected_images):
            done += import_originals(self._bound_catalog, [path])
            self._show_add_progress(done, total)

    def _show_add_progress(self, done: int, total: int) -> None:
        if self.import_status_label is None:
            return
        self.import_status_label.setText(f"Added {done}/{total}")

    def _recorded_count(self) -> int | None:
        try:
            return self._record_originals(self.selected_images)
        except ValueError as error:
            QMessageBox.warning(self, "Add", str(error))
            return None

    def _record_originals(self, paths: list[Path]) -> int:
        if self._bound_catalog is None:
            raise ValueError("Open a catalog before importing.")
        return import_originals(self._bound_catalog, list(paths))

    def _record_original(self, path: Path) -> None:
        self._record_originals([path])

    def _place_original(self, source: Path, destination: Path) -> Path:
        if self._import_mode == "move":
            return move_original(source, destination)
        return copy_original(source, destination)

    def _setup_folder_tree(self, parent: QSplitter) -> None:
        left = QWidget()
        left.setMinimumWidth(220)
        layout = QVBoxLayout(left)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(CollapsibleSection("Source", self._source_body(), True, arrow_on_left=True, fill=True), 1)
        parent.addWidget(left)
        self._load_folder_structure()

    def _source_body(self) -> QWidget:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.itemClicked.connect(self._on_folder_selected)
        self.folder_tree.itemExpanded.connect(self._on_folder_expanded)
        self.recursive_checkbox = QCheckBox("Include Subfolders")
        self.recursive_checkbox.setChecked(True)
        self.recursive_checkbox.toggled.connect(self._on_recursive_toggled)
        layout.addWidget(self.folder_tree, 1)
        layout.addWidget(self.recursive_checkbox)
        return body

    def _setup_image_grid(self, parent: QSplitter) -> None:
        middle = QWidget()
        layout = QVBoxLayout(middle)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.culling_bar = self._culling_bar()
        self.culling_bar.setVisible(False)
        self.center_stack = QStackedWidget()
        self.source_prompt = QLabel("Please select a source.")
        self.source_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area = self._image_scroll()
        self.center_stack.addWidget(self.source_prompt)
        self.center_stack.addWidget(self.scroll_area)
        layout.addWidget(self.culling_bar)
        layout.addWidget(self.center_stack, 1)
        parent.addWidget(middle)

    def _culling_bar(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        self.pick_filter_combo = self._bound_combo(self.PICK_OPTIONS)
        self.rating_filter_combo = self._bound_combo(self.RATING_OPTIONS)
        self.color_filter_combo = self._bound_combo(self.COLOR_OPTIONS)
        self.days_back_spin = self._days_spin()
        row.addWidget(QLabel("Pick"))
        row.addWidget(self.pick_filter_combo)
        row.addWidget(QLabel("Stars"))
        row.addWidget(self.rating_filter_combo)
        row.addWidget(QLabel("Color"))
        row.addWidget(self.color_filter_combo)
        row.addWidget(QLabel("Days"))
        row.addWidget(self.days_back_spin)
        row.addStretch()
        return bar

    def _bound_combo(self, options: tuple[tuple[str, str], ...]) -> QComboBox:
        combo = self._create_marker_combo(options)
        combo.currentIndexChanged.connect(self._on_media_filter_changed)
        return combo

    def _days_spin(self) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(self.FILTER_DAYS_MIN, self.FILTER_DAYS_MAX)
        spin.setValue(self.FILTER_DAYS_DEFAULT)
        spin.setFixedWidth(80)
        spin.valueChanged.connect(self._on_media_filter_changed)
        return spin

    def _image_scroll(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.grid_widget = GridImageWidget()
        self.grid_widget.selection_changed.connect(self._on_grid_selection_changed)
        self.grid_widget.marker_changed.connect(self._on_marker_changed)
        scroll.setWidget(self.grid_widget)
        return scroll

    def _setup_import_settings(self, parent: QSplitter) -> None:
        right = QWidget()
        right.setMinimumWidth(260)
        layout = QVBoxLayout(right)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        settings = QWidget()
        settings_layout = QVBoxLayout(settings)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._render_import_sections(settings_layout)
        scroll.setWidget(settings)
        layout.addWidget(scroll)
        parent.addWidget(right)

    def _create_marker_combo(self, options: tuple[tuple[str, str], ...]) -> QComboBox:
        """Create a filter combo box"""
        combo_box = QComboBox()
        combo_box.setFixedWidth(120)
        for display_label, data_value in options:
            combo_box.addItem(display_label, data_value)
        return combo_box

    # ===== Folder Tree Methods =====

    def _setup_volume_monitoring(self) -> None:
        """Setup mounted volume monitoring."""
        if platform.system() != "Darwin":
            return
        if not self.volume_root_path.exists():
            return
        self.volume_watcher = QFileSystemWatcher(self)
        self.volume_watcher.addPath(str(self.volume_root_path))
        self.volume_watcher.directoryChanged.connect(self._schedule_volume_refresh)
        self.volume_refresh_timer = QTimer(self)
        self.volume_refresh_timer.setSingleShot(True)
        self.volume_refresh_timer.timeout.connect(self._refresh_folder_structure)

    def _schedule_volume_refresh(self) -> None:
        """Schedule a delayed refresh after volume changes."""
        if self.volume_refresh_timer is None:
            return
        self.volume_refresh_timer.start(400)

    def _refresh_folder_structure(self) -> None:
        """Refresh the top-level folder tree items."""
        selected_path = self._get_selected_folder_path()
        expanded_paths = self._get_expanded_top_level_paths()
        self.folder_tree.clear()
        self._load_folder_structure()
        self._restore_top_level_state(selected_path, expanded_paths)

    def _get_selected_folder_path(self) -> Optional[str]:
        """Get the currently selected folder path."""
        current_item = self.folder_tree.currentItem()
        if current_item is None:
            return None
        return current_item.data(0, Qt.ItemDataRole.UserRole)

    def _get_expanded_top_level_paths(self) -> Set[str]:
        """Collect expanded top-level paths."""
        expanded_paths: Set[str] = set()
        for index in range(self.folder_tree.topLevelItemCount()):
            item = self.folder_tree.topLevelItem(index)
            if item.isExpanded():
                expanded_paths.add(item.data(0, Qt.ItemDataRole.UserRole))
        return expanded_paths

    def _restore_top_level_state(self, selected_path: Optional[str], expanded_paths: Set[str]) -> None:
        """Restore selection and expanded state after refresh."""
        for index in range(self.folder_tree.topLevelItemCount()):
            item = self.folder_tree.topLevelItem(index)
            item_path = item.data(0, Qt.ItemDataRole.UserRole)
            if item_path in expanded_paths:
                item.setExpanded(True)
            if item_path == selected_path:
                self.folder_tree.setCurrentItem(item)

    def _load_folder_structure(self) -> None:
        """Load the folder tree structure"""
        self.folder_tree.clear()

        home = Path.home()
        root_directories = [home]

        # Add common directories
        common_dirs = [home / "Pictures", home / "Desktop", home / "Documents", home / "Downloads"]
        for dir_path in common_dirs:
            if dir_path.exists() and dir_path != home:
                root_directories.append(dir_path)

        # Add mounted volumes on macOS
        if platform.system() == "Darwin" and self.volume_root_path.exists():
            for volume_path in sorted(self.volume_root_path.iterdir()):
                if volume_path.is_dir() and volume_path != home:
                    root_directories.append(volume_path)

        # Add items to tree
        for dir_path in root_directories:
            if dir_path.exists():
                self._add_folder_to_tree(dir_path, self.folder_tree)

    def _add_folder_to_tree(self, folder_path: Path, parent) -> Optional[QTreeWidgetItem]:
        """Add a folder to the tree widget"""
        try:
            if not folder_path.exists():
                return None

            item = QTreeWidgetItem(parent)
            item.setText(0, folder_path.name if folder_path.name else str(folder_path))
            item.setData(0, Qt.ItemDataRole.UserRole, str(folder_path))
            item.setToolTip(0, str(folder_path))

            # Add dummy child to show expand arrow
            try:
                has_subdirs = any(d.is_dir() and not d.name.startswith('.') for d in folder_path.iterdir())
                if has_subdirs:
                    dummy = QTreeWidgetItem(item)
                    dummy.setText(0, "Loading...")
            except (PermissionError, OSError):
                pass

            return item
        except Exception as e:
            logger.error("Error adding folder to tree: %s", e)
            return None

    def _on_folder_expanded(self, item: QTreeWidgetItem) -> None:
        """Handle folder expansion"""
        # Remove dummy children and load real ones
        while item.childCount() > 0:
            child = item.child(0)
            if child.text(0) == "Loading...":
                item.removeChild(child)
                break
            else:
                return  # Already loaded

        folder_path = item.data(0, Qt.ItemDataRole.UserRole)
        if folder_path:
            try:
                path = Path(folder_path)
                subdirs = sorted([d for d in path.iterdir() if d.is_dir() and not d.name.startswith('.')])
                for subdir in subdirs:
                    self._add_folder_to_tree(subdir, item)
            except (PermissionError, OSError):
                pass

    def _on_folder_selected(self, item: QTreeWidgetItem) -> None:
        """Handle folder selection"""
        folder_path = item.data(0, Qt.ItemDataRole.UserRole)
        if folder_path:
            self._load_source_folder(Path(folder_path))

    def _on_recursive_toggled(self, checked: bool) -> None:
        """Handle recursive loading toggle"""
        self.recursive_loading = checked
        if self.current_folder:
            self._load_source_folder(self.current_folder)

    def _load_source_folder(self, folder_path: Path) -> None:
        """Load images from source folder"""
        self.current_folder = folder_path
        if hasattr(self, "source_button"):
            self.source_button.setText(folder_path.name)
        self._sync_center_view()
        self.import_status_label.setText(f"Loading from: {folder_path.name}...")

        # Cancel any existing discovery
        if self.discovery_thread and self.discovery_thread.isRunning():
            self.discovery_thread.cancel()
            self.discovery_thread.wait(1000)

        # Cancel any active thumbnail loading
        self._cancel_loading()

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.cancel_button.setVisible(True)

        # Start new discovery
        self.discovery_thread = ImageDiscoveryThread(str(folder_path), recursive=self.recursive_loading)
        self.discovery_thread.discovery_finished.connect(self._on_discovery_finished)
        self.discovery_thread.start()

    def _on_discovery_finished(self, image_paths: List[str]) -> None:
        """Handle discovery completion"""
        self.discovered_image_files = [Path(p) for p in image_paths]
        self.image_files = self.discovered_image_files.copy()
        self.total_images = len(self.discovered_image_files)
        self.processed_images = 0

        if not self.discovered_image_files:
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.is_loading = False
            self._sync_center_view()
            self._refresh_import_summary()
            return

        # Show images in grid immediately (thumbnails will load async)
        self._apply_media_filters_to_grid()

        # Start thumbnail generation
        self._start_thumbnail_loading()

    def _start_thumbnail_loading(self) -> None:
        """Start generating thumbnails for discovered images"""
        self.is_loading = True
        self._loading_session_id += 1
        current_session_id = self._loading_session_id

        self.progress_bar.setRange(0, self.total_images)
        self.progress_bar.setValue(0)

        # Calculate target icon size based on current grid columns
        scroll_width = self.scroll_area.viewport().width() - 40
        target_size = max(120, (scroll_width - (self.grid_columns - 1) * 8) // self.grid_columns)

        # Start loading thumbnails for each image
        for batch_id, image_path in enumerate(self.discovered_image_files):
            runnable = ImageProcessorRunnable([str(image_path)], batch_id, target_size)
            runnable.signals.image_found.connect(
                lambda path, name, img, sid=current_session_id: self._on_image_found(path, name, img, sid)
            )
            self.thread_pool.start(runnable)

    def _on_image_found(self, image_path: str, image_name: str, image: QImage, session_id: int = 0) -> None:
        """Handle when an image thumbnail is loaded"""
        # Ignore signals from old/cancelled loading sessions
        if session_id != self._loading_session_id:
            return
        if not self.is_loading:
            return

        path = Path(image_path)
        pixmap = QPixmap.fromImage(image)
        if not pixmap.isNull():
            self.thumbnail_cache[path] = pixmap
            self.grid_widget.set_thumbnail(path, pixmap)

        self.processed_images += 1
        if self.total_images > 0:
            self.progress_bar.setValue(self.processed_images)
            self.progress_bar.setFormat(f"Loading images... ({self.processed_images}/{self.total_images})")

        if self.processed_images >= self.total_images:
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.is_loading = False
            # Just update status, don't re-apply filters to avoid panel jumping
            self._refresh_import_summary()

    def _cancel_loading(self) -> None:
        """Cancel loading operations"""
        self.is_loading = False
        self._loading_session_id += 1  # Increment session ID to ignore old signals

        if self.discovery_thread and self.discovery_thread.isRunning():
            self.discovery_thread.cancel()
            self.discovery_thread.wait(1000)

        # Cancel thread pool tasks
        self.thread_pool.clear()
        self.thread_pool.waitForDone(2000)

        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)

    # ===== Filter Methods =====

    def _on_media_filter_changed(self) -> None:
        """Handle media filter changes"""
        self.media_filter_state["pick"] = str(self.pick_filter_combo.currentData())
        self.media_filter_state["rating"] = str(self.rating_filter_combo.currentData())
        self.media_filter_state["color"] = str(self.color_filter_combo.currentData())
        self.media_filter_state["days"] = int(self.days_back_spin.value())
        self.media_filter_state["sort_by"] = str(self.sort_combo.currentData())
        self._apply_media_filters_to_grid()

    def _apply_media_filters_to_grid(self) -> None:
        """Apply filters to the grid"""
        filtered_images = self._filter_images(self.discovered_image_files)

        # Save current selection
        saved_selection = list(self.grid_widget.selected_images) if self.grid_widget else []

        # Update grid
        self.grid_widget.set_images(filtered_images)

        # Restore thumbnails from cache for visible images
        for image_path in filtered_images:
            if image_path in self.thumbnail_cache:
                self.grid_widget.set_thumbnail(image_path, self.thumbnail_cache[image_path])

        # Apply grid layout immediately
        self._apply_grid_layout()

        # Restore selection for images that are still visible
        if saved_selection:
            restored_selection = [path for path in saved_selection if path in filtered_images]
            if restored_selection:
                self.grid_widget.set_selected_images(restored_selection)

        # Restore splitter sizes to prevent automatic resizing
        self._restore_splitter_sizes()

        self.image_files = filtered_images
        self._sync_center_view()
        self._refresh_import_summary()

    def _filter_images(self, images: List[Path]) -> List[Path]:
        """Filter images based on current filter state"""
        pick_value = str(self.media_filter_state.get("pick", "any"))
        rating_value = str(self.media_filter_state.get("rating", "any"))
        color_value = str(self.media_filter_state.get("color", "any"))
        days_value = int(self.media_filter_state.get("days", self.FILTER_DAYS_DEFAULT))
        sort_by = str(self.media_filter_state.get("sort_by", "none"))

        filtered = []
        cutoff_date = datetime.now().timestamp() - (days_value * 24 * 60 * 60) if days_value < self.FILTER_DAYS_MAX else 0

        for image_path in images:
            # Check days filter
            if days_value < self.FILTER_DAYS_MAX:
                try:
                    mtime = image_path.stat().st_mtime
                    if mtime < cutoff_date:
                        continue
                except (OSError, IOError):
                    pass

            # Get marker data from grid
            marker_data = self.grid_widget.image_markers.get(image_path, {}) if self.grid_widget else {}

            # Check pick filter
            if pick_value != "any":
                pick_marker = str(marker_data.get("pick", "none")).lower()
                if pick_value == "accepted" and pick_marker != "accepted":
                    continue
                if pick_value == "rejected" and pick_marker != "rejected":
                    continue
                if pick_value == "none" and pick_marker in ("accepted", "rejected"):
                    continue

            # Check rating filter
            if rating_value != "any":
                rating_marker = str(marker_data.get("rating", "0"))
                try:
                    current_rating = int(rating_marker) if rating_marker else 0
                except ValueError:
                    current_rating = 0

                if rating_value.startswith("exact_"):
                    target_rating = int(rating_value.split("_")[1])
                    if current_rating != target_rating:
                        continue
                elif rating_value == "0":
                    if current_rating != 0:
                        continue
                else:
                    min_rating = int(rating_value)
                    if current_rating < min_rating:
                        continue

            # Check color filter
            if color_value != "any":
                color_marker = str(marker_data.get("color", "none")).lower()
                if color_value == "none":
                    if color_marker != "none" and color_marker:
                        continue
                elif color_marker != color_value:
                    continue

            filtered.append(image_path)

        # Apply sorting
        if sort_by == "rating_asc":
            filtered.sort(key=lambda p: int(self.grid_widget.image_markers.get(p, {}).get("rating", 0)) if self.grid_widget else 0)
        elif sort_by == "rating_desc":
            filtered.sort(key=lambda p: int(self.grid_widget.image_markers.get(p, {}).get("rating", 0)) if self.grid_widget else 0, reverse=True)

        return filtered

    # ===== Grid Methods =====

    def _on_columns_changed(self, value: int) -> None:
        """Handle grid columns change"""
        self.grid_columns = value
        self.columns_value_label.setText(str(value))
        if self.grid_widget:
            # Simple: (viewport - spacing) / columns
            w = self.scroll_area.viewport().width()
            cell = (w - (value - 1) * 8) // value
            self.grid_widget.set_grid_layout(
                columns=value,
                cell_width=max(100, cell),
                cell_height=int(max(100, cell) * 1.12) + 42,
                spacing=8,
                left_margin=0,
                right_margin=0
            )

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """Handle splitter moved - save user preferences and update grid"""
        # Save the new splitter sizes
        if self.main_splitter:
            self._splitter_sizes = self.main_splitter.sizes()
        # Update grid layout after splitter move
        if self.resize_timer:
            self.resize_timer.start(100)

    def _restore_splitter_sizes(self) -> None:
        """Restore user-set splitter sizes to prevent automatic resizing"""
        if self.main_splitter and self._splitter_sizes:
            current_sizes = self.main_splitter.sizes()
            # Only restore if sizes actually changed (not due to user interaction)
            if current_sizes != self._splitter_sizes:
                self.main_splitter.setSizes(self._splitter_sizes)

    def _apply_grid_layout(self) -> None:
        """Apply grid layout"""
        if not self.grid_widget:
            return
        w = self.scroll_area.viewport().width()
        c = self.grid_columns
        cell = (w - (c - 1) * 8) // c
        self.grid_widget.set_grid_layout(
            columns=c,
            cell_width=max(100, cell),
            cell_height=int(max(100, cell) * 1.12) + 42,
            spacing=8,
            left_margin=0,
            right_margin=0
        )

    def _on_grid_selection_changed(self, image_paths: List[Path]) -> None:
        """Handle grid selection change"""
        self.selected_images = list(image_paths)
        self._refresh_import_summary()
        
        # Update IPTC fields from selected images
        self._update_iptc_fields_from_selection()

    def _on_marker_changed(self, image_path: Path, marker_type: str, value: str) -> None:
        """Handle marker change from grid"""
        # Update filter if needed
        if marker_type in ("pick", "rating", "color"):
            self._apply_media_filters_to_grid()

    def _select_all_images(self) -> None:
        """Select all images"""
        if self.grid_widget:
            self.grid_widget.select_all_images()

    def _clear_selected_images(self) -> None:
        """Clear selection"""
        if self.grid_widget:
            self.grid_widget.clear_selection()

    # ===== Import Settings Methods =====

    def _render_import_sections(self, parent_layout: QVBoxLayout) -> None:
        """Render import settings sections"""
        parent_layout.addWidget(CollapsibleSection("File Handling", self._file_handling_stack()))
        parent_layout.addWidget(CollapsibleSection("Apply During Import", self._create_iptc_widget()))
        parent_layout.addStretch()

    def _file_handling_stack(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        layout.addWidget(self._create_file_handling_widget())
        layout.addWidget(self._create_destination_widget())
        layout.addWidget(self._create_file_renaming_widget())
        return widget

    def _add_import_group(self, panel_key: str, title: str, content_widget: QWidget, parent_layout: QVBoxLayout) -> None:
        """Add collapsible import group"""
        group_widget = self._create_collapsible_group(title, content_widget, True, panel_key)
        parent_layout.addWidget(group_widget)

    def _create_collapsible_group(self, title: str, content_widget: QWidget, is_expanded: bool = True, panel_key: str = "") -> QWidget:
        """Create a collapsible group widget"""
        panel_color = (35, 35, 40)
        lighter_color = tuple(min(255, int(c + (255 - c) * 0.25)) for c in panel_color)
        lighter_color_str = f"rgb({lighter_color[0]}, {lighter_color[1]}, {lighter_color[2]})"

        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(0)

        header_widget = QWidget()
        header_widget.setFixedHeight(28)
        header_widget.setStyleSheet(
            f"background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 5px;"
        )
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 4, 10, 4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold; background-color: transparent; border: none;")

        toggle_button = QPushButton("▼" if is_expanded else "▶")
        toggle_button.setFixedSize(18, 18)
        toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_button.setStyleSheet(
            f"QPushButton {{ color: white; background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 3px; font-size: 9px; font-weight: bold; }}"
        )

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(toggle_button)

        if not is_expanded:
            content_widget.hide()

        def toggle_content() -> None:
            is_visible = content_widget.isVisible()
            content_widget.setVisible(not is_visible)
            toggle_button.setText("▼" if not is_visible else "▶")

        toggle_button.clicked.connect(toggle_content)

        # Style content widget
        content_widget.setStyleSheet(
            f"background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 5px; border-top-left-radius: 0px; border-top-right-radius: 0px; margin-top: -1px;"
        )

        group_layout.addWidget(header_widget)
        group_layout.addWidget(content_widget)
        return group_widget

    def _create_import_preset_widget(self) -> QWidget:
        """Create import preset widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel("Import Preset"))
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(120)
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        layout.addWidget(self.preset_combo)
        layout.addWidget(self._create_small_button("Create", self._create_import_preset))
        layout.addWidget(self._create_small_button("Save", self._save_selected_preset))
        layout.addWidget(self._create_small_button("Rename", self._rename_import_preset))
        layout.addWidget(self._create_small_button("Delete", self._delete_import_preset))
        self.preset_feedback_label = QLabel("")
        self.preset_feedback_label.setStyleSheet("color: rgb(180, 180, 180); font-size: 11px;")
        layout.addWidget(self.preset_feedback_label)

        return widget

    def _create_file_handling_widget(self) -> QWidget:
        """Create file handling widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        skip_duplicates = QCheckBox("Don't Import Suspected Duplicates")
        skip_rejected = QCheckBox("Don't Import Rejected Images")
        for checkbox, key in ((skip_duplicates, "skip_duplicates"), (skip_rejected, "skip_rejected")):
            checkbox.toggled.connect(lambda checked, setting_key=key: self._on_import_setting_changed(setting_key, checked))
            self.import_panel_widgets[key] = checkbox
            layout.addWidget(checkbox)

        return widget

    def _create_file_renaming_widget(self) -> QWidget:
        """Create file renaming widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Pattern:"))
        self.rename_preset_label = QLabel("Original filename")
        self.rename_preset_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.rename_preset_label)
        layout.addStretch()

        edit_button = self._create_small_button("Configure...", self._open_rename_dialog)
        layout.addWidget(edit_button)

        return widget

    def _create_destination_widget(self) -> QWidget:
        """Create destination widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Destination"))
        self.destination_preset_label = QLabel("Default")
        self.destination_preset_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.destination_preset_label)
        layout.addStretch()

        edit_button = self._create_small_button("Configure...", self._open_destination_dialog)
        layout.addWidget(edit_button)

        return widget

    def _develop_settings_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel("Develop Settings"))
        combo = QComboBox()
        combo.addItem("None")
        row.addWidget(combo, 1)
        return row

    def _create_iptc_widget(self) -> QWidget:
        """Create IPTC metadata widget with all fields and smart asterisk handling"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        layout.addLayout(self._develop_settings_row())

        # Preset selector row
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Metadata"))
        self.iptc_preset_label = QLabel("Default")
        self.iptc_preset_label.setStyleSheet("color: white; font-weight: bold;")
        preset_layout.addWidget(self.iptc_preset_label)
        preset_layout.addStretch()

        edit_button = self._create_small_button("Configure...", self._open_iptc_dialog)
        preset_layout.addWidget(edit_button)

        layout.addLayout(preset_layout)

        # Help text for asterisk behavior
        help_label = QLabel("* = existing in images (delete to remove, keep to preserve)")
        help_label.setStyleSheet("color: rgb(180, 180, 180); font-size: 10px;")
        layout.addWidget(help_label)

        # Creator field
        creator_layout = QHBoxLayout()
        creator_layout.addWidget(QLabel("Creator:"))
        self.iptc_creator_input = QLineEdit()
        self.iptc_creator_input.setPlaceholderText("Photographer name")
        self.iptc_creator_input.textEdited.connect(self._on_iptc_field_changed)
        creator_layout.addWidget(self.iptc_creator_input)
        layout.addLayout(creator_layout)

        # Copyright field
        copyright_layout = QHBoxLayout()
        copyright_layout.addWidget(QLabel("Copyright:"))
        self.iptc_copyright_input = QLineEdit()
        self.iptc_copyright_input.setPlaceholderText("Copyright notice")
        self.iptc_copyright_input.textEdited.connect(self._on_iptc_field_changed)
        copyright_layout.addWidget(self.iptc_copyright_input)
        layout.addLayout(copyright_layout)

        # Credit field
        credit_layout = QHBoxLayout()
        credit_layout.addWidget(QLabel("Credit:"))
        self.iptc_credit_input = QLineEdit()
        self.iptc_credit_input.setPlaceholderText("Credit line")
        self.iptc_credit_input.textEdited.connect(self._on_iptc_field_changed)
        credit_layout.addWidget(self.iptc_credit_input)
        layout.addLayout(credit_layout)

        # Source field
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))
        self.iptc_source_input = QLineEdit()
        self.iptc_source_input.setPlaceholderText("Source")
        self.iptc_source_input.textEdited.connect(self._on_iptc_field_changed)
        source_layout.addWidget(self.iptc_source_input)
        layout.addLayout(source_layout)

        # Keywords text area
        keywords_label = QLabel("Keywords")
        layout.addWidget(keywords_label)

        self.iptc_keywords_input = QTextEdit()
        self.iptc_keywords_input.setMaximumHeight(100)
        self.iptc_keywords_input.setPlaceholderText("Enter keywords, one per line...\nExisting keywords will be marked with *")
        self.iptc_keywords_input.textChanged.connect(self._on_iptc_keywords_changed)
        layout.addWidget(self.iptc_keywords_input)

        return widget

    def _on_iptc_field_changed(self) -> None:
        """Handle IPTC field change - track removed asterisk-marked fields"""
        sender = self.sender()
        if isinstance(sender, QLineEdit):
            text = sender.text()
            field_map = {
                self.iptc_creator_input: "creator",
                self.iptc_copyright_input: "copyright",
                self.iptc_credit_input: "credit",
                self.iptc_source_input: "source",
            }
            field_name = field_map.get(sender)
            if field_name:
                # Check if this field had an asterisk-marked value that was cleared
                if field_name in self._iptc_existing_data:
                    if not text:  # Field was cleared -> mark as removed
                        self._iptc_removed_fields.add(field_name)
                    elif not text.startswith("*"):  # User typed new value without asterisk
                        self._iptc_removed_fields.discard(field_name)  # User is overriding, not removing

            # If user starts typing and field has asterisk-marked value, clear it
            if text.startswith("*") and len(text) > 1 and not text[1:].startswith("*"):
                # User is editing an asterisk-marked field - remove the asterisk
                sender.setText(text[1:])

    def _on_iptc_keywords_changed(self) -> None:
        """Handle IPTC keywords change - track removed asterisk-marked keywords"""
        if self._updating_import_ui:
            return

        # Get current keywords from text field
        current_text = self.iptc_keywords_input.toPlainText() if self.iptc_keywords_input else ""
        current_keywords = {kw.strip() for kw in current_text.split("\n") if kw.strip()}

        # Find asterisk-marked keywords that were removed
        removed_asterisk_keywords = set()
        for orig_kw in self._iptc_original_keywords:
            asterisk_kw = f"*{orig_kw}"
            # If original was in the list but asterisk version is not in current
            if asterisk_kw not in current_keywords and orig_kw not in current_keywords:
                removed_asterisk_keywords.add(orig_kw)

        self._iptc_removed_keywords = removed_asterisk_keywords

        # Save to settings
        import_config = self._get_import_config()
        current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
        current_settings["iptc_keywords"] = current_text
        import_config[self.IMPORT_SETTINGS_KEY] = current_settings
        self._save_import_config(import_config)

    def _get_iptc_data_from_ui(self) -> IPTCData:
        """Get IPTC data from UI fields, stripping asterisks"""
        def strip_asterisk(text: str) -> str:
            return text[1:] if text.startswith("*") else text

        # Get keywords, handling asterisks
        keywords_text = self.iptc_keywords_input.toPlainText() if self.iptc_keywords_input else ""
        keywords = []
        for kw in keywords_text.split("\n"):
            kw = kw.strip()
            if kw:
                # Strip asterisk if present
                keywords.append(strip_asterisk(kw))

        return IPTCData(
            creator=strip_asterisk(self.iptc_creator_input.text()) if self.iptc_creator_input else "",
            copyright=strip_asterisk(self.iptc_copyright_input.text()) if self.iptc_copyright_input else "",
            credit=strip_asterisk(self.iptc_credit_input.text()) if self.iptc_credit_input else "",
            source=strip_asterisk(self.iptc_source_input.text()) if self.iptc_source_input else "",
            keywords=keywords,
        )

    def _update_iptc_fields_from_selection(self) -> None:
        """Update IPTC fields when image selection changes - read from selected images"""
        if not self.selected_images or len(self.selected_images) == 0:
            # No selection - clear existing data tracking
            self._iptc_existing_data = {}
            self._iptc_original_keywords = set()
            self._iptc_removed_keywords = set()
            return

        # Read IPTC data from all selected images
        all_keywords: set[str] = set()
        creator_values: set[str] = set()
        copyright_values: set[str] = set()
        credit_values: set[str] = set()
        source_values: set[str] = set()

        for image_path in self.selected_images:
            iptc_data = read_iptc_from_image(image_path)
            if iptc_data.creator:
                creator_values.add(iptc_data.creator)
            if iptc_data.copyright:
                copyright_values.add(iptc_data.copyright)
            if iptc_data.credit:
                credit_values.add(iptc_data.credit)
            if iptc_data.source:
                source_values.add(iptc_data.source)
            all_keywords.update(iptc_data.keywords)

        self._updating_import_ui = True

        # Update fields with asterisk-prefixed values if they exist in images
        # If all images have the same value, show it with asterisk
        # If values differ or are empty, leave field empty

        if len(creator_values) == 1:
            creator = creator_values.pop()
            if self.iptc_creator_input:
                self.iptc_creator_input.setText(f"*{creator}")
                self._iptc_existing_data["creator"] = creator

        if len(copyright_values) == 1:
            copyright = copyright_values.pop()
            if self.iptc_copyright_input:
                self.iptc_copyright_input.setText(f"*{copyright}")
                self._iptc_existing_data["copyright"] = copyright

        if len(credit_values) == 1:
            credit = credit_values.pop()
            if self.iptc_credit_input:
                self.iptc_credit_input.setText(f"*{credit}")
                self._iptc_existing_data["credit"] = credit

        if len(source_values) == 1:
            source = source_values.pop()
            if self.iptc_source_input:
                self.iptc_source_input.setText(f"*{source}")
                self._iptc_existing_data["source"] = source

        # Update keywords with asterisk prefix
        if all_keywords and self.iptc_keywords_input:
            asterisk_keywords = [f"*{kw}" for kw in sorted(all_keywords)]
            self.iptc_keywords_input.setPlainText("\n".join(asterisk_keywords))
            self._iptc_original_keywords = all_keywords.copy()
            self._iptc_removed_keywords = set()

        self._updating_import_ui = False

    def _create_small_button(self, text: str, handler) -> QPushButton:
        """Create a small styled button"""
        button = QPushButton(text)
        button.clicked.connect(handler)
        button.setStyleSheet(
            "QPushButton { background-color: rgb(62, 62, 68); color: white; border: 1px solid rgb(80, 80, 85); border-radius: 4px; padding: 4px 8px; font-size: 11px; }"
            "QPushButton:hover { background-color: rgb(74, 74, 80); }"
        )
        return button

    # ===== Import Configuration Methods =====

    def _default_import_settings(self) -> dict[str, object]:
        return {
            "skip_duplicates": True,
            "skip_rejected": True,
            "selected_template": self.RENAME_TEMPLATE_OPTIONS[0],
            "template_pattern": self.RENAME_TEMPLATE_OPTIONS[0],
            "target_root": "",
            "organize_mode": self.ORGANIZE_OPTIONS[0][0],
            "date_format": self.DATE_FORMAT_OPTIONS[0][0],
            "delete_after_import": False,
        }

    def _default_import_config(self) -> dict[str, object]:
        settings = self._default_import_settings()
        return {
            self.IMPORT_PRESET_ACTIVE_KEY: self.DEFAULT_IMPORT_PRESET_NAME,
            self.IMPORT_SETTINGS_KEY: settings,
            "panel_states": {
                "import_preset": True,
                "file_handling": True,
                "file_renaming": True,
                "destination": True,
            },
            self.RENAME_TEMPLATE_LIST_KEY: self._default_rename_templates(),
            self.IMPORT_PRESET_LIST_KEY: {
                self.DEFAULT_IMPORT_PRESET_NAME: dict(settings),
            },
        }

    def _default_rename_templates(self) -> dict[str, str]:
        return {
            self.DEFAULT_RENAME_TEMPLATE_NAMES[pattern]: pattern
            for pattern in self.RENAME_TEMPLATE_OPTIONS
        }

    def _get_import_config(self) -> dict[str, object]:
        import_config = self.config_manager.get(self.IMPORT_PRESET_CONFIG_KEY)
        if not isinstance(import_config, dict):
            import_config = self._default_import_config()
            self.config_manager.set(self.IMPORT_PRESET_CONFIG_KEY, import_config)
        presets = import_config.get(self.IMPORT_PRESET_LIST_KEY)
        if not isinstance(presets, dict) or not presets:
            import_config = self._default_import_config()
            self.config_manager.set(self.IMPORT_PRESET_CONFIG_KEY, import_config)
        return import_config

    def _normalize_import_settings(self, settings: Optional[dict[str, object]]) -> dict[str, object]:
        normalized = self._default_import_settings()
        if isinstance(settings, dict):
            normalized.update(settings)
        rename_templates = self._get_rename_templates_map()
        selected_template = str(normalized.get("selected_template", "")).strip()
        template_pattern = str(normalized.get("template_pattern", "")).strip()
        if selected_template in rename_templates:
            normalized["selected_template"] = selected_template
        normalized["template_pattern"] = rename_templates.get(normalized["selected_template"], template_pattern)
        return normalized

    def _get_rename_templates_map(self) -> dict[str, str]:
        import_config = self._get_import_config()
        templates = import_config.get(self.RENAME_TEMPLATE_LIST_KEY, {})
        if isinstance(templates, dict) and templates:
            return templates
        return self._default_rename_templates()

    def _save_import_config(self, import_config: dict[str, object]) -> None:
        self.config_manager.set(self.IMPORT_PRESET_CONFIG_KEY, import_config)

    def _load_import_settings_into_ui(self) -> None:
        """Load settings into UI - always use Default preset on dialog open"""
        if self.preset_combo is None:
            return

        import_config = self._get_import_config()
        preset_names = sorted(import_config[self.IMPORT_PRESET_LIST_KEY].keys())

        # Always use Default preset on dialog open
        active_preset = self.DEFAULT_IMPORT_PRESET_NAME

        # Update config to reflect Default as active
        if import_config.get(self.IMPORT_PRESET_ACTIVE_KEY) != active_preset:
            import_config[self.IMPORT_PRESET_ACTIVE_KEY] = active_preset
            if active_preset in import_config[self.IMPORT_PRESET_LIST_KEY]:
                import_config[self.IMPORT_SETTINGS_KEY] = self._normalize_import_settings(
                    import_config[self.IMPORT_PRESET_LIST_KEY][active_preset]
                )
            self._save_import_config(import_config)

        # Get settings for Default preset
        current_settings = self._normalize_import_settings(
            import_config[self.IMPORT_PRESET_LIST_KEY].get(active_preset, {})
        )

        self._updating_import_ui = True
        self.preset_combo.clear()
        self.preset_combo.addItems(preset_names)
        self.preset_combo.setCurrentText(active_preset)

        # Update checkbox values
        skip_duplicates_widget = self.import_panel_widgets.get("skip_duplicates")
        if isinstance(skip_duplicates_widget, QCheckBox):
            skip_duplicates_widget.setChecked(bool(current_settings.get("skip_duplicates", True)))

        skip_rejected_widget = self.import_panel_widgets.get("skip_rejected")
        if isinstance(skip_rejected_widget, QCheckBox):
            skip_rejected_widget.setChecked(bool(current_settings.get("skip_rejected", True)))

        self._updating_import_ui = False
        self._update_rename_preset_display()
        self._update_destination_preset_display()
        self._update_iptc_preset_display()

        # Load IPTC keywords from settings
        iptc_keywords = str(current_settings.get("iptc_keywords", ""))
        if self.iptc_keywords_input:
            self.iptc_keywords_input.setPlainText(iptc_keywords)

    def _on_import_setting_changed(self, key: str, value: object) -> None:
        """Handle import setting change"""
        if self._updating_import_ui:
            return
        import_config = self._get_import_config()
        current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
        current_settings[key] = value
        import_config[self.IMPORT_SETTINGS_KEY] = current_settings
        self._save_import_config(import_config)

    def _current_preset_name(self) -> str:
        if self.preset_combo is not None and self.preset_combo.currentText():
            return self.preset_combo.currentText()
        return self.DEFAULT_IMPORT_PRESET_NAME

    # ===== Preset Management =====

    def _create_import_preset(self) -> None:
        """Create new import preset"""
        preset_name, accepted = QInputDialog.getText(self, "Create Import Preset", "Preset name:")
        if not accepted or not preset_name:
            return

        unique_name = self._make_unique_preset_name(preset_name)
        import_config = self._get_import_config()
        presets = dict(import_config[self.IMPORT_PRESET_LIST_KEY])
        presets[unique_name] = self._get_current_import_settings_from_ui()
        import_config[self.IMPORT_PRESET_LIST_KEY] = presets
        import_config[self.IMPORT_PRESET_ACTIVE_KEY] = unique_name
        import_config[self.IMPORT_SETTINGS_KEY] = dict(presets[unique_name])
        self._save_import_config(import_config)
        self._load_import_settings_into_ui()
        self._set_preset_feedback(f"Preset saved as '{unique_name}'.")

    def _save_selected_preset(self) -> None:
        """Save current settings to selected preset"""
        preset_name = self._current_preset_name()
        import_config = self._get_import_config()
        presets = dict(import_config[self.IMPORT_PRESET_LIST_KEY])
        presets[preset_name] = self._get_current_import_settings_from_ui()
        import_config[self.IMPORT_PRESET_LIST_KEY] = presets
        import_config[self.IMPORT_PRESET_ACTIVE_KEY] = preset_name
        import_config[self.IMPORT_SETTINGS_KEY] = dict(presets[preset_name])
        self._save_import_config(import_config)
        self._set_preset_feedback(f"Preset '{preset_name}' updated.")

    def _rename_import_preset(self) -> None:
        """Rename current preset"""
        current_name = self._current_preset_name()
        if current_name == self.DEFAULT_IMPORT_PRESET_NAME:
            QMessageBox.information(self, "Rename Preset", "Cannot rename the default preset.")
            return

        new_name, accepted = QInputDialog.getText(self, "Rename Import Preset", "New name:", text=current_name)
        if not accepted or not new_name:
            return

        unique_name = self._make_unique_preset_name(new_name, excluded_name=current_name)
        import_config = self._get_import_config()
        presets = dict(import_config[self.IMPORT_PRESET_LIST_KEY])
        presets[unique_name] = presets.pop(current_name)
        import_config[self.IMPORT_PRESET_LIST_KEY] = presets
        import_config[self.IMPORT_PRESET_ACTIVE_KEY] = unique_name
        self._save_import_config(import_config)
        self._load_import_settings_into_ui()
        self._set_preset_feedback(f"Preset renamed to '{unique_name}'.")

    def _delete_import_preset(self) -> None:
        """Delete current preset"""
        current_name = self._current_preset_name()
        if current_name == self.DEFAULT_IMPORT_PRESET_NAME:
            QMessageBox.information(self, "Delete Preset", "Cannot delete the default preset.")
            return

        reply = QMessageBox.question(self, "Delete Preset", f"Delete preset '{current_name}'?")
        if reply != QMessageBox.StandardButton.Yes:
            return

        import_config = self._get_import_config()
        presets = dict(import_config[self.IMPORT_PRESET_LIST_KEY])
        presets.pop(current_name, None)
        next_name = sorted(presets.keys())[0] if presets else self.DEFAULT_IMPORT_PRESET_NAME
        if not presets:
            presets = self._default_import_config()[self.IMPORT_PRESET_LIST_KEY]
        import_config[self.IMPORT_PRESET_LIST_KEY] = presets
        import_config[self.IMPORT_PRESET_ACTIVE_KEY] = next_name
        import_config[self.IMPORT_SETTINGS_KEY] = self._normalize_import_settings(presets[next_name])
        self._save_import_config(import_config)
        self._load_import_settings_into_ui()
        self._set_preset_feedback(f"Preset '{current_name}' deleted.")

    def _on_preset_selected(self, preset_name: str) -> None:
        """Handle preset selection - restore ALL settings"""
        if self._updating_import_ui or not preset_name:
            return

        import_config = self._get_import_config()
        presets = import_config[self.IMPORT_PRESET_LIST_KEY]
        selected_settings = self._normalize_import_settings(presets.get(preset_name))

        import_config[self.IMPORT_PRESET_ACTIVE_KEY] = preset_name
        import_config[self.IMPORT_SETTINGS_KEY] = selected_settings

        # Restore destination preset NAME and settings
        destination_preset_name = str(selected_settings.get("destination_preset_name", self.DEFAULT_DESTINATION_PRESET_NAME))
        destination_presets = import_config.get(self.DESTINATION_PRESET_LIST_KEY, {})

        # If the saved preset name exists, use it; otherwise use default
        if destination_preset_name not in destination_presets:
            destination_preset_name = self.DEFAULT_DESTINATION_PRESET_NAME
            if destination_preset_name not in destination_presets:
                destination_presets[destination_preset_name] = {}

        import_config[self.DESTINATION_PRESET_ACTIVE_KEY] = destination_preset_name

        # Update destination preset with saved values
        destination_presets[destination_preset_name]["target_root"] = selected_settings.get("target_root", "")
        destination_presets[destination_preset_name]["organize_mode"] = selected_settings.get("organize_mode", self.ORGANIZE_OPTIONS[0][0])
        destination_presets[destination_preset_name]["date_format"] = selected_settings.get("date_format", self.DATE_FORMAT_OPTIONS[0][0])
        destination_presets[destination_preset_name]["delete_after_import"] = selected_settings.get("delete_after_import", False)
        import_config[self.DESTINATION_PRESET_LIST_KEY] = destination_presets

        self._save_import_config(import_config)

        self._updating_import_ui = True

        # Restore File Handling checkboxes
        skip_duplicates_widget = self.import_panel_widgets.get("skip_duplicates")
        if isinstance(skip_duplicates_widget, QCheckBox):
            skip_duplicates_widget.setChecked(bool(selected_settings.get("skip_duplicates", True)))

        skip_rejected_widget = self.import_panel_widgets.get("skip_rejected")
        if isinstance(skip_rejected_widget, QCheckBox):
            skip_rejected_widget.setChecked(bool(selected_settings.get("skip_rejected", True)))

        # Restore Filter settings and update media_filter_state
        pick_filter = str(selected_settings.get("pick_filter", "any"))
        if self.pick_filter_combo:
            index = self.pick_filter_combo.findData(pick_filter)
            if index >= 0:
                self.pick_filter_combo.setCurrentIndex(index)
        self.media_filter_state["pick"] = pick_filter

        rating_filter = str(selected_settings.get("rating_filter", "any"))
        if self.rating_filter_combo:
            index = self.rating_filter_combo.findData(rating_filter)
            if index >= 0:
                self.rating_filter_combo.setCurrentIndex(index)
        self.media_filter_state["rating"] = rating_filter

        color_filter = str(selected_settings.get("color_filter", "any"))
        if self.color_filter_combo:
            index = self.color_filter_combo.findData(color_filter)
            if index >= 0:
                self.color_filter_combo.setCurrentIndex(index)
        self.media_filter_state["color"] = color_filter

        # Restore Days and Sort
        days_back = int(selected_settings.get("days_back", self.FILTER_DAYS_DEFAULT))
        if self.days_back_spin:
            self.days_back_spin.setValue(days_back)
        self.media_filter_state["days"] = days_back

        sort_by = str(selected_settings.get("sort_by", "none"))
        if self.sort_combo:
            index = self.sort_combo.findData(sort_by)
            if index >= 0:
                self.sort_combo.setCurrentIndex(index)
        self.media_filter_state["sort_by"] = sort_by

        # Restore Recursive loading
        recursive_loading = bool(selected_settings.get("recursive_loading", True))
        if self.recursive_checkbox:
            self.recursive_checkbox.setChecked(recursive_loading)

        self._updating_import_ui = False

        # Apply filters after restoring all settings
        self._apply_media_filters_to_grid()

        self._update_rename_preset_display()
        self._update_destination_preset_display()
        self._update_iptc_preset_display()

        # Restore IPTC keywords from preset
        iptc_keywords = str(selected_settings.get("iptc_keywords", ""))
        if self.iptc_keywords_input:
            self.iptc_keywords_input.setPlainText(iptc_keywords)

        # Restore IPTC preset name
        iptc_preset_name = str(selected_settings.get("iptc_preset_name", self.DEFAULT_IPTC_PRESET_NAME))
        import_config[self.IPTC_PRESET_ACTIVE_KEY] = iptc_preset_name
        self._save_import_config(import_config)

    def _make_unique_preset_name(self, base_name: str, excluded_name: str = "") -> str:
        """Make unique preset name"""
        import_config = self._get_import_config()
        presets = import_config[self.IMPORT_PRESET_LIST_KEY]
        existing_names = set(presets.keys())
        if excluded_name:
            existing_names.discard(excluded_name)

        if base_name not in existing_names:
            return base_name

        counter = 1
        while f"{base_name} ({counter})" in existing_names:
            counter += 1
        return f"{base_name} ({counter})"

    def _set_preset_feedback(self, message: str) -> None:
        """Set preset feedback message"""
        if self.preset_feedback_label:
            self.preset_feedback_label.setText(message)
            QTimer.singleShot(3000, lambda: self.preset_feedback_label.setText(""))

    def _get_current_import_settings_from_ui(self) -> dict[str, object]:
        """Read ALL current import settings from UI"""
        import_config = self._get_import_config()
        current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))

        # File handling checkboxes
        skip_duplicates_widget = self.import_panel_widgets.get("skip_duplicates")
        skip_rejected_widget = self.import_panel_widgets.get("skip_rejected")

        # Rename template
        rename_templates = self._get_rename_templates_map()
        selected_template = str(current_settings.get("selected_template", self.RENAME_TEMPLATE_OPTIONS[0]))
        template_pattern = rename_templates.get(selected_template, self.RENAME_TEMPLATE_OPTIONS[0])

        # Destination preset
        destination_presets = import_config.get(self.DESTINATION_PRESET_LIST_KEY, {})
        active_destination = str(import_config.get(self.DESTINATION_PRESET_ACTIVE_KEY, self.DEFAULT_DESTINATION_PRESET_NAME))
        dest_settings = destination_presets.get(active_destination, {})

        # Save destination preset NAME too
        destination_preset_name = active_destination

        # Grid/filter settings from UI widgets
        pick_filter = str(self.pick_filter_combo.currentData()) if self.pick_filter_combo else "any"
        rating_filter = str(self.rating_filter_combo.currentData()) if self.rating_filter_combo else "any"
        color_filter = str(self.color_filter_combo.currentData()) if self.color_filter_combo else "any"
        days_back = int(self.days_back_spin.value()) if self.days_back_spin else self.FILTER_DAYS_DEFAULT
        sort_by = str(self.sort_combo.currentData()) if self.sort_combo else "none"
        recursive_loading = bool(self.recursive_checkbox.isChecked()) if self.recursive_checkbox else True

        # IPTC settings
        iptc_keywords = self.iptc_keywords_input.toPlainText() if self.iptc_keywords_input else ""
        iptc_preset_name = str(import_config.get(self.IPTC_PRESET_ACTIVE_KEY, self.DEFAULT_IPTC_PRESET_NAME))

        return {
            # File handling
            "skip_duplicates": skip_duplicates_widget.isChecked() if isinstance(skip_duplicates_widget, QCheckBox) else True,
            "skip_rejected": skip_rejected_widget.isChecked() if isinstance(skip_rejected_widget, QCheckBox) else True,
            # Renaming
            "selected_template": selected_template,
            "template_pattern": template_pattern,
            # Destination - save both name and values
            "destination_preset_name": destination_preset_name,
            "target_root": str(dest_settings.get("target_root", current_settings.get("target_root", ""))),
            "organize_mode": str(dest_settings.get("organize_mode", current_settings.get("organize_mode", self.ORGANIZE_OPTIONS[0][0]))),
            "date_format": str(dest_settings.get("date_format", current_settings.get("date_format", self.DATE_FORMAT_OPTIONS[0][0]))),
            "delete_after_import": bool(dest_settings.get("delete_after_import", current_settings.get("delete_after_import", False))),
            # Grid/filter settings
            "pick_filter": pick_filter,
            "rating_filter": rating_filter,
            "color_filter": color_filter,
            "days_back": days_back,
            "sort_by": sort_by,
            "recursive_loading": recursive_loading,
            # IPTC settings
            "iptc_preset_name": iptc_preset_name,
            "iptc_keywords": iptc_keywords,
        }

    def _update_rename_preset_display(self) -> None:
        """Update rename preset display"""
        if self.rename_preset_label:
            import_config = self._get_import_config()
            current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
            template_name = str(current_settings.get("selected_template", "Original filename"))
            self.rename_preset_label.setText(template_name)

    def _update_destination_preset_display(self) -> None:
        """Update destination preset display"""
        if self.destination_preset_label:
            import_config = self._get_import_config()
            preset_name = str(import_config.get(self.DESTINATION_PRESET_ACTIVE_KEY, self.DEFAULT_DESTINATION_PRESET_NAME))
            self.destination_preset_label.setText(preset_name)

    # ===== Dialog Methods =====

    def _open_rename_dialog(self) -> None:
        """Open the rename pattern dialog"""
        import_config = self._get_import_config()
        templates = self._get_rename_templates_map()
        current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
        current_template = str(current_settings.get("selected_template", "Original filename"))

        dialog = RenamePatternDialog(
            self,
            templates,
            current_template,
            self.SAMPLE_FILENAME,
            self.SAMPLE_SEQUENCE,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_name, selected_pattern, updated_templates = dialog.get_result()
            import_config[self.RENAME_TEMPLATE_LIST_KEY] = updated_templates
            current_settings["selected_template"] = selected_name
            current_settings["template_pattern"] = selected_pattern
            import_config[self.IMPORT_SETTINGS_KEY] = current_settings
            self._save_import_config(import_config)
            self._update_rename_preset_display()

    def _open_destination_dialog(self) -> None:
        """Open the destination settings dialog"""
        import_config = self._get_import_config()

        # Get or initialize destination presets
        destination_presets = import_config.get(self.DESTINATION_PRESET_LIST_KEY)
        if not isinstance(destination_presets, dict) or not destination_presets:
            current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
            destination_presets = {
                self.DEFAULT_DESTINATION_PRESET_NAME: {
                    "target_root": str(current_settings.get("target_root", "")),
                    "organize_mode": str(current_settings.get("organize_mode", self.ORGANIZE_OPTIONS[0][0])),
                    "date_format": str(current_settings.get("date_format", self.DATE_FORMAT_OPTIONS[0][0])),
                    "delete_after_import": bool(current_settings.get("delete_after_import", False)),
                }
            }
            import_config[self.DESTINATION_PRESET_LIST_KEY] = destination_presets

        active_preset = str(import_config.get(self.DESTINATION_PRESET_ACTIVE_KEY, self.DEFAULT_DESTINATION_PRESET_NAME))
        if active_preset not in destination_presets:
            active_preset = self.DEFAULT_DESTINATION_PRESET_NAME

        dialog = DestinationSettingsDialog(
            self,
            destination_presets,
            active_preset,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_name, selected_settings, updated_presets = dialog.get_result()
            import_config[self.DESTINATION_PRESET_LIST_KEY] = updated_presets
            import_config[self.DESTINATION_PRESET_ACTIVE_KEY] = selected_name

            # Update current import settings
            current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
            current_settings["target_root"] = selected_settings["target_root"]
            current_settings["organize_mode"] = selected_settings["organize_mode"]
            current_settings["date_format"] = selected_settings["date_format"]
            current_settings["delete_after_import"] = selected_settings["delete_after_import"]
            import_config[self.IMPORT_SETTINGS_KEY] = current_settings

            self._save_import_config(import_config)
            self._update_destination_preset_display()

    def _open_iptc_dialog(self) -> None:
        """Open the IPTC preset dialog"""
        import_config = self._get_import_config()

        # Get or initialize IPTC presets
        iptc_presets = import_config.get(self.IPTC_PRESET_LIST_KEY)
        if not isinstance(iptc_presets, dict) or not iptc_presets:
            default_preset = get_default_iptc_preset()
            iptc_presets = {default_preset.name: default_preset.to_dict()}
            import_config[self.IPTC_PRESET_LIST_KEY] = iptc_presets

        active_preset = str(import_config.get(self.IPTC_PRESET_ACTIVE_KEY, self.DEFAULT_IPTC_PRESET_NAME))
        if active_preset not in iptc_presets:
            active_preset = self.DEFAULT_IPTC_PRESET_NAME

        # Convert dict to IPTCPreset objects
        preset_objects = {}
        for name, data in iptc_presets.items():
            if isinstance(data, dict):
                preset_objects[name] = IPTCPreset.from_dict(data)

        dialog = IPTCPresetDialog(preset_objects, active_preset, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_name = dialog.get_selected_preset_name()
            updated_presets = dialog.get_presets()

            # Convert back to dict for storage
            iptc_presets = {name: preset.to_dict() for name, preset in updated_presets.items()}
            import_config[self.IPTC_PRESET_LIST_KEY] = iptc_presets
            import_config[self.IPTC_PRESET_ACTIVE_KEY] = selected_name

            # Update keywords in UI from selected preset
            selected_preset = updated_presets.get(selected_name)
            if selected_preset and self.iptc_keywords_input:
                self.iptc_keywords_input.setPlainText(selected_preset.data.get_keywords_text())

            self._save_import_config(import_config)
            self._update_iptc_preset_display()

    def _update_iptc_preset_display(self) -> None:
        """Update IPTC preset display"""
        if self.iptc_preset_label:
            import_config = self._get_import_config()
            preset_name = str(import_config.get(self.IPTC_PRESET_ACTIVE_KEY, self.DEFAULT_IPTC_PRESET_NAME))
            self.iptc_preset_label.setText(preset_name)

    # ===== Import Execution =====

    def _start_import(self) -> None:
        """Start import process"""
        if self.is_importing:
            return
        if self._import_mode == "add":
            self._add_selection_to_catalog()
            return

        if not self.selected_images:
            QMessageBox.information(self, "Import", "Please select at least one image to import.")
            return
        if self._bound_catalog is None:
            QMessageBox.warning(self, "Import", "Open a catalog before importing.")
            return

        import_config = self._get_import_config()
        destination_presets = import_config.get(self.DESTINATION_PRESET_LIST_KEY, {})
        active_destination = str(import_config.get(self.DESTINATION_PRESET_ACTIVE_KEY, self.DEFAULT_DESTINATION_PRESET_NAME))

        if active_destination not in destination_presets:
            QMessageBox.warning(self, "Import", "Please configure destination settings first.")
            return

        dest_settings = destination_presets[active_destination]
        target_root = str(dest_settings.get("target_root", "")).strip()

        if not target_root:
            QMessageBox.warning(self, "Import", "Please set a destination folder in the destination settings.")
            return

        target_path = Path(target_root)
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Import", f"Cannot create destination folder: {e}")
            return

        self.is_importing = True
        self.import_cancel_requested = False
        self.import_button.setEnabled(False)

        organize_mode = str(dest_settings.get("organize_mode", self.ORGANIZE_OPTIONS[0][0]))
        date_format = str(dest_settings.get("date_format", self.DATE_FORMAT_OPTIONS[0][0]))

        # Get IPTC data for import from UI
        ui_iptc_data = self._get_iptc_data_from_ui()
        removed_fields = self._iptc_removed_fields.copy()

        imported_sources: List[Path] = []

        try:
            total_count = len(self.selected_images)
            for sequence_number, source_path in enumerate(list(self.selected_images), start=1):
                if self.import_cancel_requested:
                    break

                target_file_path = self._build_import_target_path(
                    source_path, target_path, sequence_number,
                    organize_mode, date_format
                )
                target_file_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    self._place_original(source_path, target_file_path)
                    self._record_original(target_file_path)
                    self._write_target_xmp(source_path, target_file_path)

                    # Read existing IPTC data from source image
                    existing_iptc = read_iptc_from_image(source_path)
                    
                    # Merge IPTC data: existing + UI changes (with removal tracking)
                    merged_iptc = merge_iptc_data(
                        existing_iptc, 
                        ui_iptc_data, 
                        self._iptc_removed_keywords,
                        removed_fields
                    )
                    
                    # Apply merged IPTC metadata to imported image
                    if merged_iptc.creator or merged_iptc.copyright or merged_iptc.credit or merged_iptc.source or merged_iptc.keywords:
                        apply_iptc_to_image(target_file_path, merged_iptc)

                    # Copy markers (pick, rating, color) to imported image via XMP
                    self._copy_markers_to_target(source_path, target_file_path)

                    imported_sources.append(source_path)
                    self.import_status_label.setText(f"Imported {len(imported_sources)}/{total_count}: {target_file_path.name}")
                except Exception as e:
                    logger.error("Failed to import %s: %s", source_path, e)

                QApplication.processEvents()

            if self.import_cancel_requested:
                self.import_status_label.setText(f"Import cancelled after {len(imported_sources)} item(s).")
                QMessageBox.information(self, "Import", f"Import cancelled. {len(imported_sources)} images imported.")
            else:
                self.import_status_label.setText(f"Import complete: {len(imported_sources)} item(s) imported.")
                QMessageBox.information(self, "Import", f"Successfully imported {len(imported_sources)} image(s).")

        except Exception as e:
            logger.error("Import failed: %s", e)
            QMessageBox.critical(self, "Import", f"Import failed: {e}")
            self.import_status_label.setText("Import failed.")

        finally:
            self.is_importing = False
            self.import_cancel_requested = False
            self._sync_import_button()

    def _build_import_target_path(self, source_path: Path, target_root: Path, sequence_number: int,
                                  organize_mode: str, date_format: str) -> Path:
        """Build target path for import"""
        import_config = self._get_import_config()
        current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
        template = str(current_settings.get("template_pattern", "{filename}"))
        filename = source_path.stem

        # Resolve sequence token
        new_filename = self._resolve_sequence_token(template, sequence_number)
        new_filename = new_filename.replace("{filename}", filename)

        # Try to get capture time from EXIF
        capture_time = self._get_capture_time(source_path)
        if capture_time:
            new_filename = new_filename.replace("{capture_time}", capture_time.strftime(self.CAPTURE_TIME_FORMAT))
            new_filename = new_filename.replace("{date}", capture_time.strftime(date_format))
        else:
            now = datetime.now()
            new_filename = new_filename.replace("{capture_time}", now.strftime(self.CAPTURE_TIME_FORMAT))
            new_filename = new_filename.replace("{date}", now.strftime(date_format))

        # Determine folder structure
        if organize_mode == "by_date":
            if capture_time:
                date_folder = capture_time.strftime(date_format)
            else:
                date_folder = datetime.now().strftime(date_format)
            target_folder = target_root / date_folder
        else:
            target_folder = target_root

        return target_folder / (new_filename + source_path.suffix.lower())

    def _resolve_sequence_token(self, template_value: str, sequence_number: int) -> str:
        """Resolve sequence token in template"""
        def replace_sequence(match: re.Match[str]) -> str:
            digits_group = match.group(1)
            if digits_group is None:
                digit_count = self.DEFAULT_SEQUENCE_DIGITS
            else:
                try:
                    digit_count = max(1, min(9, int(digits_group)))
                except ValueError:
                    digit_count = self.DEFAULT_SEQUENCE_DIGITS
            return f"{sequence_number:0{digit_count}d}"

        return re.sub(r"\{sequence(?::(\d+))?\}", replace_sequence, template_value)

    def _get_capture_time(self, image_path: Path) -> Optional[datetime]:
        """Get capture time from EXIF"""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            with Image.open(image_path) as img:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == "DateTimeOriginal" or tag == "DateTime":
                            try:
                                return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                            except ValueError:
                                pass
        except Exception:
            pass
        return None

    def _write_target_xmp(self, source_path: Path, target_path: Path) -> None:
        """Write XMP sidecar for target"""
        try:
            source_xmp = source_path.with_suffix(".xmp")
            if source_xmp.exists():
                target_xmp = target_path.with_suffix(".xmp")
                shutil.copy2(source_xmp, target_xmp)
        except Exception:
            pass

    def _copy_markers_to_target(self, source_path: Path, target_path: Path) -> None:
        """Copy markers (pick, rating, color) from source to target XMP"""
        try:
            # Get markers from grid widget
            if not self.grid_widget:
                return

            marker_data = self.grid_widget.image_markers.get(source_path, {})
            if not marker_data:
                return

            # Build XMP content with markers
            xmp_content = self._build_xmp_with_markers(marker_data)
            if not xmp_content:
                return

            # Write to target XMP sidecar
            target_xmp = target_path.with_suffix(".xmp")
            if target_xmp.exists():
                # Read existing XMP and merge
                try:
                    with open(target_xmp, 'r', encoding='utf-8') as f:
                        existing_xmp = f.read()
                    merged_xmp = self._merge_xmp_markers(existing_xmp, marker_data)
                    with open(target_xmp, 'w', encoding='utf-8') as f:
                        f.write(merged_xmp)
                except Exception:
                    pass
            else:
                # Create new XMP sidecar
                with open(target_xmp, 'w', encoding='utf-8') as f:
                    f.write(xmp_content)

        except Exception as e:
            logger.error("Failed to copy markers for %s: %s", source_path, e)

    def _build_xmp_with_markers(self, marker_data: dict) -> str:
        """Build XMP XML content with marker data"""
        pick = marker_data.get("pick", "none")
        rating = marker_data.get("rating", "0")
        color = marker_data.get("color", "none")

        xmp_template = '''<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:darktable="http://darktable.sf.net/"
    darktable:pick="{pick}"
    darktable:rating="{rating}"
    darktable:color="{color}"/>
 </rdf:RDF>
</x:xmpmeta>'''

        return xmp_template.format(pick=pick, rating=rating, color=color)

    def _merge_xmp_markers(self, existing_xmp: str, marker_data: dict) -> str:
        """Merge markers into existing XMP content"""
        pick = marker_data.get("pick", "none")
        rating = marker_data.get("rating", "0")
        color = marker_data.get("color", "none")

        # Simple string replacement approach for now
        # In production, proper XML parsing would be better
        if 'darktable:pick=' in existing_xmp:
            existing_xmp = existing_xmp.replace(
                'darktable:pick="', f'darktable:pick="{pick}" darktable:oldpick="'
            )
        else:
            existing_xmp = existing_xmp.replace(
                '</rdf:Description>',
                f' darktable:pick="{pick}" darktable:rating="{rating}" darktable:color="{color}"/>'
            )

        return existing_xmp

    def _delete_imported_sources(self, imported_sources: List[Path]) -> None:
        """Delete source files after import"""
        deleted_count = 0
        for source_path in imported_sources:
            try:
                source_path.unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning("Failed to delete source %s: %s", source_path, e)
        self.import_status_label.setText(f"Deleted {deleted_count} source files.")

    def reject(self) -> None:
        """Handle dialog reject/cancel"""
        if self.is_importing:
            self.import_cancel_requested = True
            return

        if self.discovery_thread and self.discovery_thread.isRunning():
            self.discovery_thread.cancel()
            self.discovery_thread.wait(1000)
        super().reject()

    def resizeEvent(self, event) -> None:
        """Override resize to enforce minimum panel widths"""
        super().resizeEvent(event)
        
        # Enforce minimum widths on side panels
        if hasattr(self, '_left_panel') and self._left_panel:
            if self._left_panel.width() < 250:
                self._left_panel.setMinimumWidth(250)
        
        if hasattr(self, '_right_panel') and self._right_panel:
            if self._right_panel.width() < 350:
                self._right_panel.setMinimumWidth(350)
