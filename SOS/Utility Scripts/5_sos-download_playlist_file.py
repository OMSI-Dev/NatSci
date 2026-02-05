"""
Executes on the B-link device in the SOS network.

Displays all clips in the current SOS playlist and allows the user to download 
the associated playlist.sos file from the SOS server.

Uses the 'data' or 'caption' metadata field to determine the directory location,
then downloads the playlist.sos file from that directory.

IMPORTANT: The SOS app must be running with a playlist loaded for this to work.
"""

import socket
import time
import re
import subprocess
import os
from datetime import datetime


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


def get_playlist_clips(host: str = "10.10.51.87", port: int = 2468, timeout: float = 4.0):
    """
    Connect to SOS and retrieve all clip names and their metadata.
    
    Returns:
        tuple: (clip_list, playlist_name) or (None, None) on failure
            clip_list is a list of dicts with clip info
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
        
        # Get playlist name
        sock.sendall(b'get_playlist_name\n')
        data = recv_data(sock, timeout_idle=1.0)
        playlist_name = data.decode('utf-8', 'ignore').strip()
        
        # Get clip count
        sock.sendall(b'get_clip_count\n')
        data = recv_data(sock, timeout_idle=1.0)
        clip_count_str = data.decode('utf-8', 'ignore').strip()
        
        try:
            clip_count = int(clip_count_str)
        except ValueError:
            print(f"Error: Could not determine clip count. Received: '{clip_count_str}'")
            return None, None
        
        if clip_count <= 0:
            print("Error: No clips in playlist")
            return None, None
        
        print(f"Playlist: {playlist_name}")
        print(f"Found {clip_count} clips.\n")
        
        clips = []
        
        # Iterate through all clips
        for clip_num in range(1, clip_count + 1):
            # Get all name-value pairs for this clip
            command = f'get_all_name_value_pairs {clip_num}\n'.encode('utf-8')
            sock.sendall(command)
            data = recv_data(sock, timeout_idle=1.0)
            clip_data = data.decode('utf-8', 'ignore').strip()
            
            # Parse the data into a dictionary
            clip_info = parse_name_value_pairs(clip_data)
            clip_info['clip_number'] = str(clip_num)
            
            clips.append(clip_info)
        
        return clips, playlist_name
        
    except OSError as e:
        print(f"Error: {e}")
        return None, None
    finally:
        sock.close()


def extract_directory_from_metadata(clip_metadata):
    """
    Extract the directory path from clip metadata.
    Tries multiple fields in priority order: caption, data, audio, file
    
    Args:
        clip_metadata: Dictionary of clip metadata
        
    Returns:
        str: Directory path (e.g., /shared/sos/media/site-custom/Movies/clip_name/)
             or None if no valid path found
    """
    # Try fields in priority order
    path_fields = ['caption', 'caption2', 'data', 'audio', 'file', 'layer', 'layerdata']
    
    for field in path_fields:
        if field in clip_metadata:
            file_path = clip_metadata[field]
            
            # Check if it's a full server path
            if file_path.startswith('/shared/sos/'):
                # Extract directory (remove filename)
                directory = os.path.dirname(file_path)
                return directory
    
    return None


def download_playlist_file(remote_dir, local_path, ssh_user='sosdemo', ssh_host='10.10.51.87'):
    """
    Download playlist.sos file from remote directory to local path using SCP.
    
    Args:
        remote_dir: Remote directory path (e.g., /shared/sos/media/site-custom/Movies/clip_name/)
        local_path: Local path to save the file
        ssh_user: SSH username
        ssh_host: SSH host IP
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Construct full remote path to playlist.sos
    remote_file = f"{remote_dir}/playlist.sos"
    
    print(f"\nDownloading from: {remote_file}")
    print(f"Saving to: {local_path}")
    
    # Build SCP command
    scp_cmd = [
        "scp",
        "-o", "StrictHostKeyChecking=no",
        f"{ssh_user}@{ssh_host}:{remote_file}",
        local_path
    ]
    
    try:
        result = subprocess.run(
            scp_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and os.path.exists(local_path):
            file_size = os.path.getsize(local_path)
            print(f"✓ Download successful! ({file_size} bytes)")
            return True
        else:
            print(f"✗ Download failed")
            if result.stderr:
                print(f"  Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Download timed out")
        return False
    except Exception as e:
        print(f"✗ Error during download: {e}")
        return False


def main():
    print("=" * 80)
    print("SOS Playlist File Downloader")
    print("=" * 80)
    print()
    
    # Get playlist clips
    clips, playlist_name = get_playlist_clips()
    
    if not clips:
        print("Failed to retrieve playlist information")
        return
    
    # Display clips with directory information
    print("=" * 80)
    print("Clips in Current Playlist:")
    print("=" * 80)
    
    clips_with_dirs = []
    for clip in clips:
        clip_num = clip.get('clip_number', '?')
        clip_name = clip.get('name', 'Unknown')
        duration = clip.get('timer', clip.get('duration', 'N/A'))
        remote_dir = extract_directory_from_metadata(clip)
        
        print(f"  [{clip_num}] {clip_name} (duration: {duration}s)")
        
        if remote_dir:
            clips_with_dirs.append((clip_num, clip_name, remote_dir))
    
    print("=" * 80)
    print()
    
    # Check if we found any clips with directory information
    if not clips_with_dirs:
        print("✗ Could not determine playlist directory from any clip metadata.")
        print("  No 'caption', 'data', 'audio', or 'file' fields found with full paths.")
        return
    
    # Let user select which clip to use for directory
    print(f"Found {len(clips_with_dirs)} clip(s) with directory information:")
    for clip_num, clip_name, remote_dir in clips_with_dirs:
        print(f"  [{clip_num}] {clip_name}")
        print(f"      → {remote_dir}")
    
    print()
    print("Enter clip number to download its playlist.sos file")
    print("(or press Enter to use first clip):")
    user_choice = input("> ").strip()
    
    # Find selected clip
    selected_clip = None
    if user_choice:
        for clip_num, clip_name, remote_dir in clips_with_dirs:
            if clip_num == user_choice:
                selected_clip = (clip_num, clip_name, remote_dir)
                break
        
        if not selected_clip:
            print(f"✗ Invalid clip number: {user_choice}")
            return
    else:
        # Use first clip with directory info
        selected_clip = clips_with_dirs[0]
    
    clip_num, source_clip, remote_dir = selected_clip
    
    print()
    print(f"Selected clip [{clip_num}]: {source_clip}")
    print(f"Playlist directory: {remote_dir}")
    print()
    
    # Prompt user for download location
    print("Enter local download path (or press Enter for current directory):")
    user_input = input("> ").strip()
    
    if not user_input:
        # Default to current directory with timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = f"playlist_{timestamp}.sos"
    else:
        local_path = user_input
        # If user provided a directory, append filename
        if os.path.isdir(local_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_path = os.path.join(local_path, f"playlist_{timestamp}.sos")
    
    # Ensure directory exists
    local_dir = os.path.dirname(local_path)
    if local_dir and not os.path.exists(local_dir):
        try:
            os.makedirs(local_dir)
            print(f"Created directory: {local_dir}")
        except Exception as e:
            print(f"✗ Could not create directory: {e}")
            return
    
    # Download the file
    success = download_playlist_file(remote_dir, local_path)
    
    if success:
        print()
        print("=" * 80)
        print("Download Complete!")
        print("=" * 80)
        print(f"\nYou can now edit the playlist.sos file at:")
        print(f"  {os.path.abspath(local_path)}")
    else:
        print()
        print("Download failed. Please check:")
        print("  - SSH keys are properly configured")
        print("  - The playlist.sos file exists in the detected directory")
        print("  - Network connectivity to the SOS server")


if __name__ == '__main__':
    main()
