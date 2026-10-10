"""
Theme definitions for Photo Editor
Dark theme with macOS-like styling
"""

from PyQt6.QtWidgets import QStyleFactory
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette


class DarkTheme:
    """Lightroom Classic neutral charcoal palette."""

    BACKGROUND_DARK = QColor(32, 32, 32)
    BACKGROUND_MEDIUM = QColor(43, 43, 43)
    BACKGROUND_LIGHT = QColor(58, 58, 58)
    ACCENT_COLOR = QColor(96, 96, 96)
    TEXT_PRIMARY = QColor(230, 230, 230)
    TEXT_SECONDARY = QColor(176, 176, 176)
    TEXT_DISABLED = QColor(110, 110, 110)
    BORDER_COLOR = QColor(18, 18, 18)
    HOVER_COLOR = QColor(72, 72, 72)
    PRESSED_COLOR = QColor(48, 48, 48)
    
    @classmethod
    def apply_theme(cls, app) -> None:
        """Apply dark theme to the application"""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, cls.BACKGROUND_DARK)
        palette.setColor(QPalette.ColorRole.WindowText, cls.TEXT_PRIMARY)
        
        # Base colors (for text widgets)
        palette.setColor(QPalette.ColorRole.Base, cls.BACKGROUND_MEDIUM)
        palette.setColor(QPalette.ColorRole.AlternateBase, cls.BACKGROUND_LIGHT)
        palette.setColor(QPalette.ColorRole.Text, cls.TEXT_PRIMARY)
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, cls.BACKGROUND_LIGHT)
        palette.setColor(QPalette.ColorRole.ButtonText, cls.TEXT_PRIMARY)
        
        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, cls.ACCENT_COLOR)
        palette.setColor(QPalette.ColorRole.HighlightedText, cls.TEXT_PRIMARY)
        
        # Disabled colors
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, cls.TEXT_DISABLED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, cls.TEXT_DISABLED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, cls.TEXT_DISABLED)
        
        # Set palette
        app.setPalette(palette)
        
        # Set style
        app.setStyle(QStyleFactory.create("Fusion"))


