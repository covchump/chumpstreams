"""
ChumpStreams UI Components

Version: 2.0.3
Author: covchump
Last updated: 2025-05-24 07:54:53

Main UI components for ChumpStreams application
"""
import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QSplitter, QLabel, QRadioButton, QButtonGroup,
    QPushButton, QLineEdit, QDialog, QCheckBox,
    QProgressBar, QMenu, QAction, QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QDateTime

# Import panel components from the UI Manager module
from chumpstreams_ui_manager import (
    ContentPanel, CategoryPanel, InfoPanel, EpisodeSelectionDialog
)

class ContentTypeBar(QWidget):
    """Content type selection bar"""
    
    # Signal for content type changes
    content_type_changed = pyqtSignal(str)
    
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
        
        # Search field
        layout.addStretch(1)  # Add spacer
        
        # Connect signals
        self.content_type_group.buttonClicked.connect(self._on_content_type_changed)
        
        # Set fixed height to make the bar more compact
        self.setFixedHeight(35)
        
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
            self.content_type_changed.emit(content_type)
    
    def get_current_content_type(self):
        """Get currently selected content type"""
        for button in self.content_type_group.buttons():
            if button.isChecked():
                return button.property("content_type")
        return "live"  # Default

class ChumpStreamsMainWindow(QMainWindow):
    """Main window for ChumpStreams application"""
    
    # Signals
    login_requested = pyqtSignal(str, str, bool)  # username, password, remember
    logout_requested = pyqtSignal()
    category_changed = pyqtSignal(str, str)  # content_type, category_name
    search_requested = pyqtSignal(str)  # search_term
    epg_debug_requested = pyqtSignal()  # Added for EPG Debug
    epg_delete_requested = pyqtSignal()  # Added for Delete EPG
    epg_refresh_requested = pyqtSignal()  # Added for Refresh EPG
    settings_requested = pyqtSignal()    # Added for Settings
    
    def __init__(self):
        """Initialize main window"""
        super().__init__()
        
        # Setup window properties
        self.setWindowTitle("ChumpStreams")
        self.resize(1280, 720)
        
        # Init state
        self.is_logged_in = False
        self.current_username = ""
        
        # Create UI components
        self._create_menu_bar()
        self._create_status_bar()
        self._create_central_widget()
        self._create_login_dialog()
        
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
        
        # Create content type bar
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
        self.category_panel.category_selected.connect(self._on_category_selected)
        
        # Connect play signal from info panel to content panel
        self.info_panel.content_play_requested.connect(self.content_panel.play_content)
    
    def _create_login_dialog(self):
        """Create login dialog"""
        self.login_dialog = QDialog(self)
        self.login_dialog.setWindowTitle("Login")
        self.login_dialog.setFixedSize(300, 150)
        
        # Layout
        layout = QVBoxLayout(self.login_dialog)
        
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
        self.remember_checkbox = QCheckBox("Remember username")
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
        
        # Emit login signal
        self.login_requested.emit(username, password, remember)
        
        # Close dialog
        self.login_dialog.accept()
    
    def _on_content_type_changed(self, content_type):
        """Handle content type change"""
        self.category_changed.emit(content_type, "")
    
    def _on_category_selected(self, category_name):
        """Handle category selection"""
        content_type = self.content_type_bar.get_current_content_type()
        self.category_changed.emit(content_type, category_name)
    
    # Search method kept but not connected to UI elements
    def _on_search(self, search_term):
        """Handle search"""
        if not search_term:
            self.show_error_message("Search", "Please enter a search term")
            return
        
        self.search_requested.emit(search_term)
    
    def _show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self, 
            "About ChumpStreams",
            "ChumpStreams 2.0.3\n\n"
            "A clean, modern interface for IPTV streaming.\n\n"
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
    
    def set_login_credentials(self, username, remember=False):
        """Set login credentials"""
        self.username_edit.setText(username)
        self.remember_checkbox.setChecked(remember)
    
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