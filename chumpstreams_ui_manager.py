"""
ChumpStreams UI Manager

Version: 2.0.6
Author: covchump
Last updated: 2025-05-26 15:22:41

Handles UI coordination and panel components for ChumpStreams
"""
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt, QSize
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMenu, QAction, QStackedWidget,
    QDialog, QDialogButtonBox
)
from PyQt5.QtGui import QColor, QFont

logger = logging.getLogger('chumpstreams')

# Import for episode selection dialog
import re

class EpisodeSelectionDialog(QDialog):
    """Dialog for selecting episodes from a series"""
    
    def __init__(self, parent=None, episodes=None, series_title=""):
        super().__init__(parent)
        
        self.setWindowTitle(f"Episodes - {series_title}")
        self.setMinimumSize(500, 400)
        
        # Store episodes data
        self.episodes = episodes or []
        self.selected_episode = None
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create episode list widget
        self.episodes_list = QListWidget()
        layout.addWidget(self.episodes_list)
        
        # Add episodes to list grouped by season
        self._populate_episodes_list()
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect signals
        self.episodes_list.itemDoubleClicked.connect(self.accept)
        
    def _populate_episodes_list(self):
        """Populate the episodes list"""
        if not self.episodes:
            return
            
        # Group episodes by season
        seasons = {}
        for episode in self.episodes:
            season = episode.get('season', 1)
            if season not in seasons:
                seasons[season] = []
            seasons[season].append(episode)
        
        # Add episodes to list
        for season in sorted(seasons.keys()):
            # Add season header
            season_header = QListWidgetItem(f"Season {season}")
            season_header.setBackground(QColor(40, 40, 50))
            font = season_header.font()
            font.setBold(True)
            season_header.setFont(font)
            self.episodes_list.addItem(season_header)
            
            # Add episodes with proper numbering
            for episode in sorted(seasons[season], key=lambda x: int(x.get('episode', x.get('episode_number', 1)))):
                # Try multiple possible field names for episode number
                episode_num = episode.get('episode', episode.get('episode_number', episode.get('episodeNumber', '')))
                
                # If we still don't have a number, check if episode number is embedded in the title
                if not episode_num:
                    # Try to extract from titles like "S01E02 - Episode Name"
                    title = episode.get('title', episode.get('name', ''))
                    match = re.search(r'E(\d+)', title)
                    if match:
                        episode_num = match.group(1)
                
                # If we still have no episode number, use a counter based on position
                if not episode_num:
                    # Just use the count within this season (starting at 1)
                    episode_num = str(seasons[season].index(episode) + 1)
                
                # Make sure episode_num is a string
                episode_num = str(episode_num)
                
                title = episode.get('title', episode.get('name', 'Unknown'))
                display_text = f"E{episode_num}: {title}"
                
                # Store the episode data in the item
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, episode)
                self.episodes_list.addItem(item)
                
    def get_selected_episode(self):
        """Get the selected episode"""
        current_item = self.episodes_list.currentItem()
        if current_item:
            text = current_item.text()
            # Skip season headers
            if text.startswith("Season "):
                return None
            
            # Return the episode data stored in the item
            return current_item.data(Qt.UserRole)
        return None


