"""
Example integration of dataset cache into engine.py

This shows how to modify your SimplePPEngine to use the dataset cache
to detect movies and display captions.
"""

# Add to top of engine.py imports:
from dataset_cache_loader import DatasetCache

# Modify SimplePPEngine.__init__:
def __init__(self, pp, pp_dictionary, sos_ip, sos_port, dataset_cache_file=None):
    """
    Initialize the engine.
    
    Args:
        pp: LibreOffice Impress controller object
        pp_dictionary: Dict mapping clip names to slide numbers
        sos_ip: IP address of SOS server
        sos_port: Port number of SOS server
        dataset_cache_file: Path to dataset_cache.json (optional)
    """
    self.pp = pp
    self.pp_dictionary = pp_dictionary
    self.sos_ip = sos_ip
    self.sos_port = sos_port
    self.running = True
    self.current_slide = -1
    self.sock = None
    
    # Load dataset cache
    self.dataset_cache = None
    if dataset_cache_file:
        try:
            self.dataset_cache = DatasetCache(dataset_cache_file)
        except Exception as e:
            print(f"Warning: Could not load dataset cache: {e}")

# Add new method to SimplePPEngine:
def handle_movie_clip(self, clip_name):
    """
    Handle special processing for movie clips (e.g., display captions).
    
    Args:
        clip_name: Name of the current clip
    """
    if not self.dataset_cache:
        return
    
    # Check if this is a movie
    if self.dataset_cache.is_movie(clip_name):
        print(f"  → Movie detected!")
        
        # Check for captions
        if self.dataset_cache.has_captions(clip_name):
            srt_path = self.dataset_cache.get_srt_path(clip_name)
            print(f"  → Captions available: {srt_path}")
            
            # TODO: Add your caption display logic here
            # For example:
            # - Parse the SRT file
            # - Display captions on a secondary screen
            # - Send to a caption display system
            
        else:
            print(f"  → No captions available")

# Modify the main loop in SimplePPEngine.run():
# Add this inside the main while loop, after detecting clip change:

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
    
    # Handle movie-specific processing (NEW!)
    self.handle_movie_clip(clip_name)


# Example: Modified sdc_simple.py main() function to pass cache file:

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
    slideshow_path = config["default_path"] + config["default_name"] + ".odp"
    database_path = config["default_path"] + config["default_name"] + ".csv"
    
    # Dataset cache file path (NEW!)
    cache_path = config["default_path"] + "dataset_cache.json"
    
    print(f"\nSlideshow: {slideshow_path}")
    print(f"Database:  {database_path}")
    print(f"Cache:     {cache_path}")
    
    # Load database
    pp_dictionary = load_database(database_path)
    if not pp_dictionary:
        sys.exit(1)
    
    # Initialize LibreOffice Impress controller
    print("\nInitializing LibreOffice Impress controller...")
    pp = PowerPointShowController(slideshow_path)
    
    # Initialize engine with SOS connection info AND cache file (MODIFIED!)
    print("Initializing engine...")
    engine = SimplePPEngine(pp, pp_dictionary, config["sos_ip"], config["port"], cache_path)
    
    # ... rest of main() unchanged ...
