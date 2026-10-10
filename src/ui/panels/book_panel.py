from PyQt6.QtWidgets import QLabel

from src.ui.panels.base_panel import BasePanel


class BookPanel(BasePanel):
    def __init__(self) -> None:
        super().__init__("book")

    def _add_placeholder_content(self) -> None:
        description = QLabel("Book layouts will be built from the library selection.")
        description.setWordWrap(True)
        description.setStyleSheet("color: rgb(180, 180, 180); font-size: 14px;")
        self.content_layout.addWidget(description)
