"""
SRT Subtitle Parser and Sync Module (Dev Version)
Handles parsing .srt files and finding subtitles based on playback time.
Adapted for usage in dev environment with OverlayManager.
"""

import re
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsBlurEffect
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QFontMetrics, QFontDatabase

# Inter font loading (lazy - only loads when QApplication exists)
_INTER_FONT_LOADED = False
_INTER_FONT_NAME = 'Arial'  # Default fallback

def get_inter_font():
    """Load Inter font from the network share location (lazy loading)."""
    global _INTER_FONT_LOADED, _INTER_FONT_NAME
    
    if _INTER_FONT_LOADED:
        return _INTER_FONT_NAME
    
    try:
        font_path = r'\\sos2\AuxShare\assets\Inter_18pt-Medium.ttf'
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    _INTER_FONT_NAME = font_families[0]
    except Exception as e:
        print(f"[Font] Warning: Could not load Inter font: {e}")
    
    _INTER_FONT_LOADED = True
    return _INTER_FONT_NAME

# Inter Bold font loading (lazy - only loads when QApplication exists)
_INTER_BOLD_FONT_LOADED = False
_INTER_BOLD_FONT_NAME = 'Arial'  # Default fallback

def get_inter_bold_font():
    """Load Inter Bold font from the network share location (lazy loading)."""
    global _INTER_BOLD_FONT_LOADED, _INTER_BOLD_FONT_NAME
    
    if _INTER_BOLD_FONT_LOADED:
        return _INTER_BOLD_FONT_NAME
    
    try:
        font_path = r'\\sos2\AuxShare\assets\Inter_18pt-Bold.ttf'
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    _INTER_BOLD_FONT_NAME = font_families[0]
    except Exception as e:
        print(f"[Font] Warning: Could not load Inter Bold font: {e}")
    
    _INTER_BOLD_FONT_LOADED = True
    return _INTER_BOLD_FONT_NAME

def srt_time_to_seconds(timestamp):
    """Convert SRT timestamp to seconds."""
    try:
        time_part, ms_part = timestamp.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return (h * 3600) + (m * 60) + s + (ms / 1000.0)
    except:
        return 0.0

def parse_srt_file(filepath):
    """Parse an SRT subtitle file."""
    if not os.path.exists(filepath):
        # In dev, filepath might be absolute or relative to cache
        # Check if it exists as is, otherwise try to locate in subtitle cache
        # Logic matches cache_manager cache path.
        if os.path.exists(os.path.basename(filepath)):
             filepath = os.path.basename(filepath)
        else:
             # Try default cache dir construction just in case
             cache_path = os.path.join(r'\\sos2\AuxShare\cache\subtitles', os.path.basename(filepath))
             if os.path.exists(cache_path):
                 filepath = cache_path
             else:
                 print(f"Warning: Subtitle file not found: {filepath}")
                 return []
    
    subtitles = []
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            
        blocks = re.split(r'\n\s*\n', content.strip())
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3: continue
            
            try:
                index = int(lines[0].strip())
                timestamp_line = lines[1].strip()
                match = re.match(r'(\S+)\s*-->\s*(\S+)', timestamp_line)
                if not match: continue
                
                start_time = srt_time_to_seconds(match.group(1))
                end_time = srt_time_to_seconds(match.group(2))
                text = '\n'.join(lines[2:])
                
                subtitles.append({
                    'index': index,
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text
                })
            except: continue
            
        # print(f"[Subtitles] Loaded {len(subtitles)} entries from {os.path.basename(filepath)}")
        return subtitles
    except Exception as e:
        print(f"Error reading subtitle file {filepath}: {e}")
        return []

