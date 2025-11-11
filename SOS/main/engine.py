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
    Parse SOS name-value pair output into a dictionary.
    Handles values in curly braces {like this} and regular values.
    """
    result = {}
    # Pattern to match: key followed by either {value} or regular value
    pattern = r'(\w+)\s+(?:\{([^}]+)\}|(\S+))'
    
    matches = re.findall(pattern, data)
    for match in matches:
        key = match[0]
        value = match[1] if match[1] else match[2]
        result[key] = value
    
    return result


class SimplePPEngine:
    """Simplified LibreOffice Impress engine for SOS integration."""
    
    def __init__(self, pp, pp_dictionary, sos_ip, sos_port):
        """
        Initialize the engine.
        
        Args:
            pp: LibreOffice Impress controller object
            pp_dictionary: Dict mapping clip names to slide numbers
            sos_ip: IP address of SOS server
            sos_port: Port number of SOS server
        """
        self.pp = pp
        self.pp_dictionary = pp_dictionary
        self.sos_ip = sos_ip
        self.sos_port = sos_port
        self.running = True
        self.current_slide = -1
        self.sock = None
        
        # GUI overlay support
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
        
        # Create local cache directory for subtitles
        self.subtitle_cache_dir = os.path.join(os.path.dirname(__file__), 'subtitle_cache')
        os.makedirs(self.subtitle_cache_dir, exist_ok=True)
        
        # TEMPORARY: Testing stopwatch counter for clips without duration/timer
        self.clip_start_time = None
        self.clip_real_start_time = None  # Track real elapsed time for progress bar
        
        # Multi-slide navigation support
        self.current_slide_list = []  # All slides for current dataset
        self.current_slide_index = 0  # Current position in slide list
        self.slide_durations = []     # Duration for each slide in the list
        self.auto_advance_sent = False  # Flag to prevent repeated auto-advances
        self.cached_total_duration = 180.0  # Cached duration for current clip
    
    def connect_to_sos(self, timeout=4):
        """
        Connect to the SOS server and send enable handshake.
        
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
                print("[Success] SOS Handshake successful")
                return True
            else:
                print(f"⚠ Unexpected handshake response: {response}")
                # Continue anyway - some SOS versions respond differently
                return True
                
        except socket.error as e:
            print(f"✗ Failed to connect to SOS: {e}")
            return False
        except Exception as e:
            print(f"✗ Error during SOS connection: {e}")
            return False
    
    def restart_current_clip(self):
        """
        Restart the currently playing clip by going to previous then next.
        This is a workaround since SOS doesn't have a direct restart command.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sock:
            return False
        
        try:
            print("Restarting current clip...")
            
            # Send prev_clip command
            self.sock.sendall(b'prev_clip\n')
            time.sleep(0.2)  # Small delay to let SOS process the command
            
            # Clear any response
            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            # Send next_clip command to return to the clip
            self.sock.sendall(b'next_clip\n')
            time.sleep(0.2)
            
            # Clear any response
            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            print("[Success] Clip restarted")
            return True
            
        except socket.error as e:
            print(f"⚠ Error restarting clip: {e}")
            return False
        except Exception as e:
            print(f"⚠ Error restarting clip: {e}")
            return False
    
    def get_current_clip_info(self):
        """
        Get current clip information from SOS server.
        
        Returns:
            tuple: (success, clip_name)
        """
        if not self.sock:
            return (False, "")
        
        try:
            # Request current clip number
            self.sock.sendall(b'get_clip_number\n')
            
            # Receive response
            data = self.sock.recv(1024)
            clip_number = data.decode('utf-8', 'ignore').strip()
            
            if not clip_number or not clip_number.isdigit():
                return (False, "")
            
            # Request clip info
            cmd = f"get_clip_info {clip_number}\n".encode('utf-8')
            self.sock.sendall(cmd)
            
            # Receive clip info
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
        Fetch all metadata for a clip from SOS server using get_all_name_value_pairs.
        
        Args:
            clip_number: The clip number to fetch metadata for
            
        Returns:
            dict: Parsed metadata dictionary, or empty dict on failure
        """
        if not self.sock:
            return {}
        
        try:
            # Get all name-value pairs for the current clip
            command = f'get_all_name_value_pairs {clip_number}\n'.encode('utf-8')
            self.sock.sendall(command)
            data = recv_data(self.sock, timeout_idle=1.0)
            clip_data = data.decode('utf-8', 'ignore').strip()
            
            # Parse the data into a dictionary
            clip_metadata = parse_name_value_pairs(clip_data)
            clip_metadata['clip_number'] = clip_number
            
            return clip_metadata
            
        except Exception as e:
            print(f"Warning: Could not fetch clip metadata: {e}")
            return {}
    
    def get_frame_number(self):
        """
        Get current frame number from SOS server.
        
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
        Get frame rate from SOS server.
        
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
        Fetch subtitle file from SOS server via HTTP.
        
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
            print(f" → Filename: {filename}")
            return local_path
                
    
    def get_slide_numbers(self, clip_name):
        """
        Map clip name to slide number(s).
        
        Args:
            clip_name: Name of the current clip
            
        Returns:
            list: List of slide numbers (defaults to [1] if not found)
        """
        if clip_name.strip() in self.pp_dictionary:
            return self.pp_dictionary[clip_name.strip()]
        return [1]
    
    def run(self, poll_interval=0.5):
        """
        Main engine loop.
        
        Args:
            poll_interval: Time between checks in seconds (default: 0.5 seconds)
        """
        print("Starting LibreOffice Impress Engine...")
        
        # Start GUI overlay
        print("Starting GUI overlay...")
        self.overlay.start()
        time.sleep(1)
        print("[Success] GUI overlay started")
        
        # Launch LibreOffice Impress first
        try:
            self.pp.launchpp(RunShow=True)
            print("LibreOffice slideshow started")
        except Exception as e:
            print(f"Failed to launch LibreOffice Impress: {e}")
            print("\nDEBUG INFO:")
            import traceback
            traceback.print_exc()
            if self.overlay:
                self.overlay.stop()
            return
        
        # Connect to SOS
        if not self.connect_to_sos():
            print("Failed to connect to SOS. Exiting.")
            self.pp.close()
            return
        
        # Restart the current clip to sync from the beginning
        self.restart_current_clip()
        
        # Main loop
        print("\nEngine loop running...")
        print("Monitoring SOS for clip changes...\n")
        
        last_clip = ""
        # Initialize timing to avoid None checks
        self.clip_real_start_time = time.time()
        
        while self.running:
            # Process Qt events to keep GUI responsive
            self.qapp.processEvents()
            
            time.sleep(poll_interval)
            
            # Get current clip info from SOS
            success, clip_name = self.get_current_clip_info()
            
            if not success:
                # Connection issue - try to reconnect
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
            
            # Update progress overlay continuously during playback
            if clip_name:
                current_frame = self.get_frame_number()
                fps = self.get_frame_rate()
                
                # Calculate current time using real elapsed time
                if self.clip_real_start_time is not None:
                    current_time = time.time() - self.clip_real_start_time
                else:
                    current_time = current_frame / fps if fps > 0 else 0
                
                # Use cached total duration (calculated when clip changed)
                total_duration = self.cached_total_duration
                
                # Handle multi-slide progression
                if len(self.current_slide_list) > 1 and self.slide_durations:
                    # Calculate which slide we should be on based on elapsed time
                    # Build cumulative time boundaries for each slide
                    cumulative_time = 0
                    target_slide_index = 0
                    
                    for i, slide_duration in enumerate(self.slide_durations):
                        cumulative_time += slide_duration
                        if current_time < cumulative_time:
                            # We're still within this slide's time window
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
                        print(f"     Slide boundaries: {' | '.join(time_boundaries)}")
                        self.pp.goto(target_slide)
                        self.current_slide = target_slide
                
                # Get current subtitle text
                subtitle_text = ""
                if self.subtitle_enabled and self.subtitle_manager.has_subtitles():
                    if self.subtitle_manager.current_clip == clip_name:
                        from subtitles import find_subtitle_at_time
                        subtitle_text = find_subtitle_at_time(self.subtitle_manager.subtitles, current_time)
                
                # Update progress overlay with slide transition markers
                self.overlay.update_progress(current_time, total_duration, subtitle_text, current_frame, 
                                            slide_count=len(self.current_slide_list))
                
                # Auto-advance to next clip if duration is exceeded (only once)
                if current_time > total_duration and not self.auto_advance_sent:
                    print(f"\n[Auto-advance] Duration exceeded ({current_time:.1f}s > {total_duration:.1f}s), advancing to next clip...")
                    try:
                        self.sock.sendall(b'next_clip\n')
                        time.sleep(0.1)
                        # Clear response
                        try:
                            self.sock.recv(1024)
                        except socket.timeout:
                            pass
                        print("[Auto-advance] Sent next_clip command")
                        self.auto_advance_sent = True  # Mark that we've sent the command
                    except Exception as e:
                        print(f"[Auto-advance] Error sending next_clip: {e}")
            
            # Only process if clip changed
            if clip_name and clip_name != last_clip:
                # Print stopwatch value for previous clip (if not first clip)
                if self.clip_start_time is not None and last_clip:
                    elapsed = time.time() - self.clip_start_time
                    print(f"[Stopwatch] Actual duration for '{last_clip}': {elapsed:.2f}s\n")

                # Start timer for new clip
                self.clip_start_time = time.time()
                self.clip_real_start_time = time.time()  # Track real elapsed time independently

                # Reset auto-advance flag for new clip
                self.auto_advance_sent = False

                last_clip = clip_name

                # Subtitle check: Clear old subtitles when clip changes
                self.subtitle_manager.subtitles = []
                self.subtitle_manager.current_clip = None

                # Get slide numbers for this clip
                slide_nums = self.get_slide_numbers(clip_name)
                
                # Fetch clip metadata from SOS server
                try:
                    # Get clip number for metadata fetch
                    self.sock.sendall(b'get_clip_number\n')
                    data = self.sock.recv(1024)
                    clip_number = data.decode('utf-8', 'ignore').strip()
                    
                    if clip_number and clip_number.isdigit():
                        self.current_clip_metadata = self.fetch_clip_metadata(clip_number)
                        
                        # Display fetched metadata in formatted dictionary style
                        if self.current_clip_metadata:
                            print("Clip Metadata:")
                            print("-" * 50)
                            for key, value in sorted(self.current_clip_metadata.items()):
                                print(f"  {key:20s}: {value}")
                            print("-" * 50)
                        
                        # Set up multi-slide navigation
                        self.current_slide_list = slide_nums
                        self.current_slide_index = 0
                        
                        # Determine if this is an image or movie based on file extension
                        data_path = self.current_clip_metadata.get('data', '')
                        is_image = False
                        if data_path:
                            data_lower = data_path.lower()
                            is_image = data_lower.endswith('.jpg') or data_lower.endswith('.jpeg') or data_lower.endswith('.png')
                        
                        # Get total duration for the dataset
                        # Images default to 180s, movies only default to 180s as last resort
                        total_duration = None
                        duration_str = self.current_clip_metadata.get('duration', '')
                        timer_str = self.current_clip_metadata.get('timer', '')
                        
                        # Check explicit duration fields first
                        if duration_str:
                            try:
                                total_duration = float(duration_str)
                                print(f"[Duration] Using duration field: {total_duration:.1f}s")
                            except (ValueError, TypeError):
                                pass
                        elif timer_str:
                            try:
                                total_duration = float(timer_str)
                                print(f"[Duration] Using timer field: {total_duration:.1f}s")
                            except (ValueError, TypeError):
                                pass
                        
                        # If no explicit duration, try to calculate from frame data (movies only)
                        if total_duration is None:
                            startframe_str = self.current_clip_metadata.get('startframe', '')
                            endframe_str = self.current_clip_metadata.get('endframe', '')
                            fps_str = self.current_clip_metadata.get('fps', '')
                            firstdwell_str = self.current_clip_metadata.get('firstdwell', '')
                            lastdwell_str = self.current_clip_metadata.get('lastdwell', '')
                            
                            if startframe_str and endframe_str and fps_str:
                                try:
                                    startframe = int(startframe_str)
                                    endframe = int(endframe_str)
                                    fps = float(fps_str)
                                    
                                    if fps > 0:
                                        frame_count = endframe - startframe
                                        base_duration = frame_count / fps
                                        
                                        # Add dwell times (converted from milliseconds to seconds)
                                        firstdwell_sec = 0.0
                                        lastdwell_sec = 0.0
                                        if firstdwell_str:
                                            try:
                                                firstdwell_sec = float(firstdwell_str) / 1000.0
                                            except (ValueError, TypeError):
                                                pass
                                        if lastdwell_str:
                                            try:
                                                lastdwell_sec = float(lastdwell_str) / 1000.0
                                            except (ValueError, TypeError):
                                                pass
                                        
                                        # Calculate dwell frames to subtract from total frame count
                                        firstdwell_frames = int(firstdwell_sec * fps) if firstdwell_sec > 0 else 0
                                        lastdwell_frames = int(lastdwell_sec * fps) if lastdwell_sec > 0 else 0
                                        
                                        # Actual playback frames = total frames minus dwell frames
                                        playback_frame_count = frame_count - firstdwell_frames - lastdwell_frames
                                        playback_duration = playback_frame_count / fps if playback_frame_count > 0 else base_duration
                                        
                                        total_duration = playback_duration
                                        print(f"[Duration] Calculated from frames: {total_duration:.1f}s")
                                except (ValueError, TypeError):
                                    pass
                        
                        # Apply defaults only if no duration found
                        if total_duration is None:
                            if is_image:
                                total_duration = 180.0  # Images always default to 180s
                                print(f"[Duration] Image detected, using default: {total_duration:.1f}s")
                            else:
                                # For movies, only default to 180s as last resort
                                total_duration = 180.0
                                print(f"[Duration] No metadata found, using default: {total_duration:.1f}s")
                        
                        # Cache the calculated duration for use in progress loop
                        self.cached_total_duration = total_duration
                        
                        # Calculate duration for each slide (divide total duration evenly)
                        num_slides = len(slide_nums)
                        slide_duration = total_duration / num_slides
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
                        
                        # Load subtitles when clip changes
                        print()
                        if self.subtitle_enabled:
                            caption_path = self.current_clip_metadata.get('caption', '')
                            if caption_path:
                                print(f"[Subtitles]: {clip_name}")
                                
                                # Try to fetch from SOS server if path looks like a server path
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
                                
                                if local_subtitle_path:
                                    self.subtitle_manager.load_subtitles_for_clip(clip_name, local_subtitle_path)
                                    print(f"[Subtitles] Ready for display\n")
                                else:
                                    print(f"[Subtitles-error] Could not load subtitle file\n")
                except Exception as e:
                    print(f"Warning: Could not fetch clip metadata: {e}")
        
        # Cleanup
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        
        # Stop GUI overlay
        print("\nStopping GUI overlay...")
        self.overlay.stop()
        
        self.pp.close()
        print("Engine stopped")
    
    def stop(self):
        """Stop the engine."""
        self.running = False
        self.overlay.stop()
