#!/usr/bin/env python3
"""
Photo Editor - Lightroom Classic Alternative
Main entry point for the application
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QScreen
from src.startup import launch_is_allowed
from src.ui.main_window import MainWindow


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
    _refuse_missing_screen(app.primaryScreen(), logger)

    try:
        main_window = MainWindow()
        main_window.show()
        logger.info("Application started successfully")
        
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


def _refuse_missing_screen(screen: QScreen | None, logger: logging.Logger) -> None:
    width, height = _screen_size(screen)
    if launch_is_allowed(width, height):
        return
    logger.error("Application failed to start: no display")
    sys.exit(1)


def _screen_size(screen: QScreen | None) -> tuple[int, int]:
    if screen is None:
        return (0, 0)
    size = screen.size()
    return (size.width(), size.height())


if __name__ == "__main__":
    main()
