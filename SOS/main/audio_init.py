"""
Audio Initialization Module
Loads audio file mappings and initializes the MPV Audio Controller.
"""

import os
import csv
from audio_access import AudioController
from config import get_config

# Load configuration
config = get_config()

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

# Get paths from configuration
base_share = config.get('paths.audio_dir', r'\\10.0.0.16\AuxShare\audio')
AUDIO_CSV = os.path.join(base_share, 'audio-list.csv')

# SOS2 SSH Configuration from config
SOS2_IP = config.get('sos.ip', '10.0.0.16')
SOS2_USER = config.get('sos.user', 'sos')
SOS2_AUDIO_PATH = config.get('audio.remote_path', '/AuxShare/audio/mp3')

# ============================================================================
# FUNCTIONS
# ============================================================================

def load_audio_dictionary(csv_path=None):
    """
    Load audio file mappings from CSV file.
    
    CSV Format:
        Filename, Category
        air_1.mp3, air
        ...
    
    Args:
        csv_path: Path to CSV file (uses AUDIO_CSV if None)
        
    Returns:
        dict: Mapping of {category: [filenames]}, or None on failure
    """
    if not csv_path:
        csv_path = AUDIO_CSV
    
    if not os.path.exists(csv_path):
        print(f"ERROR: Audio CSV not found: {csv_path}")
        return None
    
    audio_dict = {}
    
    try:
        # Try multiple encodings
        encodings_to_try = ['utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        file_content = None
        used_encoding = None
        
        for encoding in encodings_to_try:
            try:
                with open(csv_path, 'r', encoding=encoding, newline='') as f:
                    file_content = f.read()
                    used_encoding = encoding
                    break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if not file_content:
            print("ERROR: Could not decode audio CSV file")
            return None
        
        # Parse CSV
        from io import StringIO
        reader = csv.DictReader(StringIO(file_content), delimiter='\t')
        
        for row in reader:
            filename = row.get('Filename', '').strip()
            category = row.get('Category', '').strip()
            
            if not filename or not category:
                continue
            
            if category not in audio_dict:
                audio_dict[category] = []
            
            audio_dict[category].append(filename)
        
        if not audio_dict:
            print("ERROR: No valid audio mappings found in CSV")
            return None
        
        print(f"[Audio] Loaded {len(audio_dict)} categories with {sum(len(v) for v in audio_dict.values())} audio files")
        return audio_dict
    
    except Exception as e:
        print(f"ERROR: Failed to load audio CSV: {e}")
        import traceback
        traceback.print_exc()
        return None


def initialize_audio(csv_path=None, sos2_ip=None, sos2_user=None, audio_path=None):
    """
    Initialize the audio system.
    
    Args:
        csv_path: Path to audio CSV (uses AUDIO_CSV if None)
        sos2_ip: SOS2 server IP address (uses SOS2_IP if None)
        sos2_user: SSH username (uses SOS2_USER if None)
        audio_path: Path to audio files on SOS2 (uses SOS2_AUDIO_PATH if None)
        
    Returns:
        tuple: (audio_dictionary, AudioController) or (None, None) on failure
    """
    # Load audio mappings
    audio_dict = load_audio_dictionary(csv_path)
    if not audio_dict:
        print("ERROR: Failed to load audio dictionary")
        return None, None
    
    # Initialize controller
    try:
        controller = AudioController(
            sos2_ip=sos2_ip or SOS2_IP,
            sos2_user=sos2_user or SOS2_USER,
            audio_path=audio_path or SOS2_AUDIO_PATH
        )
        
        print("[Audio] Audio controller initialized successfully")
        return audio_dict, controller
    
    except Exception as e:
        print(f"ERROR: Failed to initialize audio controller: {e}")
        import traceback
        traceback.print_exc()
        return None, None


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def initialize_all():
    """
    Initialize audio dictionary and controller in one call.
    
    Returns:
        tuple: (audio_dictionary, controller) or (None, None) on failure
    """
    return initialize_audio()
