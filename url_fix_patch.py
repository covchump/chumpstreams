"""
URL Protocol Fix Patch

Version: 1.0.0
Author: covchump
Created: 2025-07-12 19:17:08

Direct patch to fix URL protocol handling issues
"""

def fix_url_protocol(url, use_https=True):
    """
    Fix URLs with double protocols and extract clean domain
    
    Args:
        url: The URL to fix
        use_https: Whether to use HTTPS if no protocol specified
        
    Returns:
        tuple: (fixed_url, adjusted_use_https)
    """
    # Save original https setting
    original_use_https = use_https
    
    # Fix URLs with duplicate protocols
    if url.startswith('https://http://'):
        url = url.replace('https://', '', 1)
        use_https = False  # Force HTTP since URL already has it
    elif url.startswith('http://https://'):
        url = url.replace('http://', '', 1)
        use_https = True  # Force HTTPS since URL already has it
        
    # Return results
    return url, use_https

def apply_patch():
    """Apply the patch to all necessary components"""
    import logging
    import sys
    
    # Get logger
    logger = logging.getLogger('chumpstreams')
    logger.info("Applying URL protocol fix patch")
    
    # Import API client
    try:
        from api_client import ApiClient
        
        # Add method to ApiClient class
        setattr(ApiClient, "fix_url_protocol", staticmethod(fix_url_protocol))
        
        # Store original __init__ method
        original_init = ApiClient.__init__
        
        # Define new init method using our fix
        def patched_init(self, base_url, use_https=True, username='', password=''):
            base_url, use_https = fix_url_protocol(base_url, use_https)
            original_init(self, base_url, use_https, username, password)
        
        # Replace __init__ method
        setattr(ApiClient, "__init__", patched_init)
        
        # Add patched set_base_url method if it doesn't exist
        if not hasattr(ApiClient, "set_base_url"):
            def set_base_url(self, url, use_https=True):
                url, use_https = fix_url_protocol(url, use_https)
                
                # Now set the base URL using the fixed URL
                if url.startswith('http://') or url.startswith('https://'):
                    # Keep existing protocol
                    self.base_url = url
                    
                    # Add port if not already specified
                    if not any(f":{port}" in self.base_url for port in ['80', '443', '8080']):
                        if url.startswith('https://'):
                            self.base_url += ':443'
                        else:
                            self.base_url += ':80'
                else:
                    # No protocol in URL, add it
                    protocol = 'https' if use_https else 'http'
                    port = '443' if use_https else '80'
                    self.base_url = f"{protocol}://{url}:{port}"
            
            setattr(ApiClient, "set_base_url", set_base_url)
        
        logger.info("Successfully patched ApiClient")
        
        # Also patch any other modules that might be handling URLs
        try:
            from chumpstreams_epg import EPGManager
            from chumpstreams_playback import PlaybackManager
            
            # Helper function to extract clean domain
            def get_clean_domain(url):
                url, _ = fix_url_protocol(url)
                
                # Extract domain without protocol
                if '://' in url:
                    url = url.split('://', 1)[1]
                
                # Remove port if present
                if ':' in url:
                    url = url.split(':', 1)[0]
                    
                return url
            
            # Patch EPGManager if exists
            if EPGManager:
                logger.info("Patching EPGManager")
                
                # Store original init
                original_epg_init = EPGManager.__init__
                
                # Define new init
                def patched_epg_init(self, server, use_https=True):
                    server, use_https = fix_url_protocol(server, use_https)
                    server = get_clean_domain(server)
                    original_epg_init(self, server, use_https)
                
                # Replace init
                setattr(EPGManager, "__init__", patched_epg_init)
            
            # Patch PlaybackManager if exists
            if PlaybackManager:
                logger.info("Patching PlaybackManager")
                
                # Store original init
                original_pb_init = PlaybackManager.__init__
                
                # Define new init that includes our fix
                def patched_pb_init(self, api, auth, content_manager, player, buffer_settings=None, 
                                    use_https=True, server=None):
                    if server:
                        server, use_https = fix_url_protocol(server, use_https)
                        server = get_clean_domain(server)
                    
                    original_pb_init(self, api, auth, content_manager, player, buffer_settings, 
                                     use_https, server)
                
                # Replace init
                setattr(PlaybackManager, "__init__", patched_pb_init)
                
            logger.info("Successfully patched supporting modules")
            
        except Exception as e:
            logger.error(f"Error patching supporting modules: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error patching API client: {str(e)}")
    
    # Return success indicator
    return True

# Apply patch when imported
patch_applied = apply_patch()