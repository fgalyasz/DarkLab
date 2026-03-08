"""
Library Browser Panel for Photo Editor
Handles library browsing features separately from import.
"""

from PyQt6.QtWidgets import QLabel

from .base_panel import BasePanel


class LibraryBrowserPanel(BasePanel):
    """Library panel placeholder for future library browsing workflows."""

    def __init__(self):
        super().__init__("library")

    def _add_placeholder_content(self) -> None:
        """Add library-specific placeholder content."""
        description = QLabel(
            "Browse and manage your imported photo library here.\n\n"
            "Planned features:\n"
            "- Folder-based library browsing\n"
            "- Search and filtering\n"
            "- Ratings and flags overview\n"
            "- Collection management\n"
            "- Library maintenance tools"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: rgb(180, 180, 180); font-size: 14px; line-height: 1.6;")
        self.content_layout.addWidget(description)
