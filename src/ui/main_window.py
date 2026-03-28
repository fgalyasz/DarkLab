"""
Main Window for DarkLab Application
Handles the main UI layout and panel management
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QToolBar, QStackedWidget, QFrame, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, QRect, QTimer
from PyQt6.QtGui import QScreen, QGuiApplication, QFont

from src.config.config_manager import ConfigManager
from src.ui.themes import DarkTheme, StyleSheet
from src.ui.panels.import_panel import ImportPanel
from src.ui.panels.library_browser_panel import LibraryBrowserPanel
from src.ui.panels.develop_panel import DevelopPanel
from src.ui.panels.print_panel import PrintPanel
from src.ui.panels.slideshow_panel import SlideshowPanel
from src.ui.panels.website_panel import WebsitePanel


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.panels = {}
        self.toolbar_buttons = {}
        
        self._setup_window()
        self._setup_ui()
        self._setup_panels()
        self._apply_initial_state()
        
        # Setup auto-save timer
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save_state)
        self._auto_save_timer.start(5000)  # Save every 5 seconds
    
    def _setup_window(self) -> None:
        """Setup main window properties"""
        self.setWindowTitle("DarkLab")
        self.setMinimumSize(1000, 700)
        
        # Apply dark theme
        DarkTheme.apply_theme(QGuiApplication.instance())
        self.setStyleSheet(StyleSheet.MAIN_WINDOW)
    
    def _setup_ui(self) -> None:
        """Setup the main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar
        self._setup_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # Panel container
        self.panel_container = QStackedWidget()
        self.panel_container.setStyleSheet(StyleSheet.PANEL)
        main_layout.addWidget(self.panel_container)
    
    def _setup_toolbar(self) -> None:
        """Setup the toolbar with title and panel navigation buttons"""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet(StyleSheet.TOOLBAR)
        self.toolbar.setOrientation(Qt.Orientation.Horizontal)
        
        # Add title on the left side
        title_label = QLabel("DarkLab")
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; margin-right: 20px;")
        self.toolbar.addWidget(title_label)
        
        # Add spacer to push panel buttons to the right
        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Preferred
        )
        self.toolbar.addWidget(spacer)
        
        # Panel buttons on the right side
        panels = [
            ("import", "Import"),
            ("library", "Library"),
            ("develop", "Develop"),
            ("print", "Print"),
            ("slideshow", "Slideshow"),
            ("website", "Website")
        ]
        
        for panel_id, panel_name in panels:
            button = self.toolbar.addAction(panel_name)
            button.setData(panel_id)
            button.triggered.connect(lambda checked, pid=panel_id: self._switch_to_panel(pid))
            self.toolbar_buttons[panel_id] = button
    
    def _setup_panels(self) -> None:
        """Setup all panels"""
        panel_classes = {
            "import": ImportPanel,
            "library": LibraryBrowserPanel,
            "develop": DevelopPanel,
            "print": PrintPanel,
            "slideshow": SlideshowPanel,
            "website": WebsitePanel
        }
        
        for panel_id, panel_class in panel_classes.items():
            panel = panel_class()
            self.panels[panel_id] = panel
            self.panel_container.addWidget(panel)
    
    def _apply_initial_state(self) -> None:
        """Apply initial window state from config"""
        # Try to restore saved geometry
        saved_geometry = self.config_manager.get_window_geometry()
        if saved_geometry:
            self.setGeometry(saved_geometry)
        else:
            # Center window and set to 80% of screen size
            self._center_window()
        
        # Restore maximized state
        if self.config_manager.get("window.maximized", False):
            self.showMaximized()
        
        # Restore current panel
        current_panel = self.config_manager.get_current_panel()
        if current_panel == "library_import":
            current_panel = "import"
        elif (
            current_panel == "library"
            and "import" in self.panels
            and not self.config_manager.get("window.import_panel_migrated", False)
        ):
            current_panel = "import"
            self.config_manager.set("window.import_panel_migrated", True)
        self._switch_to_panel(current_panel)
    
    def _center_window(self) -> None:
        """Center window on screen and set to 80% of screen size"""
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            width = int(screen_geometry.width() * 0.8)
            height = int(screen_geometry.height() * 0.8)
            
            x = (screen_geometry.width() - width) // 2
            y = (screen_geometry.height() - height) // 2
            
            self.setGeometry(x, y, width, height)
    
    def _switch_to_panel(self, panel_id: str) -> None:
        """Switch to specified panel"""
        if panel_id in self.panels:
            self.panel_container.setCurrentWidget(self.panels[panel_id])
            self.config_manager.set_current_panel(panel_id)
            
            # Update toolbar button states
            for pid, button in self.toolbar_buttons.items():
                button.setChecked(pid == panel_id)
            
            self.logger.info(f"Switched to panel: {panel_id}")
        else:
            self.logger.error(f"Unknown panel: {panel_id}")
    
    def _auto_save_state(self) -> None:
        """Automatically save window state"""
        if not self.isMaximized():
            self.config_manager.set_window_geometry(self.geometry())
        
        self.config_manager.set("window.maximized", self.isMaximized())
    
    def closeEvent(self, event) -> None:
        """Handle window close event"""
        # Save final state
        if not self.isMaximized():
            self.config_manager.set_window_geometry(self.geometry())
        
        self.config_manager.set("window.maximized", self.isMaximized())
        
        # Stop auto-save timer
        self._auto_save_timer.stop()
        
        self.logger.info("Application closed")
        event.accept()
