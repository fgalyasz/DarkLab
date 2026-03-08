"""Library Panel for Photo Editor.

Handles photo library management with folder tree and metadata.
Includes threaded image loading with cancellation and detailed logging.
"""

import logging
import os
import platform
import re
import shutil
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from hashlib import sha1
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import time
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QListView, QScrollArea, QWidget, QFrame,
    QSplitter, QLineEdit, QSpinBox, QFormLayout, QGroupBox, QCheckBox,
    QGridLayout, QTextEdit, QSizePolicy, QPushButton, QProgressBar,
    QAbstractItemView, QSlider, QComboBox, QFileDialog, QMessageBox,
    QInputDialog, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDir, QFileSystemWatcher, QSize, QTimer, QThread, pyqtSignal, QThreadPool, QRunnable, QObject, QEvent
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QIcon, QImage, QImageReader, QKeySequence, QShortcut

from src.config.config_manager import ConfigManager
from src.ui.widgets.grid_image_widget import GridImageWidget
from .base_panel import BasePanel


logger = logging.getLogger(__name__)

# Ensure file-based logging for this module in addition to any global handlers
_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, "library_panel.log")

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


class ImageProcessorRunnable(QRunnable):
    """Runnable for processing a batch of images"""
    
    def __init__(self, image_paths: List[str], batch_id: int, target_size: int):
        super().__init__()
        self.image_paths = image_paths
        self.batch_id = batch_id
        self.target_size = max(32, int(target_size))
        self.signals = ImageProcessorSignals()
    
    def run(self):
        """Process a batch of images: load files into QImage in worker thread"""
        try:
            logger.debug("[LIB][RUN] Batch %s started with %s images", self.batch_id, len(self.image_paths))
            for index, image_path in enumerate(self.image_paths):
                if self.signals.cancelled:
                    logger.debug("[LIB][RUN] Batch %s cancelled before image %s", self.batch_id, index)
                    break

                reader = QImageReader(str(image_path))
                reader.setAutoTransform(True)
                original_size = reader.size()
                if original_size.isValid() and original_size.width() > 0 and original_size.height() > 0:
                    max_side = max(original_size.width(), original_size.height())
                    scale = self.target_size / max_side
                    scaled_size = QSize(
                        max(1, int(original_size.width() * scale)),
                        max(1, int(original_size.height() * scale)),
                    )
                    reader.setScaledSize(scaled_size)
                else:
                    reader.setScaledSize(QSize(self.target_size, self.target_size))
                image = reader.read()
                if image.isNull():
                    logger.debug("[LIB][RUN] Failed to load thumbnail: %s (%s)", image_path, reader.errorString())
                    image = QImage()

                self.signals.image_found.emit(image_path, Path(image_path).name, image)

                if self.signals.cancelled:
                    break

                if index % 3 == 0:
                    time.sleep(0.0001)
                    if self.signals.cancelled:
                        break

            logger.debug("[LIB][RUN] Batch %s finished loop", self.batch_id)
            self.signals.batch_finished.emit(self.batch_id)
        except Exception as error:
            logger.error("[LIB][RUN] Error in batch %s: %s", self.batch_id, error)
            self.signals.batch_finished.emit(self.batch_id)


class ImageProcessorSignals(QObject):
    """Signals for image processing"""
    image_found = pyqtSignal(str, str, QImage)
    batch_finished = pyqtSignal(int)
    # Simple cooperative cancellation flag, read/write from worker
    cancelled: bool = False


