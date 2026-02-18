"""
SOS2 Engine
Connects to SOS server and controls LibreOffice Impress via CacheManager lookups.
"""

import socket
import time
import sys
import threading
import json
import atexit
from PyQt5.QtWidgets import QApplication
from overlay_subtitles import SubtitleManager, SubtitleOverlay
from overlay_progressBar import ProgressBarOverlay

class OverlayManager:
    """
    Manages the lifecycle and updates of the Progress and Subtitle overlays.
    """
    def __init__(self):
        # Ensure Qt App exists
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
            
        # Initialize Overlays (Hidden by default)
        self.progress_overlay = ProgressBarOverlay()
        
        self.subtitle_overlay = SubtitleOverlay(
            position='bottom',  # Changed from 'top' to avoid positioning issues
            opacity=0.85,
            y_offset=80,  # Offset above progress bar
            subtitle_font_size=28,
            subtitle_bg_opacity=150,
            show_title_row=False,
            parent_container_height=1.0  # Support entire length of the screen
        )
        
        # State
        self.mode = "HIDDEN" # HIDDEN, PROGRESS_ONLY, SUBTITLES_AND_PROGRESS
        
    def show_progress_only(self):
        """Display only the progress bar."""
        if self.mode != "PROGRESS_ONLY":
            self.subtitle_overlay.hide()
            self.progress_overlay.start() # Ensure it's visible/raised
            self.mode = "PROGRESS_ONLY"
            
    def show_subtitles_and_progress(self):
        """Display both subtitles and progress bar."""
        if self.mode != "SUBTITLES_AND_PROGRESS":
            self.progress_overlay.start()
            self.subtitle_overlay.start()
            self.mode = "SUBTITLES_AND_PROGRESS"
            
    def hide_all(self):
        """Hide all overlays."""
        if self.mode != "HIDDEN":
            self.progress_overlay.stop()
            self.subtitle_overlay.stop()
            self.mode = "HIDDEN"
            
    def update_progress(self, current_time, total_duration, slide_count=1):
        """Update progress bar data."""
        if self.mode != "HIDDEN":
            self.progress_overlay.update_progress(current_time, total_duration, slide_count)
            
    def update_subtitles(self, text1, text2=""):
        """Update subtitle text."""
        if self.mode == "SUBTITLES_AND_PROGRESS":
            self.subtitle_overlay.update_subtitles(text1, text2)

    def update_titles(self, left_title, right_title):
        """Update subtitle titles."""
        self.subtitle_overlay.update_titles(left_title, right_title)

    def process_events(self):
        """Keep GUI responsive."""
        self.app.processEvents()


SOS_IP = "10.10.51.98" #NETWORK
SOS_PORT = 2468
PI_IP = "10.10.51.111" #NETWORK
PI_PORT = 4096
ENGINE_QUERY_PORT = 4097  # Port for Pi to query engine state
HTTP_SERVER_PORT = 5000  # Port for HTTP facilitation interface

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

def parse_http_request(data: bytes) -> tuple:
    """
    Parse HTTP request and extract JSON body.
    Returns (is_http, json_body, method, path)
    """
    try:
        request_text = data.decode('utf-8', errors='ignore')
        
        # Check if it's an HTTP request
        if not (request_text.startswith('POST') or request_text.startswith('GET') or request_text.startswith('OPTIONS')):
            return (False, request_text, None, None)
        
        # Split headers and body
        parts = request_text.split('\r\n\r\n', 1)
        if len(parts) < 2:
            parts = request_text.split('\n\n', 1)
        
        if len(parts) < 2:
            return (False, request_text, None, None)
        
        headers_text = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        
        # Parse first line for method and path
        first_line = headers_text.split('\n')[0]
        method = first_line.split(' ')[0] if ' ' in first_line else 'POST'
        path = first_line.split(' ')[1] if len(first_line.split(' ')) > 1 else '/'
        
        return (True, body, method, path)
        
    except Exception as e:
        print(f"[Engine HTTP] Error parsing request: {e}")
        return (False, data.decode('utf-8', errors='ignore'), None, None)

