"""
ChumpStreams Player Module

Version: 1.9.5
Author: covchump
Last updated: 2025-05-23 15:10:00

Module for handling VLC player integration
"""
import os
import sys
import logging
import subprocess
import threading
import time
import signal
import psutil
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# Configure logging
logger = logging.getLogger('chumpstreams')

class QtVlcPlayer(QObject):
    """VLC player for ChumpStreams"""
    
    # Signals
    player_started = pyqtSignal()
    player_exited = pyqtSignal(int, str)  # exit_code, stderr
    
    def __init__(self):
        """Initialize VLC player"""
        super().__init__()
        
        # VLC process
        self.process = None
        self.output_reader = None
        self.vlc_path = None
        
        # Attempt to find VLC
        self.vlc_path = self.find_vlc()
        logger.info(f"VLC path: {self.vlc_path}")
    
    def find_vlc(self):
        """Find VLC executable"""
        # Check common locations
        vlc_paths = []
        
        # Windows paths
        if sys.platform == 'win32':
            # Common program files locations
            program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
            program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
            
            vlc_paths = [
                os.path.join(program_files, 'VideoLAN', 'VLC', 'vlc.exe'),
                os.path.join(program_files_x86, 'VideoLAN', 'VLC', 'vlc.exe'),
                os.path.join(program_files, 'VLC', 'vlc.exe'),
                os.path.join(program_files_x86, 'VLC', 'vlc.exe'),
                # Common portable locations
                os.path.join(os.path.dirname(sys.executable), 'VLC', 'vlc.exe'),
                os.path.join(os.path.dirname(sys.executable), 'portable_apps', 'VLC', 'vlc.exe')
            ]
        
        # macOS paths
        elif sys.platform == 'darwin':
            vlc_paths = [
                '/Applications/VLC.app/Contents/MacOS/VLC',
                os.path.expanduser('~/Applications/VLC.app/Contents/MacOS/VLC')
            ]
        
        # Linux paths
        else:
            vlc_paths = [
                '/usr/bin/vlc',
                '/usr/local/bin/vlc',
                '/snap/bin/vlc'
            ]
        
        # Try to find VLC in each path
        for path in vlc_paths:
            if os.path.exists(path) and os.path.isfile(path):
                logger.info(f"Found VLC at: {path}")
                return path
        
        # If not found, try to use 'vlc' command
        try:
            subprocess.run(['vlc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            logger.info("Found VLC in system PATH")
            return 'vlc'
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("VLC not found in system PATH")
        
        # VLC not found
        logger.error("VLC not found in any common locations")
        return None
    
    def play(self, url, content_type, title, buffer_settings, simple_mode=False):
        """Play content with VLC"""
        logger.info(f"Play request: {content_type} - {title}")
        logger.info(f"Using buffer settings: {buffer_settings}")
        
        # Make sure we don't start multiple players
        self.close()
        
        # Get path to VLC executable
        vlc_path = self.find_vlc()
        if not vlc_path:
            logger.error("VLC not found")
            return False
        
        # Create command
        cmd = [vlc_path]
        
        # Start with splash screen minimized, then go to fullscreen for playback
        cmd.append("--qt-start-minimized")  # Start Qt interface minimized
        cmd.append("--started-from-file")   # Behave as if started by opening a file
        cmd.append("--fullscreen")          # Go to fullscreen when playing starts
        
        # Prevent all VLC notifications and overlays
        cmd.append("--no-video-title-show")  # Disable the video title overlay
        cmd.append("--quiet")                # Suppress information messages
        cmd.append("--no-osd")               # Disable On-Screen Display completely
        cmd.append("--no-interact")          # Disable user interface interaction
        cmd.append("--qt-notification=0")    # Explicitly disable Qt notifications
        cmd.append("--no-snapshot-preview")  # Disable snapshot preview popups
        cmd.append("--no-one-instance")      # Avoid triggering notifs from existing instances
        
        # Add title parameter to display the content name in VLC's title bar
        if title:
            # Use proper quoting for the title to handle special characters
            cmd.append("--meta-title")
            cmd.append(title)
        
        # Add auto-exit options to ensure VLC closes when stream ends or is stopped
        cmd.append("--play-and-exit")  # Exit VLC when the playlist ends
        cmd.append("--no-repeat")      # Don't repeat playback
        cmd.append("--no-loop")        # Don't loop playback
        
        # Add buffer argument based on content type
        if content_type == 'live':
            buffer_ms = buffer_settings.get('live', 5000)
            cmd.append(f"--network-caching={buffer_ms}")
            logger.info(f"Using live buffer: {buffer_ms}ms")
        elif content_type == 'vod':
            buffer_ms = buffer_settings.get('vod', 10000)
            cmd.append(f"--network-caching={buffer_ms}")
            logger.info(f"Using VOD buffer: {buffer_ms}ms")
        else:
            buffer_ms = buffer_settings.get('network', 3000)
            cmd.append(f"--network-caching={buffer_ms}")
            logger.info(f"Using default buffer: {buffer_ms}ms")
        
        # Simple mode (reduced UI)
        if simple_mode:
            cmd.append("--qt-minimal-view")
            logger.info("Using simple mode (minimal view)")
        
        # Add URL
        cmd.append(url)
        
        # Convert url for logging to prevent sensitive data exposure
        safe_url = url[:30] + "..." if len(url) > 30 else url
        logger.info(f"VLC command: {' '.join(cmd[:5])} [URL REDACTED]")
        
        try:
            # Start process
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("VLC process started with minimized splash and fullscreen playback for: " + title)
            
            # Start thread to monitor process output
            self.output_reader = threading.Thread(target=self._read_process_output)
            self.output_reader.daemon = True
            self.output_reader.start()
            
            # Emit signal
            self.player_started.emit()
            
            return True
        except Exception as e:
            logger.error(f"Error starting VLC: {str(e)}")
            return False
    
    def _read_process_output(self):
        """Read and log process output"""
        if not self.process:
            return
            
        # Read stderr
        stderr_lines = []
        for line in iter(self.process.stderr.readline, b''):
            stderr_line = line.decode('utf-8', errors='replace').strip()
            stderr_lines.append(stderr_line)
            # Only log if not empty
            if stderr_line:
                logger.debug(f"VLC stderr: {stderr_line}")
        
        # Wait for process to exit
        exit_code = self.process.wait()
        logger.info(f"VLC process exited with code: {exit_code}")
        
        # Emit signal with exit code and stderr
        stderr_text = '\n'.join(stderr_lines)
        self.player_exited.emit(exit_code, stderr_text)
    
    def close(self, force=False):
        """Close VLC player"""
        if not self.process:
            return
            
        logger.info("Closing VLC player")
        
        try:
            # Try graceful shutdown first
            if sys.platform == 'win32':
                # Windows requires different approach
                self.process.terminate()
            else:
                # Send SIGTERM
                self.process.terminate()
                
            # Wait for process to exit
            if force:
                # Force kill after 1 second
                for _ in range(10):
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.1)
                
                if self.process.poll() is None:
                    logger.info("Forcing VLC to close")
                    self.process.kill()
            else:
                # Wait for process to exit (up to 3 seconds)
                for _ in range(30):
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.1)
            
            logger.info("VLC player closed")
        except Exception as e:
            logger.error(f"Error closing VLC: {str(e)}")
        
        # Clear process
        self.process = None
    
    def kill_all_vlc_processes(self):
        """Kill all VLC processes"""
        killed_count = 0
        
        try:
            # Use psutil to find and kill VLC processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Check if it's a VLC process
                    if 'vlc' in proc.info['name'].lower():
                        logger.info(f"Killing VLC process: {proc.info['pid']}")
                        # Kill process
                        proc.kill()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            logger.error(f"Error killing VLC processes: {str(e)}")
        
        logger.info(f"Killed {killed_count} VLC processes")
        return killed_count