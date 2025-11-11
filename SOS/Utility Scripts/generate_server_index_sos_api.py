"""
SOS Server Index Generator (SOS API Method)
Generates comprehensive CSV index of all media files on SOS server.

This script uses a hybrid approach:
1. Scans playlist.sos files via SSH to get organizational metadata (category, majorcategory)
2. Uses SOS API (load + get_all_name_value_pairs) to fetch computed metadata from actual media files
3. Merges both datasets into a comprehensive CSV output

This ensures we capture both static playlist metadata and dynamic media properties.
"""

import subprocess
import os
import csv
import socket
import time
import re
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


def connect_to_sos(sos_ip='10.10.51.87', sos_port=2468, timeout=4):
    """
    Connect to the SOS server and send enable handshake.
    
    Args:
        sos_ip: IP address of SOS server
        sos_port: Port number of SOS server
        timeout: Socket timeout in seconds
        
    Returns:
        socket object if successful, None otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        print(f"Connecting to SOS at {sos_ip}:{sos_port}...")
        sock.connect((sos_ip, sos_port))
        
        # Send enable handshake
        sock.sendall(b'enable\n')
        
        # Wait for response
        data = sock.recv(1024)
        response = data.decode('utf-8', 'ignore').strip()
        
        if response == 'R':
            print("✓ Connected to SOS server\n")
            return sock
        else:
            print(f"⚠ Unexpected handshake response: {response}")
            return sock  # Continue anyway
            
    except socket.error as e:
        print(f"✗ Failed to connect to SOS: {e}")
        return None
    except Exception as e:
        print(f"✗ Error during SOS connection: {e}")
        return None


def load_file_in_sos(sock, file_path, timeout=5.0, debug=False):
    """
    Load a file in SOS using the 'load' command.
    This creates a temporary clip (number 0) that we can query for metadata.
    
    Args:
        sock: Connected SOS socket
        file_path: Full path to media file on SOS server
        timeout: Maximum time to wait for load operation
        debug: Print debug information
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if debug:
            print(f"  [DEBUG] Loading: {file_path}")
        
        # Set socket timeout for this operation
        orig_timeout = sock.gettimeout()
        sock.settimeout(timeout)
        
        command = f'load {file_path}\n'.encode('utf-8')
        sock.sendall(command)
        
        # Wait for SOS to process the load
        time.sleep(0.2)
        
        # Clear any response
        try:
            data = recv_data(sock, timeout_idle=0.3)
            if debug and data:
                print(f"  [DEBUG] Load response: {data.decode('utf-8', 'ignore')[:100]}")
        except socket.timeout:
            if debug:
                print(f"  [DEBUG] No response from load (normal)")
            pass
        
        # Restore original timeout
        sock.settimeout(orig_timeout)
        
        return True
        
    except socket.timeout:
        print(f"  ⚠ Timeout loading file")
        return False
    except Exception as e:
        print(f"  ⚠ Error loading file: {e}")
        return False


def fetch_metadata_from_sos(sock, timeout=5.0, debug=False):
    """
    Fetch metadata for currently loaded file (clip 0) using get_all_name_value_pairs.
    
    Args:
        sock: Connected SOS socket
        timeout: Maximum time to wait for metadata
        debug: Print debug information
        
    Returns:
        dict: Parsed metadata dictionary, or empty dict on failure
    """
    try:
        if debug:
            print(f"  [DEBUG] Fetching metadata for clip 0...")
        
        # Set socket timeout for this operation
        orig_timeout = sock.gettimeout()
        sock.settimeout(timeout)
        
        # Get all name-value pairs for clip 0 (temporary loaded file)
        command = b'get_all_name_value_pairs 0\n'
        sock.sendall(command)
        
        # Receive data with timeout
        data = recv_data(sock, timeout_idle=1.5)
        metadata_str = data.decode('utf-8', 'ignore').strip()
        
        # Restore original timeout
        sock.settimeout(orig_timeout)
        
        if not metadata_str:
            if debug:
                print(f"  [DEBUG] No metadata received")
            return {}
        
        if debug:
            print(f"  [DEBUG] Received {len(metadata_str)} bytes of metadata")
        
        # Parse the data into a dictionary
        metadata = parse_name_value_pairs(metadata_str)
        
        if debug:
            print(f"  [DEBUG] Parsed {len(metadata)} metadata fields")
        
        return metadata
        
    except socket.timeout:
        print(f"  ⚠ Timeout fetching metadata")
        return {}
    except Exception as e:
        print(f"  ⚠ Error fetching metadata: {e}")
        return {}


