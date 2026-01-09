"""
SRT Subtitle Parser and Sync Module
Handles parsing .srt files and finding subtitles based on playback time.
"""

import re
import os


def srt_time_to_seconds(timestamp):
    """
    Convert SRT timestamp to seconds.
    
    Args:
        timestamp: SRT timestamp string (e.g., "00:02:38,400")
        
    Returns:
        float: Time in seconds (e.g., 158.4)
    """
    # Split time and milliseconds
    time_part, ms_part = timestamp.split(',')
    h, m, s = map(int, time_part.split(':'))
    ms = int(ms_part)
    
    total_seconds = (h * 3600) + (m * 60) + s + (ms / 1000.0)
    return total_seconds


def parse_srt_file(filepath):
    """
    Parse an SRT subtitle file.
    
    Args:
        filepath: Path to the .srt file
        
    Returns:
        list: List of subtitle dictionaries with keys:
              - index: Subtitle number
              - start_time: Start time in seconds
              - end_time: End time in seconds
              - text: Subtitle text (can be multi-line)
    """
    if not os.path.exists(filepath):
        print(f"Warning: Subtitle file not found: {filepath}")
        return []
    
    subtitles = []
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Split by double newlines to separate subtitle blocks
        # SRT format: index, timestamp, text, blank line
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            
            if len(lines) < 3:
                continue  # Invalid block
            
            try:
                # First line: index
                index = int(lines[0].strip())
                
                # Second line: timestamp (e.g., "00:00:05,000 --> 00:00:08,500")
                timestamp_line = lines[1].strip()
                match = re.match(r'(\S+)\s*-->\s*(\S+)', timestamp_line)
                
                if not match:
                    print(f"Warning: Invalid timestamp format in block {index}")
                    continue
                
                start_timestamp = match.group(1)
                end_timestamp = match.group(2)
                
                start_time = srt_time_to_seconds(start_timestamp)
                end_time = srt_time_to_seconds(end_timestamp)
                
                # Remaining lines: subtitle text
                text = '\n'.join(lines[2:])
                
                subtitles.append({
                    'index': index,
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text
                })
                
            except (ValueError, IndexError) as e:
                print(f"Warning: Error parsing subtitle block: {e}")
                continue
        
        print(f"[Success] Yippee ~ Loaded {len(subtitles)} subtitles")
        return subtitles
        
    except Exception as e:
        print(f"Error reading subtitle file {filepath}: {e}")
        return []


# Track accumulated subtitles across calls
_subtitle_accumulator = []
_last_subtitle_index = -1

def find_subtitle_at_time(subtitles, time_seconds, max_chars=200):
    """
    Find and accumulate subtitles over time until line is full, then clear and continue.
    
    Args:
        subtitles: List of subtitle dictionaries from parse_srt_file()
        time_seconds: Current playback time in seconds
        max_chars: Maximum characters before clearing (roughly screen width)
        
    Returns:
        str: Accumulated subtitle text, or empty string if none
    """
    global _subtitle_accumulator, _last_subtitle_index
    
    # Find current active subtitle
    current_sub = None
    for sub in subtitles:
        if sub['start_time'] <= time_seconds <= sub['end_time']:
            current_sub = sub
            break
    
    # If no subtitle is active, keep showing accumulated text
    if not current_sub:
        return " ".join(_subtitle_accumulator)
    
    # If this is a new subtitle we haven't seen yet
    if current_sub['index'] != _last_subtitle_index:
        _last_subtitle_index = current_sub['index']
        
        # Clean subtitle text (remove newlines)
        new_text = current_sub['text'].replace('\n', ' ')
        
        # Check if adding this would exceed max_chars
        current_length = sum(len(text) for text in _subtitle_accumulator)
        
        if current_length + len(new_text) > max_chars:
            # Clear and start fresh with new subtitle
            _subtitle_accumulator = [new_text]
        else:
            # Add to accumulator
            _subtitle_accumulator.append(new_text)
    
    # Return accumulated text joined with spaces
    return " ".join(_subtitle_accumulator)


def get_duration_from_subtitles(subtitles):
    """
    Get the total duration from the last subtitle's end time.
    
    Args:
        subtitles: List of subtitle dictionaries from parse_srt_file()
        
    Returns:
        float: Duration in seconds, or 0 if no subtitles
    """
    if not subtitles:
        return 0.0
    
    # Subtitles should be in order, but just in case, find max end time
    max_end_time = max(sub['end_time'] for sub in subtitles)
    return max_end_time


