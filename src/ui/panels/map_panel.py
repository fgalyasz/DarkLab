from PyQt6.QtWidgets import QLabel

from src.ui.panels.base_panel import BasePanel


class MapPanel(BasePanel):
    def __init__(self) -> None:
        super().__init__("map")

    def _add_placeholder_content(self) -> None:
        description = QLabel("Photo locations will appear on the map.")
        description.setWordWrap(True)
        description.setStyleSheet("color: rgb(180, 180, 180); font-size: 14px;")
        self.content_layout.addWidget(description)
