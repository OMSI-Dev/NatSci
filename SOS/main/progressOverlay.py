"""
Progress Overlay GUI (PyQt5 version)
Displays a transparent overlay window with playback progress and timestamp information.
Designed to appear over LibreOffice presentations.
"""

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QProgressBar, QPushButton, QGraphicsBlurEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QBrush, QLinearGradient
import sys
import ctypes
from ctypes import c_int, byref, sizeof


class ProgressOverlay(QWidget):
    """
    A transparent/semi-transparent overlay window that shows playback progress.
    """
    
    def __init__(self, position='bottom', opacity=0.85):
        """
        Initialize the progress overlay.
        
        Args:
            position: Position of overlay ('bottom', 'top', 'bottom-right', 'top-right')
            opacity: Window opacity from 0.0 (transparent) to 1.0 (opaque)
        """
        super().__init__()
        
        self.position = position
        self.opacity_value = opacity
        
        # Current state
        self.current_time = 0.0
        self.total_duration = 0.0
        self.current_subtitle = ""
        self.current_frame = 0
        
        self._setup_window()
        self._create_widgets()
        self._position_window()
    
    def _setup_window(self):
        """Configure window properties for overlay appearance."""
        # Window flags: stay on top, frameless, tool window
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        
        # Fully transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Get screen width and set window to full width with extra height for subtitles
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
        
        # Progress bar - desaturated purple/magenta color
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: rgba(42, 42, 42, 200);
            }
            QProgressBar::chunk {
                background-color: #9B6B9E;
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
        
        # Frame counter (smaller, for debugging)
        self.frame_label = QLabel("Frame: 0")
        self.frame_label.setFont(QFont('Arial', 8))
        self.frame_label.setStyleSheet("color: #888888; background: transparent;")
        self.frame_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.frame_label)
        
        self.setLayout(layout)
    
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
        
        self.move(x, y)
    
    def update_progress(self, current_time, total_duration, subtitle_text="", current_frame=None):
        """
        Update the progress display.
        
        Args:
            current_time: Current playback time in seconds
            total_duration: Total duration in seconds
            subtitle_text: Current subtitle text to display
            current_frame: Optional frame number
        """
        self.current_time = current_time
        self.total_duration = total_duration
        self.current_subtitle = subtitle_text
        self.current_frame = current_frame if current_frame is not None else 0
        
        # Update UI elements
        self._update_ui()
    
    def _update_ui(self):
        """Update UI elements with current values."""
        # Update time label
        current_str = self._format_time(self.current_time)
        total_str = self._format_time(self.total_duration)
        self.time_label.setText(f"{current_str} / {total_str}")
        
        # Update progress bar
        if self.total_duration > 0:
            progress = int((self.current_time / self.total_duration) * 100)
            progress = min(100, max(0, progress))
        else:
            progress = 0
        self.progress_bar.setValue(progress)
        
        # Update subtitle
        if self.current_subtitle:
            self.subtitle_label.setText(f"► {self.current_subtitle}")
        else:
            self.subtitle_label.setText("")
        
        # Update frame counter
        if self.current_frame > 0:
            self.frame_label.setText(f"Frame: {self.current_frame}")
        else:
            self.frame_label.setText("")
    
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


# Test the overlay if run directly
if __name__ == "__main__":
    import time
    
    print("Testing Progress Overlay (PyQt5 version)...")
    print("Overlay will appear on screen for 30 seconds with simulated progress.")
    
    app = QApplication(sys.argv)
    overlay = ProgressOverlay(position='bottom', opacity=0.85)
    overlay.start()
    
    # Simulate playback for 30 seconds
    total_duration = 30.0
    
    timer = QTimer()
    counter = [0]  # Use list to allow modification in closure
    
    def update():
        current_time = counter[0] / 10.0
        frame = counter[0] * 3  # Simulate 30 fps
        
        # Simulate subtitle appearance
        if 5 < current_time < 10:
            subtitle = "This is a test subtitle that appears during playback"
        elif 15 < current_time < 20:
            subtitle = "Another subtitle appears here to test the display"
        else:
            subtitle = ""
        
        overlay.update_progress(current_time, total_duration, subtitle, frame)
        
        counter[0] += 1
        if counter[0] >= 300:  # 30 seconds at 10 updates per second
            timer.stop()
            print("\nTest complete. Closing overlay...")
            overlay.close()
            app.quit()
    
    timer.timeout.connect(update)
    timer.start(100)  # Update every 100ms
    
    sys.exit(app.exec_())
