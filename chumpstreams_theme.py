"""
ChumpStreams Theme

Version: 1.9.3
Author: covchump
Last updated: 2025-05-23 19:44:35

Defines the visual theme for ChumpStreams application
"""
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt


class ChumpStreamsTheme:
    """Theme definitions for ChumpStreams"""
    
    # Colors - Modern dark theme with rich purple/blue accents
    COLOR_BACKGROUND_DARK = "#121212"      # Main background - deep charcoal
    COLOR_BACKGROUND_MEDIUM = "#1E1E1E"    # Panel backgrounds - rich dark gray
    COLOR_BACKGROUND_LIGHT = "#252525"     # Selected items, buttons - lighter charcoal
    
    # Colors - Text with high contrast
    COLOR_TEXT_PRIMARY = "#FFFFFF"         # Main text - bright white for high readability
    COLOR_TEXT_SECONDARY = "#BBBBBB"       # Secondary text - light gray
    COLOR_TEXT_DISABLED = "#777777"        # Disabled text - medium gray
    
    # Colors - Vibrant accent colors
    COLOR_ACCENT_PRIMARY = "#5D49B5"       # Primary accent - rich purple
    COLOR_ACCENT_SECONDARY = "#FF7043"     # Secondary accent - vibrant coral
    COLOR_ACCENT_SUCCESS = "#43A047"       # Success color - emerald green
    COLOR_ACCENT_WARNING = "#FFCA28"       # Warning color - bright amber
    COLOR_ACCENT_ERROR = "#F44336"         # Error color - vivid red
    
    # Colors - Border and detail colors
    COLOR_METALLIC_DARK = "#333333"        # Dark metallic (borders)
    COLOR_METALLIC_MEDIUM = "#555555"      # Medium metallic
    COLOR_GRADIENT_START = "#5D49B5"       # Start of gradient effects
    COLOR_GRADIENT_END = "#7E57C2"         # End of gradient effects
    
    # Spacing
    SPACING_SMALL = 4                      # Small spacing
    SPACING_NORMAL = 8                     # Normal spacing
    SPACING_LARGE = 16                     # Large spacing
    
    # Font sizes
    FONT_SIZE_SMALL = 9                    # Small text
    FONT_SIZE_NORMAL = 10                  # Normal text
    FONT_SIZE_LARGE = 12                   # Large text
    FONT_SIZE_XLARGE = 14                  # Extra large text
    
    # Opacity
    OPACITY_DISABLED = 0.5                 # Opacity for disabled elements
    
    @classmethod
    def apply_application_theme(cls, app):
        """Apply theme to application"""
        # Create dark palette
        palette = QPalette()
        
        # Set window and base colors
        palette.setColor(QPalette.Window, QColor(cls.COLOR_BACKGROUND_DARK))
        palette.setColor(QPalette.WindowText, QColor(cls.COLOR_TEXT_PRIMARY))
        palette.setColor(QPalette.Base, QColor(cls.COLOR_BACKGROUND_MEDIUM))
        palette.setColor(QPalette.AlternateBase, QColor(cls.COLOR_BACKGROUND_DARK))
        
        # Set text colors
        palette.setColor(QPalette.Text, QColor(cls.COLOR_TEXT_PRIMARY))
        palette.setColor(QPalette.ButtonText, QColor(cls.COLOR_TEXT_PRIMARY))
        
        # Set button and highlight colors
        palette.setColor(QPalette.Button, QColor(cls.COLOR_BACKGROUND_LIGHT))
        palette.setColor(QPalette.Highlight, QColor(cls.COLOR_ACCENT_PRIMARY))
        palette.setColor(QPalette.HighlightedText, QColor(cls.COLOR_TEXT_PRIMARY))
        
        # Set disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(cls.COLOR_TEXT_DISABLED))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(cls.COLOR_TEXT_DISABLED))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(cls.COLOR_TEXT_DISABLED))
        
        # Apply palette to application
        app.setPalette(palette)
        
        # Set application font
        app_font = QFont("Segoe UI", cls.FONT_SIZE_NORMAL)
        app.setFont(app_font)
    
    @classmethod
    def get_stylesheet(cls):
        """Get application-wide stylesheet"""
        return f"""
            QMainWindow, QDialog {{
                background-color: {cls.COLOR_BACKGROUND_DARK};
                border: none;
            }}
            
            QWidget {{
                font-family: "Segoe UI", "SF Pro Text", "Roboto", sans-serif;
                color: {cls.COLOR_TEXT_PRIMARY};
            }}
            
            QFrame#panel {{
                background-color: {cls.COLOR_BACKGROUND_MEDIUM};
                border-radius: 8px;
                border: none;
            }}
            
            QSplitter::handle {{
                background-color: {cls.COLOR_METALLIC_DARK};
            }}
            
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
            
            QSplitter::handle:vertical {{
                height: 1px;
            }}
            
            QLabel[title="true"] {{
                color: {cls.COLOR_ACCENT_PRIMARY};
                font-size: {cls.FONT_SIZE_LARGE}pt;
                font-weight: bold;
                padding: 5px 0;
            }}
            
            QListWidget, QTextBrowser {{
                background-color: {cls.COLOR_BACKGROUND_MEDIUM};
                color: {cls.COLOR_TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 5px;
                outline: none;
            }}
            
            QListWidget::item {{
                padding: 8px 5px;
                margin: 2px 0px;
                border-radius: 4px;
            }}
            
            QListWidget::item:hover {{
                background-color: #303030;
            }}
            
            QListWidget::item:selected {{
                background-color: {cls.COLOR_ACCENT_PRIMARY};
                color: {cls.COLOR_TEXT_PRIMARY};
            }}
            
            QLineEdit {{
                background-color: {cls.COLOR_BACKGROUND_LIGHT};
                color: {cls.COLOR_TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                selection-background-color: {cls.COLOR_ACCENT_PRIMARY};
                selection-color: white;
            }}
            
            QLineEdit:focus {{
                border: 1px solid {cls.COLOR_ACCENT_PRIMARY};
            }}
            
            QPushButton {{
                background-color: {cls.COLOR_ACCENT_PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 18px;
                min-height: 20px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            QPushButton:hover {{
                background-color: {cls.COLOR_GRADIENT_END};
            }}
            
            QPushButton:pressed {{
                background-color: #4D3A9E;
            }}
            
            QPushButton:disabled {{
                background-color: #393939;
                color: {cls.COLOR_TEXT_DISABLED};
            }}
            
            QPushButton#primary {{
                background-color: {cls.COLOR_ACCENT_SECONDARY};
                color: white;
            }}
            
            QPushButton#primary:hover {{
                background-color: #FF8A65;
            }}
            
            QRadioButton, QCheckBox {{
                color: {cls.COLOR_TEXT_PRIMARY};
                spacing: 8px;
                padding: 4px;
            }}
            
            QRadioButton::indicator, QCheckBox::indicator {{
                width: 20px;
                height: 20px;
            }}
            
            QRadioButton::indicator::unchecked {{
                border: 2px solid {cls.COLOR_METALLIC_MEDIUM};
                background-color: {cls.COLOR_BACKGROUND_DARK};
                border-radius: 11px;
            }}
            
            QRadioButton::indicator::checked {{
                border: 2px solid {cls.COLOR_ACCENT_PRIMARY};
                background-color: {cls.COLOR_BACKGROUND_DARK};
                border-radius: 11px;
            }}
            
            QRadioButton::indicator::checked:disabled {{
                border: 2px solid {cls.COLOR_TEXT_DISABLED};
            }}
            
            QCheckBox::indicator:unchecked {{
                border: 2px solid {cls.COLOR_METALLIC_MEDIUM};
                background-color: {cls.COLOR_BACKGROUND_DARK};
                border-radius: 4px;
            }}
            
            QCheckBox::indicator:checked {{
                border: 2px solid {cls.COLOR_ACCENT_PRIMARY};
                background-color: {cls.COLOR_ACCENT_PRIMARY};
                border-radius: 4px;
                image: url(checkmark.png);
            }}
            
            QScrollBar:vertical {{
                background: #1A1A1A;
                width: 14px;
                margin: 0px;
                border-radius: 7px;
            }}
            
            QScrollBar::handle:vertical {{
                background: #444444;
                min-height: 40px;
                border-radius: 7px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: #555555;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background: #1A1A1A;
                height: 14px;
                margin: 0px;
                border-radius: 7px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: #444444;
                min-width: 40px;
                border-radius: 7px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: #555555;
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            QComboBox {{
                background-color: {cls.COLOR_BACKGROUND_LIGHT};
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 20px;
                color: {cls.COLOR_TEXT_PRIMARY};
                selection-background-color: {cls.COLOR_ACCENT_PRIMARY};
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border: none;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {cls.COLOR_BACKGROUND_DARK};
                color: {cls.COLOR_TEXT_PRIMARY};
                selection-background-color: {cls.COLOR_ACCENT_PRIMARY};
                selection-color: white;
                border: 1px solid {cls.COLOR_METALLIC_DARK};
                border-radius: 4px;
            }}
            
            QMenuBar {{
                background-color: {cls.COLOR_BACKGROUND_DARK};
                color: {cls.COLOR_TEXT_PRIMARY};
                border-bottom: 1px solid #333333;
                padding: 3px 0px;
            }}
            
            QMenuBar::item {{
                padding: 6px 12px;
                background: transparent;
                border-radius: 4px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {cls.COLOR_ACCENT_PRIMARY};
            }}
            
            QMenu {{
                background-color: {cls.COLOR_BACKGROUND_MEDIUM};
                color: {cls.COLOR_TEXT_PRIMARY};
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px 0px;
            }}
            
            QMenu::item {{
                padding: 8px 28px 8px 22px;
                border: none;
            }}
            
            QMenu::item:selected {{
                background-color: {cls.COLOR_ACCENT_PRIMARY};
            }}
            
            QStatusBar {{
                background-color: {cls.COLOR_BACKGROUND_DARK};
                color: {cls.COLOR_TEXT_SECONDARY};
                border-top: 1px solid #333333;
                padding: 4px;
                min-height: 24px;
            }}
            
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: #303030;
                text-align: center;
                color: white;
                font-weight: bold;
                height: 12px;
            }}
            
            QProgressBar::chunk {{
                background-color: {cls.COLOR_ACCENT_PRIMARY};
                border-radius: 4px;
            }}
            
            QTabWidget::pane {{
                border: none;
                background-color: {cls.COLOR_BACKGROUND_MEDIUM};
                border-radius: 8px;
                padding: 8px;
            }}
            
            QTabBar::tab {{
                background-color: {cls.COLOR_BACKGROUND_DARK};
                color: {cls.COLOR_TEXT_SECONDARY};
                border: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                min-width: 90px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {cls.COLOR_ACCENT_PRIMARY};
                color: white;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: #303030;
            }}
            
            QGroupBox {{
                background-color: {cls.COLOR_BACKGROUND_MEDIUM};
                border: none;
                border-radius: 8px;
                margin-top: 24px;
                padding-top: 12px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {cls.COLOR_ACCENT_PRIMARY};
                font-size: 11pt;
            }}
            
            /* Special styles for content panels */
            #content_panel, #info_panel, #category_panel {{
                background-color: {cls.COLOR_BACKGROUND_MEDIUM};
                border-radius: 8px;
                padding: 5px;
            }}
            
            ContentTypeBar {{
                background-color: {cls.COLOR_BACKGROUND_DARK};
                border-bottom: 1px solid #333333;
                padding: 8px 16px;
            }}
            
            /* Better styling for radio buttons in content type bar */
            ContentTypeBar QRadioButton {{
                color: {cls.COLOR_TEXT_SECONDARY};
                background-color: transparent;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            
            ContentTypeBar QRadioButton:checked {{
                color: white;
                background-color: {cls.COLOR_ACCENT_PRIMARY};
            }}
            
            ContentTypeBar QRadioButton:hover:!checked {{
                background-color: #303030;
            }}
        """