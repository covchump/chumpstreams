"""
ChumpStreams Splash Screen

Version: 1.0.0
Author: covchump
Created: 2025-05-24 09:52:09

Splash screen shown during application startup
"""
import sys
import os
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer, QSize, QRect, QEventLoop
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush, QPainter, QPixmap


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


class ChumpStreamsSplash(QSplashScreen):
    """Splash screen for ChumpStreams application"""
    
    def __init__(self):
        """Initialize splash screen"""
        # Create a pixmap for the splash screen with a black background
        self.pixmap_size = QSize(1280, 720)
        pixmap = QPixmap(self.pixmap_size)
        
        # Fill with black background
        pixmap.fill(QColor(0, 0, 0))  # Pure black
        
        super().__init__(pixmap)
        
        # Set window flags to ensure it stays on top and has no frame
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Create progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(QRect(300, 550, 680, 30))
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 5px;
            }
            
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
        """)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        
        # Create status label
        self.status_label = QLabel(self)
        self.status_label.setGeometry(QRect(300, 510, 680, 30))
        self.status_label.setStyleSheet("color: white; font-size: 14pt;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setText("Initializing...")
        
        # Draw content (like logo)
        self._draw_content()
        
        # Progress tracking variables
        self.current_progress = 0
        self.timer = None
        
    def _draw_content(self):
        """Draw content on the splash screen"""
        # Get the current pixmap
        pixmap = self.pixmap()
        
        # Create a painter to draw on the pixmap
        painter = QPainter(pixmap)
        
        # Load and draw the logo image using resource_path
        logo_path = resource_path("chumpstreams.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            
            # Scale the logo to a reasonable size if needed (max 400px wide)
            if logo_pixmap.width() > 400:
                logo_pixmap = logo_pixmap.scaledToWidth(400, Qt.SmoothTransformation)
                
            # Center the logo in the top half of the screen
            logo_x = (self.pixmap_size.width() - logo_pixmap.width()) // 2
            logo_y = 180  # Position from top
            
            # Draw the logo
            painter.drawPixmap(logo_x, logo_y, logo_pixmap)
        
        # Finish painting
        painter.end()
        
        # Set the updated pixmap
        self.setPixmap(pixmap)
    
    def start_progress(self, duration_ms=10000):
        """Start progress animation with given duration"""
        # Progress status messages
        self.status_messages = [
            "Loading core components...",
            "Initializing user interface...",
            "Loading channel data...",
            "Preparing EPG guide...",
            "Starting application..."
        ]
        
        # Calculate update interval
        self.steps_per_phase = 20  # 20 steps per phase (5 phases = 100 steps)
        self.phases = len(self.status_messages)
        interval = max(50, int(duration_ms / (self.steps_per_phase * self.phases)))
        
        # Initialize progress
        self.current_progress = 0
        self.current_phase = 0
        self.status_label.setText(self.status_messages[0])
        
        # Start timer for progress updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_progress)
        self.timer.start(interval)
    
    def _update_progress(self):
        """Update progress bar value"""
        self.current_progress += 1
        phase_progress = self.current_progress % self.steps_per_phase
        
        # Check if we need to move to next phase
        if phase_progress == 0:
            self.current_phase = min(self.current_phase + 1, self.phases - 1)
            self.status_label.setText(self.status_messages[self.current_phase])
        
        # Calculate overall progress
        overall_progress = min(100, int((self.current_progress / (self.steps_per_phase * self.phases)) * 100))
        self.progress_bar.setValue(overall_progress)
        
        # If we've reached 100%, stop the timer
        if overall_progress >= 100:
            self.timer.stop()
            QTimer.singleShot(500, self.close)  # Close after a short delay


def show_splash_screen(app, duration_ms=10000):
    """Show splash screen for the application"""
    # Create splash screen
    splash = ChumpStreamsSplash()
    
    # Position in center of screen
    screen_geometry = app.desktop().screenGeometry()
    x = (screen_geometry.width() - splash.width()) // 2
    y = (screen_geometry.height() - splash.height()) // 2
    splash.move(x, y)
    
    # Show the splash screen
    splash.show()
    app.processEvents()
    
    # Start progress animation
    splash.start_progress(duration_ms)
    
    return splash