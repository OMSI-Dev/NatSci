"""
Simplified SOS LibreOffice Impress Engine
Connects to SOS server and controls LibreOffice Impress slides based on clip names.
"""

import socket
import time


class SimplePPEngine:
    """Simplified LibreOffice Impress engine for SOS integration."""
    
    def __init__(self, pp, pp_dictionary, sos_ip, sos_port):
        """
        Initialize the engine.
        
        Args:
            pp: LibreOffice Impress controller object
            pp_dictionary: Dict mapping clip names to slide numbers
            sos_ip: IP address of SOS server
            sos_port: Port number of SOS server
        """
        self.pp = pp
        self.pp_dictionary = pp_dictionary
        self.sos_ip = sos_ip
        self.sos_port = sos_port
        self.running = True
        self.current_slide = -1
        self.sock = None
    
    def connect_to_sos(self, timeout=4):
        """
        Connect to the SOS server and send enable handshake.
        
        Args:
            timeout: Socket timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            
            print(f"Connecting to SOS at {self.sos_ip}:{self.sos_port}...")
            self.sock.connect((self.sos_ip, self.sos_port))
            print("✓ Connected to SOS server")
            
            # Send enable handshake
            print("Sending handshake...")
            self.sock.sendall(b'enable\n')
            
            # Wait for response
            data = self.sock.recv(1024)
            response = data.decode('utf-8', 'ignore').strip()
            print(f"Handshake response: {repr(response)}")
            
            if response == 'R':
                print("✓ Handshake successful")
                return True
            else:
                print(f"⚠ Unexpected handshake response: {response}")
                # Continue anyway - some SOS versions respond differently
                return True
                
        except socket.error as e:
            print(f"✗ Failed to connect to SOS: {e}")
            return False
        except Exception as e:
            print(f"✗ Error during SOS connection: {e}")
            return False
    
    def get_current_clip_info(self):
        """
        Get current clip information from SOS server.
        
        Returns:
            tuple: (success, clip_name)
        """
        if not self.sock:
            return (False, "")
        
        try:
            # Request current clip number
            self.sock.sendall(b'get_clip_number\n')
            
            # Receive response
            data = self.sock.recv(1024)
            clip_number = data.decode('utf-8', 'ignore').strip()
            
            if not clip_number or not clip_number.isdigit():
                return (False, "")
            
            # Request clip info
            cmd = f"get_clip_info {clip_number}\n".encode('utf-8')
            self.sock.sendall(cmd)
            
            # Receive clip info
            data = self.sock.recv(2048)
            clip_name = data.decode('utf-8', 'ignore').strip()
            
            return (True, clip_name)
            
        except socket.timeout:
            return (False, "")
        except socket.error as e:
            print(f"Socket error: {e}")
            return (False, "")
        except Exception as e:
            print(f"Error getting clip info: {e}")
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
        
        # Connect to SOS
        print(f"\nConnecting to SOS server...")
        if not self.connect_to_sos():
            print("Failed to connect to SOS. Exiting.")
            self.pp.close()
            return
        
        # Main loop
        print("\nEngine running...")
        print("Monitoring SOS for clip changes...")
        print("Note: Slide navigation uses keyboard simulation")
        
        last_clip = ""
        while self.running:
            time.sleep(poll_interval)
            
            # Get current clip info from SOS
            success, clip_name = self.get_current_clip_info()
            
            if not success:
                # Connection issue - try to reconnect
                print("Lost connection to SOS, attempting to reconnect...")
                if self.sock:
                    try:
                        self.sock.close()
                    except:
                        pass
                if not self.connect_to_sos():
                    print("Reconnection failed. Exiting.")
                    break
                continue
            
            # Only process if clip changed
            if clip_name and clip_name != last_clip:
                last_clip = clip_name
                
                # Get slide numbers for this clip
                slide_nums = self.get_slide_numbers(clip_name)
                
                # Navigate to slide if different
                if self.current_slide not in slide_nums:
                    target_slide = slide_nums[0]
                    print(f"Clip: '{clip_name}' -> Slide {target_slide}")
                    self.pp.goto(target_slide)
                    self.current_slide = target_slide
        
        # Cleanup
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.pp.close()
        print("Engine stopped")
    
    def stop(self):
        """Stop the engine."""
        self.running = False
