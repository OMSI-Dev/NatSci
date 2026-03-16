"""
SOS2 Main Controller (Optimized /dev/ version)
Initializes CacheManager, synchronizes with SOS, and launches LibreOffice Engine.
"""

import sys
import os
import socket
import time

from cache_manager import CacheManager
from engine import SimplePPEngine
from pp_init import initialize_all
from audio_init import initialize_audio
from config import get_config
from config.constants import *

# Load configuration
config = get_config()

# Get configuration values
PI_IP = config.get('pi.ip', '10.10.51.111')
PI_PORT = config.get('pi.port', 4096)
NOWPLAYING_ENABLED = config.get('pi.enabled', False)

def initialize_cache_and_playlist():
    """
    Connects to SOS to get the current playlist name,
    then initializes the CacheManager and syncs if necessary.
    """
    # Use configuration for SOS connection
    host = config.get('sos.ip', '10.0.0.16')
    port = config.get('sos.port', 2468)
    
    print("Connecting to SOS for initialization...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(SOS_SOCKET_TIMEOUT)  # Use constant from config
    
    try:
        sock.connect((host, port))
        sock.sendall(b'enable\n')
        sock.recv(1024) # Handshake response
        
        # Get Playlist Name
        sock.sendall(b'get_playlist_name\n')
        # Use simple recv since we expect a short string
        data = sock.recv(4096) 
        playlist_path = data.decode('utf-8', 'ignore').strip()
        print(f"Current Playlist: {playlist_path}")
        
        # Initialize Cache Manager
        cm = CacheManager()
        
        # Sync Cache (This handles the "Once a day" logic)
        # Checks last modified date and updates cache only if needed
        cm.sync(sock, playlist_path)
        
        # Cache Subtitles
        cm.cache_subtitles()
        
        return cm
        
    except Exception as e:
        print(f"Error during initialization: {e}")
        return None
    finally:
        sock.close()

def initialize_nowplaying(cache_mgr: CacheManager) -> None:
    """Send the current playlist metadata to nowPlaying on the Pi."""
    if not cache_mgr or not cache_mgr.current_playlist:
        print("[nowPlaying] No current playlist available.")
        return

    clips = cache_mgr.current_playlist.get('clips', [])
    lines = ["INIT"]

    for index, clip in enumerate(clips, start=1):
        clip_name = clip.get('name', '')
        spanish_title, english_title = cache_mgr.get_clip_titles(clip_name)
        if not english_title:
            english_title = clip_name
        if not spanish_title:
            spanish_title = clip_name

        metadata = cache_mgr.get(clip_name)
        duration = metadata.get('duration') if isinstance(metadata, dict) else None
        if not duration and isinstance(metadata, dict):
            duration = metadata.get('timer')
        if not duration:
            duration = 90

        lines.append(f"{index}|{english_title}|{spanish_title}|{duration}")

    payload = "\n".join(lines) + "\n"

    try:
        pi_sock = socket.create_connection((PI_IP, PI_PORT), timeout=PI_QUERY_TIMEOUT)
        pi_sock.sendall(payload.encode('utf-8'))
        pi_sock.shutdown(socket.SHUT_WR)  # Signal end of data
        
        # Wait for ACK
        ack = pi_sock.recv(1024)
        pi_sock.close()
        
        print(f"[nowPlaying] Sent {len(clips)} playlist items to Pi.")
    except Exception as e:
        print(f"[nowPlaying] Failed to send playlist: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("SOS2 Controller (/dev/)")
    print("=" * 60)
    
    # Print configuration summary
    print("\nConfiguration:")
    print(f"  SOS Server:     {config.get('sos.ip')}:{config.get('sos.port')}")
    print(f"  Base Share:     {config.get('paths.base_share')}")
    print(f"  Now Playing:    {'Enabled' if NOWPLAYING_ENABLED else 'Disabled'} ({PI_IP}:{PI_PORT})")
    print(f"  Audio:          {'Enabled' if config.get('features.audio_enabled', True) else 'Disabled'}")
    print()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors detected:")
        for error in errors:
            print(f"  ERROR: {error}")
        print("\nPlease fix configuration issues before continuing.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # 1. Initialize Cache
    cache_mgr = initialize_cache_and_playlist()
    
    if not cache_mgr or not cache_mgr.current_playlist:
        print("\nERROR: Failed to initialize cache or get playlist.")
        input("Press Enter to exit...")
        sys.exit(1)
        
    # 2. Initialize LibreOffice (Reusing SOS2 logic)
    print("\nInitializing LibreOffice...")
    pp, slide_dictionary = initialize_all()
    
    if not pp or not slide_dictionary:
        print("\nERROR: Failed to initialize presentation.")
        sys.exit(1)
    
    # 3. Initialize Audio System
    print("\nInitializing Audio System...")
    audio_dict, audio_controller = initialize_audio()
    
    if not audio_dict or not audio_controller:
        print("\nWARNING: Audio system failed to initialize. Continuing without audio.")
        audio_dict = None
        audio_controller = None
    else:
        # Only sync audio config if CSV has been modified
        if cache_mgr.needs_audio_sync():
            print("[Audio] Syncing audio configuration...")
            for category, filenames in audio_dict.items():
                cache_mgr.initialize_audio_category(category, filenames)
            cache_mgr.finalize_audio_sync()
            print(f"[Audio] Registered {len(audio_dict)} audio categories")
        else:
            print("[Audio] Audio config up to date, using cache")
        
    # 4. Initialize nowPlaying
    if NOWPLAYING_ENABLED:
        print("\nInitializing nowPlaying...")
        initialize_nowplaying(cache_mgr)
    else:
        print("\n[nowPlaying] Disabled (NOWPLAYING_ENABLED=False) - skipping init")

    # 5. Start Engine
    print("\nStarting Optimized Engine...")
    print("=" * 60)
    
    engine = SimplePPEngine(pp, slide_dictionary, cache_mgr, audio_controller,
                             nowplaying_enabled=NOWPLAYING_ENABLED)
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\n[SDC] Interrupted.")
    except Exception as e:
        print(f"[SDC] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n[SDC] Cleaning up...")
        
        # Close LibreOffice — engine._cleanup() handles this on normal exit;
        # this guard catches any path where the engine did not run or crashed before cleanup.
        try:
            if pp and hasattr(pp, 'launched') and pp.launched:
                pp.close()
                print("[SDC] LibreOffice closed.")
        except Exception as e:
            print(f"[SDC] Error closing LibreOffice: {e}")

        # Close audio / MPV — engine._cleanup() calls close() on normal interrupt;
        # this ensures MPV is killed if the engine never started or exited abnormally.
        try:
            if audio_controller and hasattr(audio_controller, 'is_initialized') and audio_controller.is_initialized:
                audio_controller.close()
                print("[SDC] Audio controller closed.")
        except Exception as e:
            print(f"[SDC] Error closing audio: {e}")
        
        print("[SDC] Done.")
