# Metadata & Custom Movies Documentation

## Overview
This document explains the special logic for handling **translated movies** (`is_translated`), **credits clips**, and the **metadata management system** in the SOS2 Engine.

---

## 1. Translated Movies (`is_translated`)

### What Are Translated Movies?
Translated movies are custom video files (typically `.mp4`) located in the `/site-custom/` directory that include **dual-language subtitles** (English and Spanish). They receive special treatment in the engine:

- **Custom duration** (variable length, not fixed 60s)
- **Dual subtitle display** (bilingual overlay with English and Spanish captions)
- **No ambient audio** (audio is embedded in the video)
- **Title display** (shows both English and Spanish movie titles)

---

## 2. Detection Criteria for `is_translated`

The `CacheManager` automatically detects translated movies during playlist sync using **4 criteria**:

```python
# Location: cache_manager.py, fetch_and_update_full_data()

is_site_custom = '/site-custom/' in normalized_path.lower()
is_mp4 = 'mp4' in datadir_val or normalized_path.endswith('.mp4')
has_captions = 'caption' in metadata and 'caption2' in metadata

is_translated = is_site_custom and is_mp4 and has_captions
```

### Criteria Breakdown:
1. **Path Check**: Clip's `filename` or `datadir` contains `/site-custom/`
2. **Format Check**: `datadir` indicates `.mp4` file extension
3. **English Caption**: Metadata has `caption` field (English subtitle path)
4. **Spanish Caption**: Metadata has `caption2` field (Spanish subtitle path)

> **Note**: All 4 criteria must be TRUE for a clip to be marked as `is_translated`.

---

## 3. Translated Movie Behavior in Engine

When `is_translated == True`, the engine activates special handling:

```python
# Location: engine.py, run() main loop

if is_translated and metadata.get('duration'):
    # Use metadata-specified duration instead of default 60s
    self.current_clip_duration = float(metadata.get('duration', 60.0))
    
    # Show both progress bar and subtitle overlay
    self.overlay_manager.show_subtitles_and_progress()
    
    # Load bilingual titles from CSV
    spanish_title, english_title = self.cache_manager.get_clip_titles(clip_name)
    self.overlay_manager.update_titles(english_title, spanish_title)
    
    # Load subtitle files in background thread (deferred operation)
    self.subtitle_manager.load_subtitles_for_clip(metadata)
```

### Key Differences:
| Feature | Regular Dataset | Translated Movie |
|---------|----------------|------------------|
| Duration | Fixed 60s | Variable (from metadata) |
| Overlay Mode | Progress bar only | Progress + subtitles |
| Audio | Ambient category audio | No audio (embedded) |
| Titles | Not displayed | English + Spanish |
| Subtitles | None | Dual (.srt files) |

---

## 4. Credits Handling

### Detection
Credits clips are identified by **clip name pattern matching**:

```python
# Location: engine.py, run() main loop
is_credits = "credits" in (clip_name or "").lower()
```

Any clip whose name contains the substring `"credits"` (case-insensitive) is treated as a credits clip.

### Credits Behavior
When `is_credits == True`:

- **All overlays hidden** (no progress bar, no subtitles)
- **No audio management** (assumes silent or embedded audio)
- **Default duration** (60s)
- **Normal slide navigation** (still maps to LibreOffice slides)

```python
# Location: engine.py, run() main loop
if not is_credits:
    # Show progress bar and subtitles
    self.overlay_manager.reset_progress(self.current_clip_duration)
    # ... subtitle logic ...
else:
    # Keep overlays hidden for credits
    print("[Engine] Credits detected - overlays remain hidden")
```

---

## 5. Metadata Management Architecture

### Two-Tier Cache System

The `CacheManager` maintains two JSON cache files:

#### 1. **Playlist Cache** (`playlist_cache.JSON`)
Stores playlist structure and ordered clip list:
```json
{
  "name": "playlist_name.sos",
  "path": "/full/path/to/playlist.sos",
  "last_modified": "2026-03-15",
  "clips": [
    {"name": "example_clip_name"},
    {"name": "otro_clip"}
  ]
}
```

#### 2. **Clip Metadata Cache** (`clip_metadata_cache.JSON`)
Stores detailed metadata for each clip:
```json
{
  "ejemplo_de_clip": {
    "name": "ejemplo_de_clip",
    "duration": 120.5,
    "caption": "/path/to/subtitles_en.srt",
    "caption2": "/path/to/subtitles_es.srt",
    "translated-movie": true,
    "movie-title": "Example Movie Title",
    "spanish-translation": "Título de Ejemplo",
    "majorcategory": "Earth Science",
    "datadir": "/datasets/site-custom/ejemplo_de_clip.mp4"
  }
}
```

### Key Metadata Fields

| Field | Type | Purpose | Used By |
|-------|------|---------|---------|
| `name` | string | Unique clip identifier | Engine navigation |
| `duration` | float | Clip length in seconds | Progress bar (translated movies only) |
| `caption` | string | English subtitle path | Subtitle manager |
| `caption2` | string | Spanish subtitle path | Subtitle manager |
| `translated-movie` | boolean | Special handling flag | Engine overlay logic |
| `movie-title` | string | English display name | Overlay title display (fallback) |
| `spanish-translation` | string | Spanish display name | CSV lookup (fallback) |
| `majorcategory` | string | Content category | Audio selection system |
| `datadir` | string | File path/location | Translated movie detection |

