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
    
    def __init__(self, sos2_ip="10.10.51.98", sos2_user="sos", audio_path="/opt/share/AuxShare/audio"):
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
        
        found_keys = [k for k in key_locations if os.path.exists(k)]
        return found_keys
    
    def _test_ssh_connection(self):
        """Test basic SSH connectivity to SOS2."""
        try:
            ssh_base = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "BatchMode=yes",
                "-o", "PasswordAuthentication=no",
                "-o", "ConnectTimeout=5"
            ]
            
            found_keys = self._find_ssh_keys()
            if found_keys:
                ssh_base += ["-i", found_keys[0]]
                print(f"[Audio] Using SSH key: {found_keys[0]}")
            else:
                print("[Audio] WARNING: No SSH keys found")
            
            test_cmd = ssh_base + [f"{self.sos2_user}@{self.sos2_ip}", "echo 'SSH_OK'"]
            
            result = subprocess.run(
                test_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"[Audio] SSH connection to {self.sos2_ip} successful")
                return True
            else:
                error = result.stderr.decode('utf-8', 'ignore').strip()
                print(f"[Audio] SSH connection failed: {error}")
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
            ssh_base = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "BatchMode=yes",
                "-o", "PasswordAuthentication=no"
            ]
            
            found_keys = self._find_ssh_keys()
            if found_keys:
                ssh_base += ["-i", found_keys[0]]
            
            check_socat = ssh_base + [f"{self.sos2_user}@{self.sos2_ip}", "which socat"]
            result = subprocess.run(check_socat, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            
            if result.returncode != 0:
                print("[Audio] ERROR: socat not found on SOS2. Install with: sudo apt-get install socat")
                self.is_initialized = False
                return
            else:
                print("[Audio] socat found")
            
            # Kill any existing MPV instances on the socket
            print("[Audio] Cleaning up old MPV instances...")
            cleanup_cmd = ssh_base + [f"{self.sos2_user}@{self.sos2_ip}", 
                                      f"pkill -f 'input-ipc-server={self.mpv_socket}' ; rm -f {self.mpv_socket}"]
            subprocess.run(cleanup_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            time.sleep(1)
            
            # MPV command with IPC socket, idle mode, and no video
            mpv_cmd = (
                f"nohup mpv --idle=yes --no-video --volume=50 "
                f"--input-ipc-server={self.mpv_socket} "
                f"--really-quiet > /dev/null 2>&1 &"
            )
            
            print(f"[Audio] Starting MPV with command: {mpv_cmd}")
            ssh_cmd = ssh_base + [f"{self.sos2_user}@{self.sos2_ip}", mpv_cmd]
            
            # Launch MPV in background
            result = subprocess.run(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            if result.returncode != 0:
                error = result.stderr.decode('utf-8', 'ignore').strip()
                print(f"[Audio] MPV launch failed: {error}")
                self.is_initialized = False
                return
            
            # Give MPV time to start and create socket
            print("[Audio] Waiting for MPV to initialize...")
            time.sleep(3)
            
            # Verify socket exists
            check_socket = ssh_base + [f"{self.sos2_user}@{self.sos2_ip}", f"test -S {self.mpv_socket} && echo 'SOCKET_OK'"]
            result = subprocess.run(check_socket, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            
            if result.returncode == 0 and b'SOCKET_OK' in result.stdout:
                self.is_initialized = True
                print("[Audio] MPV initialized successfully - socket ready")
            else:
                print(f"[Audio] ERROR: MPV socket not found at {self.mpv_socket}")
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
            # Build SSH command to send JSON to socket
            ssh_base = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "BatchMode=yes",
                "-o", "PasswordAuthentication=no"
            ]
            
            found_keys = self._find_ssh_keys()
            if found_keys:
                ssh_base += ["-i", found_keys[0]]
            
            # Convert command to JSON with newline (MPV requires this)
            json_cmd = json.dumps(command_dict)
            
            # Use UNIX socket connection via socat
            socket_cmd = f"echo '{json_cmd}' | socat - UNIX-CONNECT:{self.mpv_socket}"
            
            if debug:
                print(f"[Audio DEBUG] Sending command: {json_cmd}")
                print(f"[Audio DEBUG] Socket command: {socket_cmd}")
            
            ssh_cmd = ssh_base + [f"{self.sos2_user}@{self.sos2_ip}", socket_cmd]
            
            result = subprocess.run(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            
            if debug:
                print(f"[Audio DEBUG] Return code: {result.returncode}")
                if result.stdout:
                    print(f"[Audio DEBUG] stdout: {result.stdout.decode('utf-8', 'ignore').strip()}")
                if result.stderr:
                    print(f"[Audio DEBUG] stderr: {result.stderr.decode('utf-8', 'ignore').strip()}")
            
            if result.returncode != 0:
                error = result.stderr.decode('utf-8', 'ignore').strip()
                if error:
                    print(f"[Audio] Command error: {error}")
                return False
            
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
        
        full_path = os.path.join(self.audio_path, filename)
        
        if debug:
            print(f"[Audio] Attempting to play: {full_path}")
        
        # Build loadfile command
        command = {
            "command": ["loadfile", full_path, "replace"]
        }
        
        success = self._send_mpv_command(command, debug=debug)
        
        if success:
            self.current_track = filename
            if debug:
                print(f"[Audio] Successfully loaded: {filename}")
            
            # Set loop mode if requested
            if loop:
                time.sleep(0.2)  # Give loadfile time to process
                loop_cmd = {"command": ["set_property", "loop-file", "inf"]}
                loop_success = self._send_mpv_command(loop_cmd)
                if loop_success and debug:
                    print(f"[Audio] Loop mode enabled")
        else:
            print(f"[Audio] Failed to load: {filename}")
        
        return success
    
    def stop_audio(self):
        """Stop audio playback."""
        if not self.is_initialized:
            return False
        
        command = {"command": ["stop"]}
        success = self._send_mpv_command(command)
        
        if success:
            self.current_track = None
            print("[Audio] Stopped playback")
        
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
                volume = int((i / steps) * 50)  # Fade from 50 to 0
                cmd = {"command": ["set_property", "volume", volume]}
                self._send_mpv_command(cmd)
                time.sleep(step_duration)
            
            # Stop after fade
            self.stop_audio()
            
            # Reset volume
            time.sleep(0.1)
            reset_cmd = {"command": ["set_property", "volume", 50]}
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
            print(f"[Audio] Volume set to {volume}")
        
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
        
        # Try to quit MPV gracefully
        if self.is_initialized:
            quit_cmd = {"command": ["quit"]}
            self._send_mpv_command(quit_cmd)
            time.sleep(1)
        
        # Kill SSH process if still running
        if self.ssh_process and self.ssh_process.poll() is None:
            try:
                self.ssh_process.terminate()
                self.ssh_process.wait(timeout=5)
            except:
                self.ssh_process.kill()
        
        self.is_initialized = False
        print("[Audio] Closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except:
            pass
