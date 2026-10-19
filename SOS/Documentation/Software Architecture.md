
1. sdc.py starts
   └─▶ Connect to SOS (socket)
       └─▶ Get current playlist name
           └─▶ Initialize CacheManager
               ├─▶ Load cached playlists
               ├─▶ Check if playlist is stale (SSH to get mtime)
               └─▶ Sync if needed (query all clips via socket)
   
2. Launch LibreOffice Impress
   └─▶ Load .odp presentation
       └─▶ Parse CSV for clip-to-slide mapping
           └─▶ Start presentation in slideshow mode

3. Initialize Audio System
   └─▶ Load audio category mappings (CSV)
       └─▶ SSH to SOS2 server
           └─▶ Launch MPV with IPC socket
               └─▶ Verify socket is responding

4. Start Engine
   └─▶ Launch HTTP server thread (port 5000)
   └─▶ Create PyQt5 overlays (hidden initially)
   └─▶ Enter main event loop
```

Key functions

### 1. Initialization/Access Separation

Each subsystem is split into two modules:
- `*_init.py` - Configuration loading and component initialization
- `*_access.py` - Runtime control and communication

```
audio_init.py:
  - Load audio-list.csv
  - Create AudioController instance
  - Return (audio_dict, controller)

audio_access.py:
  - SSH connection management
  - MPV IPC socket communication
  - Playback control methods
```

### 2. CacheManager Pattern

**Problem**: Frequent socket queries to SOS server are slow (100ms+ per query).

**Solution**: Single source of truth pattern
- On startup, fetch all metadata once
- Store in two JSON files:
  - `playlist_cache.JSON` - Ordered list of clips
  - `clip_metadata_cache.JSON` - Metadata for each clip
- Check server file mtime before syncing
- Runtime queries use in-memory cache (0ms)

**Benefits**:
- Fast clip lookups (dict access vs socket query)
- Offline operation possible
- Predictable behavior (no network variability)

### 3. Deferred Operations Pattern

**Problem**: Some operations are slow (audioselection, subtitle loading) and would block the UI.

**Solution**: Multi-phase transition
```python
# Phase 1: Instant (main thread)
1. Clear overlays (instant)
2. Navigate LibreOffice (blocks 7s - unavoidable)
3. Start internal timer
4. Show progress bar (instant)

# Phase 2: Deferred (background thread, +0.5s)
5. Record current clip number
6. Start ambient audio
7. Load subtitle files
```

**Benefits**:
- Progress bar appears immediately after navigation
- User sees progress start ticking right away
- Slow operations don't block UI updates

### 4. Overlay Manager Pattern

Encapsulates PyQt5 overlay lifecycle:
```python
class OverlayManager:
    modes = [
        "HIDDEN",                  # Credits screens
        "PROGRESS_ONLY",           # Regular datasets
        "SUBTITLES_AND_PROGRESS"   # Custom movies
    ]
    
    def show_progress_only():
        # Show progress bar instantly
        
    def show_subtitles_and_progress():
        # Show both with fade-in
        
    def instant_clear():
        # Clean transition between clips
```

### 5. Background Server Threads

Concurrent server threads handle external queries:

**HTTP Server** (Port 5000)
- Handles facilitation control requests
- RESTful JSON API
- CORS enabled for web interface

**SOS Monitor** (Main thread)
- Polls SOS server for clip changes
- 20 FPS event loop (50ms sleep)
- Coordinates all subsystems

## Threading Model

```
Main Thread:
├─▶ Engine event loop (50ms cycle)
│   ├─▶ Qt event processing
│   ├─▶ SOS queries
│   ├─▶ Overlay updates
│   └─▶ Sleep

Query Server Thread (daemon):
└─▶ Socket accept loop
    └─▶ Handle Pi state requests

HTTP Server Thread (daemon):
└─▶ Socket accept loop
    └─▶ Handle facilitation commands

Deferred Operations Thread (spawned on clip change):
└─▶ Execute slow operations:
    ├─▶ Record current clip number
    ├─▶ Audio management  
    └─▶ Subtitle loading
    (Thread exits when done)
```

## State Management

### Engine State Variables

```python
# Clip tracking
current_clip_number: int       # From SOS query
last_clip_name: str            # Detect changes
clip_start_time: float         # Internal timer

