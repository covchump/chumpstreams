"""
ChumpStreams Authentication Manager

Version: 1.5.0
Author: covchump
Last updated: 2025-01-12 14:46:00

Manages authentication for ChumpStreams
"""
import json
import os
import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger('chumpstreams')

class AuthenticationManager(QObject):
    """Manages authentication state and credentials"""
    
    # Signals
    login_succeeded = pyqtSignal(str)  # username
    login_failed = pyqtSignal(str)  # error message
    
    def __init__(self, api, config_file):
        """Initialize authentication manager"""
        super().__init__()
        self.api = api
        self.config_file = config_file
        self.auth = {}
        self.saved_credentials = {}
        self.current_service = None
    
    def login(self, username, password, remember=False, service=None):
        """Attempt to login"""
        try:
            # Update API with service configuration if provided
            if service:
                self.current_service = service
                self.api.base_url = self._build_base_url(service)
                logger.info(f"Using service: {service['name']} at {self.api.base_url}")
            
            # Login using API
            result = self.api.login(username, password)
            
            if result:
                # Store auth info
                self.auth = {
                    'username': username,
                    'password': password,
                    'user_info': result.get('user_info', {}),
                    'service': self.current_service
                }
                
                # Save credentials if requested
                if remember:
                    self.save_credentials(username, password, self.current_service)
                else:
                    # Clear saved credentials for this service
                    self.clear_saved_credentials(self.current_service)
                
                # Emit success signal
                self.login_succeeded.emit(username)
            else:
                # Emit failure signal
                self.login_failed.emit("Invalid username or password")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            self.login_failed.emit(f"Login error: {str(e)}")
    
    def _build_base_url(self, service):
        """Build base URL from service configuration"""
        protocol = 'https' if service.get('use_https', True) else 'http'
        port = '443' if service.get('use_https', True) else '80'
        url = service.get('url', 'subs.chumpbumptv.com')
        return f"{protocol}://{url}:{port}"
    
    def logout(self):
        """Logout and clear authentication"""
        self.api.logout()
        self.auth = {}
        logger.info("User logged out")
    
    def get_auth(self):
        """Get current authentication info"""
        return self.auth
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return bool(self.auth)
    
    def save_credentials(self, username, password, service=None):
        """Save credentials to config file"""
        try:
            # Load existing config
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            # Update credentials section
            if 'credentials' not in config:
                config['credentials'] = {}
            
            # Service key for storing credentials
            service_key = service['name'] if service else 'default'
            
            config['credentials'][service_key] = {
                'username': username,
                'password': password,
                'service': service
            }
            
            # Also store last used service
            config['last_service'] = service_key
            
            # Save config
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved credentials for {username} on {service_key}")
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
    
    def load_saved_credentials(self):
        """Load saved credentials from config file"""
        try:
            if not os.path.exists(self.config_file):
                return
                
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Get last used service
            last_service = config.get('last_service', 'default')
            
            # Load credentials for last service
            if 'credentials' in config and last_service in config['credentials']:
                creds = config['credentials'][last_service]
                self.saved_credentials = {
                    'username': creds.get('username', ''),
                    'password': creds.get('password', ''),
                    'service': creds.get('service', None),
                    'service_name': last_service
                }
                logger.info(f"Loaded saved credentials for {self.saved_credentials['username']} on {last_service}")
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
    
    def get_saved_credentials(self):
        """Get saved credentials"""
        return self.saved_credentials
    
    def has_saved_credentials(self):
        """Check if there are saved credentials"""
        return bool(self.saved_credentials)
    
    def clear_saved_credentials(self, service=None):
        """Clear saved credentials"""
        try:
            if not os.path.exists(self.config_file):
                return
                
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            if 'credentials' in config:
                if service:
                    # Clear specific service
                    service_key = service['name'] if isinstance(service, dict) else service
                    if service_key in config['credentials']:
                        del config['credentials'][service_key]
                else:
                    # Clear all credentials
                    config['credentials'] = {}
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            # Clear in-memory credentials
            if not service or (service and self.saved_credentials.get('service_name') == (service['name'] if isinstance(service, dict) else service)):
                self.saved_credentials = {}
                
            logger.info("Cleared saved credentials")
        except Exception as e:
            logger.error(f"Error clearing credentials: {str(e)}")