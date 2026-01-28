"""
Test script for separated progress bar and subtitle overlays.
Use Ctrl+C in terminal to exit.
"""

import sys
import signal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from overlay_progressBar import ProgressBarOverlay
from overlay_subtitles import SubtitleOverlay


# ============================================================================
PROGRESS_POSITION = 'bottom'
PROGRESS_OPACITY = 0.1
PROGRESS_CONTAINER_MARGIN_LEFT = 150
PROGRESS_CONTAINER_MARGIN_RIGHT = 150
PROGRESS_CONTAINER_MARGIN_BOTTOM = 82
PROGRESS_BAR_HEIGHT = 12
PROGRESS_BAR_COLOR = '#ffffff'
PROGRESS_BAR_BG_COLOR = '#000000'
PROGRESS_BAR_BG_OPACITY = 160          # 0-255 
PROGRESS_BAR_BORDER_RADIUS = 6
PROGRESS_BAR_BG_BLUR = 13              # 0-60 blur radius 
TIMESTAMP_DISTANCE = 5
TIMESTAMP_FONT = 'Arial'
TIMESTAMP_FONT_SIZE = 14
TIMESTAMP_CONTAINER_PADDING_LEFT = 0
TIMESTAMP_CONTAINER_PADDING_RIGHT = 0

# ============================================================================
SUBTITLE_POSITION = 'top'
SUBTITLE_OPACITY = 0.1
SUBTITLE_Y_OFFSET = 0

# Container sizing
PARENT_CONTAINER_WIDTH_PERCENT = 1.0    # % screen width 
PARENT_CONTAINER_HEIGHT = 0.9           # % screen height
COLUMN_HEIGHT_PERCENT = 1.0             # % parent container height

# Column layout
LEFT_COLUMN_WIDTH_PERCENT = 0.5         # % width for columns
COLUMN_SPACING = 0

# Padding
COLUMN_HORIZONTAL_PADDING = 200
COLUMN_TOP_PADDING = 0
COLUMN_BOTTOM_PADDING = 20

# Subtitle styling (applies to both columns)
SUBTITLE_FONT_SIZE = 18
SUBTITLE_FONT_FAMILY = 'Arial'
SUBTITLE_FONT_BOLD = False
SUBTITLE_TEXT_COLOR = '#ffffff'
SUBTITLE_BG_OPACITY = 0                 # 0-255 (0=transparent, 255=opaque)
SUBTITLE_ALIGNMENT = 'center'           # 'left', 'center', 'right'
SUBTITLE_TOP_SPACING = 20
TEXT_PADDING = 8

# Title row configuration
SHOW_TITLE_ROW = True
LEFT_TITLE = 'English'
RIGHT_TITLE = 'Español'
TITLE_HEIGHT = 200
TITLE_FONT_SIZE = 40
TITLE_FONT_FAMILY = 'Arial'
TITLE_FONT_BOLD = True
LEFT_TITLE_COLOR = '#ffffff'
RIGHT_TITLE_COLOR = '#ffffff'
TITLE_BG_OPACITY = 0                    # 0-255 (0=transparent, 255=opaque)
TITLE_ALIGNMENT = 'center'              # 'left', 'center', 'right'
TITLE_TOP_SPACING = 100
LEFT_TITLE_PADDING = 8
RIGHT_TITLE_PADDING = 8

# Debug
SHOW_DEBUG_BORDERS = False

# ============================================================================


# Global references for signal handler
progress_overlay = None
subtitle_overlay = None


def signal_handler(sig, frame):
    """Handle Ctrl+C to exit cleanly."""
    print("\n\nExiting overlays...")
    if progress_overlay:
        progress_overlay.stop()
    if subtitle_overlay:
        subtitle_overlay.stop()
    QApplication.quit()
    sys.exit(0)


