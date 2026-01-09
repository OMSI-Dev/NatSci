"""
Test script for Nature's Harmonious Relationships subtitle layouts.
Tests both vertical and horizontal layout modes with actual .srt files.

Controls:
  V - Switch to Vertical layout
  H - Switch to Horizontal layout
  N - Next subtitle (advance time)
  P - Previous subtitle (go back)
  + - Advance 5 seconds
  - - Go back 5 seconds
  J - Jump to specific time
  R - Reset to beginning
  X - Exit

This script simulates the subtitle display for the custom clip
to verify proper formatting before deployment.
"""

import sys
import os
import time

# Add main directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'main'))

from PyQt5.QtWidgets import QApplication
from progressOverlay import ProgressOverlay
from subtitles import SubtitleManager, parse_srt_file, get_duration_from_subtitles


def update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time):
    """Update the display with current layout and time."""
    # Find active subtitles at this time
    english_text = ""
    spanish_text = ""
    
    for sub in subtitles_en:
        if sub['start_time'] <= current_time <= sub['end_time']:
            english_text = sub['text']
            break
    
    for sub in subtitles_es:
        if sub['start_time'] <= current_time <= sub['end_time']:
            spanish_text = sub['text']
            break
    
    # Debug output
    print(f"\n[DEBUG] Time: {current_time:.1f}s / {duration:.1f}s ({(current_time/duration*100):.1f}%)")
    print(f"[DEBUG] English: {english_text if english_text else '(none)'}")
    print(f"[DEBUG] Spanish: {spanish_text if spanish_text else '(none)'}")
    
    # Update the overlay with harmonious layout (horizontal or vertical)
    overlay.update_progress_harmonious(
        current_time, duration, 
        english_text, 1, spanish_text, 
        layout_mode
    )
    
    # Manually show the progress bar and time label (harmonious mode hides them by default)
    overlay.progress_bar.setVisible(True)
    overlay.time_label.setVisible(True)
    
    # Update progress bar value
    if duration > 0:
        progress = int((current_time / duration) * 100)
        progress = min(100, max(0, progress))
        overlay.progress_bar.setValue(progress)
    
    # Update time label
    current_str = overlay._format_time(current_time)
    total_str = overlay._format_time(duration)
    overlay.time_label.setText(f"{current_str} / {total_str}")
    
    # Print status
    layout_display = "VERTICAL (columns)" if layout_mode == 'vertical' else "HORIZONTAL (rows)"
    print(f"[{layout_display}] Display updated with progress bar")


def find_next_subtitle_time(subtitles_en, subtitles_es, current_time):
    """Find the start time of the next subtitle."""
    next_times = []
    
    for sub in subtitles_en:
        if sub['start_time'] > current_time:
            next_times.append(sub['start_time'])
    
    for sub in subtitles_es:
        if sub['start_time'] > current_time:
            next_times.append(sub['start_time'])
    
    return min(next_times) if next_times else current_time


def find_previous_subtitle_time(subtitles_en, subtitles_es, current_time):
    """Find the start time of the previous subtitle."""
    prev_times = []
    
    for sub in subtitles_en:
        if sub['start_time'] < current_time - 0.1:  # Small buffer to avoid same subtitle
            prev_times.append(sub['start_time'])
    
    for sub in subtitles_es:
        if sub['start_time'] < current_time - 0.1:
            prev_times.append(sub['start_time'])
    
    return max(prev_times) if prev_times else 0.0


