"""
ChumpStreams Content Handling

Version: 1.9.0
Author: covchump
Last updated: 2025-05-23 12:10:35

Handles content loading and processing for ChumpStreams
"""
import logging
import time
import base64
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot

logger = logging.getLogger('chumpstreams')

class ContentWorker(QRunnable):
    """Worker for loading content in background"""
    
    class Signals(QObject):
        """Signals for ContentWorker"""
        finished = pyqtSignal(object)
        error = pyqtSignal(str)
    
    def __init__(self, api, auth, content_type, category_id):
        super().__init__()
        self.api = api
        self.auth = auth
        self.content_type = content_type
        self.category_id = category_id
        self.signals = self.Signals()
    
    @pyqtSlot()
    def run(self):
        """Run content loading task"""
        try:
            if self.content_type == 'live':
                items = self.api.get_live_streams(self.category_id)
            elif self.content_type == 'vod':
                items = self.api.get_vod_streams(self.category_id)
            elif self.content_type == 'series':
                items = self.api.get_series(self.category_id)
            else:
                items = []
                
            # Process items
            processed_items = self._process_items(items, self.content_type)
                
            self.signals.finished.emit(processed_items)
        except Exception as e:
            logger.error(f"Error loading content: {str(e)}")
            self.signals.error.emit(str(e))
    
    def _process_items(self, items, content_type):
        """Process items before returning"""
        # This could include decoding names, adding additional metadata, etc.
        for item in items:
            if 'name' in item:
                item['name'] = self._safe_b64decode(item['name'])
            elif 'title' in item:
                item['title'] = self._safe_b64decode(item['title'])
                
            # Add content type to each item
            item['content_type'] = content_type
        
        return items
    
    def _safe_b64decode(self, s):
        """Safely decode base64 strings with padding correction"""
        try:
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


class InfoWorker(QRunnable):
    """Worker for loading content info in background"""
    
    class Signals(QObject):
        """Signals for InfoWorker"""
        finished = pyqtSignal(object)
        error = pyqtSignal(str)
    
    def __init__(self, api, auth, content_type, item_id):
        super().__init__()
        self.api = api
        self.auth = auth
        self.content_type = content_type
        self.item_id = item_id
        self.signals = self.Signals()
    
    @pyqtSlot()
    def run(self):
        """Run info loading task"""
        try:
            result = {}
            
            if self.content_type == 'live':
                # For live streams, no detailed info to fetch
                result = {'channel_info': self._get_stream_info(self.item_id)}
            elif self.content_type == 'vod':
                # For VOD, get movie info
                result = self.api.get_vod_info(self.item_id)
            elif self.content_type == 'series':
                # For series, get series info including episodes
                result = self.api.get_series_info(self.item_id)
            
            # Process result
            processed_result = self._process_result(result, self.content_type)
                
            self.signals.finished.emit(processed_result)
        except Exception as e:
            logger.error(f"Error loading info: {str(e)}")
            self.signals.error.emit(str(e))
    
    def _get_stream_info(self, stream_id):
        """Get basic info for a stream"""
        # This is a simplified version that doesn't attempt to get EPG data
        return {
            'stream_id': stream_id,
            'name': f"Channel {stream_id}"
        }
    
    def _process_result(self, result, content_type):
        """Process result before returning"""
        # This could include decoding names, adding additional metadata, etc.
        
        # Handle different result formats
        if content_type == 'vod':
            # Process VOD info
            if 'info' in result:
                info = result['info']
                if isinstance(info, dict):
                    if 'name' in info:
                        info['name'] = self._safe_b64decode(info['name'])
                    if 'title' in info:
                        info['title'] = self._safe_b64decode(info['title'])
                    if 'plot' in info:
                        info['plot'] = self._safe_b64decode(info['plot'])
                        
        elif content_type == 'series':
            # Process series info
            if 'info' in result:
                info = result['info']
                if isinstance(info, dict):
                    if 'name' in info:
                        info['name'] = self._safe_b64decode(info['name'])
                    if 'title' in info:
                        info['title'] = self._safe_b64decode(info['title'])
                    if 'plot' in info:
                        info['plot'] = self._safe_b64decode(info['plot'])
            
            # Process episodes
            if 'episodes' in result:
                eps = result['episodes']
                flat_episodes = []
                
                if isinstance(eps, dict):
                    # Episodes can be nested by season
                    for season_key, season_episodes in eps.items():
                        if isinstance(season_episodes, list):
                            for ep in season_episodes:
                                if isinstance(ep, dict):
                                    if 'title' in ep:
                                        ep['title'] = self._safe_b64decode(ep['title'])
                                    if 'name' in ep:
                                        ep['name'] = self._safe_b64decode(ep['name'])
                                    if 'plot' in ep or 'overview' in ep:
                                        ep['plot'] = self._safe_b64decode(ep.get('plot', ep.get('overview', '')))
                                    
                                    # Add season info if not already present
                                    if 'season' not in ep:
                                        try:
                                            # Try to parse season from key (e.g., "1" for season 1)
                                            ep['season'] = int(season_key)
                                        except:
                                            ep['season'] = season_key
                                            
                                    flat_episodes.append(ep)
                elif isinstance(eps, list):
                    # Episodes can also be a simple list
                    for ep in eps:
                        if isinstance(ep, dict):
                            if 'title' in ep:
                                ep['title'] = self._safe_b64decode(ep['title'])
                            if 'name' in ep:
                                ep['name'] = self._safe_b64decode(ep['name'])
                            if 'plot' in ep or 'overview' in ep:
                                ep['plot'] = self._safe_b64decode(ep.get('plot', ep.get('overview', '')))
                                
                            flat_episodes.append(ep)
                
                # Replace nested episodes with flat list
                result['episodes'] = flat_episodes
                
        return result
    
    def _safe_b64decode(self, s):
        """Safely decode base64 strings with padding correction"""
        try:
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


