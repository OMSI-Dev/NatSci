"""
System Constants for SOS Control System

This file contains all magic numbers, timeouts, and fixed values used throughout
the system. Centralizing these values makes the code more maintainable and
easier to understand.
"""

# =============================================================================
# NETWORK TIMEOUTS (seconds)
# =============================================================================

# SOS Server
SOS_CONNECTION_TIMEOUT = 4.0
SOS_SOCKET_TIMEOUT = 8.0
SOS_QUERY_TIMEOUT = 8.0  # Alias for SOS_SOCKET_TIMEOUT
SOS_RECV_IDLE_TIMEOUT = 1.0
SOS_SOCKET_POLL_TIMEOUT = 0.2  # Non-blocking socket polling

# Raspberry Pi / Now Playing
PI_CONNECTION_TIMEOUT = 3.0
PI_QUERY_TIMEOUT = 10.0

# SSH Operations
SSH_CONNECTION_TIMEOUT = 5.0
SSH_COMMAND_TIMEOUT = 10.0
SSH_FILE_TRANSFER_TIMEOUT = 5.0

# HTTP Server and Client
HTTP_CONNECTION_TIMEOUT = 2.0
SERVER_ACCEPT_TIMEOUT = 1.0  # Server socket accept timeout
CLIENT_CONNECTION_TIMEOUT = 2.0  # Client connection timeout

# Socket Buffer
SOCKET_BUFFER_SIZE = 4096  # bytes


# =============================================================================
# NETWORK PORTS
# =============================================================================

# SOS server port
SOS_PORT = 2468
SOS_PORT_DEFAULT = 2468  # Default value

# Raspberry Pi now playing display port
PI_PORT = 4096
PI_PORT_DEFAULT = 4096  # Default value

# Engine query server port (for Pi to query engine state)
ENGINE_QUERY_PORT = 4097

# HTTP facilitation interface port
HTTP_SERVER_PORT = 5000


# =============================================================================
# ENGINE TIMING
# =============================================================================

# Main engine loop sleep duration (20 FPS)
ENGINE_LOOP_SLEEP = 0.05  # seconds

# Qt overlay refresh rate (60 FPS)
OVERLAY_REFRESH_RATE = 16  # milliseconds

# MPV socket polling interval
MPV_POLL_INTERVAL = 0.2  # seconds

# Delay before executing deferred operations (allows progress bar animation)
DEFERRED_OPERATIONS_COUNTDOWN = 10  # iterations (~0.5s at 20 FPS)


# =============================================================================
# DATASET DURATIONS
# =============================================================================

# Default duration for regular datasets (NOAA SOS clips)
DEFAULT_DATASET_DURATION = 60.0  # seconds


# Wait time for subtitle fade before proceeding
SUBTITLE_FADE_WAIT = 2.2  # seconds

# Pause between audio tracks
AUDIO_TRACK_PAUSE = 0.5  # seconds

# Small delay for custom moviesets to ease transition from credits
PRESENTATION_TRANSITION_DELAY = 0.3  # seconds
# Default fade duration for audio transitions
DEFAULT_AUDIO_FADE_DURATION = 2.0  # seconds


# =============================================================================
# MPV / AUDIO SETTINGS
# =============================================================================

# Default audio volume (0-100)
DEFAULT_AUDIO_VOLUME = 100

# MPV socket path on remote server
MPV_SOCKET_PATH = "/tmp/mpv-audio-socket"

# MPV initialization wait time
MPV_INIT_WAIT_TIME = 3.0  # seconds

# Audio fade steps for smooth transitions
AUDIO_FADE_STEPS = 10


# =============================================================================
# OVERLAY DISPLAY SETTINGS
# =============================================================================

# Progress bar dimensions
PROGRESS_BAR_HEIGHT = 12  # pixels
PROGRESS_BAR_MARGIN_LEFT = 210  # pixels
PROGRESS_BAR_MARGIN_RIGHT = 210  # pixels
PROGRESS_BAR_MARGIN_BOTTOM = 25  # pixels
PROGRESS_BAR_Y_OFFSET = 87  # pixels from bottom

# Progress bar styling
PROGRESS_BAR_BORDER_RADIUS = 6  # pixels
PROGRESS_BAR_COLOR = '#ffffff'

# Timestamp font
TIMESTAMP_FONT_SIZE = 16  # points
TIMESTAMP_SPACING = 15  # pixels

# Subtitle font
SUBTITLE_FONT_SIZE = 28  # points
SUBTITLE_BG_OPACITY = 150  # 0-255
SUBTITLE_Y_OFFSET = 80  # pixels above progress bar

# Subtitle transition tolerance
SUBTITLE_GAP_TOLERANCE = 0.25  # seconds

# Fade animation durations
OVERLAY_FADE_IN_DURATION = 250  # milliseconds
OVERLAY_FADE_OUT_DURATION = 300  # milliseconds


# =============================================================================
# CACHE AND FILE SETTINGS
# =============================================================================

# Subtitle gap tolerance for seamless transitions
SUBTITLE_TRANSITION_GAP = 0.25  # seconds

# Maximum characters per subtitle line
SUBTITLE_MAX_CHARS_SINGLE = 350  # when showing only one subtitle
SUBTITLE_MAX_CHARS_DUAL = 170  # when showing two subtitles

# Subtitle cache directory name
SUBTITLE_CACHE_DIR = "subtitles"


# =============================================================================
# LIBERAR OFFICE / PRESENTATION SETTINGS
# =============================================================================

# Wait time for LibreOffice to start
LIBREOFFICE_START_WAIT = 3.0  # seconds

# Wait time after starting presentation
PRESENTATION_START_WAIT = 2.0  # seconds

# Wait time after playlist reload
PLAYLIST_RELOAD_WAIT = 2.0  # seconds


# =============================================================================
# HTTP API RESPONSE CODES
# =============================================================================

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_ERROR = 500


# =============================================================================
# DEBUG FLAGS (for development)
# =============================================================================

# Show debug borders on overlays
DEBUG_SHOW_OVERLAY_BORDERS = False

# Enable verbose SSH output
DEBUG_SSH_VERBOSE = False

# Enable MPV debug output
DEBUG_MPV_VERBOSE = False
