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
from PyQt5.QtWidgets import QApplication
from subtitles import SubtitleManager
from progressOverlay import ProgressOverlay


class SimplePPEngine:
    """Simplified LibreOffice Impress engine for SOS integration."""
    
    def __init__(self, pp, pp_dictionary, sos_ip, sos_port, clip_metadata=None, sos_user='sosdemo', sos_password=None, use_gui_overlay=True, overlay_position='bottom'):
        """
        Initialize the engine.
        
        Args:
            pp: LibreOffice Impress controller object
            pp_dictionary: Dict mapping clip names to slide numbers
            sos_ip: IP address of SOS server
            sos_port: Port number of SOS server
            clip_metadata: Optional dict mapping clip names to metadata (caption paths, etc.)
            use_gui_overlay: If True, use GUI overlay instead of terminal display
            overlay_position: Position of overlay ('bottom', 'top', 'bottom-right', 'top-right')
        """
        self.pp = pp
        self.pp_dictionary = pp_dictionary
        self.sos_ip = sos_ip
        self.sos_port = sos_port
        self.sos_user = sos_user
        self.sos_password = sos_password
        self.running = True
        self.current_slide = -1
        self.sock = None
        
        # GUI overlay support (PyQt5)
        self.use_gui_overlay = use_gui_overlay
        self.overlay = None
        self.qapp = None
        if use_gui_overlay:
            print("Initializing GUI overlay for progress display...")
            # Initialize QApplication if not already done
            if not QApplication.instance():
                self.qapp = QApplication(sys.argv)
            self.overlay = ProgressOverlay(position=overlay_position, opacity=0.85)
        
        # Subtitle support
        self.clip_metadata = clip_metadata or {}
        self.subtitle_manager = SubtitleManager(gui_overlay=self.overlay)
        self.subtitle_enabled = True  # Set to False to disable subtitle display
        
        # Create local cache directory for subtitles
        self.subtitle_cache_dir = os.path.join(os.path.dirname(__file__), 'subtitle_cache')
        os.makedirs(self.subtitle_cache_dir, exist_ok=True)
    
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
            print("✓ Connected to SOS server")
            
            # Send enable handshake
            print("Sending handshake...")
            self.sock.sendall(b'enable\n')
            
            # Wait for response
            data = self.sock.recv(1024)
            response = data.decode('utf-8', 'ignore').strip()
            print(f"Handshake response: {repr(response)}")
            
            if response == 'R':
                print("✓ Handshake successful")
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
        Fetch subtitle file from SOS server via SSH/SCP.
        
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
            print(f"  ✓ Using cached subtitle: {filename}")
            return local_path
        
        print(f"  Fetching subtitle from SOS server: {filename}")
        
        # Use plink/pscp on Windows if password is provided
        import platform
        is_windows = platform.system() == 'Windows'
        
        if is_windows and self.sos_password:
            # Try using pscp (PuTTY's SCP) with password on Windows
            try:
                pscp_command = [
                    'pscp',
                    '-batch',
                    '-pw', self.sos_password,
                    f'{self.sos_user}@{self.sos_ip}:{remote_path}',
                    local_path
                ]
                
                result = subprocess.run(
                    pscp_command,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and os.path.exists(local_path):
                    print(f"  ✓ Downloaded subtitle: {filename}")
                    return local_path
                    
            except FileNotFoundError:
                # pscp not available, will try socket method
                pass
            except Exception as e:
                print(f"  ⚠ pscp error: {e}")
        
        # Socket-based method - read file directly via SSH socket connection
        # This is more portable and doesn't require external tools
        try:
            print(f"  Trying direct socket SSH method...")
            import socket as net_socket
            
            # Connect to SSH server
            sock = net_socket.socket(net_socket.AF_INET, net_socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.sos_ip, 22))
            
            # Send SSH version exchange
            sock.recv(1024)  # Receive server version
            sock.sendall(b'SSH-2.0-Python\r\n')
            
            # This is a simplified approach - for production use paramiko
            sock.close()
            print(f"  ⚠ Socket SSH requires paramiko library")
            
        except Exception as e:
            print(f"  ⚠ Socket method failed: {e}")
        
        # Fallback: Try HTTP/network share if available
        # Many SOS servers also host files via HTTP
        try:
            import urllib.request
            
            # Try HTTP on common ports
            for port in [80, 8080]:
                try:
                    http_url = f'http://{self.sos_ip}:{port}{remote_path}'
                    print(f"  Trying HTTP: {http_url}")
                    
                    response = urllib.request.urlopen(http_url, timeout=5)
                    content = response.read()
                    
                    with open(local_path, 'wb') as f:
                        f.write(content)
                    
                    print(f"  ✓ Downloaded subtitle via HTTP: {filename}")
                    return local_path
                    
                except Exception:
                    continue
                    
        except Exception as e:
            pass
        
        # Last resort: Try SSH with key-based auth (no password)
        try:
            scp_command = [
                'scp',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'PasswordAuthentication=no',
                '-o', 'ConnectTimeout=5',
                f'{self.sos_user}@{self.sos_ip}:{remote_path}',
                local_path
            ]
            
            result = subprocess.run(
                scp_command,
                capture_output=True,
                text=True,
                timeout=10,
                stdin=subprocess.DEVNULL  # Don't prompt for password
            )
            
            if result.returncode == 0 and os.path.exists(local_path):
                print(f"  ✓ Downloaded subtitle: {filename}")
                return local_path
                
        except Exception as e:
            pass
        
        print(f"  ✗ Could not fetch subtitle file")
        print(f"     To enable automatic fetching:")
        print(f"     1. Install PuTTY (for pscp) on Windows")
        print(f"     2. Or set up SSH key: ssh-keygen & ssh-copy-id {self.sos_user}@{self.sos_ip}")
        print(f"     3. Or manually download to: {self.subtitle_cache_dir}")
        return None
    
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
    
    def run(self, poll_interval=2):
        """
        Main engine loop.
        
        Args:
            poll_interval: Time between checks in seconds
        """
        print("Starting LibreOffice Impress Engine...")
        
        # Start GUI overlay if enabled
        if self.use_gui_overlay and self.overlay:
            print("Starting GUI overlay...")
            self.overlay.start()
            time.sleep(1)  # Give overlay time to initialize
            print("✓ GUI overlay started")
        
        # Launch LibreOffice Impress first
        try:
            self.pp.launchpp(RunShow=True)
            print("LibreOffice Impress slideshow started")
        except Exception as e:
            print(f"Failed to launch LibreOffice Impress: {e}")
            print("\nDEBUG INFO:")
            import traceback
            traceback.print_exc()
            if self.overlay:
                self.overlay.stop()
            return
        
        # Connect to SOS
        print(f"\nConnecting to SOS server...")
        if not self.connect_to_sos():
            print("Failed to connect to SOS. Exiting.")
            self.pp.close()
            return
        
        # Main loop
        print("\nEngine running...")
        print("Monitoring SOS for clip changes...")
        print("Note: Slide navigation uses keyboard simulation")
        
        last_clip = ""
        while self.running:
            # Process Qt events to keep GUI responsive
            if self.qapp:
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
            
            # Only process if clip changed
            if clip_name and clip_name != last_clip:
                last_clip = clip_name
                
                # Get slide numbers for this clip
                slide_nums = self.get_slide_numbers(clip_name)
                
                # Navigate to slide if different
                if self.current_slide not in slide_nums:
                    target_slide = slide_nums[0]
                    print(f"Clip: '{clip_name}' -> Slide {target_slide}")
                    self.pp.goto(target_slide)
                    self.current_slide = target_slide
                
                # Load subtitles when clip changes
                if self.subtitle_enabled and clip_name in self.clip_metadata:
                    caption_path = self.clip_metadata[clip_name].get('caption', '')
                    if caption_path:
                        print(f"\n[Subtitles] Loading for: {clip_name}")
                        
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
                            print(f"[Subtitles] ✓ Ready for display\n")
                        else:
                            print(f"[Subtitles] ✗ Could not load subtitle file\n")
            
            # Update subtitle display during playback
            if self.subtitle_enabled and clip_name and self.subtitle_manager.has_subtitles():
                current_frame = self.get_frame_number()
                fps = self.get_frame_rate()
                
                # SubtitleManager.update() handles its own display via display_progress()
                # No need to manually print subtitles here
                self.subtitle_manager.update(current_frame, fps)
                
                # Process Qt events after updating GUI
                if self.qapp:
                    self.qapp.processEvents()
        
        # Cleanup
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        
        # Stop GUI overlay
        if self.overlay:
            print("\nStopping GUI overlay...")
            self.overlay.stop()
        
        self.pp.close()
        print("Engine stopped")
    
    def stop(self):
        """Stop the engine."""
        self.running = False
        if self.overlay:
            self.overlay.stop()