class SubtitleManager:
    """Manages subtitle state and interaction with overlay."""
    def __init__(self, gui_overlay=None):
        self.subtitles = []
        self.subtitles2 = []
        self.accumulator = []
        self.accumulator2 = []
        self.last_index = -1
        self.last_index2 = -1
        self.gui_overlay = gui_overlay
        self.current_clip_name = None  # Track current clip to detect changes
        self.transition_gap_tolerance = 0.25  # seconds; bridge tiny SRT gaps for seamless transitions
        
    def load_subtitles_for_clip(self, metadata):
        """Load subtitles from metadata dict."""
        # Detect clip change and clear subtitles
        new_clip_name = metadata.get('name') if metadata else None
        if new_clip_name != self.current_clip_name:
            # Clear previous subtitles when clip changes
            if self.gui_overlay:
                self.gui_overlay.clear_subtitles()
            self.current_clip_name = new_clip_name
        
        self.subtitles = []
        self.subtitles2 = []
        self.accumulator = []
        self.accumulator2 = []
        self.last_index = -1
        self.last_index2 = -1
        
        if not metadata: return
        
        # Check cache path first (preferred)
        # Using the standard cache dir we defined in cache_manager
        cache_dir = r'\\sos2\AuxShare\cache\subtitles'
        
        caption_path = metadata.get('caption')
        if caption_path:
             # Look in cache first
             cached_file = os.path.join(cache_dir, os.path.basename(caption_path))
             if os.path.exists(cached_file):
                 self.subtitles = parse_srt_file(cached_file)
             else:
                 self.subtitles = parse_srt_file(caption_path)
                 
        caption2_path = metadata.get('caption2')
        if caption2_path:
             cached_file2 = os.path.join(cache_dir, os.path.basename(caption2_path))
             if os.path.exists(cached_file2):
                 self.subtitles2 = parse_srt_file(cached_file2)
             else:
                 self.subtitles2 = parse_srt_file(caption2_path)
                 
    def _get_text(self, subtitles, current_time, accumulator_list, last_index_ref):
        """Helper to find text and handle accumulation logic."""
        # Note: accumulator_list is a list object (mutable), so changes persist.
        # last_index_ref is int, so we need to return the new value.
        # But wait, python ints are immutable. 
        # I need to handle state update.
        # Actually my signature in update() was:
        # text1 = self._get_text(self.subtitles, current_time, self.accumulator, self.last_index)
        # That won't update self.last_index!
        # I should change the method to use the instance variables directly based on an index/key?
        # Or just have two separate methods or pass the attribute names?
        # Let's just fix the logic in update() to handle the return values, similar to main/subtitles.py
        pass 
        
    def _find_subtitle_text(self, subtitles, current_time, is_secondary=False):
        """Find text for primary or secondary track using instance state."""
        # Select state based on track
        if is_secondary:
             accumulator = self.accumulator2
             last_index = self.last_index2
             max_chars = 170
        else:
             accumulator = self.accumulator
             last_index = self.last_index
             max_chars = 350 if not self.subtitles2 else 170

        current_sub = None
        for sub in subtitles:
            if sub['start_time'] <= current_time <= sub['end_time']:
                current_sub = sub
                break
        
        # If no active subtitle, optionally bridge tiny gaps before next subtitle
        if not current_sub:
            if accumulator:
                next_sub = None
                for sub in subtitles:
                    if sub['start_time'] > current_time:
                        next_sub = sub
                        break

                if next_sub and (next_sub['start_time'] - current_time) <= self.transition_gap_tolerance:
                    return " ".join(accumulator)

            accumulator.clear()
            if is_secondary:
                self.last_index2 = -1
            else:
                self.last_index = -1
            return ""
            
        # If new subtitle
        if current_sub['index'] != last_index or not accumulator:
            last_index = current_sub['index']
            new_text = current_sub['text'].replace('\n', ' ')
            
            current_len = sum(len(t) for t in accumulator)
            if current_len + len(new_text) > max_chars:
                accumulator[:] = [new_text] # Modify list in place
            else:
                accumulator.append(new_text)
                
            # Update state variables
            if is_secondary:
                self.last_index2 = last_index
            else:
                self.last_index = last_index
                
        return " ".join(accumulator)

    def update(self, current_time):
        """Update overlays based on time."""
        if not self.gui_overlay: return
        
        text1 = self._find_subtitle_text(self.subtitles, current_time, is_secondary=False)
        text2 = ""
        if self.subtitles2:
            text2 = self._find_subtitle_text(self.subtitles2, current_time, is_secondary=True)
        

        self.gui_overlay.update_subtitles(text1, text2)