def format_time(seconds):
    """
    Format seconds as M:SS or H:MM:SS.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted time string
    """
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def display_progress(current_time, total_duration, subtitle_text="", current_frame=None):
    """
    Display playback progress with optional subtitle.
    
    Args:
        current_time: Current playback time in seconds
        total_duration: Total duration in seconds
        subtitle_text: Current subtitle text to display
        current_frame: Optional frame number for debugging
    """
    # Calculate progress percentage
    if total_duration > 0:
        progress = (current_time / total_duration) * 100
        progress = min(100, max(0, progress))  # Clamp to 0-100
    else:
        progress = 0
    
    # Create progress bar (40 characters wide)
    bar_length = 40
    filled_length = int(bar_length * progress / 100)
    bar = '=' * filled_length + '>' + ' ' * (bar_length - filled_length - 1)
    
    # Format time strings
    current_str = format_time(current_time)
    total_str = format_time(total_duration)
    
    # Build output
    output = f"\rCurrent: {current_str} / {total_str}  [{bar}] {progress:5.1f}%"
    
    if current_frame is not None:
        output += f" | Frame: {current_frame}"
    
    print(output, end='', flush=True)
    
    # Print subtitle on new line if present
    if subtitle_text:
        print(f"\n  >> {subtitle_text}", end='', flush=True)
    else:
        # Clear subtitle line if no subtitle
        print(" " * 80, end='', flush=True)


