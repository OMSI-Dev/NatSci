import socket
import signal
import sys
import subprocess
import os
import atexit
import threading
import time
import re
import io
import csv
import json
import unicodedata
from collections import deque, namedtuple
import pygame
from typing import Optional, List

# STATUS socket (diagnostics only; the Beelink is not involved in this display)
PI_PORT = 4096
BUFFER_SIZE = 8192
CONNECTION_TIMEOUT = 3.0  # Seconds to wait on a connected STATUS peer
MAX_MESSAGE_BYTES = 1_000_000  # Hard cap on a single inbound STATUS message

# SOS server (read-only queries)
SOS_IP = "10.0.0.16"  # NETWORK
SOS_PORT = 2468
SOS_CONNECT_TIMEOUT = 5.0  # Seconds to connect
SOS_FIRST_REPLY_TIMEOUT = 3.0  # Seconds to wait for the first byte of a reply
SOS_IDLE_TIMEOUT = 0.4  # Seconds of silence that end a reply (SOS has no delimiter)
MAX_REPLY_BYTES = 1_000_000

# Titles: SOS_datasets.csv fetched from the SOS server over SSH (key auth), cached locally
SOS_SSH_USER = "sos"
SSH_KEY_PATH = ""  # Optional private key; empty = ssh defaults / agent
SSH_CONNECT_TIMEOUT = 5
SSH_TIMEOUT = 15.0  # Whole-command limit for the CSV fetch
TITLES_REMOTE_PATH = "/AuxShare/data/SOS_datasets.csv"  # \\10.0.0.16\AuxShare\data on the SOS server
TITLES_CACHE_PATH = "/home/omsiadmin/Documents/SOS/SOS_datasets.csv"
TITLES_REFRESH_INTERVAL = 1800.0  # Refetch the CSV this often once fetched over SSH
TITLES_RETRY_INTERVAL = 300.0  # Retry interval while only a cache (or nothing) is available

# Adaptive polling (see PollScheduler)
BASE_POLL_INTERVAL = 20.0  # Poll cadence until a clip's duration is known
CATCH_POLL_INTERVAL = 2.0  # Cadence around a predicted clip change
SAFETY_POLL_INTERVAL = 60.0  # Longest gap between polls (bounds staleness after a manual skip)
EARLY_MARGIN = 1.5  # Start catch-polling this long before the predicted change
MAX_LEAD = 40.0  # Cap on how early catch-polling may start
MAX_CATCH_WINDOW = 15.0  # Keep catch-polling this long past the predicted change before giving up
HINT_ERROR = 5.0  # Assumed error of a duration taken from SOS metadata
DURATION_TOLERANCE = 2.0  # Slack when deciding two duration samples agree
IDENTITY_CHECK_INTERVAL = 180.0  # Playlist name + clip count check
FULL_REFRESH_INTERVAL = 1800.0  # Full playlist refetch
FAILURE_RETRY_DELAY = 5.0  # Retry after a failed SOS call
HEALTHY_POLL_AGE = 150.0  # STATUS in_sync is false when the last good poll is older than this
SUMMARY_LOG_INTERVAL = 60.0  # Seconds between summary log lines

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
# Sync: this Pi talks ONLY to the SOS server (read-only commands) and never to the Beelink.
#
#   SOS 10.0.0.16:2468 (plain TCP text, '\n'-terminated, replies end on silence)
#     enable, get_playlist_name, get_clip_count, get_clip_number, get_all_name_value_pairs <n>
#   Titles: SOS_datasets.csv fetched from the SOS server over SSH (UTF-8), cached locally.
#
# Port 4096 only answers STATUS (diagnostics). Check health on the Pi itself with:
#   python3 -c "import socket;s=socket.create_connection(('127.0.0.1',4096));s.sendall(b'STATUS');s.shutdown(1);print(s.recv(65536).decode())"
# NEVER add open_playlist / load / play / next_clip / prev_clip here: those change what the sphere shows.
# ---------------------------------------------------------------------------

def log(message: str) -> None:
    # flush=True: under systemd stdout is block-buffered, which hides live state in journalctl
    print(f"[Pi] {time.strftime('%H:%M:%S')} {message}", flush=True)


class SosError(Exception):
    """SOS unreachable, silent, or replied with something unusable."""


