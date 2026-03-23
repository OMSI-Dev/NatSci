
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

4. Initialize Now Playing (if enabled)
   └─▶ Build INIT message with all clips
       └─▶ Send to Pi via socket

5. Start Engine
   └─▶ Launch query server thread (port 4097)
   └─▶ Launch HTTP server thread (port 5000)
   └─▶ Create PyQt5 overlays (hidden initially)
   └─▶ Enter main event loop
```

### Main Event Loop Flow

```
┌─────────────────────────────────────────────────┐
│              Engine Main Loop (20 FPS)          │
└─────────────────────────────────────────────────┘
                      │
                      ▼
      ┌───────────────────────────────┐
      │ 1. Process Qt Events          │
      │    (Keep overlays responsive) │
      └───────────────┬───────────────┘
                      │
                      ▼
      ┌───────────────────────────────┐
      │ 2. Query SOS for clip info    │
      │    - Get clip number (fast)   │
      │    - Lookup name in cache     │
      └───────────────┬───────────────┘
                      │
                      ▼
      ┌───────────────────────────────┐
      │ 3. Clip changed?              │
      └───────────────┬───────────────┘
                      │
          ┌───────────┴────────────┐
          │ YES                    │ NO
          ▼                        │
  ┌──────────────────┐             │
  │ CLIP TRANSITION  │             │
  └──────────────────┘             │
          │                        │
          ├─▶ Instant clear overlays
          ├─▶ Navigate LibreOffice to new slide (7s)
          ├─▶ Start internal timer
          ├─▶ Show overlays instantly
          ├─▶ Schedule deferred operations:
          │   ├─▶ Update Now Playing (background thread)
          │   ├─▶ Start/fade audio (background thread)
          │   └─▶ Load subtitles (background thread)
          │
          └─────────────┬─────────────┘
                        │
                        ▼
      ┌───────────────────────────────┐
      │ 4. Update overlays            │
      │    - Progress bar (time %)    │
      │    - Subtitles (if enabled)   │
      └───────────────┬───────────────┘
                      │
                      ▼
      ┌───────────────────────────────┐
      │ 5. Sleep 50ms (20 FPS)        │
      └───────────────┬───────────────┘
                      │
                      └──────────────────┐
                                         │
                    ┌────────────────────┘
                    │
                    ▼
            Loop continues...
```

## Key Design Patterns

### 1. Initialization/Access Separation

Each subsystem is split into two modules:
- `*_init.py` - Configuration loading and component initialization
- `*_access.py` - Runtime control and communication

**Example**: Audio System
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
5. Update Now Playing display
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

Three concurrent server threads handle external queries:

**Query Server** (Port 4097)
- Listens for state requests from Raspberry Pi
- Returns: Playlist + current clip number
- Used when Pi reconnects after failure

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
    ├─▶ Update Now Playing
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

### Now Playing Protocol (TCP Socket)

```
Engine → Pi (INIT):
  "INIT\n"
  "1|English Title 1|Spanish Title 1|1m 30s\n"
  "2|English Title 2|Spanish Title 2|2m 0s\n"
  ...

Engine → Pi (CLIP):
  "CLIP:5\n"

Engine → Pi (PAUSE):
  "PAUSE\n"

Engine → Pi (UNPAUSE):
  "UNPAUSE\n"
```

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
