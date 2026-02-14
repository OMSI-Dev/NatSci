"""
Test Script for nowPlaying Socket Receiver
Tests receiving PAUSE/UNPAUSE commands from engine.

Usage:
    python test_nowplaying.py

Expected behavior:
    - Listens on port 4096 for commands from engine
    - Displays "PAUSED" or "UNPAUSED" state changes
    - Simulates the nowPlaying display behavior
"""

import socket
import sys
import time

# Configuration (matches nowPlaying.py)
PI_PORT = 4096
BUFFER_SIZE = 8192

# State
is_paused = False


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


def handle_command(message: str):
    """Process received command and update state."""
    global is_paused
    
    message = message.strip().upper()
    
    if message == "PAUSE":
        is_paused = True
        print("[nowPlaying] ▶ PAUSED - Display shows pause overlay")
        return True
    elif message == "UNPAUSE":
        is_paused = False
        print("[nowPlaying] ▶ UNPAUSED - Display shows normal content")
        return True
    else:
        print(f"[nowPlaying] ⚠ Unknown command: {message}")
        return False


def start_server():
    """Start socket server to receive commands."""
    print("=" * 60)
    print("nowPlaying Test Server")
    print("=" * 60)
    print(f"Listening on port {PI_PORT}")
    print("Waiting for commands from engine...")
    print("Press Ctrl+C to exit")
    print("=" * 60)
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Remove SO_EXCLUSIVEADDRUSE - it might be preventing connections on Windows
    # We want to allow connections, not block them
    
    try:
        server_sock.bind(('0.0.0.0', PI_PORT))
    except OSError as e:
        print(f"[ERROR] Cannot bind to port {PI_PORT}")
        print(f"[ERROR] {e}")
        print("\nTroubleshooting:")
        print("  1. Check if another instance is running")
        print("  2. Try a different port")
        print("  3. Wait a moment and try again")
        sys.exit(1)
    
    server_sock.listen(5)
    server_sock.settimeout(0.1)  # Very short timeout like the real nowPlaying.py
    
    print(f"[nowPlaying] Server started successfully")
    print(f"[nowPlaying] Bound to 0.0.0.0:{PI_PORT} (accessible via localhost:{PI_PORT})")
    
    # Verify the socket is actually listening
    sock_info = server_sock.getsockname()
    print(f"[nowPlaying] Socket info: {sock_info}")
    print(f"[nowPlaying] Current state: {'PAUSED' if is_paused else 'UNPAUSED'}")
    print(f"[nowPlaying] Listening and ready for connections...\n")
    
    # Note: Server must actively listen to accept connections, but this is very lightweight.
    # The loop just waits for incoming connections - no active polling or network traffic.
    # Commands are only processed when engine sends them (which is infrequent).
    
    connection_attempts = 0
    
    try:
        while True:
            # Check for socket connections (non-blocking with short timeout)
            # This is passive waiting - no CPU/network overhead
            try:
                conn, addr = server_sock.accept()
                connection_attempts += 1
                print(f"\n[nowPlaying] ✓ Connection #{connection_attempts} from {addr[0]}:{addr[1]}")
            except socket.timeout:
                # No connection, continue waiting (this is normal and happens frequently)
                continue
            except KeyboardInterrupt:
                print("\n\n[nowPlaying] Shutting down...")
                break
            
            # If we got a connection, set timeout and receive data
            conn.settimeout(5.0)  # Prevent infinite blocking
            
            # Receive data (using same pattern as original nowPlaying.py)
            data = bytearray()
            try:
                while True:
                    chunk = conn.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    data.extend(chunk)
            except socket.timeout:
                print("[nowPlaying] Recv timeout - processing partial data")
            
            if data:
                message = data.decode('utf-8', errors='ignore').strip()
                print(f"[nowPlaying] Received: {message}")
                
                # Process command
                if handle_command(message):
                    # Send acknowledgment
                    try:
                        conn.sendall(b"OK\n")
                    except:
                        pass
                    print(f"[nowPlaying] Current state: {'PAUSED' if is_paused else 'UNPAUSED'}")
                else:
                    try:
                        conn.sendall(b"ERROR: Unknown command\n")
                    except:
                        pass
            else:
                print("[nowPlaying] No data received")
            
            conn.close()
                
    finally:
        server_sock.close()
        print("[nowPlaying] Server closed")


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n[nowPlaying] Interrupted by user")
        sys.exit(0)