class CategoryPanel(QWidget):
    """Category panel for navigation"""
    
    # Signal for category selection
    category_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize category panel"""
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create category list
        self.categories_list = QListWidget()
        self.categories_list.setAlternatingRowColors(True)
        layout.addWidget(self.categories_list)
        
        # Connect signals
        self.categories_list.itemClicked.connect(self._on_category_clicked)
    
    def set_categories(self, categories):
        """Set category list"""
        self.categories_list.clear()
        self.categories_list.addItems(categories)
    
    def _on_category_clicked(self, item):
        """Handle category selection"""
        category_name = item.text()
        self.category_selected.emit(category_name)


class ContentPanel(QWidget):
    """Content panel for displaying content items"""
    
    # Signals
    content_selected = pyqtSignal(list, int)
    content_play_requested = pyqtSignal(dict)
    favorite_toggled = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize content panel"""
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create content list
        self.content_list = QListWidget()
        self.content_list.setAlternatingRowColors(True)
        layout.addWidget(self.content_list)
        
        # Store content items
        self.content_items = []
        self.content_type = ""
        
        # Connect signals
        self.content_list.itemClicked.connect(self._on_content_clicked)
        self.content_list.itemDoubleClicked.connect(self._on_content_double_clicked)
        self.content_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.content_list.customContextMenuRequested.connect(self._show_context_menu)
    
    def set_content(self, content_type, items, display_names):
        """Set content list"""
        self.content_list.clear()
        self.content_items = items
        self.content_type = content_type
        
        if not items or not display_names or len(items) != len(display_names):
            return
            
        # Add items
        self.content_list.addItems(display_names)
    
    def clear_content(self):
        """Clear content list"""
        self.content_list.clear()
        self.content_items = []
        self.content_type = ""
    
    def show_empty_message(self, message, title=""):
        """Show an empty state message in the content panel"""
        # Clear existing content
        self.content_list.clear()
        self.content_items = []
        
        # Create a custom widget to display message
        message_widget = QListWidgetItem()
        
        # Set custom height to give enough space for the message
        message_widget.setSizeHint(QSize(self.content_list.width(), 200))
        
        # Create a widget to hold the formatted message
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Add title if provided
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #aaaaaa;")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            layout.addSpacing(15)
        
        # Add message text
        msg_label = QLabel(message)
        msg_label.setStyleSheet("font-size: 11pt; color: #bbbbbb;")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        
        # Add to list
        self.content_list.addItem(message_widget)
        self.content_list.setItemWidget(message_widget, container)
    
    def _on_content_clicked(self, item):
        """Handle content selection"""
        index = self.content_list.row(item)
        self.content_selected.emit(self.content_items, index)
    
    def _on_content_double_clicked(self, item):
        """Handle content double-click (play)"""
        index = self.content_list.row(item)
        if index >= 0 and index < len(self.content_items):
            self.content_play_requested.emit(self.content_items[index])
    
    def _show_context_menu(self, position):
        """Show context menu for content item"""
        index = self.content_list.indexAt(position).row()
        if index < 0 or index >= len(self.content_items):
            return
            
        # Create context menu
        menu = QMenu()
        
        # Play action
        play_action = QAction("Play", self)
        play_action.triggered.connect(lambda: self._on_context_menu_play(index))
        menu.addAction(play_action)
        
        # Favorite action
        if self.content_type == 'favorites':
            fav_action = QAction("Remove from Favorites", self)
        else:
            fav_action = QAction("Add to Favorites", self)
        fav_action.triggered.connect(lambda: self._on_context_menu_favorite(index))
        menu.addAction(fav_action)
        
        # Show menu
        menu.exec_(self.content_list.mapToGlobal(position))
    
    def _on_context_menu_play(self, index):
        """Handle play action from context menu"""
        if index >= 0 and index < len(self.content_items):
            self.content_play_requested.emit(self.content_items[index])
    
    def _on_context_menu_favorite(self, index):
        """Handle favorite action from context menu"""
        if index >= 0 and index < len(self.content_items):
            self.favorite_toggled.emit(self.content_items[index])
    
    def play_content(self, item):
        """Play content (called from outside)"""
        if isinstance(item, dict):
            self.content_play_requested.emit(item)
        else:
            # Find item by name
            name = str(item)
            for i, content_item in enumerate(self.content_items):
                item_name = content_item.get('name', content_item.get('title', 'Unknown'))
                if name == item_name:
                    self.content_play_requested.emit(content_item)
                    break


