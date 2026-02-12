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
ENGINE_IP = "10.10.51.98"  # Beelink/Engine IP
ENGINE_QUERY_PORT = 4097  # Port to query engine for state

# Display Configuration
# Physical screen: 1920×1080 rotated 90° to portrait orientation
# Software renders to landscape and rotates content 90° counter-clockwise
DISPLAY_WIDTH = 1920
DISPLAY_HEIGHT = 1080
FPS = 30

# Design dimensions (portrait layout before rotation)
DESIGN_WIDTH = 1080
DESIGN_HEIGHT = 1920

# Display Controls
DATASET_FONT_SCALE = 0.7  # Multiplier for all dataset fonts (english, spanish, duration)
ROW_PADDING_LEFT = 100  # Left padding for dataset rows
ROW_PADDING_RIGHT = 100  # Right padding for dataset rows
MAX_TEXT_WIDTH = 600  # Maximum width before text wraps, originally 700

# Margin and Padding Configuration
HEADER_TOP_MARGIN = 120  # Top margin for "Now Playing" title
HEADER_BOTTOM_PADDING = 0  # Bottom padding below Spanish title (Ahora en cartelera)
PLAYLIST_START_Y = 350  # Starting Y position for playlist items (affected by header padding)
SIDE_MARGIN_OFFSET = 0  # Additional side margin offset for all elements (applied on top of ROW_PADDING)

# Canvas Background Configuration (unified background behind all text)
CANVAS_BG_ENABLED = True  # Enable/disable unified canvas background
CANVAS_BG_COLOR = (0, 0, 0)  # Background color (black)
CANVAS_BG_ALPHA = 60  # Background opacity (0-255, where 255 is fully opaque)
CANVAS_BG_X = 50  # X position in design coordinates (portrait)
CANVAS_BG_Y = 80  # Y position in design coordinates (portrait)
CANVAS_BG_WIDTH = 980  # Width in design coordinates
CANVAS_BG_HEIGHT = 1760  # Height in design coordinates
CANVAS_BG_FEATHER = 120  # Feathering/blur radius for edges (0 = no feather)

