"""
7_mpv_socket_test.py
--------------------
Standalone diagnostic script for testing MPV IPC socket creation and audio 
playback on SOS2, using the same configuration as audio_access.py.

Steps:
    1. Verify SSH connectivity to SOS2
    2. Confirm socat is available on SOS2
    3. Kill any stale MPV instance on the target socket
    4. Launch MPV in idle mode with the IPC socket
    5. Verify the socket was created
    6. Ping MPV via the socket (get_property: volume)
    7. Load and play a test audio file from AuxShare
    8. Wait and confirm playback is active (get_property: path)
    9. Stop playback and clean up MPV

Run this directly from your local machine — it SSHes into SOS2 automatically.
"""

import subprocess
import json
import time
import os
import sys

# ============================================================================
# CONFIGURATION — match values in audio_access.py / audio_init.py
# ============================================================================

SOS2_IP        = "10.0.0.16"
SOS2_USER      = "sos"
MPV_SOCKET     = "/tmp/mpv-audio-socket"
AUDIO_PATH     = "/AuxShare/audio/mp3"   # Full path on SOS2

# File to use for playback test — must exist at AUDIO_PATH on SOS2
TEST_FILE      = "air_1.mp3"

# How long to let audio play before checking / stopping (seconds)
PLAYBACK_WAIT  = 4

# ============================================================================
# HELPERS
# ============================================================================

def find_ssh_key():
    """Return the first available SSH private key, or None."""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".ssh", "id_rsa"),
        os.path.join(home, ".ssh", "id_ed25519"),
        os.path.join(home, ".ssh", "id_ecdsa"),
    ]
    for k in candidates:
        if os.path.exists(k):
            return k
    return None


def ssh_base():
    """Build the common SSH argument list."""
    args = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "PasswordAuthentication=no",
        "-o", "ConnectTimeout=5",
    ]
    key = find_ssh_key()
    if key:
        args += ["-i", key]
    return args


def run_ssh(remote_cmd, timeout=10, capture=True):
    """
    Run a command on SOS2 via SSH.
    Returns (returncode, stdout, stderr).
    """
    cmd = ssh_base() + [f"{SOS2_USER}@{SOS2_IP}", remote_cmd]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
        timeout=timeout,
    )
    stdout = result.stdout.decode("utf-8", "ignore").strip() if capture else ""
    stderr = result.stderr.decode("utf-8", "ignore").strip() if capture else ""
    return result.returncode, stdout, stderr


def send_mpv_command(command_dict, timeout=5):
    """
    Send a JSON command to MPV over the IPC socket via socat.
    Returns (success, response_text, error_text).
    """
    json_cmd = json.dumps(command_dict)
    json_escaped = json_cmd.replace("'", "'\"'\"'")
    socket_cmd = f"printf '%s\\n' '{json_escaped}' | socat - UNIX-CONNECT:{MPV_SOCKET}"
    code, out, err = run_ssh(socket_cmd, timeout=timeout)
    return (code == 0), out, err


def step(number, description):
    print(f"\n[Step {number}] {description}")
    print("-" * 50)


def ok(msg):
    print(f"  ✓  {msg}")


def fail(msg):
    print(f"  ✗  {msg}")


def info(msg):
    print(f"     {msg}")


# ============================================================================
# TEST SEQUENCE
# ============================================================================