class InfoPanel(QWidget):
    """Information panel for displaying content details"""
    
    # Signals
    episode_selected = pyqtSignal(dict)
    episode_play_requested = pyqtSignal(dict)
    series_favorite_toggled = pyqtSignal(dict)
    content_play_requested = pyqtSignal(dict)  # Added for direct play
    choose_episode_requested = pyqtSignal() # Added for episode selection
    live_favorite_toggled = pyqtSignal(dict)  # New signal for live TV favorites
    vod_favorite_toggled = pyqtSignal(dict)   # New signal for VOD favorites
    
    def __init__(self, parent=None):
        """Initialize info panel"""
        super().__init__(parent)
        
        # Create layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Create stacked widget for different content types
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        # Create widgets for different content types
        self._create_live_info_widget()  # Live TV info
        self._create_vod_info_widget()   # Movie info
        self._create_series_info_widget()  # Series info
        self._create_episode_info_widget()  # Episode info
        
        # Add empty widget for when no content is selected
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        
        # Add stretcher to push content to center
        empty_layout.addStretch(1)
        
        # Create centered message label
        empty_message = QLabel("Please select content")
        empty_message.setAlignment(Qt.AlignCenter)
        empty_message.setStyleSheet("""
            font-size: 14pt; 
            color: #AAAAAA; 
            font-weight: bold;
            margin: 20px;
        """)
        empty_layout.addWidget(empty_message)
        
        # Add stretcher to push content to center
        empty_layout.addStretch(1)
        
        # Add the empty widget to the stacked widget
        self.stacked_widget.addWidget(self.empty_widget)
        
        # Store current content
        self.current_content = None
        self.current_type = ""
        self.current_episode = None
        
        # Set empty widget as default
        self.stacked_widget.setCurrentWidget(self.empty_widget)
    
    def _create_live_info_widget(self):
        """Create widget for live TV info"""
        self.live_widget = QWidget()
        layout = QVBoxLayout(self.live_widget)
        
        # Channel info
        self.live_title_label = QLabel()
        self.live_title_label.setWordWrap(True)
        self.live_title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.live_title_label)
        
        # Current program
        self.current_program_group = QWidget()
        current_program_layout = QVBoxLayout(self.current_program_group)
        current_program_layout.setContentsMargins(0, 0, 0, 0)
        
        self.current_program_label = QLabel("Current Program")
        self.current_program_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        current_program_layout.addWidget(self.current_program_label)
        
        self.current_program_title = QLabel()
        self.current_program_title.setWordWrap(True)
        self.current_program_title.setStyleSheet("font-size: 12pt;")
        current_program_layout.addWidget(self.current_program_title)
        
        self.current_program_time = QLabel()
        current_program_layout.addWidget(self.current_program_time)
        
        self.current_program_desc = QLabel()
        self.current_program_desc.setWordWrap(True)
        current_program_layout.addWidget(self.current_program_desc)
        
        layout.addWidget(self.current_program_group)
        
        # Next program
        self.next_program_group = QWidget()
        next_program_layout = QVBoxLayout(self.next_program_group)
        next_program_layout.setContentsMargins(0, 0, 0, 0)
        
        self.next_program_label = QLabel("Next Program")
        self.next_program_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        next_program_layout.addWidget(self.next_program_label)
        
        self.next_program_title = QLabel()
        self.next_program_title.setWordWrap(True)
        next_program_layout.addWidget(self.next_program_title)
        
        self.next_program_time = QLabel()
        next_program_layout.addWidget(self.next_program_time)
        
        layout.addWidget(self.next_program_group)
        
        # EPG list
        self.epg_label = QLabel("Program Guide")
        self.epg_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        layout.addWidget(self.epg_label)
        
        self.epg_list = QListWidget()
        layout.addWidget(self.epg_list)
        
        # Button row with Play and Favorite buttons
        buttons_layout = QHBoxLayout()
        
        # Play button
        self.live_play_button = QPushButton("Play")
        self.live_play_button.clicked.connect(self._on_live_play_clicked)
        buttons_layout.addWidget(self.live_play_button)
        
        # Add to Favorites button
        self.live_favorite_button = QPushButton("Add to Favorites")
        self.live_favorite_button.clicked.connect(self._on_live_favorite_clicked)
        buttons_layout.addWidget(self.live_favorite_button)
        
        layout.addLayout(buttons_layout)
        
        # Add widget to stacked widget
        self.stacked_widget.addWidget(self.live_widget)
    
    def _create_vod_info_widget(self):
        """Create widget for movie info"""
        self.vod_widget = QWidget()
        layout = QVBoxLayout(self.vod_widget)
        
        # Movie info
        self.vod_title_label = QLabel()
        self.vod_title_label.setWordWrap(True)
        self.vod_title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.vod_title_label)
        
        # Year and genre
        self.vod_year_genre_label = QLabel()
        layout.addWidget(self.vod_year_genre_label)
        
        # Rating and duration
        self.vod_rating_duration_label = QLabel()
        layout.addWidget(self.vod_rating_duration_label)
        
        # Director and cast
        self.vod_director_label = QLabel()
        self.vod_director_label.setWordWrap(True)
        layout.addWidget(self.vod_director_label)
        
        self.vod_cast_label = QLabel()
        self.vod_cast_label.setWordWrap(True)
        layout.addWidget(self.vod_cast_label)
        
        # Plot
        self.vod_plot_label = QLabel("Plot")
        self.vod_plot_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        layout.addWidget(self.vod_plot_label)
        
        self.vod_plot = QLabel()
        self.vod_plot.setWordWrap(True)
        layout.addWidget(self.vod_plot)
        
        # Add spacer
        layout.addStretch(1)
        
        # Button row with Play and Favorite buttons
        buttons_layout = QHBoxLayout()
        
        # Play button
        self.vod_play_button = QPushButton("Play")
        self.vod_play_button.clicked.connect(self._on_vod_play_clicked)
        buttons_layout.addWidget(self.vod_play_button)
        
        # Add to Favorites button
        self.vod_favorite_button = QPushButton("Add to Favorites")
        self.vod_favorite_button.clicked.connect(self._on_vod_favorite_clicked)
        buttons_layout.addWidget(self.vod_favorite_button)
        
        layout.addLayout(buttons_layout)
        
        # Add widget to stacked widget
        self.stacked_widget.addWidget(self.vod_widget)
    
    def _create_series_info_widget(self):
        """Create widget for series info"""
        self.series_widget = QWidget()
        layout = QVBoxLayout(self.series_widget)
        
        # Series info
        self.series_title_label = QLabel()
        self.series_title_label.setWordWrap(True)
        self.series_title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.series_title_label)
        
        # Genre
        self.series_genre_label = QLabel()
        layout.addWidget(self.series_genre_label)
        
        # Rating
        self.series_rating_label = QLabel()
        layout.addWidget(self.series_rating_label)
        
        # Director and cast
        self.series_director_label = QLabel()
        self.series_director_label.setWordWrap(True)
        layout.addWidget(self.series_director_label)
        
        self.series_cast_label = QLabel()
        self.series_cast_label.setWordWrap(True)
        layout.addWidget(self.series_cast_label)
        
        # Plot
        self.series_plot_label = QLabel("Plot")
        self.series_plot_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        layout.addWidget(self.series_plot_label)
        
        self.series_plot = QLabel()
        self.series_plot.setWordWrap(True)
        layout.addWidget(self.series_plot)
        
        # Episodes section removed - we're removing both the label and list from the UI
        # Keep a reference to the episodes list for internal use but don't add it to the layout
        self.episodes_list = QListWidget()
        
        # Add spacer to push content up and buttons to the bottom
        layout.addStretch(1)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        # Choose Episode button
        self.choose_episode_button = QPushButton("Choose Episode")
        self.choose_episode_button.clicked.connect(self._on_choose_episode_clicked)
        buttons_layout.addWidget(self.choose_episode_button)
        
        # Favorite button
        self.series_favorite_button = QPushButton("Add to Favorites")
        self.series_favorite_button.clicked.connect(self._on_series_favorite_clicked)
        buttons_layout.addWidget(self.series_favorite_button)
        
        layout.addLayout(buttons_layout)
        
        # Add widget to stacked widget
        self.stacked_widget.addWidget(self.series_widget)
        
        # Connect signals - we keep these connections even though the list isn't visible
        # in case we need the functionality elsewhere in the code
        self.episodes_list.itemClicked.connect(self._on_episode_clicked)
        self.episodes_list.itemDoubleClicked.connect(self._on_episode_double_clicked)
    
    def _create_episode_info_widget(self):
        """Create widget for episode info"""
        self.episode_widget = QWidget()
        layout = QVBoxLayout(self.episode_widget)
        
        # Episode info
        self.episode_series_label = QLabel()
        self.episode_series_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.episode_series_label)
        
        self.episode_title_label = QLabel()
        self.episode_title_label.setWordWrap(True)
        self.episode_title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.episode_title_label)
        
        # Season and episode
        self.episode_season_episode_label = QLabel()
        layout.addWidget(self.episode_season_episode_label)
        
        # Plot
        self.episode_plot_label = QLabel("Plot")
        self.episode_plot_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        layout.addWidget(self.episode_plot_label)
        
        self.episode_plot = QLabel()
        self.episode_plot.setWordWrap(True)
        layout.addWidget(self.episode_plot)
        
        # Add spacer
        layout.addStretch(1)
        
        # Button row
        button_layout = QHBoxLayout()
        
        # Play button
        self.episode_play_button = QPushButton("Play")
        self.episode_play_button.clicked.connect(self._on_episode_play_clicked)
        button_layout.addWidget(self.episode_play_button)
        
        # Choose Episode button (new)
        self.episode_choose_button = QPushButton("Choose Episode")
        self.episode_choose_button.clicked.connect(self._on_choose_episode_clicked)
        button_layout.addWidget(self.episode_choose_button)
        
        layout.addLayout(button_layout)
        
        # Add widget to stacked widget
        self.stacked_widget.addWidget(self.episode_widget)
    
    def set_content_info(self, content, content_type):
        """Update content info"""
        self.current_content = content
        self.current_type = content_type
        
        if content_type == 'live':
            self._update_live_info(content)
            self.stacked_widget.setCurrentWidget(self.live_widget)
        elif content_type == 'vod':
            self._update_vod_info(content)
            self.stacked_widget.setCurrentWidget(self.vod_widget)
        elif content_type == 'series':
            self._update_series_info(content)
            self.stacked_widget.setCurrentWidget(self.series_widget)
        else:
            self.clear_info()
    
    def show_episode_info(self, episode):
        """Show episode info"""
        # Store the original episode data
        self.current_episode = episode
        
        if not episode:
            return
        
        # Check if episode is a list (error case) instead of a dictionary
        if isinstance(episode, list):
            logger.error(f"Received list instead of episode dict: {episode}")
            # Try to use the first item if it's a non-empty list
            if episode and isinstance(episode[0], dict):
                episode = episode[0]
            else:
                self.episode_title_label.setText("Error: Invalid episode data")
                self.episode_plot.setText("Could not load episode information correctly.")
                self.stacked_widget.setCurrentWidget(self.episode_widget)
                return
            
        # Update episode info
        self.episode_series_label.setText(episode.get('series_name', 'Unknown Series'))
        
        # Set title
        title = episode.get('title', episode.get('name', 'Unknown Episode'))
        self.episode_title_label.setText(title)
        
        # Set season and episode with improved number detection
        season = episode.get('season', '?')
        
        # Try multiple possible field names for episode number
        episode_num = episode.get('episode', episode.get('episode_number', episode.get('episodeNumber', '?')))
        
        # If we still don't have a number, check if episode number is embedded in the title
        if episode_num == '?':
            # Try to extract from titles like "S01E02 - Episode Name"
            title_text = episode.get('title', episode.get('name', ''))
            import re
            match = re.search(r'E(\d+)', title_text)
            if match:
                episode_num = match.group(1)
        
        self.episode_season_episode_label.setText(f"Season {season}, Episode {episode_num}")
        
        # Set plot with improved description detection - with proper type checking
        plot = None
        
        # Try to get plot from various potential locations with type safety
        if isinstance(episode.get('plot'), str):
            plot = episode.get('plot')
        elif isinstance(episode.get('description'), str):
            plot = episode.get('description')
        elif isinstance(episode.get('overview'), str):
            plot = episode.get('overview')
        elif isinstance(episode.get('synopsis'), str):
            plot = episode.get('synopsis')
        elif isinstance(episode.get('info'), dict):
            info = episode.get('info')
            if isinstance(info.get('plot'), str):
                plot = info.get('plot')
            elif isinstance(info.get('description'), str):
                plot = info.get('description')
            elif isinstance(info.get('overview'), str):
                plot = info.get('overview')
        
        # If the plot field exists but is empty or we couldn't find one, try other approaches
        if not plot:
            # Check if there's a container_extension field - if so, this might be missing plot data
            if episode.get('container_extension') and title:
                # Try to create a simple plot from title
                plot = f"Episode {episode_num} of Season {season}: {title}"
            else:
                # Default message if we couldn't find any description
                plot = "No description available for this episode."
        
        self.episode_plot.setText(plot)
        
        # Show episode widget
        self.stacked_widget.setCurrentWidget(self.episode_widget)
    
    def get_current_episode(self):
        """Get current episode if any"""
        if self.stacked_widget.currentWidget() == self.episode_widget:
            return self.current_episode
        return None
    
    def clear_info(self):
        """Clear info panel"""
        self.current_content = None
        self.current_type = ""
        self.current_episode = None
        self.stacked_widget.setCurrentWidget(self.empty_widget)
    
    def _update_live_info(self, channel):
        """Update live channel info"""
        # Set channel name
        name = channel.get('name', 'Unknown Channel')
        self.live_title_label.setText(name)
        
        # EPG data
        has_epg = False
        
        # Current program
        if 'current_program' in channel:
            current = channel['current_program']
            self.current_program_title.setText(current.get('title', 'Unknown'))
            self.current_program_time.setText(f"{current.get('start_time', '')} - {current.get('end_time', '')} ({current.get('duration', '')})")
            self.current_program_desc.setText(current.get('description', 'No description available'))
            self.current_program_group.show()
            has_epg = True
        else:
            self.current_program_group.hide()
        
        # Next program
        if 'next_program' in channel:
            next_prog = channel['next_program']
            self.next_program_title.setText(next_prog.get('title', 'Unknown'))
            self.next_program_time.setText(f"{next_prog.get('start_time', '')} - {next_prog.get('end_time', '')} ({next_prog.get('duration', '')})")
            self.next_program_group.show()
            has_epg = True
        else:
            self.next_program_group.hide()
        
        # EPG list
        self.epg_list.clear()
        
        if 'epg_list' in channel and channel['epg_list']:
            epg_list = channel['epg_list']
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
            self.epg_label.show()
            self.epg_list.show()
            has_epg = True
        else:
            self.epg_label.hide()
            self.epg_list.hide()
        
        # If no EPG, show a message
        if not has_epg:
            self.current_program_group.show()
            self.current_program_title.setText("No EPG data available")
            self.current_program_time.setText("")
            self.current_program_desc.setText("")
            
        # Update favorite button text based on if the channel is a favorite
        is_favorite = channel.get('is_favorite', False)
        if is_favorite:
            self.live_favorite_button.setText("Remove from Favorites")
        else:
            self.live_favorite_button.setText("Add to Favorites")
    
    def _update_vod_info(self, movie):
        """Update movie info"""
        # Set title
        title = movie.get('title', movie.get('name', 'Unknown Movie'))
        self.vod_title_label.setText(title)
        
        # Year and genre
        year = movie.get('year', '')
        genre = movie.get('genre', '')
        if year and genre:
            self.vod_year_genre_label.setText(f"{year} | {genre}")
        elif year:
            self.vod_year_genre_label.setText(year)
        elif genre:
            self.vod_year_genre_label.setText(genre)
        else:
            self.vod_year_genre_label.setText("")
        
        # Rating and duration
        rating = movie.get('rating', '')
        duration = movie.get('duration', '')
        if rating and duration:
            self.vod_rating_duration_label.setText(f"Rating: {rating} | Duration: {duration}")
        elif rating:
            self.vod_rating_duration_label.setText(f"Rating: {rating}")
        elif duration:
            self.vod_rating_duration_label.setText(f"Duration: {duration}")
        else:
            self.vod_rating_duration_label.setText("")
        
        # Director
        director = movie.get('director', '')
        if director:
            self.vod_director_label.setText(f"Director: {director}")
            self.vod_director_label.show()
        else:
            self.vod_director_label.hide()
        
        # Cast
        cast = movie.get('cast', '')
        if cast:
            self.vod_cast_label.setText(f"Cast: {cast}")
            self.vod_cast_label.show()
        else:
            self.vod_cast_label.hide()
        
        # Plot
        plot = movie.get('plot', movie.get('description', 'No description available'))
        self.vod_plot.setText(plot)
        
        # Update favorite button text based on if the movie is a favorite
        is_favorite = movie.get('is_favorite', False)
        if is_favorite:
            self.vod_favorite_button.setText("Remove from Favorites")
        else:
            self.vod_favorite_button.setText("Add to Favorites")
    
    def _update_series_info(self, series):
        """Update series info"""
        # Set title
        title = series.get('title', series.get('name', 'Unknown Series'))
        self.series_title_label.setText(title)
        
        # Genre
        genre = series.get('genre', '')
        if genre:
            self.series_genre_label.setText(f"Genre: {genre}")
            self.series_genre_label.show()
        else:
            self.series_genre_label.hide()
        
        # Rating
        rating = series.get('rating', '')
        if rating:
            self.series_rating_label.setText(f"Rating: {rating}")
            self.series_rating_label.show()
        else:
            self.series_rating_label.hide()
        
        # Director
        director = series.get('director', '')
        if director:
            self.series_director_label.setText(f"Director: {director}")
            self.series_director_label.show()
        else:
            self.series_director_label.hide()
        
        # Cast
        cast = series.get('cast', '')
        if cast:
            self.series_cast_label.setText(f"Cast: {cast}")
            self.series_cast_label.show()
        else:
            self.series_cast_label.hide()
        
        # Plot
        plot = series.get('plot', series.get('description', 'No description available'))
        self.series_plot.setText(plot)
        
        # Episodes - still update the episodes list even though it's not displayed
        # This ensures the choose episode dialog will have the data
        self.episodes_list.clear()
        
        episodes = series.get('episodes', [])
        if episodes:
            # Group episodes by season
            seasons = {}
            for episode in episodes:
                season = episode.get('season', 1)
                if season not in seasons:
                    seasons[season] = []
                seasons[season].append(episode)
            
            # Add episodes to list
            for season in sorted(seasons.keys()):
                # Add season header
                season_header = QListWidgetItem(f"Season {season}")
                season_header.setBackground(QColor(40, 40, 50))
                font = season_header.font()
                font.setBold(True)
                season_header.setFont(font)
                self.episodes_list.addItem(season_header)
                
                # Add episodes with proper numbering
                for episode in sorted(seasons[season], key=lambda x: int(x.get('episode', x.get('episode_number', 1)))):
                    # Try multiple possible field names for episode number
                    episode_num = episode.get('episode', episode.get('episode_number', episode.get('episodeNumber', '')))
                    
                    # If we still don't have a number, check if episode number is embedded in the title
                    if not episode_num:
                        # Try to extract from titles like "S01E02 - Episode Name"
                        title = episode.get('title', episode.get('name', ''))
                        import re
                        match = re.search(r'E(\d+)', title)
                        if match:
                            episode_num = match.group(1)
                    
                    # If we still have no episode number, use a counter based on position
                    if not episode_num:
                        # Just use the count within this season (starting at 1)
                        episode_num = str(seasons[season].index(episode) + 1)
                    
                    # Make sure episode_num is a string
                    episode_num = str(episode_num)
                    
                    title = episode.get('title', episode.get('name', 'Unknown'))
                    display_text = f"E{episode_num}: {title}"
                    
                    # Store the episode data in the item
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, episode)
                    self.episodes_list.addItem(item)
        
        # Update favorite button
        is_favorite = series.get('is_favorite', False)
        if is_favorite:
            self.series_favorite_button.setText("Remove from Favorites")
        else:
            self.series_favorite_button.setText("Add to Favorites")
    
    def _on_live_play_clicked(self):
        """Handle live play button click"""
        if self.current_content and self.current_type == 'live':
            self.content_play_requested.emit(self.current_content)
    
    def _on_vod_play_clicked(self):
        """Handle VOD play button click"""
        if self.current_content and self.current_type == 'vod':
            self.content_play_requested.emit(self.current_content)
    
    def _on_series_favorite_clicked(self):
        """Handle series favorite button click"""
        if self.current_content and self.current_type == 'series':
            self.series_favorite_toggled.emit(self.current_content)
            
    def _on_live_favorite_clicked(self):
        """Handle live favorite button click"""
        if self.current_content and self.current_type == 'live':
            self.live_favorite_toggled.emit(self.current_content)
            
    def _on_vod_favorite_clicked(self):
        """Handle VOD favorite button click"""
        if self.current_content and self.current_type == 'vod':
            self.vod_favorite_toggled.emit(self.current_content)
            
    def _on_choose_episode_clicked(self):
        """Handle choose episode button click"""
        # Show episode selection dialog
        if self.current_content and self.current_type == 'series':
            # Get episodes from current series
            episodes = self.current_content.get('episodes', [])
            series_title = self.current_content.get('title', self.current_content.get('name', 'Unknown Series'))
            
            # Create and show dialog
            dialog = EpisodeSelectionDialog(self, episodes, series_title)
            if dialog.exec_() == QDialog.Accepted:
                selected_episode = dialog.get_selected_episode()
                if selected_episode:
                    # Add series name to episode data for reference
                    selected_episode['series_name'] = series_title
                    # Show the selected episode info
                    self.episode_selected.emit(selected_episode)
        elif self.current_episode:
            # We're in episode view - get the associated series
            if self.current_type == 'series':
                # Get episodes from current series
                episodes = self.current_content.get('episodes', [])
                series_title = self.current_content.get('title', self.current_content.get('name', 'Unknown Series'))
                
                # Create and show dialog
                dialog = EpisodeSelectionDialog(self, episodes, series_title)
                if dialog.exec_() == QDialog.Accepted:
                    selected_episode = dialog.get_selected_episode()
                    if selected_episode:
                        # Add series name to episode data for reference
                        selected_episode['series_name'] = series_title
                        # Show the selected episode info
                        self.episode_selected.emit(selected_episode)
    
    def _on_episode_clicked(self, item):
        """Handle episode selection"""
        if self.current_content and self.current_type == 'series':
            # Check if this is a season header
            text = item.text()
            if text.startswith("Season "):
                return
                
            # Get the episode data directly from the item
            episode = item.data(Qt.UserRole)
            if episode:
                self.episode_selected.emit(episode)
    
    def _on_episode_double_clicked(self, item):
        """Handle episode double-click (play)"""
        if self.current_content and self.current_type == 'series':
            # Check if this is a season header
            text = item.text()
            if text.startswith("Season "):
                return
                
            # Get the episode data directly from the item
            episode = item.data(Qt.UserRole)
            if episode:
                self.episode_selected.emit(episode)
                self.episode_play_requested.emit(episode)
    
    def _on_episode_play_clicked(self):
        """Handle episode play button click"""
        if self.current_episode:
            self.episode_play_requested.emit(self.current_episode)


