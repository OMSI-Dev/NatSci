"""
SOS LibreOffice Impress Engine with Subtitle Support
Connects to SOS server and controls LibreOffice Impress slides based on clip names.
Includes integrated subtitle parsing and display functionality.
"""

import socket
import time
import os
import subprocess
import tempfile
import sys
import re
from PyQt5.QtWidgets import QApplication
from subtitles import SubtitleManager
from progressOverlay import ProgressOverlay
from metadata_cache import MetadataCache


def recv_data(sock: socket.socket, timeout_idle: float = 1.0) -> bytes:
    """Receive data from socket until idle timeout."""
    buffer = bytearray()
    orig_timeout = sock.gettimeout()
    try:
        sock.settimeout(0.2)
        start = time.time()
        while True:
            try:
                chunk = sock.recv(4096)
                if chunk:
                    buffer.extend(chunk)
                    start = time.time()
                else:
                    break
            except socket.timeout:
                if time.time() - start >= timeout_idle:
                    break
    finally:
        sock.settimeout(orig_timeout)
    return bytes(buffer)


def parse_name_value_pairs(data: str) -> dict:
    """
    This function is called for parsing clip metadata from SOS, fetched by the get_all_name_value_pairs call. 
    """
    result = {}
    pattern = r'(\w+)\s+(?:\{([^}]+)\}|(\S+))'
    
    matches = re.findall(pattern, data)
    for match in matches:
        key = match[0]
        value = match[1] if match[1] else match[2]
        result[key] = value
    return result

