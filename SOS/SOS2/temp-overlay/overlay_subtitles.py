"""
Subtitle Overlay (PyQt5 version)
Displays only subtitles in multiple layouts - standard stacked, vertical columns, or custom movie positioning.
Fully modular with configurable container sizing and padding parameters.
"""

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont


class SubtitleOverlay(QWidget):
    """
    A transparent overlay window that shows only subtitles in various layouts.
    """
    
    def __init__(self, position='bottom', opacity=0.85, y_offset=0,
                 parent_container_width_percent=1.0, parent_container_height=200,
                 column_horizontal_padding=50, column_top_padding=20,
                 column_bottom_padding=20, column_height_percent=0.8,
                 left_column_width_percent=0.5, column_spacing=0,
                 subtitle_font_size=14,
                 subtitle_font_family='Arial',
                 subtitle_text_color='#ffffff',
                 subtitle_bg_opacity=150,
                 subtitle_alignment='center',
                 subtitle_font_bold=False,
                 subtitle_top_spacing=0,
                 text_padding=8,
                 show_title_row=False, left_title='', right_title='',
                 title_height=40, title_font_size=18,
                 title_font_family='Arial', title_font_bold=True,
                 left_title_color='#ffff00', right_title_color='#ffffff',
                 title_bg_opacity=150, title_alignment='center',
                 title_top_spacing=10,
                 left_title_padding=8, right_title_padding=8,
                 show_debug_borders=True):
        """
        Initialize the subtitle overlay.
        
        Args:
            position: Position of overlay ('bottom', 'top')
            opacity: Window opacity from 0.0 (transparent) to 1.0 (opaque)
            y_offset: Vertical offset in pixels (positive = up, negative = down)
            parent_container_width_percent: Width of parent container as % of screen width (0.0-1.0)
            parent_container_height: Height of parent container as % of screen height (0.0-1.0)
            column_horizontal_padding: Horizontal padding for each column container in pixels
            column_top_padding: Top padding for column containers in pixels
            column_bottom_padding: Bottom padding for column containers in pixels
            column_height_percent: Height of column containers as % of parent container (0.0-1.0)
            left_column_width_percent: Width of left column as % of parent width (0.0-1.0, default 0.5)
            column_spacing: Spacing between columns in pixels
            subtitle_font_size: Font size for subtitle text in both columns in points
            subtitle_font_family: Font family for subtitle text (e.g., 'Arial', 'Times New Roman')
            subtitle_text_color: Text color for subtitle text in hex (e.g., '#ffffff')
            subtitle_bg_opacity: Background opacity for subtitle text (0-255)
            subtitle_alignment: Text alignment for subtitle text ('left', 'center', 'right')
            subtitle_font_bold: If True, use bold font for subtitle text
            subtitle_top_spacing: Spacing above subtitle text in pixels
            text_padding: Padding around text in pixels
            show_title_row: If True, display title row above columns
            left_title: Title text for left column
            right_title: Title text for right column
            title_height: Height of title row in pixels
            title_font_size: Font size for title text in points
            title_font_family: Font family for title text
            title_font_bold: If True, use bold font for titles
            left_title_color: Text color for left title in hex
            right_title_color: Text color for right title in hex
            title_bg_opacity: Background opacity for title text (0-255)
            title_alignment: Text alignment for titles ('left', 'center', 'right')
            title_top_spacing: Spacing above title row in pixels
            left_title_padding: Padding around left title text in pixels
            right_title_padding: Padding around right title text in pixels
            show_debug_borders: If True, show visible borders on containers for adjustment
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
        # Calculate height as percentage of screen height
        container_height = int(screen_geometry.height() * self.parent_container_height)
        self.setFixedSize(screen_geometry.width(), container_height)
        self.calculated_container_height = container_height
    
    def _create_widgets(self):
        """Create the UI widgets for subtitle display with two-column layout."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
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
        
        # Debug border for left column
        if self.show_debug_borders:
            self.left_column.setStyleSheet("border: 2px solid blue; background: rgba(0, 0, 0, 100);")
        else:
            self.left_column.setStyleSheet("background: transparent;")
        
        # Left title label (if enabled)
        if self.show_title_row:
            left_layout.addSpacing(self.title_top_spacing)  # Top spacing before title
            self.left_title_label = QLabel(self.left_title)
            title_weight = QFont.Bold if self.title_font_bold else QFont.Normal
            self.left_title_label.setFont(QFont(self.title_font_family, self.title_font_size, title_weight))
            title_align = alignment_map.get(self.title_alignment.lower(), Qt.AlignCenter)
            
            # Create styled title with background
            title_bg_hex = f"rgba(0, 0, 0, {self.title_bg_opacity})"
            title_style = f"""
                <div style='
                    background-color: {title_bg_hex};
                    padding: {self.left_title_padding}px;
                    margin: 0;
                '>
                    <span style='color: {self.left_title_color};'>{self.left_title}</span>
                </div>
            """
            self.left_title_label.setText(title_style)
            self.left_title_label.setAlignment(title_align | Qt.AlignVCenter)
            self.left_title_label.setFixedHeight(self.title_height)
            self.left_title_label.setStyleSheet("background: transparent;")
            left_layout.addWidget(self.left_title_label)
        
        # Add spacing before subtitle text
        if self.subtitle_top_spacing > 0:
            left_layout.addSpacing(self.subtitle_top_spacing)
        
        # English subtitle label - expands to fill column container
        self.subtitle_label = QLabel("")
        font_weight = QFont.Bold if self.subtitle_font_bold else QFont.Normal
        self.subtitle_label.setFont(QFont(self.subtitle_font_family, self.subtitle_font_size, font_weight))
        self.subtitle_label.setStyleSheet(f"color: {self.subtitle_text_color}; background: transparent;")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(subtitle_align | Qt.AlignTop)
        self.subtitle_label.setSizePolicy(self.subtitle_label.sizePolicy().Expanding, self.subtitle_label.sizePolicy().Expanding)
        left_layout.addWidget(self.subtitle_label)
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
        
        # Right title label (if enabled)
        if self.show_title_row:
            right_layout.addSpacing(self.title_top_spacing)  # Top spacing before title
            self.right_title_label = QLabel(self.right_title)
            title_weight = QFont.Bold if self.title_font_bold else QFont.Normal
            self.right_title_label.setFont(QFont(self.title_font_family, self.title_font_size, title_weight))
            title_align = alignment_map.get(self.title_alignment.lower(), Qt.AlignCenter)
            
            # Create styled title with background
            title_bg_hex = f"rgba(0, 0, 0, {self.title_bg_opacity})"
            title_style = f"""
                <div style='
                    background-color: {title_bg_hex};
                    padding: {self.right_title_padding}px;
                    margin: 0;
                '>
                    <span style='color: {self.right_title_color};'>{self.right_title}</span>
                </div>
            """
            self.right_title_label.setText(title_style)
            self.right_title_label.setAlignment(title_align | Qt.AlignVCenter)
            self.right_title_label.setFixedHeight(self.title_height)
            self.right_title_label.setStyleSheet("background: transparent;")
            right_layout.addWidget(self.right_title_label)
        
        # Add spacing before subtitle text
        if self.subtitle_top_spacing > 0:
            right_layout.addSpacing(self.subtitle_top_spacing)
        
        # Spanish subtitle label - expands to fill column container
        self.subtitle_label2 = QLabel("")
        font_weight2 = QFont.Bold if self.subtitle_font_bold else QFont.Normal
        self.subtitle_label2.setFont(QFont(self.subtitle_font_family, self.subtitle_font_size, font_weight2))
        self.subtitle_label2.setStyleSheet(f"color: {self.subtitle_text_color}; background: transparent;")
        self.subtitle_label2.setWordWrap(True)
        self.subtitle_label2.setAlignment(subtitle_align | Qt.AlignTop)
        self.subtitle_label2.setSizePolicy(self.subtitle_label2.sizePolicy().Expanding, self.subtitle_label2.sizePolicy().Expanding)
        right_layout.addWidget(self.subtitle_label2)
        right_layout.addStretch()  # Push subtitle to top of column
        
        self.right_column.setLayout(right_layout)
        columns_layout.addWidget(self.right_column)
        
        self.parent_container.setLayout(columns_layout)
        main_layout.addWidget(self.parent_container, alignment=Qt.AlignCenter)
        
        self.setLayout(main_layout)
    
    def _position_window(self):
        """Position the window based on the position setting."""
        screen_geometry = QApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        
        x = 0
        
        if self.position == 'bottom':
            y = screen_geometry.height() - window_rect.height()
        elif self.position == 'top':
            y = 0
        else:  # default to bottom
            y = screen_geometry.height() - window_rect.height()
        
        y = max(0, min(screen_geometry.height() - window_rect.height(), y - self.y_offset))
        self.move(x, y)
    
    def update_subtitles(self, subtitle_text="", subtitle_text2=""):
        """
        Update subtitle display in two-column layout.
        
        Args:
            subtitle_text: Primary subtitle text (English) - left column
            subtitle_text2: Secondary subtitle text (Spanish) - right column
        """
        self.current_subtitle = subtitle_text
        self.current_subtitle2 = subtitle_text2
        
        # Update English subtitle (left column)
        if subtitle_text:
            # Add background only to text, not entire column
            font_weight_str = 'font-weight: bold;' if self.subtitle_font_bold else ''
            html_text = f'<span style="background: rgba(0, 0, 0, {self.subtitle_bg_opacity}); color: {self.subtitle_text_color}; padding: {self.text_padding}px; font-family: {self.subtitle_font_family}; font-size: {self.subtitle_font_size}pt; {font_weight_str}">{subtitle_text}</span>'
            self.subtitle_label.setText(html_text)
            self.subtitle_label.setVisible(True)
        else:
            self.subtitle_label.setText("")
            self.subtitle_label.setVisible(False)
        
        # Update Spanish subtitle (right column)
        if subtitle_text2:
            # Add background only to text, not entire column
            font_weight_str2 = 'font-weight: bold;' if self.subtitle_font_bold else ''
            html_text = f'<span style="background: rgba(0, 0, 0, {self.subtitle_bg_opacity}); color: {self.subtitle_text_color}; padding: {self.text_padding}px; font-family: {self.subtitle_font_family}; font-size: {self.subtitle_font_size}pt; {font_weight_str2}">{subtitle_text2}</span>'
            self.subtitle_label2.setText(html_text)
            self.subtitle_label2.setVisible(True)
        else:
            self.subtitle_label2.setText("")
            self.subtitle_label2.setVisible(False)
    
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
