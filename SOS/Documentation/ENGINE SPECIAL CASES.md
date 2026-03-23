# Engine Special Cases & Advanced Patterns

## Overview
This document covers special handling logic, architectural patterns, and edge cases in the SOS2 Engine beyond the basic translated movies and credits functionality. These patterns ensure robustness, performance, and user experience quality.

---

## 1. Facilitation Mode

### Purpose
Allows presenters to pause the experience and speak to the audience without competing audio or visual distractions.

### Trigger
HTTP command: `{"command": "FACILITATION_TOGGLE", "enable": true/false}`

### Behavior When Enabled

```python
# Location: engine.py, _toggle_facilitation()

if enable:
    # Audio Management
    if audio_controller.is_playing():
        audio_controller.fade_out()  # Smooth fadeout
        time.sleep(SUBTITLE_FADE_WAIT)  # Wait for completion
    audio_controller.mute()  # Prevent new audio
    
    # External Display
    send_to_nowplaying("PAUSE")  # Pause Pi display
```

### Behavior When Disabled
```python
else:
    audio_controller.unmute()  # Re-enable audio
    send_to_nowplaying("UNPAUSE")  # Resume Pi display
```

### Impact on Other Systems

| System | Behavior in Facilitation Mode |
|--------|------------------------------|
| **Audio** | Fades out, mutes, blocks new tracks |
| **NowPlaying Display** | Shows "PAUSE" status |
| **Overlays** | Continue updating (progress bar still visible) |
| **Clip Detection** | Still active (clips can change) |
| **Audio Start** | Blocked via `manage_audio()` check |

### State Management
- Uses thread-safe lock (`self.state_lock`) for concurrent access
- Persists across clip changes until explicitly disabled
- Checked at start of `manage_audio()` to prevent new tracks

---

## 2. Overlay Mode State Machine

### Three Distinct States

```python
# Location: engine.py, OverlayManager class

STATES = {
    "HIDDEN": "No overlays (used for credits)",
    "PROGRESS_ONLY": "Progress bar only (regular datasets)",
    "SUBTITLES_AND_PROGRESS": "Both overlays (translated movies)"
}
```

### State Transitions

```
HIDDEN ─┬─> PROGRESS_ONLY (regular dataset starts)
        └─> SUBTITLES_AND_PROGRESS (translated movie starts)

PROGRESS_ONLY ──> HIDDEN (credits clip)

SUBTITLES_AND_PROGRESS ──> HIDDEN (credits clip)
```

### Special Method: `instant_clear()`

**Purpose**: Skip fade animations for clean clip transitions

```python
# Location: engine.py, OverlayManager.instant_clear()

def instant_clear(self):
    # Stop any in-progress fade animation
    anim = getattr(self.progress_overlay, 'fade_animation', None)
    if anim:
        anim.stop()  # Abort mid-flight animation
    
    # Instantly hide (no fade)
    self.subtitle_overlay.instant_hide()
    self.progress_overlay.hide()
    self.mode = "HIDDEN"
```

**Use Case**: Called at the start of every clip change to prevent visual artifacts from old overlays bleeding into new clips.

### Mode Guards

All update methods check the current mode:

```python
def update_progress(self, current_time, total_duration):
    if self.mode != "HIDDEN":  # Guard: only update if visible
        self.progress_overlay.update_progress(...)
        
def update_subtitles(self, text1, text2):
    if self.mode == "SUBTITLES_AND_PROGRESS":  # Guard: specific mode
        self.subtitle_overlay.update_subtitles(...)
```

---

## 3. Deferred Operations Pattern

### Problem
Long-blocking operations during clip changes cause:
- Progress bar appears frozen at 0:00 for several seconds
- Poor user experience (appears unresponsive)
- LibreOffice navigation already blocks for ~7 seconds

### Solution
Split operations into **immediate** and **deferred** phases:

