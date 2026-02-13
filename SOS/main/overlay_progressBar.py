"""
Progress Bar Overlay (PyQt5 version)
Displays only the progress bar with timestamp at the bottom of the screen.
"""

import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGraphicsBlurEffect, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QFontDatabase

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

class TickedProgressBar(QProgressBar):
    """Custom progress bar with tick marks for slide transitions and rounded corners."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tick_count = 1  # Number of slides (ticks at transitions)
        self.border_radius = 6  # Default border radius for rounded corners
        self.chunk_color = QColor(255, 255, 255)  # White by default
    
    def set_tick_count(self, count):
        """Set the number of slides (determines tick mark positions)."""
        self.tick_count = max(1, count)
        self.update()
    
    def set_border_radius(self, radius):
        """Set the border radius for rounded corners."""
        self.border_radius = radius
        self.update()
    
    def set_chunk_color(self, color):
        """Set the chunk/fill color."""
        if isinstance(color, str):
            # Parse hex color
            color = color.lstrip('#')
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            self.chunk_color = QColor(r, g, b)
        else:
            self.chunk_color = color
        self.update()
    
    def paintEvent(self, event):
        """Custom paint with rounded corners for the progress chunk."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get dimensions
        width = self.width()
        height = self.height()
        
        # Calculate progress width
        progress = self.value()
        maximum = self.maximum()
        if maximum > 0:
            progress_width = int((progress / maximum) * width)
        else:
            progress_width = 0
        
        # Draw the progress chunk with rounded corners
        if progress_width > 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.chunk_color)
            
            # Use border radius, but ensure it doesn't exceed half the height
            radius = min(self.border_radius, height // 2)
            
            # Draw rounded rectangle for progress
            # When progress is less than 100%, only round the left side fully
            # Right side should be rounded only when at 100%
            if progress >= maximum:
                # Full progress - round all corners
                painter.drawRoundedRect(0, 0, progress_width, height, radius, radius)
            else:
                # Partial progress - round left corners, square right edge
                # We'll draw a rounded rect and then overlay a square on the right
                painter.drawRoundedRect(0, 0, progress_width + radius, height, radius, radius)
                # Cover the right rounded part with a square
                if progress_width > radius:
                    painter.drawRect(progress_width, 0, radius, height)
        
        # Draw tick marks for slide transitions if we have multiple slides
        if self.tick_count > 1:
            pen = QPen(QColor(255, 255, 255, 180))  # White with some transparency
            pen.setWidth(2)
            painter.setPen(pen)
            
            # Draw tick marks at slide transition points
            for i in range(1, self.tick_count):
                position_percent = i / self.tick_count
                x = int(width * position_percent)
                
                # Draw vertical line (tick mark)
                y_start = 3
                y_end = height - 3
                painter.drawLine(x, y_start, x, y_end)
        
        painter.end()


class ProgressBarOverlay(QWidget):
    """
    Simplified progress bar overlay with direct control over all dimensions.
    Every parameter directly affects what you see - no hidden layout surprises.
    """
    
    def __init__(self, position='bottom', y_offset=0,
                 margin_left=100, margin_right=100, margin_bottom=22,
                 bar_height=7, bar_color='#ffffff',
                 bg_color='#000000', bg_opacity=125, bg_blur=7,
                 bg_extra_width=20, bg_extra_height=20,
                 border_radius=6,
                 timestamp_spacing=15, timestamp_font=None, timestamp_size=16):
       
        """
            Control width of progress bar and background with margin_left and margin_right.
             - The progress bar will always stretch to fill the space between these margins.
                - The background will also stretch, but you can add extra width with bg_extra_width.
        """
        super().__init__()

        
        # Store all parameters
        self.position = position
        self.y_offset = y_offset
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom
        self.bar_height = bar_height
        self.bar_color = bar_color
        self.bg_color = bg_color
        self.bg_opacity = bg_opacity
        self.bg_blur = bg_blur
        self.bg_extra_width = bg_extra_width
        self.bg_extra_height = bg_extra_height
        self.border_radius = border_radius
        self.timestamp_spacing = timestamp_spacing
        self.timestamp_font = timestamp_font if timestamp_font else get_inter_font()
        self.timestamp_size = timestamp_size
        
        # State
        self.current_time = 0.0
        self.total_duration = 0.0
        self.slide_count = 1
        self.target_time = 0.0
        self.last_update_timestamp = 0.0
        self.fade_animation = None
        
        # Setup
        self._setup_window()
        self._create_ui()
        
        # 60 FPS update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(16)
    
    def _setup_window(self):
        """Setup transparent overlay window."""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Calculate total height needed
        screen = QApplication.primaryScreen().geometry()
        bg_height = self.bar_height + self.bg_extra_height
        total_height = bg_height + (self.bg_blur * 2) + self.timestamp_spacing + self.timestamp_size + 30 + self.margin_bottom
        
        self.setFixedSize(screen.width(), int(total_height))
    
    def _create_ui(self):
        """Create UI with direct positioning - no complex layouts."""
        screen_width = QApplication.primaryScreen().geometry().width()
        
        # Calculate dimensions
        # Base width (screen minus margins)
        base_width = screen_width - self.margin_left - self.margin_right
        
        # Progress bar uses base width
        bar_width = base_width
        
        # Background width = base + bg_extra_width
        bg_width = base_width + self.bg_extra_width
        bg_height = self.bar_height + self.bg_extra_height
        
        # Positions (Y coordinates from top of window)
        bg_y = self.bg_blur
        bar_y = bg_y + (self.bg_extra_height // 2)
        timestamp_y = bar_y + self.bar_height + self.timestamp_spacing
        
        # Background rectangle with blur
        self.background = QWidget(self)
        self.background.setStyleSheet(f"""
            background-color: rgba{self._hex_to_rgba(self.bg_color, self.bg_opacity)};
            border-radius: {self.border_radius}px;
        """)
        self.background.setGeometry(
            self.margin_left - (self.bg_extra_width // 2),
            bg_y,
            bg_width,
            bg_height
        )
        
        if self.bg_blur > 0:
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(self.bg_blur)
            self.background.setGraphicsEffect(blur_effect)
        
        # Progress bar - DIRECT SIZE CONTROL
        self.progress_bar = TickedProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(10000)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        
        # This is THE definitive way to set height in Qt
        self.progress_bar.setFixedSize(bar_width, self.bar_height)
        self.progress_bar.move(self.margin_left, bar_y)
        
        self.progress_bar.set_border_radius(self.border_radius)
        self.progress_bar.set_chunk_color(self.bar_color)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background: transparent; }")
        
        # Timestamps
        self.time_current = QLabel("0:00", self)
        self.time_current.setFont(QFont(self.timestamp_font, self.timestamp_size, QFont.Bold))
        self.time_current.setStyleSheet("color: white;")
        self.time_current.move(self.margin_left, timestamp_y)
        
        self.time_total = QLabel("0:00", self)
        self.time_total.setFont(QFont(self.timestamp_font, self.timestamp_size, QFont.Bold))
        self.time_total.setStyleSheet("color: white;")
        self.time_total.setAlignment(Qt.AlignRight)
        
        # Position total time at right edge
        self.time_total.adjustSize()
        self.time_total.move(self.margin_left + bar_width - self.time_total.width(), timestamp_y)
        
        # Raise progress bar above background
        self.progress_bar.raise_()
    
    def _hex_to_rgba(self, hex_color, alpha):
        """Convert hex color and alpha to rgba string."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"({r}, {g}, {b}, {alpha})"
    
    def _position_window(self):
        """Position window on screen."""
        screen = QApplication.primaryScreen().geometry()
        
        if self.position == 'bottom':
            y = screen.height() - self.height() - self.y_offset
        else:
            y = self.y_offset
        
        self.move(0, max(0, y))
    
    def update_progress(self, current_time, total_duration, slide_count=1):
        """Update progress data."""
        import time
        now = time.time()
        
        if abs(current_time - self.current_time) > 2.0 or self.total_duration <= 0:
            self.current_time = current_time
        
        self.target_time = current_time
        self.total_duration = total_duration
        self.slide_count = slide_count
        self.last_update_timestamp = now
        
        self.time_total.setText(self._format_time(total_duration))
        self.progress_bar.set_tick_count(slide_count)
        
        # Reposition total time label (width may have changed)
        self.time_total.adjustSize()
        bar_width = self.width() - self.margin_left - self.margin_right
        timestamp_y = self.bg_blur + (self.bg_extra_height // 2) + self.bar_height + self.timestamp_spacing
        self.time_total.move(self.margin_left + bar_width - self.time_total.width(), timestamp_y)
    
    def _update(self):
        """Update display every frame."""
        if self.total_duration <= 0:
            return
        
        # Interpolate time
        import time
        now = time.time()
        elapsed = now - self.last_update_timestamp
        predicted_time = min(self.target_time + elapsed, self.total_duration)
        self.current_time = predicted_time
        
        # Update UI
        self.time_current.setText(self._format_time(self.current_time))
        
        if self.total_duration > 0:
            progress = int((self.current_time / self.total_duration) * 10000)
            self.progress_bar.setValue(min(10000, max(0, progress)))
    
    def _format_time(self, seconds):
        """Format seconds as M:SS or H:MM:SS."""
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def is_active(self):
        """Check if overlay is visible."""
        return self.isVisible()
    
    def start(self):
        """Show with fade-in."""
        self._position_window()
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(400)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()
        
        QApplication.processEvents()
    
    def stop(self):
        """Hide with fade-out."""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()
