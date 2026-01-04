"""
Website Panel for Photo Editor
Handles website creation functionality
"""

from PyQt6.QtWidgets import QVBoxLayout, QLabel
from .base_panel import BasePanel


class WebsitePanel(BasePanel):
    """Website panel for creating photo websites"""
    
    def __init__(self):
        super().__init__("website")
    
    def _add_placeholder_content(self) -> None:
        """Add website-specific placeholder content"""
        description = QLabel(
            "Create beautiful photo galleries and websites.\n\n"
            "Features coming soon:\n"
            "• Gallery templates\n"
            "• Custom themes\n"
            "• Responsive design\n"
            "• SEO optimization\n"
            "• Social media integration\n"
            "• E-commerce support\n"
            "• Blog integration"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: rgb(180, 180, 180); font-size: 14px; line-height: 1.6;")
        self.content_layout.addWidget(description)
