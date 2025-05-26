"""
ChumpStreams EPG Manager

Version: 2.0.1
Author: covchump
Last updated: 2025-05-24 06:58:42

Manages EPG functionality for ChumpStreams
"""
import logging
import threading
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger('chumpstreams')

class EPGManager(QObject):
    """Manages Electronic Program Guide functionality"""
    
    # Signals
    epg_loaded = pyqtSignal(str)  # status message
    epg_error = pyqtSignal(str)   # error message
    
    def __init__(self, epg_handler, ui_manager):
        super().__init__()
        self.epg = epg_handler
        self.ui = ui_manager
    
    def fetch_epg_data(self, username, password):
        """Fetch EPG data after login"""
        if not username or not password:
            return
            
        self.ui.show_status_message("Fetching EPG data...")
        
        # Run in a separate thread to avoid blocking the UI
        thread = threading.Thread(
            target=self._fetch_epg_data_thread,
            args=(username, password)
        )
        thread.daemon = True
        thread.start()

    def _fetch_epg_data_thread(self, username, password):
        """Background thread for fetching EPG data"""
        try:
            # Fetch the EPG data
            epg_data = self.epg.fetch_epg_data(username, password)
            
            # Schedule an update on the main thread
            channel_count = len(epg_data.get('channels', {}))
            status_message = f"EPG data loaded for {channel_count} channels"
            
            # Update UI via main thread
            QTimer.singleShot(0, lambda: self.epg_loaded.emit(status_message))
            
            logger.info(f"EPG data fetched successfully: {channel_count} channels")
        except Exception as e:
            logger.error(f"Error fetching EPG data: {str(e)}")
            # Update UI to show error
            QTimer.singleShot(0, lambda: self.epg_error.emit("EPG data loading failed"))

    def clear_cache(self):
        """Clear the EPG cache"""
        result = self.epg.clear_cache()
        return result
        
    def show_debug_dialog(self, parent, channel_name):
        """Show EPG debug dialog for a channel"""
        from chumpstreams_debug import EPGDebugDialog
        
        dialog = EPGDebugDialog(parent)
        dialog.set_data(self.epg, channel_name)
        dialog.show()
        
        return dialog