def test_overlays():
    """Test both overlay components together."""
    global progress_overlay, subtitle_overlay
    
    # Set up Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize Qt application
    app = QApplication(sys.argv)
    
    # Create progress bar overlay using parameters defined at top of file
    progress_overlay = ProgressBarOverlay(
        position=PROGRESS_POSITION,
        opacity=PROGRESS_OPACITY,
        container_margin_left=PROGRESS_CONTAINER_MARGIN_LEFT,
        container_margin_right=PROGRESS_CONTAINER_MARGIN_RIGHT,
        container_margin_bottom=PROGRESS_CONTAINER_MARGIN_BOTTOM,
        progress_bar_height=PROGRESS_BAR_HEIGHT,
        progress_bar_color=PROGRESS_BAR_COLOR,
        progress_bar_bg_color=PROGRESS_BAR_BG_COLOR,
        progress_bar_bg_opacity=PROGRESS_BAR_BG_OPACITY,
        progress_bar_border_radius=PROGRESS_BAR_BORDER_RADIUS,
        progress_bar_bg_blur=PROGRESS_BAR_BG_BLUR,
        timestamp_distance=TIMESTAMP_DISTANCE,
        timestamp_font=TIMESTAMP_FONT,
        timestamp_font_size=TIMESTAMP_FONT_SIZE,
        timestamp_container_padding_left=TIMESTAMP_CONTAINER_PADDING_LEFT,
        timestamp_container_padding_right=TIMESTAMP_CONTAINER_PADDING_RIGHT
    )
    
    # Create subtitle overlay using parameters defined at top of file
    subtitle_overlay = SubtitleOverlay(
        position=SUBTITLE_POSITION,
        opacity=SUBTITLE_OPACITY,
        y_offset=SUBTITLE_Y_OFFSET,
        parent_container_width_percent=PARENT_CONTAINER_WIDTH_PERCENT,
        parent_container_height=PARENT_CONTAINER_HEIGHT,
        column_height_percent=COLUMN_HEIGHT_PERCENT,
        left_column_width_percent=LEFT_COLUMN_WIDTH_PERCENT,
        column_spacing=COLUMN_SPACING,
        column_horizontal_padding=COLUMN_HORIZONTAL_PADDING,
        column_top_padding=COLUMN_TOP_PADDING,
        column_bottom_padding=COLUMN_BOTTOM_PADDING,
        subtitle_font_size=SUBTITLE_FONT_SIZE,
        subtitle_font_family=SUBTITLE_FONT_FAMILY,
        subtitle_font_bold=SUBTITLE_FONT_BOLD,
        subtitle_text_color=SUBTITLE_TEXT_COLOR,
        subtitle_bg_opacity=SUBTITLE_BG_OPACITY,
        subtitle_alignment=SUBTITLE_ALIGNMENT,
        subtitle_top_spacing=SUBTITLE_TOP_SPACING,
        text_padding=TEXT_PADDING,
        show_title_row=SHOW_TITLE_ROW,
        left_title=LEFT_TITLE,
        right_title=RIGHT_TITLE,
        title_height=TITLE_HEIGHT,
        title_font_size=TITLE_FONT_SIZE,
        title_font_family=TITLE_FONT_FAMILY,
        title_font_bold=TITLE_FONT_BOLD,
        left_title_color=LEFT_TITLE_COLOR,
        right_title_color=RIGHT_TITLE_COLOR,
        title_bg_opacity=TITLE_BG_OPACITY,
        title_alignment=TITLE_ALIGNMENT,
        title_top_spacing=TITLE_TOP_SPACING,
        left_title_padding=LEFT_TITLE_PADDING,
        right_title_padding=RIGHT_TITLE_PADDING,
        show_debug_borders=SHOW_DEBUG_BORDERS
    )
    
    # Show both overlays
    progress_overlay.start()
    subtitle_overlay.start()
    
    # Test data
    current_time = 45.0
    total_duration = 120.0
    subtitle_text = "Environmental science is an interdisciplinary field integrating biology, chemistry, and physics to study ecosystems, environmental problems, and solutions. It examines natural, built, and social environments, focusing on topics like climate change, sustainability, and biodiversity. Key areas include atmospheric science, ecology, and environmental chemistry, which analyze human impacts on Earth. "
    subtitle_text2 = "Officiet aut aspe veles vit quisquis exerum inciis ea dionseque velitiorpora pliqui nis es ex et et atem sum faccum, consequo blabore num eum que plitaquaerem que audandam vendit anderum fugitatem fugit aut pa nectiorum hiliquat. Officiet aut aspe veles vit quisquis exerum inciis ea dionseque velitiorpora pliqui nis es ex et et atem sum faccum, consequo blabore num eum que plitaquaerem que audandam vendit anderum fugitatem fugit aut pa nectiorum hiliquat."
    slide_count = 3
    
    # Update progress bar
    progress_overlay.update_progress(current_time, total_duration, slide_count)
    
    # Update subtitles (two-column layout)
    subtitle_overlay.update_subtitles(subtitle_text, subtitle_text2)
    
    print("\n" + "="*60)
    print("Overlays running with modular parameters.")
    print("Adjust parameters in the code to customize layout.")
    print("Press Ctrl+C in this terminal to exit.")
    print("="*60 + "\n")
    
    # Create a timer to allow Ctrl+C to be processed
    timer = QTimer()
    timer.start(100)
    timer.timeout.connect(lambda: None)
    
    # Run application
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == '__main__':
    test_overlays()
