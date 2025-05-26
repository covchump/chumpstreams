"""
ChumpStreams Settings Manager

Handles application settings, including buffer settings, UI preferences,
and other configuration options.

Last updated: 2025-05-26 09:22:18
"""

import os
import json
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QComboBox, QGroupBox, QSlider, QScrollArea
)
from PyQt5.QtCore import Qt, QSettings

logger = logging.getLogger('chumpstreams')

class SettingsManager:
    """Manages ChumpStreams settings"""
    
    def __init__(self, config_file):
        """Initialize the settings manager with config file path"""
        self.config_file = config_file
        self.settings = self._load_settings()
        self.cache_controls = []  # For dynamic cache controls
        
    def _load_settings(self):
        """Load settings from config file"""
        default_settings = {
            'buffer': {
                'network_buffer': 20,  # Default network buffer in MB
                'simple_buffer': 3  # Simple buffer setting (1-5 scale)
            },
            'ui': {
                'simple_mode': True  # Default to simple mode
            }
        }
        
        if not os.path.exists(self.config_file):
            return default_settings
            
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                
            # Ensure settings object has all required fields
            if 'settings' not in data:
                data['settings'] = default_settings
            else:
                # Ensure buffer section exists
                if 'buffer' not in data['settings']:
                    data['settings']['buffer'] = default_settings['buffer']
                # Ensure UI section exists
                if 'ui' not in data['settings']:
                    data['settings']['ui'] = default_settings['ui']
            
            return data['settings']
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            return default_settings
    
    def _save_settings(self):
        """Save settings to config file"""
        try:
            # Load existing config file
            data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
            
            # Update settings
            data['settings'] = self.settings
            
            # Save back to file
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
    
    def get_buffer_settings(self):
        """Get buffer settings as a dictionary"""
        return self.settings.get('buffer', {})
        
    def set_buffer_settings(self, buffer_settings):
        """Set buffer settings"""
        self.settings['buffer'] = buffer_settings
        return self._save_settings()
        
    def get_simple_mode(self):
        """Get simple mode setting"""
        ui_settings = self.settings.get('ui', {})
        return ui_settings.get('simple_mode', True)
        
    def set_simple_mode(self, simple_mode):
        """Set simple mode setting"""
        if 'ui' not in self.settings:
            self.settings['ui'] = {}
        self.settings['ui']['simple_mode'] = simple_mode
        return self._save_settings()
    
    def add_cache_control(self, cache_name, cache_info, clear_function):
        """Add a cache control to the settings dialog"""
        self.cache_controls.append({
            'name': cache_name,
            'info': cache_info,
            'clear': clear_function
        })
    
    def show_settings_dialog(self, parent=None):
        """Show settings dialog"""
        dialog = QDialog(parent)
        dialog.setWindowTitle("ChumpStreams Settings")
        dialog.resize(500, 300)
        
        # Main layout
        layout = QVBoxLayout(dialog)
        
        # Create tab widget - only include Playback tab now
        tabs = QTabWidget()
        
        # Create Playback tab
        playback_tab = self._create_playback_tab()
        tabs.addTab(playback_tab, "Playback")
        
        # Create Cache tab
        if self.cache_controls:
            cache_tab = self._create_cache_tab()
            tabs.addTab(cache_tab, "Cache")
        
        # Add tabs to layout
        layout.addWidget(tabs)
        
        # Add OK/Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Connect signals
        ok_button.clicked.connect(lambda: self._apply_settings(dialog, True))
        cancel_button.clicked.connect(dialog.reject)
        
        # Store widgets
        dialog.buffer_slider = None
        for widget in playback_tab.findChildren(QSlider):
            if widget.objectName() == "buffer_slider":
                dialog.buffer_slider = widget
                break
        
        # Show dialog
        result = dialog.exec_()
        return result == QDialog.Accepted
    
    def _create_playback_tab(self):
        """Create playback settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Current buffer settings
        buffer_settings = self.get_buffer_settings()
        simple_buffer = buffer_settings.get('simple_buffer', 3)
        
        # Simplified buffer settings - just a single slider
        buffer_group = QGroupBox("Stream Buffer")
        buffer_layout = QVBoxLayout()
        
        # Add simple buffer slider
        buffer_layout.addWidget(QLabel("Buffer Size:"))
        buffer_slider = QSlider(Qt.Horizontal)
        buffer_slider.setObjectName("buffer_slider")
        buffer_slider.setMinimum(1)
        buffer_slider.setMaximum(5)
        buffer_slider.setValue(simple_buffer)
        buffer_slider.setTickPosition(QSlider.TicksBelow)
        buffer_slider.setTickInterval(1)
        buffer_layout.addWidget(buffer_slider)
        
        # Add labels for min/max
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(QLabel("Smaller (less delay)"))
        labels_layout.addStretch()
        labels_layout.addWidget(QLabel("Larger (more stable)"))
        buffer_layout.addLayout(labels_layout)
        
        # Add current value label
        value_label = QLabel(f"Current Value: {simple_buffer}")
        buffer_layout.addWidget(value_label)
        
        # Update value label when slider changes
        buffer_slider.valueChanged.connect(lambda val: value_label.setText(f"Current Value: {val}"))
        
        buffer_group.setLayout(buffer_layout)
        layout.addWidget(buffer_group)
        
        # Add some explanation text
        info_label = QLabel(
            "A larger buffer provides more stable playback but with more delay. "
            "If you experience buffering, try increasing this value."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Add spacer
        layout.addStretch()
        
        return tab
    
    def _create_cache_tab(self):
        """Create cache management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Add cache controls
        for cache in self.cache_controls:
            group = QGroupBox(cache['name'])
            group_layout = QVBoxLayout()
            
            info_label = QLabel(cache['info'])
            clear_button = QPushButton("Clear Cache")
            clear_button.clicked.connect(cache['clear'])
            
            group_layout.addWidget(info_label)
            group_layout.addWidget(clear_button)
            group.setLayout(group_layout)
            layout.addWidget(group)
        
        # Add spacer
        layout.addStretch()
        
        return tab
    
    def _apply_settings(self, dialog, close=False):
        """Apply settings from dialog"""
        try:
            # Get buffer settings from slider
            if hasattr(dialog, 'buffer_slider') and dialog.buffer_slider:
                simple_buffer = dialog.buffer_slider.value()
                
                # Calculate network buffer based on simple buffer (1-5 scale)
                # 1 = 10MB, 2 = 15MB, 3 = 20MB, 4 = 30MB, 5 = 40MB
                network_buffer_map = {1: 10, 2: 15, 3: 20, 4: 30, 5: 40}
                network_buffer = network_buffer_map.get(simple_buffer, 20)
                
                # Update buffer settings
                buffer_settings = self.get_buffer_settings()
                buffer_settings['simple_buffer'] = simple_buffer
                buffer_settings['network_buffer'] = network_buffer
                self.set_buffer_settings(buffer_settings)
                
            if close:
                dialog.accept()
                
            return True
        except Exception as e:
            logger.error(f"Error applying settings: {str(e)}")
            return False