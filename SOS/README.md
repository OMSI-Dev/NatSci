# SOS Control System

**Science on a Sphere Control System** - A Python-based orchestration system for NOAA Science on a Sphere installations.

## Overview

This system provides synchronized control of:
-  **NOAA SOS Server** - Real-time communication with Science on a Sphere
-  **LibreOffice Impress** - Automated presentation navigation
-  **PyQt5 Overlays** - Progress bars and dual-language subtitles
-  **Remote Audio** - MPV playback with category-based ambient soundscapes
-  **Now Playing Display** - Raspberry Pi-based audience information display
-  **HTTP API** - Web-based facilitation controls

## Features

 **Caching** - Minimizes server queries for fast response times  
 **Dual-Language Subtitles** - English and Spanish side-by-side for custom movies  
 **Ambient Audio** - Category-based background music with smooth fades  
 **Facilitation Mode** - Quick mute/pause controls via web interface  
 **Progress Tracking** - Real-time progress bar with slide markers  
 **Automatic Recovery** - Self-healing SSH and MPV connections  

## Quick Start

### Prerequisites

- **Windows 10/11** (tested on Windows)
- **Python 3.8+**
- **LibreOffice 7.0+**
- **Network access** to SOS2 server (default: `\\sos2\AuxShare`)
- **SSH keys** configured for SOS2 server

### Installation

1. **Clone the repository**
   ```bash
   cd C:\Users\<username>\Documents\Github\NatSci\SOS
   ```

2. **Install Python dependencies**
   ```bash
   pip install PyQt5 pywin32
   ```

3. **Configure the system**
   
   Copy the example configuration:
   ```bash
   cd main\config
   copy settings.json.example settings.json
   ```
   
   Edit `settings.json` with your network settings (or use environment variables).

4. **Verify network access**
   
   Ensure you can access:
   - `\\sos2\AuxShare` - Network share
   - `10.0.0.16:2468` - SOS server
   - SSH access to `sos@10.0.0.16`

### Running the System

```bash
cd main
python sdc.py
```

The system will:
1. Connect to SOS server and load current playlist
2. Sync cache if playlist has changed
3. Launch LibreOffice Impress with the presentation
4. Initialize MPV audio on remote server
5. Start monitoring for clip changes

Press `Ctrl+C` to stop gracefully.

## Configuration

### Method 1: JSON Configuration (Recommended)

Create `main/config/settings.json`:

```json
{
  "sos": {
    "ip": "10.0.0.16",
    "port": 2468
  },
  "pi": {
    "ip": "10.10.51.111",
    "enabled": false
  },
  "paths": {
    "base_share": "\\\\sos2\\AuxShare"
  },
  "features": {
    "nowplaying_enabled": false,
    "audio_enabled": true
  }
}
```

See `config/settings.json.example` for all options.

### Method 2: Environment Variables

Set environment variables (overrides JSON):

```bash
set SOS_IP=10.0.0.16
set PI_ENABLED=false
set SOS_BASE_SHARE=\\sos2\AuxShare
python sdc.py
```

See `config/.env.example` for all variables.

## Project Structure

```
main/
├── sdc.py                      # Main entry point
├── engine.py                   # Core orchestration engine
├── cache_manager.py            # Playlist/metadata caching
├── pp_init.py, pp_access.py   # LibreOffice control
├── audio_init.py, audio_access.py  # Audio system
├── overlay_progressBar.py      # Progress bar overlay
├── overlay_subtitles.py        # Subtitle overlay
├── config/                     # Configuration system
│   ├── config.py               # Config management
│   ├── constants.py            # System constants
│   ├── settings.json.example   # Configuration template
│   └── .env.example            # Environment variables template
├── ref/                        # Reference data files
│   ├── SOS_datasets.csv        # Clip-to-slide mappings
│   └── audio/
│       └── audio-list.csv      # Audio category mappings
└── CODE_REVIEW.md              # Code organization review
```

## System Requirements

### Hardware
- **Control PC**: Beelink
- **SOS2 Server**: Ubuntu Linux (also hosts MPV for audio)
- **Raspberry Pi**: For Now Playing display

### Network
- All systems on same network
- SSH key authentication to SOS2 server
- Network share access to `\\sos2\AuxShare`

### Software
- Python 3.8+
- PyQt5 (for overlays)
- pywin32 (for COM automation)
- LibreOffice 7.0+ (for presentation control)
- MPV (on SOS2 server)
- socat (on SOS2 server)

## Usage

### Normal Operation

0. Run 'Start SOS' on SOS2's desktop
1. Start the system: `python sdc.py`
2. The system automatically monitors SOS for clip changes
3. Overlays appear/hide based on dataset type:
   - **Regular datasets**: Progress bar only
   - **Custom movies**: Progress bar + subtitles
   - **Credits**: Overlays hidden

### Facilitation Controls

Access the web interface at `10.0.0.16' on the 5G Network 

**Available Controls:**
- Play specific dataset
- Next/Previous dataset
- Volume up/down/mute
- Facilitation mode (mutes audio, pauses Now Playing)
- View current playlist

See `Documentation/HTTP Server/sos.html` for the control interface.

### Debug Mode

Enable verbose logging in `config/settings.json`:

```json
{
  "debug": {
    "show_borders": true,
    "verbose_ssh": true,
    "verbose_mpv": true
  }
}
```

### Testing Utilities

Utility scripts in `../Utility Scripts/`:
- `1_test_connect.py` - Test SOS connection
- `3_query_metadata.py` - Query clip metadata
- `6_get_playlist_info.py` - View playlist structure
- `7_mpv_socket_test.py` - Test MPV audio
- `8_current_clip_info.py` - Check current clip

### HTTP Facilitation API

**Endpoints:**

```javascript
// Get system state
POST / 
{
  "command": "GET_STATE"
}

// Get playlist
POST /
{
  "command": "GET_PLAYLIST"  
}

// Play specific dataset
POST /
{
  "command": "DATASET_PLAY",
  "clip_number": 5
}

// Navigation
POST /
{
  "command": "DATASET_NEXT"  // or DATASET_PREV
}

// Volume control
POST /
{
  "command": "VOLUME_CONTROL",
  "action": "UP"  // or "DOWN", "MUTE"
}

// Facilitation mode (pause and mute)
POST /
{
  "command": "FACILITATION_TOGGLE",
  "enable": true  // or false
}
```

All responses return JSON:
```json
{
  "status": "ok",  // or "error"
  "message": "...",  // if error
  ... // additional response data
}
```
