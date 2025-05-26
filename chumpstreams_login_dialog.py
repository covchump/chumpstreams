"""
ChumpStreams Login Dialog

Version: 1.0.0
Author: covchump
Created: 2025-05-24 09:52:09

Login dialog for ChumpStreams application
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QCheckBox, QPushButton, QWidget, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal


class ChumpStreamsLoginDialog(QDialog):
    """Login dialog for ChumpStreams application"""
    
    # Signal emitted when login is requested
    login_requested = pyqtSignal(str, str, bool)
    
    def __init__(self, parent=None, username="", remember=False):
        super().__init__(parent)
        self.setWindowTitle("ChumpStreams Login")
        
        # Make the dialog larger - increased width and height
        self.setMinimumSize(450, 250)  # Previous size might have been around 350x200
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)  # Increase spacing between widgets
        
        # Add header
        header_label = QLabel("Login to ChumpStreams")
        header_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Create form layout
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(15)  # Increase vertical spacing
        form_layout.setHorizontalSpacing(15)  # Increase horizontal spacing
        
        # Add username field
        username_label = QLabel("Username:")
        username_label.setStyleSheet("font-size: 12pt;")
        self.username_edit = QLineEdit()
        self.username_edit.setText(username)
        self.username_edit.setStyleSheet("font-size: 12pt; padding: 8px;")  # Increase font size and padding
        self.username_edit.setMinimumHeight(36)  # Make the input field taller
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.username_edit, 0, 1)
        
        # Add password field
        password_label = QLabel("Password:")
        password_label.setStyleSheet("font-size: 12pt;")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)  # Hide password
        self.password_edit.setStyleSheet("font-size: 12pt; padding: 8px;")  # Increase font size and padding
        self.password_edit.setMinimumHeight(36)  # Make the input field taller
        form_layout.addWidget(password_label, 1, 0)
        form_layout.addWidget(self.password_edit, 1, 1)
        
        # Add form layout to main layout with some margin
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)
        
        # Add "Remember me" checkbox
        self.remember_checkbox = QCheckBox("Remember login")
        self.remember_checkbox.setChecked(remember)
        self.remember_checkbox.setStyleSheet("font-size: 12pt;")  # Increase font size
        layout.addWidget(self.remember_checkbox)
        
        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)  # Increase spacing between buttons
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("font-size: 12pt; padding: 8px;")  # Increase font size and padding
        self.cancel_button.setMinimumHeight(40)  # Make buttons taller
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setDefault(True)
        self.login_button.setStyleSheet("font-size: 12pt; padding: 8px;")  # Increase font size and padding
        self.login_button.setMinimumHeight(40)  # Make buttons taller
        self.login_button.clicked.connect(self._handle_login)
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
        # Connect enter key to login
        self.username_edit.returnPressed.connect(self._focus_password)
        self.password_edit.returnPressed.connect(self._handle_login)
        
        # Set focus to username field if empty, otherwise to password
        if not username:
            self.username_edit.setFocus()
        else:
            self.password_edit.setFocus()
    
    def _focus_password(self):
        """Move focus to password field when enter is pressed in username field"""
        self.password_edit.setFocus()
    
    def _handle_login(self):
        """Handle login button click"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        remember = self.remember_checkbox.isChecked()
        
        if not username:
            return
            
        # Emit login signal
        self.login_requested.emit(username, password, remember)
        self.accept()


# Function to show the login dialog and return the result
def show_login_dialog(parent=None, username="", remember=False):
    """Show login dialog and return user input"""
    dialog = ChumpStreamsLoginDialog(parent, username, remember)
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        return {
            'username': dialog.username_edit.text().strip(),
            'password': dialog.password_edit.text(),
            'remember': dialog.remember_checkbox.isChecked()
        }
    else:
        return None