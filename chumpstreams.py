"""
ChumpStreams Application

Version: 2.0.6
Author: covchump
Last updated: 2025-01-12 13:35:13

Main entry point for ChumpStreams application
"""
import sys
import os
import logging
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer  # QTimer is in QtCore, not QtWidgets

# Setup logging
from chumpstreams_config import LOG_FILE, VERSION
from chumpstreams_logging import setup_logging

logger = setup_logging(LOG_FILE)
logger.info("Starting ChumpStreams application")

# Import components
try:
    from chumpstreams_app import ChumpStreamsApp
    from chumpstreams_player import QtVlcPlayer
    from chumpstreams_splash import show_splash_screen
    from chumpstreams_patches import patch_login_dialog
    from chumpstreams_ui import ChumpStreamsMainWindow
    from chumpstreams_login_dialog import show_login_dialog
    logger.info("Successfully imported all modules")
except Exception as e:
    logger.critical(f"Failed to import modules: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

# Apply patches
patch_login_dialog(ChumpStreamsMainWindow, show_login_dialog)

def main():
    """Application entry point"""
    logger.info("Starting main application function")
    
    # Kill any existing VLC processes
    try:
        player = QtVlcPlayer()
        player.kill_all_vlc_processes()
    except Exception as e:
        logger.error(f"Failed to kill existing VLC processes: {str(e)}")
        
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("ChumpStreams")
    app.setApplicationVersion(VERSION)
    logger.info("QApplication created")
    
    try:
        # Show splash screen first
        splash = show_splash_screen(app, 10000)  # Show for 10 seconds
        
        # Create and run the application while splash is showing
        chumpstreams = ChumpStreamsApp(app)
        
        # When splash is done, show the main window
        def show_main_window():
            if not chumpstreams.window.isVisible():
                chumpstreams.window.show()
                logger.info("Main window displayed")
        
        # Use timer to check if splash is still visible
        def check_splash():
            if splash.isVisible():
                QTimer.singleShot(100, check_splash)
            else:
                show_main_window()
        
        # Start checking
        QTimer.singleShot(100, check_splash)
        
        # Handle application close
        app.aboutToQuit.connect(lambda: chumpstreams.player.close(force=True))
        
        logger.info("Entering Qt event loop")
        return app.exec_()
    except Exception as e:
        logger.critical(f"Failed to initialize application: {str(e)}")
        logger.critical(traceback.format_exc())
        QMessageBox.critical(None, "Critical Error", f"Application failed to start: {str(e)}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Application crashed: {str(e)}", exc_info=True)
        # Display a critical error message to the user
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("ChumpStreams - Critical Error")
        error_box.setText(f"The application crashed due to an error:\n{str(e)}")
        error_box.setDetailedText(traceback.format_exc())
        error_box.exec_()
        
        # Force exit if all else fails
        os._exit(1)