# -- reply parsing (pure functions) ------------------------------------------

def parse_int(text: str) -> Optional[int]:
    for line in text.splitlines():
        line = line.strip()
        if line.isascii() and line.isdigit():
            return int(line)
    match = re.search(r'\d+', text)
    return int(match.group()) if match else None


def parse_playlist_name(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and line != 'R':  # 'R' is the SOS acknowledgement token
            return line
    return ''


# Tcl-style "key value key {value with spaces}"; keys may contain '-', "{}" is an empty value.
_PAIR_RE = re.compile(r'(?<![\w-])([\w-]+)[ \t]+(?:\{([^}]*)\}|(\S+))')


def parse_pairs(text: str) -> dict:
    pairs = {}
    for match in _PAIR_RE.finditer(text):
        value = match.group(2) if match.group(2) is not None else match.group(3)
        pairs.setdefault(match.group(1), value.strip())
    return pairs


def parse_seconds(value) -> Optional[float]:
    """Duration text ('65', '2:30', '2m 30s') -> seconds; None when missing/zero/unrecognized."""
    if value is None:
        return None
    text = str(value).strip()
    seconds = None
    try:
        seconds = float(text)
    except ValueError:
        parts = text.split(':')
        if 2 <= len(parts) <= 3 and all(p.strip().isdigit() for p in parts):
            seconds = 0
            for part in parts:
                seconds = seconds * 60 + int(part)
        else:
            match = re.fullmatch(r'(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?', text, re.IGNORECASE)
            if match and any(match.groups()):
                hours, minutes, secs = (int(g) if g else 0 for g in match.groups())
                seconds = hours * 3600 + minutes * 60 + secs
    return float(seconds) if seconds and seconds > 0 else None


# -- SOS client -----------------------------------------------------------------

Clip = namedtuple('Clip', 'number name duration_text movie_title spanish_translation')
Playlist = namedtuple('Playlist', 'identity current clips')  # identity = (playlist_name, clip_count)


class SosSession:
    """One short-lived, enabled connection to SOS. Read-only commands only."""

    def __init__(self, host: str, port: int):
        self.host, self.port = host, port
        self.sock = None

    def __enter__(self):
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=SOS_CONNECT_TIMEOUT)
        except OSError as e:
            raise SosError(f"connect to {self.host}:{self.port} failed: {e}") from e
        try:
            self._send('enable')
            self._read_reply()  # handshake reply; content is not needed
        except Exception:
            self.close()
            raise
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _send(self, command: str) -> None:
        try:
            self.sock.sendall(command.encode('utf-8') + b'\n')
        except OSError as e:
            raise SosError(f"send {command!r} failed: {e}") from e

    def _read_reply(self) -> bytes:
        """SOS has no reply delimiter: read until the line goes quiet."""
        data = bytearray()
        started = time.monotonic()
        last = None
        self.sock.settimeout(0.1)
        while len(data) < MAX_REPLY_BYTES:
            try:
                chunk = self.sock.recv(4096)
            except socket.timeout:
                now = time.monotonic()
                if data and now - last >= SOS_IDLE_TIMEOUT:
                    break
                if not data and now - started >= SOS_FIRST_REPLY_TIMEOUT:
                    break
                continue
            except OSError as e:
                raise SosError(f"recv failed: {e}") from e
            if not chunk:
                break
            data.extend(chunk)
            last = time.monotonic()
        return bytes(data)

    def command(self, command: str) -> str:
        self._send(command)
        data = self._read_reply()
        if not data:
            raise SosError(f"no reply to {command!r}")
        return data.decode('utf-8', 'replace')  # whole buffer at once: never splits a multi-byte char

    def clip_number(self) -> Optional[int]:
        return parse_int(self.command('get_clip_number'))

    def identity(self):
        name = parse_playlist_name(self.command('get_playlist_name'))
        count = parse_int(self.command('get_clip_count'))
        if count is None:
            raise SosError("bad get_clip_count reply")
        return (name, count)


