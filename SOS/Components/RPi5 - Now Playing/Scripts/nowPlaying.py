import socket
import signal
import sys
import subprocess
import os
import atexit
import threading
import time
import re
import json
import hashlib
from collections import deque, namedtuple
import pygame
from typing import Optional, List

# Socket Configuration
PI_PORT = 4096
BUFFER_SIZE = 8192
ENGINE_IP = "10.0.0.17"  # Beelink/Engine IP NETWORK d
ENGINE_QUERY_PORT = 4097  # Port to query engine for state
ENGINE_CONNECT_TIMEOUT = 10.0  # Seconds to wait for connection to engine
ENGINE_RECV_TIMEOUT = 5.0  # Seconds to wait for each chunk of state data
ENGINE_RETRY_INTERVAL = 5.0  # Minimum seconds between state requests (pulls)

# Sync / self-healing
HEARTBEAT_STALE_AFTER = 20.0  # No engine STATE heartbeat this long -> fall back to periodic pulls
PERIODIC_RESYNC_INTERVAL = 30.0  # Safety-net pull interval while heartbeats are absent
MISMATCH_PULL_THRESHOLD = 2  # Consecutive mismatching heartbeats before pulling (ignores transients)
CONNECTION_TIMEOUT = 3.0  # Seconds to wait on a connected peer
MAX_MESSAGE_BYTES = 1_000_000  # Hard cap on a single inbound message
SUMMARY_LOG_INTERVAL = 60.0  # Seconds between sync summary log lines

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
PAUSED_IMAGE_PATH = '/home/omsiadmin/Documents/SOS/nowPlaying_paused.jpg'
PID_FILE = '/tmp/nowPlaying.pid'