def main():
    """Main test function."""
    print("=" * 80)
    print("Nature's Harmonious Relationships - Subtitle Layout Test")
    print("=" * 80)
    print()
    
    # Load the actual .srt files from same directory as script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    english_srt = os.path.join(script_dir, "Harmonious_English.srt")
    spanish_srt = os.path.join(script_dir, "Harmonious_Spanish.srt")
    
    print(f"Script directory: {script_dir}")
    print(f"Looking for English: {english_srt}")
    print(f"  File exists: {os.path.exists(english_srt)}")
    print(f"Looking for Spanish: {spanish_srt}")
    print(f"  File exists: {os.path.exists(spanish_srt)}")
    print()
    
    # List all .srt files in the directory
    print("Files in script directory:")
    try:
        all_files = os.listdir(script_dir)
        srt_files = [f for f in all_files if f.endswith('.srt')]
        if srt_files:
            for f in srt_files:
                print(f"  - {f}")
        else:
            print("  (no .srt files found)")
    except Exception as e:
        print(f"  Error listing directory: {e}")
    print()
    
    print(f"Loading English subtitles: {os.path.basename(english_srt)}")
    subtitles_en = parse_srt_file(english_srt)
    
    print(f"Loading Spanish subtitles: {os.path.basename(spanish_srt)}")
    subtitles_es = parse_srt_file(spanish_srt)
    
    if not subtitles_en or not subtitles_es:
        print("\n✗ Error: Could not load subtitle files!")
        print(f"  Expected location: {script_dir}")
        print(f"  English file: {english_srt}")
        print(f"  Spanish file: {spanish_srt}")
        print("\nPlease ensure both files are in the same directory as this script.")
        return
    
    # Get duration from subtitles
    duration = max(get_duration_from_subtitles(subtitles_en), 
                   get_duration_from_subtitles(subtitles_es))
    
    print(f"\n✓ Loaded {len(subtitles_en)} English subtitles")
    print(f"✓ Loaded {len(subtitles_es)} Spanish subtitles")
    print(f"✓ Total duration: {duration:.1f} seconds")
    print()
    print("=" * 80)
    print("CONTROLS:")
    print("=" * 80)
    print("  V - Switch to VERTICAL layout (Spanish right, English left)")
    print("  H - Switch to HORIZONTAL layout (Spanish row 2, English row 1)")
    print("  N - Next subtitle (jump to next subtitle start time)")
    print("  P - Previous subtitle (jump to previous subtitle start time)")
    print("  + - Advance 5 seconds")
    print("  - - Go back 5 seconds")
    print("  J - Jump to specific time (in seconds)")
    print("  R - Reset to beginning (time 0)")
    print("  X - Exit")
    print("=" * 80)
    print()
    
    # Initialize Qt application
    app = QApplication(sys.argv)
    
    # Create overlay and subtitle manager
    overlay = ProgressOverlay(position='bottom', opacity=0.85)
    subtitle_manager = SubtitleManager(gui_overlay=overlay)
    
    # Set up for Harmonious clip
    subtitle_manager.current_clip = "Nature's Harmonious Relationships"
    subtitle_manager.is_harmonious = True
    subtitle_manager.subtitles = subtitles_en
    subtitle_manager.subtitles2 = subtitles_es
    subtitle_manager.duration = duration
    
    # Show overlay
    overlay.show()
    
    # Initial state
    layout_mode = 'vertical'
    current_time = 10.0  # Start at 10 seconds to show some subtitles
    
    # Initial display
    update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time)
    print(f"\n\nStarting with VERTICAL layout at {current_time:.1f}s")
    print("Use controls to navigate and change layout...")
    
    try:
        while True:
            command = input("\n> ").strip()
            command_upper = command.upper()
            
            if command_upper == 'V':
                layout_mode = 'vertical'
                print(f"\n→ Switched to VERTICAL layout (columns)")
                update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time)
                
            elif command_upper == 'H':
                layout_mode = 'horizontal'
                print(f"\n→ Switched to HORIZONTAL layout (rows)")
                update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time)
                
            elif command_upper == 'N':
                current_time = find_next_subtitle_time(subtitles_en, subtitles_es, current_time)
                print(f"\n→ Next subtitle at {current_time:.1f}s")
                update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time)
                
            elif command_upper == 'P':
                current_time = find_previous_subtitle_time(subtitles_en, subtitles_es, current_time)
                print(f"\n→ Previous subtitle at {current_time:.1f}s")
                update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time)
                
            elif command == '+':
                current_time = min(current_time + 5.0, duration)
                print(f"\n→ Advanced to {current_time:.1f}s")
                update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time)
                
            elif command == '-':
                current_time = max(current_time - 5.0, 0.0)
                print(f"\n→ Went back to {current_time:.1f}s")
                update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time)
                
            elif command_upper == 'J':
                try:
                    time_input = input("Enter time in seconds: ").strip()
                    jump_time = float(time_input)
                    if 0 <= jump_time <= duration:
                        current_time = jump_time
                        print(f"\n→ Jumped to {current_time:.1f}s")
                        update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time)
                    else:
                        print(f"Time must be between 0 and {duration:.1f} seconds")
                except ValueError:
                    print("Invalid time format. Please enter a number.")
                    
            elif command_upper == 'R':
                current_time = 0.0
                print(f"\n→ Reset to beginning (0.0s)")
                update_display(overlay, subtitles_en, subtitles_es, duration, layout_mode, current_time)
                
            elif command_upper == 'X':
                print("\nExiting...")
                break
                
            else:
                print(f"Unknown command: '{command}'. Use V, H, N, P, +, -, J, R, or X.")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    
    finally:
        overlay.close()
        app.quit()


if __name__ == '__main__':
    main()
