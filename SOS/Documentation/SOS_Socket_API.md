# SOS Socket API Documentation

This document references the socket API calls used in `/SOS2/` (latest iteration) and `/main/` (stable version) engines. It details the initialization sequences, command dictionary, and special behaviors for the Science On a Sphere (SOS) automation interface.

## 1. Connection Details

### Science On a Sphere (SOS) Server
*   **Protocol:** TCP
*   **Default IP:** `10.10.51.98`
*   **Default Port:** `2468`
*   **Timeout:** Typically `4.0s` for connection, `1.0s` for data reception.

### Raspberry Pi "Now Playing" Display (Specific to `/main/`)
*   **Protocol:** TCP
*   **Default IP:** `10.10.51.97`
*   **Default Port:** `4096`

---

## 2. Initialization & Handshake

### SOS Connection Handshake
Upon connecting to the SOS server (Port 2468), the client must immediately send an enable command to authorize control.

*   **Command:** `enable\n`
*   **Response:** `R` (indicating "Ready" or success). Note: Some versions may not return a simplified response, but the socket connection remains valid.

### Initialization Sequence (Standard Pattern)
Both engines follow this general sequence during startup (`sdc.py` -> `initializePlaylist`):

1.  **Connect & Handshake:** `enable`
2.  **Identify Playlist:** `get_playlist_name`
3.  **Read Playlist Content:**
    *   **Method A (SOS2):** `playlist_read <path>` followed by parsing `include =` lines.
    *   **Method B (Main):** `get_clip_count` followed by iterating `get_clip_info <index>`.
4.  **Fetch Metadata:** `get_all_name_value_pairs <index>` (used to populate cache/clip properties like subtitles).

---

## 3. SOS Command Reference

All commands are strings terminated by a newline (`\n`).

### Playback Control
| Command | Description | Context / Usage |
| :--- | :--- | :--- |
| `play <number>` | Plays specific clip index (1-based). | Used in Batch Engine for movieset transitions. |
| `next_clip` | Skips to the next clip in the playlist. | Standard navigation. |
| `prev_clip` | Skips to the previous clip. | Standard navigation. |
| `set_auto_presentation_mode <0\|1>` | Toggles auto-advance. `0`=Off, `1`=On. | Used in Batch Engine to pause autoplay during credits (`0`) and resume (`1`). |

### State & Information
| Command | Description | Response Example |
| :--- | :--- | :--- |
| `get_playlist_name` | Returns absolute path of current playlist. | `/shared/sos/media/playlists/default.sos` |
| `get_clip_number` | Returns index of currently playing clip. | `1` |
| `get_clip_info <number>` | Returns name of clip at index. | `1,Earth_Blue_Marble` |
| `get_clip_info *` | Returns list of all clips (one per line). | `1 Earth` \n `2 Mars` ... |
| `get_clip_count` | Returns total number of clips in playlist. | `12` |
| `get_frame_number` | Returns current playback frame. | `1050` |
| `get_frame_rate` | Returns FPS of current clip. | `30.0` |

### Metadata & Datasets
| Command | Description | Notes |
| :--- | :--- | :--- |
| `start_transmission` | **Deprecated/Internal.** | |
| `search_clip_list_from_file "" <path>`| Lists clips in a playlist file. | `SOS2` specific usage. |
| `playlist_read <path>` | Dumps playlist file content. | Used to find clip paths (`include = ...`). |
| `get_all_name_value_pairs <n>` | **CRITICAL.** Returns all metadata for clip `n`. | Returns key-value pairs like `duration`, `caption` (subtitle path), `caption2` (secondary subtitle), `timer`. |

### Visual Effects (Batch Engine Specific)
| Command | Description | Usage |
| :--- | :--- | :--- |
| `fadeout <seconds>` | Fades the sphere to black over `n` seconds. | Used before transitioning to moviesets. |
| `fadein <seconds>` | Fades the sphere in from black. | Used after credits display. |

---

## 4. Raspberry Pi Interface (`/main/` only)
The `main` engine communicates with a secondary display (Raspberry Pi) for "Now Playing" information.

| Message Format | Description |
| :--- | :--- |
| `NOW_PLAYING:<clip_name>\n` | Updates the "Now Playing" text. |
| `CLIP:<clip_name>\n` | Redundant alias for above. |
| `PLAYLIST:<name1>,<name2>...\n` | Sends full playlist as CSV string. |
| `INIT:<message>\n` | Connection test/handshake message. |

---

## 5. Important Contextual Notes

1.  **Subtitle Handling:**
    *   The engine discovers subtitles by parsing `caption` and `caption2` fields from `get_all_name_value_pairs`.
    *   Files are usually fetched via **SCP/SSH** (`scp sosdemo@10.10.51.98:/path/to/file`) and cached locally in `subtitle_cache/`.

2.  **Batch1 Specialized Behavior (`SOS2/batch_engine.py`):**
    *   This is a highly specialized engine for a specific playlist (`Batch1_2026.sos`).
    *   It overrides normal behavior for clips 1 and 6 (Moviesets).
    *   **Workflow:** Fadeout -> Move Slide (Credits) -> Wait -> Fadein -> Play Clip -> Move Slide (Subtitles) -> Spawn Overlays.

3.  **Engine Differences:**
    *   **Main:** Uses PyQt5 for overlays (Progress Bar, Subtitles) directly integrated. Communicates with Pi.
    *   **SOS2:** Modularized. Separates `SimplePPEngine` and `Batch1Engine`. Uses `subprocess` for some checks. Heavily relied on `playlist_cache.JSON`.

4.  **Socket Robustness:**
    *   Both engines implement a `recv_data` helper that handles `socket.timeout` (default ~1.0s idle timeout) to buffer disparate chunks.
    *   `socket.shutdown(SHUT_RDWR)` is used in cleanup to prevent hanging ports.
