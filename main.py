#!/usr/bin/env python3
"""
Photo Editor - Lightroom Classic Alternative
Main entry point for the application
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QScreen
from src.ui.main_window import MainWindow

# Minimum required screen resolution
MIN_SCREEN_WIDTH = 1920
MIN_SCREEN_HEIGHT = 1080


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('darklab.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Main application entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    app = QApplication(sys.argv)
    app.setApplicationName("DarkLab")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("DarkLab")
    
    # Check screen resolution
    screen = app.primaryScreen()
    if screen:
        size = screen.size()
        if size.width() < MIN_SCREEN_WIDTH or size.height() < MIN_SCREEN_HEIGHT:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Insufficient Screen Resolution")
            msg_box.setText(
                f"This application requires a minimum screen resolution of "
                f"{MIN_SCREEN_WIDTH}x{MIN_SCREEN_HEIGHT} pixels.\n\n"
                f"Your current resolution: {size.width()}x{size.height()} pixels.\n\n"
                f"Please adjust your display settings or use a larger screen."
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            logger.error(
                f"Application failed to start: insufficient screen resolution "
                f"({size.width()}x{size.height()} < {MIN_SCREEN_WIDTH}x{MIN_SCREEN_HEIGHT})"
            )
            sys.exit(1)
    
    try:
        main_window = MainWindow()
        main_window.show()
        logger.info("Application started successfully")
        
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