def main():
    print("=" * 60)
    print("  MPV Socket Test — SOS2 Audio Diagnostic")
    print(f"  Target: {SOS2_USER}@{SOS2_IP}")
    print(f"  Socket: {MPV_SOCKET}")
    print(f"  Audio:  {AUDIO_PATH}/{TEST_FILE}")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: SSH connectivity
    # ------------------------------------------------------------------
    step(1, "Testing SSH connectivity")
    key = find_ssh_key()
    if key:
        info(f"Using key: {key}")
    else:
        info("WARNING: No SSH key found in ~/.ssh — connection may fail")

    try:
        code, out, err = run_ssh("echo SSH_OK", timeout=10)
        if code == 0 and "SSH_OK" in out:
            ok(f"Connected to {SOS2_IP}")
        else:
            fail(f"SSH failed (code {code}): {err}")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        fail("SSH connection timed out")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2: Verify socat
    # ------------------------------------------------------------------
    step(2, "Checking for socat on SOS2")
    code, out, err = run_ssh("which socat")
    if code == 0 and out:
        ok(f"socat found at: {out}")
    else:
        fail("socat not found. Install with: sudo apt-get install socat")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 3: Kill stale MPV / remove old socket
    # ------------------------------------------------------------------
    step(3, "Cleaning up any existing MPV instance on socket")
    run_ssh(
        f"pkill -f 'input-ipc-server={MPV_SOCKET}' ; rm -f {MPV_SOCKET}",
        timeout=5,
    )
    time.sleep(1)
    ok("Cleanup done")

    # ------------------------------------------------------------------
    # Step 4: Start MPV with IPC socket
    # ------------------------------------------------------------------
    step(4, "Launching MPV in idle mode with IPC socket")
    mpv_cmd = (
        f"nohup mpv --idle=yes --no-video --volume=50 "
        f"--input-ipc-server={MPV_SOCKET} "
        f"--really-quiet > /dev/null 2>&1 &"
    )
    info(f"Command: {mpv_cmd}")
    code, out, err = run_ssh(mpv_cmd, timeout=10)
    if code == 0:
        ok("MPV launch command sent successfully")
    else:
        fail(f"MPV launch command returned code {code}: {err}")
        sys.exit(1)

    info("Waiting 3s for MPV to initialize...")
    time.sleep(3)

    # ------------------------------------------------------------------
    # Step 5: Verify socket exists
    # ------------------------------------------------------------------
    step(5, "Verifying IPC socket was created")
    code, out, err = run_ssh(f"test -S {MPV_SOCKET} && ls -l {MPV_SOCKET}")
    if code == 0 and out:
        ok(f"Socket exists: {out}")
    else:
        fail(f"Socket not found at {MPV_SOCKET}")
        info("Try running MPV manually without nohup to see any error output:")
        info(f"  mpv --idle=yes --no-video --input-ipc-server={MPV_SOCKET}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 6: Ping MPV — get volume
    # ------------------------------------------------------------------
    step(6, "Pinging MPV via socket (get_property: volume)")
    success, response, err = send_mpv_command({"command": ["get_property", "volume"]})
    if success and response:
        try:
            parsed = json.loads(response)
            volume = parsed.get("data")
            status = parsed.get("error")
            if status == "success":
                ok(f"MPV responding — current volume: {volume}")
            else:
                fail(f"MPV returned error: {status}")
                sys.exit(1)
        except json.JSONDecodeError:
            info(f"Raw response (non-JSON): {response}")
            ok("Socket is responding (non-JSON response)")
    else:
        fail(f"No response from socket: {err}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 7: Load and play the test file
    # ------------------------------------------------------------------
    step(7, f"Loading test file: {TEST_FILE}")
    full_path = f"{AUDIO_PATH}/{TEST_FILE}"
    info(f"Full path on SOS2: {full_path}")

    # Confirm the file exists first
    code, out, err = run_ssh(f"test -f '{full_path}' && echo FILE_OK")
    if code == 0 and "FILE_OK" in out:
        ok(f"File confirmed on SOS2: {full_path}")
    else:
        fail(f"File not found on SOS2: {full_path}")
        info("Check AUDIO_PATH at the top of this script, or list files with:")
        info(f"  ls {AUDIO_PATH}")
        sys.exit(1)

    success, response, err = send_mpv_command(
        {"command": ["loadfile", full_path, "replace"]}
    )
    if success:
        ok("loadfile command accepted by MPV")
    else:
        fail(f"loadfile failed: {err}")
        sys.exit(1)

    # Enable loop
    time.sleep(0.3)
    send_mpv_command({"command": ["set_property", "loop-file", "inf"]})
    info("Loop mode enabled")

    # ------------------------------------------------------------------
    # Step 8: Confirm playback is active
    # ------------------------------------------------------------------
    step(8, f"Confirming playback (waiting {PLAYBACK_WAIT}s...)")
    time.sleep(PLAYBACK_WAIT)

    success, response, err = send_mpv_command({"command": ["get_property", "path"]})
    if success and response:
        try:
            parsed = json.loads(response)
            playing_path = parsed.get("data", "")
            status = parsed.get("error")
            if status == "success" and playing_path:
                ok(f"Active playback confirmed: {playing_path}")
            elif status == "success" and not playing_path:
                fail("MPV reports no active file — playback may have failed silently")
            else:
                info(f"MPV error on path query: {status}")
        except json.JSONDecodeError:
            info(f"Raw response: {response}")
    else:
        fail(f"Could not query playback state: {err}")

    # ------------------------------------------------------------------
    # Step 9: Stop and clean up
    # ------------------------------------------------------------------
    step(9, "Stopping playback and quitting MPV")
    send_mpv_command({"command": ["stop"]})
    time.sleep(0.3)
    send_mpv_command({"command": ["quit"]})
    time.sleep(0.5)
    run_ssh(f"rm -f {MPV_SOCKET}", timeout=5)
    ok("MPV stopped and socket removed")

    print("\n" + "=" * 60)
    print("  All steps passed — MPV socket and audio playback working")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