class SosClient:
    def __init__(self, host: str = SOS_IP, port: int = SOS_PORT):
        self.host, self.port = host, port

    def session(self) -> SosSession:
        return SosSession(self.host, self.port)

    def fetch_playlist(self) -> Playlist:
        with self.session() as s:
            identity = s.identity()
            current = s.clip_number()
            clips = []
            for number in range(1, identity[1] + 1):
                pairs = parse_pairs(s.command(f'get_all_name_value_pairs {number}'))
                clips.append(Clip(
                    number=number,
                    name=pairs.get('name') or f"Clip {number}",
                    duration_text=pairs.get('duration') or pairs.get('timer'),
                    movie_title=pairs.get('movie-title'),
                    spanish_translation=pairs.get('spanish-translation'),
                ))
        return Playlist(identity, current, clips)


# -- titles (SOS_datasets.csv) --------------------------------------------------

TITLE_COLUMN_KEY = 'Dataset Name (Auto)'


def decode_csv_bytes(data: bytes) -> str:
    """UTF-8 first (with or without BOM); cp1252 only for files that are not valid UTF-8."""
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return data.decode('cp1252', 'replace')


def parse_titles_csv(text: str) -> dict:
    titles = {}
    for row in csv.DictReader(io.StringIO(text)):
        key = (row.get(TITLE_COLUMN_KEY) or '').strip()
        if key:
            titles[key] = (unicodedata.normalize('NFC', (row.get('English Title') or '').strip()),
                           unicodedata.normalize('NFC', (row.get('Spanish Title') or '').strip()))
    return titles


def fetch_titles_bytes() -> bytes:
    cmd = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no',
           '-o', f'ConnectTimeout={SSH_CONNECT_TIMEOUT}']
    if SSH_KEY_PATH:
        cmd += ['-i', SSH_KEY_PATH]
    cmd += [f'{SOS_SSH_USER}@{SOS_IP}', f"cat '{TITLES_REMOTE_PATH}'"]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=SSH_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError) as e:
        raise SosError(f"ssh title fetch failed: {e!r}") from e
    if result.returncode != 0:
        raise SosError(f"ssh title fetch exit {result.returncode}: "
                       f"{result.stderr.decode('utf-8', 'replace').strip()[:200]}")
    return result.stdout


class TitleSource:
    """English/Spanish titles keyed by clip name; SSH fetch, local cache, never raises."""

    def __init__(self, fetch=fetch_titles_bytes, cache_path: str = TITLES_CACHE_PATH):
        self.fetch, self.cache_path = fetch, cache_path
        self.titles = {}
        self._lower = {}
        self.source = None  # 'ssh' | 'cache' | None
        self.loaded_at = None
        self.last_try = None
        self.last_error = None

    def _set(self, titles: dict, source: str) -> None:
        self.titles = titles
        self._lower = {k.lower(): v for k, v in titles.items()}
        self.source = source
        self.loaded_at = time.time()

    def load_cache(self) -> bool:
        try:
            with open(self.cache_path, 'rb') as f:
                titles = parse_titles_csv(decode_csv_bytes(f.read()))
        except OSError:
            return False
        if titles:
            self._set(titles, 'cache')
            log(f"Titles: {len(titles)} entries loaded from cache {self.cache_path}")
        return bool(titles)

    def refresh(self, now: float) -> bool:
        self.last_try = now
        try:
            data = self.fetch()
            titles = parse_titles_csv(decode_csv_bytes(data))
            if not titles:
                raise SosError("titles CSV had no usable rows")
        except Exception as e:
            self.last_error = f"{time.strftime('%H:%M:%S')} {e}"
            log(f"Titles: refresh failed ({e}); keeping {len(self.titles)} {self.source or 'no'} entries")
            return False
        self._set(titles, 'ssh')
        self.last_error = None
        log(f"Titles: {len(titles)} entries fetched from SOS")
        try:
            tmp = self.cache_path + '.tmp'
            with open(tmp, 'wb') as f:
                f.write(data)
            os.replace(tmp, self.cache_path)
        except OSError as e:
            log(f"Titles: could not write cache: {e}")
        return True

    def due(self, now: float) -> bool:
        if self.last_try is None:
            return True
        interval = TITLES_RETRY_INTERVAL if self.source != 'ssh' else TITLES_REFRESH_INTERVAL
        return now - self.last_try >= interval

    def lookup(self, name: str):
        return self.titles.get(name) or self._lower.get(name.lower())

    def info(self) -> dict:
        return {'source': self.source, 'entries': len(self.titles),
                'age_s': None if self.loaded_at is None else round(time.time() - self.loaded_at, 1),
                'last_error': self.last_error}


