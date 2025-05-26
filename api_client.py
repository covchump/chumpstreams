"""
ChumpStreams API Client

Version: 1.9.0
Author: covchump
Last updated: 2025-05-23 12:10:35

Client for interacting with IPTV service APIs
"""
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin

# Configure logging
logger = logging.getLogger(__name__)

class ApiClient:
    """Client for interacting with the IPTV API"""
    
    def __init__(self, base_url, use_https=True, username='', password=''):
        """Initialize API client"""
        protocol = 'https' if use_https else 'http'
        # Add port 80 explicitly for HTTP connections
        port = '443' if use_https else '80'
        self.base_url = f"{protocol}://{base_url}:{port}"
        self.username = username
        self.password = password
        self.token = None
        self.user_info = {}
        self.logged_in = False
        self.last_request_time = 0
        self.request_delay = 0.5  # Delay between requests in seconds
    
    def login(self, username=None, password=None):
        """Login to the IPTV service"""
        # Update credentials if provided
        if username:
            self.username = username
        if password:
            self.password = password
        
        # Ensure we have credentials
        if not self.username or not self.password:
            logger.error("Login failed: Missing username or password")
            return False
        
        # Make login request
        url = f"{self.base_url}/player_api.php"
        params = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            self._wait_for_rate_limit()
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'user_info' in data:
                self.user_info = data['user_info']
                self.token = self.user_info.get('auth', None)
                self.logged_in = True
                logger.info(f"Login successful for user: {self.username}")
                return data
            else:
                logger.error(f"Login failed: {data.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            logger.error(f"Login request failed: {str(e)}")
            return False
    
    def logout(self):
        """Logout from the IPTV service"""
        self.token = None
        self.user_info = {}
        self.logged_in = False
        logger.info(f"Logged out user: {self.username}")
        return True
    
    def get_categories(self, content_type):
        """Get categories for a content type"""
        if not self.logged_in:
            return []
        
        action_map = {
            'live': 'get_live_categories',
            'vod': 'get_vod_categories',
            'series': 'get_series_categories'
        }
        
        if content_type not in action_map:
            logger.error(f"Invalid content type: {content_type}")
            return []
        
        url = f"{self.base_url}/player_api.php"
        params = {
            'username': self.username,
            'password': self.password,
            'action': action_map[content_type]
        }
        
        try:
            self._wait_for_rate_limit()
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get categories for {content_type}: {str(e)}")
            return []
    
    def get_live_streams(self, category_id=None):
        """Get live TV streams"""
        if not self.logged_in:
            return []
        
        url = f"{self.base_url}/player_api.php"
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_live_streams'
        }
        
        if category_id:
            params['category_id'] = category_id
        
        try:
            self._wait_for_rate_limit()
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get live streams: {str(e)}")
            return []
    
    def get_vod_streams(self, category_id=None):
        """Get video on demand streams"""
        if not self.logged_in:
            return []
        
        url = f"{self.base_url}/player_api.php"
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_vod_streams'
        }
        
        if category_id:
            params['category_id'] = category_id
        
        try:
            self._wait_for_rate_limit()
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get VOD streams: {str(e)}")
            return []
    
    def get_series(self, category_id=None):
        """Get TV series"""
        if not self.logged_in:
            return []
        
        url = f"{self.base_url}/player_api.php"
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_series'
        }
        
        if category_id:
            params['category_id'] = category_id
        
        try:
            self._wait_for_rate_limit()
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get series: {str(e)}")
            return []
    
    def get_series_info(self, series_id):
        """Get info for a specific TV series"""
        if not self.logged_in:
            return None
        
        url = f"{self.base_url}/player_api.php"
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_series_info',
            'series_id': series_id
        }
        
        try:
            self._wait_for_rate_limit()
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get series info for ID {series_id}: {str(e)}")
            return None
    
    def get_vod_info(self, vod_id):
        """Get info for a specific VOD item"""
        if not self.logged_in:
            return None
        
        url = f"{self.base_url}/player_api.php"
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_vod_info',
            'vod_id': vod_id
        }
        
        try:
            self._wait_for_rate_limit()
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get VOD info for ID {vod_id}: {str(e)}")
            return None
    
    def get_live_stream_url(self, stream_id):
        """Get URL for a live stream"""
        if not self.logged_in:
            return None
        
        return f"{self.base_url}/live/{self.username}/{self.password}/{stream_id}.ts"
    
    def get_vod_stream_url(self, stream_id, extension=None):
        """Get URL for a VOD stream"""
        if not self.logged_in:
            return None
        
        # Use the provided extension or default to mp4
        ext = extension or "mp4"
        return f"{self.base_url}/movie/{self.username}/{self.password}/{stream_id}.{ext}"
    
    def get_series_stream_url(self, stream_id, extension=None):
        """Get URL for a series episode"""
        if not self.logged_in:
            return None
        
        # Use the provided extension or default to mp4
        ext = extension or "mp4"
        return f"{self.base_url}/series/{self.username}/{self.password}/{stream_id}.{ext}"
    
    def search(self, query, content_type):
        """Search for content by name"""
        if not self.logged_in or not query:
            return []
        
        query = query.lower()
        results = []
        
        if content_type == 'live':
            streams = self.get_live_streams()
            for stream in streams:
                if query in stream.get('name', '').lower():
                    results.append(stream)
        
        elif content_type == 'vod':
            streams = self.get_vod_streams()
            for stream in streams:
                if query in stream.get('name', '').lower():
                    results.append(stream)
        
        elif content_type == 'series':
            series_list = self.get_series()
            for series in series_list:
                if query in series.get('name', '').lower():
                    results.append(series)
        
        return results
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()