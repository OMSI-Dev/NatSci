import subprocess
import os
import csv
import socket
import time
import re
from datetime import datetime, timedelta


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


def connect_to_sos(host: str = "10.10.51.87", port: int = 9750, timeout: int = 4):
    """
    Connect to the SOS server and send enable handshake.
    
    Args:
        host: SOS server IP address
        port: SOS server port
        timeout: Socket timeout in seconds
        
    Returns:
        socket.socket or None: Connected socket if successful, None otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        print(f"Connecting to SOS at {host}:{port}...")
        sock.connect((host, port))
        print("[Success] Connected to SOS server")
        
        # Send enable handshake
        sock.sendall(b'enable\n')
        
        # Wait for response
        data = sock.recv(1024)
        response = data.decode('utf-8', 'ignore').strip()
        
        if response == 'R':
            print("[Success] SOS Handshake successful")
            return sock
        else:
            print(f"⚠ Unexpected handshake response: {response}")
            # Continue anyway - some SOS versions respond differently
            return sock
            
    except socket.timeout:
        print(f"✗ Connection timeout to SOS server")
        return None
    except socket.error as e:
        print(f"✗ Failed to connect to SOS: {e}")
        return None
    except Exception as e:
        print(f"✗ Error during SOS connection: {e}")
        return None


def fetch_dataset_metadata_by_name(sock: socket.socket, dataset_name: str) -> dict:
    """
    Fetch metadata for a dataset by name using SOS filesystem query.
    Uses 'get_name_value_pairs_for_item' command which queries the filesystem.
    
    Args:
        sock: Connected socket to SOS server
        dataset_name: The name of the dataset to fetch metadata for
        
    Returns:
        dict: Parsed metadata dictionary, or empty dict on failure
    """
    if not sock:
        return {}
    
    try:
        # Query SOS for metadata of a specific dataset by name
        # This queries the filesystem, not the current playlist
        command = f'get_name_value_pairs_for_item {dataset_name}\n'.encode('utf-8')
        sock.sendall(command)
        data = recv_data(sock, timeout_idle=1.0)
        metadata_str = data.decode('utf-8', 'ignore').strip()
        
        if not metadata_str:
            return {}
        
        # Parse the data into a dictionary
        metadata = parse_name_value_pairs(metadata_str)
        
        return metadata
        
    except Exception as e:
        print(f"  ⚠ Could not fetch metadata: {e}")
        return {}


def check_directory_modified(host: str = "10.10.51.87", 
                             username: str = "sosdemo",
                             remote_dir: str = "/shared/sos/media",
                             days: int = 3):
    """
    Check if the remote directory was modified within the past N days.
    
    Args:
        host: SSH host address
        username: SSH username
        remote_dir: Remote directory to check
        days: Number of days to check
        
    Returns:
        bool: True if modified within the past N days, False otherwise
    """
    try:
        # Get modification time of directory
        cmd = f'stat -c %Y {remote_dir}'
        result = subprocess.run(
            ["ssh", f"{username}@{host}", cmd],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            mod_timestamp = int(result.stdout.strip())
            mod_date = datetime.fromtimestamp(mod_timestamp)
            current_date = datetime.now()
            days_ago = current_date - timedelta(days=days)
            
            print(f"Directory last modified: {mod_date}")
            print(f"Checking if modified since: {days_ago}")
            
            return mod_date >= days_ago
        else:
            print(f"Error checking directory modification time: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error checking directory: {e}")
        return False


def find_all_playlist_files(host: str = "10.10.51.87", 
                            username: str = "sosdemo",
                            remote_dir: str = "/shared/sos/media"):
    """
    Find all playlist.sos files recursively in the remote directory.
    
    Args:
        host: SSH host address
        username: SSH username
        remote_dir: Remote directory to search
        
    Returns:
        list: List of absolute paths to playlist.sos files
    """
    try:
        print(f"\nSearching for playlist.sos files in {remote_dir}...")
        
        # Use find command to locate all playlist.sos files
        cmd = f'find {remote_dir} -name "playlist.sos" -type f'
        result = subprocess.run(
            ["ssh", f"{username}@{host}", cmd],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            playlist_files = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            print(f"Found {len(playlist_files)} playlist.sos files")
            return playlist_files
        else:
            print(f"Error finding playlist files: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"Error finding playlist files: {e}")
        return []


def parse_playlist_file(file_content: str, playlist_path: str = ""):
    """
    Parse a playlist.sos file content and extract ALL relevant fields.
    
    Args:
        file_content: Content of the playlist.sos file
        playlist_path: Full path to the playlist.sos file (for resolving relative caption paths)
        
    Returns:
        dict: Dictionary with all parsed fields, or None if no data= field found
    """
    data = {
        'name': '',
        'category': '',
        'majorcategory': '',
        'data': '',
        'caption': '',
        'is_movie': False,
        'duration': '',
        'timer': '',
        'fps': '',
        'startframe': '',
        'endframe': '',
        'firstdwell': '',
        'lastdwell': ''
    }
    
    has_data = False
    
    for line in file_content.split('\n'):
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue
        
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip().lower()
            value = value.strip().strip('"')
            
            if key == 'name':
                data['name'] = value
            elif key == 'category':
                data['category'] = value
            elif key == 'majorcategory':
                data['majorcategory'] = value
            elif key == 'data':
                data['data'] = value
                has_data = True
                
                # Check if it's a movie (contains .mp4)
                if '.mp4' in value.lower():
                    data['is_movie'] = True
            elif key == 'caption':
                # If caption is relative path, convert to absolute
                if value and not value.startswith('/'):
                    # Get directory of playlist.sos file
                    playlist_dir = os.path.dirname(playlist_path)
                    # Join with caption path and normalize
                    caption_path = os.path.join(playlist_dir, value).replace('\\', '/')
                    data['caption'] = caption_path
                else:
                    data['caption'] = value
            elif key == 'duration':
                data['duration'] = value
            elif key == 'timer':
                data['timer'] = value
            elif key == 'fps':
                data['fps'] = value
            elif key == 'startframe':
                data['startframe'] = value
            elif key == 'endframe':
                data['endframe'] = value
            elif key == 'firstdwell':
                data['firstdwell'] = value
            elif key == 'lastdwell':
                data['lastdwell'] = value
    
    # Return None if no data= field found
    if not has_data:
        return None
    
    return data


def download_and_parse_playlist(remote_path: str,
                                host: str = "10.10.51.87",
                                username: str = "sosdemo"):
    """
    Download a playlist file via SSH and parse its contents.
    
    Args:
        remote_path: Remote path to the playlist.sos file
        host: SSH host address
        username: SSH username
        
    Returns:
        dict: Parsed playlist data, or None if error or no data= field
    """
    try:
        # Read file content via SSH
        cmd = f'cat {remote_path}'
        result = subprocess.run(
            ["ssh", f"{username}@{host}", cmd],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            content = result.stdout
            return parse_playlist_file(content, remote_path)
        else:
            print(f"Error reading file {remote_path}: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Error downloading/parsing {remote_path}: {e}")
        return None





def generate_server_index(output_file: str = "noaa_server_index.csv",
                          host: str = "10.10.51.87",
                          username: str = "sosdemo",
                          remote_dir: str = "/shared/sos/media"):
    """
    Generate a CSV index of all playlist.sos files on the server.
    Parses files directly via SSH - no SOS API calls needed.
    
    Args:
        output_file: Local path for the output CSV file
        host: SSH host address
        username: SSH username
        remote_dir: Remote directory to search
    """
    print("=" * 60)
    print("SOS Server Playlist Index Generator")
    print("=" * 60)
    
    # Find all playlist.sos files
    playlist_files = find_all_playlist_files(host, username, remote_dir)
    
    if not playlist_files:
        print("No playlist.sos files found.")
        return
    
    # Process each playlist file
    print("\nProcessing playlist files...")
    csv_data = []
    flagged_files = []
    
    for i, playlist_path in enumerate(playlist_files, 1):
        file_start_time = time.time()
        print(f"\n[{i}/{len(playlist_files)}] Processing: {playlist_path}")
        
        try:
            parsed_data = download_and_parse_playlist(playlist_path, host, username)
            
            if parsed_data is None:
                # No data= field found, flag this file
                flagged_files.append(playlist_path)
                print(f"  ⚠ No data= field found, flagged for review")
                continue
            
            # Add path to the data
            parsed_data['path'] = playlist_path
            
            # Show what we found
            key_fields = ['startframe', 'endframe', 'fps', 'firstdwell', 'lastdwell', 'timer', 'duration']
            present_fields = [f for f in key_fields if parsed_data.get(f)]
            if present_fields:
                print(f"  ✓ Metadata: {', '.join(f'{f}={parsed_data[f]}' for f in present_fields)}")
            
            csv_data.append(parsed_data)
            elapsed = time.time() - file_start_time
            print(f"  ✓ Name: {parsed_data['name']}, Category: {parsed_data.get('category', '')}, Movie: {parsed_data.get('is_movie', False)} ({elapsed:.2f}s)")
            
        except Exception as e:
            print(f"  ✗ Error processing file: {e}")
            # Continue to next file even if this one fails
            continue
    
    # Write CSV file
    print(f"\nWriting CSV to: {output_file}")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        # Include all metadata fields from playlist.sos files
        fieldnames = ['pretty_name', 'name', 'category', 'majorcategory', 'is_movie', 
                     'duration', 'timer', 'caption', 'path', 'data',
                     'fps', 'startframe', 'endframe', 'firstdwell', 'lastdwell']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        
        writer.writeheader()
        for entry in csv_data:
            row = {
                'pretty_name': '',  # Empty for manual modification
                'name': entry.get('name', ''),
                'category': entry.get('category', ''),
                'majorcategory': entry.get('majorcategory', ''),
                'is_movie': 'Yes' if entry.get('is_movie', False) else 'No',
                'duration': entry.get('duration', ''),
                'timer': entry.get('timer', ''),
                'caption': entry.get('caption', ''),
                'path': entry.get('path', ''),
                'data': entry.get('data', ''),
                'fps': entry.get('fps', ''),
                'startframe': entry.get('startframe', ''),
                'endframe': entry.get('endframe', ''),
                'firstdwell': entry.get('firstdwell', ''),
                'lastdwell': entry.get('lastdwell', '')
            }
            writer.writerow(row)
    
    print(f"✓ CSV index created with {len(csv_data)} entries")
    
    # Print flagged files
    if flagged_files:
        print(f"\n⚠ {len(flagged_files)} playlist.sos files without data= field:")
        for flagged_path in flagged_files:
            folder = os.path.dirname(flagged_path)
            print(f"  - {folder}")
    
    print("\nCompleted successfully!")


def main():
    generate_server_index()


if __name__ == '__main__':
    main()
    