"""
Audio Controller for MPV on SOS2
Provides audio playback control via SSH and MPV IPC.
"""

import subprocess
import json
import time
import socket
import os


class AudioController:
    """Controller for MPV audio playback on remote SOS2 server."""
    
    def __init__(self, sos2_ip="10.0.0.16", sos2_user="sos", audio_path="/AuxShare/audio/mp3"): #NETWORK
        """
        Initialize the audio controller.
        
        Args:
            sos2_ip: IP address of SOS2 server
            sos2_user: SSH username for SOS2
            audio_path: Path to audio files on SOS2
        """
        self.sos2_ip = sos2_ip
        self.sos2_user = sos2_user
        self.audio_path = audio_path
        self.mpv_socket = "/tmp/mpv-audio-socket"
        self.ssh_process = None
        self.is_initialized = False
        self.current_track = None
        self.fade_duration = 2.0  # Default fade duration in seconds
        
        # Initialize MPV on SOS2
        self._initialize_mpv()
    
    def _find_ssh_keys(self):
        """Find available SSH key files."""
        home = os.path.expanduser("~")
        key_locations = [
            os.path.join(home, ".ssh", "id_rsa"),
            os.path.join(home, ".ssh", "id_ed25519"),
            os.path.join(home, ".ssh", "id_ecdsa")
        ]
        return [k for k in key_locations if os.path.exists(k)]

    def _ssh_base(self):
        """Build the common SSH argument list (ConnectTimeout included)."""
        args = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "BatchMode=yes",
            "-o", "PasswordAuthentication=no",
            "-o", "ConnectTimeout=5",
        ]
        found_keys = self._find_ssh_keys()
        if found_keys:
            args += ["-i", found_keys[0]]
        return args

    def _run_ssh(self, remote_cmd, timeout=10, capture=True):
        """
        Run a command on SOS2 via SSH.
        Returns (returncode, stdout, stderr).
        """
        cmd = self._ssh_base() + [f"{self.sos2_user}@{self.sos2_ip}", remote_cmd]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
            stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
            timeout=timeout,
        )
        stdout = result.stdout.decode("utf-8", "ignore").strip() if capture else ""
        stderr = result.stderr.decode("utf-8", "ignore").strip() if capture else ""
        return result.returncode, stdout, stderr

    def _test_ssh_connection(self):
        """Test basic SSH connectivity to SOS2."""
        try:
            found_keys = self._find_ssh_keys()
            if found_keys:
                print(f"[Audio] Using SSH key: {found_keys[0]}")
            else:
                print("[Audio] WARNING: No SSH keys found")

            code, out, err = self._run_ssh("echo SSH_OK", timeout=10)
            if code == 0 and "SSH_OK" in out:
                print(f"[Audio] SSH connection to {self.sos2_ip} successful")
                return True
            else:
                print(f"[Audio] SSH connection failed: {err}")
                return False

        except Exception as e:
            print(f"[Audio] SSH test failed: {e}")
            return False
    
    def _initialize_mpv(self):
        """Launch MPV on SOS2 with IPC socket for control."""
        print("[Audio] Initializing MPV on SOS2...")

        try:
            # Test SSH connection first
            if not self._test_ssh_connection():
                print("[Audio] Cannot initialize MPV - SSH connection failed")
                self.is_initialized = False
                return

            # Check if socat is available
            print("[Audio] Checking for socat on SOS2...")
            code, out, err = self._run_ssh("which socat", timeout=5)
            if code != 0:
                print("[Audio] ERROR: socat not found on SOS2. Install with: sudo apt-get install socat")
                self.is_initialized = False
                return
            print(f"[Audio] socat found at: {out}")

            # Kill any existing MPV instances on the socket
            print("[Audio] Cleaning up old MPV instances...")
            self._run_ssh(
                f"pkill -f 'input-ipc-server={self.mpv_socket}' ; rm -f {self.mpv_socket}",
                timeout=5, capture=False
            )
            time.sleep(1)

            # MPV command with IPC socket, idle mode, and no video
            mpv_cmd = (
                f"nohup mpv --idle=yes --no-video --volume=100 "
                f"--input-ipc-server={self.mpv_socket} "
                f"--really-quiet > /dev/null 2>&1 &"
            )
            print(f"[Audio] Starting MPV with command: {mpv_cmd}")
            code, out, err = self._run_ssh(mpv_cmd, timeout=10)
            if code != 0:
                print(f"[Audio] MPV launch failed: {err}")
                self.is_initialized = False
                return

            # Give MPV time to start and create socket
            print("[Audio] Waiting for MPV to initialize...")
            time.sleep(3)

            # Verify socket exists
            code, out, err = self._run_ssh(f"test -S {self.mpv_socket} && ls -l {self.mpv_socket}")
            if code != 0 or not out:
                print(f"[Audio] ERROR: MPV socket not found at {self.mpv_socket}")
                self.is_initialized = False
                return
            print(f"[Audio] Socket exists: {out}")

            # Ping MPV via socket using printf (same method as _send_mpv_command)
            ping_cmd = f"printf '%s\\n' '{{\"command\":[\"get_property\",\"volume\"]}}' | socat - UNIX-CONNECT:{self.mpv_socket}"
            code, out, err = self._run_ssh(ping_cmd, timeout=5)
            if code == 0 and out:
                print(f"[Audio] Socket test response: {out}")
                self.is_initialized = True
                print("[Audio] ✓ MPV initialized successfully - socket ready and responding")
            else:
                print(f"[Audio] ERROR: Socket exists but not responding: {err}")
                self.is_initialized = False

        except subprocess.TimeoutExpired:
            print("[Audio] ERROR: MPV initialization timeout")
            self.is_initialized = False
        except Exception as e:
            print(f"[Audio] ERROR: Failed to initialize MPV: {e}")
            import traceback
            traceback.print_exc()
            self.is_initialized = False
    
    def _send_mpv_command(self, command_dict, debug=False):
        """
        Send a command to MPV via IPC socket.
        
        Args:
            command_dict: Dictionary containing MPV command
            debug: Print detailed debug info
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            print("[Audio] MPV not initialized")
            return False
        
        try:
            # Convert command to JSON with newline (MPV IPC protocol requires newline)
            json_cmd = json.dumps(command_dict)

            # Use printf to properly handle JSON escaping and ensure newline
            # Escape single quotes in JSON for shell safety
            json_escaped = json_cmd.replace("'", "'\"'\"'")
            socket_cmd = f"printf '%s\\n' '{json_escaped}' | socat - UNIX-CONNECT:{self.mpv_socket}"

            if debug:
                print(f"[Audio DEBUG] Original command dict: {command_dict}")
                print(f"[Audio DEBUG] JSON command: {json_cmd}")
                print(f"[Audio DEBUG] Socket path: {self.mpv_socket}")

            ssh_cmd = self._ssh_base() + [f"{self.sos2_user}@{self.sos2_ip}", socket_cmd]
            
            result = subprocess.run(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            
            stdout_text = result.stdout.decode('utf-8', 'ignore').strip()
            stderr_text = result.stderr.decode('utf-8', 'ignore').strip()
            
            if debug:
                print(f"[Audio DEBUG] Return code: {result.returncode}")
                if stdout_text:
                    print(f"[Audio DEBUG] MPV response: {stdout_text}")
                if stderr_text:
                    print(f"[Audio DEBUG] stderr: {stderr_text}")
            
            if result.returncode != 0:
                if stderr_text:
                    print(f"[Audio] ✗ Command failed: {stderr_text}")
                    # Socket missing — MPV likely crashed; attempt recovery and retry once
                    if "No such file or directory" in stderr_text and self.mpv_socket in stderr_text:
                        print("[Audio] Socket missing — attempting MPV re-initialization...")
                        self.is_initialized = False
                        self._initialize_mpv()
                        if self.is_initialized:
                            print("[Audio] Re-initialized. Retrying command...")
                            retry_result = subprocess.run(
                                ssh_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                timeout=5
                            )
                            if retry_result.returncode == 0:
                                return True
                            else:
                                retry_err = retry_result.stderr.decode('utf-8', 'ignore').strip()
                                print(f"[Audio] ✗ Retry failed: {retry_err}")
                        else:
                            print("[Audio] ✗ Re-initialization failed — audio unavailable")
                else:
                    print(f"[Audio] ✗ Command failed with code {result.returncode}")
                return False
            
            # Check if MPV returned an error in the response
            if stdout_text:
                try:
                    response = json.loads(stdout_text)
                    if response.get('error') != 'success' and 'error' in response:
                        print(f"[Audio] ✗ MPV error: {response.get('error')}")
                        return False
                    elif debug:
                        print(f"[Audio DEBUG] ✓ MPV acknowledged: {response}")
                except json.JSONDecodeError:
                    if debug:
                        print(f"[Audio DEBUG] Non-JSON response: {stdout_text}")
            
            return True
            
        except subprocess.TimeoutExpired:
            print("[Audio] MPV command timeout")
            return False
        except Exception as e:
            print(f"[Audio] Error sending MPV command: {e}")
            return False
    
    def play_audio(self, filename, loop=True, debug=False):
        """
        Play an audio file.
        
        Args:
            filename: Name of audio file (e.g., "air_1.mp3")
            loop: Whether to loop the audio (default: True)
            debug: Print debug info (default: False)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            print("[Audio] Cannot play: MPV not initialized")
            return False
        
        full_path = f"{self.audio_path}/{filename}"

        if debug:
            print(f"[Audio] Attempting to play: {full_path}")
        
        # Build loadfile command
        command = {
            "command": ["loadfile", full_path, "replace"]
        }
        
        success = self._send_mpv_command(command, debug=debug)
        
        if success:
            self.current_track = filename
            print(f"[Audio] ✓ Playing: {filename}")
            
            # Set loop mode if requested
            if loop:
                time.sleep(0.2)  # Give loadfile time to process
                loop_cmd = {"command": ["set_property", "loop-file", "inf"]}
                loop_success = self._send_mpv_command(loop_cmd, debug=debug)
                if loop_success:
                    print(f"[Audio] ✓ Loop mode enabled")
                else:
                    print(f"[Audio] ⚠ Warning: Could not enable loop mode")
        else:
            print(f"[Audio] ✗ Failed to load: {filename}")
        
        return success
    
    def stop_audio(self):
        """Stop audio playback."""
        if not self.is_initialized:
            return False
        
        command = {"command": ["stop"]}
        success = self._send_mpv_command(command)
        
        if success:
            self.current_track = None
            print("[Audio] ✓ Stopped playback")
        else:
            print("[Audio] ✗ Failed to stop playback")
        
        return success
    
    def fade_out(self, duration=None):
        """
        Fade out current audio over specified duration.
        
        Args:
            duration: Fade duration in seconds (uses default if None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized or not self.current_track:
            return False
        
        fade_time = duration if duration is not None else self.fade_duration
        
        try:
            # Get current volume
            steps = 10
            step_duration = fade_time / steps
            
            for i in range(steps, -1, -1):
                volume = int((i / steps) * 100)  # Fade from 100 to 0
                cmd = {"command": ["set_property", "volume", volume]}
                self._send_mpv_command(cmd)
                time.sleep(step_duration)
            
            # Stop after fade
            self.stop_audio()
            
            # Reset volume
            time.sleep(0.1)
            reset_cmd = {"command": ["set_property", "volume", 100]}
            self._send_mpv_command(reset_cmd)
            
            print(f"[Audio] Faded out over {fade_time}s")
            return True
            
        except Exception as e:
            print(f"[Audio] Fade out error: {e}")
            return False
    
    def set_volume(self, volume_level):
        """
        Set playback volume.
        
        Args:
            volume_level: Volume level (0-100)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            return False
        
        # Clamp volume to valid range
        volume = max(0, min(100, int(volume_level)))
        
        command = {"command": ["set_property", "volume", volume]}
        success = self._send_mpv_command(command)
        
        if success:
            print(f"[Audio] ✓ Volume set to {volume}%")
        else:
            print(f"[Audio] ✗ Failed to set volume")
        
        return success
    
    def get_volume(self):
        """
        Get current playback volume from MPV.

        Returns:
            int: Current volume (0-100) or None if failed
        """
        if not self.is_initialized:
            return None

        try:
            json_cmd = json.dumps({"command": ["get_property", "volume"]})
            json_escaped = json_cmd.replace("'", "'\"'\"'")
            socket_cmd = f"printf '%s\\n' '{json_escaped}' | socat - UNIX-CONNECT:{self.mpv_socket}"
            ssh_cmd = self._ssh_base() + [f"{self.sos2_user}@{self.sos2_ip}", socket_cmd]

            result = subprocess.run(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )

            if result.returncode == 0 and result.stdout:
                response = json.loads(result.stdout.decode('utf-8', 'ignore').strip())
                volume = response.get('data')
                if volume is not None:
                    return int(volume)

            return None

        except Exception as e:
            print(f"[Audio] Failed to get volume: {e}")
            return None
    
    def adjust_volume(self, delta):
        """
        Adjust volume by delta amount.
        
        Args:
            delta: Amount to adjust (positive or negative)
            
        Returns:
            bool: True if successful, False otherwise
        """
        current = self.get_volume()
        if current is None:
            return False
        
        new_volume = max(0, min(100, current + delta))
        return self.set_volume(new_volume)
    
    def mute(self):
        """
        Mute audio playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            return False
        
        command = {"command": ["set_property", "mute", True]}
        success = self._send_mpv_command(command)
        
        if success:
            print("[Audio] ✓ Muted")
        else:
            print("[Audio] ✗ Failed to mute")
        
        return success
    
    def unmute(self):
        """
        Unmute audio playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            return False
        
        command = {"command": ["set_property", "mute", False]}
        success = self._send_mpv_command(command)
        
        if success:
            print("[Audio] ✓ Unmuted")
        else:
            print("[Audio] ✗ Failed to unmute")
        
        return success
    
    def toggle_mute(self):
        """
        Toggle mute state.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            return False
        
        command = {"command": ["cycle", "mute"]}
        success = self._send_mpv_command(command)
        
        if success:
            print("[Audio] ✓ Mute toggled")
        else:
            print("[Audio] ✗ Failed to toggle mute")
        
        return success
    
    def get_current_track(self):
        """
        Get the currently playing track filename.
        
        Returns:
            str: Current track filename or None
        """
        return self.current_track
    
    def is_playing(self):
        """
        Check if audio is currently playing.
        
        Returns:
            bool: True if playing, False otherwise
        """
        return self.current_track is not None
    
    def close(self):
        """Cleanup and close MPV."""
        print("[Audio] Closing MPV...")

        # Try to quit MPV gracefully via socket
        if self.is_initialized:
            quit_cmd = {"command": ["quit"]}
            self._send_mpv_command(quit_cmd)
            time.sleep(0.5)

        # Force-kill MPV on SOS2 as a safety net (covers crashed/unresponsive socket)
        try:
            self._run_ssh(
                f"pkill -f 'input-ipc-server={self.mpv_socket}' ; rm -f {self.mpv_socket}",
                timeout=5, capture=False
            )
            print("[Audio] MPV process killed on SOS2")
        except Exception as e:
            print(f"[Audio] Warning: force-kill failed: {e}")

        self.is_initialized = False
        print("[Audio] Closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except:
            pass
