"""
ChumpStreams Menu Patch

Version: 1.0.0
Author: covchump
Created: 2025-07-12 16:35:21

Adds "Switch Service" option to the login menu
"""
import logging
from PyQt5.QtWidgets import QAction

logger = logging.getLogger('chumpstreams')

def patch_main_menu(window, settings_manager):
    """
    Patch the main menu to add the Switch Service option
    
    Args:
        window: The main window
        settings_manager: The settings manager instance
    """
    try:
        # Find the menubar and login menu
        menubar = window.menuBar()
        login_menu = None
        
        # Find the login menu by title
        for menu in window.findChildren(QAction):
            if menu.text() == "Login":
                login_menu = menu.menu()
                break
        
        if not login_menu:
            # Try to find it differently
            for menu in menubar.actions():
                if menu.text() == "Login":
                    login_menu = menu.menu()
                    break
        
        if not login_menu:
            logger.error("Could not find Login menu")
            return False
            
        # Create the Switch Service action
        switch_service_action = QAction("Switch Service...", window)
        switch_service_action.triggered.connect(
            lambda: settings_manager.show_switch_service_dialog(window)
        )
        
        # Get the first action (usually "Login...")
        actions = login_menu.actions()
        
        # Insert the Switch Service action at the beginning
        if actions:
            login_menu.insertAction(actions[0], switch_service_action)
            # Add separator after it
            login_menu.insertSeparator(actions[0])
        else:
            # If no actions, just add it
            login_menu.addAction(switch_service_action)
        
        logger.info("Added Switch Service option to Login menu")
        return True
        
    except Exception as e:
        logger.error(f"Error patching main menu: {str(e)}")
        return False