# Global Data
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
paused_image = None


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
    global inter_title_font, inter_subtitle_font, duration_font, background, paused_image
    
    pygame.init()
    screen = None
    for attempt in range(30):  # retry for up to ~30s
        try:
            screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN)
            break
        except pygame.error as e:
            print(f"[Pi] Display not ready ({e}), retrying...")
            time.sleep(1)
    if screen is None:
        raise RuntimeError("Display never became available")
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
    
    # Load paused image for facilitation mode
    try:
        paused_image = pygame.image.load(PAUSED_IMAGE_PATH)
        paused_image = pygame.transform.scale(paused_image, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        print("[Pi] Paused image loaded successfully")
    except Exception as e:
        print(f"[Pi] Warning: Could not load paused image: {e}")
        paused_image = None


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


DEFAULT_DURATION_DISPLAY = "3m 0s"  # Fallback when duration is missing, N/A, or 0


def format_duration(duration_str) -> str:
    """
    Convert duration to UI-friendly format.
    Examples: "65" -> "1m 5s", "45" -> "45s", "2:30" -> "2m 30s", "0m 0s" -> default
    Missing/N/A/zero durations (in any format) fall back to DEFAULT_DURATION_DISPLAY;
    unrecognized non-empty values are shown as-is.
    """
    if duration_str is None:
        return DEFAULT_DURATION_DISPLAY

    text = str(duration_str).strip()
    if not text or text.lower() in ('n/a', 'na', 'none', 'null'):
        return DEFAULT_DURATION_DISPLAY

    total_seconds = None
    try:
        total_seconds = int(round(float(text)))  # Plain seconds, e.g. "65" or "120.5"
    except (ValueError, TypeError):
        parts = text.split(':')
        if 2 <= len(parts) <= 3 and all(p.strip().isdigit() for p in parts):
            # Colon-separated, e.g. "2:30" or "1:02:30"
            total_seconds = 0
            for part in parts:
                total_seconds = total_seconds * 60 + int(part)
        else:
            # Unit-formatted, e.g. "0m 0s", "2m 30s", "45s", "1h 2m" (as sent by engine)
            match = re.fullmatch(
                r'(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?',
                text, re.IGNORECASE
            )
            if match and any(match.groups()):
                hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds

    if total_seconds is None:
        # Unrecognized format but has content - display as-is
        return text

    if total_seconds <= 0:
        return DEFAULT_DURATION_DISPLAY

    if total_seconds < 60:
        return f"{total_seconds}s"

    minutes = total_seconds // 60
    seconds = total_seconds % 60

    if seconds == 0:
        return f"{minutes}m"
    else:
        return f"{minutes}m {seconds}s"


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
    # Hide mouse
    pygame.mouse.set_visible(False)

    snap = state.snapshot()
    english_titles, spanish_titles, durations = snap.english, snap.spanish, snap.durations

    # Check if in facilitation pause mode
    if snap.paused:
        if paused_image:
            screen.blit(paused_image, (0, 0))
        else:
            screen.fill((0, 0, 0))  # Black screen if image fails to load
        pygame.display.flip()
        return
    
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
        duration = durations[idx] if idx < len(durations) and durations[idx] else DEFAULT_DURATION_DISPLAY
        is_current = (idx == snap.clip)
        
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




# ---------------------------------------------------------------------------
# Sync state and protocol
#
# Wire protocol (newline-delimited, one or more messages per connection):
#   INIT [<digest> <count>]       header, then "<n>|<english>|<spanish>|<duration>" lines
#   CLIP:<n>                      current clip
#   PAUSE / UNPAUSE               facilitation mode
#   STATE <digest> <clip|-> <0|1> engine heartbeat (playlist digest, clip, paused)
#   STATUS                        diagnostic query; replies with one JSON line
# The engine pushes INIT/CLIP/PAUSE/UNPAUSE/STATE; this Pi pulls with REQUEST_STATE.
# Check health from any machine with:
#   python3 -c "import socket;s=socket.create_connection(('<pi-ip>',4096));s.sendall(b'STATUS');s.shutdown(1);print(s.recv(65536).decode())"
# ---------------------------------------------------------------------------

def log(message: str) -> None:
    # flush=True: under systemd stdout is block-buffered, which hides live state in journalctl
    print(f"[Pi] {time.strftime('%H:%M:%S')} {message}", flush=True)


def _is_uint(text: str) -> bool:
    return text.isascii() and text.isdigit()


def _digest(entry_lines) -> str:
    """Digest of the INIT body; must match nowplaying_protocol.entries_digest on the Beelink."""
    return hashlib.sha1("\n".join(entry_lines).encode('utf-8')).hexdigest()[:8]


INVALID_CLIP = -1

Snapshot = namedtuple('Snapshot', 'english spanish durations clip paused')


def parse_payload(text: str) -> dict:
    """
    Parse any inbound message (push or pull response) into its parts. Pure function.
    Keys: init (dict|None), clip (int|None, INVALID_CLIP if unparsable), pause (bool|None),
    state ((digest, clip, paused)|None), status (bool), unknown (list of lines).
    """
    result = {'init': None, 'clip': None, 'pause': None, 'state': None,
              'status': False, 'unknown': []}
    header = None
    entries, entry_lines, malformed = [], [], []

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == 'INIT' or line.startswith('INIT '):
            header = line.split()
        elif line.startswith('CLIP:'):
            value = line[5:].strip()
            result['clip'] = int(value) if _is_uint(value) else INVALID_CLIP
        elif line == 'PAUSE':
            result['pause'] = True
        elif line == 'UNPAUSE':
            result['pause'] = False
        elif line == 'STATUS':
            result['status'] = True
        elif line.startswith('STATE '):
            parts = line.split()
            if len(parts) == 4 and (parts[2] == '-' or _is_uint(parts[2])) and parts[3] in ('0', '1'):
                result['state'] = (parts[1], None if parts[2] == '-' else int(parts[2]), parts[3] == '1')
            else:
                result['unknown'].append(line)
        elif header is not None:
            parts = line.split('|', 3)
            if len(parts) == 4 and _is_uint(parts[0].strip()) and int(parts[0]) > 0 and '|' not in parts[3]:
                entries.append(tuple(p.strip() for p in parts))
                entry_lines.append(line)
            else:
                malformed.append(line)
        else:
            result['unknown'].append(line)

    if header is not None:
        result['init'] = {
            'header_digest': header[1] if len(header) > 1 else None,
            'header_count': int(header[2]) if len(header) > 2 and _is_uint(header[2]) else None,
            'entries': entries,
            'malformed': malformed,
            'digest': _digest(entry_lines),
        }
    return result


class SyncState:
    """
    All playlist/sync state, shared by the socket thread, resync thread and renderer.
    Lists are replaced wholesale (never mutated) so a Snapshot is always consistent.
    """

    def __init__(self):
        self.lock = threading.RLock()
        self.english = [None]
        self.spanish = [None]
        self.durations = [None]
        self.digest = None  # digest of the INIT body currently held (computed locally)
        self.clip = None
        self.paused = False

        self.push_seq = {'init': 0, 'clip': 0, 'pause': 0}  # bumped by every engine push
        self.resync_requested = threading.Event()
        self.mismatch_streak = 0
        self.last_state_result = None  # result of the latest engine heartbeat comparison
        self.last_sender = None
        self.problems = deque(maxlen=20)
        self.stats = {k: 0 for k in (
            'init_applied', 'init_rejected', 'clip_applied', 'pause_applied', 'heartbeats',
            'heartbeat_mismatches', 'pulls_ok', 'pulls_failed', 'pull_parts_skipped_stale',
            'unknown_messages')}
        self.times = {k: None for k in ('init', 'clip', 'pause', 'heartbeat', 'pull_ok', 'pull_try')}
        self.started = time.time()

    # -- helpers (call with lock held unless noted)
    def loaded(self) -> bool:
        with self.lock:
            return len(self.english) > 1

    def problem(self, message: str) -> None:
        self.problems.append(f"{time.strftime('%H:%M:%S')} {message}")
        log(f"PROBLEM: {message}")

    def snapshot(self) -> Snapshot:
        with self.lock:
            return Snapshot(self.english, self.spanish, self.durations, self.clip, self.paused)

    def baseline(self) -> dict:
        with self.lock:
            return dict(self.push_seq)

    def _age(self, key):
        stamp = self.times[key]
        return None if stamp is None else round(time.time() - stamp, 1)

    # -- appliers
    def _apply_init(self, init: dict, source: str) -> None:
        entries = init['entries']
        if not entries:
            self.stats['init_rejected'] += 1
            self.problem(f"INIT from {source} rejected: no valid entries (kept {len(self.english) - 1} existing)")
            return

        size = max(int(e[0]) for e in entries)
        english, spanish, durations = [None] * (size + 1), [None] * (size + 1), [None] * (size + 1)
        for index_str, en, es, dur in entries:
            index = int(index_str)
            english[index], spanish[index], durations[index] = en, es, format_duration(dur)

        self.english, self.spanish, self.durations = english, spanish, durations
        self.digest = init['digest']
        self.times['init'] = time.time()
        self.stats['init_applied'] += 1
        log(f"INIT applied from {source}: {len(entries)} items, digest {self.digest}")

        damaged = False
        if init['malformed']:
            damaged = True
            self.problem(f"INIT had {len(init['malformed'])} malformed line(s), first: {init['malformed'][0][:80]!r}")
        if init['header_count'] is not None and init['header_count'] != len(entries):
            damaged = True
            self.problem(f"INIT announced {init['header_count']} items but {len(entries)} parsed")
        if init['header_digest'] is not None and init['header_digest'] != init['digest']:
            self.problem(f"INIT digest mismatch (engine {init['header_digest']}, local {init['digest']}): "
                         "corrupted in transit or engine/Pi digest code differ")
        if damaged and source == 'push':
            self.resync_requested.set()  # ask the engine for a clean copy

    def _apply_clip(self, value: int, source: str) -> None:
        if value == INVALID_CLIP:
            self.problem(f"Invalid CLIP message from {source}")
            return
        self.clip = value
        self.times['clip'] = time.time()
        self.stats['clip_applied'] += 1
        known = value < len(self.english) and self.english[value] is not None
        log(f"CLIP {value} applied from {source}"
            + (f": {self.english[value]!r}" if known else " (not in current playlist)"))
        if not known and source == 'push':
            self.problem(f"CLIP {value} is not in the {len(self.english) - 1}-item playlist: menu is stale or empty")
            self.resync_requested.set()

    def _apply_pause(self, value: bool, source: str) -> None:
        if value != self.paused:
            log(f"Facilitation mode {'enabled' if value else 'disabled'} ({source})")
        self.paused = value
        self.times['pause'] = time.time()
        self.stats['pause_applied'] += 1

    def _handle_state(self, digest: str, clip: Optional[int], paused: bool) -> str:
        """Compare the engine heartbeat against local state. Returns the reply line."""
        self.stats['heartbeats'] += 1
        self.times['heartbeat'] = time.time()
        diffs = []
        if digest != self.digest:
            diffs.append(f"playlist(engine {digest}, pi {self.digest})")
        if clip != self.clip:
            diffs.append(f"clip(engine {clip}, pi {self.clip})")
        if paused != self.paused:
            diffs.append(f"paused(engine {paused}, pi {self.paused})")

        if not diffs:
            if self.last_state_result != 'OK':
                log("Heartbeat: in sync with engine")
            self.mismatch_streak = 0
            self.last_state_result = 'OK'
            return f"ACK OK digest={self.digest} clip={self.clip} paused={int(self.paused)}"

        self.stats['heartbeat_mismatches'] += 1
        self.mismatch_streak += 1
        self.last_state_result = 'MISMATCH ' + ', '.join(diffs)
        log(f"Heartbeat MISMATCH #{self.mismatch_streak}: {', '.join(diffs)}")
        if self.mismatch_streak >= MISMATCH_PULL_THRESHOLD:
            self.resync_requested.set()
        return f"ACK MISMATCH {', '.join(diffs)}"

    # -- entry point
    def apply_payload(self, text: str, source: str, baseline: Optional[dict] = None,
                      sender: Optional[str] = None):
        """
        Apply a parsed message. source is 'push' (from the engine) or 'pull' (our request).
        A pull applies a part only if no push touched that part since `baseline` was taken,
        so a slow pull response can never overwrite newer pushed data.
        Returns (parsed, reply_or_None).
        """
        parsed = parse_payload(text)
        reply = None
        with self.lock:
            def fresh(kind: str) -> bool:
                if source == 'push':
                    self.push_seq[kind] += 1
                    return True
                if baseline is not None and self.push_seq[kind] != baseline[kind]:
                    self.stats['pull_parts_skipped_stale'] += 1
                    log(f"Pull response {kind.upper()} skipped: newer push already applied")
                    return False
                return True

            if source == 'push' and sender and any(
                    parsed[k] is not None for k in ('init', 'clip', 'pause', 'state')):
                if sender != self.last_sender and sender != ENGINE_IP:
                    self.problem(f"engine messages arrive from {sender} but ENGINE_IP is {ENGINE_IP}: "
                                 "state requests are going to the wrong host")
                self.last_sender = sender

            if parsed['init'] is not None and fresh('init'):
                self._apply_init(parsed['init'], source)
            if parsed['pause'] is not None and fresh('pause'):
                self._apply_pause(parsed['pause'], source)
            if parsed['clip'] is not None and fresh('clip'):
                self._apply_clip(parsed['clip'], source)
            if parsed['state'] is not None and source == 'push':
                reply = self._handle_state(*parsed['state'])
            if source == 'push':
                for line in parsed['unknown']:
                    self.stats['unknown_messages'] += 1
                    self.problem(f"unrecognized message: {line[:60]!r}")
        return parsed, reply

    def status(self) -> dict:
        with self.lock:
            hb_age = self._age('heartbeat')
            if hb_age is None or hb_age > HEARTBEAT_STALE_AFTER:
                in_sync = None  # unknown: no recent heartbeat from the engine
            else:
                in_sync = self.last_state_result == 'OK'
            return {
                'in_sync': in_sync,
                'last_heartbeat_result': self.last_state_result,
                'items': len(self.english) - 1,
                'digest': self.digest,
                'clip': self.clip,
                'paused': self.paused,
                'ages_s': {k: self._age(k) for k in self.times},
                'stats': dict(self.stats),
                'engine_ip': ENGINE_IP,
                'last_sender': self.last_sender,
                'recent_problems': list(self.problems),
                'uptime_s': round(time.time() - self.started, 1),
            }


state = SyncState()


def process_message(message: str, sender: Optional[str] = None) -> bytes:
    """Handle one inbound push message from the engine; returns the reply to send back."""
    message = message.strip()
    if message == 'STATUS':
        return (json.dumps(state.status()) + "\n").encode('utf-8')
    preview = message[:100].replace("\n", " / ")
    if not message.startswith('STATE '):  # heartbeats are logged only when they change result
        log(f"Received from {sender}: {preview}{'...' if len(message) > 100 else ''}")
    _, reply = state.apply_payload(message, 'push', sender=sender)
    return ((reply or "ACK") + "\n").encode('utf-8')


def read_message(conn: socket.socket) -> bytes:
    """Read until the peer half-closes, the size cap is hit, or the timeout expires."""
    data = bytearray()
    try:
        while len(data) < MAX_MESSAGE_BYTES:
            chunk = conn.recv(BUFFER_SIZE)
            if not chunk:
                break
            data.extend(chunk)
    except socket.timeout:
        log("Recv timeout - processing partial data")
    return bytes(data)


def request_state_from_engine() -> bool:
    """
    Pull the full state (playlist, pause, clip) from the engine query server.
    Parts that a newer engine push already updated while we were waiting are not overwritten.
    Returns True if a playlist was received.
    """
    baseline = state.baseline()
    with state.lock:
        state.times['pull_try'] = time.time()
    log(f"Requesting state from engine {ENGINE_IP}:{ENGINE_QUERY_PORT}...")
    try:
        data = bytearray()
        with socket.create_connection((ENGINE_IP, ENGINE_QUERY_PORT),
                                      timeout=ENGINE_CONNECT_TIMEOUT) as sock:
            sock.sendall(b"REQUEST_STATE\n")
            sock.settimeout(ENGINE_RECV_TIMEOUT)
            try:
                while len(data) < MAX_MESSAGE_BYTES:
                    chunk = sock.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    data.extend(chunk)
            except socket.timeout:
                pass  # engine didn't close; use what arrived
        if not data:
            raise RuntimeError("engine returned no data")

        parsed, _ = state.apply_payload(data.decode('utf-8', 'ignore'), 'pull', baseline=baseline)
        if parsed['init'] is None or not parsed['init']['entries']:
            raise RuntimeError("engine response contained no playlist")
        with state.lock:
            state.stats['pulls_ok'] += 1
            state.times['pull_ok'] = time.time()
            state.mismatch_streak = 0
        log(f"Pull complete ({len(data)} bytes)")
        return True
    except Exception as e:
        with state.lock:
            state.stats['pulls_failed'] += 1
        log(f"Pull from engine failed: {e!r}")
        return False


def resync_loop() -> None:
    """
    Background thread that decides when to pull from the engine:
      - no playlist loaded yet (retry every ENGINE_RETRY_INTERVAL)
      - a push was damaged / refers to unknown clips / heartbeats keep mismatching
      - heartbeats absent (old engine, engine down): periodic safety pull
    """
    last_try = 0.0
    last_summary = time.monotonic()
    while running:
        time.sleep(0.5)
        now = time.monotonic()
        wall = time.time()

        with state.lock:
            loaded = state.loaded()
            hb_age = state._age('heartbeat')
            last_sync = max([t for t in (state.times['pull_ok'], state.times['init'],
                                         state.times['pull_try']) if t] or [0.0])
        heartbeat_live = hb_age is not None and hb_age <= HEARTBEAT_STALE_AFTER

        reason, min_gap = None, ENGINE_RETRY_INTERVAL
        if not loaded:
            reason = "no playlist loaded"
        elif state.resync_requested.is_set():
            reason = "mismatch or damaged message"
        elif not heartbeat_live and wall - last_sync >= PERIODIC_RESYNC_INTERVAL:
            reason, min_gap = "periodic check (no engine heartbeats)", PERIODIC_RESYNC_INTERVAL

        if reason and now - last_try >= min_gap:
            state.resync_requested.clear()
            last_try = now
            log(f"Resync: {reason}")
            request_state_from_engine()

        if now - last_summary >= SUMMARY_LOG_INTERVAL:
            last_summary = now
            s = state.status()
            log(f"Summary: in_sync={s['in_sync']} items={s['items']} clip={s['clip']} "
                f"paused={s['paused']} digest={s['digest']} heartbeat_age={s['ages_s']['heartbeat']}s "
                f"problems={len(s['recent_problems'])}")


def socket_server_loop(server_sock: socket.socket) -> None:
    """
    Accept engine connections one at a time (preserves message order) on a thread
    separate from rendering, so a slow or stalled peer can never freeze the display.
    """
    server_sock.settimeout(0.5)
    while running:
        try:
            conn, addr = server_sock.accept()
        except socket.timeout:
            continue
        except OSError:
            if running:
                log("Server socket error; stopping accept loop")
            break
        try:
            conn.settimeout(CONNECTION_TIMEOUT)
            data = read_message(conn)
            if data:
                reply = process_message(data.decode('utf-8', 'ignore'), sender=addr[0])
                try:
                    conn.sendall(reply)
                except OSError:
                    pass
            else:
                log(f"Connection from {addr[0]} sent no data")
        except Exception as e:
            state.problem(f"error handling connection from {addr[0]}: {e!r}")
        finally:
            conn.close()


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
                log(f"Found old instance (PID {old_pid}), terminating...")
                os.kill(old_pid, signal.SIGTERM)
                time.sleep(0.5)
                # Force kill if still alive
                try:
                    os.kill(old_pid, signal.SIGKILL)
                except OSError:
                    pass  # Already dead
                log("Old instance terminated")
            except OSError:
                log(f"PID {old_pid} not running, cleaning up stale PID file")
        except Exception as e:
            log(f"Warning: Could not read/kill old PID: {e}")
        
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
                    log(f"Killing process {pid} using port {PI_PORT}")
                    os.kill(int(pid), signal.SIGKILL)
                except Exception as e:
                    log(f"Could not kill PID {pid}: {e}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # lsof not available or timed out
    except Exception as e:
        log(f"Warning checking port: {e}")


def write_pid_file() -> None:
    """Write current process PID to file."""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        log(f"PID file created: {PID_FILE}")
    except Exception as e:
        log(f"Warning: Could not create PID file: {e}")




def bind_server_socket() -> socket.socket:
    """Bind the listening socket, retrying briefly while a killed predecessor releases the port."""
    last_error = None
    for _ in range(10):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # No SO_REUSEPORT: it would let a duplicate instance bind silently and split traffic.
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_sock.bind(('0.0.0.0', PI_PORT))
            server_sock.listen(5)
            return server_sock
        except OSError as e:
            last_error = e
            server_sock.close()
            time.sleep(1)
    log(f"ERROR: Cannot bind to port {PI_PORT}: {last_error}")
    log(f"Another instance may be running. Try: lsof -ti:{PI_PORT} | xargs kill -9")
    sys.exit(1)


def pi_socket_server() -> None:
    """Start the sync threads and run the render loop."""
    global running

    kill_old_instance()
    write_pid_file()
    atexit.register(cleanup_pid_file)

    init_display()

    server_sock = bind_server_socket()
    log(f"Listening on port {PI_PORT} (engine {ENGINE_IP}:{ENGINE_QUERY_PORT})")
    log("Press Ctrl+C to exit")

    threading.Thread(target=socket_server_loop, args=(server_sock,), daemon=True).start()
    threading.Thread(target=resync_loop, daemon=True).start()

    pygame.mouse.set_visible(False)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False

        render_display()
        clock.tick(FPS)

    server_sock.close()
    pygame.quit()
    cleanup_pid_file()
    log("Server stopped")


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        pi_socket_server()
    except Exception as e:
        log(f"FATAL: {e}")
        cleanup_pid_file()
        raise


if __name__ == "__main__":
    main()
