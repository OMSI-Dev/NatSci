"""
Subtitle Positioning Utility for Custom Movie Display

Interactive tool to test and adjust positioning of:
- Dual column subtitles (vertically centered)
- Timestamp (above progress bar)
- Progress bar (at bottom)

Controls:
  W/S - Move subtitles up/down
  A/D - Move timestamp up/down
  R - Reset to defaults
  P - Print current values
  X - Exit and save values to file
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QProgressBar, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class PositioningTestWidget(QWidget):
    """Test widget for positioning subtitle elements."""
    
    def __init__(self):
        super().__init__()
        
        # Default positioning values (as percentages of window height)
        self.subtitle_y_percent = 0.40  # 40% down = vertically centered
        self.timestamp_offset = 30  # 30px from bottom
        self.row_spacing = 10  # Spacing between subtitle rows in pixels
        
        self.window_height = None
        self.screen = None
        
        self._setup_window()
        self._create_widgets()
        self.update_positions()
        
        print("\n" + "="*60)
        print("Subtitle Positioning Test Utility")
        print("="*60)
        print("Controls:")
        print("  W/S - Move subtitles up/down (5% increments)")
        print("  Q/E - Decrease/Increase row spacing (5px increments)")
        print("  R - Reset to default positions")
        print("  P - Print current positioning values")
        print("  X or ESC - Exit and save values to file")
        print("="*60)
        print("\n⚠️  CLICK the window first to activate keyboard controls!\n")
        self.print_values()
    
    def _setup_window(self):
        """Configure window properties."""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        
        # Use transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.screen = QApplication.primaryScreen().geometry()
        self.window_height = int(self.screen.height() * 0.85)
        self.setFixedSize(self.screen.width(), self.window_height)
        
        # Position at bottom of screen
        x = 0
        y = self.screen.height() - self.window_height
        self.move(x, y)
        
        # Enable keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)
    
    def _create_widgets(self):
        """Create UI widgets."""
        # Create a simple layout (but we'll use absolute positioning)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Timestamp label
        self.time_label = QLabel("3:45 / 5:30")
        self.time_label.setParent(self)
        self.time_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.time_label.setStyleSheet("color: #ffffff; background: rgba(0, 0, 0, 150); padding: 5px;")
        self.time_label.setAlignment(Qt.AlignRight)
        
        # Subtitle label (dual column)
        self.subtitle_label = QLabel()
        self.subtitle_label.setParent(self)
        self.subtitle_label.setStyleSheet("background: transparent; padding: 20px;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        
        # Sample dual subtitle content (horizontal rows)
        html_content = f"""
        <div style='text-align: center;'>
            <div style='margin-bottom: {self.row_spacing}px;'>
                <span style='background: rgba(0, 0, 0, 150); color: #ffffff; padding: 10px; font-family: Arial; font-size: 14pt; font-weight: bold;'>Spanish subtitle text aquí para probar posición</span>
            </div>
            <div>
                <span style='background: rgba(0, 0, 0, 150); color: #ffff00; padding: 10px; font-family: Arial; font-size: 14pt;'>English subtitle text here for testing position</span>
            </div>
        </div>
        """
        self.subtitle_label.setText(html_content)
        
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(65)
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
        
        # Position progress bar at very bottom
        self.progress_bar.setGeometry(0, self.window_height - 12, self.screen.width(), 12)
        
        # Add status indicator
        self.status_label = QLabel("⚠️ CLICK WINDOW TO ACTIVATE | W/S=Subs | Q/E=Spacing | R=Reset | P=Print | X=Exit", self)
        self.status_label.setStyleSheet("color: #ffff00; background: rgba(255, 0, 0, 200); padding: 5px; font-family: Arial; font-size: 11pt; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setGeometry(0, 0, self.screen.width(), 35)
    
    def update_positions(self):
        """Update widget positions based on current values."""
        # Calculate subtitle Y position
        subtitle_y = int(self.window_height * self.subtitle_y_percent)
        # Dynamic height: base height + row spacing + extra padding to ensure bottom subtitle never clips
        subtitle_height = 150 + self.row_spacing + 50
        self.subtitle_label.setGeometry(0, subtitle_y, self.screen.width(), subtitle_height)
        
        # Update subtitle HTML with current row spacing
        html_content = f"""
        <div style='text-align: center;'>
            <div style='margin-bottom: {self.row_spacing}px;'>
                <span style='background: rgba(0, 0, 0, 150); color: #ffffff; padding: 10px; font-family: Arial; font-size: 14pt; font-weight: bold;'>Spanish subtitle text aquí para probar posición</span>
            </div>
            <div>
                <span style='background: rgba(0, 0, 0, 150); color: #ffff00; padding: 10px; font-family: Arial; font-size: 14pt;'>English subtitle text here for testing position</span>
            </div>
        </div>
        """
        self.subtitle_label.setText(html_content)
        
        # Calculate timestamp Y position
        timestamp_y = self.window_height - self.timestamp_offset
        self.time_label.setGeometry(0, timestamp_y, self.screen.width(), 20)
    
    def print_values(self):
        """Print current positioning values."""
        print(f"\nCurrent Positioning:")
        print(f"  Subtitle Y: {self.subtitle_y_percent:.2f} (as % of window height)")
        print(f"  Row spacing: {self.row_spacing}px")
        print(f"  Timestamp offset from bottom: {self.timestamp_offset}px")
        print(f"  Window height: {self.window_height}px ({int(self.window_height / self.screen.height() * 100)}% of screen)\n")
    
    def save_values(self):
        """Save current values to a file."""
        with open('positioning_values.txt', 'w') as f:
            f.write(f"# Subtitle Positioning Values (Horizontal Row Layout)\n")
            f.write(f"# Generated by Subtitle Positioning Utility\n\n")
            f.write(f"subtitle_y_percent = {self.subtitle_y_percent:.3f}\n")
            f.write(f"row_spacing = {self.row_spacing}\n")
            f.write(f"timestamp_offset = {self.timestamp_offset}\n")
            f.write(f"window_height_percent = 0.85\n")
        
        print(f"\n✓ Values saved to positioning_values.txt")
        print(f"\nTo apply in progressOverlay.py:")
        print(f"  1. In update_progress_custom_movie():")
        print(f"     - subtitle_y = int(window_height * {self.subtitle_y_percent:.3f})")
        print(f"     - row_spacing = {self.row_spacing}")
        print(f"     - timestamp_y = window_height - {self.timestamp_offset}")
    
    def mousePressEvent(self, event):
        """Handle mouse clicks to grab focus."""
        self.setFocus()
        self.status_label.setText("✓ ACTIVE | W/S=Subs | Q/E=Spacing | R=Reset | P=Print | X=Exit")
        self.status_label.setStyleSheet("color: #00ff00; background: rgba(0, 100, 0, 200); padding: 5px; font-family: Arial; font-size: 11pt; font-weight: bold;")
        print("\n✓ Window activated - keyboard controls enabled")
    
    def keyPressEvent(self, event):
        """Handle keyboard input."""
        key = event.key()
        
        if key == Qt.Key_W:
            self.subtitle_y_percent = max(0.1, self.subtitle_y_percent - 0.05)
            self.update_positions()
            print(f"↑ Subtitles: {self.subtitle_y_percent:.2f}")
            
        elif key == Qt.Key_S:
            self.subtitle_y_percent = min(0.8, self.subtitle_y_percent + 0.05)
            self.update_positions()
            print(f"↓ Subtitles: {self.subtitle_y_percent:.2f}")
            
        elif key == Qt.Key_Q:
            self.row_spacing = max(0, self.row_spacing - 5)
            self.update_positions()
            print(f"Row spacing: {self.row_spacing}px")
            
        elif key == Qt.Key_E:
            self.row_spacing = min(1000, self.row_spacing + 5)
            self.update_positions()
            print(f"Row spacing: {self.row_spacing}px")
            
        elif key == Qt.Key_R:
            self.subtitle_y_percent = 0.40
            self.timestamp_offset = 30
            self.row_spacing = 10
            self.update_positions()
            print("\n↻ Reset to defaults")
            self.print_values()
            
        elif key == Qt.Key_P:
            self.print_values()
            
        elif key == Qt.Key_X or key == Qt.Key_Escape:
            self.save_values()
            print("\nExiting...")
            self.close()
            QApplication.instance().quit()


def main():
    """Run the positioning test utility."""
    app = QApplication(sys.argv)
    widget = PositioningTestWidget()
    widget.show()
    widget.raise_()
    widget.activateWindow()
    widget.setFocus()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
