"""
Executes on the B-link device in the SOS network.
Retrieves complete metadata for all clips in the current playlist.
Combines functionality of test_connect (getting all metadata) with query_metadata (iterating through playlist).

IMPORTANT: The SOS app must be running with a playlist loaded for this to work.
"""

import socket
import time
import re


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


def parse_name_value_pairs(data: str) -> dict:
    """
    Parse SOS name-value pair output into a dictionary.
    Handles values in curly braces {like this} and regular values.
    """
    result = {}
    # Pattern to match: key followed by either {value} or regular value
    pattern = r'(\w+)\s+(?:\{([^}]+)\}|(\S+))'
    
    matches = re.findall(pattern, data)
    for match in matches:
        key = match[0]
        value = match[1] if match[1] else match[2]
        result[key] = value
    
    return result


def get_all_playlist_metadata(host: str = "10.10.51.98", port: int = 2468, timeout: float = 4.0):
    """
    Connects to the SOS server and retrieves all metadata for all clips in the playlist.
    
    Args:
        host: IP address of SOS server
        port: Port number of SOS server
        timeout: Connection timeout in seconds
        
    Returns:
        List of dicts: [{clip_number, name, metadata...}, ...] or None if connection fails
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        # Connect
        print(f"Connecting to SOS at {host}:{port}...")
        sock.connect((host, port))
        
        # Handshake
        sock.sendall(b'enable\n')
        recv_data(sock, timeout_idle=1.0)
        print("Connected successfully.\n")
        
        # Get clip count
        sock.sendall(b'get_clip_count\n')
        data = recv_data(sock, timeout_idle=1.0)
        clip_count_str = data.decode('utf-8', 'ignore').strip()
        
        try:
            clip_count = int(clip_count_str)
        except ValueError:
            print(f"Error: Could not determine clip count. Received: '{clip_count_str}'")
            return None
        
        if clip_count <= 0:
            print("Error: No clips in playlist")
            return None
        
        print(f"Found {clip_count} clips in playlist.")
        print("Retrieving complete metadata for each clip...\n")
        
        results = []
        
        # Iterate through all clips in the playlist (clips are numbered starting from 1)
        for clip_num in range(1, clip_count + 1):
            # Get all name-value pairs for this clip
            command = f'get_all_name_value_pairs {clip_num}\n'.encode('utf-8')
            sock.sendall(command)
            data = recv_data(sock, timeout_idle=1.0)
            clip_data = data.decode('utf-8', 'ignore').strip()
            
            # Parse the data into a dictionary
            clip_info = parse_name_value_pairs(clip_data)
            clip_info['clip_number'] = str(clip_num)
            
            results.append(clip_info)
        
        return results
        
    except OSError as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()


def display_playlist_metadata(playlist_data, display_mode='compact'):
    """
    Display playlist metadata in various formats.
    
    Args:
        playlist_data: List of clip metadata dictionaries
        display_mode: 'compact', 'detailed', or 'csv'
    """
    if not playlist_data:
        print("No data to display")
        return
    
    if display_mode == 'csv':
        # CSV format - good for importing into spreadsheet
        print("\n" + "=" * 80)
        print("CSV Format (copy to spreadsheet)")
        print("=" * 80)
        
        # Collect all possible keys across all clips
        all_keys = set()
        for clip in playlist_data:
            all_keys.update(clip.keys())
        
        # Sort keys, but keep clip_number and name first
        priority_keys = ['clip_number', 'name']
        other_keys = sorted([k for k in all_keys if k not in priority_keys])
        ordered_keys = priority_keys + other_keys
        
        # Print header
        print(','.join(ordered_keys))
        
        # Print each clip
        for clip in playlist_data:
            values = [clip.get(key, '') for key in ordered_keys]
            # Escape values with commas
            escaped_values = [f'"{v}"' if ',' in str(v) else str(v) for v in values]
            print(','.join(escaped_values))
    
    elif display_mode == 'compact':
        # Compact format - one line per clip showing key metadata
        print("\n" + "=" * 80)
        print("Playlist Metadata - Compact View")
        print("=" * 80)
        
        # Define which fields to show in compact mode
        compact_fields = ['name', 'duration', 'timer', 'caption', 'fps', 'data']
        
        for clip in playlist_data:
            clip_num = clip.get('clip_number', '?')
            clip_name = clip.get('name', 'Unknown')
            
            print(f"\n[Clip {clip_num}] {clip_name}")
            print("-" * 60)
            
            for field in compact_fields:
                if field in clip:
                    value = clip[field]
                    print(f"  {field:15s}: {value}")
    
    elif display_mode == 'detailed':
        # Detailed format - all metadata for each clip
        print("\n" + "=" * 80)
        print("Playlist Metadata - Detailed View")
        print("=" * 80)
        
        for clip in playlist_data:
            clip_num = clip.get('clip_number', '?')
            clip_name = clip.get('name', 'Unknown')
            
            print(f"\n{'=' * 80}")
            print(f"Clip {clip_num}: {clip_name}")
            print('=' * 80)
            
            # Sort keys alphabetically, but keep name first
            keys = sorted(clip.keys())
            if 'name' in keys:
                keys.remove('name')
                keys.insert(0, 'name')
            if 'clip_number' in keys:
                keys.remove('clip_number')
            
            for key in keys:
                value = clip[key]
                print(f"  {key:20s}: {value}")
    
    print("\n" + "=" * 80)
    print(f"Total clips: {len(playlist_data)}")
    print("=" * 80)


if __name__ == '__main__':
    print("=" * 80)
    print("SOS Playlist Complete Metadata Tool")
    print("=" * 80)
    print("\nDisplay mode options:")
    print("  [1] Compact  - Key metadata fields only")
    print("  [2] Detailed - All metadata fields")
    print("  [3] CSV      - Comma-separated for spreadsheet import")
    print("\nEnter display mode (1/2/3) or press Enter for compact:")
    
    mode_input = input("> ").strip()
    
    mode_map = {
        '1': 'compact',
        '2': 'detailed',
        '3': 'csv',
        '': 'compact'  # default
    }
    
    display_mode = mode_map.get(mode_input, 'compact')
    
    print()
    
    # Query the playlist
    playlist_data = get_all_playlist_metadata()
    
    if playlist_data:
        display_playlist_metadata(playlist_data, display_mode)
    else:
        print("Failed to retrieve playlist metadata")
