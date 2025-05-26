"""
ChumpStreams Info Panel Extensions

Version: 1.0.0
Author: covchump
Last updated: 2025-05-24 12:10:25

Extensions to add artwork display capabilities to the info panel
"""
import logging
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QWidget, QSpacerItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

logger = logging.getLogger('chumpstreams')

def extend_info_panel(info_panel):
    """
    Extend the info panel with artwork display capabilities
    
    Args:
        info_panel: The InfoPanel instance to extend
    """
    logger.info("Adding artwork display capabilities to info panel (left side, top-aligned)")
    
    try:
        # Check if already extended
        if hasattr(info_panel, '_artwork_initialized'):
            logger.info("Info panel already has artwork capabilities")
            return
            
        # Store original layout for later use
        original_layout = info_panel.layout()
        if not original_layout:
            logger.error("Info panel has no layout")
            return
            
        # Create a container with HORIZONTAL layout
        container = QWidget(info_panel)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(10)
        
        # Create left side container for poster and vertical spacer
        left_container = QWidget(container)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Create poster frame with fixed dimensions
        poster_frame = QFrame(left_container)
        poster_frame.setFrameShape(QFrame.StyledPanel)
        poster_frame.setFixedWidth(180)
        poster_frame.setFixedHeight(270)
        poster_layout = QVBoxLayout(poster_frame)
        poster_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create poster label
        poster_label = QLabel(poster_frame)
        poster_label.setAlignment(Qt.AlignCenter)
        poster_label.setStyleSheet("background-color: #1A1A1A;")
        poster_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        poster_label.setScaledContents(False)  # Don't stretch images
        poster_layout.addWidget(poster_label)
        
        # Add poster frame to left layout
        left_layout.addWidget(poster_frame)
        
        # Add vertical spacer to push poster to top
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        left_layout.addItem(vertical_spacer)
        
        # Get existing content widget
        existing_content = QWidget(container)
        existing_layout = QVBoxLayout(existing_content)
        existing_layout.setContentsMargins(0, 0, 0, 0)
        
        # Move all existing widgets to the existing content layout
        while original_layout.count():
            item = original_layout.takeAt(0)
            if item.widget():
                existing_layout.addWidget(item.widget())
        
        # Add widgets to container layout (left side and main content)
        container_layout.addWidget(left_container)
        container_layout.addWidget(existing_content)
        
        # Set new layout on info panel 
        original_layout.addWidget(container)
        
        # Store references
        info_panel._poster_frame = poster_frame
        info_panel._poster_label = poster_label
        info_panel._artwork_initialized = True
        
        # Initially hide artwork elements
        info_panel._poster_frame.setVisible(False)
        
        # Add methods to the info panel
        def set_poster(self, pixmap):
            """Set poster image"""
            logger.info("Setting poster in info panel")
            if pixmap and not pixmap.isNull():
                # Scale the image to fit in our frame but maintain aspect ratio
                scaled_pixmap = pixmap.scaled(
                    170, 260,  # Target dimensions inside the frame with margins
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self._poster_label.setPixmap(scaled_pixmap)
                self._poster_frame.setVisible(True)
                logger.info(f"Poster set with dimensions: original={pixmap.width()}x{pixmap.height()}, scaled={scaled_pixmap.width()}x{scaled_pixmap.height()}")
            else:
                logger.info("Invalid poster pixmap or null")
                self._poster_frame.setVisible(False)
                
        def set_backdrop(self, pixmap):
            """
            Stub method for backdrop setting - doesn't actually display
            the backdrop to avoid layout issues
            """
            # We don't use the backdrop, but need the method for compatibility
            logger.info("Backdrop image received but not displayed (disabled)")
            pass
                
        def clear_artwork(self):
            """Clear artwork images"""
            logger.info("Clearing artwork in info panel")
            self._poster_label.clear()
            self._poster_frame.setVisible(False)
            
        # Add methods to info panel
        info_panel.set_poster = set_poster.__get__(info_panel)
        info_panel.set_backdrop = set_backdrop.__get__(info_panel)
        info_panel.clear_artwork = clear_artwork.__get__(info_panel)
        
        # Patch the original clear_info method to also clear artwork
        original_clear_info = getattr(info_panel, 'clear_info', None)
        if original_clear_info:
            def patched_clear_info(self):
                """Patched clear info to also clear artwork"""
                original_clear_info()
                self.clear_artwork()
                
            info_panel.clear_info = patched_clear_info.__get__(info_panel)
            
        logger.info("Successfully extended info panel with left side, top-aligned artwork")
        
    except Exception as e:
        logger.error(f"Error extending info panel: {str(e)}")
        logger.exception("Extension error details:")