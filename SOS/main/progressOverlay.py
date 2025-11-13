"""
Progress Overlay GUI (PyQt5 version)
Displays a transparent overlay window with playback progress and timestamp information.
Designed to appear over LibreOffice presentations.
"""

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QRect
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


class ProgressOverlay(QWidget):
    """
    A transparent/semi-transparent overlay window that shows playback progress.
    """
    
    def __init__(self, position='bottom', opacity=0.85, y_offset=35):
        """
        Initialize the progress overlay.
        
        Args:
            position: Position of overlay ('bottom', 'top', 'bottom-right', 'top-right')
            opacity: Window opacity from 0.0 (transparent) to 1.0 (opaque)
            y_offset: Vertical offset in pixels (positive = up, negative = down)
        """
        super().__init__()
        
        self.position = position
        self.opacity_value = opacity
        self.y_offset = y_offset
        
        self.current_time = 0.0
        self.total_duration = 0.0
        self.current_subtitle = ""
        self.current_frame = 0
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
        self.setFixedSize(screen.width(), 180)
    
    def _create_widgets(self):
        """Create the UI widgets for the overlay."""
        # Main layout for content
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(8)
        
        # Time display (current / total) - right aligned
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.time_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.time_label)
        
        # Progress bar with tick marks - desaturated purple/magenta color
        self.progress_bar = TickedProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #210dff;
                border-radius: 2px;
                background-color: rgba(0, 0, 0, 200);
            }
            QProgressBar::chunk {
                background-color: #210dff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Subtitle display - allow more height for wrapping
        self.subtitle_label = QLabel("")
        self.subtitle_label.setFont(QFont('Arial', 12))
        self.subtitle_label.setStyleSheet("color: #ffff00; background: transparent;")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setMinimumHeight(50)  # Allow space for multiple lines
        layout.addWidget(self.subtitle_label)
        
        # # Frame counter (smaller, for debugging)
        # self.frame_label = QLabel("Frame: 0")
        # self.frame_label.setFont(QFont('Arial', 8))
        # self.frame_label.setStyleSheet("color: #888888; background: transparent;")
        # self.frame_label.setAlignment(Qt.AlignRight)
        # layout.addWidget(self.frame_label)
        
        self.setLayout(layout)
        
        # Standard progress bar (0-100)
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
    
    def update_progress(self, current_time, total_duration, subtitle_text="", slide_count=1):
        """
        Update the progress display.
        
        Args:
            current_time: Current playback time in seconds
            total_duration: Total duration in seconds
            subtitle_text: Current subtitle text to display
            slide_count: Number of slides in the dataset (for tick marks)
        """
        self.current_time = current_time
        self.total_duration = total_duration
        self.current_subtitle = subtitle_text
        self.slide_count = slide_count
        
        self._update_ui()
    
    def _update_ui(self):
        """Update UI elements with current values."""
        current_str = self._format_time(self.current_time)
        total_str = self._format_time(self.total_duration)
        self.time_label.setText(f"{current_str} / {total_str}")
        
        # Update progress bar (0-100)
        if self.total_duration > 0:
            progress = int((self.current_time / self.total_duration) * 100)
            progress = min(100, max(0, progress))
        else:
            progress = 0
            #initialize with duration timer 
        
        self.progress_bar.setValue(progress)
        self.progress_bar.set_tick_count(self.slide_count) #multiple slides
        
        if self.current_subtitle:
            self.subtitle_label.setText(f"► {self.current_subtitle}")
        else:
            self.subtitle_label.setText("")
        
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
    
    def stop(self):
        """Close the overlay window."""
        self.close()
