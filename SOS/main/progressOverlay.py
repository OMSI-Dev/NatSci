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
    
    def __init__(self, position='bottom', opacity=0.85, y_offset=0):
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
        self.current_subtitle2 = ""  # Secondary subtitle (Spanish)
        self.current_frame = 0
        self.slide_count = 1  # Number of slides in current dataset
        self.is_custom_movie_mode = False  # Track if layout has been modified for custom movies
        
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
        self.setFixedSize(screen.width(), 130)
    
    def _create_widgets(self):
        """Create the UI widgets for the overlay."""
        # Main layout for content
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(5)
        
        # Time display (current / total) - right aligned
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.time_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.time_label.setAlignment(Qt.AlignRight)
        self.time_label.setContentsMargins(10, 0, 10, 0)
        layout.addWidget(self.time_label)
        
        # Secondary subtitle display (Spanish) - shown on top
        self.subtitle_label2 = QLabel("")
        self.subtitle_label2.setFont(QFont('Arial', 12, QFont.Bold))
        self.subtitle_label2.setStyleSheet("color: #ffffff; background: rgba(0, 0, 0, 150); padding: 2px;")
        self.subtitle_label2.setWordWrap(True)
        self.subtitle_label2.setMinimumHeight(25)
        self.subtitle_label2.setContentsMargins(10, 0, 250, 0)  # Comfortable reading width for children
        self.subtitle_label2.setVisible(False)  # Hidden initially
        layout.addWidget(self.subtitle_label2)
        
        # Primary subtitle display (English) - shown below Spanish
        self.subtitle_label = QLabel("")
        self.subtitle_label.setFont(QFont('Arial', 12))
        self.subtitle_label.setStyleSheet("color: #ffff00; background: rgba(0, 0, 0, 150); padding: 2px;")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setMinimumHeight(25)
        self.subtitle_label.setContentsMargins(10, 0, 250, 0)  # Comfortable reading width for children
        self.subtitle_label.setVisible(False)  # Hidden initially
        layout.addWidget(self.subtitle_label)
        
        # Add stretch to push progress bar to bottom
        layout.addStretch()
        
        # Progress bar with tick marks - RED color, half height, at bottom
        self.progress_bar = TickedProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 0px;
                background-color: rgba(0, 0, 0, 200);
            }
            QProgressBar::chunk {
                background-color: #ff0000;
                border-radius: 0px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
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
    
    def _restore_layout_control(self):
        """Restore layout control for standard subtitle display after custom movie mode."""
        # Only restore if we were previously in custom movie mode
        if not self.is_custom_movie_mode:
            return  # Nothing to restore
        
        # Check current window size - if still in custom movie size, don't restore yet
        # (this handles cases where engine calls wrong method during loop)
        screen = QApplication.primaryScreen().geometry()
        current_height = self.size().height()
        custom_movie_height = int(screen.height() * 0.85)
        
        if abs(current_height - custom_movie_height) < 50:
            # Window is still custom movie sized - don't restore
            # This means we're still playing custom movies (likely looped)
            return
        
        current_layout = self.layout()
        
        # Check if we need to restore layout (it was emptied by custom movie mode)
        if current_layout is not None and current_layout.count() == 0:
            # Layout exists but is empty - just re-add widgets
            current_layout.addWidget(self.time_label)
            current_layout.addWidget(self.subtitle_label2)
            current_layout.addWidget(self.subtitle_label)
            current_layout.addStretch()  # Push progress bar to bottom
            current_layout.addWidget(self.progress_bar)
        
        # Reset window size to standard only if it's not already standard
        current_size = self.size()
        if current_size.width() != screen.width() or current_size.height() != 130:
            self.setFixedSize(screen.width(), 130)
            self._position_window()
        
        # Mark that we're back in standard mode
        self.is_custom_movie_mode = False
    
    def update_progress(self, current_time, total_duration, subtitle_text="", slide_count=1, subtitle_text2=""):
        """
        Update the progress display.
        Uses vertical two-column layout when both subtitles are present.
        
        Args:
            current_time: Current playback time in seconds
            total_duration: Total duration in seconds
            subtitle_text: Current subtitle text to display (primary/English)
            slide_count: Number of slides in the dataset (for tick marks)
            subtitle_text2: Secondary subtitle text to display (Spanish)
        """
        # Restore layout control for standard subtitle display
        # (custom movie mode removes layout control for absolute positioning)
        self._restore_layout_control()
        
        self.current_time = current_time
        self.total_duration = total_duration
        self.current_subtitle = subtitle_text
        self.current_subtitle2 = subtitle_text2
        self.slide_count = slide_count
        
        # Use vertical two-column layout when both subtitles are present
        if subtitle_text and subtitle_text2:
            self._update_ui_vertical()
        else:
            self._update_ui()
    
    def _update_ui_vertical(self):
        """Update UI with vertical two-column layout for dual subtitles."""
        current_str = self._format_time(self.current_time)
        total_str = self._format_time(self.total_duration)
        self.time_label.setText(f"{current_str} / {total_str}")
        
        # Update progress bar (0-100)
        if self.total_duration > 0:
            progress = int((self.current_time / self.total_duration) * 100)
            progress = min(100, max(0, progress))
        else:
            progress = 0
        
        self.progress_bar.setValue(progress)
        self.progress_bar.set_tick_count(self.slide_count)
        
        # Hide subtitle_label2, use only subtitle_label for two-column layout
        self.subtitle_label2.setVisible(False)
        self.subtitle_label.setVisible(True)
        
        # Reset to full width and no margins for fully centered vertical layout
        self.subtitle_label.setMaximumWidth(16777215)  # Qt's default QWIDGETSIZE_MAX
        self.subtitle_label.setContentsMargins(0, 0, 0, 0)  # No margins for centered dual layout
        
        # Create two-column layout with centered text
        english_display = self.current_subtitle if self.current_subtitle else ""
        spanish_display = self.current_subtitle2 if self.current_subtitle2 else ""
        
        # Use HTML table for precise column control
        html_content = f"""
        <table width='100%' style='border: none;'>
            <tr>
                <td width='50%' align='center' valign='middle' style='color: #ffff00; font-size: 14pt; padding: 15px;'>
                    {english_display}
                </td>
                <td width='50%' align='center' valign='middle' style='color: #ffffff; font-size: 14pt; padding: 15px;'>
                    {spanish_display}
                </td>
            </tr>
        </table>
        """
        
        self.subtitle_label.setText(html_content)
        self.subtitle_label.setStyleSheet("background: rgba(0, 0, 0, 180); font-family: Arial;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setMinimumHeight(100)
    
    def update_progress_custom_movie(self, current_time, total_duration, subtitle_text="", slide_count=1, subtitle_text2=""):
        """
        Update progress display for site-custom movies with dual captions.
        Subtitles vertically centered on screen, progress bar and timestamp at bottom.
        
        Args:
            current_time: Current playback time in seconds
            total_duration: Total duration in seconds
            subtitle_text: English subtitle text
            slide_count: Number of slides in the dataset (for tick marks)
            subtitle_text2: Spanish subtitle text
        """
        self.current_time = current_time
        self.total_duration = total_duration
        self.current_subtitle = subtitle_text
        self.current_subtitle2 = subtitle_text2
        self.slide_count = slide_count
        
        # Mark that we're in custom movie mode
        self.is_custom_movie_mode = True
        
        # CRITICAL: Remove layout control to allow absolute positioning
        # The VBoxLayout was overriding setGeometry() calls
        if self.layout() is not None:
            # Remove all widgets from layout control (but don't delete them)
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().setParent(self)  # Keep widget but remove from layout
        
        # Expand window height to nearly full screen, but keep it anchored at bottom
        screen = QApplication.primaryScreen().geometry()
        window_height = int(screen.height() * 0.85)  # 85% of screen height
        self.setFixedSize(screen.width(), window_height)
        
        # Position window at BOTTOM of screen (not centered)
        # This keeps progress bar and timestamp at screen bottom
        x = 0
        y = screen.height() - window_height
        self.move(x, y)
        
        # Update progress bar
        if total_duration > 0:
            progress = int((current_time / total_duration) * 100)
            progress = min(100, max(0, progress))
        else:
            progress = 0
        
        self.progress_bar.setValue(progress)
        self.progress_bar.set_tick_count(slide_count)
        
        # Position progress bar at absolute bottom using setGeometry
        self.progress_bar.setGeometry(0, window_height - 12, screen.width(), 12)
        
        # Update timestamp - position it right above progress bar using absolute positioning
        current_str = self._format_time(current_time)
        total_str = self._format_time(total_duration)
        self.time_label.setText(f"{current_str} / {total_str}")
        self.time_label.setAlignment(Qt.AlignRight)
        self.time_label.setContentsMargins(10, 0, 10, 0)  # Reset margins
        
        # Use absolute positioning for timestamp (place just above progress bar)
        timestamp_y = window_height - 40  # 40px from bottom (above progress bar)
        self.time_label.setGeometry(0, timestamp_y, screen.width(), 50)
        
        self.time_label.setVisible(True)
        self.progress_bar.setVisible(True)
        
        # Hide subtitle_label2, use only subtitle_label for two-column layout
        self.subtitle_label2.setVisible(False)
        self.subtitle_label.setVisible(True)
        
        # Use absolute positioning for subtitle label (vertically centered)
        subtitle_y = int(window_height * 0.30)  # 30% from top for vertical centering
        subtitle_height = 150
        self.subtitle_label.setGeometry(0, subtitle_y, screen.width(), subtitle_height)
        
        # Reset styling for custom movie centered display
        self.subtitle_label.setStyleSheet("background: transparent; padding: 20px;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setMaximumWidth(16777215)
        self.subtitle_label.setContentsMargins(0, 0, 0, 0)
        
        # Create two-column layout with text-only backgrounds (like standard display)
        english_display = subtitle_text if subtitle_text else ""
        spanish_display = subtitle_text2 if subtitle_text2 else ""
        
        # Use HTML table with inline-style backgrounds that only cover text
        html_content = f"""
        <table width='100%' style='border: none;'>
            <tr>
                <td width='50%' align='center' valign='middle' style='padding: 25px;'>
                    <span style='background: rgba(0, 0, 0, 150); color: #ffff00; padding: 10px; font-family: Arial; font-size: 14pt;'>► {english_display}</span>
                </td>
                <td width='50%' align='center' valign='middle' style='padding: 25px;'>
                    <span style='background: rgba(0, 0, 0, 150); color: #ffffff; padding: 10px; font-family: Arial; font-size: 14pt;'>► {spanish_display}</span>
                </td>
            </tr>
        </table>
        """
        
        self.subtitle_label.setText(html_content)
    
    def _update_ui(self):
        """Update UI elements with current values for standard single or stacked subtitle display."""
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
        
        # Reset subtitle labels to standard stacked layout styling
        # Show/hide labels based on whether we have content
        self.subtitle_label.setVisible(True)
        
        # Reset subtitle_label styling to standard (left-aligned, yellow text)
        # Container spans full width, but background only covers text
        self.subtitle_label.setStyleSheet("background: transparent; padding: 10px;")
        self.subtitle_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.subtitle_label.setWordWrap(True)  # Enable word wrapping for multiple lines
        self.subtitle_label.setMinimumHeight(100)  # Match dual subtitle height
        self.subtitle_label.setMaximumWidth(16777215)  # Reset to full width
        self.subtitle_label.setContentsMargins(10, 0, 250, 0)  # 250px right margin for children's museum
        
        # Reset subtitle_label2 styling to standard (left-aligned, white text)
        self.subtitle_label2.setStyleSheet("background: transparent; padding: 10px;")
        self.subtitle_label2.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.subtitle_label2.setWordWrap(True)  # Enable word wrapping for multiple lines
        self.subtitle_label2.setMinimumHeight(100)  # Match dual subtitle height
        self.subtitle_label2.setMaximumWidth(16777215)  # Reset to full width
        self.subtitle_label2.setContentsMargins(10, 0, 250, 0)  # 250px right margin for children's museum
        
        # Update secondary subtitle (Spanish) - shown on top
        if self.current_subtitle2:
            self.subtitle_label2.setVisible(True)
            # Simple span with background - QLabel word wrap handles multi-line
            html_text = f'<span style="background: rgba(0, 0, 0, 150); color: #ffffff; padding: 8px; font-family: Arial; font-size: 12pt;">► {self.current_subtitle2}</span>'
            self.subtitle_label2.setText(html_text)
        else:
            self.subtitle_label2.setVisible(False)  # Hide completely when no Spanish subtitle
            self.subtitle_label2.setText("")
        
        # Update primary subtitle (English) - shown below
        if self.current_subtitle:
            self.subtitle_label.setVisible(True)
            # Simple span with background - QLabel word wrap handles multi-line
            html_text = f'<span style="background: rgba(0, 0, 0, 150); color: #ffff00; padding: 8px; font-family: Arial; font-size: 12pt;">► {self.current_subtitle}</span>'
            self.subtitle_label.setText(html_text)
        else:
            self.subtitle_label.setVisible(False)  # Hide when no subtitle
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
