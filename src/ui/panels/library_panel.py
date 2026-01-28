"""Library Panel for Photo Editor.

Handles photo library management with folder tree and metadata.
Includes threaded image loading with cancellation and detailed logging.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import time
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QListView, QScrollArea, QWidget, QFrame,
    QSplitter, QLineEdit, QSpinBox, QFormLayout, QGroupBox, QCheckBox,
    QGridLayout, QTextEdit, QSizePolicy, QPushButton, QProgressBar,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QDir, QFileSystemWatcher, QSize, QTimer, QThread, pyqtSignal, QThreadPool, QRunnable, QObject, QEvent
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QIcon, QImage, QImageReader

from src.config.config_manager import ConfigManager
from src.ui.widgets.image_list_model import ImageListModel
from src.ui.widgets.image_item_delegate import ImageItemDelegate
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
    
    def __init__(self):
        super().__init__("library")
        self.current_folder: Optional[Path] = None
        self.image_files: List[Path] = []
        self.selected_image: Optional[Path] = None
        self.grid_columns = 5
        self.recursive_loading = False
        self.config_manager = ConfigManager()
        self.image_model = ImageListModel()
        self.image_list_view: Optional[QListView] = None
        self.image_delegate: Optional[ImageItemDelegate] = None
        self.current_icon_size = 140
        self.metadata_widgets = {}  # Store metadata edit widgets
        
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
        
        # Setup resize timer for dynamic cell sizing
        self.resize_timer = QTimer()
        self.resize_timer.timeout.connect(self._update_cell_sizes)
        self.resize_timer.setSingleShot(True)
        
        # Setup UI update timer for continuous image display
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self._continuous_ui_update)
        self.ui_update_timer.setSingleShot(True)
    
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
        
        # Connect resize event and splitter change event
        self.resizeEvent = self._on_resize_event
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
        
        self.columns_spinbox = QSpinBox()
        self.columns_spinbox.setRange(1, 10)
        self.columns_spinbox.setValue(self.grid_columns)
        self.columns_spinbox.valueChanged.connect(self._on_columns_changed)
        controls_layout.addWidget(self.columns_spinbox)
        
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
        
        # QListView-based grid
        self.image_list_view = QListView()
        self.image_list_view.setFrameShape(QFrame.Shape.NoFrame)
        self.image_list_view.setContentsMargins(0, 0, 0, 0)
        self.image_list_view.setViewportMargins(0, 0, 0, 0)
        self.image_list_view.setViewMode(QListView.ViewMode.IconMode)
        self.image_list_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.image_list_view.setMovement(QListView.Movement.Static)
        self.image_list_view.setSpacing(2)
        self.image_list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.image_list_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.image_list_view.setLayoutMode(QListView.LayoutMode.SinglePass)
        self.image_list_view.setFlow(QListView.Flow.LeftToRight)
        self.image_list_view.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.image_list_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.image_list_view.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.image_list_view.verticalScrollBar().setSingleStep(20)
        self.image_list_view.verticalScrollBar().setPageStep(200)
        self.image_list_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.image_list_view.setSelectionRectVisible(False)
        self.image_list_view.setUniformItemSizes(False)
        self.image_list_view.setMouseTracking(True)
        self.image_list_view.setWordWrap(True)
        self.image_list_view.setWrapping(True)
        self.image_list_view.setStyleSheet("""
            QListView {
                background-color: rgb(35, 35, 40);
                border: none;
            }
        """)
        self.image_delegate = ImageItemDelegate(self.image_list_view)
        self.image_list_view.setItemDelegate(self.image_delegate)
        self.image_list_view.setModel(self.image_model)
        self.image_list_view.selectionModel().selectionChanged.connect(self._on_view_selection_changed)
        middle_layout.addWidget(self.image_list_view)
        self._update_icon_metrics()

        parent.addWidget(middle_widget)
    
    def _setup_metadata_panel(self, parent: QSplitter) -> None:
        """Setup metadata panel"""
        logger.debug("Setting up metadata panel...")
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Title
        title = QLabel("Metadata")
        title.setStyleSheet("font-weight: bold; color: white; padding: 5px;")
        right_layout.addWidget(title)
        
        # Scroll area for metadata
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.metadata_widget = QWidget()
        self.metadata_layout = QVBoxLayout(self.metadata_widget)  # Changed to QVBoxLayout
        
        # Add empty placeholder message
        placeholder_label = QLabel("Select an image to view metadata")
        placeholder_label.setStyleSheet("""
            QLabel {
                color: rgb(120, 120, 120);
                font-size: 14px;
                padding: 20px;
                text-align: center;
            }
        """)
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.metadata_layout.addWidget(placeholder_label)
        
        scroll_area.setWidget(self.metadata_widget)
        
        right_layout.addWidget(scroll_area)
        
        parent.addWidget(right_widget)
        logger.debug("Metadata panel setup complete.")
    
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
            logger.debug(f"Toggle clicked for {title}")
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
        # Load only home directory for now to avoid performance issues
        home = Path.home()
        
        # Just add home directory initially, subdirectories will be loaded on demand
        self._add_folder_item(home, None)
        
        # Add common photo directories as top-level items
        common_dirs = [
            home / "Pictures",
            home / "Desktop",
            home / "Documents",
        ]
        
        for dir_path in common_dirs:
            if dir_path.exists() and dir_path != home:
                self._add_folder_item(dir_path, None)
    
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
        self.image_model.clear_images()
        self.image_files.clear()
        self.selected_image = None
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
        if self.image_list_view:
            self.image_list_view.viewport().update()
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
        if self.is_loading and self.image_list_view:
            self.image_list_view.viewport().update()
            QApplication.processEvents()
            if self.is_loading:
                self.ui_update_timer.start(30)
        else:
            self.ui_update_timer.stop()

    def _add_image_to_grid(self, image_path: Path, image: Optional[QImage] = None) -> None:
        """Add image thumbnail to the QListView model."""
        pixmap = self._create_thumbnail_pixmap(image_path, image)
        item = self.image_model.add_image(image_path, pixmap)
        self.image_files.append(image_path)
        if len(self.image_files) == 1:
            self._update_icon_metrics()
        if self.selected_image == image_path:
            self._select_item(item)

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

    def _on_view_selection_changed(self, selected, deselected) -> None:
        """React to QListView selection changes."""
        if not selected.indexes():
            return
        index = selected.indexes()[0]
        path_value = index.data(ImageListModel.PATH_ROLE)
        if not path_value:
            return
        image_path = Path(path_value)
        if self.selected_image == image_path:
            return
        self.selected_image = image_path
        self._load_image_metadata(image_path)

    def _select_image(self, image_path: Path) -> None:
        """Select the given image path in the view."""
        if not self.image_list_view:
            return
        item = self.image_model.get_item(image_path)
        if not item:
            self.selected_image = image_path
            return
        self._select_item(item)

    def _select_item(self, item) -> None:
        if not self.image_list_view:
            return
        index = self.image_model.indexFromItem(item)
        if not index.isValid():
            return
        from PyQt6.QtCore import QItemSelectionModel
        selection_model = self.image_list_view.selectionModel()
        if selection_model:
            selection_model.setCurrentIndex(index, QItemSelectionModel.ClearAndSelect)
        self.image_list_view.scrollTo(index, QListView.ScrollHint.PositionAtCenter)
        path_value = item.data(ImageListModel.PATH_ROLE)
        if path_value:
            self.selected_image = Path(path_value)
    
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
        # Only need to recompute the view cell sizes; the QListView will
        # automatically reflow items according to the new column count.
        self._update_cell_sizes()
        self.logger.info(f"Grid columns changed to: {value}")
    
    def _on_resize_event(self, event) -> None:
        """Handle window resize event"""
        # Start timer to update cell sizes after resize is complete
        self.resize_timer.start(100)  # 100ms delay
    
    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """Handle splitter moved event"""
        # Start timer to update cell sizes after splitter movement is complete
        self.resize_timer.start(100)  # 100ms delay
    
    def _load_image_metadata(self, image_path: Path) -> None:
        """Load and display image metadata with editable fields"""
        print(f"Loading metadata for: {image_path.name}")  # Debug
        
        # Clear existing metadata
        for i in reversed(range(self.metadata_layout.count())):
            self.metadata_layout.itemAt(i).widget().setParent(None)
        
        self.metadata_widgets.clear()
        
        # File information (read-only)
        file_data = {
            "Filename": image_path.name,
            "Path": str(image_path.parent),
            "Size": self._format_file_size(image_path.stat().st_size),
            "Modified": self._format_timestamp(image_path.stat().st_mtime),
        }
        file_group = self._create_simple_collapsible_group("File Information", file_data)
        self.metadata_layout.addWidget(file_group)
        
        # Load EXIF data
        exif_data = self._load_exif_data(image_path)
        exif_group = self._create_simple_collapsible_group("EXIF Data", exif_data)
        self.metadata_layout.addWidget(exif_group)
        
        # Load IPTC data
        iptc_data = self._load_iptc_data(image_path)
        iptc_group = self._create_simple_collapsible_group("IPTC Data", iptc_data)
        self.metadata_layout.addWidget(iptc_group)
        
        print(f"Metadata loaded for: {image_path.name}")  # Debug
    
    def _load_exif_data(self, image_path: Path) -> dict:
        """Load EXIF data from image file"""
        try:
            # Try to use Pillow to read EXIF data
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            
            with Image.open(image_path) as img:
                exif_data = {}
                
                # Get EXIF data
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        # Convert GPS data
                        if tag == "GPSInfo":
                            gps_data = {}
                            for gps_tag_id, gps_value in value.items():
                                gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                gps_data[gps_tag] = gps_value
                            exif_data[tag] = gps_data
                        else:
                            # Format some common EXIF tags
                            if tag in ["Make", "Model", "DateTime", "ExposureTime", "FNumber", "ISOSpeedRatings", "FocalLength"]:
                                if isinstance(value, tuple) and len(value) > 1 and value[1] != 0:
                                    # Handle rational numbers (e.g., exposure time, f-number)
                                    formatted_value = f"{value[0]}/{value[1]}"
                                else:
                                    formatted_value = str(value)
                                exif_data[tag] = formatted_value
                
                # Map EXIF tags to user-friendly names
                mapped_data = {
                    "Camera": f"{exif_data.get('Make', 'Unknown')} {exif_data.get('Model', 'Unknown')}".strip() or "Unknown",
                    "Lens": exif_data.get("LensModel", "Unknown"),
                    "ISO": str(exif_data.get("ISOSpeedRatings", "Unknown")),
                    "Aperture": f"f/{exif_data.get('FNumber', 'Unknown')}" if exif_data.get('FNumber') else "Unknown",
                    "Shutter Speed": exif_data.get("ExposureTime", "Unknown"),
                    "Focal Length": f"{exif_data.get('FocalLength', 'Unknown')}mm" if exif_data.get('FocalLength') else "Unknown",
                    "Flash": "On" if exif_data.get("Flash", 0) & 1 else "Off",
                    "White Balance": exif_data.get("WhiteBalance", "Unknown"),
                    "Date Taken": exif_data.get("DateTime", "Unknown"),
                }
                
                return mapped_data
                
        except ImportError:
            # Pillow not available, use fallback
            self.logger.warning("Pillow not available, using fallback EXIF data")
            return self._get_fallback_exif_data(image_path)
        except Exception as e:
            self.logger.error(f"Error loading EXIF data: {e}")
            return self._get_fallback_exif_data(image_path)
    
    def _get_fallback_exif_data(self, image_path: Path) -> dict:
        """Get fallback EXIF data when Pillow is not available"""
        try:
            # Use basic file info as fallback
            stat = image_path.stat()
            return {
                "Camera": "Unknown",
                "Lens": "Unknown", 
                "ISO": "Unknown",
                "Aperture": "Unknown",
                "Shutter Speed": "Unknown",
                "Focal Length": "Unknown",
                "Flash": "Unknown",
                "White Balance": "Unknown",
                "Date Taken": self._format_timestamp(stat.st_mtime),
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
        """Load IPTC data from image file"""
        # Placeholder IPTC data - in real implementation, use libraries like iptcinfo3
        return {
            "Title": "",
            "Description": "",
            "Keywords": "",
            "Copyright": "",
            "Creator": "",
            "Credit": "",
            "Source": "",
            "City": "",
            "State": "",
            "Country": "",
            "Rating": "0",
        }
    
    def _add_metadata_group(self, title: str, data: dict, editable: bool = True) -> None:
        """Add metadata group to panel with editable fields"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 1px solid rgb(60, 60, 65);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QFormLayout(group)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 15, 10, 10)
        
        for key, value in data.items():
            if editable:
                # Create editable field
                if key in ["Description"]:
                    # Multi-line text for description
                    edit_widget = QTextEdit()
                    edit_widget.setPlainText(str(value))
                    edit_widget.setMaximumHeight(80)
                    edit_widget.setStyleSheet("""
                        QTextEdit {
                            background-color: rgb(45, 45, 50);
                            color: white;
                            border: 1px solid rgb(60, 60, 65);
                            border-radius: 3px;
                            padding: 5px;
                            font-family: monospace;
                        }
                    """)
                    # Connect text change signal
                    edit_widget.textChanged.connect(
                        lambda text=edit_widget.toPlainText, k=key: self._on_metadata_changed(k, text())
                    )
                elif key in ["Rating"]:
                    # Spinbox for rating
                    edit_widget = QSpinBox()
                    edit_widget.setRange(0, 5)
                    edit_widget.setValue(int(str(value)) if str(value).isdigit() else 0)
                    edit_widget.setStyleSheet("""
                        QSpinBox {
                            background-color: rgb(45, 45, 50);
                            color: white;
                            border: 1px solid rgb(60, 60, 65);
                            border-radius: 3px;
                            padding: 5px;
                        }
                    """)
                    # Connect value change signal
                    edit_widget.valueChanged.connect(
                        lambda v, k=key: self._on_metadata_changed(k, str(v))
                    )
                else:
                    # Single line text edit
                    edit_widget = QLineEdit()
                    edit_widget.setText(str(value))
                    edit_widget.setStyleSheet("""
                        QLineEdit {
                            background-color: rgb(45, 45, 50);
                            color: white;
                            border: 1px solid rgb(60, 60, 65);
                            border-radius: 3px;
                            padding: 5px;
                        }
                    """)
                    # Connect text change signal
                    edit_widget.textChanged.connect(
                        lambda text=edit_widget.text, k=key: self._on_metadata_changed(k, text())
                    )
                
                self.metadata_widgets[key] = edit_widget
                layout.addRow(QLabel(f"{key}:"), edit_widget)
            else:
                # Read-only label
                label = QLabel(str(value))
                label.setStyleSheet("""
                    QLabel {
                        color: rgb(200, 200, 200);
                        padding: 5px;
                        font-family: monospace;
                    }
                """)
                label.setWordWrap(True)
                layout.addRow(QLabel(f"{key}:"), label)
        
        self.metadata_layout.addWidget(group)
    
    def _on_metadata_changed(self, key: str, value: str) -> None:
        """Handle metadata field change"""
        if self.selected_image:
            self.logger.info(f"Metadata changed for {self.selected_image.name}: {key} = {value}")
            # In real implementation, save the metadata to the image file
            # For now, just log the change
    
    def _on_image_clicked(self, image_path: Path, widget: QWidget) -> None:
        """Handle image click with selection highlighting"""
        self._select_image(image_path)
        self._load_image_metadata(image_path)
    
    def _update_cell_sizes(self) -> None:
        """Update cell sizes based on available space"""
        if not self.image_list_view:
            return
        viewport_rect = self.image_list_view.viewport().contentsRect()
        available_width = viewport_rect.width()
        if available_width <= 0:
            return
        spacing = self.image_list_view.spacing() if hasattr(self.image_list_view, "spacing") else 0
        columns = max(1, self.grid_columns)
        # Osszuk el a teljes szélességet a kívánt oszlopszámmal, figyelembe véve
        # az oszlopok közötti spacinget. Így pontosan annyi oszlop fér ki,
        # amennyit a spinbox mutat.
        effective_width = max(0, available_width - max(0, columns - 1) * spacing)
        # Pixelpontos számolás: a viewport kliens területéből (scrollbar és frame
        # nélkül) képezzük a cellaszélességet, hogy pontosan N oszlop kiférjen.
        cell_width = max(effective_width // columns, 50)

        # Thumbnail terület legyen legalább 1:1 (négyzet), plusz alul a fájlnév.
        icon_padding = 12
        icon_size = max(80, cell_width - icon_padding)

        filename_height = 26
        vertical_padding = 10
        # Minimum 1:1 cella (a kép négyzetes területe a cell_width-hoz igazodik)
        cell_height = max(icon_size, cell_width) + filename_height + vertical_padding

        self.current_icon_size = icon_size
        self.logger.debug(
            "[LIB][SIZE] viewport=%s, columns=%s, spacing=%s, cell_width=%s, icon_size=%s, cell_height=%s",
            available_width,
            columns,
            spacing,
            cell_width,
            icon_size,
            cell_height,
        )
        self._update_icon_metrics(column_count=self.grid_columns)

    def _update_icon_metrics(self, column_count: Optional[int] = None) -> None:
        """Update QListView grid size based on current icon size and column count."""
        if not self.image_list_view or not self.image_delegate:
            return
        columns = column_count or self.grid_columns
        columns = max(1, columns)

        viewport_rect = self.image_list_view.viewport().contentsRect()
        available_width = viewport_rect.width()
        if available_width <= 0:
            return
        spacing = self.image_list_view.spacing() if hasattr(self.image_list_view, "spacing") else 0
        effective_width = max(0, available_width - max(0, columns - 1) * spacing)
        cell_width = max(effective_width // columns, 50)

        filename_height = 26
        vertical_padding = 10
        cell_height = max(self.current_icon_size, cell_width) + filename_height + vertical_padding

        grid_size = QSize(cell_width, cell_height)
        self.image_list_view.setIconSize(QSize(self.current_icon_size, self.current_icon_size))
        self.image_list_view.setGridSize(grid_size)
        self.image_list_view.updateGeometry()
        logger.debug(
            "[LIB][GRID] viewport=%s, columns=%s, spacing=%s, cell_width=%s, cell_height=%s, icon=%s",
            available_width,
            columns,
            spacing,
            cell_width,
            cell_height,
            self.current_icon_size,
        )
    
