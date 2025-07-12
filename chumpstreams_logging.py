"""
ChumpStreams Logging Configuration

Version: 2.0.6
Author: covchump
Last updated: 2025-01-12 13:26:57

Logging setup for ChumpStreams application
"""
import logging
import sys

def setup_logging(log_file):
    """Setup logging configuration"""
    # Configure basic logging
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('chumpstreams')
    
    # Also log to console for debugging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger