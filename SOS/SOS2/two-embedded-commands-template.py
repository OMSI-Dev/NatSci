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


def get_playlist_name(host: str = "10.10.51.98", port: int = 2468, timeout: float = 4.0):
    """
    Gets playlist name from the SOS server 
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        sock.connect((host, port))
        sock.sendall(b'enable\n')
        recv_data(sock, timeout_idle=1.0)
        
        # Get playlist name 
        sock.sendall(b'get_playlist_name\n')
        data = recv_data(sock, timeout_idle=1.0)
        playlist_data = data.decode('utf-8', 'ignore').strip()

        # Get paths of all clips in playlist, useful for subtitle fetch 
        sock.sendall(b'playlist_read ' + playlist_data.encode('utf-8') + b'\n')
        data = recv_data(sock, timeout_idle=1.0)
        playlist_read = data.decode('utf-8', 'ignore').strip()

        return playlist_read
        
    except OSError as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()


if __name__ == '__main__':
    playlist_name = get_playlist_name()
    if playlist_name:
        print(playlist_name) #put into JSON 
    else:
        print("Failed to retrieve clip data")
