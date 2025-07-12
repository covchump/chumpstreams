"""
ChumpStreams Patches

Version: 1.3.2
Author: covchump
Last updated: 2025-07-12 17:18:34

Patches for ChumpStreams application to apply fixes without modifying core files
"""
import os
import sys
import logging
from PyQt5.QtWidgets import QAction, QMenu, QMessageBox, QWidget
from PyQt5.QtCore import Qt

# Import API patches
from chumpstreams_api_fix import apply_api_patches
# Import menu patch
from chumpstreams_switch_service_patch import patch_main_window
# Import login dialog fix
from chumpstreams_login_dialog_fix import patch_service_dialog

logger = logging.getLogger('chumpstreams')

# Update this function to accept two arguments
def patch_login_dialog(window_class, custom_login_dialog_func):
    """
    Patch the login dialog to use a custom dialog function
    
    Args:
        window_class: The window class to patch
        custom_login_dialog_func: The custom login dialog function to use
    """
    # Import the custom login dialog
    from chumpstreams_login_dialog import show_login_dialog
    
    # Define the patched show login dialog method
    def _patched_show_login_dialog(self):
        # Get username and service name if we have one
        username = ""
        remember = False
        service_name = None
        
        if hasattr(self, 'username_edit') and self.username_edit.text():
            username = self.username_edit.text()
            if hasattr(self, 'remember_checkbox'):
                remember = self.remember_checkbox.isChecked()
        
        # Check for saved service
        if hasattr(self, 'service_combo'):
            current_index = self.service_combo.currentIndex()
            if current_index >= 0:
                service_name = self.service_combo.itemText(current_index)
        
        # Show the dialog using the provided custom login function
        result = show_login_dialog(self, username, remember, service_name)
        
        if result:
            # Important: Pass all 4 arguments to the signal including service
            self.login_requested.emit(
                result['username'], 
                result['password'], 
                result['remember'],
                result['service']
            )
    
    # Patch the window class's _show_login_dialog method
    window_class._show_login_dialog = _patched_show_login_dialog
    
    logger.info("Applied login dialog patch")
    return True

def enable_favorite_context_menu(content_panel):
    """Enable right-click context menu for toggling favorites in the content panel"""
    if not hasattr(content_panel, 'content_list'):
        return
        
    content_list = content_panel.content_list
    
    # Create context menu
    context_menu = QMenu(content_list)
    
    # Add actions
    toggle_favorite_action = QAction("Toggle Favorite", content_list)
    toggle_favorite_action.triggered.connect(lambda: content_panel._toggle_favorite_context_menu())
    context_menu.addAction(toggle_favorite_action)
    
    # Set context menu policy
    content_list.setContextMenuPolicy(Qt.CustomContextMenu)
    content_list.customContextMenuRequested.connect(
        lambda pos: context_menu.exec_(content_list.mapToGlobal(pos))
    )

def disable_all_context_menus_except_content(app):
    """Disable context menus for all widgets except content panel"""
    if not hasattr(app, 'window'):
        return
        
    window = app.window
    
    # Disable category panel context menu
    if hasattr(window, 'category_panel') and hasattr(window.category_panel, 'categories_list'):
        window.category_panel.categories_list.setContextMenuPolicy(Qt.NoContextMenu)
    
    # Disable info panel context menu
    if hasattr(window, 'info_panel'):
        window.info_panel.setContextMenuPolicy(Qt.NoContextMenu)
        
        # Also disable for any child widgets that might have context menus
        for child in window.info_panel.findChildren(QWidget):
            child.setContextMenuPolicy(Qt.NoContextMenu)
    
    logger.info("Disabled context menus for all widgets except content panel")

def remove_favorite_buttons(app):
    """Remove favorite buttons but keep the Favorites tab"""
    # This is just a stub function - implement as needed based on your application structure
    logger.info("Removed favorite buttons while keeping the Favorites tab")
    pass

def apply_all_patches(app):
    """Apply all patches to the application"""
    if hasattr(app, 'window'):
        # Apply URL fix patches first
        apply_api_patches(app)
        patch_service_dialog()
        
        # Apply menu patch to add Switch Service option
        patch_main_window(app.window)
        
        # Apply other patches
        enable_favorite_context_menu(app.window.content_panel)
        disable_all_context_menus_except_content(app)
        remove_favorite_buttons(app)
        
        logger.info("All patches applied successfully")
    else:
        logger.error("Failed to apply patches: app.window not found")