---

## 6. Subtitle File Caching

The `CacheManager` automatically fetches subtitle files during playlist sync:

```python
# Location: cache_manager.py, cache_subtitles()

for clip_name, metadata in self.clip_metadata.items():
    is_translated = self.is_translated_movie(clip_name)
    
    if is_translated and 'caption' in metadata:
        # Fetch English subtitle
        self.fetch_subtitle_file(metadata['caption'])
        
        # Derive Spanish subtitle path (_en.srt → _es.srt)
        if '_en.srt' in caption_path:
            caption2_path = caption_path.replace('_en.srt', '_es.srt')
            self.fetch_subtitle_file(caption2_path)
            metadata['caption2'] = caption2_path
```

### Subtitle Naming Convention
- **English**: `movie_name_en.srt`
- **Spanish**: `movie_name_es.srt`

Files are cached locally to: `\\sos2\AuxShare\cache\subtitles\`

---

## 7. Title Display System

Titles for translated movies are loaded from a CSV file:

```python
# Location: cache_manager.py, load_titles_csv()

# CSV Format: Dataset Name (Auto), Spanish Title, English Title, ...
# Example row: "my_movie_clip", "Mi Película", "My Movie"

self.dataset_titles[dataset_name] = {
    'spanish': spanish_title,
    'english': english_title
}
```

**Fallback Chain**:
1. CSV title lookup (`get_clip_titles()`)
2. Metadata field `movie-title` (English only)
3. Raw clip name (last resort)

---

## 8. Audio Management Rules

The engine's audio logic follows these rules:

```python
# Location: engine.py, manage_audio()

if is_credits or is_translated:
    # Stop any playing audio (fade out)
    # No new audio starts
    return

# For regular datasets:
major_category = cache_manager.get_majorcategory(clip_name)
next_track = cache_manager.get_next_audio_track(major_category)
audio_controller.play_audio(next_track, loop=True)
```

### Audio Decision Table

| Condition | Audio Behavior |
|-----------|---------------|
| Regular dataset | Play category-based ambient track |
| Translated movie | No audio (embedded in video) |
| Credits clip | No audio |
| Facilitation mode ON | Fade out and mute |

---

## 9. Engine Flow for Clip Change

This is the sequence when a new clip is detected:

```
1. Detect clip number change (get_current_clip_info)
   ↓
2. Resolve metadata and flags (is_credits, is_translated)
   ↓
3. Determine clip duration (translated: metadata, regular: 60s)
   ↓
4. Instantly clear old overlays (instant_clear)
   ↓
5. Navigate to LibreOffice slide (~7s blocking operation)
   ↓
6. START INTERNAL TIMER (clip_start_time)
   ↓
7. Show progress bar immediately (reset_progress, update_progress)
   ↓
8. For translated movies: show subtitle overlay + load titles
   ↓
9. Schedule deferred operations in background thread (~0.5s delay):
   - Send nowPlaying update to Pi
   - Manage audio (start/stop based on clip type)
   - Load subtitle files from cache (translated movies only)
   ↓
10. Loop: Update progress bar and subtitles every 50ms (20 FPS)
```

---

## 10. Developer Notes

### Adding a New Translated Movie
1. Place `.mp4` file in `/datasets/site-custom/` on SOS server
2. Create subtitle files: `movie_name_en.srt` and `movie_name_es.srt`
3. Add entry to SOS playlist (`.sos` file)
4. Ensure metadata includes:
   - `caption`: Path to English subtitle
   - `caption2`: Path to Spanish subtitle
   - `duration`: Video length in seconds
5. Add title entry to `SOS_datasets.csv`
6. Restart engine — auto-detection will mark it as `translated-movie: true`

### Troubleshooting Detection Issues
If a movie isn't detected as translated, check these in order:

```python
# Add debug output in cache_manager.py, fetch_and_update_full_data()
print(f"  is_site_custom: {is_site_custom}")
print(f"  is_mp4: {is_mp4}")
print(f"  has 'caption': {'caption' in metadata}")
print(f"  has 'caption2': {'caption2' in metadata}")
print(f"  → is_translated: {is_translated}")
```

Common issues:
- **Path mismatch**: File not in `/site-custom/` folder
- **Missing caption2**: Only one subtitle file defined
- **Wrong format**: Not an `.mp4` file (check `datadir`)
- **Metadata parse error**: name-value pairs not extracted correctly

---

## 11. Related Files

| File | Purpose |
|------|---------|
| `engine.py` | Main loop, clip detection, overlay management |
| `cache_manager.py` | Metadata fetching, caching, translated movie detection |
| `overlay_subtitles.py` | Subtitle display and parsing |
| `overlay_progressBar.py` | Progress bar rendering |
| `clip_metadata_cache.JSON` | Runtime metadata storage |
| `SOS_datasets.csv` | Title translations database |

---

## 12. Future Enhancements

Potential improvements for consideration:

- **Multi-language support**: Add more subtitle tracks (French, Mandarin, etc.)
- **Automatic subtitle generation**: Use speech-to-text for English, then translate
- **Dynamic duration detection**: Query video file directly instead of metadata
- **Subtitle format support**: Support WebVTT in addition to SRT
- **Metadata validation**: Pre-flight check for missing fields before engine starts

---

**Last Updated**: March 16, 2026  
**Maintainer**: Development Team  
**Version**: 2.0
