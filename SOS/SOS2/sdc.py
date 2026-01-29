"""
SOS2 Main Controller
Initializes LibreOffice presentation, creates slide mappings, and starts the engine.
"""

import subprocess
import socket
import time
import re
import json 
from pp_init import initialize_all
from engine import SimplePPEngine

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
                    print("Playlist exists in cache.")

                    # Check last modified date
                    command = 'ssh sos@10.10.51.98 "stat -c %y" ' + loaded_playlist_path + '"'
                    try:
                        result = subprocess.check_output(command, shell=True, text=True)
                        modification_date = result.strip().split()[0]

                        if modification_date == cached_entry[0]['last_modified']:
                            print("Playlist last modified date matches cache.")
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
        csv_path = r'\\sos2\AuxShare\Documents\sos_datasetss.csv'
        try:
            import csv
            with open(csv_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    english_title = row.get('English Title', '').strip()
                    if english_title:
                        csv_metadata[english_title] = {
                            'spanish_title': row.get('Spanish Title', '').strip(),
                            'majorcategory': row.get('Major Categories', '').strip()
                        }
        except Exception as e:
            print(f"Warning: Could not load CSV metadata: {e}")
        
        # Combine clip data with CSV metadata
        for name, path in zip(clip_names, clip_paths):
            clip_entry = {
                'name': name,
                'path': path,
                'spanish_title': csv_metadata.get(name, {}).get('spanish_title', ''),
                'english_title': name,  # English title is the clip name
                'majorcategory': csv_metadata.get(name, {}).get('majorcategory', '')
            }
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
    
    # Step 1: Initialize playlist from SOS server (checks cache, fetches if needed)
    print("\nInitializing playlist from SOS server...")
    playlist_metadata = initializePlaylist()
    
    if not playlist_metadata:
        print("\nERROR: Failed to initialize playlist from SOS server")
        print("Exiting...")
        exit(1)
    
    print(f"Playlist metadata retrieved successfully")
    
    # Step 2: Initialize LibreOffice presentation and slide dictionary
    print("\nInitializing presentation and slide mappings...")
    pp, slide_dictionary = initialize_all()
    
    if not pp or not slide_dictionary:
        print("\nERROR: Failed to initialize presentation or slide mappings")
        print("Exiting...")
        exit(1)
    
    print(f"\nPresentation loaded: {pp.count} slides")
    print(f"Slide mappings loaded: {len(slide_dictionary)} clips")
    
    # Step 3: Initialize and start the engine with playlist metadata
    # Note: SOS connection details (IP, port) are now handled as global variables in engine.py
    print("\nInitializing engine...")
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
