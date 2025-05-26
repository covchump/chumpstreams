"""
ChumpStreams EPG Module

Version: 1.9.3-custom-mapping
Author: covchump, Copilot
Created: 2025-05-21 12:40:09
Last updated: 2025-05-25 20:35:14

Module for handling Electronic Program Guide (EPG) data with user-provided channel mapping support
"""
import requests
import logging
import time
import xml.etree.ElementTree as ET
import os
import json
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger('chumpstreams')

def get_channel_mapping_path():
    """Get the path to the user-specific channel mapping JSON file."""
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    cache_dir = os.path.join(appdata, "ChumpStreams", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "channel_mappings.json")

class EPGManager:
    """Manager for handling Electronic Program Guide data, with channel mapping override"""

    def __init__(self, base_url, use_https=True):
        """Initialize EPG Manager"""
        # Ensure base_url doesn't include protocol
        if base_url.startswith('http://') or base_url.startswith('https://'):
            base_url = base_url.split('://')[-1]

        protocol = 'https' if use_https else 'http'
        self.base_url = f"{protocol}://{base_url}"
        logger.info(f"EPG Manager initialized with base URL: {self.base_url}")

        self.epg_cache = {}
        self.epg_cache_time = 0
        self.epg_cache_duration = 3600  # In-memory cache for 1 hour
        self.file_cache_duration = 86400  # File cache for 24 hours (in seconds)
        self.channels = {}
        self.programs = {}

        # Set up cache file path
        self.cache_dir = self._get_cache_dir()
        self.cache_file = os.path.join(self.cache_dir, "epg_cache.json")
        logger.info(f"EPG cache file: {self.cache_file}")

        # Load channel mapping override
        self._load_channel_mappings()

    def _get_cache_dir(self):
        """Get cache directory path"""
        # Use the same config directory as the main application
        appdata = os.getenv("APPDATA") or os.path.expanduser("~")
        cache_dir = os.path.join(appdata, "ChumpStreams", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    def _save_epg_to_cache_file(self, epg_data):
        """Save EPG data to a cache file"""
        try:
            cache_data = {
                "timestamp": time.time(),
                "epg_data": epg_data
            }

            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)

            logger.info(f"EPG data saved to cache file")
            return True
        except Exception as e:
            logger.error(f"Failed to save EPG data to cache file: {str(e)}")
            return False

    def _load_epg_from_cache_file(self):
        """Load EPG data from cache file if it exists and is valid"""
        if not os.path.exists(self.cache_file):
            logger.info("No EPG cache file found")
            return None

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            timestamp = cache_data.get("timestamp", 0)
            current_time = time.time()

            # Check if cache is still valid (less than 24 hours old)
            if current_time - timestamp < self.file_cache_duration:
                logger.info(f"Using EPG data from cache file (age: {(current_time - timestamp) / 3600:.1f} hours)")

                # Load the cached data into our data structures
                epg_data = cache_data.get("epg_data", {})
                self.channels = epg_data.get("channels", {})
                self.programs = epg_data.get("programs", {})

                # Also update the in-memory cache
                self.epg_cache = epg_data
                self.epg_cache_time = time.time()

                return epg_data
            else:
                logger.info(f"EPG cache file is too old ({(current_time - timestamp) / 3600:.1f} hours), fetching new data")
                return None
        except Exception as e:
            logger.error(f"Failed to load EPG data from cache file: {str(e)}")
            return None

    def fetch_epg_data(self, username, password, force_refresh=False):
        """Fetch EPG data from the XMLTV endpoint or load from cache"""
        # Check if force refresh is requested
        if force_refresh:
            logger.info("Force refresh requested for EPG data")
            return self._fetch_epg_from_server(username, password)

        # First check if we have valid in-memory cache
        current_time = time.time()
        if self.epg_cache and (current_time - self.epg_cache_time) < self.epg_cache_duration:
            logger.info("Using in-memory EPG cache")
            return self.epg_cache

        # Then check if we have a valid cache file
        cached_data = self._load_epg_from_cache_file()
        if cached_data:
            return cached_data

        # If no valid cache, fetch from server
        return self._fetch_epg_from_server(username, password)

    def _fetch_epg_from_server(self, username, password):
        """Fetch EPG data from the server"""
        if not username or not password:
            logger.error("Cannot fetch EPG: Missing credentials")
            return {}

        url = f"{self.base_url}/xmltv.php"
        params = {
            'username': username,
            'password': password
        }

        try:
            logger.info(f"Fetching XMLTV EPG data from {url}...")
            response = requests.get(url, params=params)

            if response.status_code != 200:
                logger.error(f"XMLTV EPG request failed with status code: {response.status_code}")
                return {}

            # Check if response looks like XML (should start with <?xml)
            if not response.text.strip().startswith('<?xml'):
                logger.error("Response from XMLTV endpoint is not valid XML")
                logger.debug(f"Response preview: {response.text[:200]}...")

                # Check if the response is a text list of channels
                if len(response.text) > 0 and not response.text.startswith('{'):
                    logger.info("Response appears to be a plain text list of channels")
                    # Parse the text list into a simple EPG structure
                    epg_data = self._parse_channel_list(response.text)

                    # Save to cache file
                    self._save_epg_to_cache_file(epg_data)

                    return epg_data

                return {}

            # Parse XML
            epg_data = self._parse_xmltv(response.text)

            # Save to cache file
            self._save_epg_to_cache_file(epg_data)

            return epg_data

        except Exception as e:
            logger.error(f"Failed to fetch EPG data: {str(e)}")
            return {}

    def _parse_xmltv(self, xml_data):
        """Parse XMLTV formatted data"""
        try:
            root = ET.fromstring(xml_data)

            # Process channels and programs
            channels = {}
            programs = {}

            # Parse channels
            for channel in root.findall(".//channel"):
                channel_id = channel.get('id')
                display_name = channel.findtext('.//display-name')
                icon_url = channel.find('.//icon')
                icon = icon_url.get('src') if icon_url is not None else None

                channels[channel_id] = {
                    'id': channel_id,
                    'name': display_name,
                    'icon': icon
                }
                programs[channel_id] = []

            # Parse programs
            for program in root.findall(".//programme"):
                channel_id = program.get('channel')
                start_time = self._parse_xmltv_time(program.get('start'))
                stop_time = self._parse_xmltv_time(program.get('stop'))
                title = program.findtext('.//title')
                desc = program.findtext('.//desc')
                category = program.findtext('.//category')

                if channel_id in programs:
                    programs[channel_id].append({
                        'start': start_time,
                        'start_timestamp': int(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp()) if start_time else 0,
                        'stop': stop_time,
                        'stop_timestamp': int(datetime.strptime(stop_time, "%Y-%m-%d %H:%M:%S").timestamp()) if stop_time else 0,
                        'title': title,
                        'description': desc,
                        'category': category
                    })

            # Sort programs by start time for each channel
            for channel_id in programs:
                programs[channel_id].sort(key=lambda x: x['start_timestamp'])

            # Store channels and programs
            self.channels = channels
            self.programs = programs

            # Create result
            result = {
                'channels': channels,
                'programs': programs
            }

            # Cache the result
            self.epg_cache = result
            self.epg_cache_time = time.time()

            logger.info(f"Successfully parsed XMLTV EPG data with {len(channels)} channels")
            return result

        except ET.ParseError as e:
            logger.error(f"Failed to parse XMLTV data: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error processing XMLTV data: {str(e)}")
            return {}

    def _parse_channel_list(self, text_data):
        """Parse a plain text list of channels (fallback)"""
        try:
            # Split the text by whitespace
            channel_names = text_data.strip().split()

            # Create simple channel and program structures
            channels = {}
            programs = {}

            for i, name in enumerate(channel_names):
                # Generate a simple channel ID
                channel_id = f"channel-{i+1}"

                # Store channel info
                channels[channel_id] = {
                    'id': channel_id,
                    'name': name,
                    'icon': None
                }

                # Create empty program list for this channel
                programs[channel_id] = []

            # Create result
            result = {
                'channels': channels,
                'programs': programs
            }

            # Cache the result
            self.channels = channels
            self.programs = programs
            self.epg_cache = result
            self.epg_cache_time = time.time()

            logger.info(f"Parsed text list of {len(channels)} channels")
            return result

        except Exception as e:
            logger.error(f"Error processing channel list: {str(e)}")
            return {}

    def _parse_xmltv_time(self, time_str):
        """Parse XMLTV time format (YYYYMMDDHHMMSS +0000) to datetime string"""
        if not time_str:
            return ""

        try:
            # Extract the time part without timezone
            time_part = time_str[:14]
            # Parse to datetime
            dt = datetime.strptime(time_part, "%Y%m%d%H%M%S")
            # Format to string
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Failed to parse XMLTV time '{time_str}': {str(e)}")
            return time_str

    def get_channel_epg(self, epg_channel_id, hours=12):
        """Get EPG data for a specific channel for a specified number of hours"""
        if not epg_channel_id:
            logger.error("No EPG channel ID provided")
            return []

        # Check if we have data for this channel
        if epg_channel_id not in self.programs:
            logger.error(f"No EPG data found for channel ID {epg_channel_id}")
            return []

        # Get programs for this channel
        channel_programs = self.programs.get(epg_channel_id, [])

        # Filter programs to include only those within the specified time window
        now = datetime.now()
        end_time = now + timedelta(hours=hours)
        now_timestamp = int(now.timestamp())
        end_timestamp = int(end_time.timestamp())

        filtered_programs = [
            prog for prog in channel_programs
            if prog['start_timestamp'] <= end_timestamp and prog['stop_timestamp'] >= now_timestamp
        ]

        return filtered_programs

    def _load_channel_mappings(self):
        """Load user-provided channel mapping from JSON file (if available)"""
        mapping_path = get_channel_mapping_path()
        self.channel_mappings = {}
        if os.path.exists(mapping_path):
            try:
                with open(mapping_path, "r", encoding="utf-8") as f:
                    self.channel_mappings = json.load(f)
                logger.info(f"Loaded channel mappings from {mapping_path}")
            except Exception as e:
                logger.error(f"Error loading channel mappings: {e}")
                self.channel_mappings = {}

    def reload_channel_mappings(self):
        """Public method to reload channel mappings at runtime"""
        self._load_channel_mappings()

    def map_stream_to_epg(self, stream_name):
        """Map a stream name to an EPG channel ID with custom mapping (if available)"""
        if not stream_name:
            logger.debug(f"Cannot map empty stream name to EPG")
            return None

        # 1. Try the user-provided mapping first
        mapping = getattr(self, 'channel_mappings', {})
        if mapping and stream_name in mapping:
            mapped_id = mapping[stream_name]
            logger.info(f"EPG mapping override: '{stream_name}' -> '{mapped_id}' from channel_mappings.json")
            return mapped_id

        # 2. Fallback to existing logic (original matching code)
        logger.debug(f"Attempting to map stream '{stream_name}' to EPG channel")

        # Try direct match first
        for channel_id, channel in self.channels.items():
            channel_name = channel.get('name', '')
            if channel_name and channel_name.lower() == stream_name.lower():
                logger.debug(f"Found exact match for '{stream_name}': {channel_id}")
                return channel_id

        # Try partial match with more flexible approach
        stream_name_clean = stream_name.lower()

        # Remove common prefixes/suffixes that might cause mismatch
        prefixes_to_remove = ['uk ', 'us ', 'hd ', 'fhd ', 'uhd ', '4k ']
        for prefix in prefixes_to_remove:
            if stream_name_clean.startswith(prefix):
                stream_name_clean = stream_name_clean[len(prefix):]

        suffixes_to_remove = [' hd', ' fhd', ' uhd', ' 4k', ' tv', ' channel']
        for suffix in suffixes_to_remove:
            if stream_name_clean.endswith(suffix):
                stream_name_clean = stream_name_clean[:-len(suffix)]

        # Try matching with the cleaned name
        best_match = None
        best_match_score = 0

        for channel_id, channel in self.channels.items():
            channel_name = channel.get('name', '').lower()

            # Clean the channel name the same way
            channel_name_clean = channel_name
            for prefix in prefixes_to_remove:
                if channel_name_clean.startswith(prefix):
                    channel_name_clean = channel_name_clean[len(prefix):]

            for suffix in suffixes_to_remove:
                if channel_name_clean.endswith(suffix):
                    channel_name_clean = channel_name_clean[:-len(suffix)]

            # Check if the cleaned names match
            if stream_name_clean == channel_name_clean:
                logger.debug(f"Found match for cleaned name '{stream_name_clean}': {channel_id}")
                return channel_id

            # Check for partial matches
            if stream_name_clean in channel_name_clean or channel_name_clean in stream_name_clean:
                # Calculate a simple match score based on common characters
                common_chars = sum(1 for c in stream_name_clean if c in channel_name_clean)
                score = common_chars / max(len(stream_name_clean), len(channel_name_clean))

                if score > best_match_score and score > 0.5:  # Require at least 50% similarity
                    best_match_score = score
                    best_match = channel_id

        if best_match:
            logger.debug(f"Found partial match for '{stream_name}': {best_match} (score: {best_match_score:.2f})")
            return best_match

        logger.debug(f"No EPG match found for stream '{stream_name}'")
        return None

    def get_current_program(self, epg_channel_id):
        """Get the currently airing program for a channel"""
        if not epg_channel_id:
            return None

        programs = self.get_channel_epg(epg_channel_id, hours=1)
        if not programs:
            return None

        now_timestamp = int(datetime.now().timestamp())

        # Find the program that's currently airing
        for prog in programs:
            if prog['start_timestamp'] <= now_timestamp and prog['stop_timestamp'] >= now_timestamp:
                return prog

        return None

    def get_next_program(self, epg_channel_id):
        """Get the next program for a channel"""
        if not epg_channel_id:
            return None

        programs = self.get_channel_epg(epg_channel_id, hours=12)
        if not programs:
            return None

        now_timestamp = int(datetime.now().timestamp())

        # Find the next program
        for prog in programs:
            if prog['start_timestamp'] > now_timestamp:
                return prog

        return None

    def format_epg_time(self, timestamp, format_str="%H:%M"):
        """Format a timestamp for display"""
        if not timestamp:
            return ""

        try:
            return datetime.fromtimestamp(timestamp).strftime(format_str)
        except Exception as e:
            logger.error(f"Error formatting time: {str(e)}")
            return ""

    def get_formatted_epg_for_channel(self, epg_channel_id, hours=12):
        """Get formatted EPG data for a channel suitable for UI display"""
        programs = self.get_channel_epg(epg_channel_id, hours)

        formatted_programs = []
        for prog in programs:
            formatted_programs.append({
                'time': self.format_epg_time(prog['start_timestamp']),
                'end_time': self.format_epg_time(prog['stop_timestamp']),
                'title': prog['title'],
                'description': prog['description'],
                'category': prog['category'],
                'duration': self._format_duration(prog['start_timestamp'], prog['stop_timestamp']),
                'is_current': self._is_current_program(prog)
            })

        return formatted_programs

    def _format_duration(self, start_timestamp, stop_timestamp):
        """Format the duration of a program"""
        if not start_timestamp or not stop_timestamp:
            return ""

        try:
            duration_seconds = stop_timestamp - start_timestamp
            minutes = duration_seconds // 60
            hours = minutes // 60
            minutes = minutes % 60

            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception as e:
            logger.error(f"Error calculating duration: {str(e)}")
            return ""

    def _is_current_program(self, program):
        """Check if a program is currently airing"""
        if not program:
            return False

        now_timestamp = int(datetime.now().timestamp())
        return (program['start_timestamp'] <= now_timestamp and
                program['stop_timestamp'] >= now_timestamp)

    def clear_cache(self):
        """Clear both memory and file cache for EPG data"""
        # Clear memory cache
        self.epg_cache = {}
        self.epg_cache_time = 0
        self.channels = {}
        self.programs = {}

        # Delete cache file
        if os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
                logger.info("EPG cache file deleted")
                return True
            except Exception as e:
                logger.error(f"Failed to delete EPG cache file: {str(e)}")
                return False
        return True