def build_entries(clips, titles: TitleSource):
    """Display lists indexed by clip number (index 0 unused). Titles: CSV, then SOS metadata, then name."""
    size = len(clips) + 1
    english, spanish, durations = [None] * size, [None] * size, [None] * size
    for clip in clips:
        found = titles.lookup(clip.name)
        csv_english, csv_spanish = found if found else ('', '')
        english[clip.number] = csv_english or clip.movie_title or clip.name
        spanish[clip.number] = csv_spanish or clip.spanish_translation or ''
        durations[clip.number] = format_duration(clip.duration_text)
    return english, spanish, durations


# -- adaptive polling ---------------------------------------------------------------

class PollScheduler:
    """
    Decides when to ask SOS for the current clip. Pure: every method takes `now`.

    Start with BASE_POLL_INTERVAL. Each observed clip change gives a start-time estimate
    (midpoint of the two polls around it, +/- half the gap); the time between two consecutive
    starts is that clip's duration (+/- the sum of both errors). Once a clip's duration is
    known, sleep until just before its predicted end and poll every CATCH_POLL_INTERVAL until
    the change lands. Lower-error samples replace higher-error ones, so predictions tighten.
    A clip that outlasts its prediction falls back to BASE polling; a safety poll
    (SAFETY_POLL_INTERVAL) bounds how stale the display can get after a manual skip.
    """

    def __init__(self):
        self.count = None
        self.reset()

    def reset(self) -> None:
        """New playlist: forget everything learned."""
        self.learned = {}      # clip -> (seconds, error)
        self.hints = {}        # clip -> seconds from SOS metadata (trusted less)
        self.pending_short = {}
        self.misses = 0
        self.reset_tracking()

    def reset_tracking(self) -> None:
        """Lose track of the running clip (e.g. after a long fetch) without forgetting durations."""
        self.clip = None
        self.start = None
        self.start_err = None
        self.last_poll = None
        self._miss_counted = False

    def set_hints(self, hints: dict) -> None:
        self.hints = dict(hints)

    def estimate(self, clip):
        if clip in self.learned:
            seconds, err = self.learned[clip]
            return seconds, err, 'learned'
        if clip in self.hints:
            return self.hints[clip], HINT_ERROR, 'hint'
        return None

    def _is_next(self, previous: int, current: int) -> bool:
        if current == previous + 1:
            return True
        return current == 1 and (self.count is None or previous == self.count)

    def observe(self, clip: int, now: float) -> str:
        """Record a successful poll. Returns 'joined', 'same' or 'changed'."""
        previous, last_poll = self.clip, self.last_poll
        self.last_poll = now
        if previous is None or last_poll is None:
            self.clip, self.start, self.start_err = clip, None, None
            self._miss_counted = False
            return 'joined'

        if clip == previous:
            est = self.estimate(clip)
            if (est and self.start is not None and not self._miss_counted
                    and now > self.start + est[0] + MAX_CATCH_WINDOW):
                self._miss_counted = True
                self.misses += 1
                if est[2] == 'hint':
                    self.hints.pop(clip, None)  # metadata duration was wrong for this clip
            return 'same'

        new_start = (last_poll + now) / 2.0
        new_err = (now - last_poll) / 2.0
        if self.start is not None and self._is_next(previous, clip):
            self._learn(previous, new_start - self.start, new_err + self.start_err)
        self.clip, self.start, self.start_err = clip, new_start, new_err
        self._miss_counted = False
        return 'changed'

    def _learn(self, clip: int, seconds: float, err: float) -> None:
        if seconds <= 0:
            return
        old = self.learned.get(clip)
        if old is None:
            self.learned[clip] = (seconds, err)
            return
        old_seconds, old_err = old
        if abs(seconds - old_seconds) <= old_err + err + DURATION_TOLERANCE:
            if err <= old_err:
                self.learned[clip] = (seconds, err)  # same duration, better precision
            self.pending_short.pop(clip, None)
        elif seconds > old_seconds:
            self.learned[clip] = (seconds, err)  # clip genuinely ran longer
            self.pending_short.pop(clip, None)
        else:
            pending = self.pending_short.get(clip)  # shorter once could be a manual skip
            if pending is not None and abs(pending - seconds) <= err + DURATION_TOLERANCE:
                self.learned[clip] = (seconds, err)
                self.pending_short.pop(clip, None)
            else:
                self.pending_short[clip] = seconds

    def next_delay(self, now: float):
        """Seconds until the next poll and the mode ('base' | 'predict' | 'catch' | 'lost')."""
        if self.clip is None or self.start is None:
            return BASE_POLL_INTERVAL, 'base'
        est = self.estimate(self.clip)
        if est is None:
            return BASE_POLL_INTERVAL, 'base'
        seconds, err, _ = est
        end = self.start + seconds
        lead = min(EARLY_MARGIN + self.start_err + err, MAX_LEAD)
        window_open = end - lead
        if now < window_open:
            return max(min(window_open - now, SAFETY_POLL_INTERVAL), CATCH_POLL_INTERVAL), 'predict'
        if now <= end + MAX_CATCH_WINDOW:
            return CATCH_POLL_INTERVAL, 'catch'
        return BASE_POLL_INTERVAL, 'lost'

    def describe(self, now: float) -> dict:
        delay, mode = self.next_delay(now)
        return {'mode': mode, 'next_poll_in_s': round(delay, 1), 'tracking_clip': self.clip,
                'start_known': self.start is not None, 'misses': self.misses,
                'learned_s': {str(c): [round(s, 1), round(e, 1)] for c, (s, e) in sorted(self.learned.items())},
                'hints': len(self.hints)}


