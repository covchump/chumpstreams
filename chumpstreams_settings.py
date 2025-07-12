"""
ChumpStreams Settings Manager

Handles application settings, including buffer settings, UI preferences,
and other configuration options.

Last updated: 2025-07-12 16:25:23
"""

import os
import json
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QComboBox, QGroupBox, QSlider, QScrollArea, QMessageBox, QMenu, QAction
)
from PyQt5.QtCore import Qt, QSettings, pyqtSignal

logger = logging.getLogger('chumpstreams')

class ServiceSwitchDialog(QDialog):
    """Dialog for switching between services"""
    
    service_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Switch Service")
        self.setMinimumSize(450, 200)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Select Service")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Service selection
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        service_label = QLabel("Service:")
        service_label.setStyleSheet("font-size: 12pt;")
        
        self.service_combo = QComboBox()
        self.service_combo.setStyleSheet("font-size: 12pt; padding: 8px;")
        self.service_combo.setMinimumHeight(36)
        
        # Add service options - will be populated from outside
        form_layout.addRow(service_label, self.service_combo)
        
        # Service options buttons
        buttons_layout = QHBoxLayout()
        
        self.edit_service_btn = QPushButton("Edit")
        self.edit_service_btn.setStyleSheet("font-size: 11pt; padding: 5px;")
        self.edit_service_btn.setMinimumHeight(36)
        buttons_layout.addWidget(self.edit_service_btn)
        
        self.delete_service_btn = QPushButton("Delete")
        self.delete_service_btn.setStyleSheet("font-size: 11pt; padding: 5px;")
        self.delete_service_btn.setMinimumHeight(36)
        buttons_layout.addWidget(self.delete_service_btn)
        
        self.add_service_btn = QPushButton("Add New...")
        self.add_service_btn.setStyleSheet("font-size: 11pt; padding: 5px;")
        self.add_service_btn.setMinimumHeight(36)
        buttons_layout.addWidget(self.add_service_btn)
        
        form_layout.addRow("", buttons_layout)
        
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)
        
        # Dialog buttons
        dialog_buttons = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("font-size: 12pt; padding: 8px;")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self.reject)
        dialog_buttons.addWidget(self.cancel_button)
        
        self.switch_button = QPushButton("Switch Service")
        self.switch_button.setDefault(True)
        self.switch_button.setStyleSheet("font-size: 12pt; padding: 8px; background-color: #2980b9; color: white;")
        self.switch_button.setMinimumHeight(40)
        self.switch_button.clicked.connect(self._handle_switch)
        dialog_buttons.addWidget(self.switch_button)
        
        layout.addSpacing(20)
        layout.addLayout(dialog_buttons)
    
    def _handle_switch(self):
        """Handle switch button click"""
        index = self.service_combo.currentIndex()
        if index < 0:
            return
            
        service_data = self.service_combo.itemData(index)
        if not service_data:
            QMessageBox.warning(self, "Service Selection", "Please select a valid service")
            return
            
        self.service_selected.emit(service_data)
        self.accept()
    
    def get_current_service(self):
        """Get the selected service data"""
        index = self.service_combo.currentIndex()
        if index >= 0:
            return self.service_combo.itemData(index)
        return None


