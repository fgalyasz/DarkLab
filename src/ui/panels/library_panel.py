"""
Library Panel for Photo Editor
Handles photo library management with folder tree and metadata
"""

import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QScrollArea, QWidget, QFrame,
    QSplitter, QLineEdit, QSpinBox, QFormLayout, QGroupBox, QCheckBox,
    QGridLayout, QTextEdit, QSizePolicy, QPushButton
)
from PyQt6.QtCore import Qt, QDir, QFileSystemWatcher, QSize, QTimer
from PyQt6.QtGui import QPixmap, QIcon

from src.config.config_manager import ConfigManager
from .base_panel import BasePanel


class CollapsibleGroupBox(QWidget):
    """Custom collapsible group box for metadata sections"""
    
    def __init__(self, title: str, parent=None):
        print(f"Creating CollapsibleGroupBox with title: {title}")  # Debug
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
            
            print(f"CollapsibleGroupBox created successfully: {title}")  # Debug
        except Exception as e:
            print(f"Error creating CollapsibleGroupBox: {e}")  # Debug
    
    def toggle(self):
        """Toggle collapsed state"""
        print(f"Toggle called, current state: {self.is_collapsed}")  # Debug
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.content_widget.hide()
            self.toggle_button.setText("▶")
            self.setFixedHeight(30)  # Only header height
            print("Collapsed")  # Debug
        else:
            self.content_widget.show()
            self.toggle_button.setText("▼")
            self.setMaximumHeight(16777215)  # Remove height limit
            # Update size after showing content
            self.updateGeometry()
            print("Expanded")  # Debug
    
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
        self.image_widgets = {}  # Store image widgets for selection
        self.metadata_widgets = {}  # Store metadata edit widgets
        
        # Override the default setup
        self._setup_library_ui()
        
        # Setup resize timer for dynamic cell sizing
        self.resize_timer = QTimer()
        self.resize_timer.timeout.connect(self._update_cell_sizes)
        self.resize_timer.setSingleShot(True)
    
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
        print("About to setup metadata panel...")  # Debug
        self._setup_metadata_panel(main_splitter)
        print("Metadata panel setup completed.")  # Debug
        
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
        middle_layout.addLayout(controls_layout)
        
        # Scroll area for grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Grid container widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)  # No spacing - widget borders handle separation
        self.grid_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        self.grid_widget.setLayout(self.grid_layout)
        self.grid_widget.setStyleSheet("""
            QWidget {
                background-color: rgb(35, 35, 40);  # Panel background color
            }
        """)
        self.grid_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred
        )
        
        scroll_area.setWidget(self.grid_widget)
        middle_layout.addWidget(scroll_area)
        
        # Store reference for updates
        self.image_grid_container = scroll_area
        
        parent.addWidget(middle_widget)
    
    def _setup_metadata_panel(self, parent: QSplitter) -> None:
        """Setup metadata panel"""
        print("Setting up metadata panel...")  # Debug
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
        
        # Add some test metadata to show collapsible groups
        print("Adding test metadata groups...")  # Debug
        
        # Try adding a simple group first
        try:
            print("Creating simple test group...")  # Debug
            simple_widget = QWidget()
            simple_widget.setStyleSheet("background-color: red; border: 1px solid white;")
            simple_widget.setFixedHeight(50)
            simple_label = QLabel("TEST GROUP")
            simple_label.setStyleSheet("color: white; font-size: 12px;")
            simple_layout = QVBoxLayout(simple_widget)
            simple_layout.addWidget(simple_label)
            self.metadata_layout.addWidget(simple_widget)
            print("Simple test group added successfully")  # Debug
        except Exception as e:
            print(f"Error adding simple test group: {e}")  # Debug
        
        # Now add simple collapsible groups
        print("Adding simple collapsible groups...")  # Debug
        
        # File Information group
        try:
            file_group = self._create_simple_collapsible_group("File Information", {
                "Filename": "test.jpg",
                "Path": "/path/to/test.jpg",
                "Size": "2.5 MB",
                "Modified": "2024.01.01. 12:00:00"
            })
            self.metadata_layout.addWidget(file_group)
            print("File Information group added")  # Debug
        except Exception as e:
            print(f"Error adding File Information group: {e}")  # Debug
        
        # EXIF Data group
        try:
            exif_group = self._create_simple_collapsible_group("EXIF Data", {
                "Camera": "Canon EOS R5",
                "Lens": "RF 24-70mm f/2.8L IS USM",
                "Focal Length": "50mm",
                "Aperture": "f/2.8",
                "Shutter Speed": "1/125",
                "ISO": "400"
            })
            self.metadata_layout.addWidget(exif_group)
            print("EXIF Data group added")  # Debug
        except Exception as e:
            print(f"Error adding EXIF Data group: {e}")  # Debug
        
        # IPTC Data group
        try:
            iptc_group = self._create_simple_collapsible_group("IPTC Data", {
                "Title": "Test Photo",
                "Description": "This is a test photo description",
                "Keywords": "test, photo, sample",
                "Copyright": "© 2024 Test"
            })
            self.metadata_layout.addWidget(iptc_group)
            print("IPTC Data group added")  # Debug
        except Exception as e:
            print(f"Error adding IPTC Data group: {e}")  # Debug
        
        print("Finished adding test metadata groups.")  # Debug
        
        scroll_area.setWidget(self.metadata_widget)
        
        right_layout.addWidget(scroll_area)
        
        parent.addWidget(right_widget)
        print("Metadata panel setup complete.")  # Debug
    
    def _create_simple_collapsible_group(self, title: str, data: dict) -> QWidget:
        """Create a simple collapsible group widget"""
        print(f"Creating simple collapsible group: {title}")  # Debug
        
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
            print(f"Toggle clicked for {title}")  # Debug
            if content_widget.isVisible():
                content_widget.hide()
                toggle_button.setText("▶")
                group_widget.setFixedHeight(30)
                print(f"Collapsed {title}")  # Debug
            else:
                content_widget.show()
                toggle_button.setText("▼")
                group_widget.setMaximumHeight(16777215)
                print(f"Expanded {title}")  # Debug
        
        toggle_button.mousePressEvent = lambda e: toggle_content()
        
        # Assemble
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(toggle_button)
        
        group_layout.addWidget(header_widget)
        group_layout.addWidget(content_widget)
        
        print(f"Simple collapsible group created: {title}")  # Debug
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
        print(f"Recursive toggled: {checked}")  # Debug
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
                        print("Loading recursively")  # Debug
                        self._load_subdirectories_recursive(folder_path, current_item)
                    else:
                        print("Loading non-recursively")  # Debug
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
        print(f"Folder expanded: {item.text(0)}")  # Debug
        
        folder_path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if not folder_path_str:
            print("No folder path data found")  # Debug
            return
        
        folder_path = Path(folder_path_str)
        if not folder_path.is_dir():
            print(f"Folder path is not a directory: {folder_path}")  # Debug
            return
        
        print(f"Loading subdirectories for: {folder_path}")  # Debug
        
        # Remove dummy items (items with no UserRole data)
        removed_count = 0
        for i in reversed(range(item.childCount())):
            child = item.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole) is None:
                item.removeChild(child)
                removed_count += 1
        
        print(f"Removed {removed_count} dummy items")  # Debug
        
        # Load subdirectories (always load on expansion)
        print("Loading subdirectories on expansion")  # Debug
        try:
            loaded_count = 0
            for subpath in sorted(folder_path.iterdir()):
                if subpath.is_dir() and not subpath.name.startswith('.'):
                    self._add_folder_item(subpath, item)
                    loaded_count += 1
            
            print(f"Loaded {loaded_count} subdirectories")  # Debug
        except (PermissionError, OSError) as e:
            print(f"Error loading subdirectories: {e}")  # Debug
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
        """Load images from selected folder"""
        if not self.current_folder:
            return
        
        self.image_files.clear()
        self.image_widgets.clear()
        
        # Clear grid layout
        for i in reversed(range(self.grid_layout.count())):
            child = self.grid_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Supported image extensions
        image_extensions = {
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif',
            '.raw', '.cr2', '.nef', '.arw', '.orf', '.rw2', '.dng'
        }
        
        # Load images from current folder and optionally from subfolders
        def load_images_from_path(path: Path):
            try:
                for file_path in sorted(path.iterdir()):
                    # Skip hidden files
                    if file_path.name.startswith('.'):
                        continue
                    
                    # Handle directories for recursive loading
                    if file_path.is_dir():
                        if self.recursive_loading:
                            # Recursively load from subfolders
                            load_images_from_path(file_path)
                        continue
                    
                    # Only process supported image files
                    if file_path.suffix.lower() in image_extensions:
                        # Double-check it's actually a file and not a special entry
                        if file_path.is_file() and file_path.exists():
                            self._add_image_to_grid(file_path)
            except PermissionError:
                pass
        
        load_images_from_path(self.current_folder)
        
        # Add spacer at bottom to prevent stretching
        self._add_bottom_spacer()
        
        # Update cell sizes after loading images
        self._update_cell_sizes()
    
    def _add_bottom_spacer(self) -> None:
        """Add spacer at bottom of grid to prevent stretching"""
        if not self.image_files:
            return
        
        # Calculate current grid layout
        rows = (len(self.image_files) + self.grid_columns - 1) // self.grid_columns
        
        # Add vertical spacer in the last row to prevent stretching
        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        spacer.setStyleSheet("background-color: transparent;")
        
        # Add spacer to each column in the last row
        for col in range(self.grid_columns):
            self.grid_layout.addWidget(spacer, rows, col)
    
    def _add_image_to_grid(self, image_path: Path) -> None:
        """Add image to grid with custom widget for consistent text positioning"""
        # Calculate icon size based on column count
        if self.grid_columns <= 2:
            icon_size = 180
        elif self.grid_columns <= 4:
            icon_size = 160
        elif self.grid_columns <= 6:
            icon_size = 140
        else:
            icon_size = 120
        
        # Calculate lighter background color (25% lighter than panel color)
        panel_color = (35, 35, 40)  # rgb(35, 35, 40)
        lighter_color = tuple(min(255, int(c + (255 - c) * 0.25)) for c in panel_color)
        lighter_color_str = f"rgb({lighter_color[0]}, {lighter_color[1]}, {lighter_color[2]})"
        
        # Create custom widget for each image
        image_widget = QWidget()
        image_widget.setFixedSize(icon_size + 30, icon_size + 30)
        image_widget.setStyleSheet(f"""
            QWidget {{
                border: 1px solid rgb(35, 35, 40);
                border-radius: 0px;
                background-color: {lighter_color_str};
                margin: 0px;
                padding: 0px;
            }}
            QWidget:hover {{
                border: 1px solid rgb(35, 35, 40);
                background-color: rgb(55, 55, 60);
            }}
        """)
        
        # Create selection overlay widget
        selection_overlay = QWidget(image_widget)
        selection_overlay.setGeometry(0, 0, icon_size + 30, icon_size + 30)
        selection_overlay.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        selection_overlay.hide()  # Initially hidden
        
        layout = QVBoxLayout(image_widget)
        layout.setContentsMargins(10, 10, 10, 10)  # 10px margin inside widget
        layout.setSpacing(0)  # No spacing between elements
        
        # Add vertical spacer to center the image
        layout.addStretch()
        
        # Image label in center
        image_label = QLabel()
        # Calculate available space for image (cell height minus filename and margins)
        available_height = (icon_size + 30) - 20 - 10  # Total height - filename height - margins
        image_size = min(icon_size, available_height)
        image_label.setMinimumSize(image_size, image_size)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet(f"""
            QLabel {{
                background-color: {lighter_color_str};
                border: none;
                border-radius: 0px;
            }}
        """)
        
        # Try to load thumbnail
        try:
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                # Scale to fit while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    image_size - 2,
                    image_size - 2,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                image_label.setPixmap(scaled_pixmap)
            else:
                # For RAW files, show placeholder
                image_label.setText("RAW")
                image_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {lighter_color_str};
                        border: none;
                        border-radius: 0px;
                        color: rgb(180, 180, 180);
                    }}
                """)
        except Exception:
            # Fallback for unsupported formats
            image_label.setText("N/A")
            image_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {lighter_color_str};
                    border: none;
                    border-radius: 0px;
                    color: rgb(180, 180, 180);
                }}
            """)
        
        layout.addWidget(image_label)
        
        # Add vertical spacer to center the image
        layout.addStretch()
        
        # Filename label at bottom - use simple text widget to avoid border
        filename_widget = QWidget()
        filename_widget.setFixedHeight(20)
        filename_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)
        
        # Create layout for filename widget
        filename_layout = QVBoxLayout(filename_widget)
        filename_layout.setContentsMargins(0, 0, 0, 0)
        filename_layout.setSpacing(0)
        
        # Create filename label
        filename_label = QLabel(image_path.name)
        filename_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                background-color: transparent;
                padding: 2px;
                font-weight: bold;
                border: none;
            }
        """)
        filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename_label.setWordWrap(True)
        
        filename_layout.addWidget(filename_label)
        
        layout.addWidget(filename_widget)
        
        # Add to grid layout
        row = (len(self.image_files)) // self.grid_columns
        col = (len(self.image_files)) % self.grid_columns
        self.grid_layout.addWidget(image_widget, row, col)
        
        # Add to list AFTER adding to grid
        self.image_files.append(image_path)
        
        # Store widget and overlay for selection
        self.image_widgets[str(image_path)] = {
            'widget': image_widget,
            'overlay': selection_overlay,
            'filename_widget': filename_widget,
            'filename_label': filename_label,
            'image_label': image_label
        }
        
        # Make widget clickable
        image_widget.mousePressEvent = lambda e: self._on_image_clicked(image_path, image_widget)
    
    def _on_image_clicked(self, image_path: Path, widget: QWidget) -> None:
        """Handle image click with selection highlighting"""
        print(f"Image clicked: {image_path.name}")  # Debug
        self.selected_image = image_path
        self._load_image_metadata(image_path)
        
        # Update all widget styles to show selection
        for path, widgets in self.image_widgets.items():
            # Update filename label
            filename_label = widgets['filename_label']
            if filename_label:
                if path == image_path:
                    filename_label.setStyleSheet("""
                        QLabel {
                            color: white;
                            font-size: 12px;
                            background-color: transparent;
                            padding: 2px;
                            font-weight: bold;
                            text-decoration: underline;
                            border: none;
                        }
                    """)
                else:
                    filename_label.setStyleSheet("""
                        QLabel {
                            color: white;
                            font-size: 12px;
                            background-color: transparent;
                            padding: 2px;
                            font-weight: bold;
                            border: none;
                        }
                    """)
            
            # Update image label
            image_label = widgets['image_label']
            if image_label:
                if path == image_path:
                    image_label.setStyleSheet("""
                        QLabel {
                            background-color: rgb(0, 122, 255);
                            border: none;
                            border-radius: 0px;
                        }
                    """)
                else:
                    image_label.setStyleSheet("""
                        QLabel {
                            background-color: rgb(71, 71, 76);
                            border: none;
                            border-radius: 0px;
                        }
                    """)
            
            # Update widget style
            if path == image_path:
                widgets['widget'].setStyleSheet("""
                    QWidget {
                        border: 3px solid rgb(0, 122, 255);
                        border-radius: 0px;
                        background-color: rgb(0, 122, 255);
                        margin: 0px;
                        padding: 0px;
                    }
                """)
                widgets['overlay'].show()
            else:
                widgets['widget'].setStyleSheet(f"""
                    QWidget {{
                        border: 1px solid rgb(35, 35, 40);
                        border-radius: 0px;
                        background-color: rgb(71, 71, 76);
                        margin: 0px;
                        padding: 0px;
                    }}
                    QWidget:hover {{
                        border: 1px solid rgb(35, 35, 40);
                        background-color: rgb(55, 55, 60);
                    }}
                """)
                widgets['overlay'].hide()
    
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
        
        # Reload all images with new column layout
        if self.current_folder:
            current_images = self.image_files.copy()
            self.image_files.clear()
            self.image_widgets.clear()
            
            # Clear grid layout
            for i in reversed(range(self.grid_layout.count())):
                child = self.grid_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            # Re-add all images with new layout
            for image_path in current_images:
                self.image_files.append(image_path)
                self._add_image_to_grid(image_path)
        
        # Update cell sizes to match new window size
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
        self.selected_image = image_path
        self._load_image_metadata(image_path)
        
        # Hide all overlays first
        for path, widgets in self.image_widgets.items():
            widgets['overlay'].hide()
            # Reset styles
            widgets['widget'].setStyleSheet(f"""
                QWidget {{
                    border: 1px solid rgb(35, 35, 40);
                    border-radius: 0px;
                    background-color: rgb(71, 71, 76);
                    margin: 0px;
                    padding: 0px;
                }}
                QWidget:hover {{
                    border: 1px solid rgb(35, 35, 40);
                    background-color: rgb(55, 55, 60);
                }}
            """)
            widgets['image_label'].setStyleSheet("""
                QLabel {
                    background-color: rgb(71, 71, 76);
                    border: none;
                    border-radius: 0px;
                }
            """)
            widgets['filename_label'].setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 12px;
                    background-color: transparent;
                    padding: 2px;
                    font-weight: bold;
                }
            """)
        
        # Show selection for clicked image
        if str(image_path) in self.image_widgets:
            selected_widgets = self.image_widgets[str(image_path)]
            
            # Apply selection styles
            selected_widgets['widget'].setStyleSheet("""
                QWidget {
                    border: 3px solid rgb(0, 122, 255);
                    border-radius: 0px;
                    background-color: rgb(0, 122, 255);
                    margin: 0px;
                    padding: 0px;
                }
            """)
            selected_widgets['image_label'].setStyleSheet("""
                QLabel {
                    background-color: rgb(0, 122, 255);
                    border: none;
                    border-radius: 0px;
                }
            """)
            selected_widgets['filename_label'].setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 12px;
                    background-color: transparent;
                    padding: 2px;
                    font-weight: bold;
                    text-decoration: underline;
                }
            """)
            
            # Show overlay
            selected_widgets['overlay'].setStyleSheet("""
                QWidget {
                    background-color: rgba(0, 122, 255, 30);
                    border: 3px solid rgb(0, 122, 255);
                    border-radius: 0px;
                }
            """)
            selected_widgets['overlay'].show()
            selected_widgets['overlay'].raise_()
    
    def _update_cell_sizes(self) -> None:
        """Update cell sizes based on available space"""
        if not self.current_folder or not self.image_files:
            return
        
        # Get available width for grid (excluding scrollbars)
        available_width = self.image_grid_container.width() - 40  # Subtract scrollbar margin
        if available_width <= 0:
            return
        
        # Calculate optimal cell size
        cell_width = available_width // self.grid_columns
        cell_height = int(cell_width * 1.2)  # 5:4 aspect ratio for better image display
        
        # Minimum cell size to maintain usability
        min_cell_size = 100
        cell_width = max(cell_width, min_cell_size)
        cell_height = max(cell_height, int(min_cell_size * 1.2))
        
        # Calculate icon size (fill most of the cell with margins)
        icon_size = min(cell_width - 22, cell_height - 45)  # Leave 10px margins + 2px border + 20px for filename
        
        # Update all existing widgets
        for image_path, widgets in self.image_widgets.items():
            # Update widget size
            widgets['widget'].setFixedSize(cell_width, cell_height)
            
            # Update overlay size
            widgets['overlay'].setGeometry(0, 0, cell_width, cell_height)
            
            # Calculate available space for image (cell height minus margins and filename)
            available_height = cell_height - 42  # 10px top + 10px bottom + 20px filename + 2px padding
            image_size = min(icon_size, available_height)
            
            # Update image label size
            image_label = widgets['image_label']
            if image_label:
                image_label.setMinimumSize(image_size, image_size)
                image_label.setMaximumSize(image_size, image_size)
                
                # Reload and rescale the pixmap
                try:
                    pixmap = QPixmap(str(image_path))
                    if not pixmap.isNull():
                        # Scale to fit while maintaining aspect ratio
                        scaled_pixmap = pixmap.scaled(
                            image_size,
                            image_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        image_label.setPixmap(scaled_pixmap)
                except Exception:
                    pass
            
            # Update styles with selection state
            is_selected = (self.selected_image and str(self.selected_image) == str(image_path))
            if is_selected:
                widgets['widget'].setStyleSheet("""
                    QWidget {
                        border: 3px solid rgb(0, 122, 255);
                        border-radius: 0px;
                        background-color: rgb(0, 122, 255);
                        margin: 0px;
                        padding: 0px;
                    }
                """)
                widgets['image_label'].setStyleSheet("""
                    QLabel {
                        background-color: rgb(0, 122, 255);
                        border: none;
                        border-radius: 0px;
                    }
                """)
                widgets['filename_label'].setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 12px;
                        background-color: transparent;
                        padding: 2px;
                        font-weight: bold;
                        text-decoration: underline;
                    }
                """)
                widgets['overlay'].show()
            else:
                widgets['widget'].setStyleSheet(f"""
                    QWidget {{
                        border: 1px solid rgb(35, 35, 40);
                        border-radius: 0px;
                        background-color: rgb(71, 71, 76);
                        margin: 0px;
                        padding: 0px;
                    }}
                    QWidget:hover {{
                        border: 1px solid rgb(35, 35, 40);
                        background-color: rgb(55, 55, 60);
                    }}
                """)
                widgets['image_label'].setStyleSheet("""
                    QLabel {
                        background-color: rgb(71, 71, 76);
                        border: none;
                        border-radius: 0px;
                    }
                """)
                widgets['filename_label'].setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 12px;
                        background-color: transparent;
                        padding: 2px;
                        font-weight: bold;
                    }
                """)
                widgets['overlay'].hide()
        
        self.logger.info(f"Updated cell sizes: {cell_width}x{cell_height}, icon: {image_size}x{image_size}")
    
    def _update_widget_style(self, widget: QWidget, is_selected: bool = False) -> None:
        """Update widget styling with selection state"""
        # Calculate lighter background color (25% lighter than panel color)
        panel_color = (35, 35, 40)  # rgb(35, 35, 40)
        lighter_color = tuple(min(255, int(c + (255 - c) * 0.25)) for c in panel_color)
        lighter_color_str = f"rgb({lighter_color[0]}, {lighter_color[1]}, {lighter_color[2]})"
        
        # Update widget style based on selection
        if is_selected:
            widget.setStyleSheet(f"""
                QWidget {{
                    border: 3px solid rgb(0, 122, 255);
                    border-radius: 0px;
                    background-color: rgb(0, 122, 255);
                    margin: 0px;
                    padding: 0px;
                }}
                QWidget:hover {{
                    border: 3px solid rgb(0, 122, 255);
                    background-color: rgb(0, 122, 255);
                }}
            """)
        else:
            widget.setStyleSheet(f"""
                QWidget {{
                    border: 1px solid rgb(35, 35, 40);
                    border-radius: 0px;
                    background-color: {lighter_color_str};
                    margin: 0px;
                    padding: 0px;
                }}
                QWidget:hover {{
                    border: 1px solid rgb(35, 35, 40);
                    background-color: rgb(55, 55, 60);
                }}
            """)
        
        # Update image label style
        image_label = widget.findChild(QLabel)
        if image_label:
            if is_selected:
                image_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: rgb(0, 122, 255);
                        border: none;
                        border-radius: 0px;
                    }}
                """)
            else:
                image_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {lighter_color_str};
                        border: none;
                        border-radius: 0px;
                    }}
                """)
        
        # Update filename label style
        filename_label = widget.findChild(QLabel, "filename")
        if filename_label:
            if is_selected:
                filename_label.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 12px;
                        background-color: transparent;
                        padding: 2px;
                        font-weight: bold;
                        text-decoration: underline;
                        border: none;
                    }
                """)
            else:
                filename_label.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 12px;
                        background-color: transparent;
                        padding: 2px;
                        font-weight: bold;
                        border: none;
                    }
                """)