# UI Manager class for coordinating UI components
class UIManager(QObject):
    """Manages UI interaction and coordination"""
    
    # Signals
    category_updated = pyqtSignal(list)  # For updating category list
    content_updated = pyqtSignal(str, list, list)  # content_type, items, display_names
    info_updated = pyqtSignal(dict, str)  # content, content_type
    
    def __init__(self, main_window):
        super().__init__()
        self.window = main_window
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect UI component signals"""
        # Connect signals from window components
        self.category_updated.connect(self.window.category_panel.set_categories)
        self.content_updated.connect(self.window.content_panel.set_content)
        self.info_updated.connect(self.window.info_panel.set_content_info)
    
    def show_logged_in_ui(self, username):
        """Update UI for logged in state"""
        self.window.show_logged_in_ui(username)
    
    def show_logged_out_ui(self):
        """Update UI for logged out state"""
        self.window.show_logged_out_ui()
        self.window.content_panel.clear_content()
        self.window.info_panel.clear_info()
        self.window.category_panel.set_categories([])
        self.window.show_status_message("Logged out")
    
    def update_categories(self, categories):
        """Update category list in UI"""
        category_names = [cat['category_name'] for cat in categories]
        self.category_updated.emit(category_names)
        
    def update_content(self, content_type, items, display_names):
        """Update content list in UI"""
        self.content_updated.emit(content_type, items, display_names)
        
    def update_info(self, content, content_type):
        """Update info panel in UI"""
        self.info_updated.emit(content, content_type)
    
    def clear_info(self):
        """Clear info panel"""
        self.window.info_panel.clear_info()
    
    def show_status_message(self, message):
        """Show message in status bar"""
        self.window.show_status_message(message)
    
    def show_error_message(self, title, message):
        """Show error message dialog"""
        self.window.show_error_message(title, message)
    
    def show_info_message(self, title, message):
        """Show info message dialog"""
        self.window.show_info_message(title, message)
    
    def select_default_category(self, categories, default_category):
        """Select default category in UI"""
        if not categories:
            return
            
        items = self.window.category_panel.categories_list.findItems(default_category, Qt.MatchExactly)
        if items:
            self.window.category_panel.categories_list.setCurrentItem(items[0])
        else:
            # If default not found, select first category
            self.window.category_panel.categories_list.setCurrentRow(0)