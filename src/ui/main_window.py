"""
Main Window for DarkLab Application
Handles the main UI layout and panel management
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QFileDialog, QMainWindow, QMenu, QMenuBar, QMessageBox,
    QStackedWidget, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QGuiApplication, QKeySequence, QShortcut

from src.catalog.database import create_catalog, open_catalog
from src.catalog.startup_policy import plan_startup, require_catalog
from src.config.config_manager import ConfigManager
from src.ui.themes import DarkTheme, StyleSheet
from src.ui.panels.library_browser_panel import LibraryBrowserPanel
from src.ui.panels.develop_panel import DevelopPanel
from src.ui.panels.map_panel import MapPanel
from src.ui.panels.book_panel import BookPanel
from src.ui.panels.print_panel import PrintPanel
from src.ui.panels.slideshow_panel import SlideshowPanel
from src.ui.panels.website_panel import WebsitePanel
from src.ui.catalog_filter import CATALOG_FILTER
from src.ui.dialogs import ImportDialog
from src.ui.dialogs.catalog_settings_dialog import CatalogSettingsDialog
from src.ui.dialogs.select_catalog_dialog import SelectCatalogDialog
from src.ui.widgets.module_bar import ModuleBar


def _text_setting(value: object) -> str:
    if isinstance(value, str):
        return value
    return ""


def _selected_path(selected: str) -> Path | None:
    if selected == "":
        return None
    return Path(selected)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.panels = {}
        self.catalog_path: Path | None = None
        self.module_bar: ModuleBar | None = None
        
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
        self.setWindowTitle("DarkLab Catalog - DarkLab")
        self.setMinimumSize(1000, 700)
        
        # Apply dark theme
        DarkTheme.apply_theme(QGuiApplication.instance())
        self.setStyleSheet(StyleSheet.MAIN_WINDOW)
    
    def _setup_ui(self) -> None:
        """Setup the main UI layout"""
        # Setup menu bar
        self._setup_menu_bar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._setup_module_bar()
        main_layout.addWidget(self.module_bar)

        # Panel container
        self.panel_container = QStackedWidget()
        self.panel_container.setStyleSheet(StyleSheet.PANEL)
        main_layout.addWidget(self.panel_container)

    def _setup_menu_bar(self) -> None:
        """Setup the menu bar with File menu"""
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)

        # File menu
        file_menu = QMenu("&File", self)
        menu_bar.addMenu(file_menu)
        self._setup_catalog_actions(file_menu)

        # Import action
        import_action = file_menu.addAction("&Import...")
        import_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        import_action.triggered.connect(self._open_import_dialog)

        file_menu.addSeparator()

        # Exit action
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
    
    def _setup_module_bar(self) -> None:
        modules = (
            ("library", "Library"),
            ("develop", "Develop"),
            ("map", "Map"),
            ("book", "Book"),
            ("slideshow", "Slideshow"),
            ("print", "Print"),
            ("website", "Web"),
        )
        self.module_bar = ModuleBar(modules, "DarkLab Catalog")
        self.module_bar.setStyleSheet(StyleSheet.MODULE_BAR)
        self.module_bar.module_selected.connect(self._switch_to_panel)
    
    def _setup_panels(self) -> None:
        """Setup all panels (Import removed - now a dialog)"""
        panel_classes = {
            "library": LibraryBrowserPanel,
            "develop": DevelopPanel,
            "map": MapPanel,
            "book": BookPanel,
            "print": PrintPanel,
            "slideshow": SlideshowPanel,
            "website": WebsitePanel,
        }

        for panel_id, panel_class in panel_classes.items():
            panel = panel_class()
            self.panels[panel_id] = panel
            self.panel_container.addWidget(panel)
        library = self.panels.get("library")
        if isinstance(library, LibraryBrowserPanel):
            library.import_requested.connect(self._open_import_dialog)
    
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

        # Library is now the default panel
        current_panel = self.config_manager.get_current_panel()
        if current_panel not in self.panels:
            current_panel = "library"
        self._switch_to_panel(current_panel)
        self._restore_catalog()

        # Setup keyboard shortcut for Import dialog (Cmd+I on Mac, Ctrl+I elsewhere)
        self._setup_import_shortcut()
    
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

    def _setup_import_shortcut(self) -> None:
        """Setup keyboard shortcut for Import dialog"""
        # Use Ctrl+Shift+I on all platforms (PyQt handles Cmd+Shift on Mac automatically)
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+I"), self)
        shortcut.activated.connect(self._open_import_dialog)

    def _setup_catalog_actions(self, file_menu: QMenu) -> None:
        new_catalog = file_menu.addAction("New &Catalog...")
        new_catalog.triggered.connect(self._create_catalog)
        open_action = file_menu.addAction("&Open Catalog...")
        open_action.triggered.connect(self._open_catalog_dialog)
        settings_action = file_menu.addAction("Catalog &Settings...")
        settings_action.triggered.connect(self._edit_catalog_settings)
        file_menu.addSeparator()

    def _create_catalog(self) -> None:
        path = _selected_path(self._choose_save_path())
        if path is None:
            return
        self._create_chosen_catalog(path)

    def _create_chosen_catalog(self, path: Path) -> None:
        try:
            self._use_catalog(create_catalog(path))
        except OSError as error:
            self.logger.error("Create catalog failed: %s", path)
            QMessageBox.warning(self, "New Catalog", str(error))

    def _open_catalog_dialog(self) -> None:
        path = _selected_path(self._choose_open_path())
        if path is None:
            return
        self._open_chosen_catalog(path)

    def _open_chosen_catalog(self, path: Path) -> None:
        try:
            self._use_catalog(open_catalog(path))
        except (FileNotFoundError, ValueError) as error:
            self.logger.error("Open catalog failed: %s", path)
            QMessageBox.warning(self, "Open Catalog", str(error))

    def _choose_save_path(self) -> str:
        selected, _chosen = QFileDialog.getSaveFileName(self, "New Catalog", "", CATALOG_FILTER)
        return selected

    def _choose_open_path(self) -> str:
        return QFileDialog.getExistingDirectory(self, "Open Catalog", "")

    def _use_catalog(self, path: Path) -> None:
        self.config_manager.set("catalog.path", str(path))
        self._publish_catalog(path)

    def _edit_catalog_settings(self) -> None:
        dialog = CatalogSettingsDialog(self._catalog_settings(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._store_startup(dialog)

    def _store_startup(self, dialog: CatalogSettingsDialog) -> None:
        self.config_manager.set("catalog.startup_mode", dialog.chosen_mode())
        self.config_manager.set("catalog.fixed_path", dialog.chosen_fixed_path())

    def launch_window(self) -> bool:
        chosen = require_catalog(self._catalog_settings(), SelectCatalogDialog.pick)
        if chosen is None:
            return False
        if self.catalog_path != chosen:
            self._use_catalog(chosen)
        return True

    def _restore_catalog(self) -> None:
        action, path = plan_startup(self._catalog_settings())
        if action == "open" and path is not None:
            self._show_open_catalog(path)

    def _show_open_catalog(self, path: Path) -> None:
        self._publish_catalog(path)

    def _publish_catalog(self, path: Path) -> None:
        self.catalog_path = path
        self.setWindowTitle(f"{path.stem} - DarkLab")
        self._show_catalog_photos(path)

    def _show_catalog_photos(self, path: Path) -> None:
        for panel in self.panels.values():
            show = getattr(panel, "show_catalog", None)
            if show is not None:
                show(path)

    def _catalog_settings(self) -> dict[str, str]:
        return {
            "startup_mode": _text_setting(self.config_manager.get("catalog.startup_mode", "")),
            "catalog_path": _text_setting(self.config_manager.get("catalog.path", "")),
            "fixed_catalog": _text_setting(self.config_manager.get("catalog.fixed_path", "")),
        }

    def _open_import_dialog(self) -> None:
        dialog = ImportDialog(self)
        dialog.bind_catalog(self.catalog_path)
        dialog.exec()
        self._refresh_open_catalog()
        self.logger.info("Import dialog closed")

    def _refresh_open_catalog(self) -> None:
        if self.catalog_path is None:
            return
        self._show_catalog_photos(self.catalog_path)
    
    def _switch_to_panel(self, panel_id: str) -> None:
        """Switch to specified panel"""
        if panel_id in self.panels:
            self.panel_container.setCurrentWidget(self.panels[panel_id])
            self.config_manager.set_current_panel(panel_id)
            
            # Update toolbar button states
            if self.module_bar is not None:
                self.module_bar.set_current(panel_id)
            
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
