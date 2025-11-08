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


class ExitController(threading.Thread):
    """Simple thread to handle user exit input."""
    
    def __init__(self, engine):
        threading.Thread.__init__(self)
        self.engine = engine
        self.daemon = True
    
    def run(self):
        time.sleep(2)
        while True:
            user_input = input("\nPress 'q' to quit: ")
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("Stopping engine...")
                self.engine.stop()
                break


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


def load_database(database_path):
    """
    Load and parse slide database.
    
    Args:
        database_path: Path to CSV database file
        
    Returns:
        tuple: (pp_dictionary, clip_metadata) or (None, None) on failure
            pp_dictionary: Mapping of clip names to slide numbers
            clip_metadata: Dict with clip names as keys, containing caption paths, etc.
    """
    print(f"Loading database from: {database_path}")
    success, pp_dictionary = parseSlideNames(database_path)
    
    if not success:
        print("ERROR: Failed to parse database file")
        return None, None
    
    print(f"Loaded {len(pp_dictionary)} clip-to-slide mappings")
    
    # Try to load subtitle metadata if available
    # The merged CSV should have a 'caption' column with paths to .srt files
    clip_metadata = {}
    try:
        import csv
        with open(database_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Get clip name - prefer 'name', fallback to 'pretty_name'
                clip_name = row.get('name', '').strip()
                if not clip_name:
                    clip_name = row.get('pretty_name', '').strip()
                
                caption_path = row.get('caption', '').strip()
                
                if clip_name:
                    clip_metadata[clip_name] = {
                        'caption': caption_path,
                        'pretty_name': row.get('pretty_name', ''),
                        'category': row.get('category', ''),
                        'path': row.get('path', ''),
                    }
        
        # Count clips with captions
        with_captions = sum(1 for meta in clip_metadata.values() if meta.get('caption'))
        if with_captions > 0:
            print(f"✓ Found caption metadata for {with_captions} clips")
        else:
            print("ℹ No caption paths found in database")
            
    except Exception as e:
        print(f"Warning: Could not load caption metadata: {e}")
        # Continue without metadata - subtitles will be disabled
    
    return pp_dictionary, clip_metadata


def main():
    """Main entry point for the SOS LibreOffice Impress controller."""
    
    print("=" * 60)
    print("SOS LibreOffice Impress Controller - Simplified Version")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    if not config:
        sys.exit(1)
    
    # Build file paths
    # Support multiple presentation formats (.odp for LibreOffice, .ppt, .pptx)
    slideshow_path = config["default_path"] + config["default_name"] + ".odp"
    database_path = config["default_path"] + config["default_name"] + ".csv"
    
    print(f"\nSlideshow: {slideshow_path}")
    print(f"Database:  {database_path}")
    
    # Load database (now returns both dictionary and metadata)
    pp_dictionary, clip_metadata = load_database(database_path)
    if not pp_dictionary:
        sys.exit(1)
    
    # Initialize LibreOffice Impress controller
    print("\nInitializing LibreOffice Impress controller...")
    pp = PowerPointShowController(slideshow_path)
    
    # Initialize engine with SOS connection info and subtitle metadata
    print("Initializing engine with subtitle support and GUI overlay...")
    # Note: Default SOS user is 'sosdemo', update if different
    # Password can be passed as 5th parameter if needed
    engine = SimplePPEngine(
        pp, 
        pp_dictionary, 
        config["sos_ip"], 
        config["port"], 
        clip_metadata,
        sos_user='sosdemo',        # Update if your SOS server uses different username
        sos_password=None,         # Set password here if needed, or None for SSH key auth
        use_gui_overlay=True,      # Set to False to use terminal display instead
        overlay_position='bottom'  # Options: 'bottom', 'top', 'bottom-right', 'top-right'
    )
    
    # Start exit controller thread
    exit_thread = ExitController(engine)
    exit_thread.start()
    
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
