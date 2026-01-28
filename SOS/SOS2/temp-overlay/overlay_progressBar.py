"""
Progress Bar Overlay (PyQt5 version)
Displays only the progress bar with timestamp at the bottom of the screen.
"""

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGraphicsBlurEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter, QPen, QColor


class TickedProgressBar(QProgressBar):
    """Custom progress bar with tick marks for slide transitions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tick_count = 1  # Number of slides (ticks at transitions)
    
    def set_tick_count(self, count):
        """Set the number of slides (determines tick mark positions)."""
        self.tick_count = max(1, count)
        self.update()
    
    def paintEvent(self, event):
        """Override paint to add tick marks."""
        # Draw the standard progress bar first
        super().paintEvent(event)
        
        # Only draw ticks if we have multiple slides
        if self.tick_count <= 1:
            return
        
        # Draw tick marks for slide transitions
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set tick mark style
        pen = QPen(QColor(255, 255, 255, 180))  # White with some transparency
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Get progress bar dimensions
        width = self.width()
        height = self.height()
        
        # Draw tick marks at slide transition points
        # We want (tick_count - 1) tick marks between the slides
        for i in range(1, self.tick_count):
            # Calculate position as percentage of total width
            position_percent = i / self.tick_count
            x = int(width * position_percent)
            
            # Draw vertical line (tick mark)
            # Make it slightly shorter than the bar height
            y_start = 3
            y_end = height - 3
            painter.drawLine(x, y_start, x, y_end)
        
        painter.end()


class ProgressBarOverlay(QWidget):
    """
    A transparent overlay window that shows only the progress bar and timestamp.
    Fully modular with configurable margins and layout parameters.
    """
    
    def __init__(self, position='bottom', opacity=0.85, y_offset=0,
                 container_margin_left=50, container_margin_right=50,
                 container_margin_bottom=100, progress_bar_height=12,
                 progress_bar_color='#ffffff', progress_bar_bg_color='#000000',
                 progress_bar_bg_opacity=200, progress_bar_border_radius=0,
                 progress_bar_bg_blur=15, progress_bar_bg_width_extend=0,
                 progress_bar_bg_height_extend=0,
                 timestamp_distance=5, timestamp_font='Arial',
                 timestamp_font_size=12, timestamp_container_padding_left=0,
                 timestamp_container_padding_right=0):
        """
        Initialize the progress bar overlay.
        
        Args:
            position: Position of overlay ('bottom', 'top')
            opacity: Window opacity from 0.0 (transparent) to 1.0 (opaque)
            y_offset: Vertical offset in pixels (positive = up, negative = down)
            container_margin_left: Left margin of progress bar container in pixels
            container_margin_right: Right margin of progress bar container in pixels
            container_margin_bottom: Bottom margin of entire overlay in pixels
            progress_bar_height: Height of progress bar in pixels
            progress_bar_color: Color of progress bar fill in hex (e.g., '#ffffff')
            progress_bar_bg_color: Background color of progress bar container in hex
            progress_bar_bg_opacity: Background opacity of progress bar container (0-255, min 100 for blur)
            progress_bar_border_radius: Border radius for rounded corners in pixels (0=square)
            progress_bar_bg_blur: Blur radius for background (0-60)
            progress_bar_bg_width_extend: Additional width for background beyond progress bar in pixels (total, distributed equally on both sides)
            progress_bar_bg_height_extend: Additional height for background beyond progress bar in pixels (total, distributed equally on top/bottom)
            timestamp_distance: Distance between progress bar and timestamps in pixels
            timestamp_font: Font family for timestamps (e.g., 'Arial')
            timestamp_font_size: Font size for timestamps in points
            timestamp_container_padding_left: Left padding inside timestamp container in pixels
            timestamp_container_padding_right: Right padding inside timestamp container in pixels
        """
        super().__init__()
        
        self.position = position
        self.opacity_value = opacity
        self.y_offset = y_offset
        
        # Modular parameters
        self.container_margin_left = container_margin_left
        self.container_margin_right = container_margin_right
        self.container_margin_bottom = container_margin_bottom
        self.progress_bar_height = progress_bar_height
        self.progress_bar_color = progress_bar_color
        self.progress_bar_bg_color = progress_bar_bg_color
        self.progress_bar_bg_opacity = progress_bar_bg_opacity
        self.progress_bar_border_radius = progress_bar_border_radius
        self.progress_bar_bg_blur = progress_bar_bg_blur
        self.blur_radius = progress_bar_bg_blur  # Store as blur_radius for consistency
        self.progress_bar_bg_width_extend = progress_bar_bg_width_extend
        self.progress_bar_bg_height_extend = progress_bar_bg_height_extend
        self.timestamp_distance = timestamp_distance
        self.timestamp_font = timestamp_font
        self.timestamp_font_size = timestamp_font_size
        self.timestamp_container_padding_left = timestamp_container_padding_left
        self.timestamp_container_padding_right = timestamp_container_padding_right
        
        self.current_time = 0.0
        self.total_duration = 0.0
        self.slide_count = 1  # Number of slides in current dataset
        
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
        
        screen = QApplication.primaryScreen().geometry()
        # Height = progress bar + timestamp spacing + timestamp height + extra padding + bottom margin
        timestamp_height = self.timestamp_font_size + 20  # Font size + extra padding for safety
        overlay_height = self.progress_bar_height + self.timestamp_distance + timestamp_height + self.container_margin_bottom + 20
        self.setFixedSize(screen.width(), overlay_height)
    
    def _create_widgets(self):
        """Create the UI widgets for the overlay - background, progress bar, and timestamps."""
        # Calculate blur extension
        blur_extend = self.progress_bar_bg_blur * 2  # Extend on each side for blur
        
        # Main container with horizontal margins - reduced by blur extension to prevent clipping
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(
            max(0, self.container_margin_left - blur_extend),
            0,
            max(0, self.container_margin_right - blur_extend),
            self.container_margin_bottom
        )
        container_layout.setSpacing(5)
        
        # Create a wrapper to hold background and progress bar
        progress_wrapper = QWidget()
        progress_wrapper.setFixedHeight(self.progress_bar_height + (self.progress_bar_bg_blur * 2))
        # Allow children to extend beyond bounds (prevents blur clipping)
        progress_wrapper.setAttribute(Qt.WA_TranslucentBackground)
        progress_wrapper.setStyleSheet("background: transparent;")
        
        # Background rectangle widget (Method 3: QGraphicsBlurEffect on semi-transparent widget)
        self.background_rect = QWidget(progress_wrapper)
        
        # Convert progress bar bg color to rgba
        pb_bg_color = self.progress_bar_bg_color.lstrip('#')
        pb_bg_r = int(pb_bg_color[0:2], 16)
        pb_bg_g = int(pb_bg_color[2:4], 16)
        pb_bg_b = int(pb_bg_color[4:6], 16)
        
        # Use semi-transparent background (minimum 100 opacity for blur to be visible)
        bg_opacity = max(100, self.progress_bar_bg_opacity)
        
        self.background_rect.setStyleSheet(f"""
            QWidget {{
                background-color: rgba({pb_bg_r}, {pb_bg_g}, {pb_bg_b}, {bg_opacity});
                border-radius: {self.progress_bar_border_radius}px;
            }}
        """)
        
        # Apply QGraphicsBlurEffect to background widget
        if self.progress_bar_bg_blur > 0:
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(self.blur_radius)
            self.background_rect.setGraphicsEffect(blur_effect)
        
        # Progress bar on top (sharp, not blurred)
        self.progress_bar = TickedProgressBar(progress_wrapper)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(self.progress_bar_height)
        
        # Progress bar with transparent background, only the fill (chunk) is visible
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: {self.progress_bar_border_radius}px;
                background-color: transparent;
            }}
            QProgressBar::chunk {{
                background-color: {self.progress_bar_color};
                border-radius: {self.progress_bar_border_radius}px;
            }}
        """)
        
        # Position background and progress bar
        # Offset progress bar to account for blur extension in margins
        blur_padding = self.progress_bar_bg_blur
        x_offset = blur_extend  # Offset to compensate for reduced margins
        
        # Calculate background dimensions with extensions
        bg_width_offset = self.progress_bar_bg_width_extend // 2  # Distribute equally on both sides
        bg_height_offset = self.progress_bar_bg_height_extend // 2  # Distribute equally on top/bottom
        bg_width = 1920 + self.progress_bar_bg_width_extend
        bg_height = self.progress_bar_height + self.progress_bar_bg_height_extend
        
        # Background and progress bar positioned with offset to center them properly
        self.background_rect.setGeometry(x_offset - bg_width_offset, blur_padding - bg_height_offset, bg_width, bg_height)
        self.progress_bar.setGeometry(x_offset, blur_padding, 1920, self.progress_bar_height)
        
        # Ensure progress bar is on top
        self.background_rect.lower()
        self.progress_bar.raise_()
        
        # Store wrapper reference for later updates
        self.progress_wrapper = progress_wrapper
        
        container_layout.addWidget(progress_wrapper)
        
        # Timestamp container with horizontal layout for current time (left) and end time (right)
        # Add blur_extend to timestamp padding to align with progress bar
        timestamp_widget = QWidget()
        timestamp_widget.setStyleSheet("background: transparent;")
        timestamp_layout = QHBoxLayout()
        timestamp_layout.setContentsMargins(
            self.timestamp_container_padding_left + blur_extend,
            self.timestamp_distance,
            self.timestamp_container_padding_right + blur_extend,
            0
        )
        timestamp_layout.setSpacing(0)
        
        # Current time - leftmost
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setFont(QFont(self.timestamp_font, self.timestamp_font_size, QFont.Bold))
        self.current_time_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.current_time_label.setAlignment(Qt.AlignLeft)
        timestamp_layout.addWidget(self.current_time_label)
        
        # Spacer to push end time to the right
        timestamp_layout.addStretch()
        
        # End time - rightmost
        self.end_time_label = QLabel("0:00")
        self.end_time_label.setFont(QFont(self.timestamp_font, self.timestamp_font_size, QFont.Bold))
        self.end_time_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.end_time_label.setAlignment(Qt.AlignRight)
        timestamp_layout.addWidget(self.end_time_label)
        
        timestamp_widget.setLayout(timestamp_layout)
        container_layout.addWidget(timestamp_widget)
        
        container.setLayout(container_layout)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(container)
        
        self.setLayout(main_layout)
        self.progress_bar.setMaximum(100)
    
    def _position_window(self):
        """Position the window based on the position setting."""
        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        
        # Full width, so x is always 0
        x = 0

        # Calculate y position based on setting
        if self.position == 'bottom' or self.position == 'bottom-right':
            y = screen.height() - window_rect.height()
        elif self.position == 'top' or self.position == 'top-right':
            y = 0
        else:  # default to bottom
            y = screen.height() - window_rect.height()
        
        # Apply y_offset (positive moves up, negative moves down)
        y = max(0, min(screen.height() - window_rect.height(), y - self.y_offset))
        self.move(x, y)
    
    def update_progress(self, current_time, total_duration, slide_count=1):
        """
        Update the progress bar and timestamp.
        
        Args:
            current_time: Current playback time in seconds
            total_duration: Total duration in seconds
            slide_count: Number of slides in the dataset (for tick marks)
        """
        self.current_time = current_time
        self.total_duration = total_duration
        self.slide_count = slide_count
        
        # Update timestamps - separate current and end time
        current_str = self._format_time(current_time)
        total_str = self._format_time(total_duration)
        self.current_time_label.setText(current_str)
        self.end_time_label.setText(total_str)
        
        # Update progress bar (0-100)
        if total_duration > 0:
            progress = int((current_time / total_duration) * 100)
            progress = min(100, max(0, progress))
        else:
            progress = 0
        
        self.progress_bar.setValue(progress)
        self.progress_bar.set_tick_count(slide_count)
        
        # Update geometry to match wrapper width
        blur_padding = self.progress_bar_bg_blur
        blur_extend = blur_padding * 2
        x_offset = blur_extend
        wrapper_width = self.progress_wrapper.width()
        
        # Calculate actual progress bar width accounting for the offset on both sides
        actual_width = wrapper_width - (blur_extend * 2)
        
        # Calculate background dimensions with extensions
        bg_width_offset = self.progress_bar_bg_width_extend // 2
        bg_height_offset = self.progress_bar_bg_height_extend // 2
        bg_width = actual_width + self.progress_bar_bg_width_extend
        bg_height = self.progress_bar_height + self.progress_bar_bg_height_extend
        
        self.background_rect.setGeometry(x_offset - bg_width_offset, blur_padding - bg_height_offset, bg_width, bg_height)
        self.progress_bar.setGeometry(x_offset, blur_padding, actual_width, self.progress_bar_height)
    
    def _format_time(self, seconds):
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

