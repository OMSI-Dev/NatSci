"""
SOS2 Engine
Connects to SOS server and controls LibreOffice Impress via CacheManager lookups.
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
    Optimized Engine:
    - Connects to SOS server
    - Gets clip NUMBER from SOS
    - Gets clip NAME from local CacheManager (no socket usage)
    - Navigates LibreOffice
    """
    
    def __init__(self, pp, slide_dictionary, cache_manager):
        """
        Initialize the engine.
        
        Args:
            pp: LibreOffice Impress controller object
            slide_dictionary: Dict mapping clip names to slide numbers
            cache_manager: Initialized CacheManager instance
        """
        self.pp = pp
        self.slide_dictionary = slide_dictionary
        self.cache_manager = cache_manager
        self.running = True
        self.current_slide = -1
        self.sock = None
        
        print(f"[Engine] Initialized with CacheManager")
    
    def connect_to_sos(self, timeout=4):
        """Connect to SOS server."""
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
    
    def get_current_clip_info(self):
        """
        Get current clip info optimized for caching.
        1. Fetch only clip NUMBER from socket (fastest operation).
        2. Lookup Name in CacheManager (0ms).
        """
        if not self.sock:
            return None, None
        
        try:
            # 1: Get current clip number
            self.sock.sendall(b'get_clip_number\n')
            data = self.sock.recv(1024)
            clip_number_str = data.decode('utf-8', 'ignore').strip()
            
            if not clip_number_str or not clip_number_str.isdigit():
                return None, None
            
            clip_number = int(clip_number_str)
            
            # 2: Use CacheManager for name lookup (No Socket Call!)
            
            clip_name = None
            if self.cache_manager.current_playlist:
                clips = self.cache_manager.current_playlist.get('clips', [])
                if 0 < clip_number <= len(clips):
                    clip_name = clips[clip_number - 1].get('name')
            
            return clip_number, clip_name
            
        except socket.timeout:
            return None, None
        except socket.error:
            return None, None
        except Exception as e:
            print(f"Error getting clip info: {e}")
            return None, None

    def navigate_to_clip(self, clip_name):
        """Navigate to the slide(s) associated with the given clip name."""
        if clip_name not in self.slide_dictionary:
            # print(f"[Engine] Warning: No slide mapping for '{clip_name}'")
            return
        
        slide_numbers = self.slide_dictionary[clip_name]
        if not slide_numbers:
            return
        
        target_slide = slide_numbers[0]
        
        if target_slide != self.current_slide:
            print(f"[Engine] Navigating to Slide {target_slide} for '{clip_name}'")
            self.pp.goto(target_slide)
            self.current_slide = target_slide
    
    def run(self):
        """Main engine loop."""
        if not self.connect_to_sos():
            print("[Engine] ERROR: Failed to connect to SOS")
            return
        
        print("[Engine] Monitoring for clip changes...\n")
        
        last_clip_number = -1
        
        try:
            while self.running:
                clip_number, clip_name = self.get_current_clip_info()
                
                if clip_number and clip_number != last_clip_number:
                    if clip_name:
                        print(f"\n[Clip {clip_number}] {clip_name}")
                        self.navigate_to_clip(clip_name)
                    else:
                        print(f"\n[Clip {clip_number}] Unknown Name")
                    
                    last_clip_number = clip_number
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n[Engine] Keyboard interrupt")
        except Exception as e:
            print(f"[Engine] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()
    
    def stop(self):
        """Stop the engine."""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        print("[Engine] Stopped")
