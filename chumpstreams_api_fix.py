"""
ChumpStreams API URL Fix

Version: 1.1.0
Author: covchump
Created: 2025-07-12 17:18:34

Comprehensive fix for URL handling in API calls
"""
import logging
import re
import inspect
import types

logger = logging.getLogger('chumpstreams')

def normalize_url(url, use_https=True):
    """
    Normalize a URL to ensure it has the correct protocol and format
    
    Args:
        url: The URL string to normalize
        use_https: Whether to use HTTPS protocol if none exists
        
    Returns:
        str: Properly formatted URL
    """
    # Strip whitespace
    url = url.strip()
    
    # Check if URL already has protocol
    has_protocol = bool(re.match(r'^https?://', url))
    
    if has_protocol:
        # URL already has protocol, don't add another
        # Extract the protocol from the URL
        protocol = url.split('://', 1)[0].lower()
        logger.debug(f"URL already has protocol: {protocol}://, keeping it")
        
        # Strip any trailing slashes
        clean_url = url.rstrip('/')
        return clean_url
    else:
        # No protocol in URL, add it
        protocol = "https" if use_https else "http"
        clean_url = f"{protocol}://{url.rstrip('/')}"
        logger.debug(f"Added protocol {protocol}:// to URL")
        return clean_url

def patch_api_class(api_obj):
    """
    Patch the API class with proper URL handling
    
    Args:
        api_obj: The API instance to patch
    
    Returns:
        bool: True if patch was successful
    """
    try:
        # Store original methods before patching
        original_methods = {}
        
        # Patch set_service method
        if hasattr(api_obj, 'set_service'):
            original_methods['set_service'] = api_obj.set_service
            
            def patched_set_service(self, service):
                """Patched method to set service with proper URL handling"""
                # Make a copy of the service dict so we don't modify the original
                service_copy = service.copy()
                
                # Make sure URL is properly normalized
                if 'url' in service_copy:
                    original_url = service_copy['url']
                    use_https = service_copy.get('use_https', True)
                    service_copy['url'] = normalize_url(original_url, use_https)
                    
                    # Log the change
                    if original_url != service_copy['url']:
                        logger.info(f"Normalized service URL from '{original_url}' to '{service_copy['url']}'")
                    else:
                        logger.info(f"Using service URL as is: '{service_copy['url']}'")
                
                # Call original method with normalized service
                return original_methods['set_service'](self, service_copy)
            
            # Bind the patched method to the object
            api_obj.set_service = types.MethodType(patched_set_service, api_obj)
        
        # Patch _build_url method
        if hasattr(api_obj, '_build_url'):
            original_methods['_build_url'] = api_obj._build_url
            
            def patched_build_url(self, endpoint, use_https=True):
                """Patched method to build URLs with proper handling"""
                # Get base URL
                base_url = self.base_url if hasattr(self, 'base_url') else ""
                
                # Normalize the base URL first
                base_url = normalize_url(base_url, use_https)
                logger.debug(f"Building URL with normalized base: {base_url}")
                
                # Handle endpoint
                if endpoint.startswith('/'):
                    endpoint = endpoint[1:]
                
                # Combine and return
                full_url = f"{base_url}/{endpoint}"
                logger.debug(f"Built full URL: {full_url}")
                return full_url
            
            # Bind the patched method to the object
            api_obj._build_url = types.MethodType(patched_build_url, api_obj)
        
        # Also directly fix the base_url if it already has a bad format
        if hasattr(api_obj, 'base_url'):
            original_url = api_obj.base_url
            if original_url.startswith('https://http://') or original_url.startswith('http://https://'):
                # Fix the double protocol
                fixed_url = re.sub(r'^https?://(https?://)', r'\1', original_url)
                api_obj.base_url = fixed_url
                logger.info(f"Fixed double protocol in base_url: {original_url} -> {fixed_url}")
        
        # Add a utility method for URL normalization
        api_obj.normalize_url = types.MethodType(normalize_url, api_obj)
        
        logger.info("Successfully patched API methods for proper URL handling")
        return True
    
    except Exception as e:
        logger.error(f"Error patching API class: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def apply_api_patches(app):
    """
    Apply comprehensive patches to API handling
    
    Args:
        app: The main application instance
    """
    try:
        # Check if app has api attribute
        if not hasattr(app, 'api'):
            logger.error("Cannot patch API: app.api not found")
            return False
        
        # Log current state
        if hasattr(app, 'current_service'):
            service = app.current_service
            logger.info(f"Current service before patching: {service.get('name', 'Unknown')} at {service.get('url', 'Unknown URL')}")
        
        # Patch the API class
        success = patch_api_class(app.api)
        
        # If already connected to a service with a bad URL, reconnect
        if success and hasattr(app, 'current_service') and hasattr(app.api, 'base_url'):
            current_url = app.api.base_url
            if current_url.startswith('https://http://') or current_url.startswith('http://https://'):
                logger.info(f"Detected bad URL format: {current_url}, attempting to reconnect")
                
                # Force reconnect with current service
                if hasattr(app.api, 'set_service'):
                    try:
                        app.api.set_service(app.current_service)
                        logger.info(f"Reconnected to service with fixed URL: {app.api.base_url}")
                    except Exception as e:
                        logger.error(f"Error reconnecting to service: {str(e)}")
        
        return success
    
    except Exception as e:
        logger.error(f"Error applying API patches: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False