def send_http_response(conn: socket.socket, data: dict, status_code: int = 200):
    """Send HTTP response with CORS headers."""
    status_messages = {
        200: "OK",
        400: "Bad Request",
        500: "Internal Server Error"
    }
    
    status_message = status_messages.get(status_code, "OK")
    response_body = json.dumps(data)
    
    # Build HTTP response with CORS headers
    response = f"HTTP/1.1 {status_code} {status_message}\r\n"
    response += "Content-Type: application/json\r\n"
    response += f"Content-Length: {len(response_body)}\r\n"
    response += "Access-Control-Allow-Origin: *\r\n"
    response += "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
    response += "Access-Control-Allow-Headers: Content-Type\r\n"
    response += "Connection: close\r\n"
    response += "\r\n"
    response += response_body
    
    conn.sendall(response.encode('utf-8'))

class SimplePPEngine:
    """
    Optimized Engine:
    - Connects to SOS server
    - Gets clip NUMBER from SOS
    - Gets clip NAME from local CacheManager (no socket usage)
    - Navigates LibreOffice
    """
    
    def __init__(self, pp, slide_dictionary, cache_manager, audio_controller=None):
        """
        Initialize the engine.
        
        Args:
            pp: LibreOffice Impress controller object
            slide_dictionary: Dict mapping clip names to slide numbers
            cache_manager: Initialized CacheManager instance
            audio_controller: Optional AudioController instance
        """
        self.pp = pp
        self.slide_dictionary = slide_dictionary
        self.cache_manager = cache_manager
        self.audio_controller = audio_controller
        self.running = True
        self.current_slide = -1
        self.sock = None
        
        # State tracking for queries
        self.current_clip_number = None
        self.playlist_init_data = None  # Stores the INIT message data
        self.state_lock = threading.Lock()
        
        # Audio state tracking
        self.current_audio_category = None
        self.audio_enabled = audio_controller is not None
        
        # Facilitation mode state
        self.facilitation_mode = False
        
        print(f"[Engine] Initialized with CacheManager")
        if self.audio_enabled:
            print("[Engine] Audio controller active")

        # UI Overlay Initialization
        if not QApplication.instance():
            self.qapp = QApplication(sys.argv)
        else:
            self.qapp = QApplication.instance()
            
        self.overlay_manager = OverlayManager()
        self.subtitle_manager = SubtitleManager(gui_overlay=self.overlay_manager.subtitle_overlay)
        
        # Timing state
        self.clip_start_time = None
        self.last_clip_name = None
        self.current_duration = 0
        
        # Start query server thread
        self.query_server_thread = threading.Thread(target=self._run_query_server, daemon=True)
        self.query_server_thread.start()
        
        # Start HTTP facilitation server thread
        self.http_server_thread = threading.Thread(target=self._run_http_server, daemon=True)
        self.http_server_thread.start()
        print(f"[Engine] HTTP facilitation server starting on port {HTTP_SERVER_PORT}")
        
        # Register cleanup handler for unexpected exits
        atexit.register(self._cleanup)
    
    def connect_to_sos(self, timeout=4):
        """Connect to SOS server."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            
            self.sock.connect((SOS_IP, SOS_PORT))
            print(f"[Engine] Connected to SOS at {SOS_IP}:{SOS_PORT}")
            
            # Send enable handshake
            self.sock.sendall(b'enable\n')
            data = self.sock.recv(1024)
            return True
                
        except socket.error as e:
            print(f"Failed to connect to SOS: {e}")
            return False
        except Exception as e:
            print(f"Error during SOS connection: {e}")
            return False
    
    def get_current_clip_info(self):
        """
        Get current clip info optimized for caching.
        1. Fetch only clip NUMBER from socket (fastest operation).
        2. Lookup Name in CacheManager (0ms).
        """
        if not self.sock:
            return None, None
        
        try:
            # 1: Get current clip number
            self.sock.sendall(b'get_clip_number\n')
            data = self.sock.recv(1024)
            clip_number_str = data.decode('utf-8', 'ignore').strip()
            
            if not clip_number_str or not clip_number_str.isdigit():
                return None, None
            
            clip_number = int(clip_number_str)
            
            # 2: Use CacheManager for name lookup (No Socket Call!)
            
            clip_name = None
            if self.cache_manager.current_playlist:
                clips = self.cache_manager.current_playlist.get('clips', [])
                if 0 < clip_number <= len(clips):
                    clip_name = clips[clip_number - 1].get('name')
            
            return clip_number, clip_name
            
        except socket.timeout:
            return None, None
        except socket.error:
            return None, None
        except Exception as e:
            print(f"Error getting clip info: {e}")
            return None, None

    def get_frame_number(self):
        """Get current frame number from SOS."""
        if not self.sock: return 0
        try:
            self.sock.sendall(b'get_frame_number\n')
            data = self.sock.recv(1024)
            val = data.decode('utf-8', 'ignore').strip()
            return int(val) if val.isdigit() else 0
        except: return 0
            
    def get_frame_rate(self):
        """Get frame rate from SOS."""
        if not self.sock: return 30.0
        try:
            self.sock.sendall(b'get_frame_rate\n')
            data = self.sock.recv(1024)
            val = data.decode('utf-8', 'ignore').strip().split()[0]
            return float(val) if val else 30.0
        except: return 30.0

    def _send_nowplaying_message(self, message: str) -> None:
        """Send a nowPlaying socket message to the Pi."""
        try:
            with socket.create_connection((PI_IP, PI_PORT), timeout=2.0) as pi_sock:
                pi_sock.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"[Engine] nowPlaying send failed: {e}")

    def update_nowPlaying(self, clip_number: int) -> None:
        """Send the current clip number to nowPlaying."""
        if clip_number is None:
            return
        with self.state_lock:
            self.current_clip_number = clip_number
        self._send_nowplaying_message(f"CLIP:{clip_number}\n")
    
    def _build_init_message(self) -> str:
        """Build INIT message from current playlist data."""
        if not self.cache_manager.current_playlist:
            return "INIT\n"
        
        clips = self.cache_manager.current_playlist.get('clips', [])
        lines = ["INIT"]
        
        for idx, clip in enumerate(clips, start=1):
            clip_name = clip.get('name', '')
            metadata = self.cache_manager.get(clip_name) or {}
            
            english_title = metadata.get('movie-title', clip_name)
            spanish_title = metadata.get('spanish-translation', '')
            duration_raw = metadata.get('duration', 0)
            
            # Handle both int and float duration values
            if isinstance(duration_raw, str):
                try:
                    duration_sec = float(duration_raw)
                except ValueError:
                    duration_sec = 0
            else:
                duration_sec = float(duration_raw)
            
            # Format duration as "Xm Xs" (no decimals)
            total_seconds = int(duration_sec)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            duration_str = f"{minutes}m {seconds}s"
            
            lines.append(f"{idx}|{english_title}|{spanish_title}|{duration_str}")
        
        return "\n".join(lines) + "\n"
    
    def _run_query_server(self):
        """Run a server socket to handle state queries from Pi."""
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('0.0.0.0', ENGINE_QUERY_PORT))
            server_sock.listen(1)
            server_sock.settimeout(1.0)  # Allow periodic checks of self.running
            
            print(f"[Engine] Query server listening on port {ENGINE_QUERY_PORT}")
            
            while self.running:
                try:
                    conn, addr = server_sock.accept()
                    print(f"[Engine] Query connection from {addr}")
                    
                    with conn:
                        conn.settimeout(2.0)
                        try:
                            # Receive request
                            data = conn.recv(1024).decode('utf-8', 'ignore').strip()
                            print(f"[Engine] Query request: {data}")
                            
                            if data == "REQUEST_STATE":
                                # Build complete response message
                                init_msg = self._build_init_message()
                                
                                # Append current clip if available
                                with self.state_lock:
                                    if self.current_clip_number is not None:
                                        clip_msg = f"CLIP:{self.current_clip_number}\n"
                                        complete_msg = init_msg + "\n" + clip_msg
                                    else:
                                        complete_msg = init_msg
                                
                                # Send as single message
                                conn.sendall(complete_msg.encode('utf-8'))
                                print(f"[Engine] Sent state to {addr} ({len(complete_msg)} bytes)")
                                print(f"[Engine] Preview: {complete_msg[:200]}..." if len(complete_msg) > 200 else f"[Engine] Full message: {complete_msg}")
                        except socket.timeout:
                            print(f"[Engine] Query timeout from {addr}")
                        except Exception as e:
                            print(f"[Engine] Query handler error: {e}")
                            
                except socket.timeout:
                    continue  # Check self.running and continue
                except Exception as e:
                    if self.running:
                        print(f"[Engine] Query server error: {e}")
                    break
            
            server_sock.close()
            print("[Engine] Query server stopped")
            
        except Exception as e:
            print(f"[Engine] Failed to start query server: {e}")

    def _run_http_server(self):
        """Run HTTP server for facilitation commands."""
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('0.0.0.0', HTTP_SERVER_PORT))
            server_sock.listen(5)
            server_sock.settimeout(1.0)
            
            print(f"[Engine] HTTP server ready on port {HTTP_SERVER_PORT}")
            
            while self.running:
                try:
                    conn, addr = server_sock.accept()
                    
                    # Receive data
                    data = recv_data(conn)
                    
                    if data:
                        # Parse HTTP request
                        is_http, body, method, path = parse_http_request(data)
                        
                        if is_http:
                            # Handle OPTIONS preflight
                            if method == "OPTIONS":
                                response = "HTTP/1.1 200 OK\r\n"
                                response += "Access-Control-Allow-Origin: *\r\n"
                                response += "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
                                response += "Access-Control-Allow-Headers: Content-Type\r\n"
                                response += "Content-Length: 0\r\n"
                                response += "Connection: close\r\n\r\n"
                                conn.sendall(response.encode('utf-8'))
                                conn.close()
                                continue
                            
                            # Handle POST/GET with body
                            if body:
                                response_data = self._handle_http_command(body)
                                send_http_response(conn, response_data)
                            else:
                                send_http_response(conn, {"status": "error", "message": "No data"}, 400)
                        else:
                            # Non-HTTP (raw socket)
                            response_data = self._handle_http_command(body)
                            conn.sendall(json.dumps(response_data).encode('utf-8'))
                    
                    conn.close()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[Engine HTTP] Connection error: {e}")
            
            server_sock.close()
            print("[Engine] HTTP server stopped")
            
        except Exception as e:
            print(f"[Engine] Failed to start HTTP server: {e}")
    
    def _handle_http_command(self, message: str) -> dict:
        """Process HTTP command from facilitation interface."""
        try:
            message = message.strip()
            if not message:
                return {"status": "error", "message": "Empty command"}
            
            data = json.loads(message)
            command = data.get("command", "").upper()
            
            if command == "FACILITATION_TOGGLE":
                enable = data.get("enable", False)
                return self._toggle_facilitation(enable)
            
            elif command == "VOLUME_CONTROL":
                action = data.get("action", "").upper()
                return self._handle_volume_control(action)
            
            elif command == "GET_STATE":
                with self.state_lock:
                    return {
                        "status": "ok",
                        "facilitation_mode": self.facilitation_mode,
                        "volume": self.audio_controller.get_volume() if self.audio_enabled else None,
                        "audio_enabled": self.audio_enabled
                    }
            
            else:
                return {"status": "error", "message": f"Unknown command: {command}"}
                
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def _toggle_facilitation(self, enable: bool) -> dict:
        """Toggle facilitation mode."""
        try:
            with self.state_lock:
                old_state = self.facilitation_mode
                self.facilitation_mode = enable
            
            if enable:
                print("[Engine] Facilitation ON")
                
                # Fade out and mute audio if playing
                if self.audio_enabled and self.audio_controller:
                    if self.audio_controller.is_playing():
                        print("[Engine] Fading out audio...")
                        self.audio_controller.fade_out()
                        time.sleep(2.2)  # Wait for fade
                    
                    print("[Engine] Muting audio")
                    self.audio_controller.mute()
                
                # Send PAUSE to nowPlaying
                self._send_to_nowplaying("PAUSE")
                
            else:
                print("[Engine] Facilitation OFF")
                
                # Unmute audio
                if self.audio_enabled and self.audio_controller:
                    print("[Engine] Unmuting audio")
                    self.audio_controller.unmute()
                
                # Send UNPAUSE to nowPlaying
                self._send_to_nowplaying("UNPAUSE")
            
            return {"status": "ok", "facilitation_mode": self.facilitation_mode}
            
        except Exception as e:
            print(f"[Engine] Facilitation toggle error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_volume_control(self, action: str) -> dict:
        """Handle volume control commands."""
        try:
            if not self.audio_enabled or not self.audio_controller:
                return {"status": "error", "message": "Audio not available"}
            
            if action == "UP":
                self.audio_controller.adjust_volume(10)
            elif action == "DOWN":
                self.audio_controller.adjust_volume(-10)
            elif action == "MUTE":
                self.audio_controller.toggle_mute()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
            
            volume = self.audio_controller.get_volume()
            return {"status": "ok", "volume": volume}
            
        except Exception as e:
            print(f"[Engine] Volume control error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_to_nowplaying(self, command: str):
        """Send command to nowPlaying display."""
        try:
            with socket.create_connection((PI_IP, PI_PORT), timeout=3.0) as sock:
                sock.sendall(command.encode('utf-8'))
                print(f"[Engine] Sent to nowPlaying: {command}")
        except ConnectionRefusedError:
            print(f"[Engine] nowPlaying not responding ({PI_IP}:{PI_PORT})")
        except socket.timeout:
            print(f"[Engine] nowPlaying timeout ({PI_IP}:{PI_PORT})")
        except Exception as e:
            print(f"[Engine] nowPlaying send error: {e}")

    def navigate_to_clip(self, clip_name):
        """Navigate to the slide(s) associated with the given clip name."""
        if clip_name not in self.slide_dictionary:
            print(f"[Engine] Warning: No slide mapping for '{clip_name}'")
            return
        
        slide_numbers = self.slide_dictionary[clip_name]
        if not slide_numbers:
            return
        
        target_slide = slide_numbers[0]
        
        if target_slide != self.current_slide:
            print(f"[Engine] Navigating to Slide {target_slide}")
            self.pp.goto(target_slide)
            self.current_slide = target_slide
    
    def manage_audio(self, clip_name, is_credits, is_translated):
        """
        Manage audio playback based on clip metadata.
        Plays ambient audio for non-subtitle, non-credits datasets.
        
        Args:
            clip_name: Name of the current clip
            is_credits: Whether this is a credits clip
            is_translated: Whether this is a translated movie with subtitles
        """
        if not self.audio_enabled or not self.audio_controller:
            return
        
        # Check facilitation mode - fade out and don't start new audio
        with self.state_lock:
            if self.facilitation_mode:
                if self.audio_controller.is_playing():
                    self.audio_controller.fade_out()
                    self.current_audio_category = None
                return
        
        # Don't play audio for credits or translated movies with subtitles
        if is_credits or is_translated:
            if self.audio_controller.is_playing():
                print("[Audio] Fading out audio for credits/subtitle clip")
                self.audio_controller.fade_out()
                self.current_audio_category = None
            return
        
        # Get the major category for this clip
        major_category = self.cache_manager.get_majorcategory(clip_name)
        
        if not major_category:
            # No category found - stop audio if playing
            if self.audio_controller.is_playing():
                print(f"[Audio] No major category found for '{clip_name}', stopping audio")
                self.audio_controller.fade_out()
                self.current_audio_category = None
            return
        
        # Handle multiple categories - use only the first one
        if ',' in major_category:
            categories = [cat.strip() for cat in major_category.split(',')]
            major_category = categories[0]
            print(f"[Audio] Multiple categories detected, using first: {major_category}")
        
        # Every clip change with a valid category should trigger new audio selection
        # This ensures audio changes even when consecutive clips have the same category
        if major_category != self.current_audio_category:
            print(f"[Audio] Category change: {self.current_audio_category} -> {major_category}")
        else:
            print(f"[Audio] Clip change (category: {major_category})")
        
        # Fade out current audio if playing
        if self.audio_controller.is_playing():
            self.audio_controller.fade_out()
            time.sleep(0.5)  # Brief pause between tracks
        
        # Get the next track for this category
        next_track = self.cache_manager.get_next_audio_track(major_category)
        
        if next_track:
            # Play the new track
            success = self.audio_controller.play_audio(next_track, loop=True)
            
            if success:
                self.current_audio_category = major_category
                self.cache_manager.update_last_played(major_category, next_track)
                print(f"[Audio] Now playing: {next_track} (category: {major_category})")
            else:
                print(f"[Audio] Failed to play: {next_track}")
        else:
            print(f"[Audio] No audio tracks available for category: {major_category}")
    
    def run(self):
        """Main engine loop."""
        if not self.connect_to_sos():
            print("[Engine] ERROR: Failed to connect to SOS")
            return
        
        print("[Engine] Monitoring for clip changes...\n")
        
        last_clip_number = -1
        
        try:
            while self.running:
                # 1. Process Qt Events
                self.qapp.processEvents()
                self.overlay_manager.process_events()
                
                # 2. Get SOS Status
                clip_number, clip_name = self.get_current_clip_info()
                
                # 3. Handle Clip Logic
                if clip_number and clip_name != self.last_clip_name:
                    print(f"\n[Clip {clip_number}] {clip_name}")
                    self.last_clip_name = clip_name
                    self.navigate_to_clip(clip_name or "")
                    self.update_nowPlaying(clip_number)
                    
                    # Update Overlay State
                    metadata = self.cache_manager.get(clip_name) if clip_name else {}
                    self.current_duration = float(metadata.get('duration', 180.0)) if metadata else 180.0
                    
                    # Determine visibility
                    is_credits = "credits" in (clip_name or "").lower()

                    is_translated = str(metadata.get('translated-movie', '')).lower() == 'true'
                    print(f"[Engine] is_credits: {is_credits}, is_translated: {is_translated}")
                    
                    # Manage audio playback based on clip type
                    self.manage_audio(clip_name, is_credits, is_translated)
                    
                    if is_credits:
                        self.overlay_manager.hide_all()
                    elif is_translated:
                        # print(f"[Subtitles] Translated clip detected: {clip_name}")
                        local_meta = metadata.copy()
                        if metadata.get('caption'):
                            path1 = self.cache_manager.fetch_subtitle_file(metadata['caption'])
                            if path1: local_meta['caption'] = path1
                        if metadata.get('caption2'):
                            path2 = self.cache_manager.fetch_subtitle_file(metadata['caption2'])
                            if path2: local_meta['caption2'] = path2
                            
                        self.overlay_manager.show_subtitles_and_progress()
                        self.subtitle_manager.load_subtitles_for_clip(local_meta)
                        
                        # Update titles from CSV
                        spanish_title, english_title = self.cache_manager.get_clip_titles(clip_name)
                        print(f"[Engine] Title Logic - Name: '{clip_name}', EN: '{english_title}', ES: '{spanish_title}'")
                        # Rule 2a: English Title above Col 1 (Left), Spanish Title above Col 2 (Right)
                        self.overlay_manager.update_titles(english_title, spanish_title)
                    else:
                        self.overlay_manager.hide_all() # Hide titles if not translated
                        self.overlay_manager.show_progress_only()
                
                # 4. Update Progress & Subtitles
                current_frame = self.get_frame_number()
                fps = self.get_frame_rate()
                current_time = current_frame / fps if fps > 0 else 0
                
                # Push updates to UI
                self.overlay_manager.update_progress(current_time, self.current_duration)
                
                # Subtitles (if enabled, manager will verify time and update overlay)
                if self.overlay_manager.mode == "SUBTITLES_AND_PROGRESS":
                    self.subtitle_manager.update(current_time)
                
                # Process Qt events for smooth UI
                self.overlay_manager.process_events()

                time.sleep(0.05) # 20 FPS for smoother updates
                
        except KeyboardInterrupt:
            print("\n[Engine] Keyboard interrupt")
        except Exception as e:
            print(f"[Engine] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()
    
    def _cleanup(self):
        """Internal cleanup method called by stop() or atexit."""
        if not self.running:
            return  # Already cleaned up
            
        self.running = False
        
        # Close overlays
        try:
            if hasattr(self, 'overlay_manager'):
                self.overlay_manager.hide_all()
        except Exception as e:
            print(f"[Engine] Error closing overlays: {e}")
        
        # Stop audio
        try:
            if self.audio_controller and hasattr(self.audio_controller, 'is_playing'):
                if self.audio_controller.is_playing():
                    self.audio_controller.fade_out()
        except Exception as e:
            print(f"[Engine] Error stopping audio: {e}")
        
        # Close socket
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                print(f"[Engine] Error closing socket: {e}")
        
        # Close LibreOffice
        try:
            if self.pp and hasattr(self.pp, 'close'):
                print("[Engine] Closing LibreOffice...")
                self.pp.close()
        except Exception as e:
            print(f"[Engine] Error closing LibreOffice: {e}")
    
    def stop(self):
        """Stop the engine and clean up resources."""
        print("[Engine] Stopping...")
        self._cleanup()
        print("[Engine] Stopped")