class ContentManager:
    """Manages content loading and processing"""
    
    def __init__(self, api):
        self.api = api
        self.thread_pool = QThreadPool()
        logger.info(f"Using thread pool with maximum {self.thread_pool.maxThreadCount()} threads")
    
    def load_content(self, auth, content_type, category_id, callback, error_callback):
        """Load content in background thread"""
        worker = ContentWorker(self.api, auth, content_type, category_id)
        worker.signals.finished.connect(callback)
        worker.signals.error.connect(error_callback)
        self.thread_pool.start(worker)
    
    def load_info(self, auth, content_type, item_id, callback, error_callback):
        """Load content info in background thread"""
        worker = InfoWorker(self.api, auth, content_type, item_id)
        worker.signals.finished.connect(callback)
        worker.signals.error.connect(error_callback)
        self.thread_pool.start(worker)
    
    def extract_stream_url(self, api, auth, item, content_type):
        """Extract stream URL from item based on content type"""
        try:
            if content_type == 'live':
                stream_id = item.get('stream_id')
                if not stream_id:
                    return None
                    
                return api.get_live_stream_url(stream_id)
                
            elif content_type == 'vod':
                stream_id = item.get('stream_id') or item.get('vod_id')
                # Get the container extension if available
                ext = item.get('container_extension', 'mp4')
                
                if not stream_id:
                    return None
                    
                # First try to get URL from VOD info
                try:
                    info = api.get_vod_info(stream_id)
                    url = info.get('info', {}).get('stream_url') or info.get('info', {}).get('playlist_url')
                    if url:
                        return url
                except:
                    pass
                    
                # Fallback to direct URL construction with the correct extension
                return api.get_vod_stream_url(stream_id, ext)
                
            elif content_type == 'series':
                # Episodes need special handling - this assumes the item is an episode
                stream_id = item.get('id') or item.get('stream_id')
                # Get the container extension if available
                ext = item.get('container_extension', 'mp4')
                
                if not stream_id:
                    return None
                    
                # Use the correct extension for the series stream URL
                return api.get_series_stream_url(stream_id, ext)
                
            return None
        except Exception as e:
            logger.error(f"Error extracting stream URL: {str(e)}")
            return None