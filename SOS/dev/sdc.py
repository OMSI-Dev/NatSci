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

def initialize_cache_and_playlist():
    """
    Connects to SOS to get the current playlist name,
    then initializes the CacheManager and syncs if necessary.
    """
    host = "10.10.51.98"
    port = 2468
    
    print("Connecting to SOS for initialization...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(4.0)
    
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
        
        return cm
        
    except Exception as e:
        print(f"Error during initialization: {e}")
        return None
    finally:
        sock.close()

if __name__ == '__main__':
    print("=" * 60)
    print("SOS2 Controller (/dev/)")
    print("=" * 60)
    
    # 1. Initialize Cache
    # This replaces the complex 'initializePlaylist' function in old sdc.py
    cache_mgr = initialize_cache_and_playlist()
    
    if not cache_mgr or not cache_mgr.current_playlist:
        print("\nERROR: Failed to initialize cache or get playlist.")
        # Fallback rationale: If cache fails, we can't map clip numbers to names efficiently.
        # We could implement a fallback to old 'query every time' method, but 
        # for this optimization/dev script, we'll exit.
        input("Press Enter to exit...")
        sys.exit(1)
        
    # 2. Initialize LibreOffice (Reusing SOS2 logic)
    print("\nInitializing LibreOffice...")
    pp, slide_dictionary = initialize_all()
    
    if not pp or not slide_dictionary:
        print("\nERROR: Failed to initialize presentation.")
        sys.exit(1)
        
    # 3. Start Engine
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
