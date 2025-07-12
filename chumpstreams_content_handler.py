"""
ChumpStreams Content Handler

Version: 1.0.0
Author: covchump
Created: 2025-07-12 18:47:07

Handles content loading, display, and interaction for ChumpStreams
"""
import logging
import traceback
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger('chumpstreams')

class ContentHandler(QObject):
    """Handler for content-related operations"""
    
    def __init__(self, window, ui_manager, content_manager, auth_manager, 
                 favorites_manager, search_manager, artwork_manager,
                 epg_handler, playback_manager, player):
        """Initialize the content handler"""
        super().__init__()
        self.window = window
        self.ui_manager = ui_manager
        self.content_manager = content_manager
        self.auth_manager = auth_manager
        self.favorites_manager = favorites_manager
        self.search_manager = search_manager
        self.artwork_manager = artwork_manager
        self.epg_handler = epg_handler
        self.playback_manager = playback_manager
        self.player = player
        
        # Initialize state
        self.content_type = 'live'  # Default content type
        self.content_items = []  # Current content items
        self.displayed_category = ""  # Currently displayed category
        self.current_series = None  # Currently displayed series
        self.episodes = []  # Episodes for the current series
        self.search_results = []  # Search results
        self.categories_by_type = {
            "live": [],
            "vod": [],
            "series": []
        }

    def set_categories(self, categories_by_type):
        """Set the categories by content type"""
        self.categories_by_type = categories_by_type

    def update_categories_for_type(self, content_type):
        """Update categories in UI for selected content type"""
        if content_type == 'favorites':
            self._display_favorites()
            return
        
        categories = self.categories_by_type.get(content_type, [])
        category_names = [cat['category_name'] for cat in categories]
        
        logger.info(f"Updating UI with {len(category_names)} {content_type} categories")
        
        # Update category list in UI
        self.window.category_panel.categories_list.clear()
        self.window.category_panel.categories_list.addItems(category_names)
        
        # Process events to ensure UI updates
        QApplication.processEvents()
        
        # Log actual count
        after_count = self.window.category_panel.categories_list.count()
        logger.info(f"After UI update: {after_count} items in category list")
        
        # If categories exist, select a default one
        if category_names:
            # Get the default category for this content type
            from chumpstreams_config import DEFAULT_CATEGORIES
            default = DEFAULT_CATEGORIES.get(content_type, '')
            logger.info(f"Looking for default category: {default}")
            
            # Try to find exact match first
            if default in category_names:
                category_name = default
                logger.info(f"Found exact match for default category: {category_name}")
            else:
                # Try to find partial match
                for name in category_names:
                    if "uk" in name.lower() and "entertainment" in name.lower():
                        category_name = name
                        logger.info(f"Found partial match for default category: {category_name}")
                        break
                        
                # If still no match, use first category
                if not 'category_name' in locals() and category_names:
                    category_name = category_names[0]
                    logger.info(f"Using first category as default: {category_name}")
            
            # Select the category in the UI
            if 'category_name' in locals():
                logger.info(f"Selecting default category: {category_name}")
                items = self.window.category_panel.categories_list.findItems(category_name, Qt.MatchExactly)
                if items:
                    self.window.category_panel.categories_list.setCurrentItem(items[0])
                    # Load content for the default category
                    self._load_content_for_category(content_type, category_name)

    def on_category_changed(self, content_type, category_name):
        """Handle category change"""
        logger.info(f"Category changed: {content_type}, {category_name}")
        self.content_type = content_type
        
        if content_type == 'favorites':
            # Display favorites
            self._display_favorites()
            return
        
        if not self.auth_manager.get_auth():
            # Not logged in, can't show content
            self.window.content_panel.clear_content()
            self.window.info_panel.clear_info()
            self.window.show_status_message("Please log in to view content")
            return
        
        # If category name is empty but content type changed, 
        # update the categories for that type
        if not category_name:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.update_categories_for_type(content_type))
            return
        
        # Load content for the specified category
        self._load_content_for_category(content_type, category_name)

    def _load_content_for_category(self, content_type, category_name):
        """Load content for the selected category"""
        auth = self.auth_manager.get_auth()
        if not auth:
            return
            
        self.window.show_status_message(f"Loading {category_name}...")
        
        try:
            # Find category ID
            category_id = None
            for cat in self.categories_by_type[content_type]:
                if cat['category_name'] == category_name:
                    category_id = cat['category_id']
                    break
            
            if not category_id:
                self.window.show_error_message("Error", f"Category not found: {category_name}")
                return
                
            # Use content manager to load content
            self.content_manager.load_content(
                auth,
                content_type,
                category_id,
                lambda items: self._on_content_loaded(items, content_type),
                lambda error: self._on_content_error(error)
            )
            
        except Exception as e:
            logger.error(f"Error setting up content load: {str(e)}")
            self.window.show_error_message("Error", f"Failed to load content: {str(e)}")

    def _on_content_loaded(self, items, content_type):
        """Handle loaded content"""
        # Store items
        self.content_items = items
        
        # Set content items on the content panel for the context menu to work
        if hasattr(self.window.content_panel, 'content_items'):
            self.window.content_panel.content_items = items
        if hasattr(self.window.content_panel, 'content_type'):
            self.window.content_panel.content_type = content_type
        
        # Pre-mark favorites for UI consistency
        for item in items:
            is_fav = self.favorites_manager.is_favorite(item, content_type)
            item['is_favorite'] = is_fav
        
        # Extract display names
        display_names = []
        for item in items:
            name = item.get('name', item.get('title', 'Unknown'))
            if content_type == 'live':
                display_names.append(name)
            elif content_type == 'vod':
                # Add year to movie name if available
                if 'year' in item:
                    display_names.append(f"{name} ({item['year']})")
                else:
                    display_names.append(name)
            elif content_type == 'series':
                display_names.append(name)
        
        # Update content panel
        self.ui_manager.update_content(content_type, items, display_names)
        
        # Clear info panel
        self.ui_manager.clear_info()
        
        # Update status
        self.ui_manager.show_status_message(f"Loaded {len(items)} items")
        
        # Re-apply right-click favorites menu in case the content list was recreated
        from chumpstreams_patches import enable_favorite_context_menu
        if hasattr(self.window, 'content_panel'):
            enable_favorite_context_menu(self.window.content_panel)

    def _on_content_error(self, error):
        """Handle content loading error"""
        self.window.show_error_message("Error", f"Failed to load content: {error}")
        self.window.show_status_message("Error loading content")

    def _display_favorites(self):
        """Display favorites in the content panel"""
        # Extract items from favorites
        items = self.favorites_manager.get_all_favorites()
        
        # No need to load anything, just display
        if not items:
            # First clear existing content
            self.window.content_panel.clear_content()
            self.window.info_panel.clear_info()
            
            # Show empty favorites message with instructions
            empty_message = self.favorites_manager.get_empty_favorites_message()
            self.window.content_panel.show_empty_message(
                empty_message["message"],
                empty_message["title"]
            )
            
            # Clear categories
            self.window.category_panel.set_categories([])
            
            # Also show brief status
            self.window.show_status_message("No favorites")
            return
            
        # Extract display names
        display_names = [fav.get('label', 'Unknown') for fav in items]
        
        # Update content panel
        self.ui_manager.update_content('favorites', items, display_names)
        
        # Set content items on the content panel for the context menu to work
        if hasattr(self.window.content_panel, 'content_items'):
            self.window.content_panel.content_items = items
        if hasattr(self.window.content_panel, 'content_type'):
            self.window.content_panel.content_type = 'favorites'
        
        # Clear info panel
        self.ui_manager.clear_info()
        
        # Clear categories
        self.window.category_panel.set_categories([])
        
        # Update status
        self.window.show_status_message(f"Loaded {len(items)} favorites")
        
        # Re-apply right-click favorites menu in case the content list was recreated
        from chumpstreams_patches import enable_favorite_context_menu
        if hasattr(self.window, 'content_panel'):
            enable_favorite_context_menu(self.window.content_panel)

    def on_content_selected(self, items, index):
        """Handle content selection"""
        if index < 0 or index >= len(items):
            return
            
        item = items[index]
        
        # Determine content type
        if self.content_type == 'search':
            # For search results, get the content type from the item itself
            content_type = item.get('content_type', 'unknown')
            logger.info(f"Search result selected, item type: {content_type}, item name: {item.get('name', 'Unknown')}")
        elif self.content_type == 'favorites':
            # For favorites, get type from item
            content_type = item.get('type', '')
            item = item.get('item', {})
        else:
            # Use the current content type
            content_type = self.content_type
            
        # Load info based on content type
        if content_type == 'live':
            self._load_live_info(item)
        elif content_type == 'vod':
            self._load_vod_info(item)
        elif content_type == 'series' or content_type == 'full_series':
            self._load_series_info(item)
        elif content_type == 'episode':
            self._display_episode_info(item)
        else:
            logger.error(f"Unknown content type: {content_type}")
            self.window.show_error_message("Error", f"Unknown content type: {content_type}")

    def _load_live_info(self, channel):
        """Load info for live channel"""
        self.window.show_status_message("Loading channel info...")
        
        # Get stream ID
        stream_id = channel.get('stream_id')
        if not stream_id:
            self.window.info_panel.set_content_info(channel, 'live')
            return
            
        # Use content manager to load info
        self.content_manager.load_info(
            self.auth_manager.get_auth(),
            'live',
            stream_id,
            lambda result: self._on_live_info_loaded(channel, result),
            lambda error: self._on_info_error(error)
        )

    def _on_live_info_loaded(self, channel, info_result):
        """Handle loaded live channel info"""
        # Check if this channel is a favorite
        is_favorite = self.favorites_manager.is_favorite(channel, 'live')
        channel_with_epg = dict(channel)  # Create a copy of channel dict
        channel_with_epg['is_favorite'] = is_favorite  # Set favorite flag
        
        # Add EPG data if available
        channel_name = channel.get('name', '')
        logger.info(f"Looking up EPG data for channel: {channel_name}")
        
        epg_channel_id = self.epg_handler.map_stream_to_epg(channel_name)
        
        if epg_channel_id:
            logger.info(f"Found EPG channel ID: {epg_channel_id}")
            
            # Get the current and next program
            current_program = self.epg_handler.get_current_program(epg_channel_id)
            next_program = self.epg_handler.get_next_program(epg_channel_id)
            
            if current_program:
                logger.info(f"Current program: {current_program.get('title')}")
            else:
                logger.info("No current program found")
                
            if next_program:
                logger.info(f"Next program: {next_program.get('title')}")
            else:
                logger.info("No next program found")
            
            # Add program info to the channel data
            
            if current_program:
                channel_with_epg['current_program'] = {
                    'title': current_program.get('title', 'Unknown'),
                    'start_time': self.epg_handler.format_epg_time(current_program.get('start_timestamp')),
                    'end_time': self.epg_handler.format_epg_time(current_program.get('stop_timestamp')),
                    'description': current_program.get('description', ''),
                    'duration': self.epg_handler._format_duration(
                        current_program.get('start_timestamp'),
                        current_program.get('stop_timestamp')
                    )
                }
            
            if next_program:
                channel_with_epg['next_program'] = {
                    'title': next_program.get('title', 'Unknown'),
                    'start_time': self.epg_handler.format_epg_time(next_program.get('start_timestamp')),
                    'end_time': self.epg_handler.format_epg_time(next_program.get('stop_timestamp')),
                    'description': next_program.get('description', ''),
                    'duration': self.epg_handler._format_duration(
                        next_program.get('start_timestamp'),
                        next_program.get('stop_timestamp')
                    )
                }
            
            # Get the full EPG for the next 12 hours
            epg_list = self.epg_handler.get_formatted_epg_for_channel(epg_channel_id, hours=12)
            logger.info(f"Retrieved {len(epg_list)} EPG entries for the next 12 hours")
            
            channel_with_epg['epg_list'] = epg_list
            
            # Update info panel with the enhanced channel data
            self.ui_manager.update_info(channel_with_epg, 'live')
        else:
            logger.info(f"No EPG data found for channel: {channel_name}")
            # No EPG data, just show basic channel info
            self.ui_manager.update_info(channel_with_epg, 'live')
        
        # Add artwork for the channel
        self.artwork_manager.update_artwork(self.window.info_panel, channel_with_epg, 'live')
        
        # Update status
        self.window.show_status_message("Channel info loaded")

    def _load_vod_info(self, movie):
        """Load info for movie"""
        self.window.show_status_message("Loading movie info...")
        
        # Get stream ID
        stream_id = movie.get('stream_id') or movie.get('vod_id')
        if not stream_id:
            self.window.info_panel.set_content_info(movie, 'vod')
            return
            
        # Use content manager to load movie info
        self.content_manager.load_info(
            self.auth_manager.get_auth(),
            'vod',
            stream_id,
            lambda result: self._on_movie_info_loaded(movie, result),
            lambda error: self._on_info_error(error)
        )

    def _on_movie_info_loaded(self, movie, info_result):
        """Handle loaded movie info"""
        # Combine movie with info
        movie_with_info = dict(movie)
        if 'info' in info_result:
            # Copy relevant fields from info to movie
            info = info_result['info']
            for key in ['plot', 'genre', 'rating', 'duration', 'director', 'cast']:
                if key in info:
                    movie_with_info[key] = info[key]
        
        # Check if this movie is a favorite
        is_favorite = self.favorites_manager.is_favorite(movie, 'vod')
        movie_with_info['is_favorite'] = is_favorite
        
        # Update info panel
        self.ui_manager.update_info(movie_with_info, 'vod')
        
        # Add artwork for the movie
        self.artwork_manager.update_artwork(self.window.info_panel, movie_with_info, 'vod')
        
        # Update status
        self.window.show_status_message("Movie info loaded")

    def _load_series_info(self, series):
        """Load info for series"""
        self.window.show_status_message("Loading series info...")
        
        # Store current series
        self.current_series = series
        
        # Get series ID
        series_id = series.get('series_id')
        if not series_id:
            self.window.info_panel.set_content_info(series, 'series')
            return
            
        # Use content manager to load series info
        self.content_manager.load_info(
            self.auth_manager.get_auth(),
            'series',
            series_id,
            lambda result: self._on_series_info_loaded(series, result),
            lambda error: self._on_info_error(error)
        )

    def _on_series_info_loaded(self, series, info_result):
        """Handle loaded series info"""
        # Combine series with info
        series_with_info = dict(series)
        if 'info' in info_result:
            # Copy relevant fields from info to series
            info = info_result['info']
            for key in ['plot', 'genre', 'rating', 'cast', 'director']:
                if key in info:
                    series_with_info[key] = info[key]
        
        # Add episodes
        episodes = info_result.get('episodes', [])
        series_with_info['episodes'] = episodes
        self.episodes = episodes
        
        # Check if this series is a favorite
        is_favorite = self.favorites_manager.is_series_favorite(series)
        series_with_info['is_favorite'] = is_favorite
        
        # Update info panel
        self.ui_manager.update_info(series_with_info, 'series')
        
        # Add artwork for the series
        self.artwork_manager.update_artwork(self.window.info_panel, series_with_info, 'series')
        
        # Update status
        self.window.show_status_message(f"Series info loaded with {len(episodes)} episodes")

    def on_episode_selected(self, episode):
        """Handle episode selection"""
        # Display episode info
        self._display_episode_info(episode)

    def _display_episode_info(self, episode):
        """Display episode info in info panel"""
        self.window.info_panel.show_episode_info(episode)

    def _on_info_error(self, error):
        """Handle info loading error"""
        self.window.show_error_message("Error", f"Failed to load information: {error}")
        self.window.show_status_message("Error loading information")

    def play_content(self, item):
        """Play selected content"""
        # Check if there's a selected episode first
        current_episode = self.window.info_panel.get_current_episode()
        
        if current_episode:
            # Play the selected episode instead of the content item
            self.play_episode(current_episode)
            return
        
        # Determine the actual content type for playback
        if self.content_type == 'search':
            # For search results, get the actual type from the item
            actual_type = item.get('content_type', self.content_type)
        else:
            actual_type = self.content_type
        
        # Use playback manager to handle content playback
        result = self.playback_manager.play_content(item, actual_type, self.window, original_type=self.content_type)
        
        if result:
            content_name = item.get('name', item.get('title', 'Unknown'))
            self.window.show_status_message(f"Playing: {content_name}")

    def play_episode(self, episode):
        """Play selected episode"""
        # Use playback manager to handle episode playback
        result = self.playback_manager.play_episode(episode, self.window)
        
        if result:
            episode_name = episode.get('title', episode.get('name', 'Unknown Episode'))
            self.window.show_status_message(f"Playing: {episode_name}")

    def on_player_started(self):
        """Handle player started event"""
        logger.info("Player started successfully")

    def on_player_exited(self, exit_code, stderr):
        """Handle player exited event"""
        logger.info(f"Player exited with code {exit_code}")
        if stderr:
            logger.error(f"Player stderr: {stderr}")

    def toggle_favorite(self, item):
        """Toggle favorite status for content item"""
        # Determine content type and proper item
        content_type = self.content_type
        
        # Enhanced logging for debugging favorites issue
        logger.info(f"Toggle favorite called for content_type: {content_type}")
        
        if content_type == 'favorites':
            # When removing from favorites view
            fav_item = item
            logger.info(f"Removing from favorites view: {fav_item.get('label', 'Unknown')}")
            
            try:
                # Get the current row/index directly from the content panel
                current_index = self.window.content_panel.content_list.currentRow()
                favorites = self.favorites_manager.get_all_favorites()
                
                if current_index >= 0 and current_index < len(favorites):
                    # Direct removal by index - safer than searching
                    removed_item = favorites[current_index]
                    logger.info(f"Removing favorite at index {current_index}: {removed_item.get('label')}")
                    
                    # First remove from favorites manager, then update local list
                    self.favorites_manager.remove_favorite_by_index(current_index)
                    
                    # Force save to file
                    self.favorites_manager._save_favorites()
                    logger.info("Saved favorites to file")
                    
                    # Refresh favorites view
                    self._display_favorites()
                    self.window.show_info_message("Favorites", "Removed from favorites")
                else:
                    logger.error(f"Invalid index {current_index} for favorites list of size {len(favorites)}")
                    self.window.show_error_message("Favorites", "Invalid favorite selected")
                    
            except Exception as e:
                logger.error(f"Error removing favorite: {str(e)}")
                logger.error(traceback.format_exc())
                self.window.show_error_message("Favorites", f"Error removing favorite: {str(e)}")
            return
        
        # Other content types - toggle favorite status
        try:
            # Log item details for debugging
            if content_type == 'vod':
                stream_id = item.get('stream_id') or item.get('vod_id')
                logger.info(f"Toggling VOD favorite, stream_id: {stream_id}, name: {item.get('name', 'Unknown')}")
            elif content_type == 'live':
                stream_id = item.get('stream_id')
                logger.info(f"Toggling Live favorite, stream_id: {stream_id}, name: {item.get('name', 'Unknown')}")
            
            # Toggle favorite status
            is_favorite = self.favorites_manager.toggle_favorite(item, content_type)
            
            # Force save to file
            self.favorites_manager._save_favorites()
            logger.info(f"Saved favorites after toggle, is now favorite: {is_favorite}")
            
            # Show message
            action = "Added to" if is_favorite else "Removed from"
            self.window.show_info_message("Favorites", f"{action} favorites")
            
            # Update UI to reflect new favorite status - this ensures both icons and context menus are in sync
            if content_type == 'live':
                item['is_favorite'] = is_favorite
                self.window.info_panel.set_content_info(item, 'live')
                
                # Also update the content panel favorite icon if applicable
                current_index = self.window.content_panel.content_list.currentRow()
                if current_index >= 0 and current_index < len(self.content_items):
                    selected_item = self.content_items[current_index]
                    if selected_item.get('stream_id') == item.get('stream_id'):
                        # Update favorite icon in the current list item
                        if hasattr(self.window.content_panel, 'update_favorite_status'):
                            self.window.content_panel.update_favorite_status(current_index, is_favorite)
                        
                        # Also update the selected item's favorite status
                        selected_item['is_favorite'] = is_favorite
                        
            elif content_type == 'vod':
                item['is_favorite'] = is_favorite
                self.window.info_panel.set_content_info(item, 'vod')
                
                # Also update the content panel favorite icon if applicable
                current_index = self.window.content_panel.content_list.currentRow()
                if current_index >= 0 and current_index < len(self.content_items):
                    selected_item = self.content_items[current_index]
                    if selected_item.get('stream_id') == item.get('stream_id'):
                        # Update favorite icon in the current list item
                        if hasattr(self.window.content_panel, 'update_favorite_status'):
                            self.window.content_panel.update_favorite_status(current_index, is_favorite)
                        
                        # Also update the selected item's favorite status
                        selected_item['is_favorite'] = is_favorite
        
        except Exception as e:
            logger.error(f"Error toggling favorite: {str(e)}")
            logger.error(traceback.format_exc())
            self.window.show_error_message("Favorites", f"Error toggling favorite: {str(e)}")

    def toggle_series_favorite(self, series):
        """Toggle favorite status for TV series"""
        if not series:
            return
        
        try:    
            # Toggle favorite status
            is_favorite = self.favorites_manager.toggle_series_favorite(series)
            
            # Force save to file
            self.favorites_manager._save_favorites()
            logger.info(f"Saved favorites after series toggle, is now favorite: {is_favorite}")
            
            # Update series info to reflect favorite status
            series['is_favorite'] = is_favorite
            
            # Update UI
            self.window.info_panel.set_content_info(series, 'series')
            
            # Also update the content panel favorite icon if applicable
            current_index = self.window.content_panel.content_list.currentRow()
            if current_index >= 0 and current_index < len(self.content_items):
                selected_item = self.content_items[current_index]
                if selected_item.get('series_id') == series.get('series_id'):
                    # Update favorite icon in the current list item
                    if hasattr(self.window.content_panel, 'update_favorite_status'):
                        self.window.content_panel.update_favorite_status(current_index, is_favorite)
                    
                    # Also update the selected item's favorite status
                    selected_item['is_favorite'] = is_favorite
            
            # Show message
            action = "Added to" if is_favorite else "Removed from"
            series_name = series.get('name', series.get('title', 'Unknown'))
            self.window.show_info_message("Favorites", f"Series '{series_name}' {action} favorites")
        
        except Exception as e:
            logger.error(f"Error toggling series favorite: {str(e)}")
            logger.error(traceback.format_exc())
            self.window.show_error_message("Favorites", f"Error toggling favorite: {str(e)}")

    def search(self, search_term):
        """Search for content"""
        if not self.auth_manager.get_auth():
            self.window.show_error_message("Search", "Please log in first")
            return
            
        self.window.show_status_message(f"Searching for '{search_term}'...")
        
        # Use search manager to perform search
        self.search_manager.search(
            self.auth_manager.get_auth(),
            search_term,
            None,  # All content types
            lambda results, term: self._on_search_results(results, term),
            lambda current, total: self._on_search_progress(current, total),
            lambda error: self._on_search_error(error)
        )

    def _on_search_results(self, results, search_term):
        """Handle search results"""
        # Store search results
        self.search_results = results
        self.content_type = 'search'  # Set content type to search
        
        # Set content items on the content panel for the context menu to work
        if hasattr(self.window.content_panel, 'content_items'):
            self.window.content_panel.content_items = results
        if hasattr(self.window.content_panel, 'content_type'):
            self.window.content_panel.content_type = 'search'
        
        # Extract display names with content type prefix
        display_names = []
        for item in results:
            name = item.get('name', item.get('title', 'Unknown'))
            content_type = item.get('content_type', 'unknown')
            
            if content_type == 'live':
                prefix = "[Live] "
            elif content_type == 'vod':
                prefix = "[Movie] "
            elif content_type == 'series':
                prefix = "[Series] "
            else:
                prefix = ""
                
            display_names.append(f"{prefix}{name}")
        
        # Update content panel
        self.ui_manager.update_content('search', results, display_names)
        
        # Clear info panel
        self.ui_manager.clear_info()
        
        # Update status
        self.window.show_status_message(f"Found {len(results)} results for '{search_term}'")
        
        # Re-apply right-click favorites menu in case the content list was recreated
        from chumpstreams_patches import enable_favorite_context_menu
        if hasattr(self.window, 'content_panel'):
            enable_favorite_context_menu(self.window.content_panel)

    def _on_search_progress(self, current, total):
        """Handle search progress updates"""
        # Just update status message
        self.window.show_status_message(f"Searching... ({current}/{total})")

    def _on_search_error(self, error):
        """Handle search error"""
        self.window.show_error_message("Search Error", f"Error during search: {error}")
        self.window.show_status_message("Search error")
        
    def show_epg_debug(self):
        """Show EPG debug dialog for current channel"""
        if not hasattr(self, 'content_items') or not self.content_items:
            self.window.show_info_message("EPG Debug", "Please select a channel first")
            return
            
        # Find current selected channel
        index = self.window.content_panel.content_list.currentRow()
        if index < 0 or index >= len(self.content_items):
            self.window.show_info_message("EPG Debug", "Please select a channel first")
            return
            
        channel = self.content_items[index]
        channel_name = channel.get('name', '')
        
        # Create and show dialog through EPG manager
        from chumpstreams_debug import EPGDebugDialog
        epg_debug_dialog = EPGDebugDialog(self.window, channel_name, self.epg_handler)
        epg_debug_dialog.show()
        
    def refresh_current_content_if_live(self):
        """Refresh current content if it's live TV to update EPG data"""
        if self.content_type == 'live':
            # Get current selection
            current_index = self.window.content_panel.content_list.currentRow()
            if current_index >= 0 and current_index < len(self.content_items):
                # Re-trigger content selection to refresh EPG in the info panel
                self.on_content_selected(self.content_items, current_index)
                logger.info("Refreshed live channel view to show EPG data")