# Timer state
current_clip_duration: float   # 60s or custom
DATASET_DURATION: float        # Default 60s

# Audio state
current_audio_category: str    # Track category changes
audio_enabled: bool            # Feature flag

# Facilitation mode
facilitation_mode: bool        # Paused for facilitation

# Deferred operations
deferred_operations_done: bool
deferred_operations_countdown: int
pending_clip_number: int
pending_clip_name: str
pending_metadata: dict
```

### Cache State

```python
CacheManager:
    playlists: list[dict]           # All cached playlists
    current_playlist: dict          # Active playlist
    clip_metadata: dict[str, dict]  # All clip metadata
    dataset_titles: dict            # Spanish/English titles
    audio_config: dict              # Audio playback state
```

## Data Structures

### Playlist Cache Format

```json
{
  "name": "earth_systems.sos",
  "path": "/var/sosdemo/playlists/earth_systems.sos",
  "last_modified": "2026-03-15",
  "clips": [
    {"name": "air_global_circulation"},
    {"name": "water_ocean_currents"},
    {"name": "landcover_global"}
  ]
}
```

### Clip Metadata Format

```json
{
  "air_global_circulation": {
    "name": "air_global_circulation",
    "duration": 60,
    "majorcategory": "air",
    "translated-movie": false
  },
  "custom_movie_demo": {
    "name": "custom_movie_demo", 
    "duration": 180,
    "majorcategory": "site-custom",
    "translated-movie": true,
    "caption": "/path/to/subtitle_en.srt",
    "caption2": "/path/to/subtitle_es.srt",
    "movie-title": "Earth's Water Cycle",
    "spanish-translation": "El Ciclo del Agua"
  }
}
```

### Audio Configuration Format

```json
{
  "last_modified": "2026-03-15 14:30:00",
  "volume-level": 100,
  "air": {
    "filenames": {
      "air_1.mp3": 2,
      "air_2.mp3": 1
    },
    "last_played": "air_1.mp3"
  },
  "water": {
    "filenames": {
      "ocean_1.mp3": 0,
      "ocean_2.mp3": 0
    },
    "last_played": ""
  }
}
```

## Communication Protocols

### SOS Server Protocol (TCP Socket)

```
Client → Server:
  "enable\n"
Server → Client:
  "R\n"

Client → Server:
  "get_clip_number\n"
Server → Client:
  "5\n"

Client → Server:
  "get_all_name_value_pairs 5\n"
Server → Client:
  "name air_global_circulation duration 60 ..."
```

### MPV IPC Protocol (Unix Socket via SSH)

```bash
# Command format (JSON over socket)
echo '{"command":["loadfile","/path/audio.mp3"]}' | socat - UNIX-CONNECT:/tmp/mpv-audio-socket

# Response format
{"error":"success","data":null}
```

### Now Playing (Raspberry Pi, standalone)

The Pi display (`Components/RPi5 - Now Playing/Scripts/nowPlaying.py`) does not talk to the Beelink. It reads everything from the SOS server itself, using read-only commands only (`enable`, `get_playlist_name`, `get_clip_count`, `get_clip_number`, `get_all_name_value_pairs <n>`); it never sends `open_playlist`, `load`, `play`, `next_clip` or `prev_clip`.

```
Playlist:  fetched from SOS (clip names, metadata durations). Identity (name + clip count) re-checked
           every IDENTITY_CHECK_INTERVAL s; full refetch on change and every FULL_REFRESH_INTERVAL s.
Titles:    SOS_datasets.csv copied from the SOS server over SSH (sos@10.0.0.16, key auth), decoded as
           UTF-8 (BOM tolerated, cp1252 fallback), cached locally (TITLES_CACHE_PATH) and reused if
           SSH is down. Per clip: CSV title, then SOS movie-title / spanish-translation, then clip name.
