#!/usr/bin/env python3
"""Main entry point for the LLM Chat application."""

import sys
import asyncio
import argparse
from pathlib import Path

# Ensure the package is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from llm_chat.gui.main_window import MainWindow
from llm_chat.utils.config_manager import ConfigManager
from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LLM Chat - Local LLM Chat Interface"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="Start minimized to system tray",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    return parser.parse_args()


def main():
    """Main application entry point."""
    args = parse_args()
    
    # Set up logging
    if args.debug:
        import logging
        setup_logger("llm_chat", level=logging.DEBUG)
    
    logger.info("Starting LLM Chat application")
    
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("LLM Chat")
    app.setOrganizationName("SSMIS")
    app.setOrganizationDomain("ssmis.local")
    
    # Set up async event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Load configuration
    config_manager = ConfigManager(args.config)
    settings = config_manager.load()
    
    # Create main window
    window = MainWindow(config_manager)
    
    # Handle start minimized
    if args.minimized or settings.ui.start_minimized:
        window.hide()
    else:
        window.show()
    
    logger.info("Application started")
    
    # Run application
    exit_code = app.exec_()
    
    logger.info("Application exiting")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
