"""
Science On a Sphere (SOS) TCP connection tester + media info probe.

This script:
1. Connects to the SOS server (default port 2468).
2. Performs a handshake ("enable").
3. Sends a series of metadata commands to list or discover
   media and playlist paths available to SOS.
"""

import socket
import time


# --- Socket connection utilities ---

def try_connect(host: str, port: int, timeout: float = 4.0):
    """Attempt to connect to the SOS TCP control socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        print(f"Connecting to SOS server {host}:{port} (timeout={timeout}s)...")
        sock.connect((host, port))
        print("✅ TCP connection established")
        return sock
    except OSError as e:
        print(f"❌ Connection failed: {e}")
        sock.close()
        return None


def recv_all(sock: socket.socket, timeout_idle: float = 1.0, chunk: int = 4096) -> bytes:
    """Receive data until the socket is idle for `timeout_idle` seconds."""
    buffer = bytearray()
    orig_timeout = sock.gettimeout()
    sock.settimeout(0.2)
    start = time.time()
    try:
        while True:
            try:
                data = sock.recv(chunk)
                if data:
                    buffer.extend(data)
                    start = time.time()
                else:
                    break
            except socket.timeout:
                if time.time() - start >= timeout_idle:
                    break
    finally:
        sock.settimeout(orig_timeout)
    return bytes(buffer)


def do_handshake(sock: socket.socket, timeout: float = 4.0):
    """Perform the standard SOS handshake (send 'enable')."""
    sock.settimeout(timeout)
    try:
        print("Sending handshake: 'enable\\n'")
        sock.sendall(b'enable\n')
    except OSError as e:
        print(f"❌ Failed to send handshake: {e}")
        return None

    data = recv_all(sock, timeout_idle=1.0)
    if not data:
        print("❌ No reply after handshake.")
        return None

    reply = data.decode("utf-8", "ignore").strip()
    print(f"↩ Handshake reply: {repr(reply)}")
    return reply


# --- SOS probing logic ---

def probe_commands(sock: socket.socket, commands, timeout_idle: float = 1.0):
    """Send a list of commands to the SOS server and print replies."""
    print("\n🔍 Probing SOS server for media information...\n")
    for cmd in commands:
        full = (cmd + "\n").encode("utf-8")
        print(f"--> {cmd}")
        try:
            sock.sendall(full)
        except OSError as e:
            print(f"   ❌ Failed to send: {e}")
            continue

        data = recv_all(sock, timeout_idle=timeout_idle)
        if not data:
            print("   ⚠️ No reply\n")
            continue

        text = data.decode("utf-8", "ignore").strip()
        print(f"<-- Reply ({len(text)} bytes):\n{text}\n")


# --- Main logic ---

def main():
    host = "10.10.51.87"
    port = 2468

    # Step 1: Connect to SOS
    sock = try_connect(host, port)
    if not sock:
        print("Result: connection_failed")
        return

    # Step 2: Perform handshake
    reply = do_handshake(sock)
    if reply is None:
        print("Result: handshake_failed")
        sock.close()
        return

    # Step 3: Probe for available commands / media data
    # Try common metadata-related commands
    probe_list = [
        "get_clip_count",
        "get_clip_number",
        "get_clip_info *",
        "get_clip_list",
        "get_clip_filename",
        "get_clip_path",
        "get_clip_filepath",
        "get_dataset_file",
        "get_media_path",
        "get_file_path",
        "get_file_name",
    ]

    probe_commands(sock, probe_list, timeout_idle=1.0)

    # Step 4: Clean up
    sock.close()
    print("\n🔌 Connection closed.")


if __name__ == "__main__":
    main()