# White Vignette Configuration
WHITE_VIGNETTE_ENABLED = True  # Enable/disable white vignette effect
WHITE_VIGNETTE_STRENGTH =20  # Maximum opacity at edges (0-255)
WHITE_VIGNETTE_RADIUS = 0.7  # Radius where vignette starts (0.0-1.0, where 1.0 is screen edge)
WHITE_VIGNETTE_SOFTNESS = 1  # Softness/feathering of vignette (0.0-1.0) 

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
    screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption('Now Playing')
    clock = pygame.time.Clock()
    
    # Load fonts (with scaling for dataset fonts)
    try:
        museo_title_font = pygame.font.Font(MUSEO_FONT_PATH, 120)
        museo_subtitle_font = pygame.font.Font(MUSEO_FONT_PATH, 100)
        inter_title_font = pygame.font.Font(INTER_FONT_PATH, int(42 * DATASET_FONT_SCALE))
        inter_subtitle_font = pygame.font.Font(INTER_FONT_PATH, int(38 * DATASET_FONT_SCALE))
        duration_font = pygame.font.Font(INTER_FONT_PATH, int(42 * DATASET_FONT_SCALE))
        print("[Pi] Fonts loaded successfully")
    except Exception as e:
        print(f"[Pi] Error loading fonts: {e}")
        print("[Pi] Using default fonts")
        museo_title_font = pygame.font.Font(None, 120)
        museo_subtitle_font = pygame.font.Font(None, 100)
        inter_title_font = pygame.font.Font(None, int(42 * DATASET_FONT_SCALE))
        inter_subtitle_font = pygame.font.Font(None, int(38 * DATASET_FONT_SCALE))
        duration_font = pygame.font.Font(None, int(42 * DATASET_FONT_SCALE))
    
    # Load and rotate background for 90° screen orientation
    try:
        background = pygame.image.load(BACKGROUND_PATH)
        # Scale to actual display size (landscape), then background will fit properly
        background = pygame.transform.scale(background, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        print("[Pi] Background image loaded and scaled successfully")
    except Exception as e:
        print(f"[Pi] Warning: Could not load background image: {e}")
        background = None


def rotate_and_position(surface: pygame.Surface, design_x: int, design_y: int, 
                        center: bool = False) -> tuple:
    """
    Rotate surface 90° counter-clockwise and translate coordinates.
    Design coordinates are for portrait layout (1080×1920).
    Returns (rotated_surface, (pos_x, pos_y)).
    """
    rotated = pygame.transform.rotate(surface, 90)
    
    if center:
        # For centered text, transform center point
        # Portrait center (x, y) → Landscape center (y, DISPLAY_HEIGHT - x)
        pos_x = design_y
        pos_y = DISPLAY_HEIGHT - design_x
        rect = rotated.get_rect(center=(pos_x, pos_y))
        return rotated, rect.topleft
    else:
        # For topleft positioning
        # Portrait (x, y) → Landscape (y, DISPLAY_HEIGHT - x - rotated_height)
        pos_x = design_y
        pos_y = DISPLAY_HEIGHT - design_x - rotated.get_height()
        return rotated, (pos_x, pos_y)


def draw_canvas_background():
    """
    Draw a unified semi-transparent background with feathering behind all text elements.
    This goes in front of bkg.jpg but behind all text.
    """
    if not CANVAS_BG_ENABLED or CANVAS_BG_ALPHA == 0:
        return
    
    # Create a surface for the background with extra space for feathering
    total_width = CANVAS_BG_WIDTH + CANVAS_BG_FEATHER * 2
    total_height = CANVAS_BG_HEIGHT + CANVAS_BG_FEATHER * 2
    bg_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
    bg_surface.fill((0, 0, 0, 0))  # Transparent
    
    if CANVAS_BG_FEATHER > 0:
        # Draw feathered background from outside to inside
        feather_steps = min(CANVAS_BG_FEATHER, 50)  # More steps for smoother gradient
        for i in range(feather_steps, 0, -1):
            # Progress from edge (0) to center (1)
            progress = 1 - (i / feather_steps)
            step_alpha = int(CANVAS_BG_ALPHA * progress)
            step_color = (*CANVAS_BG_COLOR, step_alpha)
            
            # Calculate inset for this step (from outer edge inward)
            inset = CANVAS_BG_FEATHER - i
            rect_x = inset
            rect_y = inset
            rect_w = total_width - 2 * inset
            rect_h = total_height - 2 * inset
            
            if rect_w > 0 and rect_h > 0:
                pygame.draw.rect(
                    bg_surface,
                    step_color,
                    (rect_x, rect_y, rect_w, rect_h),
                    border_radius=12
                )
        
        # Draw solid center
        if CANVAS_BG_WIDTH > 0 and CANVAS_BG_HEIGHT > 0:
            pygame.draw.rect(
                bg_surface,
                (*CANVAS_BG_COLOR, CANVAS_BG_ALPHA),
                (CANVAS_BG_FEATHER, CANVAS_BG_FEATHER, CANVAS_BG_WIDTH, CANVAS_BG_HEIGHT),
                border_radius=12
            )
    else:
        # Simple solid background
        pygame.draw.rect(bg_surface, (*CANVAS_BG_COLOR, CANVAS_BG_ALPHA), 
                        (0, 0, CANVAS_BG_WIDTH, CANVAS_BG_HEIGHT),
                        border_radius=12)
    
    # Rotate and position the background (account for feather offset)
    rotated_bg, pos_bg = rotate_and_position(bg_surface, CANVAS_BG_X - CANVAS_BG_FEATHER, 
                                            CANVAS_BG_Y - CANVAS_BG_FEATHER)
    screen.blit(rotated_bg, pos_bg)


def draw_white_vignette():
    """
    Draw a white vignette effect over the entire screen.
    Creates a subtle white glow that fades from the edges.
    """
    if not WHITE_VIGNETTE_ENABLED or WHITE_VIGNETTE_STRENGTH == 0:
        return
    
    # Create vignette surface
    vignette_surface = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
    vignette_surface.fill((0, 0, 0, 0))  # Transparent
    
    # Calculate center and max radius
    center_x = DISPLAY_WIDTH // 2
    center_y = DISPLAY_HEIGHT // 2
    max_radius = max(DISPLAY_WIDTH, DISPLAY_HEIGHT) * 0.7
    
    # Calculate vignette parameters
    inner_radius = max_radius * WHITE_VIGNETTE_RADIUS
    outer_radius = max_radius * (WHITE_VIGNETTE_RADIUS + WHITE_VIGNETTE_SOFTNESS)
    
    # Draw vignette as radial gradient
    steps = 60
    for i in range(steps):
        progress = i / steps
        
        # Calculate current radius
        current_radius = inner_radius + (outer_radius - inner_radius) * progress
        
        # Calculate alpha (fade from 0 at inner to max at outer)
        alpha = int(WHITE_VIGNETTE_STRENGTH * progress)
        
        # Draw circle
        if alpha > 0:
            pygame.draw.circle(
                vignette_surface,
                (255, 255, 255, alpha),
                (center_x, center_y),
                int(current_radius),
                max(1, int(outer_radius / steps) + 1)
            )
    
    screen.blit(vignette_surface, (0, 0))


def draw_background():
    """Draw the background image or fallback color."""
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.fill((15, 25, 50))


def draw_header():
    """Draw the 'Now Playing' and 'Ahora en cartelera' header."""
    # Calculate positions with configurable margins
    now_playing_y = HEADER_TOP_MARGIN
    ahora_y = now_playing_y + 130  # ~130px below "Now Playing"
    
    # "Now Playing" in white, Museo Slab (centered in design coordinates)
    now_playing_text = museo_title_font.render('Now Playing', True, WHITE)
    
    # "Ahora en cartelera" in light blue, Museo Slab
    ahora_text = museo_subtitle_font.render('Ahora en cartelera', True, LIGHT_BLUE)
    
    # Draw text (no individual backgrounds)
    rotated_np, pos_np = rotate_and_position(now_playing_text, DESIGN_WIDTH // 2, now_playing_y, center=True)
    screen.blit(rotated_np, pos_np)
    
    rotated_ahora, pos_ahora = rotate_and_position(ahora_text, DESIGN_WIDTH // 2, ahora_y, center=True)
    screen.blit(rotated_ahora, pos_ahora)


def draw_current_item_border(design_x: int, design_y: int, design_width: int, design_height: int):
    """
    Draw border around current item with coordinate transformation.
    This method is modular for easy style changes.
    """
    border_thickness = 3
    
    # Transform rectangle coordinates for 90° rotation
    # In rotated space: design_y becomes x, (DISPLAY_HEIGHT - design_x - design_width) becomes y
    # Width and height swap
    rect_x = design_y
    rect_y = DISPLAY_HEIGHT - design_x - design_width
    rect_width = design_height
    rect_height = design_width
    
    pygame.draw.rect(
        screen,
        LIGHT_BLUE,
        (rect_x, rect_y, rect_width, rect_height),
        border_thickness,
        border_radius=5
    )


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """
    Wrap text to fit within max_width.
    Returns list of text lines.
    """
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        test_surface = font.render(test_line, True, WHITE)
        
        if test_surface.get_width() <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Single word too long, add it anyway
                lines.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else [text]


def draw_playlist_item(x: int, y: int, english: str, spanish: str, 
                       duration: str, is_current: bool) -> int:
    """
    Draw a single playlist item (English/Spanish pair with duration).
    Uses design coordinates (portrait layout), renders with rotation.
    Supports text wrapping with duration always at top-right.
    Returns the height of the drawn item in design space.
    """
    left_margin = ROW_PADDING_LEFT + SIDE_MARGIN_OFFSET
    right_margin = DESIGN_WIDTH - ROW_PADDING_RIGHT - SIDE_MARGIN_OFFSET
    content_width = right_margin - left_margin
    
    # Reserve space for duration (approximate)
    duration_surface = duration_font.render(duration, True, WHITE)
    duration_width = duration_surface.get_width() + 30  # Add some padding
    text_max_width = min(MAX_TEXT_WIDTH, content_width - duration_width)
    
    # Wrap English title
    english_lines = wrap_text(english, inter_title_font, text_max_width)
    
    # Wrap Spanish title
    spanish_lines = wrap_text(spanish, inter_subtitle_font, text_max_width)
    
    current_y = y
    english_height = 0
    
    # Calculate total height first for background
    temp_y = y
    for i, line in enumerate(english_lines):
        line_surface = inter_title_font.render(line, True, WHITE)
        line_height = line_surface.get_height()
        english_height += line_height + (3 if i < len(english_lines) - 1 else 5)
    
    spanish_height = 0
    for i, line in enumerate(spanish_lines):
        line_surface = inter_subtitle_font.render(line, True, LIGHT_BLUE)
        line_height = line_surface.get_height()
        spanish_height += line_height + (3 if i < len(spanish_lines) - 1 else 10)
    
    total_item_height = english_height + spanish_height
    
    # Draw English lines (white, Inter) - no individual background
    for i, line in enumerate(english_lines):
        line_surface = inter_title_font.render(line, True, WHITE)
        rotated_line, pos_line = rotate_and_position(line_surface, left_margin, current_y)
        screen.blit(rotated_line, pos_line)
        line_height = line_surface.get_height()
        current_y += line_height + (3 if i < len(english_lines) - 1 else 5)
    
    # Draw Spanish lines (light blue, Inter)
    for i, line in enumerate(spanish_lines):
        line_surface = inter_subtitle_font.render(line, True, LIGHT_BLUE)
        rotated_line, pos_line = rotate_and_position(line_surface, left_margin, current_y)
        screen.blit(rotated_line, pos_line)
        line_height = line_surface.get_height()
        current_y += line_height + (3 if i < len(spanish_lines) - 1 else 10)
    
    # Draw duration at top-right, aligned with first line of English
    duration_color = LIGHT_BLUE if is_current else WHITE
    duration_surface = duration_font.render(duration, True, duration_color)
    duration_x = right_margin - duration_surface.get_width()
    duration_y = y  # Align with first line
    rotated_dur, pos_dur = rotate_and_position(duration_surface, duration_x, duration_y)
    screen.blit(rotated_dur, pos_dur)
    
    # Draw border if current item (adaptive height)
    if is_current:
        draw_current_item_border(
            left_margin - 20,
            y - 15,
            right_margin - left_margin + 40,
            total_item_height + 20
        )
    
    return total_item_height + 25  # Add spacing between items


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
    draw_canvas_background()  # Unified background behind all text
    draw_header()
    
    # Get valid (non-credits) indices
    valid_indices = filter_credits(english_titles)
    
    # Limit to 12 rows maximum
    display_indices = valid_indices[:12]
    
    # Starting Y position for playlist items (uses configurable value)
    current_y = PLAYLIST_START_Y + HEADER_BOTTOM_PADDING
    
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
        
        # Stop if we run out of design space (portrait layout)
        if current_y > DESIGN_HEIGHT - 100:
            break
    
    draw_white_vignette()  # Apply white vignette over everything
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


def request_state_from_engine() -> None:
    """Request current state from engine when starting late."""
    print("[Pi] Requesting current state from engine...")
    try:
        with socket.create_connection((ENGINE_IP, ENGINE_QUERY_PORT), timeout=3.0) as sock:
            # Send request
            sock.sendall(b"REQUEST_STATE\n")
            print("[Pi] Sent REQUEST_STATE to engine")
            
            # Receive response (may be large)
            data = bytearray()
            sock.settimeout(2.0)
            while True:
                try:
                    chunk = sock.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    data.extend(chunk)
                    print(f"[Pi] Received chunk: {len(chunk)} bytes")
                except socket.timeout:
                    break  # No more data
            
            if data:
                message = data.decode('utf-8', 'ignore').strip()
                print(f"[Pi] Received state from engine ({len(message)} bytes)")
                print(f"[Pi] Raw message preview: {message[:200]}..." if len(message) > 200 else f"[Pi] Raw message: {message}")
                
                # Parse messages - INIT comes first, CLIP (if present) comes after blank line
                if "CLIP:" in message:
                    # Split INIT and CLIP messages
                    parts = message.split("\n\n")
                    if len(parts) >= 2:
                        # INIT is in first part, CLIP in second
                        init_part = parts[0]
                        clip_part = parts[1]
                        print(f"[Pi] Found INIT and CLIP (split by blank line)")
                        if init_part.startswith("INIT"):
                            _parse_init_message(init_part)
                        if clip_part.startswith("CLIP:"):
                            _handle_clip_message(clip_part)
                    else:
                        # Fallback: manually split by CLIP:
                        clip_idx = message.find("CLIP:")
                        if clip_idx > 0:
                            init_part = message[:clip_idx].strip()
                            clip_part = message[clip_idx:].strip()
                            print(f"[Pi] Found INIT and CLIP (manual split)")
                            if init_part.startswith("INIT"):
                                _parse_init_message(init_part)
                            _handle_clip_message(clip_part)
                else:
                    # Only INIT message
                    print(f"[Pi] Found INIT only")
                    if message.startswith("INIT"):
                        _parse_init_message(message)
                    
                print("[Pi] State successfully loaded from engine")
            else:
                print("[Pi] No state data received from engine")
                
    except socket.timeout:
        print("[Pi] Timeout requesting state from engine")
    except ConnectionRefusedError:
        print(f"[Pi] Engine not responding on {ENGINE_IP}:{ENGINE_QUERY_PORT}")
        print("[Pi] Will wait for engine to send data...")
    except Exception as e:
        print(f"[Pi] Error requesting state: {e}")
        print("[Pi] Will wait for engine to send data...")


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
    
    # Request current state from engine (if running)
    request_state_from_engine()
    
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
