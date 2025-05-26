"""
ChumpStreams Image Cache

Version: 1.0.0
Author: covchump
Created: 2025-05-24 11:01:16

Handles downloading, caching, and retrieving of artwork images
"""
import os
import logging
import urllib.request
import urllib.parse
import hashlib
import threading
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import QObject, pyqtSignal, Qt

logger = logging.getLogger('chumpstreams')

class ImageCache(QObject):
    """
    Image cache manager for downloading, storing and retrieving artwork
    
    Signals:
        image_loaded(str, QPixmap): Emitted when an image has been loaded
    """
    
    image_loaded = pyqtSignal(str, QPixmap)
    
    def __init__(self, cache_dir):
        """
        Initialize the image cache with a directory for cached images
        
        Args:
            cache_dir: Path to store cached images
        """
        super().__init__()
        self.cache_dir = os.path.join(cache_dir, "images")
        self.ensure_cache_dir()
        self.default_poster = None
        self.default_backdrop = None
        self._loading = {}  # Track URLs in progress to avoid duplicate requests
        
    def ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Image cache directory: {self.cache_dir}")
    
    def get_cache_path(self, url):
        """
        Get the local path for a cached image
        
        Args:
            url: The URL of the image
            
        Returns:
            str: Path to the cached image file
        """
        # Hash the URL to create a safe filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Get file extension from URL or default to .jpg
        _, ext = os.path.splitext(urllib.parse.urlparse(url).path)
        if not ext or ext == ".":
            ext = ".jpg"
            
        return os.path.join(self.cache_dir, f"{url_hash}{ext}")
    
    def is_cached(self, url):
        """
        Check if an image is already cached
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if the image is cached
        """
        if not url:
            return False
            
        cache_path = self.get_cache_path(url)
        return os.path.exists(cache_path) and os.path.getsize(cache_path) > 0
    
    def get_pixmap(self, url, max_width=None, max_height=None):
        """
        Get a QPixmap for the image, either from cache or download
        
        Args:
            url: The URL of the image
            max_width: Maximum width to resize to (optional)
            max_height: Maximum height to resize to (optional)
            
        Returns:
            QPixmap: The image pixmap or None if not available immediately
        """
        if not url:
            return self.get_default_poster() if max_height > max_width else self.get_default_backdrop()
        
        cache_path = self.get_cache_path(url)
        
        if self.is_cached(url):
            # Load from cache
            pixmap = QPixmap(cache_path)
            if pixmap.isNull():
                # Cache is corrupted, redownload
                os.remove(cache_path)
                self.download_image(url)
                return self.get_default_poster() if max_height > max_width else self.get_default_backdrop()
                
            # Resize if needed
            if max_width and max_height and (pixmap.width() > max_width or pixmap.height() > max_height):
                pixmap = pixmap.scaled(
                    max_width, max_height, 
                    aspectRatioMode=Qt.KeepAspectRatio,
                    transformMode=Qt.SmoothTransformation
                )
            return pixmap
        else:
            # Not cached, start download in background
            if url not in self._loading:
                self.download_image(url)
                
            # Return default while loading
            return self.get_default_poster() if max_height > max_width else self.get_default_backdrop()
    
    def download_image(self, url):
        """
        Download an image in the background
        
        Args:
            url: The URL of the image to download
        """
        if not url or url in self._loading:
            return
            
        self._loading[url] = True
        
        # Start a thread for the download to avoid blocking UI
        thread = threading.Thread(target=self._download_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, url):
        """
        Background thread for downloading images
        
        Args:
            url: The URL of the image to download
        """
        try:
            cache_path = self.get_cache_path(url)
            
            # Skip if already downloaded since starting thread
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                logger.info(f"Image already downloaded while thread was starting: {url}")
                del self._loading[url]
                return
                
            logger.info(f"Downloading image: {url}")
            
            # Add a user agent to avoid 403 errors from some hosts
            headers = {
                'User-Agent': 'Mozilla/5.0 ChumpStreams/2.0.4',
                'Accept': 'image/jpeg,image/png,image/*',
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response, open(cache_path, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
            
            # Verify the downloaded file is a valid image
            pixmap = QPixmap()
            if not pixmap.load(cache_path):
                logger.warning(f"Downloaded file is not a valid image: {url}")
                os.remove(cache_path)
                del self._loading[url]
                return
                
            logger.info(f"Image downloaded and cached: {url}")
            
            # Emit signal that image is loaded
            self.image_loaded.emit(url, pixmap)
            
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {str(e)}")
            # Clean up any partial downloads
            cache_path = self.get_cache_path(url)
            if os.path.exists(cache_path):
                os.remove(cache_path)
        finally:
            # Clean up loading state
            if url in self._loading:
                del self._loading[url]
    
    def get_default_poster(self):
        """Get a default poster image for when artwork is not available"""
        if self.default_poster is None:
            # Create a gray placeholder with "No Poster" text
            self.default_poster = QPixmap(300, 450)
            self.default_poster.fill(QColor(40, 40, 40))
            
        return self.default_poster
    
    def get_default_backdrop(self):
        """Get a default backdrop image for when artwork is not available"""
        if self.default_backdrop is None:
            # Create a dark placeholder
            self.default_backdrop = QPixmap(800, 450)
            self.default_backdrop.fill(QColor(20, 20, 20))
            
        return self.default_backdrop
    
    def clear_cache(self):
        """Clear all cached images"""
        count = 0
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    count += 1
                    
            logger.info(f"Cleared {count} images from cache")
            return True
        except Exception as e:
            logger.error(f"Error clearing image cache: {str(e)}")
            return False