"""
Executes on the B-link device in the SOS network.
Retrieves get_clip_info and get_all_name_value_pairs for the currently loaded clip only.

IMPORTANT: The SOS app must be running with a playlist loaded for this to work.
"""

import socket
import time
import re
import os
import subprocess


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
    pattern = r'(\w+)\s+(?:\{([^}]+)\}|(\S+))'
    for match in re.findall(pattern, data):
        key = match[0]
        value = match[1] if match[1] else match[2]
        result[key] = value
    return result


SOS2_IP   = "10.0.0.16"
SOS2_USER = "sos"


def _find_ssh_key() -> str | None:
    """Return the first available SSH private key, or None."""
    home = os.path.expanduser("~")
    for name in ("id_rsa", "id_ed25519", "id_ecdsa"):
        p = os.path.join(home, ".ssh", name)
        if os.path.exists(p):
            return p
    return None


def count_frames_in_datadir(datadir: str) -> int | None:
    """
    SSH into SOS2 and count the image files inside datadir.
    Returns the count as an int, or None on failure.
    """
    args = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "PasswordAuthentication=no",
        "-o", "ConnectTimeout=5",
    ]
    key = _find_ssh_key()
    if key:
        args += ["-i", key]
    args.append(f"{SOS2_USER}@{SOS2_IP}")

    # Resolve '..' in path, then count regular files (frames are .jpg/.png)
    remote_cmd = f"ls -1 {datadir} 2>/dev/null | wc -l"
    args.append(remote_cmd)

    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        stdout = result.stdout.decode("utf-8", "ignore").strip()
        return int(stdout) if stdout.isdigit() else None
    except Exception as e:
        print(f"[SSH] Frame count failed: {e}")
        return None


def compute_duration(num_frames: int, fps: float, firstdwell_ms: int, lastdwell_ms: int) -> float:
    """Compute total clip duration in seconds."""
    return (num_frames / fps) + (firstdwell_ms + lastdwell_ms) / 1000.0


def get_current_clip_info(host: str = "10.0.0.16", port: int = 2468, timeout: float = 4.0):
    """
    Connects to the SOS server and retrieves clip info and all name-value pairs
    for the currently loaded clip.

    Returns:
        dict with keys:
            'clip_number'  : int
            'clip_info'    : str  (raw response from get_clip_info)
            'name_values'  : dict (parsed get_all_name_value_pairs response)
        or None if connection fails.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        # Connect
        print(f"Connecting to SOS at {host}:{port}...")
        sock.connect((host, port))

        # Handshake
        sock.sendall(b'enable\n')
        recv_data(sock, timeout_idle=1.0)
        print("Connected successfully.\n")

        # Get current clip number
        sock.sendall(b'get_clip_number\n')
        data = recv_data(sock, timeout_idle=1.0)
        clip_num_str = data.decode('utf-8', 'ignore').strip()

        if not clip_num_str.isdigit():
            print(f"Error: Could not determine current clip number. Received: '{clip_num_str}'")
            return None

        clip_num = int(clip_num_str)
        print(f"Current clip number: {clip_num}\n")

        # get_clip_info
        sock.sendall(f'get_clip_info {clip_num}\n'.encode('utf-8'))
        data = recv_data(sock, timeout_idle=1.0)
        clip_info_raw = data.decode('utf-8', 'ignore').strip()

        # get_all_name_value_pairs
        sock.sendall(f'get_all_name_value_pairs {clip_num}\n'.encode('utf-8'))
        data = recv_data(sock, timeout_idle=1.0)
        nvp_raw = data.decode('utf-8', 'ignore').strip()
        name_values = parse_name_value_pairs(nvp_raw)

        # Compute duration via SSH frame count
        datadir    = name_values.get('datadir', '')
        fps        = float(name_values.get('fps', 0))
        firstdwell = int(name_values.get('firstdwell', 0))
        lastdwell  = int(name_values.get('lastdwell', 0))

        duration = None
        num_frames = None
        if datadir and fps > 0:
            print(f"Counting frames in '{datadir}' via SSH...")
            num_frames = count_frames_in_datadir(datadir)
            if num_frames is not None:
                duration = compute_duration(num_frames, fps, firstdwell, lastdwell)

        return {
            'clip_number': clip_num,
            'clip_info':   clip_info_raw,
            'name_values': name_values,
            'num_frames':  num_frames,
            'duration':    duration,
        }

    except OSError as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()


if __name__ == '__main__':
    print("=" * 60)
    print("SOS Current Clip Info")
    print("=" * 60)
    print()

    result = get_current_clip_info()

    if not result:
        print("Failed to retrieve clip data.")
        exit(1)

    print(f"Clip Number : {result['clip_number']}")
    print()

    print("── get_clip_info ──────────────────────────────────────────")
    print(result['clip_info'])
    print()

    print("── Duration Estimate ───────────────────────────────────────")
    if result['duration'] is not None:
        total_sec = int(round(result['duration']))
        mins, secs = divmod(total_sec, 60)
        print(f"  num_frames : {result['num_frames']}")
        print(f"  duration   : {result['duration']:.2f}s  ({mins}m {secs}s)")
    else:
        print("  Could not compute duration (SSH frame count unavailable).")
    print()

    print("── get_all_name_value_pairs ───────────────────────────────")
    name_values = result['name_values']
    if name_values:
        max_key_len = max(len(k) for k in name_values)
        for key, value in name_values.items():
            print(f"  {key:<{max_key_len}} : {value}")
    else:
        print("  (no data returned)")
    print()
