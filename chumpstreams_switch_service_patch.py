"""
ChumpStreams Switch Service Patch

Version: 1.0.0
Author: covchump
Created: 2025-07-12 16:52:44

Adds "Switch Service" option to the Login menu
"""
import logging
from PyQt5.QtWidgets import QAction

logger = logging.getLogger('chumpstreams')

def patch_main_window(window):
    """
    Add Switch Service option to the Login menu
    
    Args:
        window: The main window to patch
    """
    try:
        # Import the login dialog directly
        from chumpstreams_login_dialog import show_login_dialog
        
        # Create the Switch Service action
        switch_service_action = QAction('Switch Service...', window)
        
        # Define the handler function
        def _on_switch_service():
            logger.info("Switch Service menu option clicked")
            
            # Get current username and remember setting if available
            username = ""
            remember = False
            
            # Try to get from the login dialog fields
            if hasattr(window, 'username_edit'):
                username = window.username_edit.text()
                
            if hasattr(window, 'remember_checkbox'):
                remember = window.remember_checkbox.isChecked()
            
            # Try to get from auth manager if available
            app = window.parent()
            if hasattr(app, 'auth_manager'):
                if hasattr(app.auth_manager, 'username'):
                    username = app.auth_manager.username
                if hasattr(app.auth_manager, 'remember_login'):
                    remember = app.auth_manager.remember_login
            
            # Get current service
            service_name = None
            current_service = getattr(app, 'current_service', None)
            if current_service:
                service_name = current_service.get('name')
            
            # Show the switch service dialog
            result = show_login_dialog(window, username, remember, service_name)
            
            # If we got a result, login with the new service
            if result:
                # Get the app instance
                if hasattr(app, '_login'):
                    app._login(
                        result['username'],
                        result['password'],
                        result['remember'],
                        result['service']
                    )
        
        # Connect the action to the handler
        switch_service_action.triggered.connect(_on_switch_service)
        
        # Add to login menu after the Login action but before Logout
        if hasattr(window, 'login_menu') and hasattr(window, 'login_action') and hasattr(window, 'logout_action'):
            # Insert after Login action
            window.login_menu.insertAction(window.logout_action, switch_service_action)
            
            # Add separator between Switch Service and Logout
            window.login_menu.insertSeparator(window.logout_action)
            
            logger.info("Added Switch Service option to Login menu")
            return True
        else:
            logger.error("Could not find login_menu, login_action, or logout_action in window")
            return False
            
    except Exception as e:
        logger.error(f"Error adding Switch Service menu option: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False