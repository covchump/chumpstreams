"""
ChumpStreams UI Components

Version: 2.0.6
Author: covchump
Last updated: 2025-01-12 14:56:00

Main UI components for ChumpStreams application with service selection
"""
import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QSplitter, QLabel, QRadioButton, QButtonGroup,
    QPushButton, QLineEdit, QDialog, QCheckBox,
    QProgressBar, QMenu, QAction, QStatusBar, QMessageBox,
    QComboBox, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QDateTime
from PyQt5.QtGui import QIcon

# Import panel components from the UI Manager module
from chumpstreams_ui_manager import (
    ContentPanel, CategoryPanel, InfoPanel, EpisodeSelectionDialog
)

class ContentTypeBar(QWidget):
    """Content type selection bar with search functionality"""
    
    # Signal for content type changes
    content_type_changed = pyqtSignal(str)
    # Signal for search requests
    search_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize content type bar"""
        super().__init__(parent)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Create content type buttons
        self.content_type_group = QButtonGroup(self)
        
        # Live TV button
        self.live_button = QRadioButton("Live TV", self)
        self.live_button.setProperty("content_type", "live")
        self.live_button.setChecked(True)  # Default selection
        self.content_type_group.addButton(self.live_button)
        layout.addWidget(self.live_button)
        
        # VOD button
        self.vod_button = QRadioButton("Movies", self)
        self.vod_button.setProperty("content_type", "vod")
        self.content_type_group.addButton(self.vod_button)
        layout.addWidget(self.vod_button)
        
        # Series button
        self.series_button = QRadioButton("TV Series", self)
        self.series_button.setProperty("content_type", "series")
        self.content_type_group.addButton(self.series_button)
        layout.addWidget(self.series_button)
        
        # Favorites button
        self.favorites_button = QRadioButton("Favorites", self)
        self.favorites_button.setProperty("content_type", "favorites")
        self.content_type_group.addButton(self.favorites_button)
        layout.addWidget(self.favorites_button)
        
        # Add spacer
        layout.addStretch(1)
        
        # Search field
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search all content...")
        self.search_edit.setMinimumWidth(200)
        self.search_edit.setMaximumWidth(300)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #2C3E50;
                color: white;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)
        layout.addWidget(self.search_edit)
        
        # Search button
        self.search_button = QPushButton("Search", self)
        self.search_button.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        layout.addWidget(self.search_button)
        
        # Clear search button (initially hidden)
        self.clear_search_button = QPushButton("Clear", self)
        self.clear_search_button.setStyleSheet("""
            QPushButton {
                padding: 5px 15px;
                border-radius: 4px;
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.clear_search_button.hide()
        layout.addWidget(self.clear_search_button)
        
        # Connect signals
        self.content_type_group.buttonClicked.connect(self._on_content_type_changed)
        self.search_button.clicked.connect(self._on_search_clicked)
        self.clear_search_button.clicked.connect(self._on_clear_search)
        self.search_edit.returnPressed.connect(self._on_search_clicked)
        
        # Set fixed height to make the bar more compact
        self.setFixedHeight(45)
        
        # Apply styling
        self.setStyleSheet("""
            QRadioButton {
                font-size: 11pt;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QRadioButton:checked {
                background-color: #2C3E50;
                color: white;
            }
        """)
    
    def _on_content_type_changed(self, button):
        """Handle content type change"""
        content_type = button.property("content_type")
        if content_type:
            # Clear search when changing content type
            self._clear_search_state()
            self.content_type_changed.emit(content_type)
    
    def _on_search_clicked(self):
        """Handle search button click"""
        search_term = self.search_edit.text().strip()
        if search_term:
            # Show clear button
            self.clear_search_button.show()
            # Emit search signal
            self.search_requested.emit(search_term)
    
    def _on_clear_search(self):
        """Handle clear search button click"""
        self._clear_search_state()
        # Return to the currently selected content type
        current_type = self.get_current_content_type()
        self.content_type_changed.emit(current_type)
    
    def _clear_search_state(self):
        """Clear search UI state"""
        self.search_edit.clear()
        self.clear_search_button.hide()
    
    def get_current_content_type(self):
        """Get currently selected content type"""
        for button in self.content_type_group.buttons():
            if button.isChecked():
                return button.property("content_type")
        return "live"  # Default
    
    def set_search_mode(self, search_term):
        """Set UI to search mode"""
        self.search_edit.setText(search_term)
        self.clear_search_button.show()

class ServiceAddDialog(QDialog):
    """Dialog for adding a new service"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Service")
        self.setFixedSize(400, 200)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Service name
        layout.addWidget(QLabel("Service Name:"))
        self.service_name_edit = QLineEdit()
        self.service_name_edit.setPlaceholderText("e.g., My IPTV Service")
        layout.addWidget(self.service_name_edit)
        
        # Service URL
        layout.addWidget(QLabel("Service URL:"))
        self.service_url_edit = QLineEdit()
        self.service_url_edit.setPlaceholderText("e.g., iptv.example.com")
        layout.addWidget(self.service_url_edit)
        
        # Use HTTPS checkbox
        self.use_https_checkbox = QCheckBox("Use HTTPS")
        self.use_https_checkbox.setChecked(True)
        layout.addWidget(self.use_https_checkbox)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.add_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def get_service_data(self):
        """Get the entered service data"""
        return {
            'name': self.service_name_edit.text().strip(),
            'url': self.service_url_edit.text().strip(),
            'use_https': self.use_https_checkbox.isChecked()
        }

class ChumpStreamsMainWindow(QMainWindow):
    """Main window for ChumpStreams application"""
    
    # Signals
    login_requested = pyqtSignal(str, str, bool, dict)  # username, password, remember, service
    logout_requested = pyqtSignal()
    category_changed = pyqtSignal(str, str)  # content_type, category_name
    search_requested = pyqtSignal(str)  # search_term
    epg_debug_requested = pyqtSignal()  # Added for EPG Debug
    epg_delete_requested = pyqtSignal()  # Added for Delete EPG
    epg_refresh_requested = pyqtSignal()  # Added for Refresh EPG
    settings_requested = pyqtSignal()    # Added for Settings
    service_changed = pyqtSignal(dict)  # Service configuration changed
    
    def __init__(self):
        """Initialize main window"""
        super().__init__()
        
        # Setup window properties
        self.setWindowTitle("ChumpStreams")
        self.resize(1280, 720)
        
        # Init state
        self.is_logged_in = False
        self.current_username = ""
        self.is_search_mode = False
        self.services = self._load_services()
        
        # Create UI components
        self._create_menu_bar()
        self._create_status_bar()
        self._create_central_widget()
        self._create_login_dialog()
        
    def _load_services(self):
        """Load saved services from configuration"""
        import json
        services = []
        
        # Always include default ChumpStreams service
        services.append({
            'name': 'ChumpStreams',
            'url': 'subs.chumpbumptv.com',
            'use_https': True,
            'is_default': True
        })
        
        # Try to load additional services from config
        try:
            config_file = os.path.join(os.path.expanduser("~"), '.chumpstreams', 'services.json')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_services = json.load(f)
                    for service in saved_services:
                        if service['name'] != 'ChumpStreams':  # Don't duplicate default
                            services.append(service)
        except Exception as e:
            print(f"Error loading services: {e}")
        
        return services
    
    def _save_services(self):
        """Save services to configuration"""
        import json
        try:
            config_dir = os.path.join(os.path.expanduser("~"), '.chumpstreams')
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, 'services.json')
            
            # Only save non-default services
            custom_services = [s for s in self.services if not s.get('is_default', False)]
            
            with open(config_file, 'w') as f:
                json.dump(custom_services, f, indent=2)
        except Exception as e:
            print(f"Error saving services: {e}")
    
    def _create_menu_bar(self):
        """Create menu bar"""
        # Create menu bar
        menu_bar = self.menuBar()
        
        # Create Login menu (renamed from File)
        self.login_menu = menu_bar.addMenu('Login')
        
        # Login actions
        self.login_action = QAction('Login', self)
        self.login_action.triggered.connect(self._show_login_dialog)
        self.login_menu.addAction(self.login_action)
        
        self.logout_action = QAction('Logout', self)
        self.logout_action.triggered.connect(self.logout_requested.emit)
        self.logout_action.setEnabled(False)
        self.login_menu.addAction(self.logout_action)
        
        self.login_menu.addSeparator()
        
        self.exit_action = QAction('Exit', self)
        self.exit_action.triggered.connect(self.close)
        self.login_menu.addAction(self.exit_action)
        
        # Create Settings menu
        settings_menu = menu_bar.addMenu('Settings')
        
        preferences_action = QAction('Preferences...', self)
        preferences_action.triggered.connect(self.settings_requested.emit)
        settings_menu.addAction(preferences_action)
        
        # Create EPG menu (renamed from Debug)
        epg_menu = menu_bar.addMenu('EPG')
        
        # EPG Debug action
        debug_epg_action = QAction('EPG Debug', self)
        debug_epg_action.triggered.connect(self.epg_debug_requested.emit)
        epg_menu.addAction(debug_epg_action)
        
        # Add EPG cache clearing option (renamed)
        delete_epg_action = QAction('Delete EPG', self)
        delete_epg_action.triggered.connect(self.epg_delete_requested.emit)
        epg_menu.addAction(delete_epg_action)
        
        # Add EPG refresh option
        refresh_epg_action = QAction('Refresh EPG', self)
        refresh_epg_action.triggered.connect(self.epg_refresh_requested.emit)
        epg_menu.addAction(refresh_epg_action)
        
        # Create Help menu (skipping View menu entirely)
        help_menu = menu_bar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add login status indicator
        self.login_status_label = QLabel("Not logged in")
        self.status_bar.addPermanentWidget(self.login_status_label)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setFixedWidth(100)
        self.progress_bar.hide()  # Hide by default
        
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Default status message
        self.status_bar.showMessage("Ready")
    
    def _create_central_widget(self):
        """Create central widget"""
        # Main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Reduce spacing to move content type bar closer to top
        
        # Create content type bar with search
        self.content_type_bar = ContentTypeBar()
        main_layout.addWidget(self.content_type_bar)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Create category panel
        self.category_panel = CategoryPanel()
        self.main_splitter.addWidget(self.category_panel)
        
        # Create content splitter
        self.content_splitter = QSplitter(Qt.Horizontal)
        
        # Create content panel
        self.content_panel = ContentPanel()
        self.content_splitter.addWidget(self.content_panel)
        
        # Create info panel
        self.info_panel = InfoPanel()
        self.content_splitter.addWidget(self.info_panel)
        
        # Set sizes for content splitter
        # Making content panel 50% of its width (250 instead of 500)
        # Giving more space to info panel (550 instead of 300)
        self.content_splitter.setSizes([250, 550])
        
        # Add content splitter to main splitter
        self.main_splitter.addWidget(self.content_splitter)
        
        # Set sizes for main splitter
        self.main_splitter.setSizes([200, 800])
        
        # Add main splitter to layout
        main_layout.addWidget(self.main_splitter)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Connect signals
        self.content_type_bar.content_type_changed.connect(self._on_content_type_changed)
        self.content_type_bar.search_requested.connect(self._on_search)
        self.category_panel.category_selected.connect(self._on_category_selected)
    
    def _create_login_dialog(self):
        """Create login dialog"""
        self.login_dialog = QDialog(self)
        self.login_dialog.setWindowTitle("Login")
        self.login_dialog.setFixedSize(350, 250)
        
        # Layout
        layout = QVBoxLayout(self.login_dialog)
        
        # Service selection
        service_layout = QHBoxLayout()
        service_layout.addWidget(QLabel("Service:"))
        
        self.service_combo = QComboBox()
        self.service_combo.setMinimumWidth(200)
        # Populate services
        for service in self.services:
            self.service_combo.addItem(service['name'], service)
        # Add "Add New..." option
        self.service_combo.addItem("Add New...", None)
        service_layout.addWidget(self.service_combo)
        
        layout.addLayout(service_layout)
        
        # Connect service combo change
        self.service_combo.currentIndexChanged.connect(self._on_service_changed)
        
        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")
        layout.addWidget(self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)
        
        # Remember checkbox
        self.remember_checkbox = QCheckBox("Remember login")
        layout.addWidget(self.remember_checkbox)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self._on_login)
        buttons_layout.addWidget(self.login_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.login_dialog.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
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
                    self._save_services()
                    
                    # Add to combo box (insert before "Add New...")
                    self.service_combo.insertItem(
                        self.service_combo.count() - 1,
                        new_service['name'],
                        new_service
                    )
                    
                    # Select the new service
                    self.service_combo.setCurrentIndex(self.service_combo.count() - 2)
                else:
                    # Reset to first service
                    self.service_combo.setCurrentIndex(0)
            else:
                # Reset to first service
                self.service_combo.setCurrentIndex(0)
    
    def _show_login_dialog(self):
        """Show login dialog"""
        # Reset password field
        self.password_edit.clear()
        
        # If username was remembered, enable checkbox
        if self.username_edit.text():
            self.remember_checkbox.setChecked(True)
        
        # Show dialog
        self.login_dialog.show()
    
    def _on_login(self):
        """Handle login button click"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        remember = self.remember_checkbox.isChecked()
        
        if not username or not password:
            self.show_error_message("Login", "Please enter username and password")
            return
        
        # Get selected service
        service_index = self.service_combo.currentIndex()
        service_data = self.service_combo.itemData(service_index)
        
        if not service_data:
            self.show_error_message("Login", "Please select a valid service")
            return
        
        # Emit login signal with service data
        self.login_requested.emit(username, password, remember, service_data)
        
        # Close dialog
        self.login_dialog.accept()
    
    def _on_content_type_changed(self, content_type):
        """Handle content type change"""
        self.is_search_mode = False
        self.category_changed.emit(content_type, "")
    
    def _on_category_selected(self, category_name):
        """Handle category selection"""
        content_type = self.content_type_bar.get_current_content_type()
        self.category_changed.emit(content_type, category_name)
    
    def _on_search(self, search_term):
        """Handle search"""
        if not search_term:
            self.show_error_message("Search", "Please enter a search term")
            return
        
        self.is_search_mode = True
        # Clear categories when searching
        self.category_panel.set_categories([])
        # Show searching status
        self.show_status_message(f"Searching for '{search_term}'...")
        # Emit search signal
        self.search_requested.emit(search_term)
    
    def _show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self, 
            "About ChumpStreams",
            "ChumpStreams 2.0.6\n\n"
            "A clean, modern interface for IPTV streaming.\n\n"
            "Now with multi-service support!\n\n"
            "© 2025 covchump"
        )
    
    def show_logged_in_ui(self, username):
        """Update UI for logged in state"""
        self.is_logged_in = True
        self.current_username = username
        
        # Update login menu
        self.login_action.setEnabled(False)
        self.logout_action.setEnabled(True)
        
        # Update window title
        self.setWindowTitle(f"ChumpStreams - {username}")
        
        # Update login status in status bar
        self.login_status_label.setText(f"Logged in as: {username}")
    
    def show_logged_out_ui(self):
        """Update UI for logged out state"""
        self.is_logged_in = False
        self.current_username = ""
        
        # Update login menu
        self.login_action.setEnabled(True)
        self.logout_action.setEnabled(False)
        
        # Update window title
        self.setWindowTitle("ChumpStreams")
        
        # Update login status in status bar
        self.login_status_label.setText("Not logged in")
        
        # Clear search
        self.content_type_bar._clear_search_state()
    
    def set_login_credentials(self, username, remember=False, service_name=None):
        """Set login credentials"""
        self.username_edit.setText(username)
        self.remember_checkbox.setChecked(remember)
        
        # Set service if specified
        if service_name:
            for i in range(self.service_combo.count()):
                if self.service_combo.itemText(i) == service_name:
                    self.service_combo.setCurrentIndex(i)
                    break
    
    def get_current_service(self):
        """Get currently selected service"""
        index = self.service_combo.currentIndex()
        return self.service_combo.itemData(index)
    
    def show_status_message(self, message):
        """Show message in status bar"""
        self.status_bar.showMessage(message)
    
    def show_progress(self, show=False):
        """Show or hide progress bar - MODIFIED to default to hidden"""
        # Do not show the progress bar, keeping it hidden
        self.progress_bar.setVisible(False)
    
    def set_deterministic_progress(self, value, maximum):
        """Set deterministic progress"""
        # Just update the values but don't show the progress bar
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(False)  # Keep invisible
    
    def show_error_message(self, title, message):
        """Show error message dialog"""
        QMessageBox.critical(self, title, message)
    
    def show_info_message(self, title, message):
        """Show info message dialog"""
        QMessageBox.information(self, title, message)

    # For compatibility with backend code
    def set_simple_mode(self, enabled):
        """Compatibility stub for simple mode"""
        pass
    
    def get_simple_mode(self):
        """Compatibility stub for simple mode"""
        return False