"""
SOS2 Batch Engine - Batch1_2026 Specialized Controller
Handles movieset credits for clips 1 and 6 with specialized transitions.

Special behavior:
- Clips 1 and 6 are moviesets with credit slides shown first
- Fadeout/fadein transitions with delays for credit display
- Autoplay toggling during transitions
- Dual-slide navigation (credit slide → subtitle slide)
- Subtitle and progress bar overlays for all clips
"""

import socket
import time
import sys
import os
import re
import threading
from typing import Dict, List, Optional
from PyQt5.QtWidgets import QApplication
from overlay_progressBar import ProgressBarOverlay
from overlay_subtitles import SubtitleOverlay

SOS_IP = "10.10.51.98"
SOS_PORT = 2468

# ============================================================================
# CONFIGURATION - Modify these values to adjust timing
# ============================================================================
FADE_DURATION = 2.0          # Duration of fade in/out effects (seconds)
CREDIT_DELAY = 5.0           # Duration to display credits before continuing (seconds)
# ============================================================================


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


class Batch1Engine:
    """
    Specialized engine for Batch1_2026 playlist.
    
    Special handling:
    - Clips 1 and 6: Moviesets with credit slides
      * Fadeout before transition (from clips 10 and 5)
      * Show credit slide during black screen
      * Delay for credits display
      * Fadein and play clip
      * Navigate to subtitle slide
      * Spawn overlays
    - All other clips: Normal playback with overlays
    """
    
    def __init__(self, pp, slide_dictionary, playlist_metadata):
        """
        Initialize the Batch1 specialized engine.
        
        Args:
            pp: LibreOffice Impress controller object
            slide_dictionary: Dict mapping clip names to slide numbers (lists)
            playlist_metadata: Playlist metadata from SOS server
        """
        self.pp = pp
        self.slide_dictionary = slide_dictionary
        self.playlist_metadata = playlist_metadata
        self.running = True
        self.current_slide = -1
        self.sock = None
        
        # Track current clip for state management
        self.current_clip_number = 0
        self.current_clip_name = None
        
        # Movieset configuration (clips 1 and 6 require special handling)
        self.movieset_clips = {1, 6}
        self.transition_clips = {5: 6, 10: 1}  # clip 5→6, clip 10→1
        
        # Timer for movieset duration tracking
        self.movieset_timer = None
        
        # Initialize PyQt5 application for overlays
        if not QApplication.instance():
            self.qapp = QApplication(sys.argv)
        else:
            self.qapp = QApplication.instance()
        
        # Create overlay instances (from overlay_init.py configuration)
        from overlay_init import (
            PROGRESS_POSITION, PROGRESS_OPACITY, PROGRESS_CONTAINER_MARGIN_LEFT,
            PROGRESS_CONTAINER_MARGIN_RIGHT, PROGRESS_CONTAINER_MARGIN_BOTTOM,
            PROGRESS_BAR_HEIGHT, PROGRESS_BAR_COLOR, PROGRESS_BAR_BG_COLOR,
            PROGRESS_BAR_BG_OPACITY, PROGRESS_BAR_BORDER_RADIUS, PROGRESS_BAR_BG_BLUR,
            PROGRESS_BAR_BG_WIDTH_EXTEND, PROGRESS_BAR_BG_HEIGHT_EXTEND,
            TIMESTAMP_DISTANCE, TIMESTAMP_FONT, TIMESTAMP_FONT_SIZE,
            TIMESTAMP_CONTAINER_PADDING_LEFT, TIMESTAMP_CONTAINER_PADDING_RIGHT,
            SUBTITLE_POSITION, SUBTITLE_OPACITY, SUBTITLE_Y_OFFSET,
            PARENT_CONTAINER_WIDTH_PERCENT, PARENT_CONTAINER_HEIGHT,
            COLUMN_HORIZONTAL_PADDING, COLUMN_TOP_PADDING, COLUMN_BOTTOM_PADDING,
            COLUMN_HEIGHT_PERCENT, LEFT_COLUMN_WIDTH_PERCENT, COLUMN_SPACING,
            SUBTITLE_FONT_SIZE, SUBTITLE_FONT_FAMILY, SUBTITLE_TEXT_COLOR,
            SUBTITLE_BG_OPACITY, SUBTITLE_ALIGNMENT, SUBTITLE_FONT_BOLD,
            SUBTITLE_TOP_SPACING, TEXT_PADDING, SHOW_TITLE_ROW, LEFT_TITLE,
            RIGHT_TITLE, TITLE_HEIGHT, TITLE_FONT_SIZE, TITLE_FONT_FAMILY,
            TITLE_FONT_BOLD, LEFT_TITLE_COLOR, RIGHT_TITLE_COLOR,
            TITLE_BG_OPACITY, TITLE_ALIGNMENT, TITLE_TOP_SPACING,
            LEFT_TITLE_PADDING, RIGHT_TITLE_PADDING, SHOW_DEBUG_BORDERS
        )
        
        self.progress_overlay = ProgressBarOverlay(
            position=PROGRESS_POSITION, opacity=PROGRESS_OPACITY,
            container_margin_left=PROGRESS_CONTAINER_MARGIN_LEFT,
            container_margin_right=PROGRESS_CONTAINER_MARGIN_RIGHT,
            container_margin_bottom=PROGRESS_CONTAINER_MARGIN_BOTTOM,
            progress_bar_height=PROGRESS_BAR_HEIGHT,
            progress_bar_color=PROGRESS_BAR_COLOR,
            progress_bar_bg_color=PROGRESS_BAR_BG_COLOR,
            progress_bar_bg_opacity=PROGRESS_BAR_BG_OPACITY,
            progress_bar_border_radius=PROGRESS_BAR_BORDER_RADIUS,
            progress_bar_bg_blur=PROGRESS_BAR_BG_BLUR,
            progress_bar_bg_width_extend=PROGRESS_BAR_BG_WIDTH_EXTEND,
            progress_bar_bg_height_extend=PROGRESS_BAR_BG_HEIGHT_EXTEND,
            timestamp_distance=TIMESTAMP_DISTANCE,
            timestamp_font=TIMESTAMP_FONT,
            timestamp_font_size=TIMESTAMP_FONT_SIZE,
            timestamp_container_padding_left=TIMESTAMP_CONTAINER_PADDING_LEFT,
            timestamp_container_padding_right=TIMESTAMP_CONTAINER_PADDING_RIGHT
        )
        
        self.subtitle_overlay = SubtitleOverlay(
            position=SUBTITLE_POSITION, opacity=SUBTITLE_OPACITY,
            y_offset=SUBTITLE_Y_OFFSET,
            parent_container_width_percent=PARENT_CONTAINER_WIDTH_PERCENT,
            parent_container_height=PARENT_CONTAINER_HEIGHT,
            column_horizontal_padding=COLUMN_HORIZONTAL_PADDING,
            column_top_padding=COLUMN_TOP_PADDING,
            column_bottom_padding=COLUMN_BOTTOM_PADDING,
            column_height_percent=COLUMN_HEIGHT_PERCENT,
            left_column_width_percent=LEFT_COLUMN_WIDTH_PERCENT,
            column_spacing=COLUMN_SPACING,
            subtitle_font_size=SUBTITLE_FONT_SIZE,
            subtitle_font_family=SUBTITLE_FONT_FAMILY,
            subtitle_text_color=SUBTITLE_TEXT_COLOR,
            subtitle_bg_opacity=SUBTITLE_BG_OPACITY,
            subtitle_alignment=SUBTITLE_ALIGNMENT,
            subtitle_font_bold=SUBTITLE_FONT_BOLD,
            subtitle_top_spacing=SUBTITLE_TOP_SPACING,
            text_padding=TEXT_PADDING,
            show_title_row=SHOW_TITLE_ROW,
            left_title=LEFT_TITLE,
            right_title=RIGHT_TITLE,
            title_height=TITLE_HEIGHT,
            title_font_size=TITLE_FONT_SIZE,
            title_font_family=TITLE_FONT_FAMILY,
            title_font_bold=TITLE_FONT_BOLD,
            left_title_color=LEFT_TITLE_COLOR,
            right_title_color=RIGHT_TITLE_COLOR,
            title_bg_opacity=TITLE_BG_OPACITY,
            title_alignment=TITLE_ALIGNMENT,
            title_top_spacing=TITLE_TOP_SPACING,
            left_title_padding=LEFT_TITLE_PADDING,
            right_title_padding=RIGHT_TITLE_PADDING,
            show_debug_borders=SHOW_DEBUG_BORDERS
        )
        
        # Subtitle data (will be loaded from .srt files)
        self.subtitle_cache_dir = os.path.join(os.path.dirname(__file__), 'subtitle_cache')
        os.makedirs(self.subtitle_cache_dir, exist_ok=True)
        
        print(f"[Batch1Engine] Initialized with {len(slide_dictionary)} clip mappings")
        if playlist_metadata:
            print(f"[Batch1Engine] Playlist: {playlist_metadata.get('name', 'Unknown')}")
    
    def connect_to_sos(self, timeout=4):
        """
        Connect to SOS server.
        
        Args:
            timeout: Socket timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            
            self.sock.connect((SOS_IP, SOS_PORT))
            print(f"[Batch1Engine] Connected to SOS at {SOS_IP}:{SOS_PORT}")
            
            # Send enable handshake
            self.sock.sendall(b'enable\n')
            data = self.sock.recv(1024)
            
            return True
                
        except socket.error as e:
            print(f"[Batch1Engine] Failed to connect to SOS: {e}")
            return False
        except Exception as e:
            print(f"[Batch1Engine] Error during SOS connection: {e}")
            return False
    
    def next_clip(self):
        """Skip to the next clip in the playlist."""
        if not self.sock:
            return False
        
        try:
            self.sock.sendall(b'next_clip\n')
            time.sleep(0.2)
            
            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            return True
            
        except socket.error as e:
            print(f"[Batch1Engine] Error sending next_clip: {e}")
            return False
    
    def prev_clip(self):
        """Go back to the previous clip in the playlist."""
        if not self.sock:
            return False
        
        try:
            self.sock.sendall(b'prev_clip\n')
            time.sleep(0.2)
            
            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            return True
            
        except socket.error as e:
            print(f"[Batch1Engine] Error sending prev_clip: {e}")
            return False
    
    def play_clip(self, clip_number):
        """
        Play a specific clip by number.
        Clears the sphere, then loads and plays the given clip_number.
        
        Args:
            clip_number: Clip number to play (1-based index)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sock:
            return False
        
        try:
            cmd = f"play {clip_number}\n".encode('utf-8')
            self.sock.sendall(cmd)
            time.sleep(0.1)
            return True
        except socket.error as e:
            print(f"[Batch1Engine] Error sending play command: {e}")
            return False
    
    def fadeout(self, duration=2.0):
        """
        Trigger fade out effect.
        
        Args:
            duration: Fade duration in seconds
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sock:
            return False
        
        try:
            cmd = f"fadeout {duration}\n".encode('utf-8')
            self.sock.sendall(cmd)
            time.sleep(0.1)
            return True
        except socket.error as e:
            print(f"[Batch1Engine] Error sending fadeout: {e}")
            return False
    
    def fadein(self, duration=2.0):
        """
        Trigger fade in effect.
        
        Args:
            duration: Fade duration in seconds
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sock:
            return False
        
        try:
            cmd = f"fadein {duration}\n".encode('utf-8')
            self.sock.sendall(cmd)
            time.sleep(0.1)
            return True
        except socket.error as e:
            print(f"[Batch1Engine] Error sending fadein: {e}")
            return False
    
    def set_auto_presentation_mode(self, enabled):
        """
        Toggle auto presentation mode on/off.
        
        Args:
            enabled: True to enable (1), False to disable (0)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sock:
            return False
        
        try:
            value = 1 if enabled else 0
            cmd = f"set_auto_presentation_mode {value}\n".encode('utf-8')
            self.sock.sendall(cmd)
            time.sleep(0.1)
            return True
        except socket.error as e:
            print(f"[Batch1Engine] Error setting auto presentation mode: {e}")
            return False
    
    def get_current_clip_info(self):
        """
        Get the currently playing clip name and number from SOS.
        Uses cached playlist metadata for efficiency (matches SOS2/engine.py pattern).
        
        Returns:
            tuple: (clip_number, clip_name) or (None, None) on failure
        """
        if not self.sock:
            return None, None
        
        try:
            # Step 1: Get current clip number
            self.sock.sendall(b'get_clip_number\n')
            data = self.sock.recv(1024)
            clip_number_str = data.decode('utf-8', 'ignore').strip()
            
            if not clip_number_str or not clip_number_str.isdigit():
                return None, None
            
            clip_number = int(clip_number_str)
            
            # Step 2: Look up clip name from cached playlist metadata
            # This matches SOS2/engine.py efficiency approach
            clip_name = None
            if self.playlist_metadata and 'clips' in self.playlist_metadata:
                clips = self.playlist_metadata['clips']
                if 0 < clip_number <= len(clips):
                    clip_name = clips[clip_number - 1].get('name', '')
            
            return (clip_number, clip_name) if clip_name else (None, None)
            
        except socket.timeout:
            return None, None
        except socket.error:
            return None, None
        except Exception:
            return None, None
        except Exception:
            return None, None
    
    def get_clip_duration(self, clip_name):
        """
        Get clip duration from playlist metadata.
        
        Args:
            clip_name: Name of the clip
            
        Returns:
            float: Duration in seconds or None
        """
        if not self.playlist_metadata or 'clips' not in self.playlist_metadata:
            return None
        
        for clip in self.playlist_metadata['clips']:
            if clip.get('name') == clip_name or clip.get('english_title') == clip_name:
                # Check for 'duration' field in metadata
                duration = clip.get('duration', None)
                if duration:
                    return float(duration)
        
        return None
    
    def start_movieset_timer(self, clip_name, clip_number):
        """
        Start a timer for movieset clip duration.
        When timer expires, re-enable autoplay to advance to next clip.
        
        Args:
            clip_name: Name of the movieset clip
            clip_number: Clip number
        """
        # Cancel any existing timer
        if self.movieset_timer:
            self.movieset_timer.cancel()
        
        # Get clip duration from metadata
        duration = self.get_clip_duration(clip_name)
        
        if not duration:
            print(f"[Batch1Engine] WARNING: No duration found for movieset '{clip_name}'")
            print(f"[Batch1Engine] Cannot start timer - autoplay will remain OFF")
            return
        
        print(f"[Batch1Engine] Starting {duration}s timer for movieset clip {clip_number}")
        
        # Create timer callback
        def timer_callback():
            print(f"\n[Batch1Engine] === MOVIESET TIMER EXPIRED ({duration}s) ===")
            print(f"[Batch1Engine] Re-enabling autoplay to advance from clip {clip_number}")
            self.set_auto_presentation_mode(enabled=True)
            print(f"[Batch1Engine] Autoplay ON - system will advance to next clip\n")
        
        # Start timer
        self.movieset_timer = threading.Timer(duration, timer_callback)
        self.movieset_timer.daemon = True  # Daemon thread will exit when main program exits
        self.movieset_timer.start()
    
    def load_subtitles_for_clip(self, clip_name):
        """
        Load subtitle files for a clip from cached metadata.
        Uses caption paths from playlist_metadata that were cached during initialization.
        
        Args:
            clip_name: Name of the clip
            
        Returns:
            tuple: (english_subtitles, spanish_subtitles) as lists of subtitle dicts
        """
        if not self.playlist_metadata or 'clips' not in self.playlist_metadata:
            return [], []
        
        # Find the clip in metadata
        clip_metadata = None
        for clip in self.playlist_metadata['clips']:
            if clip.get('name') == clip_name or clip.get('english_title') == clip_name:
                clip_metadata = clip
                break
        
        if not clip_metadata:
            return [], []
        
        # Get cached local paths for subtitles
        caption_local = clip_metadata.get('caption_local', '')
        caption2_local = clip_metadata.get('caption2_local', '')
        
        english_subs = self.parse_srt_file(caption_local) if caption_local and os.path.exists(caption_local) else []
        spanish_subs = self.parse_srt_file(caption2_local) if caption2_local and os.path.exists(caption2_local) else []
        
        return english_subs, spanish_subs
    
    def parse_srt_file(self, filepath):
        """
        Parse an SRT subtitle file (from 'main' folder subtitle logic).
        
        Args:
            filepath: Path to the .srt file
            
        Returns:
            list: List of subtitle dictionaries
        """
        if not os.path.exists(filepath):
            return []
        
        subtitles = []
        
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            blocks = re.split(r'\n\s*\n', content.strip())
            
            for block in blocks:
                lines = block.strip().split('\n')
                
                if len(lines) < 3:
                    continue
                
                try:
                    index = int(lines[0].strip())
                    timestamp_line = lines[1].strip()
                    match = re.match(r'(\S+)\s*-->\s*(\S+)', timestamp_line)
                    
                    if not match:
                        continue
                    
                    start_time = self.srt_time_to_seconds(match.group(1))
                    end_time = self.srt_time_to_seconds(match.group(2))
                    text = '\n'.join(lines[2:])
                    
                    subtitles.append({
                        'index': index,
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text
                    })
                    
                except (ValueError, IndexError):
                    continue
            
            return subtitles
            
        except Exception as e:
            print(f"[Batch1Engine] Error reading subtitle file {filepath}: {e}")
            return []
    
    def srt_time_to_seconds(self, timestamp):
        """Convert SRT timestamp to seconds (e.g., '00:02:38,400' -> 158.4)."""
        time_part, ms_part = timestamp.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return (h * 3600) + (m * 60) + s + (ms / 1000.0)
    
    def navigate_to_clip(self, clip_name, slide_index=0):
        """
        Navigate to the slide(s) associated with the given clip name.
        
        Args:
            clip_name: Name of the clip to navigate to
            slide_index: Index in the slide list (0=first slide, 1=second slide)
        """
        if clip_name not in self.slide_dictionary:
            print(f"[Batch1Engine] Warning: No slide mapping for '{clip_name}'")
            return
        
        slide_numbers = self.slide_dictionary[clip_name]
        
        if not slide_numbers or slide_index >= len(slide_numbers):
            return
        
        # Navigate to the specified slide in the list
        target_slide = slide_numbers[slide_index]
        
        if target_slide != self.current_slide:
            self.pp.goto(target_slide)
            self.current_slide = target_slide
            print(f"[Batch1Engine] Navigated to slide {target_slide} (index {slide_index}) for '{clip_name}'")
    
    def handle_movieset_transition(self, target_clip_number, target_clip_name):
        """
        Handle special transition to movieset clips (1 and 6).
        
        Sequence:
        1. Fadeout (on globe)
        2. Navigate to first slide (credit slide)
        3. Delay for credits
        4. Turn OFF autoplay
        5. Fadein (on globe)
        6. Play the clip (on globe)
        7. Wait briefly, then navigate to second slide (subtitle slide)
        8. Spawn subtitle and progress bar overlays
        9. Turn autoplay back ON
        
        Args:
            target_clip_number: Clip number to transition to (1 or 6)
            target_clip_name: Name of the target clip
        """
        print(f"\n[Batch1Engine] === MOVIESET TRANSITION TO CLIP {target_clip_number} ===")
        
        # Step 1: Fadeout on globe
        print(f"[Batch1Engine] Step 1: Fading out (duration: {FADE_DURATION}s)")
        self.fadeout(duration=FADE_DURATION)
        time.sleep(FADE_DURATION + 0.5)  # Wait for fadeout to complete
        
        # Step 2: Navigate to first slide (credit slide) on monitors
        print(f"[Batch1Engine] Step 2: Showing credit slide")
        self.navigate_to_clip(target_clip_name, slide_index=0)
        
        # Step 3: Delay for credits
        print(f"[Batch1Engine] Step 3: Displaying credits for {CREDIT_DELAY}s")
        time.sleep(CREDIT_DELAY)
        
        # Step 4: Turn OFF autoplay
        print(f"[Batch1Engine] Step 4: Disabling autoplay")
        self.set_auto_presentation_mode(enabled=False)
        time.sleep(0.2)
        
        # Step 5: Fadein on globe
        print(f"[Batch1Engine] Step 5: Fading in (duration: {FADE_DURATION}s)")
        self.fadein(duration=FADE_DURATION)
        time.sleep(0.5)
        
        # Step 6: Play the clip on globe
        print(f"[Batch1Engine] Step 6: Playing clip {target_clip_number} on globe")
        self.play_clip(target_clip_number)
        time.sleep(1.0)  # Wait for clip to start playing
        
        # Step 7: Navigate to second slide (subtitle slide) on monitors
        print(f"[Batch1Engine] Step 7: Showing subtitle slide")
        self.navigate_to_clip(target_clip_name, slide_index=1)
        time.sleep(0.5)
        
        # Step 8: Spawn subtitle and progress bar overlays
        print(f"[Batch1Engine] Step 8: Spawning overlays")
        self.spawn_overlays(target_clip_name)
        
        # Step 9: Start timer based on clip duration
        # When timer expires, autoplay will be re-enabled to advance to next clip
        print(f"[Batch1Engine] Step 9: Starting duration timer")
        self.start_movieset_timer(target_clip_name, target_clip_number)
        
        print(f"[Batch1Engine] === MOVIESET TRANSITION COMPLETE ===\n")
    
    def spawn_overlays(self, clip_name):
        """
        Spawn subtitle and progress bar overlays for a clip.
        
        Args:
            clip_name: Name of the clip
        """
        # Load subtitles
        english_subs, spanish_subs = self.load_subtitles_for_clip(clip_name)
        
        if english_subs or spanish_subs:
            print(f"[Batch1Engine] Loaded subtitles: {len(english_subs)} EN, {len(spanish_subs)} ES")
            # TODO: Start subtitle update timer
            self.subtitle_overlay.show()
        else:
            print(f"[Batch1Engine] No subtitles found for '{clip_name}'")
        
        # Get clip duration for progress bar
        duration = self.get_clip_duration(clip_name)
        if duration:
            print(f"[Batch1Engine] Clip duration: {duration}s")
            self.progress_overlay.set_duration(duration)
            self.progress_overlay.show()
        else:
            print(f"[Batch1Engine] No duration found for '{clip_name}'")
    
    def hide_overlays(self):
        """Hide all overlays."""
        self.subtitle_overlay.hide()
        self.progress_overlay.hide()
    
    def handle_clip_behavior(self, clip_number, clip_name, previous_clip_number=None):
        """
        Execute specialized behavior for specific clips.
        
        Args:
            clip_number: Current clip number (1-10)
            clip_name: Name of the current clip
            previous_clip_number: Previous clip number (for detecting transitions)
        """
        # Re-enable autoplay when transitioning FROM a movieset clip to a normal clip
        if previous_clip_number in self.movieset_clips and clip_number not in self.movieset_clips:
            print(f"[Batch1Engine] Exiting movieset clip {previous_clip_number} → re-enabling autoplay")
            self.set_auto_presentation_mode(enabled=True)
        
        # Check if this is a transition clip (5 or 10) leading to a movieset
        if clip_number in self.transition_clips:
            target_clip = self.transition_clips[clip_number]
            print(f"[Batch1Engine] Detected transition clip {clip_number} → will transition to clip {target_clip}")
            # Note: Transition will be handled when clip changes
            # For now, show the slide for this transition clip
            self.navigate_to_clip(clip_name, slide_index=0)
            self.spawn_overlays(clip_name)
        
        # For moviesets (1 and 6) that aren't part of a transition, just navigate
        elif clip_number in self.movieset_clips:
            print(f"[Batch1Engine] Movieset clip {clip_number} (not from transition): showing first slide")
            self.navigate_to_clip(clip_name, slide_index=0)
            # Don't spawn overlays - they should have been spawned during transition
        
        # For all other clips, spawn overlays normally
        else:
            print(f"[Batch1Engine] Normal clip {clip_number}: showing slide and spawning overlays")
            self.navigate_to_clip(clip_name, slide_index=0)
            self.spawn_overlays(clip_name)
    
    def initialize_on_movieset(self, clip_number, clip_name):
        """
        Handle initialization when engine starts on a movieset clip (1 or 6).
        Follows same sequence as movieset transition but without initial fadeout.
        """
        print(f"\n[Batch1Engine] === INITIALIZING ON MOVIESET CLIP {clip_number} ===")
        
        # Step 1: Navigate to first slide (credit slide) on monitors
        print(f"[Batch1Engine] Step 1: Showing credit slide")
        self.navigate_to_clip(clip_name, slide_index=0)
        
        # Step 2: Delay for credits
        print(f"[Batch1Engine] Step 2: Displaying credits for {CREDIT_DELAY}s")
        time.sleep(CREDIT_DELAY)
        
        # Step 3: Turn OFF autoplay
        print(f"[Batch1Engine] Step 3: Disabling autoplay")
        self.set_auto_presentation_mode(enabled=False)
        time.sleep(0.2)
        
        # Step 4: Fadein on globe
        print(f"[Batch1Engine] Step 4: Fading in (duration: {FADE_DURATION}s)")
        self.fadein(duration=FADE_DURATION)
        time.sleep(0.5)
        
        # Step 5: Play the clip on globe
        print(f"[Batch1Engine] Step 5: Playing clip {clip_number} on globe")
        self.play_clip(clip_number)
        time.sleep(1.0)  # Wait for clip to start playing
        
        # Step 6: Navigate to second slide (subtitle slide) on monitors
        print(f"[Batch1Engine] Step 6: Showing subtitle slide")
        self.navigate_to_clip(clip_name, slide_index=1)
        time.sleep(0.5)
        
        # Step 7: Spawn subtitle and progress bar overlays
        print(f"[Batch1Engine] Step 7: Spawning overlays")
        self.spawn_overlays(clip_name)
        
        # Step 8: Start timer based on clip duration
        # When timer expires, autoplay will be re-enabled to advance to next clip
        print(f"[Batch1Engine] Step 8: Starting duration timer")
        self.start_movieset_timer(clip_name, clip_number)
        
        print(f"[Batch1Engine] === INITIALIZATION COMPLETE ===\n")
    
    def run(self):
        """Main batch engine loop - monitors SOS and executes specialized behaviors."""
        if not self.connect_to_sos():
            print("[Batch1Engine] ERROR: Failed to connect to SOS")
            return
        
        print("[Batch1Engine] Monitoring for clip changes...\n")
        
        last_clip_number = None
        first_iteration = True
        
        try:
            while self.running:
                clip_number, clip_name = self.get_current_clip_info()
                
                if clip_number and clip_name and clip_number != last_clip_number:
                    print(f"\n[Clip {clip_number}] {clip_name}")
                    
                    # Update tracking
                    self.current_clip_number = clip_number
                    self.current_clip_name = clip_name
                    
                    # Handle first iteration - check if starting on a movieset
                    if first_iteration and clip_number in self.movieset_clips:
                        self.initialize_on_movieset(clip_number, clip_name)
                        first_iteration = False
                        last_clip_number = clip_number
                        continue
                    
                    first_iteration = False
                    
                    # Check if previous clip was a transition clip
                    if last_clip_number in self.transition_clips:
                        target_movieset_clip = self.transition_clips[last_clip_number]
                        if clip_number == target_movieset_clip:
                            # Execute movieset transition
                            self.handle_movieset_transition(clip_number, clip_name)
                        else:
                            # Normal clip behavior
                            self.handle_clip_behavior(clip_number, clip_name, last_clip_number)
                    else:
                        # Normal clip behavior
                        self.handle_clip_behavior(clip_number, clip_name, last_clip_number)
                    
                    last_clip_number = clip_number
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n[Batch1Engine] Keyboard interrupt detected")
        except Exception as e:
            print(f"[Batch1Engine] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()
    
    def stop(self):
        """Stop the engine and cleanup connections."""
        self.running = False
        
        # Cancel any running movieset timer
        if self.movieset_timer:
            self.movieset_timer.cancel()
            self.movieset_timer = None
        
        # Hide overlays
        self.hide_overlays()
        
        # Close socket
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            finally:
                self.sock = None
        
        print("[Batch1Engine] Stopped")