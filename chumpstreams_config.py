"""
ChumpStreams Configuration

Version: 2.0.6
Author: covchump
Last updated: 2025-01-12 13:26:57

Global configuration for ChumpStreams application
"""
import os

# Version
VERSION = "2.0.6"

# Server Configuration - UPDATED TO NEW URL
SERVER = "covchump.visionondemand.xyz"
USE_HTTPS = True

# Default Categories
DEFAULT_CATEGORIES = {
    "live": "UK | Entertainment",
    "vod": "Hot Right Now", 
    "series": "Top 30 IMDB"
}

# Paths
APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")
CFG_DIR = os.path.join(APPDATA, "ChumpStreams")
LOG_FILE = os.path.join(CFG_DIR, "chumpstreams.log")
CONFIG_FILE = os.path.join(CFG_DIR, "xtream_config.json")

# Ensure directories exist
os.makedirs(CFG_DIR, exist_ok=True)