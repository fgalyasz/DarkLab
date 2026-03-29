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
    QApplication, QListView, QSpinBox
)

from src.config.config_manager import ConfigManager
from src.ui.widgets.grid_image_widget import GridImageWidget
from src.ui.dialogs import RenamePatternDialog, DestinationSettingsDialog

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

    def run(self):
        """Discover image files in background thread"""
        try:
            folder_path = Path(self.folder_path)
            self.image_files = []

            if self.recursive:
                image_files = self._find_images_recursive(folder_path)
            else:
                image_files = self._find_images_non_recursive(folder_path)
            image_files = sorted(image_files, key=lambda p: (p.stem.lower(), p.suffix.lower(), p.name.lower()))

            self.image_files = [str(path) for path in image_files]

            if not self._is_cancelled:
                self.discovery_finished.emit(self.image_files)

        except Exception as e:
            logger.error("Error in image discovery thread: %s", e)

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
        self._updating_import_ui = False
        self.import_status_label: Optional[QLabel] = None
        self.import_button: Optional[QPushButton] = None
        self.import_cancel_button: Optional[QPushButton] = None
        self.is_importing = False
        self.import_cancel_requested = False

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
        """Setup the full dialog UI matching LibraryPanel layout"""
        self.setStyleSheet("""
            QDialog {
                background-color: rgb(35, 35, 40);
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: rgb(68, 68, 74);
                color: white;
                border: 1px solid rgb(90, 90, 96);
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgb(78, 78, 84);
                border-color: rgb(0, 122, 255);
            }
            QPushButton:pressed {
                background-color: rgb(88, 88, 94);
            }
            QPushButton:disabled {
                background-color: rgb(55, 55, 60);
                color: rgb(160, 160, 165);
            }
            QLineEdit {
                background-color: rgb(48, 48, 54);
                color: white;
                border: 1px solid rgb(70, 70, 76);
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus {
                border-color: rgb(0, 122, 255);
            }
            QComboBox {
                background-color: rgb(48, 48, 54);
                color: white;
                border: 1px solid rgb(70, 70, 76);
                border-radius: 4px;
                padding: 6px;
            }
            QComboBox:focus {
                border-color: rgb(0, 122, 255);
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: rgb(48, 48, 54);
                color: white;
                border: 1px solid rgb(70, 70, 76);
                selection-background-color: rgb(0, 122, 255);
            }
            QCheckBox {
                color: white;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid rgb(90, 90, 96);
                border-radius: 3px;
                background-color: rgb(48, 48, 54);
            }
            QCheckBox::indicator:checked {
                background-color: rgb(0, 122, 255);
                border-color: rgb(0, 122, 255);
            }
            QGroupBox {
                color: white;
                border: 1px solid rgb(70, 70, 76);
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QTreeWidget {
                background-color: rgb(35, 35, 40);
                color: white;
                border: 1px solid rgb(60, 60, 65);
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: rgb(0, 122, 255);
            }
            QSlider::groove:horizontal {
                border: 1px solid rgb(70, 70, 76);
                height: 8px;
                background: rgb(48, 48, 54);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: rgb(0, 122, 255);
                border: none;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QSpinBox {
                background-color: rgb(48, 48, 54);
                color: white;
                border: 1px solid rgb(70, 70, 76);
                border-radius: 4px;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid rgb(60, 60, 65);
                border-radius: 3px;
                text-align: center;
                color: white;
                background-color: rgb(40, 40, 45);
            }
            QProgressBar::chunk {
                background-color: rgb(0, 122, 255);
                border-radius: 2px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create splitter for 3-column layout
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter = main_splitter

        # Note: Not connecting splitterMoved to avoid any automatic resize behavior
        # main_splitter.splitterMoved.connect(self._on_splitter_moved)

        # Setup resize timer for manual resize only
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._apply_grid_layout)

        # Left column - Folder tree
        self._setup_folder_tree(main_splitter)

        # Middle column - Image grid with filters
        self._setup_image_grid(main_splitter)

        # Right column - Import settings
        self._setup_import_settings(main_splitter)

        # Set fixed widths on splitter widgets - no resizing allowed
        left_panel = main_splitter.widget(0)
        right_panel = main_splitter.widget(2)
        if left_panel:
            left_panel.setFixedWidth(280)  # Fixed width - cannot resize
        if right_panel:
            right_panel.setFixedWidth(380)  # Fixed width - cannot resize

        # Disable splitter resizing completely
        main_splitter.setHandleWidth(0)  # Hide splitter handles
        main_splitter.setOpaqueResize(False)  # Disable opaque resize
        
        main_layout.addWidget(main_splitter)

        # Bottom button bar
        button_layout = QHBoxLayout()
        self.import_status_label = QLabel("Select a folder to import from")
        self.import_status_label.setStyleSheet("color: rgb(180, 180, 180);")
        button_layout.addWidget(self.import_status_label)

        button_layout.addStretch()

        self.import_button = QPushButton("Import Selected")
        self.import_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(0, 122, 255);
                color: white;
                font-weight: bold;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background-color: rgb(20, 142, 255);
            }
            QPushButton:disabled {
                background-color: rgb(55, 55, 60);
                color: rgb(160, 160, 165);
            }
        """)
        self.import_button.clicked.connect(self._start_import)
        button_layout.addWidget(self.import_button)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        main_layout.addLayout(button_layout)

        # Setup keyboard shortcuts for selection
        self._setup_selection_shortcuts()

    def _setup_selection_shortcuts(self) -> None:
        """Setup keyboard shortcuts for selection"""
        # Select All: Ctrl+A (works on both macOS and Windows/Linux)
        select_all_shortcut = QShortcut(QKeySequence.StandardKey.SelectAll, self)
        select_all_shortcut.activated.connect(self._select_all_images)

        # Deselect All: Ctrl+D / Cmd+D
        deselect_all_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        deselect_all_shortcut.activated.connect(self._clear_selected_images)

        # macOS specific: Cmd+D
        if platform.system() == "Darwin":
            deselect_mac = QShortcut(QKeySequence("Meta+D"), self)
            deselect_mac.activated.connect(self._clear_selected_images)

    def _setup_folder_tree(self, parent: QSplitter) -> None:
        """Setup folder tree widget (left column)"""
        left_widget = QWidget()
        left_widget.setFixedWidth(280)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 12, 0)  # 12px right margin
        left_layout.setSpacing(8)

        # Title
        title = QLabel("Source Folders")
        title.setStyleSheet("font-weight: bold; color: white; padding: 5px; font-size: 14px;")
        left_layout.addWidget(title)

        # Recursive loading checkbox
        self.recursive_checkbox = QCheckBox("Load subfolders recursively")
        self.recursive_checkbox.setChecked(True)  # Default to recursive loading
        self.recursive_checkbox.toggled.connect(self._on_recursive_toggled)
        left_layout.addWidget(self.recursive_checkbox)

        # Folder tree
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.setRootIsDecorated(True)
        self.folder_tree.itemClicked.connect(self._on_folder_selected)
        self.folder_tree.itemExpanded.connect(self._on_folder_expanded)
        left_layout.addWidget(self.folder_tree)

        parent.addWidget(left_widget)

        # Load folder structure
        self._load_folder_structure()

    def _setup_image_grid(self, parent: QSplitter) -> None:
        """Setup image grid with filters (middle column)"""
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(12, 0, 12, 0)  # 12px left and right margins
        middle_layout.setSpacing(10)

        # Title
        title = QLabel("Select Images to Import")
        title.setStyleSheet("font-weight: bold; color: white; padding: 5px; font-size: 14px;")
        middle_layout.addWidget(title)

        # Filter controls row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)

        # Grid columns control
        columns_label = QLabel("Columns:")
        columns_label.setStyleSheet("color: white;")
        controls_layout.addWidget(columns_label)

        self.columns_slider = QSlider(Qt.Orientation.Horizontal)
        self.columns_slider.setRange(self.MIN_GRID_COLUMNS, self.MAX_GRID_COLUMNS)
        self.columns_slider.setValue(self.grid_columns)
        self.columns_slider.setFixedWidth(120)
        self.columns_slider.valueChanged.connect(self._on_columns_changed)
        controls_layout.addWidget(self.columns_slider)

        self.columns_value_label = QLabel(str(self.grid_columns))
        self.columns_value_label.setStyleSheet("color: rgb(180, 180, 180);")
        self.columns_value_label.setMinimumWidth(20)
        controls_layout.addWidget(self.columns_value_label)

        controls_layout.addSpacing(20)

        # Filter combos
        self.pick_filter_combo = self._create_marker_combo(self.PICK_OPTIONS)
        self.pick_filter_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.pick_filter_combo.currentIndexChanged.connect(self._on_media_filter_changed)
        pick_label = QLabel("Pick:")
        pick_label.setStyleSheet("color: white;")
        controls_layout.addWidget(pick_label)
        controls_layout.addWidget(self.pick_filter_combo, 1)

        controls_layout.addSpacing(8)

        self.rating_filter_combo = self._create_marker_combo(self.RATING_OPTIONS)
        self.rating_filter_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.rating_filter_combo.currentIndexChanged.connect(self._on_media_filter_changed)
        stars_label = QLabel("Stars:")
        stars_label.setStyleSheet("color: white;")
        controls_layout.addWidget(stars_label)
        controls_layout.addWidget(self.rating_filter_combo, 1)

        controls_layout.addSpacing(8)

        self.color_filter_combo = self._create_marker_combo(self.COLOR_OPTIONS)
        self.color_filter_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.color_filter_combo.currentIndexChanged.connect(self._on_media_filter_changed)
        color_label = QLabel("Color:")
        color_label.setStyleSheet("color: white;")
        controls_layout.addWidget(color_label)
        controls_layout.addWidget(self.color_filter_combo, 1)

        controls_layout.addSpacing(8)

        days_label = QLabel("Days:")
        days_label.setStyleSheet("color: white;")
        controls_layout.addWidget(days_label)
        self.days_back_spin = QSpinBox()
        self.days_back_spin.setRange(self.FILTER_DAYS_MIN, self.FILTER_DAYS_MAX)
        self.days_back_spin.setValue(self.FILTER_DAYS_DEFAULT)
        self.days_back_spin.setFixedWidth(80)
        self.days_back_spin.valueChanged.connect(self._on_media_filter_changed)
        controls_layout.addWidget(self.days_back_spin)

        controls_layout.addSpacing(8)

        self.sort_combo = self._create_marker_combo(self.SORT_OPTIONS)
        self.sort_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.sort_combo.currentIndexChanged.connect(self._on_media_filter_changed)
        sort_label = QLabel("Sort:")
        sort_label.setStyleSheet("color: white;")
        controls_layout.addWidget(sort_label)
        controls_layout.addWidget(self.sort_combo, 1)

        controls_layout.addStretch()

        # Progress bar and cancel button
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(150)
        controls_layout.addWidget(self.progress_bar)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(220, 50, 50);
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(240, 70, 70);
            }
        """)
        self.cancel_button.clicked.connect(self._cancel_loading)
        controls_layout.addWidget(self.cancel_button)

        middle_layout.addLayout(controls_layout)

        # QScrollArea with GridImageWidget
        self.scroll_area = QScrollArea()
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)  # Allow widget to resize to fit
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.grid_widget = GridImageWidget()
        self.grid_widget.selection_changed.connect(self._on_grid_selection_changed)
        self.grid_widget.marker_changed.connect(self._on_marker_changed)
        self.scroll_area.setWidget(self.grid_widget)

        middle_layout.addWidget(self.scroll_area)

        parent.addWidget(middle_widget)

    def _setup_import_settings(self, parent: QSplitter) -> None:
        """Setup import settings panel (right column)"""
        right_widget = QWidget()
        right_widget.setFixedWidth(380)
        right_widget.setStyleSheet("background-color: rgb(35, 35, 40);")  # Match other panels
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(12, 0, 0, 0)  # 12px left margin
        right_layout.setSpacing(10)

        # Title
        title = QLabel("Import Settings")
        title.setStyleSheet("font-weight: bold; color: white; padding: 5px; font-size: 14px;")
        right_layout.addWidget(title)

        # Scroll area for settings - no scrollbars needed with fixed width
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # No horizontal scrollbar
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        settings_layout.setSpacing(8)

        self._render_import_sections(settings_layout)

        scroll_area.setWidget(settings_widget)
        right_layout.addWidget(scroll_area)

        parent.addWidget(right_widget)

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
            self.import_status_label.setText(f"Loaded {len(self.discovered_image_files)} images")

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
        self.import_status_label.setText(f"Selected {len(self.selected_images)} of {len(self.image_files)} images")

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
        self._add_import_group("import_preset", "Import Preset", self._create_import_preset_widget(), parent_layout)
        self._add_import_group("file_handling", "File Handling", self._create_file_handling_widget(), parent_layout)
        self._add_import_group("file_renaming", "File Renaming", self._create_file_renaming_widget(), parent_layout)
        self._add_import_group("destination", "Destination", self._create_destination_widget(), parent_layout)
        parent_layout.addStretch()

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
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        layout.addWidget(self.preset_combo)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)
        create_button = self._create_small_button("Create", self._create_import_preset)
        save_button = self._create_small_button("Save", self._save_selected_preset)
        rename_button = self._create_small_button("Rename", self._rename_import_preset)
        delete_button = self._create_small_button("Delete", self._delete_import_preset)
        button_layout.addWidget(create_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(rename_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)

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

        skip_duplicates = QCheckBox("Skip possible duplicates")
        skip_rejected = QCheckBox("Skip rejected images")
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

        layout.addWidget(QLabel("Preset:"))
        self.destination_preset_label = QLabel("Default")
        self.destination_preset_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.destination_preset_label)
        layout.addStretch()

        edit_button = self._create_small_button("Configure...", self._open_destination_dialog)
        layout.addWidget(edit_button)

        return widget

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

    # ===== Import Execution =====

    def _start_import(self) -> None:
        """Start import process"""
        if self.is_importing:
            return

        if not self.selected_images:
            QMessageBox.information(self, "Import", "Please select at least one image to import.")
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
        delete_after_import = bool(dest_settings.get("delete_after_import", False))

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
                    shutil.copy2(source_path, target_file_path)
                    self._write_target_xmp(source_path, target_file_path)
                    imported_sources.append(source_path)
                    self.import_status_label.setText(f"Imported {len(imported_sources)}/{total_count}: {target_file_path.name}")
                except Exception as e:
                    logger.error("Failed to import %s: %s", source_path, e)

                QApplication.processEvents()

            if self.import_cancel_requested:
                self.import_status_label.setText(f"Import cancelled after {len(imported_sources)} item(s).")
                QMessageBox.information(self, "Import", f"Import cancelled. {len(imported_sources)} images imported.")
            else:
                if delete_after_import:
                    self._delete_imported_sources(imported_sources)
                self.import_status_label.setText(f"Import complete: {len(imported_sources)} item(s) imported.")
                QMessageBox.information(self, "Import", f"Successfully imported {len(imported_sources)} image(s).")

        except Exception as e:
            logger.error("Import failed: %s", e)
            QMessageBox.critical(self, "Import", f"Import failed: {e}")
            self.import_status_label.setText("Import failed.")

        finally:
            self.is_importing = False
            self.import_cancel_requested = False
            self.import_button.setEnabled(True)

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
