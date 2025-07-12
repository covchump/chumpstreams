"""
ChumpStreams Login Dialog

Version: 1.2.4
Author: covchump
Created: 2025-05-24 09:52:09
Updated: 2025-07-12 16:52:44

Login dialog for ChumpStreams application with service selection
- Added service management (add, edit, delete)
- Updated default ChumpStreams URL to covchump.visionondemand.xyz
- Reduced size of input boxes and font in Add Service dialog
- Updated example URL
"""
import os
import json
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QCheckBox, QPushButton, QWidget, QGridLayout, QComboBox,
    QMessageBox, QMenu, QAction, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal

# Set up logger
logger = logging.getLogger('chumpstreams')


class ServiceAddDialog(QDialog):
    """Dialog for adding or editing a service"""
    
    def __init__(self, parent=None, editing_service=None):
        super().__init__(parent)
        self.editing_service = editing_service
        
        if editing_service:
            self.setWindowTitle("Edit Service")
        else:
            self.setWindowTitle("Add New Service")
            
        # Keep dialog size but reduce internal element sizes
        self.setFixedSize(600, 600)
        
        # Create layout with more spacing
        layout = QVBoxLayout(self)
        layout.setSpacing(25)  # Reduced spacing slightly
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Add a title/header
        header = QLabel("Service Configuration")
        header.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2980b9;")  # Reduced from 18pt
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Service name
        name_label = QLabel("Service Name:")
        name_label.setStyleSheet("font-size: 14pt; font-weight: bold;")  # Reduced from 16pt
        layout.addWidget(name_label)
        
        self.service_name_edit = QLineEdit()
        self.service_name_edit.setPlaceholderText("e.g., My IPTV Service")
        self.service_name_edit.setStyleSheet("font-size: 13pt; padding: 10px;")  # Reduced from 15pt, 15px
        self.service_name_edit.setMinimumHeight(50)  # Reduced from 60
        layout.addWidget(self.service_name_edit)
        
        # Add vertical space
        layout.addSpacing(15)  # Reduced from 20
        
        # Service URL
        url_label = QLabel("Service URL:")
        url_label.setStyleSheet("font-size: 14pt; font-weight: bold;")  # Reduced from 16pt
        layout.addWidget(url_label)
        
        self.service_url_edit = QLineEdit()
        self.service_url_edit.setPlaceholderText("e.g., http://your.server.com")  # Updated example
        self.service_url_edit.setStyleSheet("font-size: 13pt; padding: 10px;")  # Reduced from 15pt, 15px
        self.service_url_edit.setMinimumHeight(50)  # Reduced from 60
        layout.addWidget(self.service_url_edit)
        
        # Add instructions with reduced font
        help_text = QLabel("Enter the complete URL including http:// or https:// if needed.\nDo not include port numbers.")
        help_text.setStyleSheet("font-size: 12pt; color: #555; padding: 8px;")  # Reduced from 14pt, 10px
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        # Add example for clarity with updated URL
        example_text = QLabel("Example: http://your.server.com")  # Updated example
        example_text.setStyleSheet("font-size: 12pt; font-style: italic; color: #27ae60; padding: 4px;")  # Reduced from 14pt, 5px
        layout.addWidget(example_text)
        
        # Fill fields if editing
        if editing_service:
            self.service_name_edit.setText(editing_service['name'])
            self.service_url_edit.setText(editing_service['url'])
        
        # Add stretch to push buttons to bottom
        layout.addStretch()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(25)  # Reduced from 30
        
        button_text = "Save Changes" if editing_service else "Add Service" 
        self.add_button = QPushButton(button_text)
        self.add_button.setStyleSheet("font-size: 13pt; padding: 12px 25px; background-color: #2980b9; color: white; border-radius: 8px;")  # Reduced from 15pt
        self.add_button.setMinimumHeight(60)  # Reduced from 70
        self.add_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.add_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("font-size: 13pt; padding: 12px 25px; background-color: #c0392b; color: white; border-radius: 8px;")  # Reduced from 15pt
        self.cancel_button.setMinimumHeight(60)  # Reduced from 70
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def get_service_data(self):
        """Get the entered service data"""
        return {
            'name': self.service_name_edit.text().strip(),
            'url': self.service_url_edit.text().strip()
        }


