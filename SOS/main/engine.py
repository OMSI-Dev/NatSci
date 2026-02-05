"""
SOS2 Engine
Connects to SOS server and controls LibreOffice Impress via CacheManager lookups.
"""

import socket
import time
import socket
import time
import sys
from PyQt5.QtWidgets import QApplication
from subtitles import SubtitleManager, SubtitleOverlay
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
        self.progress_overlay = ProgressBarOverlay(
            position='bottom',
            opacity=0.85,
            progress_bar_color='#ffffff',
            progress_bar_bg_color='#000000',
            progress_bar_bg_opacity=155,
            progress_bar_height=12
        )
        
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


SOS_IP = "10.10.51.98"
SOS_PORT = 2468

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

class SimplePPEngine:
    """
    Optimized Engine:
    - Connects to SOS server
    - Gets clip NUMBER from SOS
    - Gets clip NAME from local CacheManager (no socket usage)
    - Navigates LibreOffice
    """
    
    def __init__(self, pp, slide_dictionary, cache_manager):
        """
        Initialize the engine.
        
        Args:
            pp: LibreOffice Impress controller object
            slide_dictionary: Dict mapping clip names to slide numbers
            cache_manager: Initialized CacheManager instance
        """
        self.pp = pp
        self.slide_dictionary = slide_dictionary
        self.cache_manager = cache_manager
        self.running = True
        self.current_slide = -1
        self.sock = None
        
        print(f"[Engine] Initialized with CacheManager")

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
            print(f"[Engine] Navigating to Slide {target_slide} for '{clip_name}'")
            self.pp.goto(target_slide)
            self.current_slide = target_slide
    
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
                    
                    # Update Overlay State
                    metadata = self.cache_manager.get(clip_name) if clip_name else {}
                    self.current_duration = float(metadata.get('duration', 180.0)) if metadata else 180.0
                    
                    # Determine visibility
                    is_credits = "credits" in (clip_name or "").lower()

                    #this is not correct fetching from metadata
                    is_translated = str(metadata.get('translated-movie', '')).lower() == 'true'
                    print(f"[Engine] is_credits: {is_credits}, is_translated: {is_translated}")
                    
                    if is_credits:
                        self.overlay_manager.hide_all()
                    elif is_translated:
                        # Ensure subtitles are fetched/cached locally and use local path
                        print(f"[Subtitles] Translated clip detected: {clip_name}")
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
    
    def stop(self):
        """Stop the engine."""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        print("[Engine] Stopped")
