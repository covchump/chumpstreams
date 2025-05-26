"""
ChumpStreams Artwork Manager

Version: 1.0.0
Author: covchump
Last updated: 2025-05-24 11:28:42

Handles extraction and display of artwork for content
"""
import logging
import re
from PyQt5.QtCore import Qt, QObject, pyqtSlot
from PyQt5.QtGui import QPixmap

logger = logging.getLogger('chumpstreams')

class ArtworkManager(QObject):
    """Manager for handling artwork for movies and series"""
    
    def __init__(self, image_cache):
        """
        Initialize the artwork manager
        
        Args:
            image_cache: ImageCache instance for downloading/caching images
        """
        super().__init__()  # Initialize QObject properly
        self.image_cache = image_cache
        
        # Connect to cache's image_loaded signal
        self.image_cache.image_loaded.connect(self._on_image_loaded)
        
        # Keep track of which URLs are associated with which info panels
        self.active_panels = {}
    
    def extract_image_url(self, item, content_type):
        """
        Extract image URL from content item
        
        Args:
            item: Content item dict
            content_type: Type of content ('live', 'vod', 'series', etc.)
            
        Returns:
            tuple: (poster_url, backdrop_url)
        """
        poster_url = None
        backdrop_url = None
        
        try:
            # Check for direct image URLs in the item
            if 'cover' in item:
                poster_url = self._ensure_string(item['cover'])
            elif 'cover_big' in item:
                poster_url = self._ensure_string(item['cover_big'])
            elif 'stream_icon' in item:
                poster_url = self._ensure_string(item['stream_icon'])
                
            # Check for backdrop URL
            if 'backdrop_path' in item:
                backdrop_url = self._ensure_string(item['backdrop_path'])
            elif 'backdrop' in item:
                backdrop_url = self._ensure_string(item['backdrop'])
            
            # If info field exists, check there too
            if 'info' in item:
                info = item['info']
                if not poster_url and 'poster_path' in info:
                    poster_url = self._ensure_string(info['poster_path'])
                if not poster_url and 'cover' in info:
                    poster_url = self._ensure_string(info['cover'])
                if not backdrop_url and 'backdrop_path' in info:
                    backdrop_url = self._ensure_string(info['backdrop_path'])
                    
            # For VOD/Series, try to extract from the plot which might contain HTML with images
            if content_type in ['vod', 'series'] and 'plot' in item:
                plot = item.get('plot', '')
                if isinstance(plot, str):  # Ensure plot is a string before using regex
                    # Try to extract image URLs from HTML img tags
                    img_matches = re.findall(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', plot)
                    if img_matches:
                        if not poster_url:
                            poster_url = img_matches[0]
                        if len(img_matches) > 1 and not backdrop_url:
                            backdrop_url = img_matches[1]
            
            # For TMDB data, construct full URLs if needed
            if poster_url and isinstance(poster_url, str):
                if poster_url.startswith('/') and not poster_url.startswith('//'):
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_url}"
                
            if backdrop_url and isinstance(backdrop_url, str):
                if backdrop_url.startswith('/') and not backdrop_url.startswith('//'):
                    backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop_url}"
        
        except Exception as e:
            logger.error(f"Error extracting image URLs: {str(e)}")
            # Return empty URLs in case of error
            poster_url = None
            backdrop_url = None
            
        return poster_url, backdrop_url
    
    def _ensure_string(self, value):
        """
        Ensure the given value is a string
        
        Args:
            value: Value to convert to string if needed
            
        Returns:
            str: String value or None if conversion not possible
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, list) and value:
            # If it's a list, take the first item if it exists
            if isinstance(value[0], str):
                return value[0]
        elif value is not None:
            # Try to convert to string
            try:
                return str(value)
            except:
                pass
        return None
    
    def update_artwork(self, info_panel, item, content_type):
        """
        Update artwork in the info panel
        
        Args:
            info_panel: The InfoPanel instance to update
            item: Content item dict
            content_type: Type of content ('live', 'vod', 'series', etc.)
            
        Returns:
            bool: True if artwork was found and updated
        """
        try:
            poster_url, backdrop_url = self.extract_image_url(item, content_type)
            
            if not poster_url and not backdrop_url:
                logger.info(f"No artwork found for {content_type} item: {item.get('name', item.get('title', 'Unknown'))}")
                return False
                
            logger.info(f"Found artwork for {content_type}: poster={poster_url}, backdrop={backdrop_url}")
            
            # Register this panel with these URLs
            panel_id = id(info_panel)
            self.active_panels[panel_id] = {
                'panel': info_panel,
                'poster_url': poster_url,
                'backdrop_url': backdrop_url
            }
            
            # Load images (from cache or start download)
            if poster_url and hasattr(info_panel, 'set_poster'):
                poster_pixmap = self.image_cache.get_pixmap(poster_url, 300, 450)
                info_panel.set_poster(poster_pixmap)
                
            if backdrop_url and hasattr(info_panel, 'set_backdrop'):
                backdrop_pixmap = self.image_cache.get_pixmap(backdrop_url, 800, 450)
                info_panel.set_backdrop(backdrop_pixmap)
            
            return True
        except Exception as e:
            logger.error(f"Error updating artwork: {str(e)}")
            return False
    
    @pyqtSlot(str, QPixmap)
    def _on_image_loaded(self, url, pixmap):
        """
        Handle when an image has been loaded/downloaded
        
        Args:
            url: The URL of the image that was loaded
            pixmap: The QPixmap of the loaded image
        """
        try:
            # Update all panels that were waiting for this URL
            for panel_id, data in list(self.active_panels.items()):
                panel = data['panel']
                
                # Check if this panel still exists
                if not panel:
                    del self.active_panels[panel_id]
                    continue
                    
                # Check which URL matched
                if url == data['poster_url'] and hasattr(panel, 'set_poster'):
                    # Resize for poster display
                    if pixmap.height() > 450 or pixmap.width() > 300:
                        pixmap = pixmap.scaled(
                            300, 450, 
                            aspectRatioMode=Qt.KeepAspectRatio,
                            transformMode=Qt.SmoothTransformation
                        )
                    panel.set_poster(pixmap)
                    
                elif url == data['backdrop_url'] and hasattr(panel, 'set_backdrop'):
                    # Resize for backdrop display
                    if pixmap.height() > 450 or pixmap.width() > 800:
                        pixmap = pixmap.scaled(
                            800, 450, 
                            aspectRatioMode=Qt.KeepAspectRatio,
                            transformMode=Qt.SmoothTransformation
                        )
                    panel.set_backdrop(pixmap)
        except Exception as e:
            logger.error(f"Error handling loaded image: {str(e)}")