class SubtitleManager:
    """
    Manages subtitle loading and synchronization for clips.
    Supports dual subtitles (e.g., Spanish and English).
    """
    
    def __init__(self, gui_overlay=None):
        """
        Initialize the subtitle manager.
        
        Args:
            gui_overlay: Optional ProgressOverlay instance for GUI display
        """
        self.current_clip = None
        self.subtitles = []  # Primary subtitles (English)
        self.subtitles2 = []  # Secondary subtitles (Spanish)
        self.duration = 0.0
        self.last_frame = -1
        self.gui_overlay = gui_overlay
        self.use_gui = gui_overlay is not None
        self.is_custom_movie = False  # Track if this is a site-custom movie
        
        # Separate accumulators for each subtitle track
        self.accumulator = []
        self.last_index = -1
        self.accumulator2 = []
        self.last_index2 = -1
        
        # Special layout handling for Nature's Harmonious Relationships
        self.is_harmonious = False
        self.layout_mode = None  # 'vertical' or 'horizontal'
    
    def _find_subtitle_at_time(self, subtitles, time_seconds, accumulator, last_index, max_chars=200):
        """
        Find and accumulate subtitles over time until line is full, then clear and continue.
        Instance-based version to avoid global state conflicts.
        
        Args:
            subtitles: List of subtitle dictionaries from parse_srt_file()
            time_seconds: Current playback time in seconds
            accumulator: List to accumulate subtitle text
            last_index: Last subtitle index seen
            max_chars: Maximum characters before clearing (roughly screen width)
            
        Returns:
            tuple: (subtitle_text, updated_accumulator, updated_last_index)
        """
        # Find current active subtitle
        current_sub = None
        for sub in subtitles:
            if sub['start_time'] <= time_seconds <= sub['end_time']:
                current_sub = sub
                break
        
        # If no subtitle is active, keep showing accumulated text
        if not current_sub:
            return (" ".join(accumulator), accumulator, last_index)
        
        # If this is a new subtitle we haven't seen yet
        if current_sub['index'] != last_index:
            last_index = current_sub['index']
            
            # Clean subtitle text (remove newlines)
            new_text = current_sub['text'].replace('\n', ' ')
            
            # Check if adding this would exceed max_chars
            current_length = sum(len(text) for text in accumulator)
            
            if current_length + len(new_text) > max_chars:
                # Clear and start fresh with new subtitle
                accumulator = [new_text]
            else:
                # Add to accumulator
                accumulator.append(new_text)
        
        # Return accumulated text joined with spaces
        return (" ".join(accumulator), accumulator, last_index)
    
    def load_subtitles_for_clip(self, clip_name, caption_path, caption2_path=None, datadir=None):
        """
        Load subtitles for a new clip. Supports dual subtitles.
        
        Args:
            clip_name: Name of the current clip
            caption_path: Path to the primary .srt file (can be None)
            caption2_path: Path to the secondary .srt file (can be None)
            datadir: Data directory path from metadata (for detecting site-custom movies)
            
        Returns:
            bool: True if subtitles loaded, False otherwise
        """
        self.current_clip = clip_name
        self.last_frame = -1
        self.subtitles2 = []  # Reset secondary subtitles
        
        # Detect if this is a site-custom movie
        # Check if datadir contains 'site-custom' - indicates custom movie content
        self.is_custom_movie = False
        if datadir:
            datadir_lower = datadir.lower()
            if 'site-custom' in datadir_lower:
                self.is_custom_movie = True
                print(f"[Custom Movie] Detected site-custom movie (datadir: {datadir})")
                print(f"  → Using special centered subtitle layout with text-only backgrounds")
        
        # Reset accumulators for new clip
        self.accumulator = []
        self.last_index = -1
        self.accumulator2 = []
        self.last_index2 = -1
        
        if not caption_path or not caption_path.strip():
            print(f"No captions for clip: {clip_name}")
            self.subtitles = []
            self.duration = 0.0
            return False
        
        print(f"  → Primary filepath: {caption_path} \n")
        
        self.subtitles = parse_srt_file(caption_path)
        self.duration = get_duration_from_subtitles(self.subtitles)
        
        # Load secondary subtitles if provided
        if caption2_path and caption2_path.strip():
            print(f"  → Secondary filepath: {caption2_path} \n")
            self.subtitles2 = parse_srt_file(caption2_path)
            # Update duration if secondary subtitles are longer
            duration2 = get_duration_from_subtitles(self.subtitles2)
            if duration2 > self.duration:
                self.duration = duration2
        
        if self.subtitles:
            print(f"  → Duration: {format_time(self.duration)}")
            if self.subtitles2:
                print(f"  → Dual subtitles loaded (primary + secondary)")
            return True
        else:
            print(f"  No subtitles loaded")
            return False
    
    def update(self, current_frame, fps):
        """
        Update subtitle display based on current frame.
        
        Args:
            current_frame: Current frame number
            fps: Frame rate (frames per second)
        """
        # Detect clip loop
        if current_frame < self.last_frame:
            if self.use_gui:
                print("\n[Clip looped]")  # Still print to console
            else:
                print("\n[Clip looped]")
            # Reset accumulators on loop
            self.accumulator = []
            self.last_index = -1
            self.accumulator2 = []
            self.last_index2 = -1
        
        self.last_frame = current_frame
        
        # Convert frame to time
        current_time = current_frame / fps if fps > 0 else 0
        
        # Find current subtitle (primary - English)
        # Adjust character limits based on whether we have dual subtitles
        if self.subtitles2:  # Dual captions mode
            max_chars_english = 170  # Shorter for side-by-side columns
            max_chars_spanish = 170  # Shorter for side-by-side columns
        else:  # Single caption mode
            max_chars_english = 350  # ~2-3 shorter lines for easier reading
            max_chars_spanish = 350  # ~2-3 shorter lines for easier reading
        
        subtitle_text, self.accumulator, self.last_index = self._find_subtitle_at_time(
            self.subtitles, current_time, self.accumulator, self.last_index, max_chars_english
        )
        
        # Find secondary subtitle if available (Spanish)
        subtitle_text2 = ""
        if self.subtitles2:
            subtitle_text2, self.accumulator2, self.last_index2 = self._find_subtitle_at_time(
                self.subtitles2, current_time, self.accumulator2, self.last_index2, max_chars_spanish
            )
        
        # Display progress - use GUI if available, otherwise terminal
        if self.use_gui and self.gui_overlay and self.gui_overlay.is_active():
            # Check if we should use custom movie layout (dual captions + custom movie)
            if self.is_custom_movie and subtitle_text and subtitle_text2:
                self.gui_overlay.update_progress_custom_movie(current_time, self.duration, subtitle_text, 1, subtitle_text2)
            else:
                self.gui_overlay.update_progress(current_time, self.duration, subtitle_text, 1, subtitle_text2)
        else:
            display_progress(current_time, self.duration, subtitle_text, current_frame)
    
    def has_subtitles(self):
        """Check if subtitles are loaded."""
        return len(self.subtitles) > 0