def parse_playlist_file(playlist_content):
    """
    Parse playlist.sos file content to extract organizational metadata.
    
    Args:
        playlist_content: Content of playlist.sos file as string
        
    Returns:
        dict: Dictionary with name, category, majorcategory, and data path
    """
    result = {}
    
    for line in playlist_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Split on first '=' only
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Extract fields we need from playlist
            if key == 'name':
                result['name'] = value
            elif key == 'category':
                result['category'] = value
            elif key == 'majorcategory':
                result['majorcategory'] = value
            elif key == 'data':
                result['data'] = value
    
    return result


def find_all_playlist_files(ssh_user='sosdemo', ssh_host='10.10.51.87', base_dir='/shared/sos/media'):
    """
    Find all playlist.sos files on the SOS server via SSH.
    
    Returns:
        list: List of full paths to playlist.sos files
    """
    try:
        print(f"Scanning {ssh_host} for playlist.sos files...")
        
        ssh_cmd = f'ssh {ssh_user}@{ssh_host} "find {base_dir} -name playlist.sos -type f"'
        result = subprocess.run(
            ['powershell', '-Command', ssh_cmd],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        
        if result.returncode == 0:
            files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            print(f"✓ Found {len(files)} playlist.sos files\n")
            return files
        else:
            print(f"✗ SSH find command failed: {result.stderr}")
            return []
            
    except subprocess.TimeoutExpired:
        print("✗ SSH find command timed out")
        return []
    except Exception as e:
        print(f"✗ Error finding playlist files: {e}")
        return []


def read_remote_file(file_path, ssh_user='sosdemo', ssh_host='10.10.51.87', timeout=15):
    """
    Read contents of a remote file via SSH.
    
    Returns:
        str: File contents, or None if failed
    """
    try:
        ssh_cmd = f'ssh {ssh_user}@{ssh_host} "cat {file_path}"'
        result = subprocess.run(
            ['powershell', '-Command', ssh_cmd],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            return None
            
    except subprocess.TimeoutExpired:
        # SSH command timed out - skip this file
        return None
    except UnicodeDecodeError:
        # File contains characters that can't be decoded - skip it
        return None
    except Exception as e:
        return None


def generate_server_index_sos_api(output_file='noaa_server_index_sos_api.csv'):
    """
    Generate comprehensive server index using SOS API for metadata.
    
    Workflow:
    1. Find all playlist.sos files via SSH
    2. Parse each playlist for organizational metadata
    3. Extract unique media file paths
    4. Connect to SOS server
    5. For each unique media file:
       - Load it in SOS (creates temporary clip 0)
       - Fetch all metadata via get_all_name_value_pairs
       - Merge with playlist metadata
    6. Write to CSV
    """
    print("="*70)
    print("SOS Server Index Generator (SOS API Method)")
    print("="*70)
    print()
    
    # Step 1: Find all playlist files
    playlist_files = find_all_playlist_files()
    if not playlist_files:
        print("No playlist files found. Exiting.")
        return
    
    # Step 2: Parse all playlists and collect media files
    print("Parsing playlist files...")
    media_files = {}  # {data_path: {name, category, majorcategory, directory}}
    failed_reads = 0
    
    for i, playlist_path in enumerate(playlist_files, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(playlist_files)} playlists... ({len(media_files)} unique files found)")
        
        try:
            # Read playlist content
            content = read_remote_file(playlist_path, timeout=15)
            if not content:
                failed_reads += 1
                if failed_reads % 10 == 0:
                    print(f"  ⚠ {failed_reads} playlist reads have failed/timed out")
                continue
            
            # Parse playlist
            playlist_data = parse_playlist_file(content)
            
            # Get data path (media file)
            data_path = playlist_data.get('data', '')
            if not data_path:
                continue
            
            # Store organizational metadata with this media file
            # Extract directory from playlist path
            directory = os.path.dirname(playlist_path).replace('/shared/sos/media/', '')
            
            # If we've already seen this media file, keep the first one's metadata
            if data_path not in media_files:
                media_files[data_path] = {
                    'name': playlist_data.get('name', ''),
                    'category': playlist_data.get('category', ''),
                    'majorcategory': playlist_data.get('majorcategory', ''),
                    'directory': directory
                }
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted during playlist parsing. Continuing with files found so far...")
            break
        except Exception as e:
            failed_reads += 1
            continue
    
    print(f"✓ Found {len(media_files)} unique media files")
    if failed_reads > 0:
        print(f"⚠ Skipped {failed_reads} playlists due to read failures/timeouts")
    print()
    
    # Step 3: Connect to SOS server
    sos_sock = connect_to_sos()
    if not sos_sock:
        print("Cannot connect to SOS server. Exiting.")
        return
    
    # Step 4: Process each media file through SOS API
    print("Fetching metadata via SOS API...")
    print("This may take a while for large collections...")
    print("(Enable debug mode on first 5 files)\n")
    
    all_data = []
    failed_files = []
    reconnect_count = 0
    
    media_file_list = list(media_files.items())
    start_time = time.time()
    
    for i, (data_path, playlist_meta) in enumerate(media_file_list, 1):
        # Debug mode for first few files
        debug = (i <= 5)
        # Progress indicator with timing
        if i % 10 == 0 or i == 1:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(media_file_list) - i) / rate if rate > 0 else 0
            print(f"[{i}/{len(media_file_list)}] Processing... ({rate:.1f} files/sec, ETA: {eta/60:.1f} min)")
        
        # Show current file being processed (every 50 files or on failures)
        if i % 50 == 0 or (failed_files and len(failed_files) % 10 == 0):
            print(f"  Current: {os.path.basename(data_path)}")
        
        try:
            # Load file in SOS with timeout
            if not load_file_in_sos(sos_sock, data_path, timeout=8.0, debug=debug):
                print(f"  ✗ Failed to load: {os.path.basename(data_path)}")
                failed_files.append(data_path)
                
                # Check if we need to reconnect after failures
                if len(failed_files) % 5 == 0:
                    print("  Checking SOS connection health...")
                    try:
                        sos_sock.sendall(b'get_frame_number\n')
                        sos_sock.recv(1024)
                    except:
                        print("  Connection lost, reconnecting...")
                        try:
                            sos_sock.close()
                        except:
                            pass
                        sos_sock = connect_to_sos()
                        if not sos_sock:
                            print("  ✗ Reconnection failed. Saving progress and exiting.")
                            break
                        reconnect_count += 1
                continue
            
            # Fetch metadata from SOS with timeout
            sos_metadata = fetch_metadata_from_sos(sos_sock, timeout=8.0, debug=debug)
            
            if not sos_metadata:
                print(f"  ✗ No metadata: {os.path.basename(data_path)}")
                failed_files.append(data_path)
                continue
            
            if debug:
                print(f"  [DEBUG] Metadata keys: {list(sos_metadata.keys())}")
            
            # Merge playlist metadata with SOS metadata
            merged_data = {
                'directory': playlist_meta['directory'],
                'name': playlist_meta['name'] or sos_metadata.get('name', ''),
                'category': playlist_meta['category'],
                'majorcategory': playlist_meta['majorcategory'],
                'data': data_path,
                'caption': sos_metadata.get('caption', ''),
                'duration': sos_metadata.get('duration', ''),
                'timer': sos_metadata.get('timer', ''),
                'fps': sos_metadata.get('fps', ''),
                'startframe': sos_metadata.get('startframe', ''),
                'endframe': sos_metadata.get('endframe', ''),
                'firstdwell': sos_metadata.get('firstdwell', ''),
                'lastdwell': sos_metadata.get('lastdwell', '')
            }
            
            all_data.append(merged_data)
            
            # Small delay to avoid overwhelming SOS
            time.sleep(0.05)
            
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user. Saving progress...")
            break
        except Exception as e:
            print(f"  ✗ Unexpected error processing {os.path.basename(data_path)}: {e}")
            failed_files.append(data_path)
            continue
    
    # Close SOS connection
    try:
        if sos_sock:
            sos_sock.close()
    except:
        pass
    
    total_time = time.time() - start_time
    print(f"\n✓ Successfully processed {len(all_data)} files in {total_time/60:.1f} minutes")
    if failed_files:
        print(f"⚠ Failed to process {len(failed_files)} files")
        print(f"  (Check console output above for details)")
    if reconnect_count > 0:
        print(f"ℹ Reconnected to SOS {reconnect_count} times")
    print()
    
    # Step 5: Write to CSV
    if not all_data:
        print("No data to write. Exiting.")
        return
    
    print(f"Writing data to {output_file}...")
    
    fieldnames = [
        'directory', 'name', 'category', 'majorcategory', 'data',
        'caption', 'duration', 'timer', 'fps', 'startframe', 'endframe',
        'firstdwell', 'lastdwell'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"✓ CSV file created: {output_file}")
    print(f"  Total entries: {len(all_data)}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("="*70)
    print("Index generation complete!")
    print("="*70)


if __name__ == '__main__':
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Generate the index
    generate_server_index_sos_api()
