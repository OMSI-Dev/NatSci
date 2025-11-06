import subprocess
import os
import csv
from datetime import datetime, timedelta


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
    Parse a playlist.sos file content and extract relevant fields.
    
    Args:
        file_content: Content of the playlist.sos file
        playlist_path: Full path to the playlist.sos file (for resolving relative caption paths)
        
    Returns:
        dict: Dictionary with parsed fields (name, category, majorcategory, data, caption, is_movie)
              or None if no data= field found
    """
    data = {
        'name': '',
        'category': '',
        'majorcategory': '',
        'data': '',
        'caption': '',
        'is_movie': False
    }
    
    has_data = False
    
    for line in file_content.split('\n'):
        line = line.strip()
        
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
    
    Args:
        output_file: Local path for the output CSV file
        host: SSH host address
        username: SSH username
        remote_dir: Remote directory to search
    """
    print("=" * 60)
    print("SOS Server Playlist Index Generator")
    print("=" * 60)
    
    # COMMENTED OUT: Check if directory was modified in the past 3 days
    # print("\nChecking directory modification time...")
    # if not check_directory_modified(host, username, remote_dir, days=3):
    #     print("Directory has not been modified in the past 3 days. Skipping index generation.")
    #     return
    # print("Directory was recently modified. Proceeding with index generation.")
    
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
        print(f"[{i}/{len(playlist_files)}] Processing: {playlist_path}")
        
        parsed_data = download_and_parse_playlist(playlist_path, host, username)
        
        if parsed_data is None:
            # No data= field found, flag this file
            flagged_files.append(playlist_path)
            print(f"  ⚠ No data= field found, flagged for review")
            continue
        
        # Add path to the data
        parsed_data['path'] = playlist_path
        csv_data.append(parsed_data)
        print(f"  ✓ Name: {parsed_data['name']}, Category: {parsed_data['category']}, Movie: {parsed_data['is_movie']}")
    
    # Write CSV file
    print(f"\nWriting CSV to: {output_file}")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'category', 'majorcategory', 'is_movie', 'caption', 'pretty_name', 'path']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for entry in csv_data:
            writer.writerow({
                'name': entry['name'],
                'category': entry['category'],
                'majorcategory': entry['majorcategory'],
                'is_movie': 'Yes' if entry['is_movie'] else 'No',
                'caption': entry['caption'],
                'pretty_name': '',  # Empty for manual modification
                'path': entry['path']
            })
    
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
    