#### Phase 1: Immediate (Main Thread)
```python
# Location: engine.py, run() main loop

# 1. Clear old overlays (instant)
self.overlay_manager.instant_clear()

# 2. Navigate LibreOffice slide (~7s blocking - unavoidable)
self.navigate_to_clip(clip_name)

# 3. Start timer
self.clip_start_time = time.time()

# 4. Show progress bar IMMEDIATELY (seeded at 0:00)
self.overlay_manager.reset_progress(duration)
self.overlay_manager.update_progress(0.0, duration)
self.overlay_manager.show_progress_only()  # or show_subtitles_and_progress()

# Progress bar now animates in main loop!
```

#### Phase 2: Deferred (Background Thread, ~0.5s later)
```python
# Schedule operations for background execution
self.deferred_operations_countdown = 10  # 10 iterations @ 50ms = 500ms

# After countdown expires:
threading.Thread(target=self._execute_deferred_operations_background).start()

# Background thread executes:
def _execute_deferred_operations_background(self):
    # 1. Update nowPlaying Pi display (~50-200ms)
    self.update_nowPlaying(clip_number)
    
    # 2. Audio management (~100-500ms)
    self.manage_audio(clip_name, is_credits, is_translated)
    
    # 3. Load subtitle files (translated movies only, ~200-1000ms)
    if is_translated and not is_credits:
        self.subtitle_manager.load_subtitles_for_clip(metadata)
```

### Timeline

```
T+0.0s:   Clip change detected
T+0.1s:   Overlays cleared (instant)
T+0.1s:   LibreOffice navigation starts (BLOCKING)
T+7.2s:   Navigation completes
T+7.2s:   Timer starts, progress bar shown at 0:00
T+7.2s:   Progress bar ANIMATING (main loop continues)
T+7.7s:   Countdown expires (10 iterations @ 50ms)
T+7.7s:   Background thread spawned
T+7.7-8.5s: Deferred ops execute in parallel with animation
```

### Benefits
- Progress bar visible and animating within 50ms of navigation completing
- User sees immediate feedback
- Slow operations (network, file I/O) don't block UI

---

## 4. Audio Fallback Logic

### Problem
Occasionally audio files become corrupted, unavailable, or fail to load due to network/filesystem issues.

### Solution
Two-tier fallback system:

```python
# Location: engine.py, manage_audio()

# Try primary track
next_track = cache_manager.get_next_audio_track(major_category)
success = audio_controller.play_audio(next_track, loop=True)

if not success:
    # Try fallback track (different file from same category)
    fallback_track = cache_manager.get_next_audio_track(major_category)
    
    if fallback_track and fallback_track != next_track:
        success = audio_controller.play_audio(fallback_track, loop=True)
        
        if success:
            print(f"[Audio] Fallback succeeded: {fallback_track}")
        else:
            print(f"[Audio] Fallback also failed — audio skipped for this clip")
    else:
        print(f"[Audio] No alternative fallback available")
```

### Fallback Strategy
1. **Primary attempt**: Use round-robin selection from audio pool
2. **Fallback attempt**: Get next track in sequence (different file)
3. **Graceful degradation**: If both fail, continue without audio (silent clip)

### Prevents
- Engine crashes due to audio errors
- Stuck playback states
- User-visible error messages

---

## 5. Multi-Category Handling

### Problem
Some clips have multiple categories in their metadata:

```json
{
  "majorcategory": "Earth Science, Geology, Climate"
}
```

### Constraint
Audio system can only play **one track at a time** (single MPV instance).

### Solution
Use **first category only**:

```python
# Location: engine.py, manage_audio()

if ',' in major_category:
    categories = [cat.strip() for cat in major_category.split(',')]
    major_category = categories[0]  # First takes precedence
    print(f"[Audio] Multiple categories detected, using first: {major_category}")
```

### Rationale
- First category typically represents the **primary** theme
- Consistent behavior across all clips
- Prevents ambiguity in audio selection

### Example

| Original Metadata | Audio Category Used |
|-------------------|---------------------|
| `"Earth Science"` | Earth Science |
| `"Geology, Climate"` | Geology |
| `"Ocean, Biology, Ecology"` | Ocean |

---

## 6. Duration Capping