class SettingsManager:
    """Manages ChumpStreams settings"""
    
    def __init__(self, config_file):
        """Initialize the settings manager with config file path"""
        self.config_file = config_file
        self.settings = self._load_settings()
        self.cache_controls = []  # For dynamic cache controls
        self.app = None  # Will be set by the application
        
    def set_app(self, app):
        """Set the application reference"""
        self.app = app
        
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
    
    def show_switch_service_dialog(self, parent=None):
        """Show dialog to switch between services"""
        # Import here to avoid circular imports
        from chumpstreams_login_dialog import show_login_dialog, ServiceAddDialog
        
        try:
            # Create the switch service dialog
            dialog = ServiceSwitchDialog(parent)
            
            # Load services
            services = self._load_services()
            
            # Populate services in combo box
            for service in services:
                dialog.service_combo.addItem(service['name'], service)
            
            # Set current service if we have one
            current_service = getattr(self.app, 'current_service', None)
            if current_service:
                for i in range(dialog.service_combo.count()):
                    if dialog.service_combo.itemText(i) == current_service.get('name'):
                        dialog.service_combo.setCurrentIndex(i)
                        break
            
            # Connect edit button
            dialog.edit_service_btn.clicked.connect(
                lambda: self._edit_service(dialog, parent)
            )
            
            # Connect delete button
            dialog.delete_service_btn.clicked.connect(
                lambda: self._delete_service(dialog, parent)
            )
            
            # Connect add button
            dialog.add_service_btn.clicked.connect(
                lambda: self._add_new_service(dialog, parent)
            )
            
            # Connect service selection signal
            dialog.service_selected.connect(self._switch_service)
            
            # Update button states based on selection
            self._update_service_button_states(dialog)
            dialog.service_combo.currentIndexChanged.connect(
                lambda: self._update_service_button_states(dialog)
            )
            
            # Show dialog
            result = dialog.exec_()
            return result == QDialog.Accepted
            
        except Exception as e:
            logger.error(f"Error showing switch service dialog: {str(e)}")
            return False
    
    def _update_service_button_states(self, dialog):
        """Update button states based on service selection"""
        index = dialog.service_combo.currentIndex()
        
        # Disable edit/delete by default
        dialog.edit_service_btn.setEnabled(False)
        dialog.delete_service_btn.setEnabled(False)
        
        if index >= 0:
            service = dialog.service_combo.itemData(index)
            
            # Enable buttons for non-default services
            if service is not None and not service.get('is_default', False):
                dialog.edit_service_btn.setEnabled(True)
                dialog.delete_service_btn.setEnabled(True)
    
    def _load_services(self):
        """Load saved services"""
        services = []
        
        # Always include default service
        services.append({
            'name': 'ChumpStreams',
            'url': 'covchump.visionondemand.xyz',
            'is_default': True
        })
        
        # Load custom services from config file
        config_file = os.path.join(os.path.expanduser("~"), '.chumpstreams', 'services.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    saved_services = json.load(f)
                    for service in saved_services:
                        if service['name'] != 'ChumpStreams':  # Don't duplicate default
                            services.append(service)
            except Exception as e:
                logger.error(f"Error loading services: {e}")
        
        return services
    
    def _save_services(self, services):
        """Save services to config file"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), '.chumpstreams')
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, 'services.json')
            
            # Only save non-default services
            custom_services = [s for s in services if not s.get('is_default', False)]
            
            with open(config_file, 'w') as f:
                json.dump(custom_services, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving services: {e}")
            return False
    
    def _edit_service(self, dialog, parent):
        """Edit the selected service"""
        from chumpstreams_login_dialog import ServiceAddDialog
        
        index = dialog.service_combo.currentIndex()
        if index < 0:
            return
            
        service = dialog.service_combo.itemData(index)
        if service is None or service.get('is_default', False):
            return  # Don't edit default service
        
        edit_dialog = ServiceAddDialog(parent, editing_service=service)
        if edit_dialog.exec_() == QDialog.Accepted:
            # Get updated service data
            updated_service = edit_dialog.get_service_data()
            
            # Update services list
            services = self._load_services()
            for i, s in enumerate(services):
                if s['name'] == service['name']:
                    services[i] = updated_service
                    break
            
            # Save services
            if self._save_services(services):
                # Update combo box
                dialog.service_combo.setItemText(index, updated_service['name'])
                dialog.service_combo.setItemData(index, updated_service)
                
                QMessageBox.information(
                    parent,
                    "Service Updated",
                    f"Service '{updated_service['name']}' has been updated."
                )
            else:
                QMessageBox.warning(
                    parent,
                    "Save Error",
                    "Failed to save service changes."
                )
    
    def _delete_service(self, dialog, parent):
        """Delete the selected service"""
        index = dialog.service_combo.currentIndex()
        if index < 0:
            return
            
        service = dialog.service_combo.itemData(index)
        if service is None or service.get('is_default', False):
            return  # Don't delete default service
        
        service_name = service['name']
        
        # Confirm deletion
        reply = QMessageBox.question(
            parent,
            "Delete Service",
            f"Are you sure you want to delete the service '{service_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Update services list
            services = self._load_services()
            services = [s for s in services if s['name'] != service_name]
            
            # Save services
            if self._save_services(services):
                # Remove from combo box
                dialog.service_combo.removeItem(index)
                
                QMessageBox.information(
                    parent,
                    "Service Deleted",
                    f"Service '{service_name}' has been deleted."
                )
                
                # Select first item
                dialog.service_combo.setCurrentIndex(0)
                self._update_service_button_states(dialog)
            else:
                QMessageBox.warning(
                    parent,
                    "Delete Error",
                    f"Failed to delete service '{service_name}'."
                )
    
    def _add_new_service(self, dialog, parent):
        """Add a new service"""
        from chumpstreams_login_dialog import ServiceAddDialog
        
        add_dialog = ServiceAddDialog(parent)
        if add_dialog.exec_() == QDialog.Accepted:
            new_service = add_dialog.get_service_data()
            
            if new_service['name'] and new_service['url']:
                # Update services list
                services = self._load_services()
                
                # Check for duplicate name
                for service in services:
                    if service['name'].lower() == new_service['name'].lower():
                        QMessageBox.warning(
                            parent,
                            "Duplicate Service",
                            f"A service with the name '{new_service['name']}' already exists."
                        )
                        return
                
                services.append(new_service)
                
                # Save services
                if self._save_services(services):
                    # Add to combo box
                    dialog.service_combo.addItem(new_service['name'], new_service)
                    
                    # Select the new service
                    dialog.service_combo.setCurrentIndex(dialog.service_combo.count() - 1)
                    self._update_service_button_states(dialog)
                    
                    QMessageBox.information(
                        parent,
                        "Service Added",
                        f"Service '{new_service['name']}' has been added."
                    )
                else:
                    QMessageBox.warning(
                        parent,
                        "Save Error",
                        "Failed to save new service."
                    )
    
    def _switch_service(self, service):
        """Switch to the selected service"""
        if not self.app or not hasattr(self.app, '_login'):
            logger.error("Cannot switch service: app reference not set or missing login method")
            return
            
        try:
            # Get current username and password
            username = ""
            password = ""
            remember = False
            
            if hasattr(self.app, 'auth_manager'):
                username = getattr(self.app.auth_manager, 'username', "")
                password = getattr(self.app.auth_manager, 'password', "")
                remember = getattr(self.app.auth_manager, 'remember_login', False)
            
            if not username or not password:
                # If no credentials, show login dialog
                from chumpstreams_login_dialog import show_login_dialog
                result = show_login_dialog(self.app.window, username, remember, service['name'])
                
                if result:
                    # Use credentials from login dialog
                    username = result['username']
                    password = result['password']
                    remember = result['remember']
                    service = result['service']  # Use potentially updated service
                else:
                    # User cancelled login
                    return
            
            # Log out current user if logged in
            if hasattr(self.app, 'auth_manager') and self.app.auth_manager.is_logged_in():
                self.app.auth_manager.logout()
            
            # Login with new service
            self.app._login(username, password, remember, service)
            
            # Update window title to reflect new service
            if hasattr(self.app, 'window'):
                self.app.window.setWindowTitle(f"ChumpStreams - {service['name']}")
            
            # Log the switch
            logger.info(f"Switched to service: {service['name']}")
            
        except Exception as e:
            logger.error(f"Error switching service: {str(e)}")
            if hasattr(self.app, 'window'):
                QMessageBox.critical(
                    self.app.window,
                    "Switch Service Error",
                    f"An error occurred while switching services: {str(e)}"
                )
    
    def add_menu_actions(self, menubar, login_menu):
        """Add settings-related actions to the menu bar"""
        # Add Switch Service option to login menu
        switch_service_action = QAction("Switch Service...", menubar)
        switch_service_action.triggered.connect(lambda: self.show_switch_service_dialog(menubar.parent()))
        
        # Add the action after the login action but before any separators
        actions = login_menu.actions()
        if actions:
            # Find the login action - usually the first one
            login_action = actions[0]
            # Insert switch service after login
            login_menu.insertAction(login_action, switch_service_action)
            # Add a separator
            login_menu.insertSeparator(login_action)
    
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