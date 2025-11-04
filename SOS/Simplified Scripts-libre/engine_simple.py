"""
Simplified SOS LibreOffice Impress Engine
Connects to nowPlaying socket and controls LibreOffice Impress slides based on clip names.
"""

import socket
import time

NOW_PORT = 65432


class SimplePPEngine:
    """Simplified LibreOffice Impress engine for SOS integration."""
    
    def __init__(self, pp, pp_dictionary):
        """
        Initialize the engine.
        
        Args:
            pp: LibreOffice Impress controller object
            pp_dictionary: Dict mapping clip names to slide numbers
        """
        self.pp = pp
        self.pp_dictionary = pp_dictionary
        self.running = True
        self.current_slide = -1
    
    def connect_to_nowplaying(self, timeout=4, max_retries=None):
        """
        Connect to the nowPlaying socket.
        
        Args:
            timeout: Socket timeout in seconds
            max_retries: Maximum connection attempts (None for infinite)
            
        Returns:
            tuple: (success, socket) - socket is None if connection fails
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        attempt = 0
        while self.running:
            try:
                sock.connect(("localhost", NOW_PORT))
                print("Connected to nowPlaying")
                return (True, sock)
            except socket.error as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                time.sleep(2)
                attempt += 1
                
                if max_retries and attempt >= max_retries:
                    return (False, None)
        
        return (False, None)
    
    def get_clip_name(self, sock):
        """
        Read the current clip name from the nowPlaying socket.
        
        Args:
            sock: Connected socket
            
        Returns:
            tuple: (success, clip_name)
        """
        try:
            data = sock.recv(1024).decode("utf-8", "ignore")
            clip_name = data.strip()
            return (True, clip_name)
        except Exception as e:
            print(f"Error reading clip name: {e}")
            return (False, "")
    
    def get_slide_numbers(self, clip_name):
        """
        Map clip name to slide number(s).
        
        Args:
            clip_name: Name of the current clip
            
        Returns:
            list: List of slide numbers (defaults to [1] if not found)
        """
        if clip_name.strip() in self.pp_dictionary:
            return self.pp_dictionary[clip_name.strip()]
        return [1]
    
    def run(self, poll_interval=2):
        """
        Main engine loop.
        
        Args:
            poll_interval: Time between checks in seconds
        """
        print("Starting LibreOffice Impress Engine...")
        
        # Launch LibreOffice Impress first
        try:
            self.pp.launchpp(RunShow=True)
            print("LibreOffice Impress slideshow started")
        except Exception as e:
            print(f"Failed to launch LibreOffice Impress: {e}")
            print("\nDEBUG INFO:")
            import traceback
            traceback.print_exc()
            return
        
        # Connect to nowPlaying
        print("\nConnecting to nowPlaying socket...")
        success, sock = self.connect_to_nowplaying()
        if not success:
            print("Failed to connect to nowPlaying. Exiting.")
            self.pp.close()
            return
        
        # Main loop
        print("Engine running...")
        print("Monitoring nowPlaying for clip changes...")
        print("Note: Slide navigation uses keyboard simulation (limited programmatic control)")
        
        while self.running:
            time.sleep(poll_interval)
            
            # Get current clip name
            success, clip_name = self.get_clip_name(sock)
            
            if not success:
                print("Connection lost. Returning to slide 1.")
                self.pp.goto(1)
                self.current_slide = 1
                sock.close()
                
                # Try to reconnect
                success, sock = self.connect_to_nowplaying()
                if not success:
                    break
                continue
            
            # Get slide numbers for this clip
            slide_nums = self.get_slide_numbers(clip_name)
            
            # Navigate to slide if different
            if self.current_slide not in slide_nums:
                target_slide = slide_nums[0]
                print(f"Clip: '{clip_name}' -> Slide {target_slide}")
                self.pp.goto(target_slide)
                self.current_slide = target_slide
        
        # Cleanup
        sock.close()
        self.pp.close()
        print("Engine stopped")
    
    def stop(self):
        """Stop the engine."""
        self.running = False
