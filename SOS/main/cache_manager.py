import json
import os
import shutil
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
                 metadata_cache_path=r'\\sos2\AuxShare\Documents\Cache\clip_metadata_cache.JSON',
                 subtitle_cache_dir=r'\\sos2\AuxShare\Documents\Cache\subtitle_cache',
                 dataset_csv_path=r'\\sos2\AuxShare\Documents\Cache\SOS_datasets - Cache.csv'):
        
        self.playlist_cache_file = playlist_cache_path
        self.metadata_cache_file = metadata_cache_path
        self.subtitle_cache_dir = subtitle_cache_dir
        self.dataset_csv_path = dataset_csv_path
        
        self.playlists = []      # Loaded from playlist_cache.JSON
        self.clip_metadata = {}  # Loaded from clip_metadata_cache.JSON
        self.dataset_titles = {} # Loaded from SOS_datasets - Cache.csv
        self.current_playlist = None
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.playlist_cache_file), exist_ok=True)
        os.makedirs(self.subtitle_cache_dir, exist_ok=True)
        
        self.load_caches()
        self.load_titles_csv(self.dataset_csv_path)

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

    def get(self, clip_name, key=None):
        """
        Retrieve metadata for a specific clip name.
        """
        # Look up in the metadata cache dictionary
        metadata = self.clip_metadata.get(clip_name)
        
        if not metadata:
            return {}
            
        if key:
            return metadata.get(key)
            
        return metadata
    
    def is_translated_movie(self, clip_name):
        """
        Check if a clip is marked as a translated movie.
        Returns True if the clip has 'translated-movie' metadata set to True.
        """
        metadata = self.clip_metadata.get(clip_name, {})
        return metadata.get('translated-movie', False)
    
    def fetch_subtitle_file(self, source_path):
        """
        Fetch a subtitle file from source (local copy or SCP) to cache.
        Returns absolute path to cached file.
        """
        if not source_path: return None
        
        filename = os.path.basename(source_path)
        cached_path = os.path.join(self.subtitle_cache_dir, filename)
        
        if os.path.exists(cached_path):
            return cached_path
            
        # Try local copy first (if source is accessible as file)
        try:
             # Normalize separators
             src_norm = os.path.normpath(source_path)
             if os.path.exists(src_norm):
                 shutil.copy2(src_norm, cached_path)
                 print(f"[Cache] Copied local: {filename}")
                 return cached_path
        except Exception: pass
        
        # Try SCP (SOS Server)
        sos_ip = "10.10.51.98" 
        ssh_user = "sos"  # Authenticated user verified by client
        
        found_keys = []
        possible_keys = [
            r"C:\Users\sosdemo\.ssh\id_rsa",
            os.path.expanduser("~/.ssh/id_rsa"),
            os.path.expanduser("~/.ssh/id_ed25519"),
            os.path.expanduser("~/.ssh/id_ecdsa"),
        ]
        
        # Remove duplicates while preserving order
        unique_paths = []
        for p in possible_keys:
            if p not in unique_paths: unique_paths.append(p)
            
        for key_path in unique_paths:
            if os.path.exists(key_path):
                found_keys.append(key_path)
                print(f"[Cache] Found SSH key candidate: {key_path}")
        
        # Attempt 1: Use explicit keys with SCP
        base_scp_cmd = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "PasswordAuthentication=no"]
        cmd1 = list(base_scp_cmd)
        if found_keys:
            for key in found_keys:
                cmd1 += ["-i", key]
        cmd1 += [f"{ssh_user}@{sos_ip}:{source_path}", cached_path]

        try:
            print(f"[Cache] Method 1: SCP with Explicit Keys...")
            result = subprocess.run(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            if result.returncode == 0 and os.path.exists(cached_path):
                print(f"[Cache] Success (RPC).")
                return cached_path
        except Exception: pass

        # Attempt 2: SCP System Default
        print(f"[Cache] Method 2: SCP System Default...")
        cmd2 = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "PasswordAuthentication=no"]
        cmd2 += [f"{ssh_user}@{sos_ip}:{source_path}", cached_path]
        
        try:
            result = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            if result.returncode == 0 and os.path.exists(cached_path):
                print(f"[Cache] Success (System Default).")
                return cached_path
        except Exception: pass
        
        # Attempt 3: SSH Cat (Safe Mode)
        print(f"[Cache] Method 3: SSH 'cat' fallback...")
        ssh_base = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "-o", "PasswordAuthentication=no"]
        if found_keys:
             ssh_base += ["-i", found_keys[0]]
             
        ssh_cmd = ssh_base + [f"{ssh_user}@{sos_ip}", f"cat '{source_path}'"]
        
        try:
            with open(cached_path, 'wb') as f:
                result = subprocess.run(ssh_cmd, stdout=f, stderr=subprocess.PIPE, timeout=5)
                if result.returncode == 0 and os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                    print(f"[Cache] Success (SSH cat safe).")
                    return cached_path
                else:
                    # Cleanup empty file
                    f.close()
                    if os.path.exists(cached_path) and os.path.getsize(cached_path) == 0:
                        os.remove(cached_path)
        except Exception: pass
        
        # Attempt 4: SSH Cat (Bare / Agent Mode)
        print(f"[Cache] Method 4: SSH 'cat' (Agent/Interactive Mode)...")
        ssh_bare = ["ssh", "-o", "StrictHostKeyChecking=no", f"{ssh_user}@{sos_ip}", f"cat '{source_path}'"]
        
        try:
            with open(cached_path, 'wb') as f:
                result = subprocess.run(ssh_bare, stdout=f, stderr=subprocess.PIPE, timeout=5)
                if result.returncode == 0 and os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                    print(f"[Cache] Success (SSH cat agent).")
                    return cached_path
                else:
                    f.close()
                    if os.path.exists(cached_path) and os.path.getsize(cached_path) == 0:
                         os.remove(cached_path)
                    
                    err = result.stderr.decode('utf-8', 'ignore').strip()
                    print(f"[Cache] All fetch methods failed. Last error: {err}")
        except subprocess.TimeoutExpired:
            print("[Cache] Method 4 timed out (likely password prompt). Auth failed.")
        except Exception as e:
            print(f"[Cache] Method 4 failed: {e}")

        return None

    def cache_subtitles(self):
        """
        Iterate through cached metadata and ensure subtitle files are cached.
        For translated movies, automatically fetch both English and Spanish subtitles
        based on naming pattern (e.g., _en.srt and _es.srt).
        """
        print("[Cache] Checking subtitle cache...")
        count = 0
        
        for clip_name, metadata in self.clip_metadata.items():
            # Check if this is a translated movie
            is_translated = self.is_translated_movie(clip_name)
            
            if is_translated and 'caption' in metadata:
                # For translated movies, fetch both English and Spanish subtitles
                caption_path = metadata['caption']
                
                # Fetch the English subtitle (from caption field)
                if self.fetch_subtitle_file(caption_path):
                    count += 1
                    # print(f"[Cache] Fetched English subtitle for: {clip_name}")
                
                # Derive Spanish subtitle path from English path
                # Pattern: replace _en.srt with _es.srt
                if '_en.srt' in caption_path:
                    caption2_path = caption_path.replace('_en.srt', '_es.srt')
                    if self.fetch_subtitle_file(caption2_path):
                        count += 1
                        # print(f"[Cache] Fetched Spanish subtitle for: {clip_name}")
                        # Update metadata to include caption2 path
                        metadata['caption2'] = caption2_path
                elif 'caption2' in metadata:
                    # If caption2 is explicitly defined, use it
                    if self.fetch_subtitle_file(metadata['caption2']):
                        count += 1
                        print(f"[Cache] Fetched secondary subtitle for: {clip_name}")
            else:
                # For non-translated clips, just fetch whatever captions are defined
                for key in ['caption', 'caption2']:
                    if key in metadata:
                        if self.fetch_subtitle_file(metadata[key]):
                            count += 1
        
        if count > 0:
            print(f"[Cache] Cached {count} new subtitle files.")


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
        Includes logic for 'translated-movie'.
        """
        print("[Cache] Fetching full playlist data...")
        
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
            clip_count = None
            for line in lines:
                line = line.strip()
                if line.isdigit():
                    clip_count = int(line)
                    break
            
            if clip_count is None:
                import re
                match = re.search(r'\d+', count_data)
                if match:
                    clip_count = int(match.group())
                else:
                    raise ValueError(f"No numeric value found in response")
                    
        except ValueError:
            print(f"[Cache] Error parsing clip count: {count_data}")
            return

        print(f"[Cache] Found {clip_count} clips. Fetching details...")
        
        new_playlist_clips = []
        
        # 2. Iterate and Fetch Metadata (Pass 1)
        for i in range(1, clip_count + 1):
            # Fetch raw metadata string
            sock.sendall(f'get_all_name_value_pairs {i}\n'.encode())
            meta_raw = recv_till_timeout(sock).decode('utf-8', 'ignore')
            
            # Parse it
            metadata = self.parse_name_value_pairs(meta_raw)
            clip_name = metadata.get('name', f'Unknown_Clip_{i}')
            
            # --- Logic for 'translated-movie' ---
            # Criteria 1: Path indicates 'site-custom' subfolder
            # Check 'filename', 'file', 'datadir', or 'clip_filename'
            full_path = (metadata.get('filename') or 
                         metadata.get('file') or 
                         metadata.get('datadir') or 
                         metadata.get('clip_filename') or 
                         "")
            
            # Normalize slashes for check and lower case
            normalized_path = full_path.replace('\\', '/').lower()
            is_site_custom = '/site-custom/' in normalized_path
            
            # Criteria 2: 'datadir' indicates .mp4 (or fallback to extension check)
            # The prompt says: "their key 'datadir' value indicates the item is an .mp4 file"
            datadir_val = metadata.get('datadir', '').lower()
            is_mp4 = 'mp4' in datadir_val or normalized_path.endswith('.mp4')
            
            # Criteria 3 & 4: Has 'caption' and 'caption2'
            has_captions = 'caption' in metadata and 'caption2' in metadata
            
            # Determine status
            is_translated = is_site_custom and is_mp4 and has_captions
            
            metadata['translated-movie'] = is_translated
            
            # Debug output for translated movie detection
            if 'site-custom' in normalized_path.lower():
                print(f"\n[DEBUG] {clip_name}:")
                print(f"  is_site_custom: {is_site_custom}")
                print(f"  is_mp4: {is_mp4}")
                print(f"  datadir: {metadata.get('datadir', 'N/A')}")
                print(f"  has 'caption': {'caption' in metadata}")
                if 'caption' in metadata:
                    print(f"    caption value: {metadata['caption']}")
                print(f"  has 'caption2': {'caption2' in metadata}")
                if 'caption2' in metadata:
                    print(f"    caption2 value: {metadata['caption2']}")
                print(f"  All metadata keys: {list(metadata.keys())}")
                print(f"  has_captions (both): {has_captions}")
                print(f"  is_translated: {is_translated}")
            
            # Update the Metadata Cache (Global Dictionary)
            self.clip_metadata[clip_name] = metadata
        
            # Update the Playlist Structure (Ordered List)
            new_playlist_clips.append({
                'name': clip_name
            })
            
            print(f"  [{i}/{clip_count}] Processed: {clip_name} (Translated: {is_translated})")


        # 4. Update Playlist Cache Object
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
        
        # 5. Save Everything
        self.save_caches()

    def load_titles_csv(self, csv_path):
        """
        Load Spanish and English titles from the dataset CSV.
        Expected format: Dataset Name (Auto), Spanish Title, English Title, ...
        """
        print(f"[Cache] Attempting to load titles from: {csv_path}")
        if not os.path.exists(csv_path):
            print(f"[Cache] ERROR: Titles CSV not found at {csv_path}")
            return
            
        import csv
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                # Use DictReader to be robust to column order
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # Map columns by name based on the CSV header
                    dataset_name = row.get('Dataset Name (Auto)', '').strip()
                    spanish_title = row.get('Spanish Title', '').strip()
                    english_title = row.get('English Title', '').strip()
                    
                    if dataset_name:
                        self.dataset_titles[dataset_name] = {
                            'spanish': spanish_title,
                            'english': english_title
                        }
                        count += 1
                
                print(f"[Cache] Successfully loaded {count} title entries from CSV.")
                # print(f"[Cache] Current keys: {list(self.dataset_titles.keys())}")
        except Exception as e:
            print(f"[Cache] CRITICAL ERROR reading titles CSV: {e}")
            import traceback
            traceback.print_exc()

    def get_clip_titles(self, clip_name):
        """Return (spanish, english) titles for a clip, or defaults."""
        data = self.dataset_titles.get(clip_name, {})
        # Log the result of the lookup
        # if data:
        #     print(f"[Cache] Found titles for '{clip_name}': {data}")
        # else:
        #     print(f"[Cache] No titles found for '{clip_name}' in dataset_titles ({len(self.dataset_titles)} entries)")
        return data.get('spanish', ""), data.get('english', "")