# -- shared state -------------------------------------------------------------------

Snapshot = namedtuple('Snapshot', 'english spanish durations clip')


class SyncState:
    """Playlist/clip state shared by the SOS thread, STATUS thread and renderer."""

    def __init__(self):
        self.lock = threading.RLock()
        self.english = [None]
        self.spanish = [None]
        self.durations = [None]
        self.clip = None
        self.identity = None
        self.problems = deque(maxlen=20)
        self.stats = {k: 0 for k in ('full_refreshes', 'full_refresh_failures', 'polls_ok',
                                     'polls_failed', 'clip_changes', 'playlist_changes')}
        self.times = {k: None for k in ('playlist', 'poll_ok', 'poll_try', 'clip_change')}
        self.last_error = None
        self.poll_info = {}
        self.titles_info = {}
        self.started = time.time()

    def loaded(self) -> bool:
        with self.lock:
            return len(self.english) > 1

    def problem(self, message: str) -> None:
        self.problems.append(f"{time.strftime('%H:%M:%S')} {message}")
        log(f"PROBLEM: {message}")

    def snapshot(self) -> Snapshot:
        with self.lock:
            return Snapshot(self.english, self.spanish, self.durations, self.clip)

    def set_playlist(self, identity, english, spanish, durations) -> None:
        with self.lock:
            self.english, self.spanish, self.durations = english, spanish, durations
            self.identity = identity
            self.times['playlist'] = time.time()

    def set_clip(self, clip: Optional[int]) -> bool:
        """Returns True if the clip changed."""
        with self.lock:
            changed = clip != self.clip
            self.clip = clip
            if changed:
                self.times['clip_change'] = time.time()
                self.stats['clip_changes'] += 1
            return changed

    def title_for(self, clip: Optional[int]) -> str:
        with self.lock:
            if clip is not None and 0 < clip < len(self.english):
                return self.english[clip] or ''
            return ''

    def _age(self, key):
        stamp = self.times[key]
        return None if stamp is None else round(time.time() - stamp, 1)

    def status(self) -> dict:
        with self.lock:
            poll_age = self._age('poll_ok')
            return {
                'in_sync': poll_age is not None and poll_age <= HEALTHY_POLL_AGE,
                'items': len(self.english) - 1,
                'playlist': None if self.identity is None else {'name': self.identity[0], 'clips': self.identity[1]},
                'clip': self.clip,
                'clip_title': self.title_for(self.clip),
                'ages_s': {k: self._age(k) for k in self.times},
                'stats': dict(self.stats),
                'last_error': self.last_error,
                'polling': dict(self.poll_info),
                'titles': dict(self.titles_info),
                'sos': f"{SOS_IP}:{SOS_PORT}",
                'recent_problems': list(self.problems),
                'uptime_s': round(time.time() - self.started, 1),
            }


