"""
Base Panel Class for Photo Editor
Provides common functionality for all panels
"""

import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class BasePanel(QWidget):
    """Base class for all panels"""
    
    def __init__(self, panel_name: str):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{panel_name}")
        self.panel_name = panel_name
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup basic UI structure"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # Panel title
        self.title_label = QLabel(self.panel_name.title())
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.title_label)
        
        # Content area
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.main_layout.addWidget(self.content_frame)
        
        # Add placeholder content
        self._add_placeholder_content()
    
    def clear_content(self) -> None:
        """Clear placeholder content and setup for custom content"""
        if hasattr(self, 'content_frame') and self.content_frame:
            # Remove from main layout
            self.main_layout.removeWidget(self.content_frame)
            self.content_frame.deleteLater()
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.main_layout.addWidget(self.content_frame)
    
    def _add_placeholder_content(self) -> None:
        """Add placeholder content for the panel"""
        placeholder_label = QLabel(f"{self.panel_name.title()} panel - Coming soon!")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: rgb(180, 180, 180); font-size: 18px;")
        self.content_layout.addWidget(placeholder_label)
    
    def get_panel_name(self) -> str:
        """Get panel name"""
        return self.panel_name
    
    def on_activate(self) -> None:
        """Called when panel is activated"""
        self.logger.info(f"Panel {self.panel_name} activated")
    
    def on_deactivate(self) -> None:
        """Called when panel is deactivated"""
        self.logger.info(f"Panel {self.panel_name} deactivated")
