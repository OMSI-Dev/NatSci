"""
Progress Overlay GUI (PyQt5 version)
Displays a transparent overlay window with playback progress and timestamp information.
Designed to appear over LibreOffice presentations.
"""

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QProgressBar, QPushButton)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QPalette, QColor
import sys


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
        
        # Set window opacity
        self.setWindowOpacity(self.opacity_value)
        
        # Set window size
        self.setFixedSize(600, 120)
        
        # Dark background
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: white;
            }
        """)
    
    def _create_widgets(self):
        """Create the UI widgets for the overlay."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # Time display (current / total)
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.time_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.time_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444444;
                border-radius: 3px;
                background-color: #333333;
            }
            QProgressBar::chunk {
                background-color: #00aa00;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Subtitle display
        self.subtitle_label = QLabel("")
        self.subtitle_label.setFont(QFont('Arial', 11))
        self.subtitle_label.setStyleSheet("color: #ffff00;")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)
        
        # Frame counter (smaller, for debugging)
        self.frame_label = QLabel("Frame: 0")
        self.frame_label.setFont(QFont('Arial', 8))
        self.frame_label.setStyleSheet("color: #888888;")
        self.frame_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.frame_label)
        
        # Close button (small X in corner)
        close_btn = QPushButton("×")
        close_btn.setFont(QFont('Arial', 16, QFont.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        close_btn.setFixedSize(25, 25)
        close_btn.clicked.connect(self.close)
        close_btn.move(570, 5)
        
        self.setLayout(layout)
        
        # Enable mouse tracking for dragging
        self.drag_position = None
    
    def _position_window(self):
        """Position the window based on the position setting."""
        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        
        # Calculate position
        if self.position == 'bottom':
            x = (screen.width() - window_rect.width()) // 2
            y = screen.height() - window_rect.height() - 50
        elif self.position == 'top':
            x = (screen.width() - window_rect.width()) // 2
            y = 50
        elif self.position == 'bottom-right':
            x = screen.width() - window_rect.width() - 20
            y = screen.height() - window_rect.height() - 50
        elif self.position == 'top-right':
            x = screen.width() - window_rect.width() - 20
            y = 50
        else:  # default to bottom center
            x = (screen.width() - window_rect.width()) // 2
            y = screen.height() - window_rect.height() - 50
        
        self.move(x, y)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
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