### Problem
Progress calculations could overflow if:
- Internal timer drifts
- Clip runs longer than expected
- System time jumps (DST, manual adjustment)

### Solution
Cap elapsed time at clip duration:

```python
# Location: engine.py, get_elapsed_time()

def get_elapsed_time(self):
    if self.clip_start_time is None:
        return 0.0
    
    elapsed = time.time() - self.clip_start_time
    return min(elapsed, self.current_clip_duration)  # Cap at max duration
```

### Prevents
- Progress bar exceeding 100%
- Negative remaining time displays
- UI overflow errors in progress overlay

### Example

| Actual Elapsed | Clip Duration | Returned Value |
|----------------|---------------|----------------|
| 45.2s | 60.0s | 45.2s |
| 60.0s | 60.0s | 60.0s |
| 73.5s | 60.0s | 60.0s (capped) |

---

## 7. Fresh Socket Pattern

### Dual Socket Architecture

The engine uses **two different socket strategies**:

#### 1. Persistent Socket (Monitoring)
```python
# Location: engine.py, connect_to_sos() and run()

self.sock = socket.socket()
self.sock.connect((SOS_IP, SOS_PORT))
self.sock.sendall(b'enable\n')

# Used for: Continuous clip monitoring
while self.running:
    self.sock.sendall(b'get_clip_number\n')
    data = self.sock.recv(1024)
    # ... process ...
```

**Characteristics**:
- Single long-lived connection
- Fast repeated queries
- Stateful (remains "enabled")

#### 2. Fresh Sockets (Navigation Commands)
```python
# Location: engine.py, _sos_nav_command()

def _sos_nav_command(self, command: str):
    sock = socket.socket()  # NEW connection
    sock.settimeout(SOS_CONNECTION_TIMEOUT)
    sock.connect((SOS_IP, SOS_PORT))
    sock.sendall(b'enable\n')
    sock.sendall(command.encode('utf-8'))
    data = recv_data(sock, timeout_idle=1.0)
    sock.close()  # Immediate cleanup
```

**Characteristics**:
- One-off connection per command
- Clean state (no pollution from main loop)
- Immediate closure (prevents resource leaks)

### Why Two Strategies?

| Use Case | Socket Type | Reason |
|----------|-------------|--------|
| Continuous monitoring | Persistent | Performance (avoid handshake overhead) |
| HTTP-triggered nav | Fresh | Isolation (prevent state conflicts) |
| Playlist queries | Fresh | Separate from monitoring loop |

### Navigation Commands Using Fresh Sockets
- `next_clip`
- `prev_clip`
- `play {clip_number}`
- `get_playlist_name`
- `get_clip_count`

---

## 8. HTTP Command Routing

### Remote Control Interface
Engine runs HTTP server on port **5000** for external control (facilitation tablet, web interface).

### Supported Commands

#### 1. `FACILITATION_TOGGLE`
```json
{"command": "FACILITATION_TOGGLE", "enable": true}
```
**Response**: `{"status": "ok", "facilitation_mode": true}`

---

#### 2. `VOLUME_CONTROL`
```json
{"command": "VOLUME_CONTROL", "action": "UP"}
```
**Actions**: `UP`, `DOWN`, `MUTE`  
**Response**: `{"status": "ok", "volume": 75}`

---

#### 3. `GET_STATE`
```json
{"command": "GET_STATE"}
```
**Response**:
```json
{
  "status": "ok",
  "facilitation_mode": false,
  "current_clip": 3,
  "volume": 80,
  "audio_enabled": true
}
```

---

#### 4. `GET_PLAYLIST`
```json
{"command": "GET_PLAYLIST"}
```
**Response**:
```json
{
  "status": "ok",
  "playlist_name": "Ocean_Life_Show",
  "current_clip": 2,
  "clips": [
    {"clip_number": 1, "name": "Ocean Intro"},
    {"clip_number": 2, "name": "Coral Reefs"},
    {"clip_number": 3, "name": "Deep Sea"}
  ]
}
```

**Smart Fallback**: Uses in-memory cache first, falls back to SOS query if needed.

