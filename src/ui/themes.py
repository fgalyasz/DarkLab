"""
Theme definitions for Photo Editor
Dark theme with macOS-like styling
"""

from PyQt6.QtWidgets import QStyleFactory
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette


class DarkTheme:
    """Dark theme configuration with macOS-like styling"""
    
    # Color palette
    BACKGROUND_DARK = QColor(25, 25, 30)          # Very dark background
    BACKGROUND_MEDIUM = QColor(35, 35, 40)        # Panel background
    BACKGROUND_LIGHT = QColor(45, 45, 50)         # Lighter panels
    ACCENT_COLOR = QColor(0, 122, 255)           # macOS blue accent
    TEXT_PRIMARY = QColor(255, 255, 255)          # White text
    TEXT_SECONDARY = QColor(180, 180, 180)        # Gray text
    TEXT_DISABLED = QColor(100, 100, 100)         # Disabled text
    BORDER_COLOR = QColor(60, 60, 65)             # Subtle borders
    HOVER_COLOR = QColor(55, 55, 60)              # Hover state
    PRESSED_COLOR = QColor(70, 70, 75)            # Pressed state
    
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
        QMainWindow {
            background-color: rgb(25, 25, 30);
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
            background-color: rgb(0, 122, 255);
            border-color: rgb(0, 122, 255);
        }
    """
    
    PANEL = """
        QWidget {
            background-color: rgb(35, 35, 40);
            color: white;
        }
        
        QFrame {
            background-color: rgb(35, 35, 40);
            border-radius: 8px;
        }
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
