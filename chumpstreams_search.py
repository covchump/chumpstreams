"""
ChumpStreams Search Functionality

Version: 1.8.6
Author: covchump
Last updated: 2025-05-19 17:59:34

Implements search features for ChumpStreams
"""
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot

logger = logging.getLogger('chumpstreams')

class SearchWorker(QRunnable):
    """Worker for performing search in background"""
    
    class Signals(QObject):
        """Signals for SearchWorker"""
        finished = pyqtSignal(object, str)  # results, search_term
        progress = pyqtSignal(int, int)  # current, total
        error = pyqtSignal(str)  # error message
    
    def __init__(self, api, auth, search_term, content_types=None):
        super().__init__()
        self.api = api
        self.auth = auth
        self.search_term = search_term
        self.content_types = content_types or ['live', 'vod', 'series']
        self.signals = self.Signals()
    
    @pyqtSlot()
    def run(self):
        """Run search task"""
        try:
            all_results = []
            total_types = len(self.content_types)
            
            for i, content_type in enumerate(self.content_types):
                self.signals.progress.emit(i, total_types)
                
                # Get content categories
                categories = self._get_categories(content_type)
                
                # Search in each category
                for category in categories:
                    category_results = self._search_category(content_type, category)
                    all_results.extend(category_results)
            
            # Emit the final progress update
            self.signals.progress.emit(total_types, total_types)
            
            # Emit results
            self.signals.finished.emit(all_results, self.search_term)
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            self.signals.error.emit(str(e))
    
    def _get_categories(self, content_type):
        """Get content categories for the given content type"""
        try:
            if content_type == 'live':
                return self.api.get_live_categories(self.auth)
            elif content_type == 'vod':
                return self.api.get_vod_categories(self.auth)
            elif content_type == 'series':
                return self.api.get_series_categories(self.auth)
            return []
        except Exception as e:
            logger.error(f"Error getting {content_type} categories: {str(e)}")
            return []
    
    def _search_category(self, content_type, category):
        """Search for content in a specific category"""
        results = []
        category_id = category['category_id']
        category_name = category['category_name']
        
        try:
            # Get all content for this category
            if content_type == 'live':
                items = self.api.get_live_streams(self.auth, category_id)
            elif content_type == 'vod':
                items = self.api.get_vod_streams(self.auth, category_id)
            elif content_type == 'series':
                items = self.api.get_series(self.auth, category_id)
            else:
                items = []
                
            # Filter items by search term
            search_term_lower = self.search_term.lower()
            for item in items:
                # Get item name
                name = self._get_item_name(item).lower()
                
                # If search term is in name, add to results
                if search_term_lower in name:
                    # Add type and category info to item
                    item['content_type'] = content_type
                    item['category_name'] = category_name
                    results.append(item)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching {content_type} category {category_name}: {str(e)}")
            return []
    
    def _get_item_name(self, item):
        """Extract name from item"""
        if not item:
            return ""
            
        if isinstance(item, dict):
            # Try different name fields
            for field in ['name', 'title', 'stream_display_name']:
                if field in item and item[field]:
                    # Decode base64 if needed
                    return self._safe_b64decode(item[field])
                    
        return str(item)
    
    def _safe_b64decode(self, s):
        """Safely decode base64 strings with padding correction"""
        try:
            import base64
            
            if not s:
                return s
                
            data = s.strip()
            # Check if it's likely base64 encoded (heuristic)
            if all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in data):
                if len(data) % 4:
                    data += '=' * (4 - len(data) % 4)
                return base64.b64decode(data).decode('utf-8')
            return s
        except:
            return s


class SearchManager:
    """Manages search functionality"""
    
    def __init__(self, api):
        self.api = api
        self.thread_pool = QThreadPool()
        logger.info(f"Search using thread pool with maximum {self.thread_pool.maxThreadCount()} threads")
    
    def search(self, auth, search_term, content_types=None, 
              finished_callback=None, progress_callback=None, error_callback=None):
        """Perform search in background thread"""
        worker = SearchWorker(self.api, auth, search_term, content_types)
        
        if finished_callback:
            worker.signals.finished.connect(finished_callback)
        
        if progress_callback:
            worker.signals.progress.connect(progress_callback)
        
        if error_callback:
            worker.signals.error.connect(error_callback)
        
        self.thread_pool.start(worker)