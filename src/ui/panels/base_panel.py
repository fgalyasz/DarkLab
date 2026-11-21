import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from src.ui.density import Density


class BasePanel(QWidget):
    def __init__(self, panel_name: str):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{panel_name}")
        self.panel_name = panel_name
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(10)
        self.title_label = QLabel(self.panel_name.title())
        self.title_label.setStyleSheet(
            f"color: rgb(230, 230, 230); font-size: {Density.TITLE_PX}px; font-weight: 600;"
        )
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.title_label)
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_frame)
        self._add_placeholder_content()

    def clear_content(self) -> None:
        if hasattr(self, "content_frame") and self.content_frame:
            self.main_layout.removeWidget(self.content_frame)
            self.content_frame.deleteLater()
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.main_layout.addWidget(self.content_frame)

    def _add_placeholder_content(self) -> None:
        placeholder_label = QLabel(f"{self.panel_name.title()} panel — coming soon")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet(
            f"color: rgb(180, 180, 180); font-size: {Density.BODY_PX}px;"
        )
        self.content_layout.addWidget(placeholder_label)

    def get_panel_name(self) -> str:
        return self.panel_name

    def on_activate(self) -> None:
        self.logger.info(f"Panel {self.panel_name} activated")

    def on_deactivate(self) -> None:
        self.logger.info(f"Panel {self.panel_name} deactivated")
