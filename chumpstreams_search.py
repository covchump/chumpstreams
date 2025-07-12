"""
ChumpStreams Search Functionality

Version: 1.8.8
Author: covchump
Last updated: 2025-01-12 14:12:08

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
                self.signals.progress.emit(i + 1, total_types)
                
                # Use the API's search method directly
                try:
                    results = self.api.search(self.search_term, content_type)
                    
                    # Add content type to each result
                    for item in results:
                        item['content_type'] = content_type
                        all_results.append(item)
                        
                    logger.info(f"Found {len(results)} {content_type} results for '{self.search_term}'")
                    
                except Exception as e:
                    logger.error(f"Error searching {content_type}: {str(e)}")
            
            # Log total results
            logger.info(f"Total search results: {len(all_results)} for '{self.search_term}'")
            
            # Emit results
            self.signals.finished.emit(all_results, self.search_term)
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            self.signals.error.emit(str(e))
    
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