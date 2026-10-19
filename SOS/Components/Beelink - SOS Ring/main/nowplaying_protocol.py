"""
Beelink -> Pi nowPlaying wire protocol (single source of truth for message building).

Both the startup push (sdc.py) and the Pi's REQUEST_STATE pull (engine.py) MUST build
the playlist through build_init_message() so the Pi shows the same menu either way.

Messages (newline-delimited, one or more per TCP connection):
    INIT <digest> <count>      header, followed by <count> lines of
    <n>|<english>|<spanish>|<duration_seconds>
    CLIP:<n>                   current clip number
    PAUSE / UNPAUSE            facilitation state
    STATE <digest> <clip|-> <0|1>   heartbeat: playlist digest, current clip, paused flag
    STATUS                     (Pi only) returns a JSON diagnostic line
"""

import hashlib
import re

_FIELD_UNSAFE = re.compile(r'[\r\n|]+')


def clean_field(value) -> str:
    """Make a value safe for the pipe/newline delimited format."""
    if value is None:
        return ""
    return _FIELD_UNSAFE.sub(' ', str(value)).strip()


def _duration_seconds(metadata) -> int:
    """Duration in whole seconds, or 0 when unknown (the Pi owns the display default)."""
    if not isinstance(metadata, dict):
        return 0
    for key in ('duration', 'timer'):
        try:
            seconds = int(round(float(metadata.get(key))))
        except (TypeError, ValueError):
            continue
        if seconds > 0:
            return seconds
    return 0


def build_entries(cache_mgr) -> list:
    """Return the '<n>|<english>|<spanish>|<seconds>' lines for the current playlist."""
    playlist = getattr(cache_mgr, 'current_playlist', None) or {}
    entries = []
    for index, clip in enumerate(playlist.get('clips', []), start=1):
        name = clip.get('name', '')
        spanish, english = cache_mgr.get_clip_titles(name)
        metadata = cache_mgr.get(name)
        if not isinstance(metadata, dict):
            metadata = {}
        english = clean_field(english or metadata.get('movie-title') or name)
        spanish = clean_field(spanish or metadata.get('spanish-translation') or name)
        entries.append(f"{index}|{english}|{spanish}|{_duration_seconds(metadata)}")
    return entries


def entries_digest(entries) -> str:
    return hashlib.sha1("\n".join(entries).encode('utf-8')).hexdigest()[:8]


def build_init_message(cache_mgr):
    """Return (message, digest, count) for the current playlist."""
    entries = build_entries(cache_mgr)
    digest = entries_digest(entries)
    message = "\n".join([f"INIT {digest} {len(entries)}"] + entries) + "\n"
    return message, digest, len(entries)


def build_state_line(digest: str, clip_number, paused: bool) -> str:
    clip = '-' if clip_number is None else str(int(clip_number))
    return f"STATE {digest} {clip} {1 if paused else 0}\n"
