"""
SOS2 Engine
Connects to SOS server and controls LibreOffice Impress slides based on clip names.
"""

import socket
import time
import sys

SOS_IP = "10.10.51.98"
SOS_PORT = 2468

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


class SimplePPEngine:
    """
    Primary engine:
    - Connects to SOS server
    - Slide navigation for LibreOffice based on clip names
    """
    
    def __init__(self, pp, slide_dictionary, playlist_metadata):
        """
        Initialize the engine.
        
        Args:
            pp: LibreOffice Impress controller object (from pp_access.py)
            slide_dictionary: Dict mapping clip names to slide numbers
            playlist_metadata: Playlist metadata from SOS server (cached or fetched)
        """
        self.pp = pp
        self.slide_dictionary = slide_dictionary
        self.playlist_metadata = playlist_metadata
        self.running = True
        self.current_slide = -1
        self.sock = None
        
        # print(f"[Engine] Initialized with {len(slide_dictionary)} clip mappings")
        if playlist_metadata:
            pass
            # print(f"[Engine] Playlist: {playlist_metadata.get('name', 'Unknown')}")
    
    def connect_to_sos(self, timeout=4):
        """
        Connect to SOS server.
        
        Args:
            timeout: Socket timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            
            self.sock.connect((SOS_IP, SOS_PORT))
            print(f"[Engine] Connected to SOS at {SOS_IP}:{SOS_PORT}")
            
            # Send enable handshake
            self.sock.sendall(b'enable\n')
            data = self.sock.recv(1024)
            
            return True
                
        except socket.error as e:
            print(f"Failed to connect to SOS: {e}")
            return False
        except Exception as e:
            print(f"Error during SOS connection: {e}")
            return False
    
    def next_clip(self):
        """Skip to the next clip in the playlist."""
        if not self.sock:
            return False
        
        try:
            self.sock.sendall(b'next_clip\n')
            time.sleep(0.2)
            
            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            return True
            
        except socket.error as e:
            print(f"[Engine] Error sending next_clip: {e}")
            return False
    
    def prev_clip(self):
        """Go back to the previous clip in the playlist."""
        if not self.sock:
            return False
        
        try:
            self.sock.sendall(b'prev_clip\n')
            time.sleep(0.2)
            
            try:
                self.sock.recv(1024)
            except socket.timeout:
                pass
            
            return True
            
        except socket.error as e:
            print(f"[Engine] Error sending prev_clip: {e}")
            return False
    
    def get_current_clip_name(self):
        """
        Get the currently playing clip name from SOS.
        Uses cached playlist metadata for efficiency.
        
        Returns:
            str: Clip name or None on failure
        """
        if not self.sock:
            return None
        
        try:
            # Step 1: Get current clip number
            self.sock.sendall(b'get_clip_number\n')
            data = self.sock.recv(1024)
            clip_number_str = data.decode('utf-8', 'ignore').strip()
            
            if not clip_number_str or not clip_number_str.isdigit():
                return None
            
            clip_number = int(clip_number_str)
            
            # Step 2: Look up clip name from cached playlist metadata
            if self.playlist_metadata and 'clips' in self.playlist_metadata:
                clips = self.playlist_metadata['clips']
                if 0 < clip_number <= len(clips):
                    clip_name = clips[clip_number - 1].get('name', '')
                    return clip_name if clip_name else None
            
            return None
            
        except socket.timeout:
            return None
        except socket.error:
            return None
        except Exception:
            return None
    
    def navigate_to_clip(self, clip_name):
        """
        Navigate to the slide(s) associated with the given clip name.
        
        Args:
            clip_name: Name of the clip to navigate to
        """
        if clip_name not in self.slide_dictionary:
            print(f"[Engine] Warning: No slide mapping for '{clip_name}'")
            return
        
        slide_numbers = self.slide_dictionary[clip_name]
        
        if not slide_numbers:
            return
        
        # Navigate to first slide in the list
        target_slide = slide_numbers[0]
        
        if target_slide != self.current_slide:
            self.pp.goto(target_slide)
            self.current_slide = target_slide
    
    def run(self):
        """Main engine loop - monitors SOS and updates slides."""
        # Connect to SOS
        if not self.connect_to_sos():
            print("[Engine] ERROR: Failed to connect to SOS")
            return
        
        print("[Engine] Monitoring for clip changes...\n")
        
        last_clip_name = None
        
        try:
            while self.running:
                clip_name = self.get_current_clip_name()
                
                if clip_name and clip_name != last_clip_name:
                    print(f"[Clip] {clip_name}")
                    self.navigate_to_clip(clip_name)
                    last_clip_name = clip_name
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n[Engine] Keyboard interrupt detected")
        except Exception as e:
            print(f"[Engine] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()
    
    def stop(self):
        """Stop the engine and cleanup connections."""
        self.running = False
        
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            finally:
                self.sock = None
        
        print("[Engine] Stopped")
