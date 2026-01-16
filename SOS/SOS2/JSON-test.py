import subprocess
import socket
import time
import re
import json 


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

        # Check if playlist exists in JSON : Access JSON and read object data for fetched playlist path. Check last modified date if exists (update if modified), create new entry if not exists
        try:
            with open('playlist_data.json', 'r') as json_file:
                playlist_cache = json.load(json_file)
                loaded_playlist_data = [pl for pl in playlist_cache if pl['path'] == loaded_playlist_path]
                loaded_playlist_exists = len(loaded_playlist_data) > 0

                if loaded_playlist_exists:
                    print ("Playlist exists in JSON data.")

                    # Check last modified date : Access JSON and SOS server file system data
                    command = 'ssh sos@10.10.51.98 "stat -c %y" ' + loaded_playlist_path + '"'
                    try:
                        result = subprocess.check_output(command, shell=True, text=True)
                        modification_date = result.strip().split()[0]

                        # Do nothing if existing playlist has no modifications 
                        if (modification_date == loaded_playlist_data[0]['last_modified']):
                            print("Playlist last modified date matches JSON data.")

                        # Update existing exntry if playlist does have modifications
                        elif (modification_date != loaded_playlist_data[0]['last_modified']):
                            pdata = fetch_playlist_data(loaded_playlist_path)
                            index = playlist_cache.index(loaded_playlist_data[0])
                            playlist_cache[index] = pdata
                            with open('playlist_data.json', 'w') as json_file:
                                json.dump(playlist_cache, json_file, indent=4)  
                            print("Playlist data updated in JSON due to last modified date change.")
                            
                    except subprocess.CalledProcessError as e:
                        print(f"Error occurred: {e}")

                # Add new entry if playlist does not exist in JSON 
                elif loaded_playlist_exists == False:
                    print("Playlist does not exist in JSON data.")
                    pdata = fetch_playlist_data(loaded_playlist_path)
                    playlist_cache.append(pdata)
                    with open('playlist_data.json', 'w') as json_file:
                        json.dump(playlist_cache, json_file, indent=4)
                    print("Playlist data added to JSON as new entry.")


            
                
        except FileNotFoundError:
            print("playlist_data.json not found.")

        return loaded_playlist_clips 
        
    except OSError as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()


def fetch_playlist_data(playlist_path, host: str = "10.10.51.98", port: int = 2468, timeout: float = 4.0):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    #Fetch playlist data from SOS server and return as dictionary

    #Initialize to dictionary -  playlist name, clip names, path on SOS server, last modified date 
    pdata = {
        'name': '',
        'path': playlist_path,
        'clips': [],  # Each clip will be a dict with 'name' and 'path' keys
        'last_modified': ''
    }

    pdata['name'] = playlist_path.split('/')[-1]  #Extract playlist name from path

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
        
        # Combine
        pdata['clips'] = [{'name': name, 'path': path} for name, path in zip(clip_names, clip_paths)]

    except OSError as e:
            print(f"Error getting clip info and playlist info with playlist_read and get_clip_info *: {e}")
    
    finally:
        sock.close()

    try:
        command = 'ssh sos@10.10.51.98 "stat -c %y ' + playlist_path + '"'
        result = subprocess.check_output(command, shell=True, text=True)
        modification_date = result.strip().split()[0]
        pdata['last_modified'] = modification_date
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while fetching last modified date: {e}")

    print (pdata)
    return pdata


if __name__ == '__main__':
    playlist_Initialization = initializePlaylist()
    if playlist_Initialization:
        print(playlist_Initialization) 
    else:
        print("Failed to retrieve clip data")
