import socket
import time
import subprocess
import os


def connect_to_server(host: str = "10.10.51.87", port: int = 2468, timeout: float = 4.0):
    """
    Connects to the OMSI SOS server
    Assumes server is running and actively playing a clip.
    Returns socket connection.
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


def get_playlist_name(sock: socket.socket):
    """Request current playlist file name."""
    print("\nRequesting playlist name")
    sock.sendall(b'get_playlist_name\n')
    data = recv_data(sock, timeout_idle=1.0)
    playlist_name = data.decode('utf-8', 'ignore').strip()
    print(f"Current playlist name: {playlist_name}")
    return playlist_name


def download_playlist_via_scp(remote_path: str, local_dir: str = ".", 
                              host: str = "10.10.51.87", 
                              username: str = "sosdemo"):
    """
    Download the playlist file from the SOS server via SCP.
    
    Args:
        remote_path: Full path to the playlist file on the server (e.g., /home/sosdemo/sosrc/custom_playlist.sos)
        local_dir: Local directory to save the file (default: current directory)
        host: SSH host address
        username: SSH username
        
    Returns:
        str: Local path to the downloaded file, or None on failure
    """
    try:
        # Create local filename
        filename = os.path.basename(remote_path)
        local_path = os.path.join(local_dir, filename)
        
        # Build SCP command
        scp_source = f"{username}@{host}:{remote_path}"
        
        print(f"\nDownloading via SCP: {scp_source}")
        print(f"Saving to: {local_path}")
        
        # Run SCP command
        result = subprocess.run(
            ["scp", scp_source, local_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ Downloaded to: {local_path}")
            return local_path
        else:
            print(f"✗ SCP failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return None
        
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None


def main():
    # Connect to server
    sock = connect_to_server()
    if not sock:
        print("Failed to connect")
        return
    
    try:
        # Send handshake
        send_handshake(sock)
        
        # Get playlist name (full path on server)
        playlist_path = get_playlist_name(sock)
        
        if playlist_path:
            # Download the playlist file via SCP
            local_path = download_playlist_via_scp(playlist_path)
            
            if local_path:
                print(f"\n✓ Playlist file ready: {local_path}")
            else:
                print("\n✗ Failed to download playlist file")
        
        print("\nCompleted successfully")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()


if __name__ == '__main__':
    main()
