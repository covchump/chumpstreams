"""
ChumpStreams Application Controller

Version: 2.0.8
Author: covchump
Last updated: 2025-01-12 14:48:00

Main application controller for ChumpStreams with multi-service support
"""
import os
import logging
import json
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer  # QTimer is in QtCore, not QtWidgets

# Import configuration
from chumpstreams_config import *

# Import components
from api_client import ApiClient
from chumpstreams_theme import ChumpStreamsTheme
from chumpstreams_ui import ChumpStreamsMainWindow
from chumpstreams_player import QtVlcPlayer
from chumpstreams_content import ContentManager
from chumpstreams_favorites import FavoritesManager
from chumpstreams_search import SearchManager
from chumpstreams_epg import EPGManager as EPGHandler
from chumpstreams_settings import SettingsManager
from chumpstreams_debug import EPGDebugDialog, FavoritesDebugDialog
from chumpstreams_ui_manager import UIManager
from chumpstreams_auth import AuthenticationManager
from chumpstreams_epg_manager import EPGManager
from chumpstreams_playback import PlaybackManager
from chumpstreams_image_cache import ImageCache
from chumpstreams_artwork import ArtworkManager
from chumpstreams_info_panel_extensions import extend_info_panel
from chumpstreams_patches import enable_favorite_context_menu, disable_all_context_menus_except_content, remove_favorite_buttons

logger = logging.getLogger('chumpstreams')

