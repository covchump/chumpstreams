"""
ChumpStreams Authentication Manager

Version: 2.0.3
Author: covchump
Last updated: 2025-05-26 14:29:37

Handles authentication for ChumpStreams
"""
import logging
import json
import base64
import os
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger('chumpstreams')

class AuthenticationManager(QObject):
    """Manages authentication and credential persistence"""
    
    # Signals
    login_succeeded = pyqtSignal(str)  # username
    login_failed = pyqtSignal(str)     # error message
    
    def __init__(self, api_client, config_file):
        super().__init__()
        self.api = api_client
        self.config_file = config_file
        self.auth = {}
        self.saved_credentials = None
    
    def login(self, username, password, remember):
        """Handle login request"""
        try:
            # Call API login
            result = self.api.login(username, password)
            
            if isinstance(result, dict) and 'user_info' in result:
                # Store auth
                self.auth = {'username': username, 'password': password}
                
                # Save config if remember is checked
                if remember:
                    self._save_credentials()
                
                # Emit signal
                self.login_succeeded.emit(username)
                return True
            else:
                # Login failed
                self.login_failed.emit("Invalid username or password")
                return False
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            self.login_failed.emit(str(e))
            return False
    
    def logout(self):
        """Handle logout request"""
        self.api.logout()
        self.auth = {}
        self.saved_credentials = None
        
        # Delete the config file
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                logger.info(f"Config file deleted during logout: {self.config_file}")
            else:
                logger.info(f"No config file to delete: {self.config_file}")
        except Exception as e:
            logger.error(f"Error deleting config file during logout: {str(e)}")
            
        # Clear the log file contents but keep the file
        try:
            # Determine the path to the log file (in the same directory as the config file)
            cfg_dir = os.path.dirname(self.config_file)
            log_file = os.path.join(cfg_dir, "chumpstreams.log")
            
            if os.path.exists(log_file):
                # We can safely truncate the file without disturbing logging
                # by opening it in "w" mode (which truncates) then immediately closing it
                with open(log_file, 'w') as f:
                    # Write a new header line
                    f.write(f"Log file cleared during logout on {os.path.basename(self.config_file)}\n")
                
                logger.info("Log file contents cleared during logout")
            else:
                logger.info(f"No log file to clear: {log_file}")
        except Exception as e:
            logger.error(f"Error clearing log file during logout: {str(e)}")
        
        return True
    
    def get_auth(self):
        """Get current authentication details"""
        return self.auth
    
    def has_saved_credentials(self):
        """Check if there are saved credentials"""
        return (self.saved_credentials is not None and 
                isinstance(self.saved_credentials, dict) and
                self.saved_credentials.get('username') and 
                self.saved_credentials.get('password'))
    
    def get_saved_credentials(self):
        """Get saved credentials"""
        return self.saved_credentials
    
    def load_saved_credentials(self):
        """Load saved credentials from config file"""
        try:
            if not os.path.exists(self.config_file):
                return False
                
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Load saved credentials
            if config.get('save', 0) == 1:
                username = config.get('username', '')
                # Also load the password if available
                password = config.get('password', '')
                if password:
                    # Decode the obfuscated password
                    try:
                        password = base64.b64decode(password.encode('utf-8')).decode('utf-8')
                    except Exception as e:
                        password = ''
                        logger.warning(f"Could not decode saved password: {str(e)}")
                
                # Store credentials for auto-login
                if username and password:
                    self.saved_credentials = {
                        'username': username,
                        'password': password
                    }
                    return True
        except Exception as e:
            logger.error(f"Error loading saved credentials: {str(e)}")
        
        return False
    
    def _save_credentials(self, clear=False):
        """Save credentials to config file"""
        try:
            # Get username and remember state
            username = ""
            password = ""
            save = 0
            
            if self.auth and not clear:
                username = self.auth.get('username', '')
                save = 1
                # Save password if remember is enabled
                if save == 1:
                    # Simple obfuscation - not true encryption but better than plaintext
                    password_bytes = self.auth.get('password', '').encode('utf-8')
                    password = base64.b64encode(password_bytes).decode('utf-8')
            
            # Load existing config to preserve other settings
            existing_config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    existing_config = json.load(f)
            
            # Update credential fields
            existing_config['username'] = username
            existing_config['password'] = password
            existing_config['save'] = save
            
            # Save back to file
            with open(self.config_file, 'w') as f:
                json.dump(existing_config, f)
                
            logger.info("Credentials saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            return False