class ImageDiscoveryThread(QThread):
    """Thread for discovering image files (not loading them)"""
    
    # Signals
    discovery_finished = pyqtSignal(list)  # List of image paths
    progress_updated = pyqtSignal(int, int)  # current, total
    
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
            print(f"Discovering images from: {folder_path}")  # Debug
            
            # Find all image files
            if self.recursive:
                image_files = self._find_images_recursive(folder_path)
            else:
                image_files = self._find_images_non_recursive(folder_path)
            
            print(f"Discovered {len(image_files)} image files")  # Debug
            self.image_files = [str(path) for path in image_files]
            
            if not self._is_cancelled:
                self.discovery_finished.emit(self.image_files)
                
        except Exception as e:
            print(f"Error in image discovery thread: {e}")
    
    def cancel(self):
        """Cancel the discovery process"""
        self._is_cancelled = True
    
    def _find_images_recursive(self, folder_path: Path, max_depth: int = 3, current_depth: int = 0) -> List[Path]:
        """Find image files recursively"""
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
        """Find image files in current folder only"""
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
        """Check if file is an image"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        return file_path.suffix.lower() in image_extensions


class CollapsibleGroupBox(QWidget):
    """Custom collapsible group box for metadata sections"""
    
    def __init__(self, title: str, parent=None):
        logger.debug("[LIB][META] Creating CollapsibleGroupBox with title: %s", title)
        try:
            super().__init__(parent)
            self.is_collapsed = False
            
            # Calculate colors
            panel_color = (35, 35, 40)
            lighter_color = tuple(min(255, int(c + (255 - c) * 0.25)) for c in panel_color)
            lighter_color_str = f"rgb({lighter_color[0]}, {lighter_color[1]}, {lighter_color[2]})"
            
            # Field background (15% lighter than group background)
            field_lighter = tuple(min(255, int(c + (255 - c) * 0.15)) for c in lighter_color)
            field_lighter_str = f"rgb({field_lighter[0]}, {field_lighter[1]}, {field_lighter[2]})"
            
            self.field_background = field_lighter_str
            
            # Main layout
            self.main_layout = QVBoxLayout(self)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.setSpacing(0)
            
            # Header with title and toggle button
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(10, 5, 10, 5)
            
            # Title label
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    background-color: {lighter_color_str};
                    padding: 5px;
                    border: none;
                }}
            """)
            
            # Toggle button
            self.toggle_button = QPushButton("▼")
            self.toggle_button.setFixedSize(20, 20)
            self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.toggle_button.setStyleSheet(f"""
                QPushButton {{
                    color: white;
                    background-color: {lighter_color_str};
                    border: 1px solid rgb(60, 60, 65);
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: rgb(70, 70, 75);
                    border-color: rgb(80, 80, 85);
                }}
                QPushButton:pressed {{
                    background-color: rgb(80, 80, 85);
                    border-color: rgb(90, 90, 95);
                }}
            """)
            
            # Use mousePressEvent instead of clicked signal
            self.toggle_button.mousePressEvent = lambda e: self.toggle()
            
            header_layout.addWidget(self.title_label)
            header_layout.addStretch()
            header_layout.addWidget(self.toggle_button)
            
            # Content widget
            self.content_widget = QWidget()
            self.content_layout = QFormLayout(self.content_widget)
            self.content_layout.setContentsMargins(10, 5, 10, 10)
            self.content_layout.setSpacing(5)
            
            # Style the content area
            self.content_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {lighter_color_str};
                    border: 1px solid rgb(60, 60, 65);
                    border-radius: 5px;
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                    margin-top: -1px;
                }}
            """)
            
            # Add to main layout
            self.main_layout.addLayout(header_layout)
            self.main_layout.addWidget(self.content_widget)
            
            logger.debug("[LIB][META] CollapsibleGroupBox created successfully: %s", title)
        except Exception as e:
            logger.error("[LIB][META] Error creating CollapsibleGroupBox: %s", e)
    
    def toggle(self):
        """Toggle collapsed state"""
        logger.debug("[LIB][META] Toggle called, current state: %s", self.is_collapsed)
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.content_widget.hide()
            self.toggle_button.setText("▶")
            self.setFixedHeight(30)  # Only header height
            logger.debug("[LIB][META] Collapsed")
        else:
            self.content_widget.show()
            self.toggle_button.setText("▼")
            self.setMaximumHeight(16777215)  # Remove height limit
            # Update size after showing content
            self.updateGeometry()
            logger.debug("[LIB][META] Expanded")
    
    def add_row(self, label_text: str, widget: QWidget):
        """Add a row to the content layout"""
        label = QLabel(label_text)
        label.setStyleSheet(f"""
            QLabel {{
                color: rgb(180, 180, 180);
                font-size: 10px;
                background-color: transparent;
                border: none;
            }}
        """)
        
        # Style the input widget
        if isinstance(widget, QLineEdit):
            widget.setStyleSheet(f"""
                QLineEdit {{
                    color: white;
                    background-color: {self.field_background};
                    border: 1px solid rgb(60, 60, 65);
                    border-radius: 3px;
                    padding: 3px;
                    font-size: 12px;
                }}
            """)
        elif isinstance(widget, QTextEdit):
            widget.setStyleSheet(f"""
                QTextEdit {{
                    color: white;
                    background-color: {self.field_background};
                    border: 1px solid rgb(60, 60, 65);
                    border-radius: 3px;
                    padding: 3px;
                    font-size: 12px;
                }}
            """)
        
        self.content_layout.addRow(label, widget)


class LibraryPanel(BasePanel):
    """Library panel for managing photo library"""

    DEFAULT_GRID_COLUMNS = 5
    MIN_GRID_COLUMNS = 1
    MAX_GRID_COLUMNS = 10
    DEFAULT_IMPORT_PRESET_NAME = "Default"
    PRESET_NAME_SUFFIX_SEPARATOR = " ("
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
    LEGACY_RENAME_TEMPLATE_MAP = {
        "{date}_{filename}": "{filename}",
        "{filename}_{sequence}": "CustomName_{sequence}",
        "{date}_{sequence}": "{capture_time}",
    }
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
    IMPORT_PRESET_CONFIG_KEY = "panels.library.import_settings"
    IMPORT_PRESET_LIST_KEY = "presets"
    IMPORT_PRESET_ACTIVE_KEY = "active_preset"
    IMPORT_SETTINGS_KEY = "current"
    IMPORT_PANEL_STATE_KEY = "panel_states"
    RENAME_TEMPLATE_LIST_KEY = "rename_templates"
    REJECTED_RATING_VALUE = "-1"
    SAMPLE_FILENAME = "IMG_0001"
    SAMPLE_SEQUENCE = "001"
    DEFAULT_SEQUENCE_DIGITS = 3
    SAMPLE_CAPTURE_TIME = datetime(2026, 3, 8, 12, 34, 56)
    CAPTURE_TIME_FORMAT = "%y%m%d_%H%M%S"
    FILE_METADATA_FIELDS = (
        "Filename",
        "Path",
        "Size",
        "Modified",
    )
    EXIF_METADATA_FIELDS = (
        "Camera",
        "Lens",
        "ISO",
        "Aperture",
        "Shutter Speed",
        "Focal Length",
        "Flash",
        "White Balance",
        "Date Taken",
    )
    IPTC_METADATA_FIELDS = (
        "Title",
        "Description",
        "Keywords",
        "Creator",
        "Credit",
        "Source",
        "Copyright",
        "City",
        "State",
        "Country",
        "Rating",
    )
    GRID_SPACING = 8
    GRID_MIN_SPACING = 4
    GRID_MAX_SPACING_DELTA = 18
    GRID_LEFT_PADDING = 4
    GRID_RIGHT_PADDING = 4
    GRID_MIN_CELL_SIZE = 120
    GRID_CARD_MARGIN = 6
    GRID_FILENAME_HEIGHT = 24
    GRID_IMAGE_INNER_PADDING = 10
    GRID_LAYOUT_UPDATE_DELAY_MS = 60
    EXIF_WRITABLE_SUFFIXES = (".jpg", ".jpeg", ".tif", ".tiff", ".webp")
    PNG_WRITABLE_SUFFIXES = (".png",)
    RAW_WRITABLE_SUFFIXES = (".cr2", ".cr3", ".nef", ".arw", ".raf", ".orf", ".rw2", ".dng")
    EXIF_TAG_IDS = {
        "ImageDescription": 270,
        "Artist": 315,
        "Copyright": 33432,
        "XPTitle": 40091,
        "XPComment": 40092,
        "XPAuthor": 40093,
        "XPKeywords": 40094,
        "XPSubject": 40095,
    }
    FIELD_TO_EXIF_TAG = {
        "Title": "XPTitle",
        "Description": "XPComment",
        "Keywords": "XPKeywords",
        "Creator": "XPAuthor",
        "Credit": "XPSubject",
        "Source": "XPSubject",
        "Copyright": "Copyright",
    }
    FIELD_TO_PNG_KEY = {
        "Title": "Title",
        "Description": "Description",
        "Keywords": "Keywords",
        "Creator": "Author",
        "Credit": "Credit",
        "Source": "Source",
        "Copyright": "Copyright",
        "City": "City",
        "State": "State",
        "Country": "Country",
        "Rating": "Rating",
    }
    FIELD_TO_XMP_PROP = {
        "Title": "dc:title",
        "Description": "dc:description",
        "Keywords": "dc:subject",
        "Creator": "dc:creator",
        "Copyright": "dc:rights",
        "Rating": "xmp:Rating",
        "Source": "photoshop:Source",
        "City": "photoshop:City",
        "State": "photoshop:State",
        "Country": "photoshop:Country",
    }
    XMP_NAMESPACES = {
        "x": "adobe:ns:meta/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "xmp": "http://ns.adobe.com/xap/1.0/",
        "photoshop": "http://ns.adobe.com/photoshop/1.0/",
    }

    def __init__(self):
        super().__init__("library")
        self.current_folder: Optional[Path] = None
        self.image_files: List[Path] = []
        self.selected_image: Optional[Path] = None
        self.selected_images: List[Path] = []
        self.grid_columns = self.DEFAULT_GRID_COLUMNS
        self.recursive_loading = False
        self.config_manager = ConfigManager()
        self.grid_widget: Optional[GridImageWidget] = None
        self.scroll_area: Optional[QScrollArea] = None
        self.current_icon_size = self.GRID_MIN_CELL_SIZE
        self.metadata_overrides: dict[Path, dict[str, str]] = {}
        self.metadata_widgets = {}  # Store metadata edit widgets
        self.import_panel_widgets: dict[str, QWidget] = {}
        self.import_section_count = 0
        self.preset_combo: Optional[QComboBox] = None
        self.preset_feedback_label: Optional[QLabel] = None
        self.rename_sample_label: Optional[QLabel] = None
        self.rename_feedback_label: Optional[QLabel] = None
        self.rename_tokens_widget: Optional[QWidget] = None
        self._updating_import_ui = False
        self.import_status_label: Optional[QLabel] = None
        self.import_button: Optional[QPushButton] = None
        self.import_cancel_button: Optional[QPushButton] = None
        self.is_importing = False
        self.import_cancel_requested = False
        self.volume_root_path = Path("/Volumes")
        self.volume_watcher: Optional[QFileSystemWatcher] = None
        self.volume_refresh_timer: Optional[QTimer] = None

        # Setup resize timer for dynamic cell sizing
        self.resize_timer = QTimer(self)
        self.resize_timer.timeout.connect(self._apply_grid_layout)
        self.resize_timer.setSingleShot(True)
        
        logger.debug("[LIB][INIT] LibraryPanel created id=%s", id(self))

        # Threading variables
        self.discovery_thread = None
        self.thread_pool = QThreadPool()
        # Limit parallel decodes to avoid massive RAM spikes.
        self.thread_pool.setMaxThreadCount(4)
        self.is_loading = False
        self.active_processors = []  # Track active processors
        self.total_images = 0
        self.processed_images = 0
        
        # Override the default setup
        self._setup_library_ui()
        self._setup_volume_monitoring()
        
        # Setup UI update timer for continuous image display
        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.timeout.connect(self._continuous_ui_update)
        self.ui_update_timer.setSingleShot(True)
        self._setup_selection_shortcuts()

    def _setup_selection_shortcuts(self) -> None:
        self.select_all_shortcut = QShortcut(QKeySequence.StandardKey.SelectAll, self)
        self.select_all_shortcut.activated.connect(self._select_all_images)
        self.deselect_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.deselect_shortcut.activated.connect(self._clear_selected_images)
        self.meta_deselect_shortcut = QShortcut(QKeySequence("Meta+D"), self)
        self.meta_deselect_shortcut.activated.connect(self._clear_selected_images)

    def _select_all_images(self) -> None:
        if self.grid_widget is None:
            return
        self.grid_widget.select_all_images()

    def _clear_selected_images(self) -> None:
        if self.grid_widget is None:
            return
        self.grid_widget.clear_selection()
    
    def _setup_library_ui(self) -> None:
        """Setup the 3-column layout"""
        # Clear default content including title
        if hasattr(self, 'title_label') and self.title_label:
            self.main_layout.removeWidget(self.title_label)
            self.title_label.deleteLater()
        
        self.clear_content()
        
        # Create splitter for resizable columns
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_layout.addWidget(main_splitter)
        
        # Left column - Folder tree
        self._setup_folder_tree(main_splitter)
        
        # Middle column - Image grid
        self._setup_image_grid(main_splitter)
        
        # Right column - Metadata
        logger.debug("About to setup metadata panel...")
        self._setup_metadata_panel(main_splitter)
        logger.debug("Metadata panel setup completed.")
        
        # Set initial splitter sizes (20%, 60%, 20%)
        main_splitter.setSizes([200, 600, 200])
        
        # Connect splitter change event and keep a reference for eventFilter checks
        self.main_splitter = main_splitter
        main_splitter.splitterMoved.connect(self._on_splitter_moved)
    
    def _setup_folder_tree(self, parent: QSplitter) -> None:
        """Setup folder tree widget"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Title
        title = QLabel("Folders")
        title.setStyleSheet("font-weight: bold; color: white; padding: 5px;")
        left_layout.addWidget(title)
        
        # Recursive loading checkbox
        self.recursive_checkbox = QCheckBox("Load subfolders recursively")
        self.recursive_checkbox.setStyleSheet("color: white;")
        self.recursive_checkbox.setChecked(False)
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

    def _get_expanded_top_level_paths(self) -> set[str]:
        """Collect expanded top-level paths."""
        expanded_paths: set[str] = set()
        for index in range(self.folder_tree.topLevelItemCount()):
            item = self.folder_tree.topLevelItem(index)
            if item.isExpanded():
                expanded_paths.add(item.data(0, Qt.ItemDataRole.UserRole))
        return expanded_paths

    def _restore_top_level_state(self, selected_path: Optional[str], expanded_paths: set[str]) -> None:
        """Restore selection and expanded state after refresh."""
        for index in range(self.folder_tree.topLevelItemCount()):
            item = self.folder_tree.topLevelItem(index)
            item_path = item.data(0, Qt.ItemDataRole.UserRole)
            if item_path in expanded_paths:
                item.setExpanded(True)
            if item_path == selected_path:
                self.folder_tree.setCurrentItem(item)

    def _get_root_directories(self) -> List[Path]:
        """Build the folder tree root directories."""
        home = Path.home()
        root_directories = [home]
        common_directories = [home / "Pictures", home / "Desktop", home / "Documents"]
        for directory_path in common_directories:
            if directory_path.exists() and directory_path != home:
                root_directories.append(directory_path)
        root_directories.extend(self._get_mounted_volume_directories(home))
        return root_directories

    def _get_mounted_volume_directories(self, home: Path) -> List[Path]:
        """Get mounted external volume directories."""
        if platform.system() != "Darwin":
            return []
        if not self.volume_root_path.exists():
            return []
        volume_directories: List[Path] = []
        for volume_path in sorted(self.volume_root_path.iterdir()):
            if not volume_path.is_dir() or volume_path == home:
                continue
            volume_directories.append(volume_path)
        return volume_directories

    def _setup_image_grid(self, parent: QSplitter) -> None:
        """Setup image grid widget"""
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Grid columns control
        columns_label = QLabel("Columns:")
        columns_label.setStyleSheet("color: white;")
        controls_layout.addWidget(columns_label)
        
        self.columns_slider = QSlider(Qt.Orientation.Horizontal)
        self.columns_slider.setRange(self.MIN_GRID_COLUMNS, self.MAX_GRID_COLUMNS)
        self.columns_slider.setValue(self.grid_columns)
        self.columns_slider.setFixedWidth(140)
        self.columns_slider.valueChanged.connect(self._on_columns_changed)
        controls_layout.addWidget(self.columns_slider)

        self.columns_value_label = QLabel(str(self.grid_columns))
        self.columns_value_label.setStyleSheet("color: rgb(180, 180, 180);")
        self.columns_value_label.setMinimumWidth(22)
        controls_layout.addWidget(self.columns_value_label)
        
        controls_layout.addStretch()
        
        # Progress bar and cancel button
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: rgb(200, 30, 30);
            }
        """)
        self.cancel_button.clicked.connect(self._cancel_loading)
        # Extra debug to see if button gets pressed events
        self.cancel_button.pressed.connect(
            lambda: logger.debug(
                "[LIB][UI] Cancel button PRESSED (panel_id=%s, button_id=%s)",
                id(self), id(self.cancel_button)
            )
        )
        logger.debug("[LIB][UI] Cancel button created on panel id=%s, button id=%s", id(self), id(self.cancel_button))
        controls_layout.addWidget(self.cancel_button)
        middle_layout.addLayout(controls_layout)
        
        # QScrollArea with custom GridImageWidget
        self.scroll_area = QScrollArea()
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: rgb(35, 35, 40);
                border: none;
            }
        """)
        
        self.grid_widget = GridImageWidget()
        self.grid_widget.selection_changed.connect(self._on_grid_selection_changed)
        self.scroll_area.setWidget(self.grid_widget)
        self.scroll_area.installEventFilter(self)
        
        middle_layout.addWidget(self.scroll_area)
        self._queue_grid_layout_update()

        parent.addWidget(middle_widget)
    
    def _setup_metadata_panel(self, parent: QSplitter) -> None:
        """Setup metadata panel"""
        logger.debug("Setting up metadata panel...")
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Title
        title = QLabel("Import")
        title.setStyleSheet("font-weight: bold; color: white; padding: 5px;")
        right_layout.addWidget(title)
        
        # Scroll area for metadata
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.metadata_widget = QWidget()
        self.metadata_layout = QVBoxLayout(self.metadata_widget)  
        self.metadata_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._render_import_sections()
        self._render_metadata_sections(None)
        
        scroll_area.setWidget(self.metadata_widget)
        
        right_layout.addWidget(scroll_area)
        right_layout.addWidget(self._create_import_action_bar())
        
        parent.addWidget(right_widget)
        logger.debug("Metadata panel setup complete.")

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
            self.IMPORT_PANEL_STATE_KEY: self._default_panel_states(),
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
        rename_templates = self._normalize_rename_templates(import_config.get(self.RENAME_TEMPLATE_LIST_KEY))
        if not rename_templates:
            rename_templates = self._default_rename_templates()
        if import_config.get(self.RENAME_TEMPLATE_LIST_KEY) != rename_templates:
            import_config[self.RENAME_TEMPLATE_LIST_KEY] = rename_templates
            self.config_manager.set(self.IMPORT_PRESET_CONFIG_KEY, import_config)
        return import_config

    def _normalize_import_settings(self, settings: Optional[dict[str, object]]) -> dict[str, object]:
        normalized = self._default_import_settings()
        if isinstance(settings, dict):
            normalized.update(settings)
        rename_templates = self._get_rename_templates_map()
        selected_template = str(normalized.get("selected_template", "")).strip()
        template_pattern = self._normalize_template_pattern(str(normalized.get("template_pattern", "")).strip())
        if selected_template in rename_templates:
            normalized["selected_template"] = selected_template
        else:
            normalized["selected_template"] = self._find_template_name_by_pattern(template_pattern, rename_templates)
        normalized["template_pattern"] = rename_templates.get(normalized["selected_template"], template_pattern)
        return normalized

    def _resolve_sequence_token(self, template_value: str, sequence_number: int) -> str:
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

    def _normalize_rename_templates(self, config_value: object) -> dict[str, str]:
        if isinstance(config_value, dict):
            normalized_templates: dict[str, str] = {}
            for name, pattern in config_value.items():
                template_name = str(name).strip()
                template_pattern = self._normalize_template_pattern(str(pattern).strip())
                if not template_name or not template_pattern:
                    continue
                display_name = self._default_template_name(template_pattern)
                normalized_name = display_name if template_name in self.RENAME_TEMPLATE_OPTIONS or template_name in self.DEFAULT_RENAME_TEMPLATE_NAMES.values() else template_name
                normalized_templates[normalized_name] = template_pattern
            return normalized_templates
        if isinstance(config_value, list):
            return {
                self._default_template_name(self._normalize_template_pattern(str(item).strip())): self._normalize_template_pattern(str(item).strip())
                for item in config_value
                if str(item).strip()
            }
        return {}

    def _default_template_name(self, template_pattern: str) -> str:
        return self.DEFAULT_RENAME_TEMPLATE_NAMES.get(template_pattern, template_pattern)

    def _normalize_template_pattern(self, template_pattern: str) -> str:
        compact_value = re.sub(r"\s+", " ", template_pattern).strip()
        if not compact_value:
            return self.RENAME_TEMPLATE_OPTIONS[0]
        return self.LEGACY_RENAME_TEMPLATE_MAP.get(compact_value, compact_value)

    def _get_rename_templates_map(self, import_config: Optional[dict[str, object]] = None) -> dict[str, str]:
        config_value = (import_config or self._get_import_config()).get(self.RENAME_TEMPLATE_LIST_KEY)
        rename_templates = self._normalize_rename_templates(config_value)
        return rename_templates or self._default_rename_templates()

    def _find_template_name_by_pattern(self, template_pattern: str, rename_templates: Optional[dict[str, str]] = None) -> str:
        available_templates = rename_templates or self._get_rename_templates_map()
        normalized_pattern = self._normalize_template_pattern(template_pattern)
        for template_name, pattern in available_templates.items():
            if pattern == normalized_pattern:
                return template_name
        return next(iter(available_templates))

    def _default_panel_states(self) -> dict[str, bool]:
        return {
            "import_preset": True,
            "file_handling": True,
            "file_renaming": True,
            "destination": True,
        }

    def _get_panel_states(self) -> dict[str, bool]:
        import_config = self._get_import_config()
        saved_states = import_config.get(self.IMPORT_PANEL_STATE_KEY)
        panel_states = self._default_panel_states()
        if isinstance(saved_states, dict):
            for key, value in saved_states.items():
                panel_states[str(key)] = bool(value)
        return panel_states

    def _is_panel_expanded(self, panel_key: str) -> bool:
        return self._get_panel_states().get(panel_key, True)

    def _save_panel_state(self, panel_key: str, is_expanded: bool) -> None:
        import_config = self._get_import_config()
        panel_states = self._get_panel_states()
        panel_states[panel_key] = is_expanded
        import_config[self.IMPORT_PANEL_STATE_KEY] = panel_states
        self._save_import_config(import_config)

    def _get_current_import_settings(self) -> dict[str, object]:
        import_config = self._get_import_config()
        settings = import_config.get(self.IMPORT_SETTINGS_KEY)
        return self._normalize_import_settings(settings if isinstance(settings, dict) else None)

    def _save_import_config(self, import_config: dict[str, object]) -> None:
        self.config_manager.set(self.IMPORT_PRESET_CONFIG_KEY, import_config)

    def _render_import_sections(self) -> None:
        self._add_import_group("import_preset", "Import Preset", self._create_import_preset_widget())
        self._add_import_group("file_handling", "File Handling", self._create_file_handling_widget())
        self._add_import_group("file_renaming", "File Renaming", self._create_file_renaming_widget())
        self._add_import_group("destination", "Destination", self._create_destination_widget())
        self.import_section_count = self.metadata_layout.count()
        self._load_import_settings_into_ui()

    def _add_import_group(self, panel_key: str, title: str, content_widget: QWidget) -> None:
        self.metadata_layout.addWidget(
            self._create_panel_collapsible_group(
                title,
                content_widget,
                is_expanded=self._is_panel_expanded(panel_key),
                panel_key=panel_key,
            )
        )

    def _build_group_header(self, title: str) -> QWidget:
        panel_color = (35, 35, 40)
        lighter_color = tuple(min(255, int(c + (255 - c) * 0.25)) for c in panel_color)
        lighter_color_str = f"rgb({lighter_color[0]}, {lighter_color[1]}, {lighter_color[2]})"
        header_widget = QWidget()
        header_widget.setFixedHeight(30)
        header_widget.setStyleSheet(
            f"background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 5px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
        )
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background-color: transparent; border: none;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        return header_widget

    def _build_group_content_widget(self) -> tuple[QWidget, QVBoxLayout]:
        panel_color = (35, 35, 40)
        lighter_color = tuple(min(255, int(c + (255 - c) * 0.25)) for c in panel_color)
        lighter_color_str = f"rgb({lighter_color[0]}, {lighter_color[1]}, {lighter_color[2]})"
        widget = QWidget()
        widget.setStyleSheet(
            f"background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 5px; border-top-left-radius: 0px; border-top-right-radius: 0px; margin-top: -1px;"
        )
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        return widget, layout

    def _create_panel_collapsible_group(self, title: str, content_widget: QWidget, is_expanded: bool = True, panel_key: str = "") -> QWidget:
        panel_color = (35, 35, 40)
        lighter_color = tuple(min(255, int(c + (255 - c) * 0.25)) for c in panel_color)
        lighter_color_str = f"rgb({lighter_color[0]}, {lighter_color[1]}, {lighter_color[2]})"
        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(0)
        header_widget = QWidget()
        header_widget.setFixedHeight(30)
        header_widget.setStyleSheet(
            f"background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 5px;"
        )
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background-color: transparent; border: none;")
        toggle_button = QPushButton("▼" if is_expanded else "▶")
        toggle_button.setFixedSize(20, 20)
        toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_button.setStyleSheet(
            f"QPushButton {{ color: white; background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 3px; font-size: 10px; font-weight: bold; }}"
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(toggle_button)
        if is_expanded:
            content_widget.setStyleSheet(content_widget.styleSheet() + "")
        else:
            content_widget.hide()

        def toggle_content() -> None:
            is_visible = content_widget.isVisible()
            content_widget.setVisible(not is_visible)
            is_now_expanded = not is_visible
            toggle_button.setText("▼" if is_now_expanded else "▶")
            header_widget.setStyleSheet(
                f"background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 5px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
                if is_now_expanded else
                f"background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 5px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
            )
            content_widget.setStyleSheet(
                content_widget.styleSheet().replace("border-radius: 5px;", "border-radius: 5px; border-top-left-radius: 0px; border-top-right-radius: 0px;")
                if is_now_expanded else content_widget.styleSheet()
            )
            if panel_key:
                self._save_panel_state(panel_key, is_now_expanded)

        if content_widget.styleSheet():
            content_widget.setStyleSheet(
                content_widget.styleSheet().replace("border-radius: 5px;", "border-radius: 5px; border-top-left-radius: 0px; border-top-right-radius: 0px;")
            )
        if is_expanded:
            header_widget.setStyleSheet(
                f"background-color: {lighter_color_str}; border: 1px solid rgb(60, 60, 65); border-radius: 5px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
            )
        toggle_button.clicked.connect(toggle_content)
        group_layout.addWidget(header_widget)
        group_layout.addWidget(content_widget)
        return group_widget

    def _create_import_preset_widget(self) -> QWidget:
        widget, layout = self._build_group_content_widget()
        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        self._style_combo_box(self.preset_combo)
        layout.addWidget(self.preset_combo)
        button_layout = QHBoxLayout()
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
        self.preset_feedback_label.setStyleSheet("color: rgb(180, 180, 180); font-size: 11px; border: none;")
        layout.addWidget(self.preset_feedback_label)
        return widget

    def _create_file_handling_widget(self) -> QWidget:
        widget, layout = self._build_group_content_widget()
        skip_duplicates = QCheckBox("Skip possible duplicates")
        skip_rejected = QCheckBox("Skip rejected images")
        for checkbox, key in ((skip_duplicates, "skip_duplicates"), (skip_rejected, "skip_rejected")):
            checkbox.setStyleSheet("color: white;")
            checkbox.toggled.connect(lambda checked, setting_key=key: self._on_import_setting_changed(setting_key, checked))
            self.import_panel_widgets[key] = checkbox
            layout.addWidget(checkbox)
        return widget

    def _create_file_renaming_widget(self) -> QWidget:
        widget, layout = self._build_group_content_widget()
        form_layout = QFormLayout()
        template_combo = QComboBox()
        template_combo.currentTextChanged.connect(self._on_template_selected)
        self._style_combo_box(template_combo)
        template_edit = QLineEdit()
        template_edit.textChanged.connect(lambda text: self._on_import_setting_changed("template_pattern", text))
        self._style_line_edit(template_edit)
        self.rename_sample_label = QLabel("")
        self.rename_sample_label.setStyleSheet("color: rgb(180, 180, 180); font-size: 11px; border: none;")
        self.rename_tokens_widget = self._create_rename_tokens_help_widget()
        self.import_panel_widgets["selected_template"] = template_combo
        self.import_panel_widgets["template_pattern"] = template_edit
        form_layout.addRow(self._create_form_label("Template"), template_combo)
        form_layout.addRow(self._create_form_label("Edit"), template_edit)
        form_layout.addRow(self._create_form_label("Tokens"), self.rename_tokens_widget)
        form_layout.addRow(self._create_form_label("Sample"), self.rename_sample_label)
        layout.addLayout(form_layout)
        button_layout = QHBoxLayout()
        create_button = self._create_small_button("Create", self._create_rename_template)
        save_button = self._create_small_button("Save", self._save_selected_template)
        rename_button = self._create_small_button("Rename", self._rename_selected_template)
        delete_button = self._create_small_button("Delete", self._delete_selected_template)
        button_layout.addWidget(create_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(rename_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)
        self.rename_feedback_label = QLabel("")
        self.rename_feedback_label.setStyleSheet("color: rgb(180, 180, 180); font-size: 11px; border: none;")
        layout.addWidget(self.rename_feedback_label)
        return widget

    def _create_destination_widget(self) -> QWidget:
        widget, layout = self._build_group_content_widget()
        root_layout = QHBoxLayout()
        target_root_edit = QLineEdit()
        target_root_edit.textChanged.connect(lambda text: self._on_import_setting_changed("target_root", text))
        self._style_line_edit(target_root_edit)
        browse_button = self._create_small_button("Browse", self._select_target_root)
        root_layout.addWidget(target_root_edit)
        root_layout.addWidget(browse_button)
        form_layout = QFormLayout()
        organize_combo = QComboBox()
        for value, label in self.ORGANIZE_OPTIONS:
            organize_combo.addItem(label, value)
        organize_combo.currentIndexChanged.connect(lambda _: self._on_combo_setting_changed("organize_mode", organize_combo))
        self._style_combo_box(organize_combo)
        date_format_combo = QComboBox()
        for value, label in self.DATE_FORMAT_OPTIONS:
            date_format_combo.addItem(label, value)
        date_format_combo.currentIndexChanged.connect(lambda _: self._on_combo_setting_changed("date_format", date_format_combo))
        self._style_combo_box(date_format_combo)
        self.import_panel_widgets["target_root"] = target_root_edit
        self.import_panel_widgets["organize_mode"] = organize_combo
        self.import_panel_widgets["date_format"] = date_format_combo
        delete_checkbox = QCheckBox("Delete imported source files after import")
        delete_checkbox.setStyleSheet("color: white;")
        delete_checkbox.toggled.connect(lambda checked: self._on_import_setting_changed("delete_after_import", checked))
        self.import_panel_widgets["delete_after_import"] = delete_checkbox
        form_layout.addRow(self._create_form_label("Target root"), root_layout)
        form_layout.addRow(self._create_form_label("Organize"), organize_combo)
        form_layout.addRow(self._create_form_label("Date format"), date_format_combo)
        layout.addLayout(form_layout)
        layout.addWidget(delete_checkbox)
        return widget

    def _create_import_action_bar(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet(
            "QWidget { background-color: rgb(48, 48, 54); border-top: 1px solid rgb(70, 70, 76); }"
        )
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        summary_label = QLabel("Import selected images")
        summary_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; border: none;")
        summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.import_status_label = QLabel("Select images and choose a target folder.")
        self.import_status_label.setWordWrap(True)
        self.import_status_label.setStyleSheet("color: rgb(205, 205, 210); font-size: 12px; border: none;")
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        self.import_button = self._create_small_button("Import", self._start_import)
        self.import_button.setStyleSheet(
            "QPushButton { background-color: rgb(0, 122, 255); color: white; border: none; border-radius: 6px; padding: 8px 12px; font-weight: bold; } QPushButton:hover { background-color: rgb(20, 142, 255); } QPushButton:disabled { background-color: rgb(80, 80, 86); color: rgb(170, 170, 175); }"
        )
        self.import_cancel_button = self._create_small_button("Cancel", self._cancel_import)
        self.import_cancel_button.setStyleSheet(
            "QPushButton { background-color: rgb(92, 92, 98); color: white; border: none; border-radius: 6px; padding: 8px 12px; font-weight: bold; } QPushButton:hover { background-color: rgb(108, 108, 114); } QPushButton:disabled { background-color: rgb(70, 70, 76); color: rgb(150, 150, 155); }"
        )
        self.import_cancel_button.setEnabled(False)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.import_cancel_button)
        layout.addWidget(summary_label)
        layout.addWidget(self.import_status_label)
        layout.addLayout(button_layout)
        return widget

    def _create_metadata_editor_header_widget(self) -> QWidget:
        widget, layout = self._build_group_content_widget()
        label = QLabel("Editable metadata fields are shown below for the current selection.")
        label.setWordWrap(True)
        label.setStyleSheet("color: rgb(180, 180, 180); font-size: 11px; border: none;")
        layout.addWidget(label)
        return widget

    def _create_small_button(self, text: str, handler) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(handler)
        button.setStyleSheet(
            "QPushButton { background-color: rgb(62, 62, 68); color: white; border: 1px solid rgb(80, 80, 85); border-radius: 4px; padding: 5px 8px; } QPushButton:hover { background-color: rgb(74, 74, 80); }"
        )
        return button

    def _create_form_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("color: rgb(180, 180, 180); font-size: 12px; border: none;")
        return label

    def _create_rename_tokens_help_widget(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(6)
        for token, description in self.RENAME_TOKEN_DESCRIPTIONS:
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            token_button = QPushButton(token)
            token_button.setCursor(Qt.CursorShape.PointingHandCursor)
            token_button.clicked.connect(lambda _checked=False, value=token: self._insert_template_token(value))
            token_button.setStyleSheet(
                "QPushButton { color: rgb(250, 250, 252); background-color: rgb(86, 96, 112); border: 1px solid rgb(140, 150, 168); border-radius: 10px; padding: 4px 10px; font-size: 11px; font-weight: bold; text-align: center; } "
                "QPushButton:hover { background-color: rgb(104, 116, 136); border: 1px solid rgb(176, 186, 204); }"
            )
            description_label = QLabel(description)
            description_label.setWordWrap(True)
            description_label.setStyleSheet("color: rgb(210, 210, 214); font-size: 11px; border: none;")
            row_layout.addWidget(token_button, 0)
            row_layout.addWidget(description_label, 1)
            container_layout.addLayout(row_layout)
        return container

    def _style_line_edit(self, widget: QLineEdit) -> None:
        widget.setStyleSheet("QLineEdit { color: white; background-color: rgb(68, 68, 74); border: 1px solid rgb(60, 60, 65); border-radius: 3px; padding: 3px; font-size: 12px; }")

    def _style_combo_box(self, widget: QComboBox) -> None:
        widget.setEnabled(True)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        widget.setMinimumHeight(28)
        widget.setView(QListView())
        widget.setStyleSheet(
            "QComboBox { color: white; background-color: rgb(68, 68, 74); border: 1px solid rgb(90, 90, 96); border-radius: 6px; padding: 4px 30px 4px 8px; font-size: 12px; min-height: 28px; } "
            "QComboBox:hover { background-color: rgb(78, 78, 84); border: 1px solid rgb(0, 122, 255); } "
            "QComboBox:focus { border: 1px solid rgb(0, 122, 255); } "
            "QComboBox:disabled { color: rgb(160, 160, 165); background-color: rgb(55, 55, 60); border: 1px solid rgb(75, 75, 80); } "
            "QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 24px; border: none; background: transparent; } "
            "QComboBox::down-arrow { width: 10px; height: 10px; } "
            "QComboBox QAbstractItemView { color: white; background-color: rgb(52, 52, 58); border: 1px solid rgb(70, 70, 76); selection-background-color: rgb(0, 122, 255); selection-color: white; outline: 0; }"
        )

    def _load_import_settings_into_ui(self) -> None:
        if self.preset_combo is None:
            return
        import_config = self._get_import_config()
        current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
        preset_names = sorted(import_config[self.IMPORT_PRESET_LIST_KEY].keys())
        template_names = self._get_rename_template_options(import_config)
        active_preset = str(import_config.get(self.IMPORT_PRESET_ACTIVE_KEY, self.DEFAULT_IMPORT_PRESET_NAME))
        self._updating_import_ui = True
        self.preset_combo.clear()
        self.preset_combo.addItems(preset_names)
        self.preset_combo.setCurrentText(active_preset if active_preset in preset_names else preset_names[0])
        template_widget = self.import_panel_widgets.get("selected_template")
        if isinstance(template_widget, QComboBox):
            template_widget.clear()
            template_widget.addItems(template_names)
        self._set_checkbox_value("skip_duplicates", bool(current_settings["skip_duplicates"]))
        self._set_checkbox_value("skip_rejected", bool(current_settings["skip_rejected"]))
        self._set_combo_text_value("selected_template", str(current_settings["selected_template"]))
        self._set_line_edit_value("template_pattern", str(current_settings["template_pattern"]))
        self._set_line_edit_value("target_root", str(current_settings["target_root"]))
        self._set_combo_data_value("organize_mode", str(current_settings["organize_mode"]))
        self._set_combo_data_value("date_format", str(current_settings["date_format"]))
        self._set_checkbox_value("delete_after_import", bool(current_settings["delete_after_import"]))
        self._updating_import_ui = False
        self._update_rename_sample()

    def _set_checkbox_value(self, key: str, value: bool) -> None:
        widget = self.import_panel_widgets.get(key)
        if isinstance(widget, QCheckBox):
            widget.setChecked(value)

    def _set_line_edit_value(self, key: str, value: str) -> None:
        widget = self.import_panel_widgets.get(key)
        if isinstance(widget, QLineEdit):
            widget.setText(value)

    def _set_combo_text_value(self, key: str, value: str) -> None:
        widget = self.import_panel_widgets.get(key)
        if isinstance(widget, QComboBox):
            index = widget.findText(value)
            if index >= 0:
                widget.setCurrentIndex(index)
            elif value:
                widget.addItem(value)
                widget.setCurrentText(value)

    def _set_combo_data_value(self, key: str, value: str) -> None:
        widget = self.import_panel_widgets.get(key)
        if isinstance(widget, QComboBox):
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)

    def _insert_template_token(self, token: str) -> None:
        widget = self.import_panel_widgets.get("template_pattern")
        if not isinstance(widget, QLineEdit):
            return
        current_text = widget.text()
        cursor_position = widget.cursorPosition()
        new_text = f"{current_text[:cursor_position]}{token}{current_text[cursor_position:]}"
        widget.setText(new_text)
        widget.setCursorPosition(cursor_position + len(token))

    def _on_template_selected(self, template_value: str) -> None:
        if self._updating_import_ui:
            return
        template_pattern = self._get_rename_templates_map().get(template_value, self.RENAME_TEMPLATE_OPTIONS[0])
        self._set_line_edit_value("template_pattern", template_pattern)
        self._on_import_setting_changed("selected_template", template_value)

    def _on_combo_setting_changed(self, key: str, combo_box: QComboBox) -> None:
        self._on_import_setting_changed(key, combo_box.currentData())

    def _on_import_setting_changed(self, key: str, value: object) -> None:
        if self._updating_import_ui:
            return
        import_config = self._get_import_config()
        current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
        current_settings[key] = value
        import_config[self.IMPORT_SETTINGS_KEY] = current_settings
        self._save_import_config(import_config)
        self._update_rename_sample()

    def _current_preset_name(self) -> str:
        if self.preset_combo is not None and self.preset_combo.currentText():
            return self.preset_combo.currentText()
        return self.DEFAULT_IMPORT_PRESET_NAME

    def _read_import_settings_from_ui(self) -> dict[str, object]:
        return {
            "skip_duplicates": self._read_checkbox_setting("skip_duplicates"),
            "skip_rejected": self._read_checkbox_setting("skip_rejected"),
            "selected_template": self._read_combo_text_setting("selected_template"),
            "template_pattern": self._read_line_edit_setting("template_pattern"),
            "target_root": self._read_line_edit_setting("target_root"),
            "organize_mode": self._read_combo_data_setting("organize_mode"),
            "date_format": self._read_combo_data_setting("date_format"),
            "delete_after_import": self._read_checkbox_setting("delete_after_import"),
        }

    def _read_checkbox_setting(self, key: str) -> bool:
        widget = self.import_panel_widgets.get(key)
        return bool(widget.isChecked()) if isinstance(widget, QCheckBox) else False

    def _read_line_edit_setting(self, key: str) -> str:
        widget = self.import_panel_widgets.get(key)
        return widget.text().strip() if isinstance(widget, QLineEdit) else ""

    def _read_combo_text_setting(self, key: str) -> str:
        widget = self.import_panel_widgets.get(key)
        return widget.currentText() if isinstance(widget, QComboBox) else ""

    def _read_combo_data_setting(self, key: str) -> str:
        widget = self.import_panel_widgets.get(key)
        return str(widget.currentData()) if isinstance(widget, QComboBox) else ""

    def _normalize_preset_name(self, name: str) -> str:
        compact_name = re.sub(r"\s+", " ", name).strip()
        return compact_name or self.DEFAULT_IMPORT_PRESET_NAME

    def _make_unique_preset_name(self, requested_name: str, excluded_name: str = "") -> str:
        normalized_name = self._normalize_preset_name(requested_name)
        import_config = self._get_import_config()
        preset_names = set(import_config[self.IMPORT_PRESET_LIST_KEY].keys())
        if excluded_name:
            preset_names.discard(excluded_name)
        if normalized_name not in preset_names:
            return normalized_name
        suffix = 2
        while True:
            candidate = f"{normalized_name}{self.PRESET_NAME_SUFFIX_SEPARATOR}{suffix})"
            if candidate not in preset_names:
                return candidate
            suffix += 1

    def _set_preset_feedback(self, message: str) -> None:
        if self.preset_feedback_label:
            self.preset_feedback_label.setText(message)

    def _set_rename_feedback(self, message: str) -> None:
        if self.rename_feedback_label:
            self.rename_feedback_label.setText(message)

    def _get_rename_template_options(self, import_config: Optional[dict[str, object]] = None) -> list[str]:
        return list(self._get_rename_templates_map(import_config).keys())

    def _normalize_template_name(self, template_name: str) -> str:
        compact_value = re.sub(r"\s+", " ", template_name).strip()
        return compact_value or self._default_template_name(self.RENAME_TEMPLATE_OPTIONS[0])

    def _make_unique_template_name(self, requested_value: str, excluded_value: str = "") -> str:
        normalized_value = self._normalize_template_name(requested_value)
        template_options = set(self._get_rename_template_options())
        if excluded_value:
            template_options.discard(excluded_value)
        if normalized_value not in template_options:
            return normalized_value
        suffix = 2
        while True:
            candidate = f"{normalized_value}{self.PRESET_NAME_SUFFIX_SEPARATOR}{suffix})"
            if candidate not in template_options:
                return candidate
            suffix += 1

    def _save_template_options(self, template_options: dict[str, str], selected_name: str, selected_pattern: str) -> None:
        import_config = self._get_import_config()
        import_config[self.RENAME_TEMPLATE_LIST_KEY] = dict(template_options)
        current_settings = self._normalize_import_settings(import_config.get(self.IMPORT_SETTINGS_KEY))
        current_settings["selected_template"] = selected_name
        current_settings["template_pattern"] = selected_pattern
        import_config[self.IMPORT_SETTINGS_KEY] = current_settings
        active_preset = str(import_config.get(self.IMPORT_PRESET_ACTIVE_KEY, self.DEFAULT_IMPORT_PRESET_NAME))
        presets = dict(import_config[self.IMPORT_PRESET_LIST_KEY])
        if active_preset in presets:
            preset_settings = self._normalize_import_settings(presets[active_preset])
            preset_settings["selected_template"] = selected_name
            preset_settings["template_pattern"] = selected_pattern
            presets[active_preset] = preset_settings
            import_config[self.IMPORT_PRESET_LIST_KEY] = presets
        self._save_import_config(import_config)
        self._load_import_settings_into_ui()

    def _prompt_new_template_details(self) -> tuple[str, str] | None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Rename Template")
        dialog.setModal(True)
        dialog.setMinimumWidth(420)
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        template_name_edit = QLineEdit()
        template_pattern_edit = QLineEdit()
        template_pattern_edit.setText(self._read_line_edit_setting("template_pattern"))
        self._style_line_edit(template_name_edit)
        self._style_line_edit(template_pattern_edit)
        form_layout.addRow(self._create_form_label("Template name"), template_name_edit)
        form_layout.addRow(self._create_form_label("Rename pattern"), template_pattern_edit)
        layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        button_box.setStyleSheet(
            "QPushButton { background-color: rgb(62, 62, 68); color: white; border: 1px solid rgb(80, 80, 85); border-radius: 4px; padding: 5px 10px; } QPushButton:hover { background-color: rgb(74, 74, 80); }"
        )
        layout.addWidget(button_box)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        template_name = self._normalize_template_name(template_name_edit.text())
        template_pattern = self._normalize_template_pattern(template_pattern_edit.text())
        return template_name, template_pattern

    def _create_rename_template(self) -> None:
        template_details = self._prompt_new_template_details()
        if template_details is None:
            return
        template_name, template_pattern = template_details
        unique_name = self._make_unique_template_name(template_name)
        template_options = self._get_rename_templates_map()
        template_options[unique_name] = template_pattern
        self._save_template_options(template_options, unique_name, template_pattern)
        self._set_rename_feedback(f"Template saved as '{unique_name}'.")

    def _save_selected_template(self) -> None:
        current_value = self._read_combo_text_setting("selected_template")
        updated_pattern = self._normalize_template_pattern(self._read_line_edit_setting("template_pattern"))
        template_options = self._get_rename_templates_map()
        template_options[current_value] = updated_pattern
        self._save_template_options(template_options, current_value, updated_pattern)
        self._set_rename_feedback(f"Template '{current_value}' updated.")

    def _rename_selected_template(self) -> None:
        current_value = self._read_combo_text_setting("selected_template")
        renamed_value, accepted = QInputDialog.getText(self, "Rename Template", "Template name", text=current_value)
        if not accepted:
            return
        unique_value = self._make_unique_template_name(renamed_value, excluded_value=current_value)
        template_options = self._get_rename_templates_map()
        template_pattern = template_options.pop(current_value, self.RENAME_TEMPLATE_OPTIONS[0])
        template_options[unique_value] = template_pattern
        self._save_template_options(template_options, unique_value, template_pattern)
        self._set_rename_feedback(f"Template renamed to '{unique_value}'.")

    def _delete_selected_template(self) -> None:
        current_value = self._read_combo_text_setting("selected_template")
        template_options = self._get_rename_templates_map()
        if current_value not in template_options:
            return
        if len(template_options) == 1:
            QMessageBox.information(self, "Delete Template", "At least one rename template must remain.")
            return
        template_options.pop(current_value, None)
        next_value = next(iter(template_options))
        self._save_template_options(template_options, next_value, template_options[next_value])
        self._set_rename_feedback(f"Template '{current_value}' deleted.")

    def _create_import_preset(self) -> None:
        preset_name, accepted = QInputDialog.getText(self, "Create Import Preset", "Preset name")
        if not accepted:
            return
        unique_name = self._make_unique_preset_name(preset_name)
        import_config = self._get_import_config()
        presets = dict(import_config[self.IMPORT_PRESET_LIST_KEY])
        presets[unique_name] = self._read_import_settings_from_ui()
        import_config[self.IMPORT_PRESET_LIST_KEY] = presets
        import_config[self.IMPORT_PRESET_ACTIVE_KEY] = unique_name
        import_config[self.IMPORT_SETTINGS_KEY] = dict(presets[unique_name])
        self._save_import_config(import_config)
        self._load_import_settings_into_ui()
        self._set_preset_feedback(f"Preset saved as '{unique_name}'.")

    def _save_selected_preset(self) -> None:
        preset_name = self._current_preset_name()
        import_config = self._get_import_config()
        presets = dict(import_config[self.IMPORT_PRESET_LIST_KEY])
        presets[preset_name] = self._read_import_settings_from_ui()
        import_config[self.IMPORT_PRESET_LIST_KEY] = presets
        import_config[self.IMPORT_PRESET_ACTIVE_KEY] = preset_name
        import_config[self.IMPORT_SETTINGS_KEY] = dict(presets[preset_name])
        self._save_import_config(import_config)
        self._set_preset_feedback(f"Preset '{preset_name}' updated.")

    def _rename_import_preset(self) -> None:
        current_name = self._current_preset_name()
        new_name, accepted = QInputDialog.getText(self, "Rename Import Preset", "Preset name", text=current_name)
        if not accepted:
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
        current_name = self._current_preset_name()
        if current_name == self.DEFAULT_IMPORT_PRESET_NAME:
            QMessageBox.information(self, "Delete Import Preset", "The default preset cannot be deleted.")
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
        if self._updating_import_ui or not preset_name:
            return
        import_config = self._get_import_config()
        presets = import_config[self.IMPORT_PRESET_LIST_KEY]
        selected_settings = self._normalize_import_settings(presets.get(preset_name))
        import_config[self.IMPORT_PRESET_ACTIVE_KEY] = preset_name
        import_config[self.IMPORT_SETTINGS_KEY] = selected_settings
        self._save_import_config(import_config)
        self._updating_import_ui = True
        self._set_checkbox_value("skip_duplicates", bool(selected_settings["skip_duplicates"]))
        self._set_checkbox_value("skip_rejected", bool(selected_settings["skip_rejected"]))
        self._set_combo_text_value("selected_template", str(selected_settings["selected_template"]))
        self._set_line_edit_value("template_pattern", str(selected_settings["template_pattern"]))
        self._set_line_edit_value("target_root", str(selected_settings["target_root"]))
        self._set_combo_data_value("organize_mode", str(selected_settings["organize_mode"]))
        self._set_combo_data_value("date_format", str(selected_settings["date_format"]))
        self._set_checkbox_value("delete_after_import", bool(selected_settings["delete_after_import"]))
        self._updating_import_ui = False
        self._update_rename_sample()

    def _set_import_status(self, message: str) -> None:
        if self.import_status_label is not None:
            self.import_status_label.setText(message)

    def _set_import_buttons_enabled(self, is_importing: bool) -> None:
        if self.import_button is not None:
            self.import_button.setEnabled(not is_importing)
        if self.import_cancel_button is not None:
            self.import_cancel_button.setEnabled(is_importing)

    def _start_import(self) -> None:
        if self.is_importing:
            return
        if not self.selected_images:
            QMessageBox.information(self, "Import", "Select at least one image to import.")
            return
        settings = self._read_import_settings_from_ui()
        target_root_value = str(settings.get("target_root", "")).strip()
        if not target_root_value:
            QMessageBox.warning(self, "Import", "Set a target root folder before importing.")
            return
        target_root = Path(target_root_value)
        target_root.mkdir(parents=True, exist_ok=True)
        self.is_importing = True
        self.import_cancel_requested = False
        self._set_import_buttons_enabled(True)
        imported_sources: List[Path] = []
        try:
            total_count = len(self.selected_images)
            for sequence_number, source_path in enumerate(list(self.selected_images), start=1):
                if self.import_cancel_requested:
                    break
                target_path = self._build_import_target_path(source_path, target_root, sequence_number)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
                self._write_target_xmp(source_path, target_path)
                imported_sources.append(source_path)
                self._set_import_status(f"Imported {len(imported_sources)}/{total_count}: {target_path.name}")
                QApplication.processEvents()
            if self.import_cancel_requested:
                self._set_import_status(f"Import cancelled after {len(imported_sources)} item(s).")
                return
            if bool(settings.get("delete_after_import", False)):
                self._delete_imported_sources(imported_sources)
            self._set_import_status(f"Import finished: {len(imported_sources)} item(s) copied.")
            QMessageBox.information(self, "Import", f"Imported {len(imported_sources)} image(s).")
        except Exception as error:
            logger.error("Import failed: %s", error)
            QMessageBox.critical(self, "Import", f"Import failed: {error}")
            self._set_import_status("Import failed.")
        finally:
            self.is_importing = False
            self.import_cancel_requested = False
            self._set_import_buttons_enabled(False)
            if bool(settings.get("delete_after_import", False)) and self.current_folder is not None:
                self._load_images_from_folder()

    def _cancel_import(self) -> None:
        if self.is_importing:
            self.import_cancel_requested = True
            self._set_import_status("Cancelling import...")

    def _build_import_target_path(self, source_path: Path, target_root: Path, sequence_number: int) -> Path:
        settings = self._read_import_settings_from_ui()
        import_datetime = self._get_import_datetime(source_path)
        target_dir = self._resolve_import_directory(target_root, import_datetime, str(settings.get("organize_mode", "")), str(settings.get("date_format", "")))
        target_name = self._render_import_filename(source_path, import_datetime, str(settings.get("template_pattern", "")), sequence_number)
        return self._make_unique_target_path(target_dir / f"{target_name}{source_path.suffix.lower()}")

    def _resolve_import_directory(self, target_root: Path, import_datetime: datetime, organize_mode: str, date_format: str) -> Path:
        if organize_mode != "by_date":
            return target_root
        date_folder = import_datetime.strftime(date_format or self.DATE_FORMAT_OPTIONS[0][0]).strip("/ ")
        return target_root / date_folder if date_folder else target_root

    def _render_import_filename(self, source_path: Path, import_datetime: datetime, template_pattern: str, sequence_number: int) -> str:
        template_value = template_pattern or self.RENAME_TEMPLATE_OPTIONS[0]
        rendered_name = template_value.replace("{date}", import_datetime.strftime(self._read_combo_data_setting("date_format") or self.DATE_FORMAT_OPTIONS[0][0]))
        rendered_name = rendered_name.replace("{capture_time}", import_datetime.strftime(self.CAPTURE_TIME_FORMAT))
        rendered_name = rendered_name.replace("{filename}", source_path.stem)
        rendered_name = self._resolve_sequence_token(rendered_name, sequence_number)
        return self._sanitize_import_name(rendered_name) or source_path.stem

    def _sanitize_import_name(self, value: str) -> str:
        sanitized_value = re.sub(r'[\\/:*?"<>|]+', "_", value).strip()
        return sanitized_value.rstrip(".")

    def _make_unique_target_path(self, target_path: Path) -> Path:
        if not target_path.exists() and not target_path.with_suffix(".xmp").exists():
            return target_path
        suffix_number = 2
        while True:
            candidate_path = target_path.with_name(f"{target_path.stem}-{suffix_number}{target_path.suffix}")
            if not candidate_path.exists() and not candidate_path.with_suffix(".xmp").exists():
                return candidate_path
            suffix_number += 1

    def _get_import_datetime(self, image_path: Path) -> datetime:
        try:
            from PIL import Image
            with Image.open(image_path) as image:
                exif = image.getexif()
                raw_value = exif.get(36867) or exif.get(306)
                if raw_value:
                    return datetime.strptime(str(raw_value), "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass
        return datetime.fromtimestamp(image_path.stat().st_mtime)

    def _write_target_xmp(self, source_path: Path, target_path: Path) -> None:
        metadata = self._load_iptc_data(source_path)
        metadata.update(self.metadata_overrides.get(source_path, {}))
        for key, value in metadata.items():
            if key in self.FIELD_TO_XMP_PROP:
                self._write_xmp_sidecar(target_path, key, value)

    def _delete_imported_sources(self, source_paths: List[Path]) -> None:
        imported_set = set(source_paths)
        for source_path in source_paths:
            source_path.unlink(missing_ok=True)
            source_path.with_suffix(".xmp").unlink(missing_ok=True)
        if imported_set and imported_set == set(self.image_files):
            self._cleanup_empty_directories(source_paths)

    def _cleanup_empty_directories(self, source_paths: List[Path]) -> None:
        if self.current_folder is None:
            return
        root_path = self.current_folder.resolve()
        for directory_path in sorted({path.parent.resolve() for path in source_paths}, key=lambda item: len(item.parts), reverse=True):
            self._remove_empty_directory_chain(directory_path, root_path)

    def _remove_empty_directory_chain(self, start_path: Path, root_path: Path) -> None:
        current_path = start_path
        while True:
            if current_path != root_path and root_path not in current_path.parents:
                return
            try:
                current_path.rmdir()
            except OSError:
                return
            if current_path == root_path:
                return
            current_path = current_path.parent

    def _select_target_root(self) -> None:
        current_value = self._read_line_edit_setting("target_root") or str(Path.home())
        selected_dir = QFileDialog.getExistingDirectory(self, "Select Target Root", current_value)
        if not selected_dir:
            return
        self._set_line_edit_value("target_root", selected_dir)
        self._on_import_setting_changed("target_root", selected_dir)

    def _update_rename_sample(self) -> None:
        if not self.rename_sample_label:
            return
        settings = self._read_import_settings_from_ui() if self.import_panel_widgets else self._get_current_import_settings()
        template = str(settings.get("template_pattern", self.RENAME_TEMPLATE_OPTIONS[0]))
        date_value = self.SAMPLE_CAPTURE_TIME.strftime(str(settings.get("date_format", self.DATE_FORMAT_OPTIONS[0][0])))
        capture_time_value = self.SAMPLE_CAPTURE_TIME.strftime(self.CAPTURE_TIME_FORMAT)
        sample_name = template.replace("{date}", date_value)
        sample_name = sample_name.replace("{capture_time}", capture_time_value)
        sample_name = sample_name.replace("{filename}", self.SAMPLE_FILENAME)
        sample_name = self._resolve_sequence_token(sample_name, 1)
        self.rename_sample_label.setText(sample_name)

    def _filter_import_candidates(self, image_paths: List[str]) -> List[str]:
        settings = self._get_current_import_settings()
        filtered_paths = list(image_paths)
        if bool(settings.get("skip_duplicates", True)):
            filtered_paths = self._remove_possible_duplicates(filtered_paths)
        if bool(settings.get("skip_rejected", True)):
            filtered_paths = [path for path in filtered_paths if not self._is_rejected_image(Path(path))]
        return filtered_paths

    def _remove_possible_duplicates(self, image_paths: List[str]) -> List[str]:
        unique_paths: List[str] = []
        seen_fingerprints: set[str] = set()
        for image_path in image_paths:
            fingerprint = self._build_duplicate_fingerprint(Path(image_path))
            if fingerprint in seen_fingerprints:
                continue
            seen_fingerprints.add(fingerprint)
            unique_paths.append(image_path)
        return unique_paths

    def _build_duplicate_fingerprint(self, image_path: Path) -> str:
        try:
            stat_result = image_path.stat()
            fingerprint_source = f"{image_path.name.lower()}|{stat_result.st_size}|{int(stat_result.st_mtime)}"
        except OSError:
            fingerprint_source = image_path.name.lower()
        return sha1(fingerprint_source.encode("utf-8")).hexdigest()

    def _is_rejected_image(self, image_path: Path) -> bool:
        try:
            rating_value = self._read_image_rating(image_path)
        except Exception as error:
            logger.debug("Failed to read rating for %s: %s", image_path, error)
            return False
        return str(rating_value).strip() == self.REJECTED_RATING_VALUE

    def _read_image_rating(self, image_path: Path) -> str:
        suffix = image_path.suffix.lower()
        if suffix in self.RAW_WRITABLE_SUFFIXES:
            metadata = self._read_xmp_editable_metadata(image_path)
            return metadata.get("Rating", "0")
        if suffix in self.PNG_WRITABLE_SUFFIXES:
            metadata = self._read_png_editable_metadata(image_path)
            return metadata.get("Rating", "0")
        if suffix in self.EXIF_WRITABLE_SUFFIXES:
            metadata = self._read_xmp_editable_metadata(image_path)
            if metadata.get("Rating"):
                return metadata.get("Rating", "0")
        return "0"
    
    def _create_simple_collapsible_group(self, title: str, data: dict) -> QWidget:
        """Create a simple collapsible group widget"""
        logger.debug(f"Creating simple collapsible group: {title}")
        
        # Calculate colors
        panel_color = (35, 35, 40)
        lighter_color = tuple(min(255, int(c + (255 - c) * 0.25)) for c in panel_color)
        lighter_color_str = f"rgb({lighter_color[0]}, {lighter_color[1]}, {lighter_color[2]})"
        
        # Field background (15% lighter than group background)
        field_lighter = tuple(min(255, int(c + (255 - c) * 0.15)) for c in lighter_color)
        field_lighter_str = f"rgb({field_lighter[0]}, {field_lighter[1]}, {field_lighter[2]})"
        
        # Main widget
        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(0)
        
        # Header with title and toggle button
        header_widget = QWidget()
        header_widget.setFixedHeight(30)
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {lighter_color_str};
                border: 1px solid rgb(60, 60, 65);
                border-radius: 5px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }}
        """)
        
        # Toggle button
        toggle_button = QPushButton("▼")
        toggle_button.setFixedSize(20, 20)
        toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_button.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background-color: {lighter_color_str};
                border: 1px solid rgb(60, 60, 65);
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        
        # Content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {lighter_color_str};
                border: 1px solid rgb(60, 60, 65);
                border-radius: 5px;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                margin-top: -1px;
            }}
        """)
        
        content_layout = QFormLayout(content_widget)
        content_layout.setContentsMargins(10, 5, 10, 10)
        content_layout.setSpacing(5)
        
        # Add data to content
        for key, value in data.items():
            widget = QLineEdit(str(value))
            widget.setStyleSheet(f"""
                QLineEdit {{
                    color: white;
                    background-color: {field_lighter_str};
                    border: 1px solid rgb(60, 60, 65);
                    border-radius: 3px;
                    padding: 3px;
                    font-size: 12px;
                }}
            """)
            widget.textEdited.connect(lambda text, field_key=key: self._on_metadata_changed(field_key, text))
            self.metadata_widgets[f"{title}:{key}"] = widget
            
            label = QLabel(key + ":")
            label.setStyleSheet(f"""
                QLabel {{
                    color: rgb(180, 180, 180);
                    font-size: 12px;
                    background-color: transparent;
                    border: none;
                }}
            """)
            
            content_layout.addRow(label, widget)
        
        # Toggle functionality
        def toggle_content():
            if content_widget.isVisible():
                content_widget.hide()
                toggle_button.setText("▶")
                group_widget.setFixedHeight(30)
                logger.debug(f"Collapsed {title}")
            else:
                content_widget.show()
                toggle_button.setText("▼")
                group_widget.setMaximumHeight(16777215)
                logger.debug(f"Expanded {title}")
        
        toggle_button.mousePressEvent = lambda e: toggle_content()
        
        # Assemble
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(toggle_button)
        
        group_layout.addWidget(header_widget)
        group_layout.addWidget(content_widget)
        
        logger.debug(f"Simple collapsible group created: {title}")
        return group_widget


    def _load_folder_structure(self) -> None:
        """Load folder structure from file system"""
        for directory_path in self._get_root_directories():
            self._add_folder_item(directory_path, None)
    
    def _add_folder_item(self, path: Path, parent: QTreeWidgetItem = None) -> QTreeWidgetItem:
        """Add folder item to tree"""
        if parent is None:
            item = QTreeWidgetItem(self.folder_tree)
        else:
            item = QTreeWidgetItem(parent)
        
        item.setText(0, path.name)
        item.setData(0, Qt.ItemDataRole.UserRole, str(path))
        item.setIcon(0, QIcon.fromTheme("folder"))
        
        # If recursive loading is enabled, load all subdirectories
        if self.recursive_loading:
            self._load_subdirectories_recursive(path, item)
        else:
            # Add dummy item to show expandable indicator if folder has subdirectories
            if self._has_subdirectories(path):
                dummy_item = QTreeWidgetItem(item)
                dummy_item.setText(0, "")  # Empty text, just for expandability
                dummy_item.setData(0, Qt.ItemDataRole.UserRole, None)
        
        return item
    
    def _has_subdirectories(self, path: Path) -> bool:
        """Check if folder has subdirectories"""
        try:
            for subpath in path.iterdir():
                if subpath.is_dir() and not subpath.name.startswith('.'):
                    return True
        except (PermissionError, OSError):
            pass
        return False
    
    def _on_recursive_toggled(self, checked: bool) -> None:
        """Handle recursive loading checkbox toggle"""
        logger.debug(f"Recursive toggled: {checked}")
        self.recursive_loading = checked
        
        # Only reload if there are folders in the tree
        if self.folder_tree.topLevelItemCount() > 0:
            # Get currently selected folder or first folder
            current_item = self.folder_tree.currentItem()
            if not current_item and self.folder_tree.topLevelItemCount() > 0:
                current_item = self.folder_tree.topLevelItem(0)
            
            if current_item:
                # Reload the current folder structure
                folder_path = Path(current_item.data(0, Qt.ItemDataRole.UserRole))
                if folder_path and folder_path.is_dir():
                    # Clear children and reload
                    current_item.takeChildren()
                    if self.recursive_loading:
                        logger.debug("Loading recursively")
                        self._load_subdirectories_recursive(folder_path, current_item)
                    else:
                        logger.debug("Loading non-recursively")
                        # Add dummy item for expandability if folder has subdirectories
                        if self._has_subdirectories(folder_path):
                            dummy_item = QTreeWidgetItem(current_item)
                            dummy_item.setText(0, "")  # Empty text, just for expandability
                            dummy_item.setData(0, Qt.ItemDataRole.UserRole, None)
        else:
            # If no folders loaded yet, just set the flag for future loads
            pass
    
    def _on_folder_expanded(self, item: QTreeWidgetItem) -> None:
        """Handle folder expansion in tree"""
        logger.debug(f"Folder expanded: {item.text(0)}")
        
        folder_path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if not folder_path_str:
            logger.debug("No folder path data found")
            return
        
        folder_path = Path(folder_path_str)
        if not folder_path.is_dir():
            logger.debug(f"Folder path is not a directory: {folder_path}")
            return
        
        logger.debug(f"Loading subdirectories for: {folder_path}")
        
        # Remove dummy items (items with no UserRole data)
        removed_count = 0
        for i in reversed(range(item.childCount())):
            child = item.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole) is None:
                item.removeChild(child)
                removed_count += 1
        
        logger.debug(f"Removed {removed_count} dummy items")
        
        # Load subdirectories (always load on expansion)
        logger.debug("Loading subdirectories on expansion")
        try:
            loaded_count = 0
            for subpath in sorted(folder_path.iterdir()):
                if subpath.is_dir() and not subpath.name.startswith('.'):
                    self._add_folder_item(subpath, item)
                    loaded_count += 1
            
            logger.debug(f"Loaded {loaded_count} subdirectories")
        except (PermissionError, OSError) as e:
            logger.error(f"Error loading subdirectories: {e}")
            pass
    
    def _load_subdirectories_recursive(self, path: Path, parent_item: QTreeWidgetItem, max_depth: int = 3, current_depth: int = 0) -> None:
        """Load subdirectories recursively with depth limit"""
        if current_depth >= max_depth:
            return
        
        try:
            subdirs = []
            for subpath in sorted(path.iterdir()):
                if subpath.is_dir() and not subpath.name.startswith('.'):
                    subdirs.append(subpath)
            
            # Limit number of subdirectories to prevent performance issues
            max_subdirs = 50
            for i, subpath in enumerate(subdirs[:max_subdirs]):
                # Only add if not already added by expansion
                already_exists = False
                for j in range(parent_item.childCount()):
                    child = parent_item.child(j)
                    if child.data(0, Qt.ItemDataRole.UserRole) == str(subpath):
                        already_exists = True
                        break
                
                if not already_exists:
                    child_item = QTreeWidgetItem(parent_item)
                    child_item.setText(0, subpath.name)
                    child_item.setData(0, Qt.ItemDataRole.UserRole, str(subpath))
                    child_item.setIcon(0, QIcon.fromTheme("folder"))
                    
                    # Continue recursion for subdirectories
                    self._load_subdirectories_recursive(subpath, child_item, max_depth, current_depth + 1)
                
                # Add indicator if there are more subdirectories
                if i == max_subdirs - 1 and len(subdirs) > max_subdirs:
                    more_item = QTreeWidgetItem(parent_item)
                    more_item.setText(0, f"... and {len(subdirs) - max_subdirs} more")
                    more_item.setData(0, Qt.ItemDataRole.UserRole, None)
                    break
                    
        except (PermissionError, OSError):
            pass
    
    def _on_folder_selected(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle folder selection"""
        folder_path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        if folder_path.is_dir():
            self.current_folder = folder_path
            self._load_images_from_folder()
    
    def _load_images_from_folder(self) -> None:
        """Load images from selected folder using thread pool"""
        if not self.current_folder:
            return
        
        # Cancel any existing loading immediately
        logger.debug("[LIB][LOAD] Start loading images, cancelling any previous load")
        self._cancel_loading()
        self._clear_image_grid()
        
        # Start discovery in background thread
        logger.debug("[LIB][LOAD] Starting discovery for folder: %s", self.current_folder)
        self.discovery_thread = ImageDiscoveryThread(
            str(self.current_folder), 
            self.recursive_loading
        )
        
        # Connect signals
        self.discovery_thread.discovery_finished.connect(self._on_discovery_finished)
        
        # Show progress UI
        self.is_loading = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Discovering images...")
        self.cancel_button.setVisible(True)
        
        # Start discovery thread
        self.discovery_thread.start()

    def _clear_image_grid(self) -> None:
        """Clear all thumbnails and reset counters."""
        if self.grid_widget:
            self.grid_widget.clear()
        self.image_files.clear()
        self.selected_image = None
        self.selected_images = []
        self.metadata_overrides.clear()
        self._render_metadata_sections(None)
        self.total_images = 0
        self.processed_images = 0
        self.active_processors.clear()
    
    def _cancel_loading(self) -> None:
        """Cooperatively cancel current loading process"""
        # Mindig logoljunk, ha a Cancel gombot megnyomták
        logger.debug("[LIB][CANCEL] Cancel requested (is_loading=%s, active_processors=%s, discovery_thread=%s)",
                     self.is_loading, len(self.active_processors), bool(self.discovery_thread))

        # Ha semmi nincs folyamatban, nincs mit megszakítani
        if (not self.is_loading
                and not self.active_processors
                and not self.discovery_thread):
            logger.debug("[LIB][CANCEL] Nothing to cancel, returning")
            return

        # Jelöljük, hogy a folyamat leállt
        self.is_loading = False

        # Kérjük meg a discovery threadet, hogy álljon le
        if self.discovery_thread:
            self.discovery_thread.cancel()

        # Kérjük meg az összes aktív processzort, hogy álljon le
        for processor in self.active_processors:
            processor.signals.cancelled = True

        # Nem építjük újra a thread poolt, csak a queue-t ürítjük
        self.thread_pool.clear()

        # UI elemek leállítása/elrejtése
        self.ui_update_timer.stop()
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)

        QApplication.processEvents()
        logger.debug("[LIB][CANCEL] Cancel handling finished")
    
    def _on_discovery_finished(self, image_paths: List[str]) -> None:
        """Handle image discovery finished"""
        if not self.is_loading:
            # Cancelled while discovering
            return

        image_paths = self._filter_import_candidates(image_paths)
        
        self.total_images = len(image_paths)
        logger.debug("[LIB][DISC] Discovery finished: %s images found", self.total_images)
        
        if self.total_images == 0:
            self._on_loading_finished()
            return
        
        # Update progress bar
        self.progress_bar.setFormat(f"Processing {self.total_images} images...")
        
        # Create batches for parallel processing
        batch_size = max(10, min(50, self.total_images // 20))  # Smaller batches for smoother flow
        batches = []
        
        for i in range(0, self.total_images, batch_size):
            batch = image_paths[i:i + batch_size]
            batches.append(batch)
        
        logger.debug("[LIB][DISC] Created %s batches for processing", len(batches))
        
        # Process batches in parallel - start all immediately
        target_size = max(64, int(getattr(self, "current_icon_size", 140)))
        for i, batch in enumerate(batches):
            if not self.is_loading:  # Check cancellation before starting each batch
                break
                
            processor = ImageProcessorRunnable(batch, i, target_size=target_size)
            processor.signals.image_found.connect(self._on_image_found)
            processor.signals.batch_finished.connect(self._on_batch_finished)
            
            self.active_processors.append(processor)
            self.thread_pool.start(processor)
        
        # Force UI update to start showing images immediately
        QApplication.processEvents()
        
        # Start continuous UI updates
        self.ui_update_timer.start(30)
    
    def _on_batch_finished(self, batch_id: int):
        """Handle batch processing finished"""
        if not self.is_loading:
            return
        
        # Remove from active processors
        self.active_processors = [p for p in self.active_processors if p.batch_id != batch_id]
        
        # Check if all batches are finished
        if len(self.active_processors) == 0:
            logger.debug("[LIB][BATCH] All batches finished, calling _on_loading_finished")
            self._on_loading_finished()
    
    def _on_image_found(self, image_path: str, image_name: str, image: QImage) -> None:
        """Handle image found signal from worker"""
        # Check if loading was cancelled
        if not self.is_loading:
            return
        
        logger.debug("[LIB][IMG] Image found: %s", image_name)
        
        # Add image to grid (this runs in main thread)
        logger.debug("[LIB][IMG] Adding image to grid: %s", image_name)
        image_path_obj = Path(image_path)
        self._add_image_to_grid(image_path_obj, image)
        
        # Update progress
        self.processed_images += 1
        if self.total_images > 0:
            progress = int((self.processed_images / self.total_images) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"Processing {self.processed_images}/{self.total_images} images")
        
        # Időnként frissítsük a cellaméreteket betöltés közben is, hogy az
        # aktuális oszlopszám (Columns) már ilyenkor is érvényesüljön.
        if self.processed_images in (1, self.grid_columns) or self.processed_images % 10 == 0:
            self._update_cell_sizes()
        
        # Force immediate UI update to show images continuously
        if self.grid_widget:
            self.grid_widget.update()
        QApplication.processEvents()
        
        # Additional UI update every 5 images for smoother flow
        if self.processed_images % 5 == 0:
            self.ui_update_timer.start(20)  # Trigger UI update
    
    def _on_loading_finished(self) -> None:
        """Handle loading finished signal from thread"""
        self.is_loading = False
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        
        # Stop continuous UI updates
        self.ui_update_timer.stop()
        
        # Recompute cell sizes once, now hogy a view és a splitter már a
        # végleges méreteket használja. Ez segít, hogy az oszlopszám és a
        # cellaméret összhangban legyen az ablak aktuális szélességével.
        self._update_cell_sizes()
        logger.debug("[LIB][DONE] Loading finished. Loaded %s images", len(self.image_files))
    
    def _continuous_ui_update(self) -> None:
        """Continuous UI update for smooth image display"""
        if self.is_loading and self.grid_widget:
            self.grid_widget.update()
            QApplication.processEvents()
            if self.is_loading:
                self.ui_update_timer.start(30)
        else:
            self.ui_update_timer.stop()

    def _add_image_to_grid(self, image_path: Path, image: Optional[QImage] = None) -> None:
        """Add image thumbnail to the grid widget."""
        pixmap = self._create_thumbnail_pixmap(image_path, image)
        if self.grid_widget:
            self.grid_widget.add_image(image_path, pixmap)
        self.image_files.append(image_path)
        if len(self.image_files) == 1:
            self._update_icon_metrics()
        if self.selected_image == image_path:
            self._select_image(image_path)
    
    def _create_thumbnail_pixmap(self, image_path: Path, image: Optional[QImage]) -> QPixmap:
        """Create a raw pixmap; final scaling is done by the delegate.

        Fontos: itt NEM készítünk plusz keretet vagy paddinget, csak egy
        jól használható forrás-pixmapet adunk vissza. A cella méretéhez
        igazodó skálázás az ImageItemDelegate.paint-ben történik.
        """
        if image is not None and not image.isNull():
            return QPixmap.fromImage(image)

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            # Látható placeholder, a delegate a cellamérethez skálázza.
            placeholder = QPixmap(32, 32)
            placeholder.fill(Qt.GlobalColor.darkGray)
            return placeholder
        return pixmap
    
    def _select_image(self, image_path: Path) -> None:
        """Select the given image path in the view."""
        if self.grid_widget:
            self.grid_widget.select_image(image_path)
        self.selected_images = [image_path]
        self.selected_image = image_path
        self._render_metadata_sections(self.selected_images)
    
    def _add_metadata_group(self, title: str, data: dict) -> None:
        """Add metadata group to panel using collapsible group box"""
        try:
            print(f"Adding metadata group: {title}")  # Debug
            
            # Create a simple QWidget instead of CollapsibleGroupBox for now
            group_widget = QWidget()
            group_layout = QVBoxLayout(group_widget)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(0)
            
            # Calculate colors
            panel_color = (35, 35, 40)
            lighter_color = tuple(min(255, int(c + (255 - c) * 0.25)) for c in panel_color)
            lighter_color_str = f"rgb({lighter_color[0]}, {lighter_color[1]}, {lighter_color[2]})"
            
            # Field background (15% lighter than group background)
            field_lighter = tuple(min(255, int(c + (255 - c) * 0.15)) for c in lighter_color)
            field_lighter_str = f"rgb({field_lighter[0]}, {field_lighter[1]}, {field_lighter[2]})"
            
            # Header with title and toggle button
            header_widget = QWidget()
            header_widget.setFixedHeight(30)
            header_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {lighter_color_str};
                    border: 1px solid rgb(60, 60, 65);
                    border-radius: 5px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                }}
            """)
            
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(10, 5, 10, 5)
            
            # Title label
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    background-color: transparent;
                    border: none;
                }}
            """)
            
            # Toggle button
            toggle_button = QPushButton("▼")
            toggle_button.setFixedSize(20, 20)
            toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle_button.setStyleSheet(f"""
                QPushButton {{
                    color: white;
                    background-color: {lighter_color_str};
                    border: 1px solid rgb(60, 60, 65);
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: rgb(70, 70, 75);
                    border-color: rgb(80, 80, 85);
                }}
                QPushButton:pressed {{
                    background-color: rgb(80, 80, 85);
                    border-color: rgb(90, 90, 95);
                }}
            """)
            
            # Content widget
            content_widget = QWidget()
            content_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {lighter_color_str};
                    border: 1px solid rgb(60, 60, 65);
                    border-radius: 5px;
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                    margin-top: -1px;
                }}
            """)
            
            content_layout = QFormLayout(content_widget)
            content_layout.setContentsMargins(10, 5, 10, 10)
            content_layout.setSpacing(5)
            
            # Add data to content
            for key, value in data.items():
                # Create appropriate widget based on value type
                if isinstance(value, str) and len(str(value)) > 50:
                    # Use QTextEdit for long strings
                    widget = QTextEdit(str(value))
                    widget.setFixedHeight(60)
                    widget.textChanged.connect(lambda: self._on_metadata_changed(key, widget.toPlainText()))
                else:
                    # Use QLineEdit for shorter values
                    widget = QLineEdit(str(value))
                    widget.textChanged.connect(lambda text, k=key: self._on_metadata_changed(k, text))
                
                # Style the widget
                widget.setStyleSheet(f"""
                    QLineEdit {{
                        color: white;
                        background-color: {field_lighter_str};
                        border: 1px solid rgb(60, 60, 65);
                        border-radius: 3px;
                        padding: 3px;
                        font-size: 12px;
                    }}
                    QTextEdit {{
                        color: white;
                        background-color: {field_lighter_str};
                        border: 1px solid rgb(60, 60, 65);
                        border-radius: 3px;
                        padding: 3px;
                        font-size: 12px;
                    }}
                """)
                
                label = QLabel(key + ":")
                label.setStyleSheet(f"""
                    QLabel {{
                        color: rgb(180, 180, 180);
                        font-size: 12px;
                        background-color: transparent;
                        border: none;
                    }}
                """)
                
                content_layout.addRow(label, widget)
            
            # Toggle functionality
            def toggle_content():
                if content_widget.isVisible():
                    content_widget.hide()
                    toggle_button.setText("▶")
                    group_widget.setFixedHeight(30)
                else:
                    content_widget.show()
                    toggle_button.setText("▼")
                    group_widget.setMaximumHeight(16777215)
            
            toggle_button.mousePressEvent = lambda e: toggle_content()
            
            # Assemble
            header_layout.addWidget(title_label)
            header_layout.addStretch()
            header_layout.addWidget(toggle_button)
            
            group_layout.addWidget(header_widget)
            group_layout.addWidget(content_widget)
            
            self.metadata_layout.addWidget(group_widget)
            print(f"Added group to layout. Total items in layout: {self.metadata_layout.count()}")  # Debug
        except Exception as e:
            print(f"Error adding metadata group: {e}")  # Debug
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp according to configuration"""
        date_format = self.config_manager.get("panels.library.date_format", "YYYY.mm.dd. HH:MM:SS")
        
        # Convert custom format to Python strftime format
        python_format = date_format.replace("YYYY", "%Y").replace("mm", "%m").replace("dd", "%d").replace("HH", "%H").replace("MM", "%M").replace("SS", "%S")
        
        try:
            return datetime.fromtimestamp(timestamp).strftime(python_format)
        except (ValueError, OSError):
            return str(timestamp)
    
    def _on_columns_changed(self, value: int) -> None:
        """Handle grid columns change"""
        self.grid_columns = value
        if hasattr(self, "columns_value_label"):
            self.columns_value_label.setText(str(value))
        self._queue_grid_layout_update()
        self.logger.info("Grid columns changed to: %s", value)

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """Handle splitter moved event"""
        self._queue_grid_layout_update()

    def _load_image_metadata(self, image_path: Path) -> None:
        """Load and display image metadata with editable fields"""
        print(f"Loading metadata for: {image_path.name}")
        self._render_metadata_sections([image_path])
        print(f"Metadata loaded for: {image_path.name}")

    def _clear_metadata_layout(self) -> None:
        while self.metadata_layout.count() > self.import_section_count:
            item = self.metadata_layout.takeAt(self.import_section_count)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _build_empty_metadata(self, field_names: tuple[str, ...]) -> dict[str, str]:
        return {field_name: "" for field_name in field_names}

    def _get_single_image_metadata(self, image_path: Path) -> dict[str, dict[str, str]]:
        stat_result = image_path.stat()
        metadata_sections = {
            "File Information": {
                "Filename": image_path.name,
                "Path": str(image_path.parent),
                "Size": self._format_file_size(stat_result.st_size),
                "Modified": self._format_timestamp(stat_result.st_mtime),
            },
            "EXIF Data": self._load_exif_data(image_path),
            "IPTC Data": self._load_iptc_data(image_path),
        }
        overrides = self.metadata_overrides.get(image_path, {})
        for field_name, field_value in overrides.items():
            for section_data in metadata_sections.values():
                if field_name in section_data:
                    section_data[field_name] = field_value
                    break
        return metadata_sections

    def _get_empty_metadata_sections(self) -> dict[str, dict[str, str]]:
        return {
            "File Information": self._build_empty_metadata(self.FILE_METADATA_FIELDS),
            "EXIF Data": self._build_empty_metadata(self.EXIF_METADATA_FIELDS),
            "IPTC Data": self._build_empty_metadata(self.IPTC_METADATA_FIELDS),
        }

    def _get_common_metadata_sections(self, image_paths: List[Path]) -> dict[str, dict[str, str]]:
        if not image_paths:
            return self._get_empty_metadata_sections()

        metadata_sections = [self._get_single_image_metadata(image_path) for image_path in image_paths]
        common_sections = self._get_empty_metadata_sections()

        for section_name, field_names in (
            ("File Information", self.FILE_METADATA_FIELDS),
            ("EXIF Data", self.EXIF_METADATA_FIELDS),
            ("IPTC Data", self.IPTC_METADATA_FIELDS),
        ):
            for field_name in field_names:
                values = [sections.get(section_name, {}).get(field_name, "") for sections in metadata_sections]
                if values and all(value == values[0] for value in values):
                    common_sections[section_name][field_name] = values[0]
                else:
                    common_sections[section_name][field_name] = ""

        return common_sections

    def _render_metadata_sections(self, image_paths: Optional[List[Path]]) -> None:
        self._clear_metadata_layout()
        self.metadata_widgets.clear()

        if not image_paths:
            metadata_sections = self._get_empty_metadata_sections()
        elif len(image_paths) == 1:
            metadata_sections = self._get_single_image_metadata(image_paths[0])
        else:
            metadata_sections = self._get_common_metadata_sections(image_paths)

        file_group = self._create_simple_collapsible_group("File Information", metadata_sections["File Information"])
        exif_group = self._create_simple_collapsible_group("EXIF Data", metadata_sections["EXIF Data"])
        iptc_group = self._create_simple_collapsible_group("IPTC Data", metadata_sections["IPTC Data"])

        self.metadata_layout.addWidget(file_group)
        self.metadata_layout.addWidget(exif_group)
        self.metadata_layout.addWidget(iptc_group)
        self.metadata_layout.addStretch()
    
    def _on_grid_selection_changed(self, image_paths: List[Path]) -> None:
        """Handle selection changes from grid widget."""
        self.selected_images = list(image_paths)
        self.selected_image = self.selected_images[0] if len(self.selected_images) == 1 else None
        self._render_metadata_sections(self.selected_images if self.selected_images else None)
    
    def _on_metadata_changed(self, key: str, value: str) -> None:
        """Handle metadata field change."""
        if not self.selected_images:
            return
        normalized_value = self._normalize_metadata_text(value)
        for image_path in self.selected_images:
            image_override = self.metadata_overrides.setdefault(image_path, {})
            image_override[key] = normalized_value
            self.logger.info("Metadata changed for %s: %s = %s", image_path.name, key, normalized_value)

    def _save_metadata_to_file(self, image_path: Path, key: str, value: str) -> None:
        suffix = image_path.suffix.lower()
        try:
            if suffix in self.RAW_WRITABLE_SUFFIXES:
                self._write_xmp_sidecar(image_path, key, value)
                return
            if suffix in self.EXIF_WRITABLE_SUFFIXES:
                self._write_exif_metadata(image_path, key, value)
                return
            if suffix in self.PNG_WRITABLE_SUFFIXES:
                self._write_png_metadata(image_path, key, value)
                return
            logger.warning("Metadata write is not supported for file type: %s", image_path.suffix)
        except Exception as error:
            logger.error("Failed to save metadata for %s: %s", image_path, error)

    def _write_exif_metadata(self, image_path: Path, key: str, value: str) -> None:
        from PIL import Image

        exif_tag_name = self.FIELD_TO_EXIF_TAG.get(key)
        if exif_tag_name is None:
            logger.debug("Skipping EXIF write for unsupported field: %s", key)
            return

        tag_id = self.EXIF_TAG_IDS[exif_tag_name]
        with Image.open(image_path) as image:
            exif = image.getexif()
            exif[tag_id] = self._encode_exif_value(exif_tag_name, value)
            self._save_image_with_replacement(
                image=image,
                image_path=image_path,
                save_kwargs={"exif": exif.tobytes()},
            )

    def _write_png_metadata(self, image_path: Path, key: str, value: str) -> None:
        from PIL import Image
        from PIL.PngImagePlugin import PngInfo

        png_key = self.FIELD_TO_PNG_KEY.get(key)
        if png_key is None:
            logger.debug("Skipping PNG metadata write for unsupported field: %s", key)
            return

        with Image.open(image_path) as image:
            png_info = PngInfo()
            for info_key, info_value in image.info.items():
                if isinstance(info_value, str):
                    png_info.add_text(info_key, info_value)
            png_info.add_text(png_key, value)
            self._save_image_with_replacement(
                image=image,
                image_path=image_path,
                save_kwargs={"pnginfo": png_info},
            )

    def _save_image_with_replacement(self, image, image_path: Path, save_kwargs: dict) -> None:
        suffix = image_path.suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=str(image_path.parent)) as temp_file:
            temp_path = Path(temp_file.name)
        try:
            image.save(temp_path, **save_kwargs)
            shutil.move(str(temp_path), str(image_path))
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def _normalize_metadata_text(self, value: object) -> str:
        if value is None:
            return ""
        return unicodedata.normalize("NFC", str(value))

    def _encode_exif_value(self, exif_tag_name: str, value: str) -> str | bytes:
        normalized_value = self._normalize_metadata_text(value)
        if exif_tag_name.startswith("XP"):
            return (normalized_value + "\x00").encode("utf-16le")
        return normalized_value

    def _decode_exif_value(self, value: object) -> str:
        if isinstance(value, bytes):
            try:
                return self._normalize_metadata_text(value.decode("utf-16le", errors="ignore").rstrip("\x00"))
            except Exception:
                return self._normalize_metadata_text(value.decode(errors="ignore").rstrip("\x00"))
        if isinstance(value, tuple) and len(value) > 1 and value[1] != 0:
            return self._normalize_metadata_text(f"{value[0]}/{value[1]}")
        return self._normalize_metadata_text(value)

    def _read_exif_editable_metadata(self, image_path: Path) -> dict[str, str]:
        from PIL import Image

        with Image.open(image_path) as image:
            exif = image.getexif()
            title_value = self._decode_exif_value(exif.get(self.EXIF_TAG_IDS["XPTitle"], ""))
            description_value = self._decode_exif_value(exif.get(self.EXIF_TAG_IDS["XPComment"], exif.get(self.EXIF_TAG_IDS["ImageDescription"], "")))
            keywords_value = self._decode_exif_value(exif.get(self.EXIF_TAG_IDS["XPKeywords"], ""))
            creator_value = self._decode_exif_value(exif.get(self.EXIF_TAG_IDS["XPAuthor"], exif.get(self.EXIF_TAG_IDS["Artist"], "")))
            subject_value = self._decode_exif_value(exif.get(self.EXIF_TAG_IDS["XPSubject"], ""))
            copyright_value = self._decode_exif_value(exif.get(self.EXIF_TAG_IDS["Copyright"], ""))
            return {
                "Title": title_value,
                "Description": description_value,
                "Keywords": keywords_value,
                "Creator": creator_value,
                "Credit": subject_value,
                "Source": subject_value,
                "Copyright": copyright_value,
            }

    def _read_png_editable_metadata(self, image_path: Path) -> dict[str, str]:
        from PIL import Image

        with Image.open(image_path) as image:
            image_info = image.info
            return {
                "Title": self._normalize_metadata_text(image_info.get("Title", "")),
                "Description": self._normalize_metadata_text(image_info.get("Description", "")),
                "Keywords": self._normalize_metadata_text(image_info.get("Keywords", "")),
                "Creator": self._normalize_metadata_text(image_info.get("Author", "")),
                "Credit": self._normalize_metadata_text(image_info.get("Credit", "")),
                "Source": self._normalize_metadata_text(image_info.get("Source", "")),
                "Copyright": self._normalize_metadata_text(image_info.get("Copyright", "")),
                "City": self._normalize_metadata_text(image_info.get("City", "")),
                "State": self._normalize_metadata_text(image_info.get("State", "")),
                "Country": self._normalize_metadata_text(image_info.get("Country", "")),
                "Rating": self._normalize_metadata_text(image_info.get("Rating", "0")),
            }

    def _write_xmp_sidecar(self, image_path: Path, key: str, value: str) -> None:
        xmp_property = self.FIELD_TO_XMP_PROP.get(key)
        if xmp_property is None:
            logger.debug("Skipping XMP write for unsupported field: %s", key)
            return

        sidecar_path = image_path.with_suffix(".xmp")
        root = self._load_or_create_xmp_tree(sidecar_path)
        description = self._get_xmp_description(root)
        self._set_xmp_value(description, xmp_property, value)
        tree = ET.ElementTree(root)
        tree.write(sidecar_path, encoding="utf-8", xml_declaration=True)

    def _load_or_create_xmp_tree(self, sidecar_path: Path) -> ET.Element:
        for prefix, namespace in self.XMP_NAMESPACES.items():
            ET.register_namespace(prefix, namespace)

        if sidecar_path.exists():
            tree = ET.parse(sidecar_path)
            return tree.getroot()

        root = ET.Element(f"{{{self.XMP_NAMESPACES['x']}}}xmpmeta")
        rdf = ET.SubElement(root, f"{{{self.XMP_NAMESPACES['rdf']}}}RDF")
        ET.SubElement(rdf, f"{{{self.XMP_NAMESPACES['rdf']}}}Description")
        return root

    def _get_xmp_description(self, root: ET.Element) -> ET.Element:
        rdf = root.find(f"./{{{self.XMP_NAMESPACES['rdf']}}}RDF")
        if rdf is None:
            rdf = ET.SubElement(root, f"{{{self.XMP_NAMESPACES['rdf']}}}RDF")
        description = rdf.find(f"./{{{self.XMP_NAMESPACES['rdf']}}}Description")
        if description is None:
            description = ET.SubElement(rdf, f"{{{self.XMP_NAMESPACES['rdf']}}}Description")
        return description

    def _set_xmp_value(self, description: ET.Element, xmp_property: str, value: str) -> None:
        value = self._normalize_metadata_text(value)
        namespace_prefix, property_name = xmp_property.split(":", maxsplit=1)
        namespace = self.XMP_NAMESPACES[namespace_prefix]
        qualified_name = f"{{{namespace}}}{property_name}"

        if xmp_property in ("dc:title", "dc:description", "dc:rights"):
            container = description.find(qualified_name)
            if container is None:
                container = ET.SubElement(description, qualified_name)
            alternative = container.find(f"./{{{self.XMP_NAMESPACES['rdf']}}}Alt")
            if alternative is None:
                alternative = ET.SubElement(container, f"{{{self.XMP_NAMESPACES['rdf']}}}Alt")
            item = alternative.find(f"./{{{self.XMP_NAMESPACES['rdf']}}}li")
            if item is None:
                item = ET.SubElement(alternative, f"{{{self.XMP_NAMESPACES['rdf']}}}li")
                item.set("{http://www.w3.org/XML/1998/namespace}lang", "x-default")
            item.text = value
            return

        if xmp_property in ("dc:subject", "dc:creator"):
            container = description.find(qualified_name)
            if container is None:
                container = ET.SubElement(description, qualified_name)
            sequence_tag = "Bag" if xmp_property == "dc:subject" else "Seq"
            sequence = container.find(f"./{{{self.XMP_NAMESPACES['rdf']}}}{sequence_tag}")
            if sequence is None:
                sequence = ET.SubElement(container, f"{{{self.XMP_NAMESPACES['rdf']}}}{sequence_tag}")
            for child in list(sequence):
                sequence.remove(child)
            values = [item.strip() for item in value.split(",") if item.strip()]
            for item_value in values or [""]:
                item = ET.SubElement(sequence, f"{{{self.XMP_NAMESPACES['rdf']}}}li")
                item.text = item_value
            return

        description.set(qualified_name, value)

    def _read_xmp_sidecar(self, image_path: Path) -> dict[str, str]:
        sidecar_path = image_path.with_suffix(".xmp")
        if not sidecar_path.exists():
            return {}
        try:
            root = ET.parse(sidecar_path).getroot()
            description = self._get_xmp_description(root)
            return {
                "Title": self._extract_xmp_lang_alt(description, "dc:title"),
                "Description": self._extract_xmp_lang_alt(description, "dc:description"),
                "Keywords": self._extract_xmp_array(description, "dc:subject"),
                "Creator": self._extract_xmp_array(description, "dc:creator"),
                "Copyright": self._extract_xmp_lang_alt(description, "dc:rights"),
                "Rating": self._extract_xmp_attr(description, "xmp:Rating"),
                "Source": self._extract_xmp_attr(description, "photoshop:Source"),
                "City": self._extract_xmp_attr(description, "photoshop:City"),
                "State": self._extract_xmp_attr(description, "photoshop:State"),
                "Country": self._extract_xmp_attr(description, "photoshop:Country"),
            }
        except Exception as error:
            logger.error("Failed to read XMP sidecar for %s: %s", image_path, error)
            return {}

    def _extract_xmp_attr(self, description: ET.Element, xmp_property: str) -> str:
        namespace_prefix, property_name = xmp_property.split(":", maxsplit=1)
        namespace = self.XMP_NAMESPACES[namespace_prefix]
        return self._normalize_metadata_text(description.get(f"{{{namespace}}}{property_name}", ""))

    def _extract_xmp_lang_alt(self, description: ET.Element, xmp_property: str) -> str:
        namespace_prefix, property_name = xmp_property.split(":", maxsplit=1)
        namespace = self.XMP_NAMESPACES[namespace_prefix]
        container = description.find(f"./{{{namespace}}}{property_name}")
        if container is None:
            return ""
        item = container.find(f"./{{{self.XMP_NAMESPACES['rdf']}}}Alt/{{{self.XMP_NAMESPACES['rdf']}}}li")
        return self._normalize_metadata_text(item.text if item is not None and item.text is not None else "")

    def _extract_xmp_array(self, description: ET.Element, xmp_property: str) -> str:
        namespace_prefix, property_name = xmp_property.split(":", maxsplit=1)
        namespace = self.XMP_NAMESPACES[namespace_prefix]
        container = description.find(f"./{{{namespace}}}{property_name}")
        if container is None:
            return ""
        array_element = container.find(f"./{{{self.XMP_NAMESPACES['rdf']}}}Bag")
        if array_element is None:
            array_element = container.find(f"./{{{self.XMP_NAMESPACES['rdf']}}}Seq")
        if array_element is None:
            return ""
        values = [item.text for item in array_element.findall(f"./{{{self.XMP_NAMESPACES['rdf']}}}li") if item.text]
        return self._normalize_metadata_text(", ".join(values))

    def _load_exif_data(self, image_path: Path) -> dict:
        """Load EXIF data from image file."""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS

            with Image.open(image_path) as image:
                exif_data = {}

                if hasattr(image, "_getexif") and image._getexif() is not None:
                    exif = image._getexif()

                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)

                        if tag == "GPSInfo":
                            gps_data = {}
                            for gps_tag_id, gps_value in value.items():
                                gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                gps_data[gps_tag] = gps_value
                            exif_data[tag] = gps_data
                        elif tag in ["Make", "Model", "DateTime", "ExposureTime", "FNumber", "ISOSpeedRatings", "FocalLength", "LensModel", "WhiteBalance", "Flash"]:
                            if isinstance(value, tuple) and len(value) > 1 and value[1] != 0:
                                exif_data[tag] = f"{value[0]}/{value[1]}"
                            else:
                                exif_data[tag] = str(value)

                return {
                    "Camera": f"{exif_data.get('Make', 'Unknown')} {exif_data.get('Model', 'Unknown')}".strip() or "Unknown",
                    "Lens": exif_data.get("LensModel", "Unknown"),
                    "ISO": str(exif_data.get("ISOSpeedRatings", "Unknown")),
                    "Aperture": f"f/{exif_data.get('FNumber', 'Unknown')}" if exif_data.get("FNumber") else "Unknown",
                    "Shutter Speed": exif_data.get("ExposureTime", "Unknown"),
                    "Focal Length": f"{exif_data.get('FocalLength', 'Unknown')}mm" if exif_data.get("FocalLength") else "Unknown",
                    "Flash": "On" if str(exif_data.get("Flash", "0")).isdigit() and int(str(exif_data.get("Flash", "0"))) & 1 else "Off",
                    "White Balance": exif_data.get("WhiteBalance", "Unknown"),
                    "Date Taken": exif_data.get("DateTime", "Unknown"),
                }
        except ImportError:
            logger.warning("Pillow not available, using fallback EXIF data")
            return self._get_fallback_exif_data(image_path)
        except Exception as error:
            logger.error("Error loading EXIF data: %s", error)
            return self._get_fallback_exif_data(image_path)

    def _get_fallback_exif_data(self, image_path: Path) -> dict:
        """Get fallback EXIF data when Pillow is not available."""
        try:
            stat_result = image_path.stat()
            return {
                "Camera": "Unknown",
                "Lens": "Unknown",
                "ISO": "Unknown",
                "Aperture": "Unknown",
                "Shutter Speed": "Unknown",
                "Focal Length": "Unknown",
                "Flash": "Unknown",
                "White Balance": "Unknown",
                "Date Taken": self._format_timestamp(stat_result.st_mtime),
            }
        except Exception:
            return {
                "Camera": "Unknown",
                "Lens": "Unknown",
                "ISO": "Unknown",
                "Aperture": "Unknown",
                "Shutter Speed": "Unknown",
                "Focal Length": "Unknown",
                "Flash": "Unknown",
                "White Balance": "Unknown",
                "Date Taken": "Unknown",
            }

    def _load_iptc_data(self, image_path: Path) -> dict:
        """Load IPTC data from image file."""
        iptc_data = {
            "Title": "",
            "Description": "",
            "Keywords": "",
            "Creator": "",
            "Credit": "",
            "Source": "",
            "Copyright": "",
            "City": "",
            "State": "",
            "Country": "",
            "Rating": "0",
        }
        suffix = image_path.suffix.lower()
        if suffix in self.RAW_WRITABLE_SUFFIXES:
            iptc_data.update(self._read_xmp_sidecar(image_path))
        elif suffix in self.EXIF_WRITABLE_SUFFIXES:
            iptc_data.update(self._read_exif_editable_metadata(image_path))
        elif suffix in self.PNG_WRITABLE_SUFFIXES:
            iptc_data.update(self._read_png_editable_metadata(image_path))
        return iptc_data
    
    def _on_image_clicked(self, image_path: Path, widget: QWidget) -> None:
        """Handle image click with selection highlighting"""
        self._select_image(image_path)
        self._load_image_metadata(image_path)
    
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Track resize/show events that affect grid geometry."""
        scroll_area = getattr(self, "scroll_area", None)
        
        if watched in (self, scroll_area):
            if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
                self._queue_grid_layout_update()
        return super().eventFilter(watched, event)

    def _queue_grid_layout_update(self) -> None:
        """Debounce frequent geometry updates into one grid recalculation."""
        if not hasattr(self, "resize_timer") or self.resize_timer is None:
            return
        self.resize_timer.start(self.GRID_LAYOUT_UPDATE_DELAY_MS)

    def _update_icon_metrics(self, column_count: Optional[int] = None) -> None:
        """Backward-compatible entrypoint for grid metric updates."""
        self._apply_grid_layout(column_count)

    def _update_cell_sizes(self) -> None:
        """Backward-compatible wrapper for legacy call sites."""
        self._apply_grid_layout()

    def _apply_grid_layout(self, column_count: Optional[int] = None) -> None:
        """Apply pixel-perfect grid layout with fixed left/right edges.
        
        Strategy: Calculate exact cell width and spacing to fill the viewport
        completely, with fixed left/right margins. The GridImageWidget gives
        us full control over positioning.
        """
        if not self.grid_widget or not self.scroll_area:
            return
        
        columns = max(self.MIN_GRID_COLUMNS, column_count or self.grid_columns)
        
        # Get available width (scroll area viewport minus scrollbar)
        viewport = self.scroll_area.viewport()
        viewport_width = viewport.width()
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar_width = scrollbar.width() if scrollbar.isVisible() else scrollbar.sizeHint().width()
        
        available_width = viewport_width - scrollbar_width
        if available_width <= 0:
            return
        
        # Fixed margins on left and right
        left_margin = self.GRID_LEFT_PADDING
        right_margin = self.GRID_RIGHT_PADDING
        
        # Calculate content area
        content_width = available_width - left_margin - right_margin
        gap_count = max(0, columns - 1)
        
        # Search for optimal cell_width + spacing combination
        best_solution = None
        min_spacing = self.GRID_MIN_SPACING
        max_spacing = self.GRID_SPACING + self.GRID_MAX_SPACING_DELTA
        
        for spacing in range(min_spacing, max_spacing + 1):
            total_spacing = gap_count * spacing
            available_for_cells = content_width - total_spacing
            if available_for_cells < columns * self.GRID_MIN_CELL_SIZE:
                continue
            
            cell_width = available_for_cells // columns
            actual_width = cell_width * columns + total_spacing
            remainder = content_width - actual_width
            
            # Score: prefer zero remainder, then larger cells, then spacing close to default
            score = (remainder, -cell_width, abs(spacing - self.GRID_SPACING))
            
            if best_solution is None or score < best_solution[0]:
                best_solution = (score, cell_width, spacing, remainder)
                if remainder == 0:
                    break
        
        if best_solution is None:
            # Fallback
            spacing = self.GRID_SPACING
            total_spacing = gap_count * spacing
            cell_width = max(self.GRID_MIN_CELL_SIZE, (content_width - total_spacing) // columns)
            remainder = 0
        else:
            cell_width = best_solution[1]
            spacing = best_solution[2]
            remainder = best_solution[3]
        
        # Calculate cell height
        cell_side = max(1, cell_width - (self.GRID_CARD_MARGIN * 2))
        cell_height = cell_side + self.GRID_FILENAME_HEIGHT + (self.GRID_CARD_MARGIN * 2)
        
        # Debug logging
        actual_grid_width = cell_width * columns + gap_count * spacing
        logger.debug(
            f"[GRID] cols={columns}, available={available_width}, content={content_width}, "
            f"cell={cell_width}x{cell_height}, spacing={spacing}, "
            f"grid_width={actual_grid_width}, remainder={remainder}, "
            f"margins=L{left_margin}+R{right_margin}"
        )
        
        # Apply layout to grid widget
        self.grid_widget.set_grid_layout(
            columns=columns,
            cell_width=cell_width,
            cell_height=cell_height,
            spacing=spacing,
            left_margin=left_margin,
            right_margin=right_margin
        )
        
        self.grid_widget.set_cell_metrics(
            card_margin=self.GRID_CARD_MARGIN,
            filename_height=self.GRID_FILENAME_HEIGHT,
            image_padding=self.GRID_IMAGE_INNER_PADDING
        )
        
        self.current_icon_size = max(1, cell_side - (self.GRID_IMAGE_INNER_PADDING * 2))
    