---

#### 5. `DATASET_NEXT` / `DATASET_PREV`
```json
{"command": "DATASET_NEXT"}
```
**Response**: `{"status": "ok"}`

---

#### 6. `DATASET_PLAY`
```json
{"command": "DATASET_PLAY", "clip_number": 5}
```
**Response**: `{"status": "ok"}`

---

### CORS Support
All HTTP responses include CORS headers for web-based clients:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, GET, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

### OPTIONS Preflight Handling
Browsers send OPTIONS requests before POST/GET. Engine responds with headers only:

```python
if method == "OPTIONS":
    response = "HTTP/1.1 200 OK\r\n"
    response += "Access-Control-Allow-Origin: *\r\n"
    # ... more headers ...
    response += "Content-Length: 0\r\n\r\n"
```

---

## 9. State Query INIT Message

### Purpose
When the Raspberry Pi "Now Playing" display boots or reconnects, it needs the full playlist state.

### Query Protocol
Pi sends: `REQUEST_STATE`  
Engine responds with **INIT message**:

```
INIT
1|Ocean Life|Vida Oceánica|2m 30s
2|Coral Reefs|Arrecifes de Coral|1m 45s
3|Deep Sea|Mar Profundo|3m 15s

CLIP:2
```

### Format Specification

#### Line 1: Header
```
INIT
```

#### Lines 2-N: Clip Entries
```
{index}|{english_title}|{spanish_title}|{duration}
```

**Fields**:
- `index`: 1-based clip number
- `english_title`: From metadata `movie-title` or clip name
- `spanish_title`: From metadata `spanish-translation` or empty
- `duration`: Formatted as `"Xm Xs"` (e.g., `"2m 30s"`)

#### Last Section: Current Clip
```
CLIP:{current_clip_number}
```

### Building the Message

```python
# Location: engine.py, _build_init_message()

clips = cache_manager.current_playlist.get('clips', [])
lines = ["INIT"]

for idx, clip in enumerate(clips, start=1):
    metadata = cache_manager.get(clip_name) or {}
    
    english_title = metadata.get('movie-title', clip_name)
    spanish_title = metadata.get('spanish-translation', '')
    duration_sec = float(metadata.get('duration', 0))
    
    # Format duration (no decimals)
    minutes = int(duration_sec) // 60
    seconds = int(duration_sec) % 60
    duration_str = f"{minutes}m {seconds}s"
    
    lines.append(f"{idx}|{english_title}|{spanish_title}|{duration_str}")

return "\n".join(lines) + "\n"
```

### Thread Safety
Uses `self.state_lock` to safely read `current_clip_number` from the main loop thread.

---

## 10. Subtitle File Path Resolution

### Problem
Subtitle metadata contains **remote server paths**:

```json
{
  "caption": "/datasets/movies/example_en.srt",
  "caption2": "/datasets/movies/example_es.srt"
}
```

But subtitle parser needs **local filesystem paths**.

### Solution
Fetch and cache subtitles, then update metadata to local paths:

```python
# Location: engine.py, _execute_deferred_operations_background()

if is_translated and not is_credits and pending_metadata:
    local_meta = pending_metadata.copy()
    
    # Convert remote → local for English subtitle
    if pending_metadata.get('caption'):
        remote_path = pending_metadata['caption']
        local_path = cache_manager.fetch_subtitle_file(remote_path)
        if local_path:
            local_meta['caption'] = local_path  # Update to local
    
    # Convert remote → local for Spanish subtitle
    if pending_metadata.get('caption2'):
        remote_path = pending_metadata['caption2']
        local_path = cache_manager.fetch_subtitle_file(remote_path)
        if local_path:
            local_meta['caption2'] = local_path  # Update to local
    
    # Load with local paths
    subtitle_manager.load_subtitles_for_clip(local_meta)
```

### Fetch Logic (CacheManager)

