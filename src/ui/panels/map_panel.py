from PyQt6.QtWidgets import QLabel

from src.ui.density import Density
from src.ui.panels.base_panel import BasePanel


class MapPanel(BasePanel):
    def __init__(self) -> None:
        super().__init__("map")

    def _add_placeholder_content(self) -> None:
        description = QLabel("Photo locations will appear on the map.")
        description.setWordWrap(True)
        description.setStyleSheet(f"color: rgb(180, 180, 180); font-size: {Density.BODY_PX}px;")
        self.content_layout.addWidget(description)