class ChumpStreamsLoginDialog(QDialog):
    """Login dialog for ChumpStreams application"""
    
    # Signal emitted when login is requested - includes service
    login_requested = pyqtSignal(str, str, bool, dict)
    
    def __init__(self, parent=None, username="", remember=False, service_name=None):
        super().__init__(parent)
        self.setWindowTitle("ChumpStreams Login")
        
        # Load services
        self.services = self._load_services()
        
        # Make the dialog larger to accommodate service selection and buttons
        self.setMinimumSize(500, 350)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Add header
        header_label = QLabel("Login to ChumpStreams")
        header_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Create form layout
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(15)
        
        # Add service selection with Edit/Delete buttons
        service_label = QLabel("Service:")
        service_label.setStyleSheet("font-size: 12pt;")
        
        # Service row layout
        service_row_layout = QHBoxLayout()
        
        # Service combobox
        self.service_combo = QComboBox()
        self.service_combo.setStyleSheet("font-size: 12pt; padding: 8px;")
        self.service_combo.setMinimumHeight(36)
        
        # Populate services
        for service in self.services:
            self.service_combo.addItem(service['name'], service)
        # Add "Add New..." option
        self.service_combo.addItem("Add New...", None)
        
        # Set current service if specified
        if service_name:
            for i in range(self.service_combo.count()):
                if self.service_combo.itemText(i) == service_name:
                    self.service_combo.setCurrentIndex(i)
                    break
        
        # Connect service change
        self.service_combo.currentIndexChanged.connect(self._on_service_changed)
        
        # Add combo box to service layout - make it take most of the space
        service_row_layout.addWidget(self.service_combo, 3)
        
        # Add Edit button
        self.edit_service_btn = QPushButton("Edit")
        self.edit_service_btn.setStyleSheet("font-size: 11pt; padding: 5px;")
        self.edit_service_btn.setMinimumHeight(36)
        self.edit_service_btn.clicked.connect(self._edit_current_service)
        service_row_layout.addWidget(self.edit_service_btn, 1)
        
        # Add Delete button
        self.delete_service_btn = QPushButton("Delete")
        self.delete_service_btn.setStyleSheet("font-size: 11pt; padding: 5px;")
        self.delete_service_btn.setMinimumHeight(36)
        self.delete_service_btn.clicked.connect(self._delete_current_service)
        service_row_layout.addWidget(self.delete_service_btn, 1)
        
        # Update button states
        self._update_service_button_states()
        
        # Add service row to form layout
        form_layout.addWidget(service_label, 0, 0)
        service_widget = QWidget()
        service_widget.setLayout(service_row_layout)
        form_layout.addWidget(service_widget, 0, 1)
        
        # Add username field
        username_label = QLabel("Username:")
        username_label.setStyleSheet("font-size: 12pt;")
        self.username_edit = QLineEdit()
        self.username_edit.setText(username)
        self.username_edit.setStyleSheet("font-size: 12pt; padding: 8px;")
        self.username_edit.setMinimumHeight(36)
        form_layout.addWidget(username_label, 1, 0)
        form_layout.addWidget(self.username_edit, 1, 1)
        
        # Add password field
        password_label = QLabel("Password:")
        password_label.setStyleSheet("font-size: 12pt;")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet("font-size: 12pt; padding: 8px;")
        self.password_edit.setMinimumHeight(36)
        form_layout.addWidget(password_label, 2, 0)
        form_layout.addWidget(self.password_edit, 2, 1)
        
        # Add form layout to main layout
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)
        
        # Add "Remember me" checkbox
        self.remember_checkbox = QCheckBox("Remember login")
        self.remember_checkbox.setChecked(remember)
        self.remember_checkbox.setStyleSheet("font-size: 12pt;")
        layout.addWidget(self.remember_checkbox)
        
        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("font-size: 12pt; padding: 8px;")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setDefault(True)
        self.login_button.setStyleSheet("font-size: 12pt; padding: 8px;")
        self.login_button.setMinimumHeight(40)
        self.login_button.clicked.connect(self._handle_login)
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
        # Connect enter key to login
        self.username_edit.returnPressed.connect(self._focus_password)
        self.password_edit.returnPressed.connect(self._handle_login)
        
        # Set focus
        if not username:
            self.username_edit.setFocus()
        else:
            self.password_edit.setFocus()
        
        # Connect service combo for button state updates
        self.service_combo.currentIndexChanged.connect(self._update_service_button_states)
    
    def _update_service_button_states(self):
        """Update the enabled state of Edit and Delete buttons based on selection"""
        index = self.service_combo.currentIndex()
        
        # Both buttons disabled by default
        self.edit_service_btn.setEnabled(False)
        self.delete_service_btn.setEnabled(False)
        
        if index >= 0:
            service = self.service_combo.itemData(index)
            
            # Enable buttons only for non-default, non-"Add New..." services
            if service is not None and not service.get('is_default', False):
                self.edit_service_btn.setEnabled(True)
                self.delete_service_btn.setEnabled(True)
    
    def _edit_current_service(self):
        """Edit the current service"""
        index = self.service_combo.currentIndex()
        if index < 0:
            return
            
        service = self.service_combo.itemData(index)
        if service is None or service.get('is_default', False):
            return  # Don't edit "Add New..." or default service
        
        dialog = ServiceAddDialog(self, editing_service=service)
        if dialog.exec_() == QDialog.Accepted:
            # Get updated service data
            updated_service = dialog.get_service_data()
            
            # Find and update the service in our list
            for i, s in enumerate(self.services):
                if s['name'] == service['name']:  # Compare by name not by object identity
                    self.services[i] = updated_service
                    break
            
            # Update combo box
            self.service_combo.setItemText(index, updated_service['name'])
            self.service_combo.setItemData(index, updated_service)
            
            # Save services
            success = self._save_services()
            if not success:
                QMessageBox.warning(
                    self, 
                    "Save Error", 
                    "Failed to save service changes. Your changes may not persist after closing the application."
                )
    
    def _delete_current_service(self):
        """Delete the current service"""
        index = self.service_combo.currentIndex()
        if index < 0:
            return
            
        service = self.service_combo.itemData(index)
        if service is None or service.get('is_default', False):
            return  # Don't delete "Add New..." or default service
        
        service_name = service['name']
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Delete Service",
            f"Are you sure you want to delete the service '{service_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from combo box
            self.service_combo.removeItem(index)
            
            # Remove from services list - compare by name, not by reference
            self.services = [s for s in self.services if s['name'] != service_name]
            
            # Save services
            success = self._save_services()
            if success:
                logger.info(f"Deleted service: {service_name}")
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Service Deleted",
                    f"Service '{service_name}' has been deleted."
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Delete Error", 
                    f"Failed to save changes after deleting service '{service_name}'. The service may reappear the next time you open the application."
                )
            
            # Select first item (usually default service)
            self.service_combo.setCurrentIndex(0)
            
            # Update button states
            self._update_service_button_states()
    
    def _get_services_file_path(self):
        """Get the path to the services configuration file"""
        config_dir = os.path.join(os.path.expanduser("~"), '.chumpstreams')
        return os.path.join(config_dir, 'services.json')
    
    def _load_services(self):
        """Load saved services from configuration"""
        services = []
        
        # Always include default ChumpStreams service with the CORRECT URL
        services.append({
            'name': 'ChumpStreams',
            'url': 'covchump.visionondemand.xyz',  # Updated from subs.chumpbumptv.com
            'is_default': True
        })
        
        # Try to load additional services from config
        try:
            config_file = self._get_services_file_path()
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_services = json.load(f)
                    for service in saved_services:
                        if service['name'] != 'ChumpStreams':  # Don't duplicate default
                            services.append(service)
                logger.info(f"Successfully loaded {len(saved_services)} custom services")
            else:
                logger.info("No saved services file found, using default only")
        except Exception as e:
            logger.error(f"Error loading services: {e}")
        
        return services
    
    def _save_services(self):
        """Save services to configuration file
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            config_dir = os.path.join(os.path.expanduser("~"), '.chumpstreams')
            os.makedirs(config_dir, exist_ok=True)
            config_file = self._get_services_file_path()
            
            # Only save non-default services
            custom_services = [s for s in self.services if not s.get('is_default', False)]
            
            with open(config_file, 'w') as f:
                json.dump(custom_services, f, indent=2)
                
            logger.info(f"Successfully saved {len(custom_services)} custom services")
            return True
            
        except Exception as e:
            logger.error(f"Error saving services: {e}")
            return False
    
    def _on_service_changed(self, index):
        """Handle service selection change"""
        if index < 0:
            return
            
        service_data = self.service_combo.itemData(index)
        
        if service_data is None:  # "Add New..." selected
            # Show add service dialog
            dialog = ServiceAddDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                new_service = dialog.get_service_data()
                if new_service['name'] and new_service['url']:
                    # Add to services list
                    self.services.append(new_service)
                    success = self._save_services()
                    
                    # Add to combo box (insert before "Add New...")
                    self.service_combo.insertItem(
                        self.service_combo.count() - 1,
                        new_service['name'],
                        new_service
                    )
                    
                    # Select the new service
                    self.service_combo.setCurrentIndex(self.service_combo.count() - 2)
                    
                    if not success:
                        QMessageBox.warning(
                            self, 
                            "Save Error", 
                            "Failed to save new service. It may not persist after closing the application."
                        )
                else:
                    # Reset to first service
                    self.service_combo.setCurrentIndex(0)
            else:
                # Reset to first service
                self.service_combo.setCurrentIndex(0)
            
        # Update button states
        self._update_service_button_states()
    
    def _focus_password(self):
        """Move focus to password field when enter is pressed in username field"""
        self.password_edit.setFocus()
    
    def _handle_login(self):
        """Handle login button click"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        remember = self.remember_checkbox.isChecked()
        
        if not username:
            QMessageBox.warning(self, "Login", "Please enter a username")
            return
        
        if not password:
            QMessageBox.warning(self, "Login", "Please enter a password")
            return
        
        # Get selected service
        service_index = self.service_combo.currentIndex()
        service_data = self.service_combo.itemData(service_index)
        
        if not service_data:
            QMessageBox.warning(self, "Login", "Please select a valid service")
            return
        
        # Emit login signal with service
        self.login_requested.emit(username, password, remember, service_data)
        self.accept()
    
    def get_current_service(self):
        """Get currently selected service"""
        index = self.service_combo.currentIndex()
        return self.service_combo.itemData(index)


# Function to show the login dialog and return the result
def show_login_dialog(parent=None, username="", remember=False, service_name=None):
    """Show login dialog and return user input"""
    dialog = ChumpStreamsLoginDialog(parent, username, remember, service_name)
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        return {
            'username': dialog.username_edit.text().strip(),
            'password': dialog.password_edit.text(),
            'remember': dialog.remember_checkbox.isChecked(),
            'service': dialog.get_current_service()
        }
    else:
        return None