class ChumpStreamsApp:
    """Main application controller"""
    
    def __init__(self, app):
        """Initialize the application"""
        self.app = app
        logger.info("Initializing ChumpStreams App")
        
        # Apply theme
        ChumpStreamsTheme.apply_application_theme(app)
        app.setStyleSheet(ChumpStreamsTheme.get_stylesheet())
        
        # Create main window
        self.window = ChumpStreamsMainWindow()
        
        # Extend info panel with artwork display capabilities
        extend_info_panel(self.window.info_panel)
        
        # Initialize API client with default URL
        self.api = ApiClient(SERVER, use_https=USE_HTTPS)
        
        # Initialize VLC Player
        self.player = QtVlcPlayer()
        self.player.find_vlc()
        
        # Initialize image cache and artwork manager
        self.image_cache = ImageCache(CFG_DIR)
        self.artwork_manager = ArtworkManager(self.image_cache)
        
        # Initialize managers
        self.content_manager = ContentManager(self.api)
        self.favorites_manager = FavoritesManager(CONFIG_FILE)
        # IMPORTANT: Give favorites manager access to API for URL extraction
        self.favorites_manager.api = self.api
        
        self.search_manager = SearchManager(self.api)
        self.settings_manager = SettingsManager(CONFIG_FILE)
        self.auth_manager = AuthenticationManager(self.api, CONFIG_FILE)
        self.ui_manager = UIManager(self.window)
        self.epg_handler = EPGHandler(SERVER, use_https=USE_HTTPS)
        self.epg_manager = EPGManager(self.epg_handler, self.ui_manager)
        
        # Initialize playback manager
        self.buffer_settings = self.settings_manager.get_buffer_settings()
        self.playback_manager = PlaybackManager(
            self.api, 
            {}, # Empty auth initially
            self.content_manager, 
            self.player, 
            self.buffer_settings,
            use_https=USE_HTTPS,
            server=SERVER
        )
        
        # Migrate old favorites to enhanced format
        if hasattr(self.favorites_manager, 'migrate_old_favorites'):
            self.favorites_manager.migrate_old_favorites()
        
        # Initialize state
        self.content_type = 'live'  # Default to live TV
        self.categories_by_type = {
            "live": [],
            "vod": [],
            "series": []
        }
        self.content_items = []
        self.displayed_category = ""
        self.favorites = self.favorites_manager.get_all_favorites()
        self.current_series = None
        self.episodes = []
        self.search_results = []
        self.current_service = None
        
        # Enable right-click favorites menu in content panel
        if hasattr(self.window, 'content_panel'):
            enable_favorite_context_menu(self.window.content_panel)
        
        # Disable all context menus except content panel
        disable_all_context_menus_except_content(self)
        
        # Remove favorite buttons but keep the Favorites tab
        remove_favorite_buttons(self)
        
        # Connect signals
        self._connect_signals()
        self._connect_epg_signals()
        
        # Load configuration
        self._load_config()
        
        # Force Live TV selection in the UI
        self._force_select_live_tv()
        
        # Setup timer for auto-login if saved
        QTimer.singleShot(1000, self._auto_login)
    
    def _force_select_live_tv(self):
        """Force selection of Live TV in the content type bar"""
        # Find the Live TV radio button and select it
        content_type_bar = self.window.content_type_bar
        for btn in content_type_bar.content_type_group.buttons():
            if btn.property("content_type") == "live":
                btn.setChecked(True)
                logger.info("Live TV content type selected by default")
                break
    
    def _connect_signals(self):
        """Connect UI signals to handlers"""
        # Login signals - handle service parameter
        self.window.login_requested.connect(self._login)
        self.window.logout_requested.connect(self._logout)
        
        # Service change signal
        self.window.service_changed.connect(self._on_service_changed)
        
        # Settings signal
        self.window.settings_requested.connect(self._show_settings)
        
        # Category and content type signals
        self.window.category_changed.connect(self._on_category_changed)
        self.window.search_requested.connect(self._search)
        
        # Content panel signals
        content = self.window.content_panel
        content.content_selected.connect(self._on_content_selected)
        content.content_play_requested.connect(self._play_content)
        content.favorite_toggled.connect(self._toggle_favorite)
        
        # Info panel signals
        info = self.window.info_panel
        info.episode_selected.connect(self._on_episode_selected)
        info.episode_play_requested.connect(self._play_episode)
        info.series_favorite_toggled.connect(self._toggle_series_favorite)
        info.content_play_requested.connect(self._play_content)
        
        # Add connections for Live TV and VOD favorite buttons
        info.live_favorite_toggled.connect(self._toggle_favorite)
        info.vod_favorite_toggled.connect(self._toggle_favorite)
        
        # Player signals
        self.player.player_started.connect(self._on_player_started)
        self.player.player_exited.connect(self._on_player_exited)
        
        # Auth manager signals
        self.auth_manager.login_succeeded.connect(self._on_login_success)
        self.auth_manager.login_failed.connect(self._on_login_failed)
        
        # EPG manager signals
        self.epg_manager.epg_loaded.connect(self._on_epg_loaded)
        self.epg_manager.epg_error.connect(self._on_epg_error)
    
    def _connect_epg_signals(self):
        """Connect EPG-related signals from UI to handlers"""
        self.window.epg_debug_requested.connect(self._show_epg_debug)
        self.window.epg_delete_requested.connect(self._clear_epg_cache)
        self.window.epg_refresh_requested.connect(self._fetch_epg_data)
    
    def _load_config(self):
        """Load configuration from file"""
        if not os.path.exists(CONFIG_FILE):
            logger.info("No configuration file found")
            return
            
        try:
            # Load saved credentials
            self.auth_manager.load_saved_credentials()
            saved_credentials = self.auth_manager.get_saved_credentials()
            
            # Set login UI if we have credentials
            if saved_credentials:
                username = saved_credentials.get('username', '')
                service_name = saved_credentials.get('service_name', 'ChumpStreams')
                if username:
                    self.window.set_login_credentials(username, True, service_name)
                
            # Load favorites from favorites manager directly
            self.favorites = self.favorites_manager.get_all_favorites()
            
            # Load buffer settings
            self.buffer_settings = self.settings_manager.get_buffer_settings()
            
            # Simple mode
            simple_mode = self.settings_manager.get_simple_mode()
            # Apply simple mode setting to UI
            self.window.set_simple_mode(simple_mode)
                
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self.window.show_error_message("Error", f"Could not load configuration: {str(e)}")
    
    def _auto_login(self):
        """Attempt auto-login if credentials are saved, or show login dialog"""
        if self.auth_manager.has_saved_credentials():
            saved_credentials = self.auth_manager.get_saved_credentials()
            username = saved_credentials['username']
            password = saved_credentials['password']
            service = saved_credentials.get('service')
            logger.info(f"Attempting auto-login for user: {username}")
            
            # Directly call login method with saved credentials
            self._login(username, password, True, service)
        else:
            # Always show login dialog if not auto-logging in
            logger.info("No saved credentials found, showing login dialog")
            self.window._show_login_dialog()
    
    def _login(self, username, password, remember, service=None):
        """Handle login request"""
        self.window.show_status_message("Logging in...")
        
        # If service is provided, update the API configuration
        if service:
            self.current_service = service
            # Update API base URL
            protocol = 'https' if service.get('use_https', True) else 'http'
            port = '443' if service.get('use_https', True) else '80'
            url = service.get('url', 'subs.chumpbumptv.com')
            self.api.base_url = f"{protocol}://{url}:{port}"
            
            # Update EPG handler with new server
            if hasattr(self, 'epg_handler'):
                self.epg_handler.server = url
                self.epg_handler.use_https = service.get('use_https', True)
            
            # Update playback manager with new server info
            if hasattr(self, 'playback_manager'):
                self.playback_manager.server = url
                self.playback_manager.use_https = service.get('use_https', True)
        
        # Call auth manager to handle login
        self.auth_manager.login(username, password, remember, service)
    
    def _logout(self):
        """Handle logout request"""
        self.auth_manager.logout()
        self.content_type = 'live'
        self.ui_manager.show_logged_out_ui()
    
    def _on_service_changed(self, service):
        """Handle service change"""
        logger.info(f"Service changed to: {service.get('name', 'Unknown')}")
        # Clear categories when service changes
        self.categories_by_type = {
            "live": [],
            "vod": [],
            "series": []
        }
        # Clear content
        self.window.content_panel.clear_content()
        self.window.info_panel.clear_info()
    
    def _on_login_success(self, username):
        """Handle successful login"""
        # Update UI
        self.ui_manager.show_logged_in_ui(username)
        self.ui_manager.show_status_message(f"Logged in as {username}")
        
        # Update playback manager with authentication
        self.playback_manager.update_auth(self.auth_manager.get_auth())
        
        # Preload categories - make sure Live TV is loaded first
        self._preload_categories()
        
        # Fetch EPG data after successful login (with a small delay)
        QTimer.singleShot(3000, lambda: self._fetch_epg_data())
    
    def _on_login_failed(self, error_message):
        """Handle failed login"""
        self.window.show_error_message("Login Failed", error_message)
        self.window.show_status_message("Login failed")
    
    def _fetch_epg_data(self):
        """Fetch EPG data after login"""
        auth = self.auth_manager.get_auth()
        if not auth:
            return
            
        username = auth.get('username', '')
        password = auth.get('password', '')
        
        if username and password:
            self.epg_manager.fetch_epg_data(username, password)
    
    def _on_epg_loaded(self, status_message):
        """Handle successful EPG loading"""
        self.ui_manager.show_status_message(status_message)
        
        # If viewing a live channel, refresh the view
        if self.content_type == 'live':
            # Get current selection
            current_index = self.window.content_panel.content_list.currentRow()
            if current_index >= 0 and current_index < len(self.content_items):
                # Re-trigger content selection to refresh EPG in the info panel
                self._on_content_selected(self.content_items, current_index)
                logger.info("Refreshed live channel view to show EPG data")
    
    def _on_epg_error(self, error_message):
        """Handle EPG loading error"""
        self.window.show_status_message(error_message)
    
    def _preload_categories(self):
        """Preload categories for all content types"""
        self.window.show_status_message("Loading categories...")
        
        try:
            # Load categories for all content types using the correct method
            self.categories_by_type['live'] = self.api.get_categories('live')
            logger.info(f"Loaded {len(self.categories_by_type['live'])} live categories")
            
            self.categories_by_type['vod'] = self.api.get_categories('vod')
            logger.info(f"Loaded {len(self.categories_by_type['vod'])} VOD categories")
            
            self.categories_by_type['series'] = self.api.get_categories('series')
            logger.info(f"Loaded {len(self.categories_by_type['series'])} series categories")
            
            # Always start with Live TV content type
            current_type = "live"
            logger.info(f"Setting initial content type to: {current_type}")
            
            # Make sure Live TV is selected in the UI
            self._force_select_live_tv()
            
            # Manually trigger content type loading for Live TV
            QTimer.singleShot(100, lambda: self._update_categories_for_type(current_type))
            
        except Exception as e:
            logger.error(f"Error loading categories: {str(e)}")
            self.window.show_error_message("Error", f"Failed to load categories: {str(e)}")
    
    def _update_categories_for_type(self, content_type):
        """Update categories in UI for selected content type"""
        if content_type == 'favorites':
            self._display_favorites()
            return
        
        categories = self.categories_by_type.get(content_type, [])
        category_names = [cat['category_name'] for cat in categories]
        
        logger.info(f"Updating UI with {len(category_names)} {content_type} categories")
        
        # Update category list in UI - force with direct method call
        # to ensure categories are updated
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
    
    def _on_category_changed(self, content_type, category_name):
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
            QTimer.singleShot(100, lambda: self._update_categories_for_type(content_type))
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
        if hasattr(self.window, 'content_panel'):
            enable_favorite_context_menu(self.window.content_panel)
    
    def _on_content_error(self, error):
        """Handle content loading error"""
        self.window.show_error_message("Error", f"Failed to load content: {error}")
        self.window.show_status_message("Error loading content")
    
    def _display_favorites(self):
        """Display favorites in the content panel"""
        # Extract items from favorites
        items = self.favorites
        
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
        if hasattr(self.window, 'content_panel'):
            enable_favorite_context_menu(self.window.content_panel)
    
    def _on_content_selected(self, items, index):
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
    
    def _on_episode_selected(self, episode):
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
    
    def _play_content(self, item):
        """Play selected content"""
        # Check if there's a selected episode first
        current_episode = self.window.info_panel.get_current_episode()
        
        if current_episode:
            # Play the selected episode instead of the content item
            self._play_episode(current_episode)
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
    
    def _play_episode(self, episode):
        """Play selected episode"""
        # Use playback manager to handle episode playback
        result = self.playback_manager.play_episode(episode, self.window)
        
        if result:
            episode_name = episode.get('title', episode.get('name', 'Unknown Episode'))
            self.window.show_status_message(f"Playing: {episode_name}")
    
    def _on_player_started(self):
        """Handle player started event"""
        logger.info("Player started successfully")
    
    def _on_player_exited(self, exit_code, stderr):
        """Handle player exited event"""
        logger.info(f"Player exited with code {exit_code}")
        if stderr:
            logger.error(f"Player stderr: {stderr}")
    
    def _toggle_favorite(self, item):
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
                
                if current_index >= 0 and current_index < len(self.favorites):
                    # Direct removal by index - safer than searching
                    removed_item = self.favorites[current_index]
                    logger.info(f"Removing favorite at index {current_index}: {removed_item.get('label')}")
                    
                    # FIXED: First remove from favorites manager, then update local list
                    # This ensures we're working with a consistent state
                    self.favorites_manager.remove_favorite_by_index(current_index)
                    
                    # Now refresh our local favorites list from the manager
                    self.favorites = self.favorites_manager.get_all_favorites()
                    
                    # Force save to file
                    self.favorites_manager._save_favorites()
                    logger.info("Saved favorites to file")
                    
                    # Refresh favorites view
                    self._display_favorites()
                    self.window.show_info_message("Favorites", "Removed from favorites")
                else:
                    logger.error(f"Invalid index {current_index} for favorites list of size {len(self.favorites)}")
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
            
            # Refresh favorites list from manager
            self.favorites = self.favorites_manager.get_all_favorites()
            
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
    
    def _toggle_series_favorite(self, series):
        """Toggle favorite status for TV series"""
        if not series:
            return
        
        try:    
            # Toggle favorite status
            is_favorite = self.favorites_manager.toggle_series_favorite(series)
            
            # Force save to file
            self.favorites_manager._save_favorites()
            logger.info(f"Saved favorites after series toggle, is now favorite: {is_favorite}")
            
            # Refresh favorites list
            self.favorites = self.favorites_manager.get_all_favorites()
            
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
    
    def _search(self, search_term):
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
    
    def _show_epg_debug(self):
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
        self.epg_debug_dialog = self.epg_manager.show_debug_dialog(self.window, channel_name)
    
    def _show_favorites_debug(self):
        """Show favorites debug dialog"""
        # Create dialog
        if not hasattr(self, 'favorites_debug_dialog'):
            self.favorites_debug_dialog = FavoritesDebugDialog(self.window)
        
        # Set data
        self.favorites_debug_dialog.set_data(self.favorites_manager)
        
        # Show dialog
        self.favorites_debug_dialog.show()
        
    def _clear_epg_cache(self):
        """Clear the EPG cache"""
        if hasattr(self, 'epg_manager'):
            if self.epg_manager.clear_cache():
                self.window.show_info_message("EPG Cache", "EPG cache has been cleared")
                self.window.show_status_message("EPG cache cleared successfully")
                # Re-fetch EPG data if logged in
                if self.auth_manager.get_auth():
                    QTimer.singleShot(500, lambda: self._fetch_epg_data())
            else:
                self.window.show_error_message("EPG Cache", "Failed to clear EPG cache")
        else:
            self.window.show_error_message("EPG Cache", "EPG manager not initialized")
            
    def _clear_image_cache(self):
        """Clear the image cache"""
        if hasattr(self, 'image_cache'):
            if self.image_cache.clear_cache():
                self.window.show_info_message("Image Cache", "Image cache has been cleared")
                self.window.show_status_message("Image cache cleared successfully")
            else:
                self.window.show_error_message("Image Cache", "Failed to clear image cache")
        else:
            self.window.show_error_message("Image Cache", "Image cache not initialized")
    
    def _get_image_cache_size_mb(self):
        """Get the size of the image cache in megabytes"""
        if not hasattr(self, 'image_cache'):
            return 0
            
        cache_dir = self.image_cache.cache_dir
        if not os.path.exists(cache_dir):
            return 0
            
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(cache_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        
        # Convert bytes to MB
        return total_size / (1024 * 1024)
    
    def _show_settings(self):
        """Show settings dialog"""
        if not hasattr(self, 'settings_manager'):
            self.window.show_error_message("Settings", "Settings manager not initialized")
            return
            
        # Get current simple mode setting
        simple_mode = self.window.get_simple_mode()
        
        # Add image cache control to settings dialog
        if hasattr(self.settings_manager, 'add_cache_control'):
            self.settings_manager.add_cache_control(
                "Image Cache",
                f"Current size: {self._get_image_cache_size_mb():.1f} MB",
                self._clear_image_cache
            )
        
        # Show settings dialog using the settings manager
        if self.settings_manager.show_settings_dialog(self.window):
            # Update settings from the settings manager
            self.buffer_settings = self.settings_manager.get_buffer_settings()
            simple_mode = self.settings_manager.get_simple_mode()
            
            # Apply settings
            self.window.set_simple_mode(simple_mode)
            
            # Update playback manager with new buffer settings
            self.playback_manager.update_buffer_settings(self.buffer_settings)
            
            # Show confirmation
            self.window.show_status_message("Settings saved")