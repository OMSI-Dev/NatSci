import json
import os
import time
import socket
import subprocess
import re
from datetime import datetime

class CacheManager:
    """
    Manages SOS playlist and clip metadata caching to minimize server probing.
    
    Principles:
    1. Single Source of Truth: The cache files are the primary data source during runtime.
    2. Split Architecture: 
       - playlist_cache.JSON: Stores playlist structure (ordered list of clips).
       - clip_metadata_cache.JSON: Stores detailed metadata (duration, captions) for each clip.
    3. Smart Sync: Only fetch from server if playlist modification date has changed.
    """
    
    def __init__(self, 
                 playlist_cache_path=r'\\sos2\AuxShare\Documents\Cache\playlist_cache.JSON', 
                 metadata_cache_path=r'\\sos2\AuxShare\Documents\Cache\clip_metadata_cache.JSON'):
        
        self.playlist_cache_file = playlist_cache_path
        self.metadata_cache_file = metadata_cache_path
        
        self.playlists = []      # Loaded from playlist_cache.JSON
        self.clip_metadata = {}  # Loaded from clip_metadata_cache.JSON
        self.current_playlist = None
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.playlist_cache_file), exist_ok=True)
        self.load_caches()

    def load_caches(self):
        """Load both JSON caches from disk."""
        # Load Playlists
        if os.path.exists(self.playlist_cache_file):
            try:
                with open(self.playlist_cache_file, 'r', encoding='utf-8') as f:
                    self.playlists = json.load(f)
                # print(f"[Cache] Loaded {len(self.playlists)} playlists from disk.")
            except Exception as e:
                print(f"[Cache] Error loading playlist cache: {e}")
                self.playlists = []
        else:
            self.playlists = []

        # Load Metadata
        if os.path.exists(self.metadata_cache_file):
            try:
                with open(self.metadata_cache_file, 'r', encoding='utf-8') as f:
                    self.clip_metadata = json.load(f)
                # print(f"[Cache] Loaded metadata for {len(self.clip_metadata)} clips.")
            except Exception as e:
                print(f"[Cache] Error loading metadata cache: {e}")
                self.clip_metadata = {}
        else:
            self.clip_metadata = {}

    def save_caches(self):
        """Save in-memory data to disk."""
        try:
            with open(self.playlist_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, indent=4)
                
            with open(self.metadata_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.clip_metadata, f, indent=4)
                
            print("[Cache] All caches saved successfully.")
        except Exception as e:
            print(f"[Cache] Error saving caches: {e}")

    def parse_name_value_pairs(self, data: str) -> dict:
        """
        Parse SOS name-value pair output into a dictionary.
        Logic adapted from 3_sos-query_metadata.py.
        """
        result = {}
        # Pattern matches: key followed by {value} OR regular_value
        pattern = r'(\w+)\s+(?:\{([^}]+)\}|(\S+))'
        
        for match in re.findall(pattern, data):
            key = match[0]
            # match[1] is content inside {}, match[2] is bare value
            value = match[1] if match[1] else match[2]
            result[key] = value
        
        return result

    def get_server_modification_date(self, playlist_path, host="10.10.51.98"):
        """Get the last modified date of the playlist file on the SOS server via SSH."""
        try:
            command = f'ssh sos@{host} "stat -c %y \\"{playlist_path}\\""'
            result = subprocess.check_output(command, shell=True, text=True)
            return result.strip().split()[0]
        except subprocess.CalledProcessError as e:
            print(f"[Cache] SSH check failed: {e}")
            return None

    def get_metadata(self, clip_name, key=None):
        """
        Retrieve metadata for a specific clip name.
        """
        # Look up in the metadata cache dictionary
        metadata = self.clip_metadata.get(clip_name)
        
        if not metadata:
            return None
            
        if key:
            return metadata.get(key)
        return metadata

    def sync(self, socket_connection, current_playlist_path):
        """
        Synchronize local caches with SOS server.
        """
        # print(f"[Cache] Syncing for playlist: {current_playlist_path}")
        
        # 1. Check Playlist Cache Status
        cached_playlist = next((p for p in self.playlists if p['path'] == current_playlist_path), None)
        server_mod_date = self.get_server_modification_date(current_playlist_path)
        
        needs_update = False
        if not cached_playlist:
            print("[Cache] Playlist not found locally. Full fetch required.")
            needs_update = True
        elif server_mod_date and cached_playlist.get('last_modified') != server_mod_date:
            print(f"[Cache] Playlist stale ({cached_playlist.get('last_modified')} != {server_mod_date}). Updating...")
            needs_update = True
        else:
            print("[Cache] Playlist structure matches server. Using cache.")
            self.current_playlist = cached_playlist
            return

        if needs_update:
            # Force SOS to reload the modified playlist
            print(f"[Cache] Reloading playlist on SOS: {current_playlist_path}")
            socket_connection.sendall(f'open_playlist {current_playlist_path}\n'.encode())
            time.sleep(2.0) # Allow time for SOS to load the file
            
            self.fetch_and_update_full_data(socket_connection, current_playlist_path, server_mod_date)

    def fetch_and_update_full_data(self, sock, playlist_path, mod_date):
        """
        Fetch all data from SOS and update both caches.
        """
        # print("[Cache] Fetching full playlist data...")
        
        # Helper for socket recv
        def recv_till_timeout(s, timeout=1.0):
            s.settimeout(0.2)
            total_data = b""
            start = time.time()
            while True:
                try:
                    chunk = s.recv(4096)
                    if chunk: 
                        total_data += chunk
                        start = time.time()
                    else: break
                except socket.timeout:
                    if time.time() - start > timeout: break
            return total_data

        # 1. Get Clip Count
        sock.sendall(b'get_clip_count\n')
        count_data = recv_till_timeout(sock).decode('utf-8', 'ignore').strip()
        try:
            # Extract just the numeric part in case response has prefix like "R\n8"
            lines = count_data.split('\n')
            # Try each line until we find a valid integer
            clip_count = None
            for line in lines:
                line = line.strip()
                if line.isdigit():
                    clip_count = int(line)
                    break
            
            if clip_count is None:
                # Fallback: try to extract any digits from the response
                import re
                match = re.search(r'\d+', count_data)
                if match:
                    clip_count = int(match.group())
                else:
                    raise ValueError(f"No numeric value found in response")
                    
        except ValueError as e:
            print(f"[Cache] Error parsing clip count: {count_data}")
            return

        # print(f"[Cache] Found {clip_count} clips. Fetching details...")        
        new_playlist_clips = []
        
        # 2. Iterate and Fetch Metadata
        for i in range(1, clip_count + 1):
            # Fetch raw metadata string
            sock.sendall(f'get_all_name_value_pairs {i}\n'.encode())
            meta_raw = recv_till_timeout(sock).decode('utf-8', 'ignore')
            
            # Parse it
            metadata = self.parse_name_value_pairs(meta_raw)
            clip_name = metadata.get('name', f'Unknown_Clip_{i}')
            
            # Update the Metadata Cache (Global Dictionary)
            # Use 'name' as key. This overwrites old entries for the same clip name, which is desired.
            self.clip_metadata[clip_name] = metadata
        
            # Update the Playlist Structure (Ordered List)
            new_playlist_clips.append({
                'name': clip_name
            })
            
            # print(f"  [{i}/{clip_count}] Processed: {clip_name}")

        # 3. Update Playlist Cache Object
        new_playlist_entry = {
            'name': os.path.basename(playlist_path),
            'path': playlist_path,
            'last_modified': mod_date,
            'clips': new_playlist_clips
        }
        
        # Remove old entry if exists
        self.playlists = [p for p in self.playlists if p['path'] != playlist_path]
        self.playlists.append(new_playlist_entry)
        self.current_playlist = new_playlist_entry
        
        # 4. Save Everything
        self.save_caches()
