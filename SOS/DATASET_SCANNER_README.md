# SOS Dataset Scanner - Workflow Guide

## Overview
This solution allows your remote computer to identify which SOS datasets are movies and locate their .srt caption files, without needing to maintain a manual CSV file with movie indicators.

## Files Created

### On SOS Server:
- **`sos_dataset_scanner.py`** - Standalone script that scans the SOS dataset directory structure

### On Remote Computer:
- **`dataset_cache_loader.py`** - Module to load and query the cache
- **`INTEGRATION_EXAMPLE.py`** - Example of how to integrate into your existing code

## Workflow

### Step 1: Run Scanner on SOS Server

Copy `sos_dataset_scanner.py` to the SOS server and run it:

```bash
# On the SOS server
python sos_dataset_scanner.py C:/sos/datasets/
```

Or with a custom output location:

```bash
python sos_dataset_scanner.py C:/sos/datasets/ output/dataset_cache.json
```

This will:
- Recursively scan all theme folders (air, land, ocean, etc.)
- Find all folders containing `playlist.sos`
- Detect video files (.mp4, .mov, .avi, etc.)
- Locate associated .srt caption files
- Generate two files:
  - `dataset_cache.json` - Machine-readable cache
  - `dataset_cache.csv` - Human-readable report

### Step 2: Copy Cache to Remote Computer

Transfer the generated `dataset_cache.json` file to your remote computer:

```bash
# Example using network share
copy dataset_cache.json \\remote-computer\sos\
```

Or via any file transfer method (SCP, USB, shared folder, etc.)

### Step 3: Update Remote Scripts

Integrate the cache into your existing code:

```python
# In your sdc_simple.py or engine.py
from dataset_cache_loader import DatasetCache

# Load the cache (do this at startup)
cache = DatasetCache("C:/path/to/dataset_cache.json")

# Query during runtime
if cache.is_movie(clip_name):
    print("This is a movie!")
    
    if cache.has_captions(clip_name):
        srt_path = cache.get_srt_path(clip_name)
        print(f"Captions at: {srt_path}")
        
        # Load and parse SRT content
        srt_content = cache.get_srt_content(clip_name)
```

## Cache File Structure

The `dataset_cache.json` file contains:

```json
{
  "scan_timestamp": "2025-11-05T10:30:00",
  "total_datasets": 450,
  "total_movies": 87,
  "datasets": {
    "Aquaculture": {
      "is_movie": true,
      "theme": "ocean",
      "path": "C:/sos/datasets/ocean/Aquaculture",
      "srt_files": ["Aquaculture.srt"],
      "srt_path": "C:/sos/datasets/ocean/Aquaculture/Aquaculture.srt",
      "video_files": ["Aquaculture.mp4"],
      "has_captions": true
    },
    "Hurricane Tracks": {
      "is_movie": false,
      "theme": "weather",
      "path": "C:/sos/datasets/weather/Hurricane Tracks",
      "srt_files": [],
      "srt_path": null,
      "video_files": [],
      "has_captions": false
    }
  }
}
```

## Benefits Over Manual CSV

✅ **Automatic detection** - No manual tagging of datasets as "movie"  
✅ **Finds SRT files** - Automatically locates caption files  
✅ **Theme organization** - Preserves SOS folder structure  
✅ **Easy updates** - Just re-run scanner when datasets change  
✅ **Detailed info** - Includes paths, video files, themes, etc.  
✅ **CSV export** - Human-readable report for review  

## Maintenance

When SOS datasets are added, removed, or modified:

1. Re-run `sos_dataset_scanner.py` on the SOS server
2. Copy new `dataset_cache.json` to remote computer
3. Restart your remote control application

You could automate this with a scheduled task or cron job.

## Notes

- The scanner checks for `playlist.sos` files to identify dataset folders
- Video detection looks for common extensions: .mp4, .mov, .avi, .m4v, .mpg, .mpeg, .wmv
- Also checks playlist.sos content for video file references
- SRT files must be in the same folder as the video files
- Remote computer needs filesystem access to read SRT files (or copy them separately)

## Troubleshooting

**No datasets found:**
- Verify the SOS data path is correct
- Check that dataset folders contain `playlist.sos` files

**Movies not detected:**
- Ensure video files have recognized extensions
- Check that `playlist.sos` references the video files

**Can't read SRT files on remote computer:**
- Ensure remote computer has network access to SOS filesystem
- Or: Copy SRT files separately to remote computer
- Or: Modify loader to fetch via HTTP if SOS exposes datasets via web
