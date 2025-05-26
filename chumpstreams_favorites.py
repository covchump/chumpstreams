"""
ChumpStreams Favorites Manager

Version: 2.0.2
Author: covchump
Last updated: 2025-05-26 14:55:27

Manager for handling favorites
"""
import os
import json
import logging
from copy import deepcopy

logger = logging.getLogger('chumpstreams')

class FavoritesManager:
    """Manager for handling favorites"""
    
    def __init__(self, config_file):
        """Initialize favorites manager with config file path"""
        self.config_file = config_file
        self.favorites = []
        self.api = None  # Will be set by main app
        
        # Load favorites from config if exists
        self._load_favorites()
    
    def _load_favorites(self):
        """Load favorites from config file"""
        if not os.path.exists(self.config_file):
            logger.info("No config file found for favorites")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            if 'favorites' in config:
                self.favorites = config['favorites']
                logger.info(f"Loaded {len(self.favorites)} favorites from config")
        except Exception as e:
            logger.error(f"Error loading favorites: {e}")
    
    def _save_favorites(self):
        """Save favorites to config file"""
        if not os.path.exists(self.config_file):
            # Create empty config
            config = {}
        else:
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Error reading config for saving favorites: {e}")
                config = {}
        
        # Update favorites
        config['favorites'] = self.favorites
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved {len(self.favorites)} favorites to config")
        except Exception as e:
            logger.error(f"Error saving favorites: {e}")
    
    def get_all_favorites(self):
        """Get all favorites"""
        return self.favorites
    
    def get_empty_favorites_message(self):
        """Get the message to display when favorites are empty"""
        return {
            "title": "No Favorites Found",
            "message": (
                "To add content to Favorites:\n"
                "• Right-click on any content and select 'Add to Favorites'\n\n"
                "To remove from Favorites:\n"
                "• Select content in Favorites tab, right-click and select 'Remove from Favorites'"
            )
        }
    
    def add_favorite(self, item, content_type):
        """Add an item to favorites with stored stream URL"""
        # Create a copy of the item to avoid modifying original
        item_copy = deepcopy(item)
        
        # Store the stream URL directly if the API is available
        if self.api:
            try:
                # Extract the stream URL using the same method as playback
                stream_url = None
                if content_type == 'live':
                    stream_id = item.get('stream_id')
                    if stream_id:
                        stream_url = self.api.get_live_stream_url(stream_id)
                elif content_type == 'vod':
                    stream_id = item.get('vod_id') or item.get('stream_id')
                    if stream_id:
                        stream_url = self.api.get_vod_stream_url(stream_id, item.get('container_extension', 'mp4'))
                elif content_type == 'series' and 'id' in item:
                    # For episodes directly
                    stream_url = self.api.get_series_stream_url(item.get('id'), item.get('container_extension', 'mp4'))
                
                # Store the stream URL in the favorite
                if stream_url:
                    item_copy['_stream_url'] = stream_url
                    logger.info(f"Stored stream URL in favorite: {stream_url[:30]}...")
            except Exception as e:
                logger.error(f"Error storing stream URL in favorite: {str(e)}")
        
        # Create a favorite entry with metadata
        favorite = {
            'type': content_type,
            'label': item_copy.get('name', item_copy.get('title', 'Unknown')),
            'item': item_copy
        }
        
        # Also store stream URL at top level for easier access
        if '_stream_url' in item_copy:
            favorite['_stream_url'] = item_copy['_stream_url']
        
        # Check if already in favorites
        if self._find_favorite_index(item_copy, content_type) >= 0:
            logger.info(f"Item already in favorites: {favorite['label']}")
            return
        
        # Add to favorites
        self.favorites.append(favorite)
        
        # Save to file
        self._save_favorites()
        logger.info(f"Added to favorites: {favorite['label']} ({content_type})")
    
    def remove_favorite(self, item, content_type):
        """Remove an item from favorites"""
        index = self._find_favorite_index(item, content_type)
        if index >= 0:
            return self.remove_favorite_by_index(index)
        return False
    
    def remove_favorite_by_index(self, index):
        """Remove a favorite by index"""
        if index < 0 or index >= len(self.favorites):
            logger.error(f"Invalid favorite index: {index}")
            return False
        
        # Get favorite info for logging
        favorite = self.favorites[index]
        label = favorite.get('label', 'Unknown')
        content_type = favorite.get('type', 'unknown')
        
        # Remove from list
        self.favorites.pop(index)
        
        # Save to file
        self._save_favorites()
        logger.info(f"Removed from favorites: {label} ({content_type})")
        return True
    
    def _find_favorite_index(self, item, content_type):
        """Find index of item in favorites"""
        # For live and vod, search by stream_id/vod_id
        if content_type in ['live', 'vod']:
            item_id = item.get('stream_id', item.get('vod_id'))
            if not item_id:
                return -1
                
            for i, favorite in enumerate(self.favorites):
                if favorite.get('type') != content_type:
                    continue
                    
                fav_item = favorite.get('item', {})
                fav_id = fav_item.get('stream_id', fav_item.get('vod_id'))
                
                if fav_id and fav_id == item_id:
                    return i
        
        # For series, search by series_id
        elif content_type in ['series', 'full_series']:
            series_id = item.get('series_id')
            if not series_id:
                return -1
                
            for i, favorite in enumerate(self.favorites):
                if favorite.get('type') not in ['series', 'full_series']:
                    continue
                    
                fav_item = favorite.get('item', {})
                fav_id = fav_item.get('series_id')
                
                if fav_id and fav_id == series_id:
                    return i
        
        # For episodes, search by id
        elif content_type == 'episode':
            episode_id = item.get('id')
            if not episode_id:
                return -1
                
            for i, favorite in enumerate(self.favorites):
                if favorite.get('type') != 'episode':
                    continue
                    
                fav_item = favorite.get('item', {})
                fav_id = fav_item.get('id')
                
                if fav_id and fav_id == episode_id:
                    return i
                
        return -1
    
    def is_favorite(self, item, content_type):
        """Check if an item is a favorite"""
        return self._find_favorite_index(item, content_type) >= 0
    
    def toggle_favorite(self, item, content_type):
        """Toggle favorite status of an item"""
        if self.is_favorite(item, content_type):
            self.remove_favorite(item, content_type)
            return False
        else:
            self.add_favorite(item, content_type)
            return True
    
    def add_series_favorite(self, series):
        """Add a series to favorites"""
        # Create a copy of the item to avoid modifying original
        series_copy = deepcopy(series)
        
        # Create a favorite entry with metadata
        favorite = {
            'type': 'full_series',
            'label': series_copy.get('name', 'Unknown Series'),
            'item': series_copy
        }
        
        # Check if already in favorites
        if self._find_favorite_index(series_copy, 'full_series') >= 0:
            logger.info(f"Series already in favorites: {favorite['label']}")
            return
        
        # Add to favorites
        self.favorites.append(favorite)
        
        # Save to file
        self._save_favorites()
        logger.info(f"Added series to favorites: {favorite['label']}")
    
    def remove_series_favorite(self, series):
        """Remove a series from favorites"""
        index = self._find_favorite_index(series, 'full_series')
        if index < 0:
            # Try with 'series' type as well
            index = self._find_favorite_index(series, 'series')
            
        if index >= 0:
            # Get favorite info for logging
            favorite = self.favorites[index]
            label = favorite.get('label', 'Unknown')
            
            # Remove from list
            self.favorites.pop(index)
            
            # Save to file
            self._save_favorites()
            logger.info(f"Removed series from favorites: {label}")
            return True
        
        return False
    
    def is_series_favorite(self, series):
        """Check if a series is a favorite"""
        return (self._find_favorite_index(series, 'full_series') >= 0 or
                self._find_favorite_index(series, 'series') >= 0)
    
    def toggle_series_favorite(self, series):
        """Toggle favorite status of a series"""
        if self.is_series_favorite(series):
            self.remove_series_favorite(series)
            return False
        else:
            self.add_series_favorite(series)
            return True
    
    def migrate_old_favorites(self):
        """Migrate old format favorites to enhanced format if needed"""
        needs_migration = False
        
        # Check if any items need migration
        for fav in self.favorites:
            if 'type' not in fav or 'label' not in fav or 'item' not in fav:
                needs_migration = True
                break
        
        if not needs_migration:
            return
            
        logger.info("Migrating old favorites format to enhanced format")
        new_favorites = []
        
        for fav in self.favorites:
            # Skip entries that already have the new format
            if 'type' in fav and 'label' in fav and 'item' in fav:
                new_favorites.append(fav)
                continue
            
            # Determine type and create new format entry
            if 'stream_id' in fav and 'stream_type' in fav:
                if fav['stream_type'] == 'live':
                    content_type = 'live'
                else:
                    content_type = 'vod'
                
                new_fav = {
                    'type': content_type,
                    'label': fav.get('name', 'Unknown'),
                    'item': deepcopy(fav)
                }
                new_favorites.append(new_fav)
            elif 'series_id' in fav:
                new_fav = {
                    'type': 'full_series',
                    'label': fav.get('name', 'Unknown Series'),
                    'item': deepcopy(fav)
                }
                new_favorites.append(new_fav)
        
        # Update favorites list
        self.favorites = new_favorites
        
        # Save to file
        self._save_favorites()
        logger.info(f"Migrated {len(self.favorites)} favorites to enhanced format")
    
    def update_favorite_stream_urls(self):
        """Update all favorites with direct stream URLs"""
        if not self.api:
            logger.error("Cannot update stream URLs: API not available")
            return False
            
        updated_count = 0
        for favorite in self.favorites:
            content_type = favorite.get('type', '')
            item = favorite.get('item', {})
            
            try:
                if content_type == 'live':
                    stream_id = item.get('stream_id')
                    if stream_id:
                        stream_url = self.api.get_live_stream_url(stream_id)
                        if stream_url:
                            favorite['_stream_url'] = stream_url
                            item['_stream_url'] = stream_url
                            updated_count += 1
                
                elif content_type == 'vod':
                    stream_id = item.get('vod_id') or item.get('stream_id')
                    if stream_id:
                        stream_url = self.api.get_vod_stream_url(stream_id, item.get('container_extension', 'mp4'))
                        if stream_url:
                            favorite['_stream_url'] = stream_url
                            item['_stream_url'] = stream_url
                            updated_count += 1
                
                elif content_type == 'episode':
                    stream_id = item.get('id')
                    if stream_id:
                        stream_url = self.api.get_series_stream_url(stream_id, item.get('container_extension', 'mp4'))
                        if stream_url:
                            favorite['_stream_url'] = stream_url
                            item['_stream_url'] = stream_url
                            updated_count += 1
            
            except Exception as e:
                logger.error(f"Error updating stream URL for {favorite.get('label')}: {str(e)}")
        
        # Save to file
        if updated_count > 0:
            self._save_favorites()
            logger.info(f"Updated stream URLs for {updated_count} favorites")
            
        return updated_count > 0

    # New methods to improve synchronization between UI elements
    def update_favorite_status(self, item, content_type, is_favorite):
        """Update favorite status in the item"""
        if not item:
            return
        
        # Set is_favorite flag on the item for UI consistency
        item['is_favorite'] = is_favorite

    def sync_favorite_status(self, items, content_type):
        """Sync favorite status for a list of items"""
        if not items:
            return
            
        # For each item, set its favorite status
        for item in items:
            is_fav = self.is_favorite(item, content_type)
            item['is_favorite'] = is_fav
    
    def debug_favorites(self):
        """Get debug information about favorites"""
        debug_info = []
        
        for i, fav in enumerate(self.favorites):
            # Basic info
            info = {
                'index': i,
                'label': fav.get('label', 'Unknown'),
                'type': fav.get('type', 'unknown'),
                'has_stream_url': '_stream_url' in fav or ('item' in fav and '_stream_url' in fav.get('item', {})),
                'ids': {}
            }
            
            # Extract IDs
            if 'item' in fav:
                item = fav['item']
                for id_field in ['stream_id', 'vod_id', 'id', 'series_id']:
                    if id_field in item:
                        info['ids'][id_field] = item[id_field]
            
            debug_info.append(info)
            
        return debug_info