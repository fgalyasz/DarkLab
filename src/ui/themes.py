from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QStyleFactory

from src.ui.density import Density


class DarkTheme:
    BACKGROUND_DARK = QColor(36, 36, 36)
    BACKGROUND_MEDIUM = QColor(50, 50, 50)
    BACKGROUND_LIGHT = QColor(80, 80, 80)
    ACCENT_COLOR = QColor(104, 104, 104)
    TEXT_PRIMARY = QColor(224, 224, 224)
    TEXT_SECONDARY = QColor(176, 176, 176)
    TEXT_DISABLED = QColor(110, 110, 110)
    BORDER_COLOR = QColor(14, 14, 14)
    HOVER_COLOR = QColor(92, 92, 92)
    PRESSED_COLOR = QColor(58, 58, 58)

    @classmethod
    def apply_theme(cls, app) -> None:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, cls.BACKGROUND_MEDIUM)
        palette.setColor(QPalette.ColorRole.WindowText, cls.TEXT_PRIMARY)
        palette.setColor(QPalette.ColorRole.Base, cls.BACKGROUND_LIGHT)
        palette.setColor(QPalette.ColorRole.AlternateBase, cls.BACKGROUND_LIGHT)
        palette.setColor(QPalette.ColorRole.Text, cls.TEXT_PRIMARY)
        palette.setColor(QPalette.ColorRole.Button, cls.BACKGROUND_LIGHT)
        palette.setColor(QPalette.ColorRole.ButtonText, cls.TEXT_PRIMARY)
        palette.setColor(QPalette.ColorRole.Highlight, cls.ACCENT_COLOR)
        palette.setColor(QPalette.ColorRole.HighlightedText, cls.TEXT_PRIMARY)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, cls.TEXT_DISABLED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, cls.TEXT_DISABLED)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, cls.TEXT_DISABLED)
        app.setPalette(palette)
        app.setStyle(QStyleFactory.create("Fusion"))
        font = QFont(app.font())
        font.setPointSize(Density.BODY_POINT_SIZE)
        app.setFont(font)


