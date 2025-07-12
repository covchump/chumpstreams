"""
Fix for ChumpStreams Login Dialog

Version: 1.0.0
Author: covchump
Created: 2025-07-12 17:18:34

Adds URL validation to service add/edit dialog
"""
import logging
import re
from PyQt5.QtWidgets import QMessageBox, QDialog

logger = logging.getLogger('chumpstreams')

def normalize_url_for_display(url):
    """
    Normalize a URL for display purposes
    
    Args:
        url: The URL to normalize
        
    Returns:
        str: Clean URL without duplicate protocols
    """
    # Remove duplicate protocols
    while re.match(r'^https?://https?://', url):
        url = re.sub(r'^https?://(https?://)', r'\1', url)
    
    # Strip trailing slashes
    return url.rstrip('/')

def patch_service_dialog():
    """Patch the ServiceAddDialog class with URL validation"""
    try:
        # Import the class to patch
        from chumpstreams_login_dialog import ServiceAddDialog
        
        # Store original accept method
        original_accept = ServiceAddDialog.accept
        
        # Define patched accept method
        def patched_accept(self):
            """Patched accept method with URL validation"""
            # Get the URL
            url = self.service_url_edit.text().strip()
            
            # Validate URL
            if not url:
                QMessageBox.warning(
                    self,
                    "Invalid URL",
                    "Please enter a valid service URL."
                )
                return
            
            # Check for common issues
            if url.startswith('https://http://') or url.startswith('http://https://'):
                # Fix and show warning
                fixed_url = re.sub(r'^https?://(https?://)', r'\1', url)
                
                msg = (f"The URL has a protocol issue:\n\n"
                       f"Original: {url}\n"
                       f"Fixed: {fixed_url}\n\n"
                       f"The fixed URL will be used.")
                
                QMessageBox.warning(self, "URL Format", msg)
                
                # Update the field with fixed URL
                self.service_url_edit.setText(fixed_url)
                
                # Let the dialog continue
                original_accept(self)
            else:
                # Normalize the URL for display
                clean_url = normalize_url_for_display(url)
                if clean_url != url:
                    self.service_url_edit.setText(clean_url)
                
                # Proceed with the original accept
                original_accept(self)
        
        # Apply the patch
        ServiceAddDialog.accept = patched_accept
        
        logger.info("Successfully patched ServiceAddDialog with URL validation")
        return True
    
    except Exception as e:
        logger.error(f"Error patching ServiceAddDialog: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False