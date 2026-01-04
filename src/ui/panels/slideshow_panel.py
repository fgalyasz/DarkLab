"""
Slideshow Panel for Photo Editor
Handles slideshow creation and playback
"""

from PyQt6.QtWidgets import QVBoxLayout, QLabel
from .base_panel import BasePanel


class SlideshowPanel(BasePanel):
    """Slideshow panel for creating and playing slideshows"""
    
    def __init__(self):
        super().__init__("slideshow")
    
    def _add_placeholder_content(self) -> None:
        """Add slideshow-specific placeholder content"""
        description = QLabel(
            "Create and present beautiful photo slideshows.\n\n"
            "Features coming soon:\n"
            "• Timeline editor\n"
            "• Transition effects\n"
            "• Audio integration\n"
            "• Text overlays\n"
            "• Multiple aspect ratios\n"
            "• Export to video\n"
            "• Live presentation mode"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: rgb(180, 180, 180); font-size: 14px; line-height: 1.6;")
        self.content_layout.addWidget(description)
