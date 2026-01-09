"""
Simplified SOS LibreOffice Impress Controller
Main entry point for the SOS-LibreOffice Impress integration system.
"""

import sys
import threading
import time
from parsers import parseConfig, parseSlideNames
from ppAccess import PowerPointShowController
from engine import SimplePPEngine


DEFAULT_CONFIG = r"C:\OMSI\App\SOS\config.txt"


class CommandController(threading.Thread):
    """Thread to handle user command input during playback."""
    
    def __init__(self, engine):
        threading.Thread.__init__(self)
        self.engine = engine
        self.daemon = True
    
    def run(self):
        time.sleep(2)
        self.print_help()
        
        while True:
            try:
                user_input = input("\n[Command] > ").strip().lower()
                
                if not user_input:
                    continue
                
                if user_input in ['q', 'quit', 'exit']:
                    print("Stopping engine...")
                    self.engine.stop()
                    break
                
                elif user_input in ['n', 'next']:
                    self.engine.next_clip()
                
                elif user_input in ['p', 'prev', 'previous']:
                    self.engine.prev_clip()
                
                elif user_input in ['r', 'restart']:
                    self.engine.restart_current_clip()
                
                elif user_input in ['h', 'help', '?']:
                    self.print_help()
                
                else:
                    print(f"Unknown command: '{user_input}'. Type 'h' for help.")
                    
            except EOFError:
                # Handle Ctrl+D or input stream closing
                break
            except Exception as e:
                print(f"Error processing command: {e}")
    
    def print_help(self):
        """Print available commands."""
        print("\n" + "=" * 60)
        print("Available Commands:")
        print("=" * 60)
        print("  n, next      - Skip to next clip")
        print("  p, prev      - Go to previous clip")
        print("  r, restart   - Restart current clip")
        print("  h, help      - Show this help message")
        print("  q, quit      - Exit the program")
        print("=" * 60)


def load_config(config_path=None):
    """
    Load and parse configuration file.
    
    Args:
        config_path: Path to config file (uses DEFAULT_CONFIG if None)
        
    Returns:
        dict: Configuration dictionary or None on failure
    """
    if not config_path:
        config_path = DEFAULT_CONFIG
    
    print(f"Loading config from: {config_path}")
    success, config_dict = parseConfig(config_path)
    
    if not success:
        print("ERROR: Failed to parse config file")
        return None
    
    return config_dict


def load_slide_mapping(database_path):
    """
    Load slide mapping from CSV file.
    
    Args:
        database_path: Path to CSV database file containing clip-to-slide mappings
        
    Returns:
        dict: Mapping of clip names to slide numbers, or None on failure
    """
    print(f"Loading slide mappings from: {database_path}")
    success, pp_dictionary = parseSlideNames(database_path)
    
    if not success:
        print("ERROR: Failed to parse database file")
        return None
    
    print(f"Loaded {len(pp_dictionary)} clip-to-slide mappings")
    return pp_dictionary


def main():
    """Main entry point for the SOS LibreOffice Impress controller."""
    
    print("=" * 60)
    print("SOS LibreOffice Impress Controller - Simplified Version")
    print("=" * 60)
    
    config = load_config()
    if not config:
        sys.exit(1)
    
    slideshow_path = config["default_path"] + config["default_name"] + ".odp"
    database_path = config["default_path"] + config["default_name"] + ".csv"
    
    print(f"\nSlideshow: {slideshow_path}")
    print(f"Database:  {database_path}")
    
    pp_dictionary = load_slide_mapping(database_path)
    if not pp_dictionary:
        sys.exit(1)
    
    print("\nInitializing LibreOffice Impress controller...")
    pp = PowerPointShowController(slideshow_path)
    
    # Initialize engine with SOS connection info
    print("Initializing engine...")
    engine = SimplePPEngine(
        pp, 
        pp_dictionary, 
        config["sos_ip"], 
        config["port"]
    )
    
    # Start command controller thread
    command_thread = CommandController(engine)
    command_thread.start()
    
    # Run engine (blocking)
    print("\nStarting engine...\n")
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt detected")
        engine.stop()
    except Exception as e:
        print(f"\nERROR: {e}")
        engine.stop()
    
    # Cleanup
    print("\nCleaning up...")
    time.sleep(1)
    pp.close()
    print("Done!")


if __name__ == "__main__":
    main()
