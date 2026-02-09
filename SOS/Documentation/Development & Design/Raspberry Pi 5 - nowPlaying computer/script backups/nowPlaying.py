# backup from 2.9.26

import socket
import signal
import sys
import subprocess
import os
import atexit
import pygame
from typing import Optional, List

# Socket Configuration
PI_PORT = 4096
BUFFER_SIZE = 8192

# Display Configuration
DISPLAY_WIDTH = 1080
DISPLAY_HEIGHT = 1920
FPS = 30

# Color Definitions
WHITE = (255, 255, 255)
LIGHT_BLUE = (100, 200, 255)

MUSEO_FONT_PATH = '/home/omsiadmin/Documents/SOS/Museo_Slab_500.otf'
INTER_FONT_PATH = '/home/omsiadmin/Documents/SOS/Inter_24pt-Regular.ttf'
BACKGROUND_PATH = '/home/omsiadmin/Documents/SOS/bkg.jpg'
PID_FILE = '/tmp/nowPlaying.pid'

# Global Data
english_titles = [None]
spanish_titles = [None]
durations = [None]
current_clip_number = None
running = True

# Pygame Objects
screen = None
clock = None
museo_title_font = None
museo_subtitle_font = None
inter_title_font = None
inter_subtitle_font = None
duration_font = None
background = None


def cleanup_pid_file():
    """Remove PID file on exit."""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            print("[Pi] PID file cleaned up")
    except Exception as e:
        print(f"[Pi] Warning: Could not remove PID file: {e}")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    print("\n[Pi] Shutting down...")
    running = False
    cleanup_pid_file()
    pygame.quit()
    sys.exit(0)


