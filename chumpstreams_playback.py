"""
ChumpStreams Playback Manager

Version: 2.0.6-store-urls
Author: covchump
Last updated: 2025-05-25 21:05:00

Handles playback of content for ChumpStreams application
"""
import logging

logger = logging.getLogger('chumpstreams')

class PlaybackManager:
    """Manages content playback"""
    
    def __init__(self, api, auth, content_manager, player, settings, use_https=True, server=""):
        self.api = api
        self.auth = auth
        self.content_manager = content_manager
        self.player = player
        self.buffer_settings = settings
        self.USE_HTTPS = use_https
        self.SERVER = server
    
    def update_auth(self, auth):
        """Update authentication details"""
        self.auth = auth
    
    def update_buffer_settings(self, buffer_settings):
        """Update buffer settings"""
        self.buffer_settings = buffer_settings
    
    def play_content(self, item, content_type, window=None, original_type=None):
        """Play content item using stored URL for favorites"""
        # Check if this is a favorite with a stored stream URL
        if original_type == 'favorites':
            # Look for stream URL at top level or in item
            stream_url = None
            
            # Check top level
            if '_stream_url' in item:
                stream_url = item['_stream_url']
                logger.info("Using stored top-level stream URL from favorite")
            
            # Check item level if available
            elif 'item' in item and isinstance(item['item'], dict) and '_stream_url' in item['item']:
                stream_url = item['item']['_stream_url']
                logger.info("Using stored item-level stream URL from favorite")
            
            # If we have a stream URL, use it directly
            if stream_url:
                # Get content name
                content_name = item.get('label', item.get('name', item.get('title', 'Unknown')))
                
                # Play content with stored URL
                simple_mode = window.get_simple_mode() if window else False
                self.player.play(stream_url, content_type, content_name, self.buffer_settings, simple_mode)
                
                if window:
                    window.show_status_message(f"Playing: {content_name}")
                return True
            
            # Handle special favorite types
            fav_type = item.get('type', '')
            if fav_type == 'episode':
                return self.play_episode(item.get('item', {}), window)
            elif fav_type in ['series', 'full_series']:
                if window:
                    window.show_info_message("Series", "Please select an episode to play")
                return False
                
            # If no stored URL, try reconstructing it
            logger.info(f"No stored URL found in favorite, trying to reconstruct")
            
            # Get the item from the favorite
            if 'item' in item and isinstance(item['item'], dict):
                content_type = fav_type  # Use the favorite's type
                item = item['item']  # Use the nested item for URL extraction
        
        # For non-favorites or favorites without stored URL, use normal extraction
        content_name = item.get('name', item.get('title', 'Unknown'))
        
        # Get URL from content manager
        url = self.content_manager.extract_stream_url(
            self.api, 
            self.auth, 
            item, 
            content_type
        )
        
        # As a backup, try direct URL construction for live/VOD
        if not url:
            logger.info("Trying direct URL construction as fallback")
            try:
                if content_type == 'live' and 'stream_id' in item:
                    stream_id = item['stream_id']
                    username = self.auth.get('username', '')
                    password = self.auth.get('password', '')
                    url = f"http{'s' if self.USE_HTTPS else ''}://{self.SERVER}/live/{username}/{password}/{stream_id}.ts"
                    logger.info(f"Directly constructed live URL: {url[:30]}...")
                elif content_type == 'vod':
                    stream_id = item.get('vod_id', item.get('stream_id'))
                    if stream_id:
                        ext = item.get('container_extension', 'mp4')
                        username = self.auth.get('username', '')
                        password = self.auth.get('password', '')
                        url = f"http{'s' if self.USE_HTTPS else ''}://{self.SERVER}/movie/{username}/{password}/{stream_id}.{ext}"
                        logger.info(f"Directly constructed VOD URL: {url[:30]}...")
            except Exception as e:
                logger.error(f"Error in direct URL construction: {str(e)}")
        
        if not url:
            if window:
                window.show_error_message("Playback", "Could not get stream URL")
            logger.error(f"Failed to get stream URL for {content_type}: {content_name}")
            return False
        
        # Play content
        simple_mode = window.get_simple_mode() if window else False
        self.player.play(url, content_type, content_name, self.buffer_settings, simple_mode)
        
        if window:
            window.show_status_message(f"Playing: {content_name}")
        return True
    
    def play_episode(self, episode, window=None):
        """Play selected episode"""
        # Check for stored stream URL in episode
        if '_stream_url' in episode:
            stream_url = episode['_stream_url']
            episode_name = episode.get('title', episode.get('name', 'Unknown Episode'))
            
            logger.info(f"Using stored stream URL from episode favorite")
            
            # Play content with the stored URL
            simple_mode = window.get_simple_mode() if window else False
            self.player.play(stream_url, 'vod', episode_name, self.buffer_settings, simple_mode)
            
            if window:
                window.show_status_message(f"Playing: {episode_name}")
            return True
        
        # Get episode name for display
        episode_name = episode.get('title', episode.get('name', 'Unknown Episode'))
        
        # Get URL
        url = self.content_manager.extract_stream_url(
            self.api,
            self.auth,
            episode,
            'series'
        )
        
        # As a backup, try direct URL construction
        if not url:
            try:
                stream_id = episode.get('id')
                if stream_id:
                    ext = episode.get('container_extension', 'mp4')
                    username = self.auth.get('username', '')
                    password = self.auth.get('password', '')
                    url = f"http{'s' if self.USE_HTTPS else ''}://{self.SERVER}/series/{username}/{password}/{stream_id}.{ext}"
                    logger.info(f"Directly constructed episode URL: {url[:30]}...")
            except Exception as e:
                logger.error(f"Error in direct episode URL construction: {str(e)}")
        
        if not url:
            if window:
                window.show_error_message("Playback", "Could not get episode stream URL")
            return False
        
        # Play content
        simple_mode = window.get_simple_mode() if window else False
        self.player.play(url, 'vod', episode_name, self.buffer_settings, simple_mode)
        
        if window:
            window.show_status_message(f"Playing: {episode_name}")
        return True