class SubtitleOverlay(QWidget):
    """
    A transparent overlay window that shows only subtitles in various layouts.
    """
    
    def __init__(self, position='center', opacity=0.85, y_offset=0,
                 parent_container_width_percent=1.0, parent_container_height=1.0,
                 column_horizontal_padding=60, column_top_padding=35,
                 column_bottom_padding=20, column_height_percent=1.0,
                 left_column_width_percent=0.5, column_spacing=10,

                 subtitle_font_size=12,
                 subtitle_font_family=None,
                 subtitle_text_color='#ffffff',
                 subtitle_bg_opacity=150,
                 subtitle_alignment='center',
                 subtitle_font_bold=False,
                 subtitle_top_spacing=0,
                 subtitle_horizontal_padding=45,

                 text_padding=0,
                 show_title_row=False, left_title='', right_title='',
                 title_font_size=38,
                 title_font_family=None, title_font_bold=True,
                 left_title_color="#ffffff", right_title_color='#ffffff',
                 title_bg_opacity=150, title_alignment='center',
                 title_vertical_padding=0,
                 title_horizontal_padding=30,
                 show_debug_borders=False,

                 # Fuzzy background parameters 
                 fuzzy_bg_enabled=True,
                 fuzzy_bg_color='#000000',
                 fuzzy_bg_opacity=160,
                 fuzzy_bg_margin_left=80,
                 fuzzy_bg_margin_right=80,
                 fuzzy_bg_margin_top=100,
                 fuzzy_bg_margin_bottom=150,
                 fuzzy_bg_feather_strength = 30,
                 fuzzy_bg_feather_distance=60,
                 fuzzy_bg_border_radius=20,
                 
                 # Vertical center line parameters
                 center_line_enabled=True,
                 center_line_color='#ffffff',
                 center_line_width=3,
                 center_line_height_percent=.8,  # None = match fuzzy bg height
                 center_line_opacity=255):
        """
       
        """
        super().__init__()
        
        self.position = position
        self.opacity_value = opacity
        self.y_offset = y_offset
        
        # Container parameters
        self.parent_container_width_percent = parent_container_width_percent
        self.parent_container_height = parent_container_height
        self.column_horizontal_padding = column_horizontal_padding
        self.column_top_padding = column_top_padding
        self.column_bottom_padding = column_bottom_padding
        self.column_height_percent = column_height_percent
        self.left_column_width_percent = left_column_width_percent
        self.column_spacing = column_spacing
        
        # Font and styling parameters for subtitles
        self.subtitle_font_size = subtitle_font_size
        self.subtitle_font_family = subtitle_font_family if subtitle_font_family else get_inter_font()
        self.subtitle_text_color = subtitle_text_color
        self.subtitle_bg_opacity = subtitle_bg_opacity
        self.subtitle_alignment = subtitle_alignment
        self.subtitle_font_bold = subtitle_font_bold
        self.subtitle_top_spacing = subtitle_top_spacing
        self.subtitle_horizontal_padding = subtitle_horizontal_padding
        self.text_padding = text_padding
        
        # Title row parameters
        self.show_title_row = show_title_row
        self.left_title = left_title
        self.right_title = right_title
        self.title_font_size = title_font_size
        self.title_font_family = title_font_family if title_font_family else get_inter_bold_font()
        self.title_font_bold = title_font_bold
        self.left_title_color = left_title_color
        self.right_title_color = right_title_color
        self.title_bg_opacity = title_bg_opacity
        self.title_alignment = title_alignment
        self.title_vertical_padding = title_vertical_padding
        self.title_horizontal_padding = title_horizontal_padding
        
        # Fuzzy background parameters
        self.fuzzy_bg_enabled = fuzzy_bg_enabled
        self.fuzzy_bg_color = fuzzy_bg_color
        self.fuzzy_bg_opacity = fuzzy_bg_opacity
        self.fuzzy_bg_margin_left = fuzzy_bg_margin_left
        self.fuzzy_bg_margin_right = fuzzy_bg_margin_right
        self.fuzzy_bg_margin_top = fuzzy_bg_margin_top
        self.fuzzy_bg_margin_bottom = fuzzy_bg_margin_bottom
        self.fuzzy_bg_feather_strength = fuzzy_bg_feather_strength
        self.fuzzy_bg_feather_distance = fuzzy_bg_feather_distance
        self.fuzzy_bg_border_radius = fuzzy_bg_border_radius
        
        # Vertical center line parameters
        self.center_line_enabled = center_line_enabled
        self.center_line_color = center_line_color
        self.center_line_width = center_line_width
        self.center_line_height_percent = center_line_height_percent
        self.center_line_opacity = center_line_opacity
        
        self.show_debug_borders = show_debug_borders
        
        self.current_subtitle = ""
        self.current_subtitle2 = ""  # Secondary subtitle (Spanish)
        self.is_custom_movie_mode = False
        
        # Fade animation using window opacity (doesn't conflict with blur effects)
        self.fade_animation = None
        
        self._setup_window()
        self._create_widgets()
        self._position_window()
    
    def _setup_window(self):
        """Configure window properties for overlay appearance."""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        screen_geometry = QApplication.primaryScreen().geometry()
        
        self.setFixedSize(screen_geometry.width(), screen_geometry.height())
        
        # Calculate container height for internal layout
        if self.parent_container_height <= 1.0:
            self.calculated_container_height = int(screen_geometry.height() * self.parent_container_height)
        else:
            self.calculated_container_height = int(self.parent_container_height)
        
        # Ensure calculated height doesn't exceed screen height
        self.calculated_container_height = min(self.calculated_container_height, screen_geometry.height())
    
    def _create_widgets(self):
        """Create the UI widgets for subtitle display with two-column layout."""
        # Main layout covering full screen
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Align container based on position
        if self.position == 'bottom':
            main_layout.addStretch()
            # y_offset from bottom
            content_alignment = Qt.AlignHCenter | Qt.AlignBottom
        elif self.position == 'top':
            # y_offset from top
            content_alignment = Qt.AlignHCenter | Qt.AlignTop
        else:
            content_alignment = Qt.AlignCenter
            
        # Parent container - holds both column containers
        screen_geometry = QApplication.primaryScreen().geometry()
        parent_width = int(screen_geometry.width() * self.parent_container_width_percent)
        
        self.parent_container = QWidget()
        self.parent_container.setFixedSize(parent_width, self.calculated_container_height)
        
        # Debug border for parent container
        if self.show_debug_borders:
            self.parent_container.setStyleSheet("border: 2px solid red; background: transparent;")
        else:
            self.parent_container.setStyleSheet("background: transparent;")
        
        # Create fuzzy background widget (behind columns)
        if self.fuzzy_bg_enabled:
            self.fuzzy_background = QWidget(self.parent_container)
            
            # Parse hex color
            bg_color_hex = self.fuzzy_bg_color.lstrip('#')
            bg_r = int(bg_color_hex[0:2], 16)
            bg_g = int(bg_color_hex[2:4], 16)
            bg_b = int(bg_color_hex[4:6], 16)
            
            # Set background style with opacity and rounded corners
            self.fuzzy_background.setStyleSheet(f"""
                QWidget {{
                    background-color: rgba({bg_r}, {bg_g}, {bg_b}, {self.fuzzy_bg_opacity});
                    border-radius: {self.fuzzy_bg_border_radius}px;
                }}
            """)
            
            # Apply blur effect for feathering
            if self.fuzzy_bg_feather_strength > 0:
                blur_effect = QGraphicsBlurEffect()
                blur_effect.setBlurRadius(self.fuzzy_bg_feather_strength)
                self.fuzzy_background.setGraphicsEffect(blur_effect)
            
            # Position and size background (will be updated in update_subtitles)
            # Calculate size: parent minus margins
            bg_width = parent_width - self.fuzzy_bg_margin_left - self.fuzzy_bg_margin_right
            bg_height = self.calculated_container_height - self.fuzzy_bg_margin_top - self.fuzzy_bg_margin_bottom
            self.fuzzy_background.setGeometry(
                self.fuzzy_bg_margin_left,
                self.fuzzy_bg_margin_top,
                bg_width,
                bg_height
            )
            self.fuzzy_background.lower()  # Send to back
        
        # Calculate fuzzy background dimensions for columns container
        bg_width = parent_width - self.fuzzy_bg_margin_left - self.fuzzy_bg_margin_right
        bg_height = self.calculated_container_height - self.fuzzy_bg_margin_top - self.fuzzy_bg_margin_bottom
        
        # Create columns container to match fuzzy background dimensions
        self.columns_container = QWidget(self.parent_container)
        self.columns_container.setGeometry(
            self.fuzzy_bg_margin_left,
            self.fuzzy_bg_margin_top,
            bg_width,
            bg_height
        )
        self.columns_container.setStyleSheet("background: transparent;")
        
        # Horizontal layout for two columns
        columns_layout = QHBoxLayout()
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(self.column_spacing)
        
        # Calculate column dimensions based on columns_container width (bg_width)
        left_column_width = int(bg_width * self.left_column_width_percent)
        right_column_width = bg_width - left_column_width - self.column_spacing
        column_height = int(bg_height * self.column_height_percent)
        
        # Map alignment strings to Qt constants
        alignment_map = {
            'left': Qt.AlignLeft,
            'center': Qt.AlignCenter,
            'right': Qt.AlignRight
        }
        subtitle_align = alignment_map.get(self.subtitle_alignment.lower(), Qt.AlignCenter)
        
        # Left column container (English)
        self.left_column = QWidget()
        self.left_column.setFixedSize(left_column_width, column_height)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(
            self.column_horizontal_padding,
            self.column_top_padding,
            self.column_horizontal_padding,
            self.column_bottom_padding
        )
        left_layout.setSpacing(0)
        
        # print(f"[Overlay] Creating widgets - Title Height: {self.title_height}, Title Top Spacing: {self.title_top_spacing}")
        
        # Debug border for left column
        if self.show_debug_borders:
            self.left_column.setStyleSheet("border: 2px solid blue; background: rgba(0, 0, 0, 100);")
        else:
            self.left_column.setStyleSheet("background: transparent;")
        
        # Always create Left title label, hide if not initially shown
        if self.title_vertical_padding > 0:
            left_layout.addSpacing(self.title_vertical_padding)  # Space above title
        self.left_title_label = QLabel(self.left_title)
        title_weight = QFont.Bold if self.title_font_bold else QFont.Normal
        self.left_title_label.setFont(QFont(self.title_font_family, self.title_font_size, title_weight))
        title_align = alignment_map.get(self.title_alignment.lower(), Qt.AlignCenter)
        
        # Create styled title without background or padding
        title_style = f"""<div style='margin: 0; padding: 0;'><span style='color: {self.left_title_color}; margin: 0; padding: 0;'>{self.left_title}</span></div>"""
        self.left_title_label.setText(title_style)
        self.left_title_label.setAlignment(title_align | Qt.AlignTop)
        self.left_title_label.setWordWrap(True)
        self.left_title_label.setStyleSheet("background: transparent;")
        self.left_title_label.setContentsMargins(0, 0, 0, 0)
        
        # Wrapper for title horizontal padding
        title1_wrapper = QWidget()
        title1_wrapper.setFixedHeight(150)  # Fixed height prevents layout shifts, sized for 2-line titles
        title1_sub_layout = QVBoxLayout()
        title1_sub_layout.setContentsMargins(self.title_horizontal_padding, 0, self.title_horizontal_padding, 0)
        title1_sub_layout.setSpacing(0)
        title1_sub_layout.addStretch()
        title1_sub_layout.addWidget(self.left_title_label)
        title1_sub_layout.addStretch()
        title1_wrapper.setLayout(title1_sub_layout)
        title1_wrapper.setVisible(self.show_title_row)
        self.left_title_wrapper = title1_wrapper  # Store to toggle visibility
        
        left_layout.addWidget(title1_wrapper)
        
        # Add spacing between title and subtitle (or above subtitle if no title)
        if self.show_title_row and self.title_vertical_padding > 0:
            left_layout.addSpacing(self.title_vertical_padding)
        elif not self.show_title_row and self.subtitle_top_spacing > 0:
            left_layout.addSpacing(self.subtitle_top_spacing)
        
        # Subtitle label with explicit horizontal padding
        self.subtitle_label = QLabel("")
        font_weight = QFont.Bold if self.subtitle_font_bold else QFont.Normal
        self.subtitle_label.setFont(QFont(self.subtitle_font_family, self.subtitle_font_size, font_weight))
        self.subtitle_label.setStyleSheet(f"color: {self.subtitle_text_color}; background: transparent;")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(subtitle_align | Qt.AlignTop)
        self.subtitle_label.setSizePolicy(self.subtitle_label.sizePolicy().Expanding, self.subtitle_label.sizePolicy().Expanding)
        
        # Wrapper for subtitle padding
        sub1_wrapper = QWidget()
        sub1_sub_layout = QVBoxLayout()
        sub1_sub_layout.setContentsMargins(self.subtitle_horizontal_padding, 0, self.subtitle_horizontal_padding, 0)
        sub1_sub_layout.setSpacing(0)
        sub1_sub_layout.addWidget(self.subtitle_label)
        sub1_wrapper.setLayout(sub1_sub_layout)
        left_layout.addWidget(sub1_wrapper)  # Natural height based on content
        left_layout.addStretch()  # Push content to top
        
        self.left_column.setLayout(left_layout)
        columns_layout.addWidget(self.left_column)
        
        # Right column container (Spanish)
        self.right_column = QWidget()
        self.right_column.setFixedSize(right_column_width, column_height)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(
            self.column_horizontal_padding,
            self.column_top_padding,
            self.column_horizontal_padding,
            self.column_bottom_padding
        )
        right_layout.setSpacing(0)
        
        # Debug border for right column
        if self.show_debug_borders:
            self.right_column.setStyleSheet("border: 2px solid green; background: rgba(0, 0, 0, 100);")
        else:
            self.right_column.setStyleSheet("background: transparent;")
        
        # Always create Right title label, hide if not initially shown
        if self.title_vertical_padding > 0:
            right_layout.addSpacing(self.title_vertical_padding)  # Space above title
        self.right_title_label = QLabel(self.right_title)
        title_weight = QFont.Bold if self.title_font_bold else QFont.Normal
        self.right_title_label.setFont(QFont(self.title_font_family, self.title_font_size, title_weight))
        title_align = alignment_map.get(self.title_alignment.lower(), Qt.AlignCenter)
        
        # Create styled title without background or padding
        title_style = f"""<div style='margin: 0; padding: 0;'><span style='color: {self.right_title_color}; margin: 0; padding: 0;'>{self.right_title}</span></div>"""
        self.right_title_label.setText(title_style)
        self.right_title_label.setAlignment(title_align | Qt.AlignTop)
        self.right_title_label.setWordWrap(True)
        self.right_title_label.setStyleSheet("background: transparent;")
        self.right_title_label.setContentsMargins(0, 0, 0, 0)
        
        # Wrapper for title horizontal padding
        title2_wrapper = QWidget()
        title2_wrapper.setFixedHeight(150)  # Fixed height prevents layout shifts, sized for 2-line titles
        title2_sub_layout = QVBoxLayout()
        title2_sub_layout.setContentsMargins(self.title_horizontal_padding, 0, self.title_horizontal_padding, 0)
        title2_sub_layout.setSpacing(0)
        title2_sub_layout.addStretch()
        title2_sub_layout.addWidget(self.right_title_label)
        title2_sub_layout.addStretch()
        title2_wrapper.setLayout(title2_sub_layout)
        title2_wrapper.setVisible(self.show_title_row)
        self.right_title_wrapper = title2_wrapper  # Store to toggle visibility
        
        right_layout.addWidget(title2_wrapper)
        
        # Add spacing between title and subtitle (or above subtitle if no title)
        if self.show_title_row and self.title_vertical_padding > 0:
            right_layout.addSpacing(self.title_vertical_padding)
        elif not self.show_title_row and self.subtitle_top_spacing > 0:
            right_layout.addSpacing(self.subtitle_top_spacing)
        
        # Spanish subtitle label with explicit horizontal padding
        self.subtitle_label2 = QLabel("")
        font_weight2 = QFont.Bold if self.subtitle_font_bold else QFont.Normal
        self.subtitle_label2.setFont(QFont(self.subtitle_font_family, self.subtitle_font_size, font_weight2))
        self.subtitle_label2.setStyleSheet(f"color: {self.subtitle_text_color}; background: transparent;")
        self.subtitle_label2.setWordWrap(True)
        self.subtitle_label2.setAlignment(subtitle_align | Qt.AlignTop)
        self.subtitle_label2.setSizePolicy(self.subtitle_label2.sizePolicy().Expanding, self.subtitle_label2.sizePolicy().Expanding)
        
        # Wrapper for subtitle padding
        sub2_wrapper = QWidget()
        sub2_sub_layout = QVBoxLayout()
        sub2_sub_layout.setContentsMargins(self.subtitle_horizontal_padding, 0, self.subtitle_horizontal_padding, 0)
        sub2_sub_layout.setSpacing(0)
        sub2_sub_layout.addWidget(self.subtitle_label2)
        sub2_wrapper.setLayout(sub2_sub_layout)
        right_layout.addWidget(sub2_wrapper)  # Natural height based on content
        right_layout.addStretch()  # Push content to top
        
        self.right_column.setLayout(right_layout)
        columns_layout.addWidget(self.right_column)
        
        # Set layout on columns container (not parent_container)
        self.columns_container.setLayout(columns_layout)
        
        # Create vertical center line (on top layer)
        if self.center_line_enabled:
            self.center_line = QWidget(self.parent_container)
            
            # Parse hex color
            line_color_hex = self.center_line_color.lstrip('#')
            line_r = int(line_color_hex[0:2], 16)
            line_g = int(line_color_hex[2:4], 16)
            line_b = int(line_color_hex[4:6], 16)
            
            # Set line style
            self.center_line.setStyleSheet(f"""
                QWidget {{
                    background-color: rgba({line_r}, {line_g}, {line_b}, {self.center_line_opacity});
                }}
            """)
            
            # Calculate height: match fuzzy bg if no custom height specified
            if self.center_line_height_percent is None:
                # Match fuzzy background height
                line_height = bg_height
                line_y = self.fuzzy_bg_margin_top
            else:
                # Use custom height percentage
                line_height = int(bg_height * self.center_line_height_percent)
                line_y = self.fuzzy_bg_margin_top + (bg_height - line_height) // 2
            
            # Position horizontally centered within columns container
            line_x = self.fuzzy_bg_margin_left + (bg_width - self.center_line_width) // 2
            
            self.center_line.setGeometry(
                line_x,
                line_y,
                self.center_line_width,
                line_height
            )
            self.center_line.raise_()  # Bring to front
        
        # Add positioning spacers based on position and y_offset
        if self.position == 'bottom':
            main_layout.addStretch()
            main_layout.addWidget(self.parent_container, alignment=Qt.AlignCenter)
            if self.y_offset > 0:
                main_layout.addSpacing(self.y_offset)
        elif self.position == 'top':
            if self.y_offset > 0:
                main_layout.addSpacing(self.y_offset)
            main_layout.addWidget(self.parent_container, alignment=Qt.AlignCenter)
            main_layout.addStretch()
        else:  # center
            main_layout.addStretch()
            if self.y_offset > 0:
                main_layout.addSpacing(self.y_offset)
            main_layout.addWidget(self.parent_container, alignment=Qt.AlignCenter)
            if self.y_offset < 0:
                main_layout.addSpacing(abs(self.y_offset))
            main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def _position_window(self):
        """Position the window at the top-left of the screen."""
        self.move(0, 0)
    
    def clear_subtitles(self):
        """Clear all subtitle text immediately (called when clip changes)."""
        self.current_subtitle = ""
        self.current_subtitle2 = ""
        self.subtitle_label.setText("")
        self.subtitle_label.setVisible(False)
        self.subtitle_label2.setText("")
        self.subtitle_label2.setVisible(False)
    
    def update_subtitles(self, subtitle_text="", subtitle_text2=""):
        """
        Update subtitle display in two-column layout.
        
        Args:
            subtitle_text: Primary subtitle text (English) - left column
            subtitle_text2: Secondary subtitle text (Spanish) - right column
        """
        self.current_subtitle = subtitle_text
        self.current_subtitle2 = subtitle_text2
        
        # Column 1 (Left): English subtitles
        if subtitle_text:
            font_weight_str = 'font-weight: bold;' if self.subtitle_font_bold else ''
            html_text = f'<span style="color: {self.subtitle_text_color}; padding: {self.text_padding}px; font-family: {self.subtitle_font_family}; font-size: {self.subtitle_font_size}pt; {font_weight_str}">{subtitle_text}</span>'
            self.subtitle_label.setText(html_text)
            self.subtitle_label.setVisible(True)
        else:
            self.subtitle_label.setText("")
            self.subtitle_label.setVisible(False)
        
        # Column 2 (Right): Spanish subtitles
        if subtitle_text2:
            font_weight_str2 = 'font-weight: bold;' if self.subtitle_font_bold else ''
            html_text = f'<span style="color: {self.subtitle_text_color}; padding: {self.text_padding}px; font-family: {self.subtitle_font_family}; font-size: {self.subtitle_font_size}pt; {font_weight_str2}">{subtitle_text2}</span>'
            self.subtitle_label2.setText(html_text)
            self.subtitle_label2.setVisible(True)
        else:
            self.subtitle_label2.setText("")
            self.subtitle_label2.setVisible(False)

    def update_titles(self, left_title="", right_title=""):
        """Update the titles shown above the columns."""
        if not hasattr(self, 'left_title_label') or not hasattr(self, 'right_title_label'):
            return
            
        self.left_title = left_title
        self.right_title = right_title
        
        if left_title:
            # Simple HTML with title styling
            font_weight = "font-weight: bold;" if self.title_font_bold else ""
            title_html = f"""<div style='margin: 0; padding: 0;'><span style='color: {self.left_title_color}; font-family: {self.title_font_family}; font-size: {self.title_font_size}pt; margin: 0; padding: 0; {font_weight}'>{left_title}</span></div>"""
            self.left_title_label.setText(title_html)
            if hasattr(self, 'left_title_wrapper'):
                self.left_title_wrapper.setVisible(True)
            else:
                self.left_title_label.setVisible(True)
        else:
            if hasattr(self, 'left_title_wrapper'):
                self.left_title_wrapper.setVisible(False)
            else:
                self.left_title_label.setVisible(False)
            
        if right_title:
            # Simple HTML with title styling
            font_weight = "font-weight: bold;" if self.title_font_bold else ""
            title_html = f"""<div style='margin: 0; padding: 0;'><span style='color: {self.right_title_color}; font-family: {self.title_font_family}; font-size: {self.title_font_size}pt; margin: 0; padding: 0; {font_weight}'>{right_title}</span></div>"""
            self.right_title_label.setText(title_html)
            if hasattr(self, 'right_title_wrapper'):
                self.right_title_wrapper.setVisible(True)
            else:
                self.right_title_label.setVisible(True)
        else:
            if hasattr(self, 'right_title_wrapper'):
                self.right_title_wrapper.setVisible(False)
            else:
                self.right_title_label.setVisible(False)
    
    def is_active(self):
        """Check if the overlay is visible."""
        return self.isVisible()
    
    def start(self):
        """Show the overlay window with fade-in animation."""
        # Use window opacity for fade (doesn't conflict with blur effects on child widgets)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        
        # Fade in animation using window opacity
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(400)  # 400ms fade-in
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()
        
        QApplication.processEvents()
        self.repaint()
    
    def stop(self):
        """Close the overlay window with fade-out animation."""
        # Fade out animation using window opacity
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)  # 300ms fade-out
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()
