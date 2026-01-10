"""
Executes on the B-link device in the SOS network.
This is a standalone script for connecting to the SOS server. 
Returns current clip information if a playlist is loaded. 

IMPORTANT: The SOS app must be running for the connection to succeed. 
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


def get_clip_info(host: str = "10.10.51.87", port: int = 2468, timeout: float = 4.0):
    """
    Connects to the OMSI SOS server and retrieves clip information.
    Returns a dictionary of clip metadata, or None if connection fails.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        # Connect
        sock.connect((host, port))
        
        # Handshake
        sock.sendall(b'enable\n')
        recv_data(sock, timeout_idle=1.0)
        
        # Get current clip number
        sock.sendall(b'get_clip_info 1\n')
        data = recv_data(sock, timeout_idle=1.0)
        clip_number = data.decode('utf-8', 'ignore').strip()
        
        # Get all name-value pairs for the current clip
        command = f'get_all_name_value_pairs {clip_number}\n'.encode('utf-8')
        sock.sendall(command)
        data = recv_data(sock, timeout_idle=1.0)
        clip_data = data.decode('utf-8', 'ignore').strip()
        
        # Parse the data into a dictionary
        clip_info = parse_name_value_pairs(clip_data)
        clip_info['clip_number'] = clip_number
        
        return clip_info
        
    except OSError as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()


if __name__ == '__main__':
    clip_info = get_clip_info()
    if clip_info:
        print("Clip Information:")
        print("-" * 50)
        for key, value in sorted(clip_info.items()):
            print(f"{key:20s}: {value}")
    else:
        print("Failed to retrieve clip data")