class StyleSheet:
    """CSS stylesheets for custom styling"""
    
    MAIN_WINDOW = """
        QMainWindow, QMenuBar, QMenu {
            background-color: rgb(38, 38, 38);
            color: rgb(230, 230, 230);
        }
        QMenuBar::item:selected, QMenu::item:selected {
            background-color: rgb(78, 78, 78);
        }
    """

    MODULE_BAR = """
        QWidget {
            background-color: rgb(46, 46, 46);
            border-bottom: 1px solid rgb(16, 16, 16);
        }
    """

    LIGHTROOM = """
        QWidget { background-color: rgb(49, 49, 49); color: rgb(226, 226, 226); }
        QLabel { background: transparent; color: rgb(220, 220, 220); }
        QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit, QListWidget, QTreeWidget {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(24, 24, 24), stop:1 rgb(36, 36, 36));
            color: rgb(230, 230, 230);
            border-top: 1px solid rgb(8, 8, 8);
            border-left: 1px solid rgb(12, 12, 12);
            border-right: 1px solid rgb(72, 72, 72);
            border-bottom: 1px solid rgb(84, 84, 84);
            border-radius: 2px;
            padding: 3px 6px;
            selection-background-color: rgb(92, 92, 92);
        }
        QComboBox::drop-down { border: none; width: 18px; }
        QComboBox QAbstractItemView {
            background-color: rgb(36, 36, 36);
            color: white;
            selection-background-color: rgb(88, 88, 88);
            border: 1px solid rgb(16, 16, 16);
        }
        QTreeWidget::item:selected, QListWidget::item:selected { background-color: rgb(86, 86, 86); }
        QCheckBox { color: rgb(220, 220, 220); spacing: 8px; background: transparent; }
        QCheckBox::indicator {
            width: 13px; height: 13px;
            background-color: rgb(26, 26, 26);
            border-top: 1px solid rgb(8, 8, 8);
            border-left: 1px solid rgb(10, 10, 10);
            border-right: 1px solid rgb(78, 78, 78);
            border-bottom: 1px solid rgb(90, 90, 90);
        }
        QCheckBox::indicator:checked { background-color: rgb(214, 214, 214); }
        QPushButton {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(96, 96, 96), stop:1 rgb(62, 62, 62));
            color: rgb(236, 236, 236);
            border-top: 1px solid rgb(128, 128, 128);
            border-left: 1px solid rgb(96, 96, 96);
            border-right: 1px solid rgb(42, 42, 42);
            border-bottom: 1px solid rgb(22, 22, 22);
            border-radius: 2px;
            padding: 3px 8px;
        }
        QPushButton:hover {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(112, 112, 112), stop:1 rgb(74, 74, 74));
        }
        QPushButton:pressed {
            background-color: rgb(40, 40, 40);
            border-top: 1px solid rgb(12, 12, 12);
            border-bottom: 1px solid rgb(90, 90, 90);
        }
        QPushButton:checked { background-color: rgb(78, 78, 78); }
        QPushButton:disabled { color: rgb(140, 140, 140); background-color: rgb(52, 52, 52); }
        QSlider::groove:horizontal {
            height: 4px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(14, 14, 14), stop:1 rgb(58, 58, 58));
            border-top: 1px solid rgb(6, 6, 6);
            border-bottom: 1px solid rgb(88, 88, 88);
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(236, 236, 236), stop:1 rgb(176, 176, 176));
            border: 1px solid rgb(40, 40, 40);
            width: 11px;
            margin: -5px 0;
            border-radius: 6px;
        }
        QScrollArea { border: none; background: transparent; }
        QProgressBar {
            border-top: 1px solid rgb(10, 10, 10);
            border-bottom: 1px solid rgb(80, 80, 80);
            color: white;
            background: rgb(28, 28, 28);
        }
        QProgressBar::chunk { background-color: rgb(168, 168, 168); }
        #panelColumn { background-color: rgb(45, 45, 45); }
        #panelHeader {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(82, 82, 82), stop:1 rgb(54, 54, 54));
            border-top: 1px solid rgb(104, 104, 104);
            border-bottom: 1px solid rgb(16, 16, 16);
        }
        #panelTitle {
            color: rgb(236, 236, 236);
            font-size: 12px;
            font-weight: 600;
            background: transparent;
        }
        #developRow, #developGroupBody { background: transparent; }
        #developGroup {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(30, 30, 30), stop:1 rgb(40, 40, 40));
            border-top: 1px solid rgb(6, 6, 6);
            border-left: 1px solid rgb(10, 10, 10);
            border-right: 1px solid rgb(62, 62, 62);
            border-bottom: 2px solid rgb(8, 8, 8);
            border-radius: 3px;
        }
        #developHeading {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(92, 92, 92), stop:1 rgb(56, 56, 56));
            color: rgb(242, 242, 242);
            font-size: 11px;
            font-weight: 600;
            border-top: 1px solid rgb(124, 124, 124);
            border-bottom: 1px solid rgb(12, 12, 12);
            padding: 4px 8px;
        }
    """

    IMPORT_DIALOG = LIGHTROOM + """
        QPushButton#importMode {
            background: transparent; border: none; color: rgb(176, 176, 176); font-size: 13px; padding: 2px 8px;
        }
        QPushButton#importMode:checked { color: white; font-weight: 600; }
        QPushButton#importAction {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(244, 244, 244), stop:1 rgb(196, 196, 196));
            color: rgb(20, 20, 20);
            border-top: 1px solid rgb(255, 255, 255);
            border-bottom: 1px solid rgb(90, 90, 90);
            font-weight: 600;
        }
    """
    
    TOOLBAR = """
        QToolBar {
            background-color: rgb(35, 35, 40);
            border: none;
            spacing: 8px;
            padding: 8px;
        }
        
        QToolBar QToolButton {
            background-color: rgb(45, 45, 50);
            border: 1px solid rgb(60, 60, 65);
            border-radius: 6px;
            padding: 8px 16px;
            color: white;
            font-weight: 500;
        }
        
        QToolBar QToolButton:hover {
            background-color: rgb(55, 55, 60);
            border-color: rgb(70, 70, 75);
        }
        
        QToolBar QToolButton:pressed {
            background-color: rgb(70, 70, 75);
        }
        
        QToolBar QToolButton:checked {
            background-color: rgb(78, 78, 78);
            border-color: rgb(110, 110, 110);
        }
    """
    
    PANEL = """
        QWidget { background-color: rgb(49, 49, 49); color: rgb(226, 226, 226); }
        QFrame { background-color: rgb(49, 49, 49); border: none; }
    """
    
    BUTTON = """
        QPushButton {
            background-color: rgb(45, 45, 50);
            border: 1px solid rgb(60, 60, 65);
            border-radius: 6px;
            padding: 8px 16px;
            color: white;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: rgb(55, 55, 60);
            border-color: rgb(70, 70, 75);
        }
        
        QPushButton:pressed {
            background-color: rgb(70, 70, 75);
        }
        
        QPushButton:disabled {
            background-color: rgb(30, 30, 35);
            color: rgb(100, 100, 100);
        }
    """
