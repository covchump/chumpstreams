"""
ChumpStreams Debug Dialogs

Version: 2.0.1
Author: covchump
Last updated: 2025-05-23 21:57:19

Debug dialogs for ChumpStreams application
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import logging

logger = logging.getLogger('chumpstreams')

class EPGDebugDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EPG Debug Info")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Channel info
        self.channel_label = QLabel("Channel: Not Selected")
        layout.addWidget(self.channel_label)
        
        # Channel ID info
        self.channel_id_label = QLabel("EPG Channel ID: None")
        layout.addWidget(self.channel_id_label)
        
        # Current program info
        self.current_program_label = QLabel("Current Program: None")
        layout.addWidget(self.current_program_label)
        
        # Next program info
        self.next_program_label = QLabel("Next Program: None")
        layout.addWidget(self.next_program_label)
        
        # EPG list count
        self.epg_count_label = QLabel("EPG Items: 0")
        layout.addWidget(self.epg_count_label)
        
        # EPG list
        self.epg_list = QListWidget()
        layout.addWidget(self.epg_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        buttons_layout.addWidget(self.refresh_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        
        # Store references
        self.epg_manager = None
        self.channel_name = ""
    
    def set_data(self, epg_manager, channel_name):
        self.epg_manager = epg_manager
        self.channel_name = channel_name
        self.refresh()
    
    def refresh(self):
        if not self.epg_manager or not self.channel_name:
            return
            
        self.channel_label.setText(f"Channel: {self.channel_name}")
        
        # Find EPG channel ID
        epg_channel_id = self.epg_manager.map_stream_to_epg(self.channel_name)
        self.channel_id_label.setText(f"EPG Channel ID: {epg_channel_id or 'None'}")
        
        if epg_channel_id:
            # Get current program
            current_program = self.epg_manager.get_current_program(epg_channel_id)
            if current_program:
                start_time = self.epg_manager.format_epg_time(current_program.get('start_timestamp'))
                end_time = self.epg_manager.format_epg_time(current_program.get('stop_timestamp'))
                title = current_program.get('title', 'Unknown')
                self.current_program_label.setText(f"Current Program: {title} ({start_time} - {end_time})")
            else:
                self.current_program_label.setText("Current Program: None")
            
            # Get next program
            next_program = self.epg_manager.get_next_program(epg_channel_id)
            if next_program:
                start_time = self.epg_manager.format_epg_time(next_program.get('start_timestamp'))
                end_time = self.epg_manager.format_epg_time(next_program.get('stop_timestamp'))
                title = next_program.get('title', 'Unknown')
                self.next_program_label.setText(f"Next Program: {title} ({start_time} - {end_time})")
            else:
                self.next_program_label.setText("Next Program: None")
            
            # Get full EPG
            epg_list = self.epg_manager.get_formatted_epg_for_channel(epg_channel_id, hours=12)
            self.epg_count_label.setText(f"EPG Items: {len(epg_list)}")
            
            # Populate list
            self.epg_list.clear()
            for prog in epg_list:
                time_info = f"{prog['time']} - {prog['end_time']}"
                display_text = f"{time_info}  {prog['title']}"
                item = QListWidgetItem(display_text)
                if prog.get('is_current', False):
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setBackground(QColor(60, 60, 80))
                self.epg_list.addItem(item)
        else:
            self.current_program_label.setText("Current Program: Not Available")
            self.next_program_label.setText("Next Program: Not Available")
            self.epg_count_label.setText("EPG Items: 0")
            self.epg_list.clear()


class FavoritesDebugDialog(QDialog):
    """Dialog to debug favorites information"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Favorites Debug Info")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Info header
        self.info_label = QLabel("Favorites Debug Information")
        self.info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.info_label)
        
        # Count display
        self.count_label = QLabel("Total favorites: 0")
        layout.addWidget(self.count_label)
        
        # Favorites list
        self.favorites_list = QListWidget()
        layout.addWidget(self.favorites_list)
        
        # Details area
        self.details_label = QLabel("Details")
        self.details_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.details_label)
        
        self.details_text = QListWidget()
        layout.addWidget(self.details_text)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        buttons_layout.addWidget(self.refresh_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        
        # Store references
        self.favorites_manager = None
        
        # Connect signals
        self.favorites_list.itemClicked.connect(self._show_item_details)
    
    def set_data(self, favorites_manager):
        self.favorites_manager = favorites_manager
        self.refresh()
    
    def refresh(self):
        if not self.favorites_manager:
            return
            
        # Get debug info from favorites manager
        debug_info = self.favorites_manager.debug_favorites()
        
        # Update count
        self.count_label.setText(f"Total favorites: {len(debug_info)}")
        
        # Populate list
        self.favorites_list.clear()
        for item in debug_info:
            display_text = f"{item['label']} ({item['type']})"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, item)
            self.favorites_list.addItem(list_item)
    
    def _show_item_details(self, item):
        """Show details for the selected favorite"""
        data = item.data(Qt.UserRole)
        if not data:
            return
            
        self.details_text.clear()
        
        # Add basic info
        self.details_text.addItem(f"Label: {data['label']}")
        self.details_text.addItem(f"Type: {data['type']}")
        self.details_text.addItem(f"Index: {data['index']}")
        
        # Add IDs
        self.details_text.addItem("")
        self.details_text.addItem("IDs:")
        for id_name, id_value in data['ids'].items():
            self.details_text.addItem(f"  {id_name}: {id_value or 'None'}")