class StyleSheet:
    MAIN_WINDOW = """
        QMainWindow, QMenuBar, QMenu {
            background-color: rgb(36, 36, 36);
            color: rgb(224, 224, 224);
            font-size: 11px;
        }
        QMenuBar::item:selected, QMenu::item:selected {
            background-color: rgb(80, 80, 80);
        }
    """

    MODULE_BAR = """
        QWidget {
            background-color: rgb(14, 14, 14);
            border-bottom: 1px solid rgb(32, 32, 32);
        }
    """

    LIGHTROOM = f"""
        QWidget {{ background-color: rgb(50, 50, 50); color: rgb(224, 224, 224); font-size: {Density.BODY_PX}px; }}
        QLabel {{ background: transparent; color: rgb(224, 224, 224); font-size: {Density.BODY_PX}px; }}
        QLineEdit, QSpinBox, QTextEdit, QPlainTextEdit {{
            background-color: rgb(56, 56, 56);
            color: rgb(226, 226, 226);
            border: 1px solid rgb(32, 32, 32);
            border-radius: {Density.CORNER_RADIUS_PX}px;
            padding: 2px 5px;
            min-height: 18px;
            selection-background-color: rgb(104, 104, 104);
            font-size: {Density.BODY_PX}px;
        }}
        QComboBox {{
            background-color: rgb(68, 68, 68);
            color: rgb(224, 224, 224);
            border: 1px solid rgb(44, 44, 44);
            border-radius: {Density.CORNER_RADIUS_PX}px;
            padding: 1px 6px;
            min-height: 18px;
            font-size: {Density.BODY_PX}px;
        }}
        QComboBox:hover {{ background-color: rgb(76, 76, 76); border-color: rgb(96, 96, 96); }}
        QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 18px; border: none; background: transparent; }}
        QComboBox QAbstractItemView {{
            background-color: rgb(52, 52, 52);
            color: rgb(232, 232, 232);
            selection-background-color: rgb(92, 92, 92);
            border: 1px solid rgb(16, 16, 16);
            font-size: {Density.BODY_PX}px;
        }}
        QListWidget, QTreeWidget {{
            background-color: rgb(80, 80, 80);
            color: rgb(222, 222, 222);
            border: none;
            outline: none;
            selection-background-color: rgb(104, 104, 104);
            font-size: {Density.BODY_PX}px;
        }}
        QTreeWidget::item, QListWidget::item {{
            padding: 2px 6px;
            font-size: {Density.BODY_PX}px;
        }}
        QTreeWidget::item:hover, QListWidget::item:hover {{ background-color: rgb(90, 90, 90); }}
        QTreeWidget::item:selected, QListWidget::item:selected {{ background-color: rgb(104, 104, 104); color: rgb(242, 242, 242); }}
        QCheckBox {{ color: rgb(222, 222, 222); spacing: 6px; background: transparent; font-size: {Density.BODY_PX}px; }}
        QCheckBox::indicator {{
            width: 12px; height: 12px;
            background-color: rgb(54, 54, 54);
            border: 1px solid rgb(26, 26, 26);
            border-radius: 1px;
        }}
        QCheckBox::indicator:checked {{ background-color: rgb(206, 206, 206); }}
        QPushButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(72, 72, 72), stop:1 rgb(60, 60, 60));
            color: rgb(224, 224, 224);
            border: 1px solid rgb(36, 36, 36);
            border-top: 1px solid rgb(88, 88, 88);
            border-radius: {Density.CORNER_RADIUS_PX}px;
            padding: 2px 8px;
            min-height: 18px;
            font-size: {Density.BODY_PX}px;
        }}
        QPushButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(84, 84, 84), stop:1 rgb(70, 70, 70));
        }}
        QPushButton:pressed {{
            background-color: rgb(52, 52, 52);
            border-top: 1px solid rgb(24, 24, 24);
        }}
        QPushButton:checked {{
            background-color: rgb(96, 96, 96);
            color: rgb(242, 242, 242);
            border: 1px solid rgb(32, 32, 32);
        }}
        QPushButton:disabled {{ color: rgb(118, 118, 118); background-color: rgb(64, 64, 64); }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgb(48, 48, 48), stop:1 rgb(84, 84, 84));
            border: 1px solid rgb(24, 24, 24);
            border-radius: 0px;
        }}
        QSlider::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(192, 192, 192), stop:1 rgb(142, 142, 142));
            border: 1px solid rgb(22, 22, 22);
            width: 10px;
            margin: -4px 0;
            border-radius: 2px;
        }}
        QScrollArea {{ border: none; background-color: rgb(50, 50, 50); }}
        QScrollBar:vertical {{
            background: rgb(16, 16, 16);
            width: 9px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: rgb(154, 154, 154);
            min-height: 28px;
            border-radius: 3px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{ background: rgb(192, 192, 192); }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; border: none; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        QScrollBar:horizontal {{
            background: rgb(16, 16, 16);
            height: 9px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: rgb(154, 154, 154);
            min-width: 28px;
            border-radius: 3px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: rgb(192, 192, 192); }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; border: none; }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}
        QSplitter::handle {{ background-color: rgb(18, 18, 18); width: 3px; height: 3px; }}
        QFormLayout, QFormLayout QLabel {{ font-size: {Density.BODY_PX}px; }}
        QProgressBar {{
            border: 1px solid rgb(20, 20, 20);
            color: white;
            background: rgb(42, 42, 42);
            font-size: {Density.HINT_PX}px;
            max-height: 14px;
        }}
        QProgressBar::chunk {{ background-color: rgb(158, 158, 158); }}
        #panelColumn, #toolStack {{ background-color: rgb(50, 50, 50); }}
        #panelBody, #developRow, #developGroup, #developGroupBody {{ background: transparent; border: none; }}
        #collapsibleSection {{
            background-color: rgb(80, 80, 80);
            border: 1px solid rgb(14, 14, 14);
            border-radius: {Density.PANEL_CORNER_RADIUS_PX}px;
        }}
        #panelHeader {{
            background-color: rgb(50, 50, 50);
            border: none;
            border-top: 1px solid rgb(62, 62, 62);
            border-bottom: 1px solid rgb(12, 12, 12);
            border-radius: {Density.PANEL_CORNER_RADIUS_PX}px;
        }}
        #panelTitle {{
            color: rgb(210, 210, 210);
            font-size: {Density.HEADER_PX}px;
            font-weight: 500;
            background: transparent;
        }}
        #developHeading {{
            background: transparent;
            border: none;
            padding: 0px;
        }}
        #developHeadingTitle {{
            color: rgb(204, 204, 204);
            font-size: {Density.BODY_PX}px;
            font-weight: 500;
            background: transparent;
        }}
        #sliderCaption {{
            color: rgb(222, 222, 222);
            font-size: {Density.BODY_PX}px;
            background: transparent;
        }}
        #sliderValue {{
            color: rgb(218, 218, 218);
            font-size: {Density.HINT_PX}px;
            background: transparent;
        }}
        #toolStrip {{
            background-color: rgb(62, 62, 62);
            border: 1px solid rgb(14, 14, 14);
            border-top: 1px solid rgb(78, 78, 78);
        }}
        #toolStrip QPushButton {{
            background: transparent;
            border: none;
            color: rgb(206, 206, 206);
            padding: 3px 6px;
            min-height: 20px;
        }}
        #toolStrip QPushButton:hover {{ background-color: rgb(78, 78, 78); color: rgb(236, 236, 236); }}
        #toolStrip QPushButton:checked {{ background-color: rgb(88, 88, 88); color: rgb(246, 246, 246); }}
        #panelActionBar {{
            background-color: rgb(38, 38, 38);
            border-top: 1px solid rgb(14, 14, 14);
        }}
        #panelActionButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(72, 72, 72), stop:1 rgb(56, 56, 56));
            color: rgb(224, 224, 224);
            border: 1px solid rgb(18, 18, 18);
            border-top: 1px solid rgb(88, 88, 88);
            border-radius: 2px;
            min-height: 22px;
            padding: 2px 8px;
        }}
        #panelActionButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(84, 84, 84), stop:1 rgb(68, 68, 68));
        }}
        #panelActionButton:pressed {{ background-color: rgb(48, 48, 48); }}
    """

    IMPORT_DIALOG = LIGHTROOM + f"""
        QPushButton#importMode {{
            background: transparent; border: none; color: rgb(176, 176, 176);
            font-size: {Density.BODY_PX}px; padding: 2px 6px;
        }}
        QPushButton#importMode:checked {{ color: white; font-weight: 600; }}
        QPushButton#importAction {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(244, 244, 244), stop:1 rgb(196, 196, 196));
            color: rgb(20, 20, 20);
            border-top: 1px solid rgb(255, 255, 255);
            border-bottom: 1px solid rgb(90, 90, 90);
            font-weight: 600;
            font-size: {Density.BODY_PX}px;
            padding: 3px 10px;
        }}
        QWidget#importTopBar {{
            background-color: rgb(30, 30, 30);
            border-bottom: 1px solid rgb(8, 8, 8);
        }}
        QWidget#importBottomBar {{
            background-color: rgb(30, 30, 30);
            border-top: 1px solid rgb(8, 8, 8);
        }}
        QWidget#importSource {{
            background-color: rgb(42, 42, 42);
            border-right: 1px solid rgb(10, 10, 10);
        }}
        QWidget#importStage {{ background-color: rgb(22, 22, 22); }}
        QWidget#importSide {{
            background-color: rgb(54, 54, 54);
            border-left: 1px solid rgb(10, 10, 10);
        }}
        QFrame#importBlock {{
            background-color: rgb(80, 80, 80);
            border: 1px solid rgb(14, 14, 14);
            border-radius: {Density.PANEL_CORNER_RADIUS_PX}px;
        }}
        QLabel#importBlockTitle {{
            background-color: rgb(50, 50, 50);
            color: rgb(210, 210, 210);
            font-size: {Density.HEADER_PX}px;
            font-weight: 500;
            padding: 4px 8px;
            border-top: 1px solid rgb(62, 62, 62);
            border-bottom: 1px solid rgb(12, 12, 12);
            border-radius: {Density.PANEL_CORNER_RADIUS_PX}px;
        }}
        QWidget#importBlockBody {{ background-color: rgb(80, 80, 80); }}
        QWidget#importBlockBody QLabel {{ background: transparent; font-size: {Density.BODY_PX}px; }}
    """

    TOOLBAR = f"""
        QToolBar {{
            background-color: rgb(36, 36, 36);
            border: none;
            spacing: 4px;
            padding: 2px;
        }}
        QToolBar QToolButton {{
            background-color: rgb(60, 60, 60);
            border: 1px solid rgb(32, 32, 32);
            border-radius: {Density.CORNER_RADIUS_PX}px;
            padding: 2px 8px;
            color: rgb(224, 224, 224);
            font-size: {Density.BODY_PX}px;
            font-weight: 500;
        }}
        QToolBar QToolButton:hover {{
            background-color: rgb(74, 74, 74);
            border-color: rgb(44, 44, 44);
        }}
        QToolBar QToolButton:pressed {{ background-color: rgb(50, 50, 50); }}
        QToolBar QToolButton:checked {{
            background-color: rgb(88, 88, 88);
            border-color: rgb(110, 110, 110);
        }}
    """

    PANEL = """
        QWidget { background-color: rgb(50, 50, 50); color: rgb(224, 224, 224); }
        QFrame { background-color: rgb(50, 50, 50); border: none; }
    """

    BUTTON = f"""
        QPushButton {{
            background-color: rgb(66, 66, 66);
            border: 1px solid rgb(34, 34, 34);
            border-radius: {Density.CORNER_RADIUS_PX}px;
            padding: 2px 8px;
            color: rgb(224, 224, 224);
            font-size: {Density.BODY_PX}px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: rgb(78, 78, 78);
            border-color: rgb(46, 46, 46);
        }}
        QPushButton:pressed {{ background-color: rgb(52, 52, 52); }}
        QPushButton:disabled {{
            background-color: rgb(48, 48, 48);
            color: rgb(110, 110, 110);
        }}
    """