state = SyncState()


class SosSync:
    """Drives SosClient + PollScheduler + TitleSource. step() does one unit of work and returns the sleep."""

    def __init__(self, sync_state: SyncState, client, titles: TitleSource,
                 scheduler: PollScheduler, clock=time.monotonic):
        self.state, self.client, self.titles, self.scheduler, self.clock = \
            sync_state, client, titles, scheduler, clock
        self.clips = []
        self.last_full = None
        self.last_identity = None
        self.force_full = False
        self.failures = 0
        self.last_mode = None

    # -- helpers
    def _failed(self, what: str, error: Exception) -> None:
        self.failures += 1
        with self.state.lock:
            self.state.stats['polls_failed'] += 1
            self.state.last_error = f"{time.strftime('%H:%M:%S')} {what}: {error}"
        if self.failures == 1 or self.failures % 10 == 0:
            log(f"SOS {what} failed ({self.failures} in a row): {error}")

    def _succeeded(self) -> None:
        if self.failures:
            log(f"SOS reachable again after {self.failures} failure(s)")
        self.failures = 0
        with self.state.lock:
            self.state.stats['polls_ok'] += 1
            self.state.times['poll_ok'] = time.time()
            self.state.last_error = None

    def _publish_text(self) -> None:
        english, spanish, durations = build_entries(self.clips, self.titles)
        self.state.set_playlist(self.state.identity, english, spanish, durations)
        self.state.titles_info = self.titles.info()

    def _update_clip(self, clip: Optional[int]) -> None:
        previous = self.state.clip
        if self.state.set_clip(clip):
            title = self.state.title_for(clip)
            log(f"Clip {previous} -> {clip}" + (f": {title!r}" if title else " (not in playlist)"))

    def _refresh_polling_info(self) -> float:
        now = self.clock()
        delay, mode = self.scheduler.next_delay(now)
        self.state.poll_info = self.scheduler.describe(now)
        if mode != self.last_mode:
            log(f"Polling mode {self.last_mode} -> {mode} (next poll in {delay:.1f}s)")
            self.last_mode = mode
        return delay

    # -- work
    def full_refresh(self) -> bool:
        with self.state.lock:
            self.state.times['poll_try'] = time.time()
        try:
            playlist = self.client.fetch_playlist()
        except SosError as e:
            with self.state.lock:
                self.state.stats['full_refresh_failures'] += 1
            self._failed("playlist fetch", e)
            return False

        changed = playlist.identity != self.state.identity
        if changed:
            if self.state.identity is not None:
                self.state.stats['playlist_changes'] += 1
            self.scheduler.reset()
            log(f"Playlist: {playlist.identity[0]!r} with {playlist.identity[1]} clips")
        if changed or self.titles.due(self.clock()):
            self.titles.refresh(self.clock())

        now = self.clock()
        self.clips = playlist.clips
        self.state.identity = playlist.identity
        self._publish_text()
        hints = {}
        for clip in playlist.clips:
            seconds = parse_seconds(clip.duration_text)
            if seconds:
                hints[clip.number] = seconds
        self.scheduler.count = len(playlist.clips)
        self.scheduler.set_hints(hints)
        self.scheduler.reset_tracking()
        if playlist.current is not None:
            self.scheduler.observe(playlist.current, now)
        self._update_clip(playlist.current)

        self.last_full = self.last_identity = now
        self.force_full = False
        with self.state.lock:
            self.state.stats['full_refreshes'] += 1
        self._succeeded()
        return True

    def step(self) -> float:
        """One iteration; returns seconds to sleep before the next."""
        now = self.clock()
        needs_full = (not self.state.loaded() or self.force_full or
                      (self.last_full is not None and now - self.last_full >= FULL_REFRESH_INTERVAL))
        if needs_full:
            if self.full_refresh():
                return self._refresh_polling_info()
            return FAILURE_RETRY_DELAY

        if self.titles.due(now) and self.titles.source != 'ssh':
            if self.titles.refresh(now):
                self._publish_text()  # titles arrived after the playlist was loaded

        check_identity = now - self.last_identity >= IDENTITY_CHECK_INTERVAL
        with self.state.lock:
            self.state.times['poll_try'] = time.time()
        try:
            with self.client.session() as session:
                clip = session.clip_number()
                identity = session.identity() if check_identity else None
        except SosError as e:
            self._failed("poll", e)
            return FAILURE_RETRY_DELAY
        polled_at = self.clock()
        self._succeeded()

        if identity is not None:
            self.last_identity = polled_at
            if identity != self.state.identity:
                log(f"Playlist identity changed {self.state.identity} -> {identity}")
                self.force_full = True
                return 0.0

        if clip is not None:
            self.scheduler.observe(clip, polled_at)
        self._update_clip(clip)
        return self._refresh_polling_info()


