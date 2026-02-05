"""
SRT Subtitle Parser and Sync Module (Dev Version)
Handles parsing .srt files and finding subtitles based on playback time.
Adapted for usage in dev environment with OverlayManager.
"""

import re
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont, QFontMetrics

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
             cache_path = os.path.join(r'\\sos2\AuxShare\Documents\Cache\subtitle_cache', os.path.basename(filepath))
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
        
    def load_subtitles_for_clip(self, metadata):
        """Load subtitles from metadata dict."""
        self.subtitles = []
        self.subtitles2 = []
        self.accumulator = []
        self.accumulator2 = []
        self.last_index = -1
        self.last_index2 = -1
        
        if not metadata: return
        
        # Check cache path first (preferred)
        # Using the standard cache dir we defined in cache_manager
        cache_dir = r'\\sos2\AuxShare\Documents\Cache\subtitle_cache'
        
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
        
        # If no active subtitle, return current accumulation
        if not current_sub:
            return " ".join(accumulator)
            
        # If new subtitle
        if current_sub['index'] != last_index:
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
    
    def __init__(self, position='bottom', opacity=0.85, y_offset=0,
                 parent_container_width_percent=1.0, parent_container_height=1.0,
                 column_horizontal_padding=50, column_top_padding=20,
                 column_bottom_padding=20, column_height_percent=0.8,
                 left_column_width_percent=0.5, column_spacing=10,
                 subtitle_font_size=14,
                 subtitle_font_family='Arial',
                 subtitle_text_color='#ffffff',
                 subtitle_bg_opacity=150,
                 subtitle_alignment='center',
                 subtitle_font_bold=False,
                 subtitle_top_spacing=0,
                 subtitle_horizontal_padding=40,
                 text_padding=100,
                 show_title_row=False, left_title='', right_title='',
                 title_height=200, title_font_size=38,
                 title_font_family='Arial', title_font_bold=True,
                 left_title_color='#ffff00', right_title_color='#ffffff',
                 title_bg_opacity=150, title_alignment='center',
                 title_top_spacing=0,
                 left_title_padding=10, right_title_padding=10,
                 title_horizontal_padding=20,
                 show_debug_borders=False):
        """
        Initialize the subtitle overlay.
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
        self.subtitle_font_family = subtitle_font_family
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
        self.title_height = title_height
        self.title_font_size = title_font_size
        self.title_font_family = title_font_family
        self.title_font_bold = title_font_bold
        self.left_title_color = left_title_color
        self.right_title_color = right_title_color
        self.title_bg_opacity = title_bg_opacity
        self.title_alignment = title_alignment
        self.title_top_spacing = title_top_spacing
        self.left_title_padding = left_title_padding
        self.right_title_padding = right_title_padding
        self.title_horizontal_padding = title_horizontal_padding
        
        self.show_debug_borders = show_debug_borders
        
        self.current_subtitle = ""
        self.current_subtitle2 = ""  # Secondary subtitle (Spanish)
        self.is_custom_movie_mode = False
        
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
        
        # Make the window full screen to "support the entire length of the screen"
        # The parent_container will be positioned within this full-screen window
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
        
        # Horizontal layout for two columns
        columns_layout = QHBoxLayout()
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(self.column_spacing)
        
        # Calculate column dimensions
        left_column_width = int(parent_width * self.left_column_width_percent)
        right_column_width = parent_width - left_column_width - self.column_spacing
        column_height = int(self.calculated_container_height * self.column_height_percent)
        
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
        left_layout.addSpacing(self.title_top_spacing)  # Top spacing before title
        self.left_title_label = QLabel(self.left_title)
        title_weight = QFont.Bold if self.title_font_bold else QFont.Normal
        self.left_title_label.setFont(QFont(self.title_font_family, self.title_font_size, title_weight))
        title_align = alignment_map.get(self.title_alignment.lower(), Qt.AlignCenter)
        
        # Create styled title with background
        title_bg_hex = f"rgba(0, 0, 0, {self.title_bg_opacity})"
        title_style = f"""<div style='background-color: {title_bg_hex}; padding: {self.left_title_padding}px; margin: 0;'><span style='color: {self.left_title_color};'>{self.left_title}</span></div>"""
        self.left_title_label.setText(title_style)
        self.left_title_label.setAlignment(title_align | Qt.AlignVCenter)
        self.left_title_label.setWordWrap(True)
        self.left_title_label.setFixedHeight(self.title_height)
        self.left_title_label.setStyleSheet("background: transparent;")
        
        # Wrapper for title horizontal padding
        title1_wrapper = QWidget()
        title1_sub_layout = QVBoxLayout()
        title1_sub_layout.setContentsMargins(self.title_horizontal_padding, 0, self.title_horizontal_padding, 0)
        title1_sub_layout.addWidget(self.left_title_label)
        title1_wrapper.setLayout(title1_sub_layout)
        title1_wrapper.setVisible(self.show_title_row)
        self.left_title_wrapper = title1_wrapper  # Store to toggle visibility
        
        left_layout.addWidget(title1_wrapper)
        
        # Add spacing before subtitle text
        if self.subtitle_top_spacing > 0:
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
        sub1_sub_layout.addWidget(self.subtitle_label)
        sub1_wrapper.setLayout(sub1_sub_layout)
        left_layout.addWidget(sub1_wrapper)
        
        left_layout.addStretch()  # Push subtitle to top of column
        
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
        right_layout.addSpacing(self.title_top_spacing)  # Top spacing before title
        self.right_title_label = QLabel(self.right_title)
        title_weight = QFont.Bold if self.title_font_bold else QFont.Normal
        self.right_title_label.setFont(QFont(self.title_font_family, self.title_font_size, title_weight))
        title_align = alignment_map.get(self.title_alignment.lower(), Qt.AlignCenter)
        
        # Create styled title with background
        title_bg_hex = f"rgba(0, 0, 0, {self.title_bg_opacity})"
        title_style = f"""<div style='background-color: {title_bg_hex}; padding: {self.right_title_padding}px; margin: 0;'><span style='color: {self.right_title_color};'>{self.right_title}</span></div>"""
        self.right_title_label.setText(title_style)
        self.right_title_label.setAlignment(title_align | Qt.AlignVCenter)
        self.right_title_label.setWordWrap(True)
        self.right_title_label.setFixedHeight(self.title_height)
        self.right_title_label.setStyleSheet("background: transparent;")
        
        # Wrapper for title horizontal padding
        title2_wrapper = QWidget()
        title2_sub_layout = QVBoxLayout()
        title2_sub_layout.setContentsMargins(self.title_horizontal_padding, 0, self.title_horizontal_padding, 0)
        title2_sub_layout.addWidget(self.right_title_label)
        title2_wrapper.setLayout(title2_sub_layout)
        title2_wrapper.setVisible(self.show_title_row)
        self.right_title_wrapper = title2_wrapper  # Store to toggle visibility
        
        right_layout.addWidget(title2_wrapper)
        
        # Add spacing before subtitle text
        if self.subtitle_top_spacing > 0:
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
        sub2_sub_layout.addWidget(self.subtitle_label2)
        sub2_wrapper.setLayout(sub2_sub_layout)
        right_layout.addWidget(sub2_wrapper)
        
        right_layout.addStretch()  # Push subtitle to top of column
        
        self.right_column.setLayout(right_layout)
        columns_layout.addWidget(self.right_column)
        
        self.parent_container.setLayout(columns_layout)
        
        # Add positioning spacers based on position and y_offset
        if self.position == 'bottom':
            main_layout.addWidget(self.parent_container, alignment=Qt.AlignCenter)
            if self.y_offset > 0:
                main_layout.addSpacing(self.y_offset)
        elif self.position == 'top':
            if self.y_offset > 0:
                main_layout.addSpacing(self.y_offset)
            main_layout.addWidget(self.parent_container, alignment=Qt.AlignCenter)
            main_layout.addStretch()
        else:
            main_layout.addWidget(self.parent_container, alignment=Qt.AlignCenter)
        
        self.setLayout(main_layout)
    
    def _position_window(self):
        """Position the window at the top-left of the screen."""
        self.move(0, 0)
    
    def update_subtitles(self, subtitle_text="", subtitle_text2=""):
        """
        Update subtitle display in two-column layout.
        
        Args:
            subtitle_text: Primary subtitle text (English) - left column
            subtitle_text2: Secondary subtitle text (Spanish) - right column
        """
        self.current_subtitle = subtitle_text
        self.current_subtitle2 = subtitle_text2
        
        # Column 1 (Left): Now receives subtitle_text2 (Spanish)
        if subtitle_text2:
            font_weight_str = 'font-weight: bold;' if self.subtitle_font_bold else ''
            html_text = f'<span style="background: rgba(0, 0, 0, {self.subtitle_bg_opacity}); color: {self.subtitle_text_color}; padding: {self.text_padding}px; font-family: {self.subtitle_font_family}; font-size: {self.subtitle_font_size}pt; {font_weight_str}">{subtitle_text2}</span>'
            self.subtitle_label.setText(html_text)
            self.subtitle_label.setVisible(True)
        else:
            self.subtitle_label.setText("")
            self.subtitle_label.setVisible(False)
        
        # Column 2 (Right): Now receives subtitle_text (English)
        if subtitle_text:
            font_weight_str2 = 'font-weight: bold;' if self.subtitle_font_bold else ''
            html_text = f'<span style="background: rgba(0, 0, 0, {self.subtitle_bg_opacity}); color: {self.subtitle_text_color}; padding: {self.text_padding}px; font-family: {self.subtitle_font_family}; font-size: {self.subtitle_font_size}pt; {font_weight_str2}">{subtitle_text}</span>'
            self.subtitle_label2.setText(html_text)
            self.subtitle_label2.setVisible(True)
        else:
            self.subtitle_label2.setText("")
            self.subtitle_label2.setVisible(False)

    def _get_fitted_title_html(self, text, color, initial_size, inner_w, inner_h, title_padding):
        """
        Calculate the best font size to fit text in the fixed title box.
        inner_w: the maximum available width for the label widget itself.
        inner_h: the maximum available height for the label widget itself.
        """
        size = initial_size
        
        # Space inside the label for the text itself (subtract label's HTML padding)
        # padding here is the CSS padding inside the label's <div>
        target_w = inner_w - (title_padding * 2)
        target_h = inner_h - (title_padding * 2)
        
        # print(f"[Overlay] Fitting Title: '{text}' (Available: {inner_w}x{inner_h} -> Text Target: {target_w}x{target_h})")
        
        # Safety check for invalid dimensions
        if target_w <= 0 or target_h <= 0:
            alpha = self.title_bg_opacity / 255.0
            return f"<div style='background: rgba(0,0,0,{alpha}); color: {color}; padding: {title_padding}px;'>{text}</div>"

        # Scaling loop
        font = QFont(self.title_font_family, size)
        if self.title_font_bold:
            font.setBold(True)
            
        while size > 8:
            font.setPointSize(size)
            metrics = QFontMetrics(font)
            # Use boundingRect with word wrap. Note: target_w is the constraint.
            rect = metrics.boundingRect(0, 0, target_w, 2000, Qt.TextWordWrap, text)
            if rect.height() <= target_h:
                break
            size -= 1
        
        print(f"  - Final size chosen: {size} (Rect height: {rect.height() if 'rect' in locals() else 'N/A'})")
            
        alpha = self.title_bg_opacity / 255.0
        font_weight = "font-weight: bold;" if self.title_font_bold else ""
        return f"""<div style='background-color: rgba(0,0,0,{alpha}); padding: {title_padding}px; margin: 0;'><span style='color: {color}; font-family: {self.title_font_family}; font-size: {size}pt; {font_weight}'>{text}</span></div>"""

    def update_titles(self, left_title="", right_title=""):
        """Update the titles shown above the columns."""
        if not hasattr(self, 'left_title_label') or not hasattr(self, 'right_title_label'):
            # print(f"[Overlay] Warning: Title labels not initialized!")
            return
            
        # print(f"[Overlay] Updating titles - Left: '{left_title}', Right: '{right_title}'")
        self.left_title = left_title
        self.right_title = right_title
        
        # Calculate maximum available width for the title label widget
        # screen_w is the window width. 
        # The columns have fixed sizes calculated in _create_widgets.
        # But we can also use the geometry of the column widgets if they are laid out.
        # For robustness during first update, we recalculate based on percentages.
        screen_geometry = QApplication.primaryScreen().geometry()
        calculated_width = int(screen_geometry.width() * self.parent_container_width_percent)
        
        left_column_total_w = int(calculated_width * self.left_column_width_percent)
        right_column_total_w = calculated_width - left_column_total_w - self.column_spacing
        
        # Inner width for widgets inside the column layout (subtract column margins)
        # Also subtract the title_horizontal_padding (wrapper margins)
        left_inner_w = left_column_total_w - (self.column_horizontal_padding * 2) - (self.title_horizontal_padding * 2)
        right_inner_w = right_column_total_w - (self.column_horizontal_padding * 2) - (self.title_horizontal_padding * 2)
        
        if left_title:
            styled_left = self._get_fitted_title_html(
                left_title, self.left_title_color, self.title_font_size, 
                left_inner_w, self.title_height, self.left_title_padding
            )
            self.left_title_label.setText(styled_left)
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
            styled_right = self._get_fitted_title_html(
                right_title, self.right_title_color, self.title_font_size, 
                right_inner_w, self.title_height, self.right_title_padding
            )
            self.right_title_label.setText(styled_right)
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
        """Show the overlay window."""
        self.show()
        self.raise_()
        QApplication.processEvents()
        self.repaint()
    
    def stop(self):
        """Close the overlay window."""
        self.close()
