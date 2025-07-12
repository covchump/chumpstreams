"""
ChumpStreams UI Patches

Version: 2.0.6
Author: covchump
Last updated: 2025-01-12 13:26:57

UI modifications and patches for ChumpStreams
"""
import logging
import traceback
from PyQt5.QtWidgets import QMenu, QListWidget
from PyQt5.QtCore import Qt

logger = logging.getLogger('chumpstreams')

def patch_login_dialog(ChumpStreamsMainWindow, show_login_dialog):
    """Patch the login dialog to use improved version"""
    original_show_login_dialog = ChumpStreamsMainWindow._show_login_dialog

    def patched_show_login_dialog(self):
        """Patched method to show our improved login dialog"""
        # Get saved credentials if any
        username = ""
        remember = False
        if hasattr(self, 'login_username'):
            username = self.login_username
            remember = True
        
        # Show the improved larger login dialog
        result = show_login_dialog(self, username, remember)
        
        if result:
            self.login_requested.emit(result['username'], result['password'], result['remember'])

    # Apply the patch
    ChumpStreamsMainWindow._show_login_dialog = patched_show_login_dialog
    logger.info("Login dialog patched with improved version")

def patched_context_menu_event(self, event):
    """Patched context menu event to include favorite toggle"""
    # Check if this is our content list
    if not hasattr(self, 'parent') or not hasattr(self.parent(), 'create_content_menu'):
        # Not our content list, skip
        return
        
    # It's our content list, create a custom menu
    pos = event.pos()
    item = self.itemAt(pos)
    if not item:
        return
        
    index = self.row(item)
    if index < 0:
        return
    
    # Get the content panel (parent of this list widget)
    content_panel = self.parent()
    
    # Create the menu
    menu = QMenu(self)
    
    # Add play action
    play_action = menu.addAction("Play")
    play_action.triggered.connect(lambda: content_panel.play_requested(index))
    
    # Add favorite action
    content_items = getattr(content_panel, 'content_items', [])
    content_type = getattr(content_panel, 'content_type', '')
    
    # Only add favorite toggle if we're not in favorites view
    parent_window = content_panel.window()
    if hasattr(parent_window, 'content_type_bar'):
        current_content_type = None
        for btn in parent_window.content_type_bar.content_type_group.buttons():
            if btn.isChecked():
                current_content_type = btn.property("content_type")
                break
        
        if current_content_type != 'favorites':
            # Add separator
            menu.addSeparator()
            
            # Add favorite toggle option
            if index < len(content_items):
                item = content_items[index]
                is_favorite = item.get('is_favorite', False)
                
                if is_favorite:
                    fav_action = menu.addAction("Remove from Favorites")
                else:
                    fav_action = menu.addAction("Add to Favorites")
                    
                fav_action.triggered.connect(lambda: content_panel.favorite_toggled.emit(content_items[index]))
    else:
        # We're in favorites view - only add remove option
        menu.addSeparator()
        fav_action = menu.addAction("Remove from Favorites")
        fav_action.triggered.connect(lambda: content_panel.favorite_toggled.emit(content_items[index]))
    
    # Execute the menu
    menu.exec_(event.globalPos())

def enable_favorite_context_menu(content_panel):
    """Enable favorites in the right-click context menu"""
    try:
        # Get the content list
        content_list = getattr(content_panel, 'content_list', None)
        if not content_list:
            logger.error("Could not find content_list in content panel")
            return
            
        # Store old method for restoration if needed
        if not hasattr(content_list, '_original_context_menu_event'):
            content_list._original_context_menu_event = content_list.contextMenuEvent
            
        # Apply our patched method
        content_list.contextMenuEvent = lambda event: patched_context_menu_event(content_list, event)
        logger.info("Right-click favorites menu has been enabled")
    except Exception as e:
        logger.error(f"Error enabling favorites context menu: {str(e)}")
        logger.error(traceback.format_exc())

def disable_all_context_menus_except_content(app):
    """
    Disable all right-click context menus in the application except content panel
    
    Args:
        app: The ChumpStreamsApp instance
    """
    logger.info("Disabling non-content right-click context menus")
    
    try:
        # 1. Enable in content panel with favorites (this is what we want)
        if hasattr(app.window, 'content_panel'):
            enable_favorite_context_menu(app.window.content_panel)
        
        # 2. Disable in info panel
        if hasattr(app.window, 'info_panel'):
            info_panel = app.window.info_panel
            
            # Disable context menu policy
            info_panel.setContextMenuPolicy(Qt.NoContextMenu)
            
            # Disable in episodes list if it exists
            if hasattr(info_panel, 'episodes_list'):
                info_panel.episodes_list.setContextMenuPolicy(Qt.NoContextMenu)
            
            # Disable in EPG list if it exists
            if hasattr(info_panel, 'epg_list'):
                info_panel.epg_list.setContextMenuPolicy(Qt.NoContextMenu)
        
        # 3. Disable in category panel
        if hasattr(app.window, 'category_panel'):
            if hasattr(app.window.category_panel, 'categories_list'):
                app.window.category_panel.categories_list.setContextMenuPolicy(Qt.NoContextMenu)
        
        logger.info("Non-content right-click context menus disabled successfully")
        return True
    except Exception as e:
        logger.error(f"Error disabling context menus: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def remove_favorite_buttons(app):
    """
    Remove add/remove favorite buttons but keep the Favorites tab
    
    Args:
        app: The ChumpStreamsApp instance
    """
    logger.info("Removing favorite buttons from the UI")
    
    try:
        # Remove buttons from info panel
        if hasattr(app.window, 'info_panel'):
            info_panel = app.window.info_panel
            
            # Live TV favorite button
            if hasattr(info_panel, 'live_favorite_button'):
                info_panel.live_favorite_button.setVisible(False)
                logger.info("Live TV favorite button hidden")
            
            # VOD favorite button
            if hasattr(info_panel, 'vod_favorite_button'):
                info_panel.vod_favorite_button.setVisible(False)
                logger.info("VOD favorite button hidden")
            
            # Series favorite button
            if hasattr(info_panel, 'series_favorite_button'):
                info_panel.series_favorite_button.setVisible(False)
                logger.info("Series favorite button hidden")
            
            # Generic favorite button in enhanced info panel
            if hasattr(info_panel, 'favorite_button'):
                info_panel.favorite_button.setVisible(False)
                logger.info("Enhanced info panel favorite button hidden")
        
        logger.info("All favorite buttons removed successfully")
        return True
    except Exception as e:
        logger.error(f"Error removing favorite buttons: {str(e)}")
        logger.error(traceback.format_exc())
        return False