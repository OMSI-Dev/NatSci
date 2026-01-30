"""
SOS2 Main Controller
Initializes LibreOffice presentation, creates slide mappings, and starts the engine.
Conditionally starts specialized batch engine for Batch1_2026.sos playlist.
"""

import subprocess
import socket
import time
import re
import json
import os
from pp_init import initialize_all
from engine import SimplePPEngine
from batch_engine import Batch1Engine

# Subtitle cache directory
SUBTITLE_CACHE_DIR = r'\\sos2\AuxShare\Documents\subtitle_cache'

def recv_data(sock: socket.socket, timeout_idle: float = 1.0) -> bytes:
    """Receive data from socket until idle timeout."""
    buffer = bytearray()
    orig_timeout = sock.gettimeout()
    try:
        sock.settimeout(0.2)
        start = time.time()
        while True:
            try:
                chunk = sock.recv(4096)
                if chunk:
                    buffer.extend(chunk)
                    start = time.time()
                else:
                    break
            except socket.timeout:
                if time.time() - start >= timeout_idle:
                    break
    finally:
        sock.settimeout(orig_timeout)
    return bytes(buffer)


def fetch_subtitle_file(remote_path, host="10.10.51.98"):
    """
    Fetch subtitle file from SOS server via SCP and cache locally.
    
    Args:
        remote_path: Path to subtitle file on SOS server (e.g., /shared/sos/media/extras/...)
        host: SOS server IP address
        
    Returns:
        str: Local path to cached subtitle file, or None if failed
    """
    if not remote_path:
        return None
    
    # Ensure cache directory exists
    os.makedirs(SUBTITLE_CACHE_DIR, exist_ok=True)
    
    # Generate local filename from remote path
    filename = os.path.basename(remote_path)
    local_path = os.path.join(SUBTITLE_CACHE_DIR, filename)
    
    # Check if already cached
    if os.path.exists(local_path):
        # print(f"  → Subtitle cached: {filename}")
        return local_path
    
    # SSH/SCP fetch logic
    ssh_user = "sosdemo"
    scp_cmd = [
        "scp",
        "-o", "StrictHostKeyChecking=no",
        f"{ssh_user}@{host}:{remote_path}",
        local_path
    ]
    
    print(f"  → Fetching subtitle: {filename}")
    try:
        result = subprocess.run(scp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if result.returncode == 0 and os.path.exists(local_path):
            print(f"    ✓ Downloaded: {filename}")
            return local_path
        else:
            print(f"    ✗ SCP failed: {result.stderr.decode('utf-8', 'ignore')}")
            return None
    except Exception as e:
        print(f"    ✗ Exception during SCP: {e}")
        return None


def initializePlaylist(host: str = "10.10.51.98", port: int = 2468, timeout: float = 4.0):
    """
    Gets playlist name from the SOS server 
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        sock.connect((host, port))
        sock.sendall(b'enable\n')
        recv_data(sock, timeout_idle=1.0)
        
        # Get playlist path : Fetch from SOS server
        sock.sendall(b'get_playlist_name\n')
        data = recv_data(sock, timeout_idle=1.0)
        loaded_playlist_path = data.decode('utf-8', 'ignore').strip()

        # Get paths of all clips in playlist : Fetch from SOS server
        sock.sendall(b'search_clip_list_from_file "" ' + loaded_playlist_path.encode('utf-8') + b'\n')
        data = recv_data(sock, timeout_idle=1.0)
        loaded_playlist_clips = data.decode('utf-8', 'ignore').strip()

        # Check if playlist exists in JSON cache
        try:
            with open(r'\\sos2\AuxShare\Documents\Cache\playlist_cache.JSON', 'r') as json_file:
                file_content = json_file.read().strip()
                
                # Handle empty or invalid JSON file
                if not file_content:
                    print("playlist_cache.JSON is empty. Creating new cache...")
                    raise json.JSONDecodeError("Empty file", "", 0)
                
                playlist_cache = json.loads(file_content)
                
                # Ensure it's a list
                if not isinstance(playlist_cache, list):
                    print("playlist_cache.JSON has invalid format. Recreating cache...")
                    raise json.JSONDecodeError("Invalid format", "", 0)
                
                cached_entry = [pl for pl in playlist_cache if pl['path'] == loaded_playlist_path]
                playlist_exists_in_cache = len(cached_entry) > 0

                if playlist_exists_in_cache:
                    print("[YAY!] Playlist exists in cache.")

                    # Check last modified date
                    command = 'ssh sos@10.10.51.98 "stat -c %y" ' + loaded_playlist_path + '"'
                    try:
                        result = subprocess.check_output(command, shell=True, text=True)
                        modification_date = result.strip().split()[0]

                        if modification_date == cached_entry[0]['last_modified']:
                            print("[YAY!]Playlist last modified date matches cache.")
                            # Return the cached playlist metadata
                            return cached_entry[0]

                        elif modification_date != cached_entry[0]['last_modified']:
                            # Fetch updated data and modify existing entry in cache
                            playlist_metadata = fetch_playlist_data(loaded_playlist_path)
                            index = playlist_cache.index(cached_entry[0])
                            playlist_cache[index] = playlist_metadata
                            with open(r'\\sos2\AuxShare\Documents\Cache\playlist_cache.JSON', 'w') as json_file:
                                json.dump(playlist_cache, json_file, indent=4)
                            print("Playlist cache updated due to last modified date change.")
                            return playlist_metadata
                            
                                            
                    except subprocess.CalledProcessError as e:
                        print(f"Error occurred: {e}")

                else:
                    print("Playlist does not exist in cache.")
                    playlist_metadata = fetch_playlist_data(loaded_playlist_path)
                    playlist_cache.append(playlist_metadata)
                    with open(r'\\sos2\AuxShare\Documents\Cache\playlist_cache.JSON', 'w') as json_file:
                        json.dump(playlist_cache, json_file, indent=4)
                    print("Playlist added to cache as new entry.")
                    return playlist_metadata

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Cache file issue ({type(e).__name__}). Creating new cache...")
            # Create new cache with fetched data
            playlist_metadata = fetch_playlist_data(loaded_playlist_path)
            with open(r'\\sos2\AuxShare\Documents\Cache\playlist_cache.JSON', 'w') as json_file:
                json.dump([playlist_metadata], json_file, indent=4)
            return playlist_metadata
        
        return None 
        
    except OSError as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()


def fetch_playlist_data(playlist_path, host: str = "10.10.51.98", port: int = 2468, timeout: float = 4.0):
    """
    Fetch playlist metadata from SOS server and local CSV.
    Returns dictionary with playlist name, clips (with metadata), path, and last modified date.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    # Initialize playlist metadata dictionary
    playlist_metadata = {
        'name': '',
        'path': playlist_path,
        'clips': [],  # Each clip will be a dict with 'name', 'path', 'spanish_title', 'english_title', 'majorcategory'
        'last_modified': ''
    }

    playlist_metadata['name'] = playlist_path.split('/')[-1]  # Extract playlist name from path

    try:
        sock.connect((host, port))
        sock.sendall(b'enable\n')
        recv_data(sock, timeout_idle=1.0)
        
        # Get clip paths from playlist_read
        sock.sendall(b'playlist_read ' + playlist_path.encode('utf-8') + b'\n')
        data = recv_data(sock, timeout_idle=1.0)
        playlist_read_output = data.decode('utf-8', 'ignore').strip()
        
        clip_paths = []
        for line in playlist_read_output.splitlines():
            line = line.strip()
            if line.startswith('include ='):
                path = line.replace('include =', '').strip()
                clip_paths.append(path)
        
        # Get clip names from get_clip_info *
        sock.sendall(b'get_clip_info *\n')
        data = recv_data(sock, timeout_idle=1.0)
        clip_info_output = data.decode('utf-8', 'ignore').strip()
        
        # Parse fetched numbered list to extract clip names
        clip_names = []
        for line in clip_info_output.splitlines():
            line = line.strip()
            match = re.match(r'^\d+\s+(.+)$', line)
            if match:
                clip_names.append(match.group(1))
        
        # Load additional metadata from CSV (spanish_title, english_title, majorcategory)
        csv_metadata = {}
        csv_path = r'\\sos2\AuxShare\Documents\sos_datasets.csv'
        try:
            import csv
            # Try multiple encodings in order of likelihood
            encodings_to_try = ['utf-8-sig', 'latin-1', 'windows-1252', 'utf-8']
            
            for encoding in encodings_to_try:
                try:
                    with open(csv_path, 'r', encoding=encoding, newline='') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            english_title = row.get('English Title', '').strip()
                            if english_title:
                                csv_metadata[english_title] = {
                                    'spanish_title': row.get('Spanish Title', '').strip(),
                                    'majorcategory': row.get('Major Categories', '').strip()
                                }
                    print(f"CSV loaded successfully with {encoding} encoding")
                    break  # Success, exit the encoding loop
                except UnicodeDecodeError:
                    if encoding == encodings_to_try[-1]:  # Last encoding attempt
                        raise  # Re-raise if all encodings failed
                    continue  # Try next encoding
        except Exception as e:
            print(f"Warning: Could not load CSV metadata: {e}")
        
        # Combine clip data with CSV metadata and fetch clip metadata (including subtitle paths)
        print(f"\nFetching clip metadata and caching subtitles...")
        for i, (name, path) in enumerate(zip(clip_names, clip_paths), 1):
            clip_entry = {
                'name': name,
                'path': path,
                'spanish_title': csv_metadata.get(name, {}).get('spanish_title', ''),
                'english_title': name,  # English title is the clip name
                'majorcategory': csv_metadata.get(name, {}).get('majorcategory', ''),
                'caption': '',  # Will be populated from metadata
                'caption2': ''  # Will be populated from metadata
            }
            
            # Fetch metadata for this clip to get caption paths
            try:
                cmd = f'get_all_name_value_pairs {i}\n'.encode('utf-8')
                sock.sendall(cmd)
                metadata_data = recv_data(sock, timeout_idle=2.0)
                metadata_str = metadata_data.decode('utf-8', 'ignore').strip()
                
                # Parse metadata for caption, caption2, and duration
                for line in metadata_str.splitlines():
                    line = line.strip()
                    if line.startswith('caption '):
                        caption_path = line.replace('caption ', '', 1).strip()
                        clip_entry['caption'] = caption_path
                        # Fetch and cache the subtitle file
                        if caption_path:
                            local_caption = fetch_subtitle_file(caption_path, host)
                            if local_caption:
                                clip_entry['caption_local'] = local_caption
                    elif line.startswith('caption2 '):
                        caption2_path = line.replace('caption2 ', '', 1).strip()
                        clip_entry['caption2'] = caption2_path
                        # Fetch and cache the subtitle file
                        if caption2_path:
                            local_caption2 = fetch_subtitle_file(caption2_path, host)
                            if local_caption2:
                                clip_entry['caption2_local'] = local_caption2
                    elif line.startswith('duration '):
                        duration_str = line.replace('duration ', '', 1).strip()
                        try:
                            clip_entry['duration'] = float(duration_str)
                        except ValueError:
                            pass
                
                if clip_entry['caption'] or clip_entry['caption2']:
                    print(f"  [{i}] {name}")
                    if clip_entry.get('caption_local'):
                        print(f"      EN: {os.path.basename(clip_entry['caption_local'])}")
                    if clip_entry.get('caption2_local'):
                        print(f"      ES: {os.path.basename(clip_entry['caption2_local'])}")
                        
            except Exception as e:
                print(f"  Warning: Could not fetch metadata for clip {i} ({name}): {e}")
            
            playlist_metadata['clips'].append(clip_entry)

    except OSError as e:
        print(f"Error fetching playlist data from SOS: {e}")
    
    finally:
        sock.close()

    # Get last modified date
    try:
        command = 'ssh sos@10.10.51.98 "stat -c %y ' + playlist_path + '"'
        result = subprocess.check_output(command, shell=True, text=True)
        modification_date = result.strip().split()[0]
        playlist_metadata['last_modified'] = modification_date
    except subprocess.CalledProcessError as e:
        print(f"Error getting last modified date: {e}")

    print(f"Fetched playlist metadata: {playlist_metadata['name']} with {len(playlist_metadata['clips'])} clips")
    return playlist_metadata


if __name__ == '__main__':
    print("=" * 60)
    print("SOS2 LibreOffice Impress Controller")
    print("=" * 60)
    
    # print("\nInitializing playlist from SOS server...")
    playlist_metadata = initializePlaylist()
    
    if not playlist_metadata:
        print("\nERROR: Failed to initialize playlist from SOS server")
        print("Exiting...")
        exit(1)
    
    # print(f"Playlist metadata retrieved successfully")
    
    # Get playlist name for conditional engine selection
    playlist_name = playlist_metadata.get('name', '')
    print(f"\nLoaded playlist: {playlist_name}")
    
    # print("\nInitializing presentation and slide mappings...")
    pp, slide_dictionary = initialize_all()
    
    if not pp or not slide_dictionary:
        print("\nERROR: Failed to initialize presentation or slide mappings")
        print("Exiting...")
        exit(1)
    
    # print(f"\nPresentation loaded: {pp.count} slides")
    # print(f"Slide mappings loaded: {len(slide_dictionary)} clips")
    
    # Conditionally start specialized batch engine for Batch1_2026.sos
    if playlist_name == "Batch1_2026.sos":
        print("\n*** BATCH 1 DETECTED: Starting specialized batch engine ***")
        print("=" * 60)
        engine = Batch1Engine(pp, slide_dictionary, playlist_metadata)
    else:
        # Note: SOS connection details (IP, port) are now handled as global variables in engine.py
        print("\nInitializing standard engine...")
        engine = SimplePPEngine(pp, slide_dictionary, playlist_metadata)
    
    print("\nStarting engine...")
    print("=" * 60)
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt detected")
        engine.stop()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        engine.stop()
    
    # Cleanup
    print("\nCleaning up...")
    time.sleep(1)
    pp.close()
    print("Done!")