class SimplePPEngine:
    """
    Primary engine:
    - Connects to SOS server
    - Slide navigation for LibreOffice based on clip names 
    - Subtitle parsing and display 
    - Progress overlay for clip timing
    - Clip stopwatch timer for debugging
    - Now playing info sending to Raspberry Pi  
    """
    
    def __init__(self, pp, pp_dictionary, sos_ip, sos_port, pi_ip="10.10.51.97", pi_port=4096):
        """
        Initialize the engine.
        
        Args:
            pp: LibreOffice Impress controller object
            pp_dictionary: Dict mapping clip names to slide numbers
            sos_ip: IP address of SOS server
            sos_port: Port number of SOS server
            pi_ip: IP address of Raspberry Pi (optional)
            pi_port: Port number of Raspberry Pi (optional)
        """
        self.pp = pp
        self.pp_dictionary = pp_dictionary
        self.sos_ip = sos_ip
        self.sos_port = sos_port
        self.pi_ip = pi_ip
        self.pi_port = pi_port
        self.running = True
        self.current_slide = -1
        self.sock = None
        
        print("Initializing GUI overlay for progress bar...")
        if not QApplication.instance():
            self.qapp = QApplication(sys.argv)
        else:
            self.qapp = QApplication.instance()
        self.overlay = ProgressOverlay(position='bottom', opacity=0.85)
        
        # Subtitle support - metadata fetched dynamically from SOS
        self.current_clip_metadata = {}
        self.subtitle_manager = SubtitleManager(gui_overlay=self.overlay)
        self.subtitle_enabled = True
        self.subtitle_cache_dir = os.path.join(os.path.dirname(__file__), 'subtitle_cache')
        os.makedirs(self.subtitle_cache_dir, exist_ok=True)
        
        # Metadata cache - minimize server queries
        self.metadata_cache = MetadataCache()
        print(f"[Metadata Cache] Initialized: {self.metadata_cache.get_stats()['total_cached_clips']} clips in cache")
        
        # DEBUGGING : Clip stopwatch timer
        self.clip_start_time = None
        self.clip_real_start_time = None  # Track real elapsed time for progress bar
        
        # Multi-slide navigation support
        self.current_slide_list = []  
        self.current_slide_index = 0  
        self.slide_durations = []   
        self.cached_total_duration = 180.0  
        self.current_playlist_name = None
        self.overlay_shown = False  # Track if overlay has been shown yet
        self.libreoffice_launch_time = None  # Track when LibreOffice was launched
        self.first_clip_loaded = False  # Track if first clip has been loaded (for overlay display)

    def connect_to_sos(self, timeout=4):
        """
        Args:
            timeout: Socket timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            
            print(f"Connecting to SOS at {self.sos_ip}:{self.sos_port}...")
            self.sock.connect((self.sos_ip, self.sos_port))
            print("[Success] Connected to SOS server")
            
            # Send enable handshake
            self.sock.sendall(b'enable\n')
            
            # Wait for response
            data = self.sock.recv(1024)
            response = data.decode('utf-8', 'ignore').strip()
            # print(f"Handshake response: {repr(response)}")
            
            if response == 'R':
                print("[Success] SOS Handshake successful\n")
                return True
            else:
                print(f"! Unexpected handshake response: {response}")
                # Continue anyway - some SOS versions respond differently
                return True
                
        except socket.error as e:
            print(f"✗ Failed to connect to SOS: {e}")
            return False
        except Exception as e:
            print(f"✗ Error during SOS connection: {e}")
            return False
    
    def next_clip(self):
        """
        Skip to the next clip in the playlist.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sock:
            print("! No SOS connection")
            return False
        
        try:
            print("[Command] Next clip")
            self.sock.sendall(b'next_clip\n')
            time.sleep(0.2)
            
            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            return True
            
        except socket.error as e:
            print(f"! Error sending next_clip: {e}")
            return False
        except Exception as e:
            print(f"! Error sending next_clip: {e}")
            return False
    
    def prev_clip(self):
        """
        Go back to the previous clip in the playlist.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sock:
            print("! No SOS connection")
            return False
        
        try:
            print("[Command] Previous clip")
            self.sock.sendall(b'prev_clip\n')
            time.sleep(0.2)
            
            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            return True
            
        except socket.error as e:
            print(f"! Error sending prev_clip: {e}")
            return False
        except Exception as e:
            print(f"! Error sending prev_clip: {e}")
            return False
    
    def restart_current_clip(self):
        """
        This function is used on boot. 
        Restart the currently playing clip by going to previous then next.
        This is a workaround since SOS doesn't have a direct restart command.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sock:
            return False
        
        try:
            print("Restarting current clip...")
            self.sock.sendall(b'prev_clip\n')
            time.sleep(0.2) 

            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            self.sock.sendall(b'next_clip\n')
            time.sleep(0.2)
            
            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            print("[Success] Clip restarted")
            return True
            
        except socket.error as e:
            print(f"! Error restarting clip: {e}")
            return False
        except Exception as e:
            print(f"! Error restarting clip: {e}")
            return False
    
    def get_current_clip_info(self):
        """
        This function gets current clip information from SOS server via get_clip_number and get_clip_info.
        
        Returns:
            tuple: (success, clip_name)
        """
        if not self.sock:
            return (False, "")
        
        try:
            self.sock.sendall(b'get_clip_number\n')
            
            data = self.sock.recv(1024)
            clip_number = data.decode('utf-8', 'ignore').strip()
            
            if not clip_number or not clip_number.isdigit():
                return (False, "")
            
            cmd = f"get_clip_info {clip_number}\n".encode('utf-8')
            self.sock.sendall(cmd)
            
            data = self.sock.recv(2048)
            clip_name = data.decode('utf-8', 'ignore').strip()
            
            return (True, clip_name)
            
        except socket.timeout:
            return (False, "")
        except socket.error as e:
            print(f"Socket error: {e}")
            return (False, "")
        except Exception as e:
            print(f"Error getting clip info: {e}")
            return (False, "")
    
    def fetch_clip_metadata(self, clip_number):
        """
        This function fetches all metadata for a clip from SOS server via get_all_name_value_pairs.
        Uses cache to minimize server queries - only fetches from server if not cached.
        
        Args:
            clip_number: The clip number to fetch metadata for
            
        Returns:
            dict: Parsed metadata dictionary, or empty dict on failure
        """
        if not self.sock:
            return {}
        
        try:
            # First, get clip name using lightweight get_clip_info command
            cmd = f'get_clip_info * {clip_number}\n'.encode('utf-8')
            self.sock.sendall(cmd)
            info_data = recv_data(self.sock, timeout_idle=1.0).decode('utf-8', 'ignore').strip()
            
            # Parse clip name from get_clip_info response (format: "1,clip_name")
            parts = info_data.split(',', 1)
            if len(parts) == 2:
                clip_name = parts[1].strip()
            else:
                clip_name = f'Clip_{clip_number}'
            
            # Check if we have this clip cached
            cached_metadata = self.metadata_cache.get(clip_name)
            if cached_metadata is not None:
                print(f"[Metadata] Using cached metadata for '{clip_name}'")
                # Ensure clip_number is set
                cached_metadata['clip_number'] = clip_number
                return cached_metadata
            
            # Not in cache - fetch full metadata from server
            print(f"[Metadata] Fetching metadata from server for '{clip_name}'...")
            command = f'get_all_name_value_pairs {clip_number}\n'.encode('utf-8')
            self.sock.sendall(command)
            data = recv_data(self.sock, timeout_idle=1.0)
            clip_data = data.decode('utf-8', 'ignore').strip()
            
            # Parse metadata
            clip_metadata = parse_name_value_pairs(clip_data)
            clip_metadata['clip_number'] = clip_number
            
            # Cache the metadata for future use
            self.metadata_cache.set(clip_name, clip_metadata)
            print(f"[Metadata] Cached metadata for '{clip_name}'")
            
            return clip_metadata
            
        except Exception as e:
            print(f"Warning: Could not fetch clip metadata: {e}")
            return {}
    
    def get_frame_number(self):
        """
        This function gets current frame number from SOS server via get_frame_number.
        
        Returns:
            int: Current frame number, or 0 if unavailable
        """
        if not self.sock:
            return 0
        
        try:
            self.sock.sendall(b'get_frame_number\n')
            data = self.sock.recv(1024)
            frame_number = data.decode('utf-8', 'ignore').strip()
            return int(frame_number) if frame_number.isdigit() else 0
        except socket.timeout:
            return 0
        except Exception as e:
            # Only print error once to avoid spam
            if not hasattr(self, '_frame_error_logged'):
                print(f"Warning: Error getting frame number: {e}")
                self._frame_error_logged = True
            return 0
    
    def get_frame_rate(self):
        """
        This function gets frame rate from SOS server.
        
        Returns:
            float: Frame rate in fps, defaults to 30.0
        """
        if not self.sock:
            return 30.0  # Default to 30 fps
        
        try:
            self.sock.sendall(b'get_frame_rate\n')
            data = self.sock.recv(1024)
            frame_rate = data.decode('utf-8', 'ignore').strip()
            
            # SOS sometimes returns "30.000000 0 0" - take first token only
            if frame_rate:
                frame_rate = frame_rate.split()[0]
            
            fps = float(frame_rate) if frame_rate else 30.0
            return fps if fps > 0 else 30.0
        except socket.timeout:
            return 30.0
        except Exception as e:
            # Only print error once to avoid spam
            if not hasattr(self, '_fps_error_logged'):
                print(f"Warning: Error getting frame rate: {e}")
                self._fps_error_logged = True
            return 30.0
    
    def fetch_subtitle_file(self, remote_path):
        """
        This function fetches subtitle file from SOS server via SSH (scp).
        
        Args:
            remote_path: Path to subtitle file on SOS server (e.g., /shared/sos/media/extras/...)
            
        Returns:
            str: Local path to downloaded subtitle file, or None if failed
        """
        if not remote_path:
            return None

        # Generate local filename from remote path
        filename = os.path.basename(remote_path)
        local_path = os.path.join(self.subtitle_cache_dir, filename)

        # Check if already cached
        if os.path.exists(local_path):
            print(f" → Filename: {filename} (cached)")
            return local_path

        # SSH/SCP fetch logic
        ssh_user = "sosdemo"  
        ssh_host = self.sos_ip
        ssh_key = None  #automatic key already setup on B-link

        scp_cmd = [
            "scp",
            "-o", "StrictHostKeyChecking=no",
        ]
        if ssh_key:
            scp_cmd += ["-i", ssh_key]
        scp_cmd += [f"{ssh_user}@{ssh_host}:{remote_path}", local_path]

        print(f"Fetching subtitle file via SSH: {remote_path}")
        try:
            result = subprocess.run(scp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            if result.returncode == 0 and os.path.exists(local_path):
                print(f" → Filename: {filename} (fetched)")
                return local_path
            else:
                print(f"[Subtitles-error] SCP failed: {result.stderr.decode('utf-8', 'ignore')}")
                return None
        except Exception as e:
            print(f"[Subtitles-error] Exception during SCP: {e}")
            return None
    
    def get_slide_numbers(self, clip_name):
        """
        This function maps clip name to slide number(s) from the pp_dictionary.
        
        Args:
            clip_name: Name of the current clip
            
        Returns:
            list: List of slide numbers (defaults to [1] if not found)
        """
        if clip_name.strip() in self.pp_dictionary:
            return self.pp_dictionary[clip_name.strip()]
        return [1]
    
    def get_playlist_name(self):
        """
        This function fetches the current playlist name from SOS server via get_playlist_name.
        Returns:
            str: Playlist name or None if failed
        """
        if not self.sock:
            return None
        try:
            self.sock.sendall(b'get_playlist_name\n')
            data = recv_data(self.sock, timeout_idle=1.0)
            playlist_name = data.decode('utf-8', 'ignore').strip()
            return playlist_name if playlist_name else None
        except Exception as e:
            print(f"Warning: Could not fetch playlist name: {e}")
            return None
    
    def fetch_playlist_metadata(self):
        """
        This function fetches metadata for all clips in the current playlist via get_clip_count and get_all_name_value_pairs.
        Uses intelligent caching to minimize server queries.

        Prints duration/timer for each clip, or triggers duration tracker if missing (unless datadir is a .jpg).
        """
        if not self.sock:
            print("[Playlist Metadata] No SOS connection.")
            return
        try:
            self.sock.sendall(b'get_clip_count\n')
            data = recv_data(self.sock, timeout_idle=2.0)
            clip_count_str = data.decode('utf-8', 'ignore').strip()
            if not clip_count_str.isdigit():
                print(f"[Playlist Metadata] Invalid clip count: {clip_count_str}")
                return
            clip_count = int(clip_count_str)
            print("-" * 50)
            print(f"[Playlist Metadata] Total clips: {clip_count}")
            print("-" * 50)
            
            # First pass: get all clip names to check cache
            print("[Metadata Cache] Checking which clips need to be fetched...")
            clips_to_fetch = []
            clip_names = []
            
            for clip_number in range(1, clip_count + 1):
                # Get clip info to determine name
                cmd = f'get_clip_info * {clip_number}\n'.encode('utf-8')
                self.sock.sendall(cmd)
                info_data = recv_data(self.sock, timeout_idle=1.0).decode('utf-8', 'ignore').strip()
                
                # Parse clip name from get_clip_info response (format: "1,clip_name")
                parts = info_data.split(',', 1)
                if len(parts) == 2:
                    clip_name = parts[1].strip()
                else:
                    clip_name = f"Clip_{clip_number}"
                
                clip_names.append(clip_name)
                
                # Check if cached
                if not self.metadata_cache.has_clip(clip_name):
                    clips_to_fetch.append((clip_number, clip_name))
            
            # Report cache status
            cached_count = clip_count - len(clips_to_fetch)
            print(f"[Metadata Cache] {cached_count} clips in cache, {len(clips_to_fetch)} need fetching")
            
            # Second pass: fetch only uncached clips
            if clips_to_fetch:
                print("[Metadata] Fetching metadata for new clips...")
                for clip_number, clip_name in clips_to_fetch:
                    cmd = f'get_all_name_value_pairs {clip_number}\n'.encode('utf-8')
                    self.sock.sendall(cmd)
                    clip_data = recv_data(self.sock, timeout_idle=2.0).decode('utf-8', 'ignore').strip()
                    metadata = parse_name_value_pairs(clip_data)
                    metadata['clip_number'] = clip_number
                    
                    # Cache the metadata
                    self.metadata_cache.set(clip_name, metadata)
                    print(f"  → Cached: {clip_name}")
            
            # Third pass: print all clips from cache
            print("-" * 50)
            for clip_number, clip_name in enumerate(clip_names, start=1):
                metadata = self.metadata_cache.get(clip_name)
                if metadata:
                    duration = metadata.get('duration', None)
                    timer = metadata.get('timer', None)
                    has_timer = timer is not None and timer != ''

                    if not has_timer:
                        print(f"[Clip {clip_number}] {clip_name}: No timer found. Default duration is 180s.")
                    elif has_timer:
                        print(f"[Clip {clip_number}] {clip_name}: duration={duration}, timer={timer}.")
                else:
                    print(f"[Clip {clip_number}] {clip_name}: No metadata available")
    
        except Exception as e:
            print(f"[Playlist Metadata] Error: {e}")
    
    def send_now_playing_to_pi(self, clip_name):
        """
        Send the current clip name to the Raspberry Pi via socket.
        The Pi should be running nowPlaying.py and listening for messages.
        """
        if not self.pi_ip or not self.pi_port or not clip_name:
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as pi_sock:
                pi_sock.settimeout(2)
                pi_sock.connect((self.pi_ip, self.pi_port))
                msg = f"NOW_PLAYING:{clip_name}\n"
                pi_sock.sendall(msg.encode('utf-8'))
                print(f"[Pi] Sent NOW_PLAYING: {clip_name}")

        except Exception as e:
            print(f"[Pi] Could not send now playing info: {e}")

    def send_clip_to_pi(self, clip_name):
        """Send the current clip name to the Pi."""
        if not self.pi_ip or not self.pi_port or not clip_name:
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.pi_ip, self.pi_port))
                msg = f"CLIP:{clip_name}\n"
                s.sendall(msg.encode('utf-8'))
                print(f"[Pi] Sent CLIP: {clip_name}")
        except Exception as e:
            print(f"[Pi] Error sending clip name: {e}")

    def send_playlist_to_pi(self, clip_names):
        """Send the list of clip names in the playlist to the Pi."""
        if not self.pi_ip or not self.pi_port:
            print(f"[Pi] Cannot send playlist: Missing IP or port")
            return
        if not clip_names:
            print(f"[Pi] Cannot send playlist: Empty clip list")
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.pi_ip, self.pi_port))
                # Send as comma-separated string
                msg = f"PLAYLIST:{','.join(clip_names)}\n"
                s.sendall(msg.encode('utf-8'))
                print(f"[Pi] Sent PLAYLIST: {len(clip_names)} clips")
                print(f"     Clips: {', '.join(clip_names[:3])}{'...' if len(clip_names) > 3 else ''}")
        except Exception as e:
            print(f"[Pi] Error sending playlist info: {e}")

    def fetch_playlist_clip_names(self):
        """
        Fetch and return a list of all clip names in the current playlist.
        Uses get_clip_count and get_clip_info for each clip index (starting from 1).
        """
        if not self.sock:
            print("[Playlist] No SOS socket connection")
            return []
        clip_names = []
        try:
            self.sock.sendall(b'get_clip_count\n')
            data = recv_data(self.sock, timeout_idle=2.0)
            clip_count_str = data.decode('utf-8', 'ignore').strip()
            if not clip_count_str.isdigit():
                print(f"[Playlist] Invalid clip count response: {repr(clip_count_str)}")
                return []
            clip_count = int(clip_count_str)
            print(f"[Playlist] Fetching {clip_count} clip names...")
            
            # Iterate through each clip index (starting from 1) to maintain order
            for clip_number in range(1, clip_count + 1):
                # Use get_clip_info to get clip name (returns the clip name directly)
                cmd = f'get_clip_info {clip_number}\n'.encode('utf-8')
                self.sock.sendall(cmd)
                info_data = recv_data(self.sock, timeout_idle=1.0).decode('utf-8', 'ignore').strip()
                
                # The response is the clip name directly
                if info_data:
                    clip_name = info_data
                    print(f"[Playlist] Clip {clip_number}: '{clip_name}'")
                    clip_names.append(clip_name)
                else:
                    print(f"[Playlist] No response for clip {clip_number}")
                    clip_names.append(f"Clip_{clip_number}")
            
            print(f"[Playlist] Retrieved {len(clip_names)} clip names in order")
                
        except Exception as e:
            print(f"[Playlist] Error fetching clip names: {e}")
            import traceback
            traceback.print_exc()
        return clip_names

    def run(self, poll_interval=0.5):
        """
        Main engine loop with optimized startup sequence.
        
        Args:
            poll_interval: Time between checks in seconds (default: 0.5 seconds)
        """
        print("Starting LibreOffice Impress Engine...")
        
        # Initialize GUI overlay but keep it hidden initially
        print("Initializing GUI overlay...")
        print("[Success] GUI overlay initialized (hidden)")
        
        # Launch LibreOffice
        print("Launching LibreOffice slideshow...")
        try:
            self.pp.launchpp(RunShow=True)
            self.libreoffice_launch_time = time.time()
            print("[Success] LibreOffice slideshow started")
        except Exception as e:
            print(f"Failed to launch LibreOffice Impress: {e}")
            print("\nDEBUG INFO:")
            import traceback
            traceback.print_exc()
            return
        
        # Verify LibreOffice controller is accessible
        print("Verifying LibreOffice controller...")
        max_attempts = 5
        controller_ready = False
        for attempt in range(max_attempts):
            try:
                if self.pp.show:
                    test_controller = self.pp.show.getCurrentController()
                    if test_controller:
                        print("[Success] LibreOffice controller verified")
                        controller_ready = True
                        break
            except Exception as e:
                pass
            
            if attempt < max_attempts - 1:
                print(f"  Controller not ready, waiting 1s... ({attempt+1}/{max_attempts})")
                time.sleep(1)
        
        if not controller_ready:
            print("[Warning] Controller verification failed, but continuing...")
        
        # Connect to SOS
        print("Connecting to SOS server...")
        if not self.connect_to_sos():
            print("Failed to connect to SOS. Exiting.")
            self.pp.close()
            return
        print("[Success] Connected to SOS")
        
        # Test connection to Raspberry Pi (nowPlaying)
        print(f"Testing connection to Pi at {self.pi_ip}:{self.pi_port}...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                test_sock.settimeout(2)
                test_sock.connect((self.pi_ip, self.pi_port))
                test_sock.sendall(b"INIT:Engine started\n")
                print("[Success] Pi connection established")
        except Exception as e:
            print(f"[Warning] Could not connect to Pi: {e}")
            print("         Continuing without Pi integration...")
        
        # Fetch and cache playlist metadata
        print("Fetching playlist metadata...")
        self.fetch_playlist_metadata()
        print("[Success] Playlist metadata cached")
        
        # Send initial playlist to Pi
        print("Sending playlist to Pi...")
        initial_playlist = self.fetch_playlist_clip_names()
        if initial_playlist:
            self.send_playlist_to_pi(initial_playlist)
        
        print("Initialization complete. Waiting for clip detection...\n")
        
        # Main loop
        print("\nEngine loop running...")
        print("Monitoring SOS for clip changes...\n")
        
        last_clip = ""
        last_playlist = None
        # Initialize timing to avoid None checks
        self.clip_real_start_time = time.time()
        
        while self.running:
            # Process Qt events to keep GUI responsive
            self.qapp.processEvents()
            
            time.sleep(poll_interval)
            
            # Get current clip info from SOS
            success, clip_name = self.get_current_clip_info()
            
            if not success:
                print("Lost connection to SOS, attempting to reconnect...")
                if self.sock:
                    try:
                        self.sock.close()
                    except:
                        pass
                if not self.connect_to_sos():
                    print("Reconnection failed. Exiting.")
                    break
                continue
            
            # Update progress overlay continuously
            if clip_name:
                current_frame = self.get_frame_number()
                fps = self.get_frame_rate()
                
                # Calculate current time 
                if self.clip_real_start_time is not None:
                    current_time = time.time() - self.clip_real_start_time
                else:
                    current_time = current_frame / fps if fps > 0 else 0
                
                total_duration = self.cached_total_duration
                
                # Handle multi-slide progression
                if len(self.current_slide_list) > 1 and self.slide_durations:
                    cumulative_time = 0
                    target_slide_index = 0
                    
                    for i, slide_duration in enumerate(self.slide_durations):
                        cumulative_time += slide_duration
                        if current_time < cumulative_time:
                            target_slide_index = i
                            break
                    else:
                        # We've passed all time boundaries, use last slide
                        target_slide_index = len(self.current_slide_list) - 1
                    
                    # Navigate to next slide if needed
                    if target_slide_index != self.current_slide_index:
                        self.current_slide_index = target_slide_index
                        target_slide = self.current_slide_list[self.current_slide_index]
                        
                        # Calculate time boundaries for debugging
                        time_boundaries = []
                        cumulative = 0
                        for dur in self.slide_durations:
                            cumulative += dur
                            time_boundaries.append(f"{cumulative:.1f}s")
                        
                        print(f"  → Auto-advancing to slide {target_slide} ({self.current_slide_index + 1}/{len(self.current_slide_list)}) at {current_time:.1f}s")
                        print(f"     Slide boundaries: {' | '.join(time_boundaries)}\n")
                        self.pp.goto(target_slide)
                        self.current_slide = target_slide
                
                # Update subtitles via SubtitleManager (handles both primary and secondary)
                if self.subtitle_enabled and self.subtitle_manager.has_subtitles():
                    if self.subtitle_manager.current_clip == clip_name:
                        # SubtitleManager.update() will call overlay.update_progress with subtitle texts
                        # We need to update the total duration separately
                        self.subtitle_manager.update(current_frame, fps)
                        # Also update slide count for tick marks
                        self.overlay.slide_count = len(self.current_slide_list)
                else:
                    # No subtitles, update progress without them
                    self.overlay.update_progress(current_time, total_duration, "", 
                                                slide_count=len(self.current_slide_list))
                

            if clip_name and clip_name != last_clip:
                # Print stopwatch value for previous clip (if not first clip)
                if self.clip_start_time is not None and last_clip:
                    elapsed = time.time() - self.clip_start_time
                    print(f"[Stopwatch] Actual duration for '{last_clip}': {elapsed:.2f}s\n")

                # Send current clip to Pi (Pi expects "CLIP:<name>" format)
                self.send_clip_to_pi(clip_name)

                # Start timer for new clip
                self.clip_start_time = time.time()
                self.clip_real_start_time = time.time()  # Track real elapsed time independently

                last_clip = clip_name

                # Subtitle check: Clear old subtitles when clip changes
                self.subtitle_manager.subtitles = []
                self.subtitle_manager.current_clip = None

                # Get slide numbers for this clip
                slide_nums = self.get_slide_numbers(clip_name)

                # Check for playlist change
                playlist_name = self.get_playlist_name()
                if playlist_name != self.current_playlist_name:
                    print(f"[Playlist] Changed: {self.current_playlist_name} -> {playlist_name}\n")
                    self.current_playlist_name = playlist_name
                    self.current_clip_metadata = {} 
                    self.current_slide_list = []    
                    self.current_slide_index = 0    
                    self.clip_start_time = None     
                    self.clip_real_start_time = None
                    self.cached_total_duration = 180.0
                    self.fetch_playlist_metadata()
                    clip_names = self.fetch_playlist_clip_names()
                    self.send_playlist_to_pi(clip_names)
    
                try:
                    self.sock.sendall(b'get_clip_number\n')
                    data = self.sock.recv(1024)
                    clip_number = data.decode('utf-8', 'ignore').strip()
                    if clip_number and clip_number.isdigit():
                        self.current_clip_metadata = self.fetch_clip_metadata(clip_number)
                        
                        if self.current_clip_metadata:
                            print(f"\nClip '{clip_name}' Metadata:")
                            print("-" * 50)
                            for key, value in sorted(self.current_clip_metadata.items()):
                                print(f"  {key:20s}: {value}")
                            print("-" * 50)
                        
                        self.current_slide_list = slide_nums
                        self.current_slide_index = 0                         

                        duration_str = self.current_clip_metadata.get('duration', None)
                        timer_str = self.current_clip_metadata.get('timer', None)

                        total_duration = None
                        if timer_str is not None and str(timer_str).strip() != "":
                            try:
                                total_duration = float(timer_str)
                                print(f"[Duration] Using timer field: {total_duration:.1f}s")
                            except (ValueError, TypeError):
                                print(f"[Duration] Invalid timer value, using default: 180.0s")
                                total_duration = 180.0
                        elif duration_str is not None and str(duration_str).strip() != "":
                            try:
                                total_duration = float(duration_str)
                                print(f"[Duration] Using specified duration: {total_duration:.1f}s")
                            except (ValueError, TypeError):
                                print(f"[Duration] Invalid duration value, using default: 180.0s")
                                total_duration = 180.0
                        else:
                            total_duration = 180.0
                            print(f"[Duration] No timer or duration found, using default: {total_duration:.1f}s")

                        self.cached_total_duration = total_duration

                        # Calculate duration for each slide (divide total duration evenly)
                        num_slides = len(slide_nums)
                        slide_duration = total_duration / num_slides if num_slides > 0 else total_duration
                        self.slide_durations = [slide_duration] * num_slides
                        
                        # Navigate to first slide
                        if self.current_slide not in slide_nums:
                            target_slide = slide_nums[0]
                            if num_slides > 1:
                                slide_list_str = ", ".join(map(str, slide_nums))
                                print(f"Clip: '{clip_name}' -> Slides [{slide_list_str}] ({slide_duration:.1f}s each)")
                            else:
                                print(f"Clip: '{clip_name}' -> Slide {target_slide}")
                            
                            self.pp.goto(target_slide)
                            self.current_slide = target_slide
                        
                        # Load subtitles when clip changes, check if subtitles
                        print()
                        if self.subtitle_enabled:
                            caption_path = self.current_clip_metadata.get('caption', '')
                            caption2_path = self.current_clip_metadata.get('caption2', '')  # Secondary subtitles (Spanish)
                            
                            if caption_path:
                                caption_path = caption_path.strip()
                                print(f"[Subtitles]: {clip_name}")
                                
                                # Handle caption2 - might be relative path or have space before filename
                                if caption2_path:
                                    caption2_path = caption2_path.strip()
                                    # print(f"[Debug] Raw caption2_path: '{caption2_path}'")
                                    
                                    # Handle case where there's a space before the filename
                                    # e.g., ".../directory /filename.srt" should become ".../directory/filename.srt"
                                    if ' /' in caption2_path:
                                        caption2_path = caption2_path.replace(' /', '/')
                                    
                                    # If it starts with /, it's already a full path
                                    # Otherwise, construct full path from caption directory
                                    if not caption2_path.startswith('/'):
                                        caption_dir = os.path.dirname(caption_path)
                                        caption2_path = f"{caption_dir}/{caption2_path}"
                                    
                                    # print(f"[Debug] caption2_path after processing: '{caption2_path}'")
                                
                                # Try to fetch primary caption from SOS server if path looks like a server path
                                local_subtitle_path = None
                                if caption_path.startswith('/shared/sos/') or caption_path.startswith('/'):
                                    # This is a server path - try to fetch it
                                    local_subtitle_path = self.fetch_subtitle_file(caption_path)
                                elif os.path.exists(caption_path):
                                    # Already a local path that exists
                                    local_subtitle_path = caption_path
                                else:
                                    # Try relative to project directory
                                    relative_path = os.path.join(os.path.dirname(__file__), caption_path)
                                    if os.path.exists(relative_path):
                                        local_subtitle_path = relative_path
                                
                                # Try to fetch secondary caption (caption2) if available
                                local_subtitle2_path = None
                                if caption2_path:
                                    if caption2_path.startswith('/shared/sos/') or caption2_path.startswith('/'):
                                        local_subtitle2_path = self.fetch_subtitle_file(caption2_path)
                                    elif os.path.exists(caption2_path):
                                        local_subtitle2_path = caption2_path
                                    else:
                                        relative_path2 = os.path.join(os.path.dirname(__file__), caption2_path)
                                        if os.path.exists(relative_path2):
                                            local_subtitle2_path = relative_path2
                                
                                if local_subtitle_path:
                                    # Load with dual subtitle support
                                    # Pass datadir to detect site-custom movies
                                    datadir = self.current_clip_metadata.get('datadir', '')
                                    self.subtitle_manager.load_subtitles_for_clip(clip_name, local_subtitle_path, local_subtitle2_path, datadir)
                                    
                                    # Show overlay after subtitles are loaded AND layout type is determined
                                    # This prevents wrong format from flashing before adjustment
                                    if not self.overlay_shown:
                                        print("\n[Startup] Subtitles loaded and layout determined, showing overlay...")
                                        self.overlay.start()
                                        self.overlay_shown = True
                                    print(f"[Subtitles] Ready for display\n")
                                else:
                                    print(f"[Subtitles-error] Could not load subtitle file\n")
                            else:
                                # No subtitles for this clip - show overlay on startup anyway
                                if not self.overlay_shown:
                                    print("\n[Startup] No subtitles, showing overlay...")
                                    self.overlay.start()
                                    self.overlay_shown = True
                        else:
                            # Subtitles disabled - show overlay on startup anyway
                            if not self.overlay_shown:
                                print("\n[Startup] Showing overlay...")
                                self.overlay.start()
                                self.overlay_shown = True
                except Exception as e:
                    print(f"Warning: Could not fetch clip metadata: {e}")
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        
        print("\nStopping GUI overlay...")
        self.overlay.stop()
        
        self.pp.close()
        print("Engine stopped")
    
    def stop(self):
        """Stop the engine forcefully."""
        print("\nInitiating shutdown...")
        self.running = False
        
        # Force close socket
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        
        # Force stop GUI overlay
        try:
            if self.overlay:
                self.overlay.stop()
                self.overlay.close()
        except:
            pass
        
        # Force close presentation
        try:
            if self.pp:
                self.pp.close()
        except:
            pass
        
        # Force quit Qt application
        try:
            if self.qapp:
                self.qapp.quit()
        except:
            pass
        
        print("Engine stopped - exit complete")
        
        # Force exit process
        import sys
        sys.exit(0)
