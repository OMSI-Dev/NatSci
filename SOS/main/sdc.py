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

PI_IP = "10.10.51.111"
PI_PORT = 4096

def initialize_cache_and_playlist():
    """
    Connects to SOS to get the current playlist name,
    then initializes the CacheManager and syncs if necessary.
    """
    host = "10.10.51.98"
    port = 2468
    
    print("Connecting to SOS for initialization...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(8.0)
    
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
        with socket.create_connection((PI_IP, PI_PORT), timeout=3.0) as pi_sock:
            pi_sock.sendall(payload.encode('utf-8'))
        print(f"[nowPlaying] Sent {len(clips)} playlist items to Pi.")
    except Exception as e:
        print(f"[nowPlaying] Failed to send playlist: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("SOS2 Controller (/dev/)")
    print("=" * 60)
    
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
        
    # 3. Initialize nowPlaying
    print("\nInitializing nowPlaying...")
    initialize_nowplaying(cache_mgr)

    # 4. Start Engine
    print("\nStarting Optimized Engine...")
    print("=" * 60)
    
    engine = SimplePPEngine(pp, slide_dictionary, cache_mgr)
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print("Interrupted.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pp.close()
        print("Done.")
