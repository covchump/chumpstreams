"""
ChumpStreams Enhanced Info Panel

Version: 1.0.0
Author: covchump
Created: 2025-05-24 11:01:16

Enhanced info panel with artwork display support
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QScrollArea, QFrame, QGridLayout, QSplitter,
    QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QFont, QIcon, QPalette, QColor

class EnhancedInfoPanel(QWidget):
    """
    Enhanced info panel with artwork display support
    
    This panel combines all functionality of the original info panel but adds
    support for displaying poster and backdrop artwork.
    
    Signals:
        episode_selected(dict): Emitted when an episode is selected
        episode_play_requested(dict): Emitted when an episode play button is clicked
        series_favorite_toggled(dict): Emitted when a series favorite button is clicked
        content_play_requested(dict): Emitted when content play button is clicked
        live_favorite_toggled(dict): Emitted when live content favorite button is clicked
        vod_favorite_toggled(dict): Emitted when VOD content favorite button is clicked
    """
    episode_selected = pyqtSignal(dict)
    episode_play_requested = pyqtSignal(dict)
    series_favorite_toggled = pyqtSignal(dict)
    content_play_requested = pyqtSignal(dict)
    live_favorite_toggled = pyqtSignal(dict)
    vod_favorite_toggled = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the enhanced info panel"""
        super().__init__(parent)
        
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
        # Create poster area (left side)
        self.poster_frame = QFrame(self)
        self.poster_frame.setFrameShape(QFrame.StyledPanel)
        self.poster_frame.setFixedWidth(300)  # Fixed width for poster
        self.poster_frame.setMinimumHeight(450)
        poster_layout = QVBoxLayout(self.poster_frame)
        poster_layout.setContentsMargins(5, 5, 5, 5)
        
        # Poster image label
        self.poster_label = QLabel(self.poster_frame)
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_label.setStyleSheet("background-color: #1A1A1A;")
        self.poster_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        poster_layout.addWidget(self.poster_label)
        
        # Add poster frame to main layout
        self.main_layout.addWidget(self.poster_frame)
        
        # Content area (right side)
        self.content_area = QWidget(self)
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        
        # Add backdrop at top of content area
        self.backdrop_label = QLabel(self.content_area)
        self.backdrop_label.setAlignment(Qt.AlignCenter)
        self.backdrop_label.setMinimumHeight(200)
        self.backdrop_label.setMaximumHeight(450)
        self.backdrop_label.setStyleSheet("background-color: #0A0A0A;")
        content_layout.addWidget(self.backdrop_label)
        
        # Info content widget - this will hold all the specific content info
        self.info_content = QWidget(self.content_area)
        self.info_layout = QVBoxLayout(self.info_content)
        self.info_layout.setContentsMargins(10, 10, 10, 10)
        self.info_layout.setSpacing(15)
        
        # Title label
        self.title_label = QLabel(self.info_content)
        self.title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        self.title_label.setWordWrap(True)
        self.info_layout.addWidget(self.title_label)
        
        # Details grid - for metadata like genre, rating, etc.
        self.details_grid = QGridLayout()
        self.details_grid.setHorizontalSpacing(20)
        self.details_grid.setVerticalSpacing(10)
        self.info_layout.addLayout(self.details_grid)
        
        # Description label
        self.description_label = QLabel(self.info_content)
        self.description_label.setStyleSheet("font-size: 11pt;")
        self.description_label.setWordWrap(True)
        self.description_label.setTextFormat(Qt.RichText)
        self.info_layout.addWidget(self.description_label)
        
        # Action buttons layout
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(10)
        
        # Play button
        self.play_button = QPushButton("Play", self.info_content)
        self.play_button.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                padding: 8px 20px;
                background-color: #3498db;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.play_button.setMinimumHeight(40)
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.clicked.connect(self._on_play_clicked)
        self.actions_layout.addWidget(self.play_button)
        
        # Favorite button
        self.favorite_button = QPushButton("Add to Favorites", self.info_content)
        self.favorite_button.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                padding: 8px 20px;
                background-color: #2ecc71;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.favorite_button.setMinimumHeight(40)
        self.favorite_button.setCursor(Qt.PointingHandCursor)
        self.favorite_button.clicked.connect(self._on_favorite_clicked)
        self.actions_layout.addWidget(self.favorite_button)
        
        # Add actions to info layout
        self.info_layout.addLayout(self.actions_layout)
        
        # Tab widget for episodes (for series)
        self.tab_widget = QTabWidget(self.info_content)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #444;
                background-color: #222;
            }
            QTabBar::tab {
                background-color: #333;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #555;
            }
        """)
        
        # Episodes tab
        self.episodes_tab = QWidget()
        episodes_layout = QVBoxLayout(self.episodes_tab)
        
        # Episodes scroll area
        self.episodes_scroll = QScrollArea(self.episodes_tab)
        self.episodes_scroll.setWidgetResizable(True)
        self.episodes_scroll.setFrameShape(QFrame.NoFrame)
        
        # Episodes content
        self.episodes_content = QWidget(self.episodes_scroll)
        self.episodes_layout = QVBoxLayout(self.episodes_content)
        self.episodes_layout.setContentsMargins(0, 0, 0, 0)
        self.episodes_layout.setSpacing(5)
        self.episodes_scroll.setWidget(self.episodes_content)
        
        episodes_layout.addWidget(self.episodes_scroll)
        
        # Add the episode tab to the tab widget
        self.tab_widget.addTab(self.episodes_tab, "Episodes")
        
        # Add the tab widget to the info layout
        self.info_layout.addWidget(self.tab_widget)
        
        # Create a scroll area for the info content to handle overflow
        self.info_scroll = QScrollArea(self.content_area)
        self.info_scroll.setWidgetResizable(True)
        self.info_scroll.setFrameShape(QFrame.NoFrame)
        self.info_scroll.setWidget(self.info_content)
        
        # Add the scroll area to the content layout
        content_layout.addWidget(self.info_scroll)
        
        # Add the content area to the main layout
        self.main_layout.addWidget(self.content_area)
        
        # Initially hide artwork elements
        self.poster_frame.setVisible(False)
        self.backdrop_label.setVisible(False)
        self.tab_widget.setVisible(False)
        
        # Keep track of the current item and episode
        self.current_item = None
        self.current_content_type = None
        self.current_episode = None
    
    def set_poster(self, pixmap):
        """
        Set the poster image
        
        Args:
            pixmap: QPixmap with the poster image
        """
        if pixmap and not pixmap.isNull():
            self.poster_label.setPixmap(pixmap)
            self.poster_frame.setVisible(True)
        else:
            self.poster_frame.setVisible(False)
    
    def set_backdrop(self, pixmap):
        """
        Set the backdrop image
        
        Args:
            pixmap: QPixmap with the backdrop image
        """
        if pixmap and not pixmap.isNull():
            self.backdrop_label.setPixmap(pixmap)
            self.backdrop_label.setVisible(True)
        else:
            self.backdrop_label.setVisible(False)
    
    def clear_artwork(self):
        """Clear all artwork images"""
        self.poster_label.clear()
        self.backdrop_label.clear()
        self.poster_frame.setVisible(False)
        self.backdrop_label.setVisible(False)
    
    def clear_info(self):
        """Clear all information displayed"""
        self.title_label.clear()
        self.clear_details_grid()
        self.description_label.clear()
        self.clear_episodes()
        self.tab_widget.setVisible(False)
        self.clear_artwork()
        self.current_item = None
        self.current_content_type = None
        self.current_episode = None
    
    def clear_details_grid(self):
        """Clear all items in the details grid"""
        # Remove all widgets from the grid
        for i in reversed(range(self.details_grid.count())):
            widget = self.details_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()
    
    def clear_episodes(self):
        """Clear all episodes from the episodes layout"""
        for i in reversed(range(self.episodes_layout.count())):
            widget = self.episodes_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
    
    def add_detail(self, row, label_text, value_text):
        """Add a detail row to the details grid"""
        label = QLabel(f"{label_text}:", self.info_content)
        label.setStyleSheet("font-weight: bold; color: #aaa;")
        
        value = QLabel(value_text, self.info_content)
        value.setWordWrap(True)
        
        self.details_grid.addWidget(label, row, 0)
        self.details_grid.addWidget(value, row, 1)
    
    def set_content_info(self, item, content_type):
        """
        Set the content information to display
        
        Args:
            item: Content item dictionary
            content_type: Type of content ('live', 'vod', 'series')
        """
        # Store the current item and type
        self.current_item = item
        self.current_content_type = content_type
        
        # Clear existing info
        self.clear_info()
        
        # Set title
        title = item.get('name', item.get('title', 'Unknown'))
        self.title_label.setText(title)
        
        # Clear and rebuild details grid
        self.clear_details_grid()
        
        # Add common details
        row = 0
        
        # For Live TV
        if content_type == 'live':
            # Set details specific to Live TV
            stream_id = item.get('stream_id', 'Unknown')
            self.add_detail(row, "Channel ID", str(stream_id))
            row += 1
            
            # Add current program if available
            if 'current_program' in item:
                program = item['current_program']
                self.add_detail(row, "Now Playing", program.get('title', 'Unknown'))
                row += 1
                
                if 'start_time' in program and 'end_time' in program:
                    time_str = f"{program.get('start_time')} - {program.get('end_time')}"
                    self.add_detail(row, "Time", time_str)
                    row += 1
                
                if 'duration' in program:
                    self.add_detail(row, "Duration", program.get('duration', ''))
                    row += 1
            
            # Add next program if available
            if 'next_program' in item:
                next_program = item['next_program']
                self.add_detail(row, "Next", next_program.get('title', 'Unknown'))
                row += 1
                
                if 'start_time' in next_program:
                    self.add_detail(row, "Starts At", next_program.get('start_time', ''))
                    row += 1
            
            # Show description from current program if available
            description = ""
            if 'current_program' in item and 'description' in item['current_program']:
                description = item['current_program']['description']
            
            self.description_label.setText(description)
            
            # Set up the favorite button
            is_favorite = item.get('is_favorite', False)
            self._update_favorite_button(is_favorite, content_type)
            
            # If there's EPG data, show it in tabs
            if 'epg_list' in item and item['epg_list']:
                self.tab_widget.setVisible(True)
                
        # For VOD
        elif content_type == 'vod':
            # Set details specific to VOD
            if 'year' in item:
                self.add_detail(row, "Year", str(item.get('year', '')))
                row += 1
                
            if 'genre' in item:
                self.add_detail(row, "Genre", item.get('genre', ''))
                row += 1
                
            if 'rating' in item:
                self.add_detail(row, "Rating", str(item.get('rating', '')))
                row += 1
                
            if 'duration' in item:
                self.add_detail(row, "Duration", item.get('duration', ''))
                row += 1
                
            if 'director' in item:
                self.add_detail(row, "Director", item.get('director', ''))
                row += 1
                
            if 'cast' in item:
                self.add_detail(row, "Cast", item.get('cast', ''))
                row += 1
            
            # Show plot/description
            if 'plot' in item:
                self.description_label.setText(item.get('plot', ''))
                
            # Set up the favorite button
            is_favorite = item.get('is_favorite', False)
            self._update_favorite_button(is_favorite, content_type)
            
        # For Series
        elif content_type == 'series' or content_type == 'full_series':
            # Set details specific to Series
            if 'year' in item:
                self.add_detail(row, "Year", str(item.get('year', '')))
                row += 1
                
            if 'genre' in item:
                self.add_detail(row, "Genre", item.get('genre', ''))
                row += 1
                
            if 'rating' in item:
                self.add_detail(row, "Rating", str(item.get('rating', '')))
                row += 1
                
            if 'series_id' in item:
                self.add_detail(row, "Series ID", str(item.get('series_id', '')))
                row += 1
                
            if 'cast' in item:
                self.add_detail(row, "Cast", item.get('cast', ''))
                row += 1
            
            # Show plot/description
            if 'plot' in item:
                self.description_label.setText(item.get('plot', ''))
                
            # Set up the favorite button
            is_favorite = item.get('is_favorite', False)
            self._update_favorite_button(is_favorite, content_type)
            
            # Show episodes if available
            if 'episodes' in item and item['episodes']:
                self.tab_widget.setVisible(True)
                self._populate_episodes(item['episodes'])
    
    def _populate_episodes(self, episodes):
        """
        Populate the episodes tab with episodes
        
        Args:
            episodes: List of episode dictionaries
        """
        # Clear any existing episodes
        self.clear_episodes()
        
        # Group episodes by season
        seasons = {}
        for episode in episodes:
            season_number = episode.get('season', 1)
            if season_number not in seasons:
                seasons[season_number] = []
            seasons[season_number].append(episode)
        
        # Sort seasons
        sorted_seasons = sorted(seasons.keys())
        
        # Add each season's episodes
        for season in sorted_seasons:
            # Add season header
            season_frame = QFrame(self.episodes_content)
            season_frame.setFrameShape(QFrame.StyledPanel)
            season_frame.setStyleSheet("QFrame { background-color: #333; border-radius: 5px; }")
            
            season_layout = QVBoxLayout(season_frame)
            season_layout.setContentsMargins(10, 10, 10, 10)
            
            season_label = QLabel(f"Season {season}", season_frame)
            season_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #ddd;")
            season_layout.addWidget(season_label)
            
            # Add episodes for this season
            for episode in seasons[season]:
                episode_widget = self._create_episode_widget(episode)
                season_layout.addWidget(episode_widget)
            
            self.episodes_layout.addWidget(season_frame)
        
        # Add spacer at the end
        self.episodes_layout.addStretch()
    
    def _create_episode_widget(self, episode):
        """
        Create a widget for an episode
        
        Args:
            episode: Episode dictionary
            
        Returns:
            QWidget: The episode widget
        """
        # Create frame
        episode_frame = QFrame(self.episodes_content)
        episode_frame.setFrameShape(QFrame.StyledPanel)
        episode_frame.setStyleSheet("QFrame { background-color: #222; border-radius: 3px; }")
        episode_frame.setCursor(Qt.PointingHandCursor)
        
        # Create layout
        episode_layout = QHBoxLayout(episode_frame)
        episode_layout.setContentsMargins(5, 5, 5, 5)
        
        # Add episode number and title
        episode_number = episode.get('episode_num', 0)
        title = episode.get('title', f"Episode {episode_number}")
        label = QLabel(f"{episode_number}. {title}", episode_frame)
        label.setStyleSheet("font-size: 12pt;")
        episode_layout.addWidget(label)
        
        # Add play button
        play_btn = QPushButton("▶", episode_frame)
        play_btn.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                background-color: #3498db;
                border-radius: 15px;
                padding: 5px;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        play_btn.setCursor(Qt.PointingHandCursor)
        
        # Use a lambda to capture the episode
        play_btn.clicked.connect(lambda checked=False, ep=episode: self.episode_play_requested.emit(ep))
        
        episode_layout.addWidget(play_btn)
        
        # Connect click on the frame to select the episode
        episode_frame.mouseReleaseEvent = lambda event, ep=episode: self._on_episode_selected(ep)
        
        return episode_frame
    
    def _on_episode_selected(self, episode):
        """
        Handle episode selection
        
        Args:
            episode: The selected episode dictionary
        """
        # Store the current episode
        self.current_episode = episode
        
        # Update UI to show selection
        # (in a real implementation, you might highlight the selected episode)
        
        # Emit signal
        self.episode_selected.emit(episode)
    
    def show_episode_info(self, episode):
        """
        Show detailed information for an episode
        
        Args:
            episode: Episode dictionary
        """
        # Store the current episode
        self.current_episode = episode
        
        # Title from episode
        title = episode.get('title', 'Unknown Episode')
        
        # Season and episode info
        season = episode.get('season', 0)
        episode_num = episode.get('episode_num', 0)
        
        # Update the title label
        self.title_label.setText(f"{title} (S{season}E{episode_num})")
        
        # Clear and rebuild details
        self.clear_details_grid()
        
        row = 0
        if 'info' in episode:
            info = episode['info']
            
            # Add details from info
            if 'duration_secs' in info:
                duration_mins = int(info['duration_secs']) // 60
                self.add_detail(row, "Duration", f"{duration_mins} minutes")
                row += 1
                
            if 'plot' in info:
                self.description_label.setText(info['plot'])
    
    def get_current_episode(self):
        """
        Get the currently selected episode
        
        Returns:
            dict: The current episode or None
        """
        return self.current_episode
    
    def _update_favorite_button(self, is_favorite, content_type):
        """
        Update the favorite button based on favorite status
        
        Args:
            is_favorite: Whether the item is a favorite
            content_type: Type of content ('live', 'vod', 'series')
        """
        if is_favorite:
            self.favorite_button.setText("Remove from Favorites")
            self.favorite_button.setStyleSheet("""
                QPushButton {
                    font-size: 14pt;
                    padding: 8px 20px;
                    background-color: #e74c3c;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
        else:
            self.favorite_button.setText("Add to Favorites")
            self.favorite_button.setStyleSheet("""
                QPushButton {
                    font-size: 14pt;
                    padding: 8px 20px;
                    background-color: #2ecc71;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
            """)
    
    def _on_play_clicked(self):
        """Handle play button click"""
        if self.current_item:
            self.content_play_requested.emit(self.current_item)
    
    def _on_favorite_clicked(self):
        """Handle favorite button click"""
        if not self.current_item or not self.current_content_type:
            return
        
        # Emit the appropriate signal based on content type
        if self.current_content_type == 'live':
            self.live_favorite_toggled.emit(self.current_item)
        elif self.current_content_type == 'vod':
            self.vod_favorite_toggled.emit(self.current_item)
        elif self.current_content_type in ['series', 'full_series']:
            self.series_favorite_toggled.emit(self.current_item)