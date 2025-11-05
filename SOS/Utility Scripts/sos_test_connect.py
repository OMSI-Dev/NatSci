import socket
import time


def connect_to_server(host: str = "10.10.51.87", port: int = 2468, timeout: float = 4.0):
    """
    Connects to the OMSI SOS server
    Assumes server is running and actively playing a clip.
    Returns playlist info and current clip name.
    
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        print(f"Connecting to {host}:{port}")
        sock.connect((host, port))
        print("Connected successfully")
        return sock
    except OSError as e:
        print(f"Connection failed: {e}")
        sock.close()
        return None


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


def send_handshake(sock: socket.socket):
    """Send enable handshake to server."""
    print("Sending handshake")
    sock.sendall(b'enable\n')
    data = recv_data(sock, timeout_idle=1.0)
    reply = data.decode('utf-8', 'ignore').strip()
    print(f"Handshake reply: {reply}")
    return reply


def get_clip_info(sock: socket.socket):
    """Request clip info with 'get_clip_info *'."""
    print("Requesting clip info: 'get_clip_info *'")
    sock.sendall(b'get_clip_info *\n')
    data = recv_data(sock, timeout_idle=1.0)
    text = data.decode('utf-8', 'ignore').strip()
    print(f"\nClip Info:\n{text}")
    return text


def get_clip_name(sock: socket.socket):
    """Request current clip number and name."""
    print("\nRequesting current clip number")
    sock.sendall(b'get_clip_number\n')
    data = recv_data(sock, timeout_idle=0.8)
    clip_num = data.decode('utf-8', 'ignore').strip()
    print(f"Current clip number: {clip_num}")
    
    # Now get the name for this specific clip
    if clip_num.isdigit():
        print(f"Requesting clip name for clip #{clip_num}")
        sock.sendall(f'get_clip_info {clip_num}\n'.encode('utf-8'))
        data = recv_data(sock, timeout_idle=0.8)
        clip_name = data.decode('utf-8', 'ignore').strip()
        print(f"Current clip name: {clip_name}")
        return clip_num, clip_name
    else:
        print("Clip number is not numeric, cannot request clip name")
        return clip_num, None


def main():
    # Connect to server
    sock = connect_to_server()
    if not sock:
        print("Failed to connect")
        return
    
    try:
        # Send handshake
        send_handshake(sock)
        
        # Get clip info *
        get_clip_info(sock)
        
        # Get current clip name
        get_clip_name(sock)
        
        print("\nCompleted successfully")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()


if __name__ == '__main__':
    main()
