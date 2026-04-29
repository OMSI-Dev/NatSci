"""
Executes on the B-link device in the SOS network.
Prompts for a metadata type, then retrieves that metadata value for all clips in the playlist.
Returns a list of clip names with their corresponding metadata values.

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


def get_playlist_metadata(metadata_type: str, host: str = "10.10.51.87", port: int = 2468, timeout: float = 4.0):
    """
    Connects to the SOS server and retrieves specified metadata for all clips in the playlist.
    
    Args:
        metadata_type: The metadata field to retrieve (e.g., 'duration', 'caption', 'fps')
        host: IP address of SOS server
        port: Port number of SOS server
        timeout: Connection timeout in seconds
        
    Returns:
        List of tuples: [(clip_name, metadata_value), ...] or None if connection fails
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
        print(f"Retrieving '{metadata_type}' for each clip...\n")
        
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
            
            # Extract the clip name and the requested metadata
            clip_name = clip_info.get('name', f'Unknown_{clip_num}')
            metadata_value = clip_info.get(metadata_type, 'N/A')
            
            results.append((clip_name, metadata_value))
        
        return results
        
    except OSError as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()


if __name__ == '__main__':
    # Prompt user for metadata type
    print("=" * 60)
    print("SOS Playlist Metadata Query Tool")
    print("=" * 60)
    print("\nCommon metadata fields:")
    print("  - name")
    print("  - duration")
    print("  - caption")
    print("  - fps")
    print("  - file")
    print("  - aspect")
    print("  - description")
    print("\nEnter the metadata field you want to query:")
    metadata_type = input("> ").strip()
    
    if not metadata_type:
        print("Error: No metadata type provided")
        exit(1)
    
    print()
    
    # Query the playlist
    results = get_playlist_metadata(metadata_type)
    
    if results:
        print("=" * 60)
        print(f"Results: name → {metadata_type}")
        print("=" * 60)
        
        # Find the longest name for formatting
        max_name_len = max(len(name) for name, _ in results)
        
        for clip_name, metadata_value in results:
            print(f"{clip_name:<{max_name_len}} : {metadata_value}")
        
        print()
        print(f"Total clips: {len(results)}")
    else:
        print("Failed to retrieve playlist metadata")