Clip:      polled with get_clip_number (SOS has no change notification).
```

Adaptive polling (`PollScheduler`):
- Starts at `BASE_POLL_INTERVAL` (20 s). Each observed clip change is timed (start = midpoint of the two polls around the change), so the Pi learns per-clip durations; SOS metadata durations are used as hints until then.
- With a known duration it sleeps until shortly before the predicted end (`EARLY_MARGIN`, `MAX_LEAD`), then polls every `CATCH_POLL_INTERVAL` (2 s) until the change lands. A safety poll runs at most every `SAFETY_POLL_INTERVAL` (60 s).
- A miss (clip skipped, paused, or longer than predicted) falls back to the 20 s cadence and re-learns. Shorter-than-learned samples (manual skips) are held back until they repeat.

Diagnostics: `STATUS` on port 4096 (local to the Pi, e.g. `127.0.0.1`) returns one JSON line with `in_sync`, playlist/clip, polling mode and next poll, learned durations, title source/age, counters and recent errors; a summary line is logged every 60 s. Facilitation pause is not shown on the Pi.

### HTTP API Protocol

```
POST /
Content-Type: application/json

{
  "command": "DATASET_PLAY",
  "clip_number": 5
}

Response (200 OK):
{
  "status": "ok"
}
```

## Error Handling Strategy

### Connection Failures

**SOS Connection Lost**:
- Engine continues running with last known state
- Overlay shows stale progress
- Reconnection attempted on next loop

**SSH Connection Lost**:
- Audio controller attempts automatic reconnection
- MPV re-initialization on socket failure
- Graceful degradation (operates without audio)

**LibreOffice Crash**:
- No automatic recovery (requires restart)
- atexit handler attempts cleanup

### Resource Cleanup

```python
atexit.register(self._cleanup)

def _cleanup():
    1. Hide overlays
    2. Stop audio (quit MPV)
    3. Close socket connections
    4. Close LibreOffice
```

## Performance Characteristics

### Timing Measurements

| Operation | Duration | Notes |
|-----------|----------|-------|
| SOS clip query | 50-100ms | Network + parsing |
| Cache lookup | <1ms | In-memory dict access |
| LibreOffice navigation | 7-8s | COM + rendering |
| Audio start | 1-2s | SSH + MPV load |
| Subtitle file fetch | 0.5-2s | SCP transfer |
| Overlay render | 16ms | 60 FPS target |

### Optimization Techniques

1. **Cache metadata** - Avoid repeated socket queries
2. **Background threads** - Don't block UI for slow ops
3. **Instant progress bar** - Show immediately after navigation
4. **Deferred subtitle load** - Don't block transitions
5. **Internal timer** - No SOS time queries needed

## Security Considerations

### Current Implementation

- SSH key authentication (no passwords)
- Strict host key checking disabled (closed network)
- No HTTP authentication (localhost only)
- No input validation on SOS data (trusted source)

### Production Recommendations

- Enable HTTP authentication for external access
- Validate all inputs from HTTP API
- Log all facilitation commands
- Use TLS for HTTP server
- Implement rate limiting

## Scalability

### Current Limits

- **Playlists**: Tested up to 50 clips
- **Subtitles**: Supports files up to 2MB
- **Audio categories**: 8 categories configured
- **Concurrent connections**: 1 SOS, 1 Pi, unlimited HTTP

### Potential Bottlenecks

- LibreOffice COM responsiveness
- Network share latency
- SSH connection pooling
- PyQt5 event queue backlog

## Future Enhancements

### Potential Improvements

1. **Logging Framework** - Replace print() with proper logging
2. **Configuration UI** - Web-based settings editor
3. **Health Dashboard** - Real-time system status display
4. **Automatic Recovery** - Restart LibreOffice on crash
5. **Multi-Language** - Support additional subtitle languages
6. **Playlist Editor** - Web-based playlist management
7. **Analytics** - Clip view counts and duration tracking
8. **Remote Control** - Mobile app for facilitation

## Appendix: File Dependencies

### Critical Files

Must exist for system to start:
- `\\sos2\AuxShare\data\SOS_datasets.csv`
- `\\sos2\AuxShare\documents\noaa_presentation.odp`

### Optional Files

System operates without:
- `audio-list.csv` - Audio disabled
- `playlist_cache.JSON` - Fetches from SOS
- Subtitle files - Movies show without subtitles

### Generated Files

Created at runtime:
- `playlist_cache.JSON` - On first sync
- `clip_metadata_cache.JSON` - On first sync
- `audio-config.JSON` - On first audio usage
- `subtitles/*.srt` - Cached on demand