def init_display():
    """Initialize pygame display and load fonts/images."""
    global screen, clock, museo_title_font, museo_subtitle_font
    global inter_title_font, inter_subtitle_font, duration_font, background
    
    pygame.init()
    screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    pygame.display.set_caption('Now Playing')
    clock = pygame.time.Clock()
    
    # Load fonts
    try:
        museo_title_font = pygame.font.Font(MUSEO_FONT_PATH, 120)
        museo_subtitle_font = pygame.font.Font(MUSEO_FONT_PATH, 100)
        inter_title_font = pygame.font.Font(INTER_FONT_PATH, 42)
        inter_subtitle_font = pygame.font.Font(INTER_FONT_PATH, 38)
        duration_font = pygame.font.Font(INTER_FONT_PATH, 42)
        print("[Pi] Fonts loaded successfully")
    except Exception as e:
        print(f"[Pi] Error loading fonts: {e}")
        print("[Pi] Using default fonts")
        museo_title_font = pygame.font.Font(None, 120)
        museo_subtitle_font = pygame.font.Font(None, 100)
        inter_title_font = pygame.font.Font(None, 42)
        inter_subtitle_font = pygame.font.Font(None, 38)
        duration_font = pygame.font.Font(None, 42)
    
    # Load background
    try:
        background = pygame.image.load(BACKGROUND_PATH)
        background = pygame.transform.scale(background, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        print("[Pi] Background image loaded successfully")
    except Exception as e:
        print(f"[Pi] Warning: Could not load background image: {e}")
        background = None


def draw_background():
    """Draw the background image or fallback color."""
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.fill((15, 25, 50))


def draw_header():
    """Draw the 'Now Playing' and 'Ahora en cartelera' header."""
    # "Now Playing" in white, Museo Slab
    now_playing_text = museo_title_font.render('Now Playing', True, WHITE)
    now_playing_rect = now_playing_text.get_rect(center=(DISPLAY_WIDTH // 2, 120))
    screen.blit(now_playing_text, now_playing_rect)
    
    # "Ahora en cartelera" in light blue, Museo Slab
    ahora_text = museo_subtitle_font.render('Ahora en cartelera', True, LIGHT_BLUE)
    ahora_rect = ahora_text.get_rect(center=(DISPLAY_WIDTH // 2, 250))
    screen.blit(ahora_text, ahora_rect)


def draw_current_item_border(x: int, y: int, width: int, height: int):
    """
    Draw border around current item.
    This method is modular for easy style changes.
    """
    border_thickness = 3
    pygame.draw.rect(
        screen,
        LIGHT_BLUE,
        (x, y, width, height),
        border_thickness,
        border_radius=5
    )


def draw_playlist_item(x: int, y: int, english: str, spanish: str, 
                       duration: str, is_current: bool) -> int:
    """
    Draw a single playlist item (English/Spanish pair with duration).
    Returns the height of the drawn item.
    """
    item_height = 0
    left_margin = 100
    right_margin = DISPLAY_WIDTH - 100
    duration_width = 80
    
    # Draw English title (white, Inter)
    english_surface = inter_title_font.render(english, True, WHITE)
    english_rect = english_surface.get_rect(topleft=(left_margin, y))
    screen.blit(english_surface, english_rect)
    item_height += english_rect.height + 5
    
    # Draw Spanish title (light blue, Inter)
    spanish_surface = inter_subtitle_font.render(spanish, True, LIGHT_BLUE)
    spanish_rect = spanish_surface.get_rect(topleft=(left_margin, y + item_height))
    screen.blit(spanish_surface, spanish_rect)
    item_height += spanish_rect.height + 10
    
    # Draw duration (aligned to right, Inter)
    duration_color = LIGHT_BLUE if is_current else WHITE
    duration_surface = duration_font.render(duration, True, duration_color)
    duration_rect = duration_surface.get_rect(
        midright=(right_margin, y + spanish_rect.height // 2 + english_rect.height // 2)
    )
    screen.blit(duration_surface, duration_rect)
    
    # Draw border if current item (modular styling)
    if is_current:
        draw_current_item_border(
            left_margin - 20,
            y - 15,
            right_margin - left_margin + 40,
            item_height + 20
        )
    
    return item_height + 25  # Add spacing between items


def filter_credits(titles: List[Optional[str]]) -> List[int]:
    """
    Filter out items containing 'Credits:' in their title.
    Returns list of valid indices.
    """
    valid_indices = []
    for i in range(1, len(titles)):
        if titles[i] and 'Credits:' not in titles[i]:
            valid_indices.append(i)
    return valid_indices


def render_display():
    """Render the complete display."""
    draw_background()
    draw_header()
    
    # Get valid (non-credits) indices
    valid_indices = filter_credits(english_titles)
    
    # Limit to 12 rows maximum
    display_indices = valid_indices[:12]
    
    # Starting Y position for playlist items
    current_y = 350
    
    for idx in display_indices:
        english = english_titles[idx] if idx < len(english_titles) else "Unknown"
        spanish = spanish_titles[idx] if idx < len(spanish_titles) else "Desconocido"
        duration = durations[idx] if idx < len(durations) else "0m"
        is_current = (idx == current_clip_number)
        
        # Draw the item and update Y position
        item_height = draw_playlist_item(
            0, current_y, english, spanish, duration, is_current
        )
        current_y += item_height
        
        # Stop if we run out of screen space
        if current_y > DISPLAY_HEIGHT - 100:
            break
    
    pygame.display.flip()


def _parse_init_message(message: str) -> None:
    """Parse INIT message into numbered lists (index starts at 1)."""
    global english_titles, spanish_titles, durations

    lines = message.splitlines()
    if not lines:
        return

    data_lines = [line.strip() for line in lines[1:] if line.strip()]
    new_english = [None]
    new_spanish = [None]
    new_durations = [None]

    for line in data_lines:
        parts = line.split("|", 3)
        if len(parts) != 4:
            print(f"[Pi] Skipping malformed line: {line}")
            continue
        index_str, english, spanish, duration = [p.strip() for p in parts]
        if not index_str.isdigit():
            print(f"[Pi] Skipping non-numeric index: {line}")
            continue
        index = int(index_str)
        while len(new_english) <= index:
            new_english.append(None)
            new_spanish.append(None)
            new_durations.append(None)
        new_english[index] = english
        new_spanish[index] = spanish
        new_durations[index] = duration

    english_titles = new_english
    spanish_titles = new_spanish
    durations = new_durations

    print("[Pi] INIT received.")
    print(f"[Pi] Loaded {len(english_titles) - 1} items")


def _handle_clip_message(message: str) -> None:
    """Handle CLIP message and map to stored playlist data."""
    global current_clip_number

    clip_str = message.split(":", 1)[1].strip() if ":" in message else ""
    if not clip_str.isdigit():
        print(f"[Pi] Invalid CLIP message: {message}")
        return

    current_clip_number = int(clip_str)
    english = english_titles[current_clip_number] if current_clip_number < len(english_titles) else None
    spanish = spanish_titles[current_clip_number] if current_clip_number < len(spanish_titles) else None
    duration = durations[current_clip_number] if current_clip_number < len(durations) else None

    print(f"[Pi] Current clip number: {current_clip_number}")
    print(f"[Pi] Clip English: {english}")
    print(f"[Pi] Clip Spanish: {spanish}")
    print(f"[Pi] Clip Duration: {duration}")


def kill_old_instance() -> None:
    """Kill any existing process using the port and clean up old PID file."""
    # Check if PID file exists
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                print(f"[Pi] Found old instance (PID {old_pid}), terminating...")
                os.kill(old_pid, signal.SIGTERM)
                import time
                time.sleep(0.5)
                # Force kill if still alive
                try:
                    os.kill(old_pid, signal.SIGKILL)
                except OSError:
                    pass  # Already dead
                print("[Pi] Old instance terminated")
            except OSError:
                print(f"[Pi] PID {old_pid} not running, cleaning up stale PID file")
        except Exception as e:
            print(f"[Pi] Warning: Could not read/kill old PID: {e}")
        
        # Remove old PID file
        try:
            os.remove(PID_FILE)
        except:
            pass
    
    # Try using lsof to find process using the port
    try:
        result = subprocess.run(
            ['lsof', '-ti', f':{PI_PORT}'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    print(f"[Pi] Killing process {pid} using port {PI_PORT}")
                    os.kill(int(pid), signal.SIGKILL)
                except Exception as e:
                    print(f"[Pi] Could not kill PID {pid}: {e}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # lsof not available or timed out
    except Exception as e:
        print(f"[Pi] Warning checking port: {e}")


def write_pid_file() -> None:
    """Write current process PID to file."""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"[Pi] PID file created: {PID_FILE}")
    except Exception as e:
        print(f"[Pi] Warning: Could not create PID file: {e}")


def pi_socket_server() -> None:
    """Socket server that receives INIT and CLIP data from Beelink."""
    global running
    
    # Kill any old instances before starting
    kill_old_instance()
    
    # Write PID file and register cleanup
    write_pid_file()
    atexit.register(cleanup_pid_file)
    
    # Initialize display
    init_display()
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # On Linux, also set SO_REUSEPORT if available
    try:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, OSError):
        pass  # SO_REUSEPORT not available on this system
    
    server_sock.settimeout(0.1)  # Short timeout to allow display updates
    
    try:
        server_sock.bind(('0.0.0.0', PI_PORT))
    except OSError as e:
        print(f"[Pi] ERROR: Cannot bind to port {PI_PORT}")
        print(f"[Pi] {e}")
        print(f"[Pi] Another instance may be running. To fix:")
        print(f"[Pi]   1. Run: lsof -ti:{PI_PORT} | xargs kill -9")
        print(f"[Pi]   2. Or: pkill -f nowPlaying.py")
        server_sock.close()
        sys.exit(1)
    
    server_sock.listen(5)

    bound_addr = server_sock.getsockname()
    print(f"[Pi] Socket server bound to {bound_addr}")
    print(f"[Pi] Listening on port {PI_PORT}...")
    print("[Pi] Press Ctrl+C to exit")

    while running:
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
        
        # Render display
        render_display()
        clock.tick(FPS)
        
        # Check for socket connections
        try:
            conn, addr = server_sock.accept()
        except socket.timeout:
            continue  # No connection, continue display loop
        except KeyboardInterrupt:
            break
            
        conn.settimeout(5.0)  # Prevent infinite blocking
        print(f"[Pi] Connection from {addr}")

        data = bytearray()
        try:
            while True:
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    break
                data.extend(chunk)
        except socket.timeout:
            print("[Pi] Recv timeout - processing partial data")

        if data:
            message = data.decode('utf-8', 'ignore').strip()
            print(f"[Pi] Received: {message[:100]}...") if len(message) > 100 else print(f"[Pi] Received: {message}")

            if message.startswith("INIT"):
                _parse_init_message(message)
            elif message.startswith("CLIP:"):
                _handle_clip_message(message)
            else:
                print(f"[Pi] Unknown message: {message[:50]}")

            try:
                conn.sendall(b"ACK\n")
            except:
                pass
        else:
            print("[Pi] No data received")

        conn.close()

    # Cleanup
    server_sock.close()
    pygame.quit()
    cleanup_pid_file()
    print("[Pi] Server stopped")


def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)
    pi_socket_server()


if __name__ == "__main__":
    main()