```python
# Location: cache_manager.py, fetch_subtitle_file()

def fetch_subtitle_file(self, source_path):
    filename = os.path.basename(source_path)
    cached_path = os.path.join(self.subtitle_cache_dir, filename)
    
    # Already cached?
    if os.path.exists(cached_path):
        return cached_path
    
    # Try local copy first (if accessible)
    if os.path.exists(source_path):
        shutil.copy2(source_path, cached_path)
        return cached_path
    
    # Try SCP from SOS server
    # ... multiple authentication methods ...
    
    return cached_path if os.path.exists(cached_path) else None
```

### Cache Location
```
\\sos2\AuxShare\cache\subtitles\
```

---

## 11. Presentation Transition Delay

### Problem
When transitioning from **credits → translated movie**, the subtitle overlay appears too abruptly, creating a jarring visual experience.

### Solution
Small delay for translated movies only:

```python
# Location: engine.py, run() main loop

if is_translated:
    time.sleep(PRESENTATION_TRANSITION_DELAY)  # Smooth easing
    self.overlay_manager.show_subtitles_and_progress()
```

### Constant Definition
```python
# Location: config/constants.py
PRESENTATION_TRANSITION_DELAY = 0.3  # seconds
```

### Why Not for Regular Datasets?
Regular datasets show **progress bar only**, which is less visually intrusive. Translated movies show **both progress bar and subtitle overlay**, requiring smoother easing.

### Timeline

```
CREDITS CLIP (overlays hidden)
    ↓
LibreOffice navigation (~7s)
    ↓
[if is_translated: 300ms delay]
    ↓
Subtitle + Progress overlays fade in
```

---

## 12. Additional Edge Cases

### Empty Clip Name Handling
```python
clip_name = clips[clip_number - 1].get('name')
navigate_to_clip(clip_name or "")  # Empty string fallback
```

### No Slide Mapping Warning
```python
if clip_name not in self.slide_dictionary:
    print(f"[Engine] Warning: No slide mapping for '{clip_name}'")
    return  # Graceful skip
```

### Duration Type Coercion
Handles string, int, and float durations:
```python
if isinstance(duration_raw, str):
    try:
        duration_sec = float(duration_raw)
    except ValueError:
        duration_sec = 0
else:
    duration_sec = float(duration_raw)
```

### Missing Audio Controller
All audio operations check availability first:
```python
if not self.audio_enabled or not self.audio_controller:
    return  # Silent fallback
```

---

## Summary Table

| Special Case | Purpose | Impact |
|--------------|---------|--------|
| **Facilitation Mode** | Pause for presenter | Audio + NowPlaying |
| **Overlay State Machine** | Visual consistency | Progress + Subtitle display |
| **Deferred Operations** | UI responsiveness | Threading + timing |
| **Audio Fallback** | Robustness | Silent fallback on errors |
| **Multi-Category** | Single audio track | First category wins |
| **Duration Capping** | Progress overflow protection | Timer bounds |
| **Fresh Sockets** | Nav isolation | Connection strategy |
| **HTTP Commands** | Remote control | Web/tablet interface |
| **INIT Message** | Pi display sync | State recovery protocol |
| **Path Resolution** | Subtitle loading | Remote → local conversion |
| **Transition Delay** | Visual smoothness | Translated movies only |

---

## Development Guidelines

### Adding New Special Cases
1. **Document the pattern** in this file
2. **Add debug logging** with clear prefixes (`[Audio]`, `[Engine]`, etc.)
3. **Consider edge cases** (null values, network failures, etc.)
4. **Test isolation** (does it affect other systems?)
5. **Performance impact** (can it be deferred?)

### Debugging Special Cases
Most special cases have dedicated logging:
```
[Audio] Fallback succeeded: track_02.mp3
[Engine HTTP] Facilitation ON
[Engine] Launching deferred operations in background thread
```

Use these logs to trace execution flow and timing.

---

**Last Updated**: March 16, 2026  
**Maintainer**: Development Team  
**Related Docs**: 
- [METADATA_AND_CUSTOM_MOVIES.md](METADATA_AND_CUSTOM_MOVIES.md) - Translated movies & credits
- [ARCHITECTURE.md](ARCHITECTURE.md) - System overview