def sos_loop(sync: SosSync) -> None:
    next_at = 0.0
    last_summary = time.monotonic()
    while running:
        now = time.monotonic()
        if now >= next_at:
            try:
                delay = sync.step()
            except Exception as e:  # keep the thread alive no matter what
                state.problem(f"sync step crashed: {e!r}")
                delay = FAILURE_RETRY_DELAY
            next_at = time.monotonic() + delay
        if now - last_summary >= SUMMARY_LOG_INTERVAL:
            last_summary = now
            s = state.status()
            log(f"Summary: in_sync={s['in_sync']} items={s['items']} clip={s['clip']} "
                f"mode={s['polling'].get('mode')} learned={len(s['polling'].get('learned_s', {}))} "
                f"titles={s['titles'].get('source')}/{s['titles'].get('entries')} "
                f"poll_age={s['ages_s']['poll_ok']}s")
        time.sleep(0.25)


# -- STATUS socket ------------------------------------------------------------------

def process_message(message: str, sender: Optional[str] = None) -> bytes:
    """Only STATUS is meaningful; anything else (e.g. a legacy engine push) is acknowledged and ignored."""
    if message.strip() == 'STATUS':
        return (json.dumps(state.status()) + "\n").encode('utf-8')
    return b"ACK IGNORED\n"


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
        pass
    return bytes(data)


def socket_server_loop(server_sock: socket.socket) -> None:
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
                try:
                    conn.sendall(process_message(data.decode('utf-8', 'ignore'), sender=addr[0]))
                except OSError:
                    pass
        except Exception as e:
            state.problem(f"error handling connection from {addr[0]}: {e!r}")
        finally:
            conn.close()


# -- process management --------------------------------------------------------------

def kill_old_instance() -> None:
    """Kill any existing process using the port and clean up old PID file."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            try:
                os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                log(f"Found old instance (PID {old_pid}), terminating...")
                os.kill(old_pid, signal.SIGTERM)
                time.sleep(0.5)
                try:
                    os.kill(old_pid, signal.SIGKILL)
                except OSError:
                    pass  # Already dead
                log("Old instance terminated")
            except OSError:
                log(f"PID {old_pid} not running, cleaning up stale PID file")
        except Exception as e:
            log(f"Warning: Could not read/kill old PID: {e}")
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    try:
        result = subprocess.run(['lsof', '-ti', f':{PI_PORT}'], capture_output=True, text=True, timeout=2)
        if result.stdout.strip():
            for pid in result.stdout.strip().split('\n'):
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
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        log(f"PID file created: {PID_FILE}")
    except Exception as e:
        log(f"Warning: Could not create PID file: {e}")


def bind_server_socket() -> socket.socket:
    """Bind the STATUS socket, retrying briefly while a killed predecessor releases the port."""
    last_error = None
    for _ in range(10):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # No SO_REUSEPORT: it would let a duplicate instance bind silently.
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
    """Start the SOS sync and STATUS threads and run the render loop."""
    global running

    kill_old_instance()
    write_pid_file()
    atexit.register(cleanup_pid_file)

    init_display()

    titles = TitleSource()
    titles.load_cache()  # show titles immediately even if SSH is slow or down
    sync = SosSync(state, SosClient(), titles, PollScheduler())

    server_sock = bind_server_socket()
    log(f"STATUS on port {PI_PORT}; syncing from SOS {SOS_IP}:{SOS_PORT}")
    log("Press Ctrl+C to exit")

    threading.Thread(target=socket_server_loop, args=(server_sock,), daemon=True).start()
    threading.Thread(target=sos_loop, args=(sync,), daemon=True).start()

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
