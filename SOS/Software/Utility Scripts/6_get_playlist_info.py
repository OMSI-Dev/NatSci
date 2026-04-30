"""
Executes on the B-link device in the SOS network.
A simple probe using playlist_read
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


def get_playlist_info(host: str = "10.10.51.98", port: int = 2468, timeout: float = 4.0):
    """
    Connects to the OMSI SOS server and retrieves playlist information for current clip. 

    Output: 
    '/home/sos/sosrc/Batch1_2026.sos'

    'Batch1_2026' representing the playlist name
    
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        # Connect
        sock.connect((host, port))
        
        # Handshake
        sock.sendall(b'enable\n')
        recv_data(sock, timeout_idle=1.0)
        
        # Get current playlist name
        sock.sendall(b'get_playlist_name\n')
        data = recv_data(sock, timeout_idle=1.0)
        playlist_info = data.decode('utf-8', 'ignore').strip()
        
        return playlist_info
        
    except OSError as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()


if __name__ == '__main__':
    playlist_info = get_playlist_info()
    if playlist_info:
        print("Playlist Information:")
        print("-" * 50)
        print(playlist_info)
    else:
        print("Failed to retrieve playlist data")
