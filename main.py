#!/usr/bin/env python3
"""
Photo Editor - Lightroom Classic Alternative
Main entry point for the application
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('photo_editor.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Main application entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Photo Editor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Photo Editor")
    
    # Enable high DPI scaling (PyQt6 handles this automatically)
    # app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
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
