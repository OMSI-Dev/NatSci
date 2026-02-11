"""  
Presentation Initialization Module
Launches LibreOffice Impress with the specified .odp file and creates slide mapping dictionary.
"""

import os
import csv
import re
from pp_access import PowerPointShowController


# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

# Path to the .odp presentation file in SOS2 folder
ODP_FILE = r"\\sos2\AuxShare\documents\noaa_presentation.odp"

# Path to the CSV database file for slide mappings
SLIDE_DATABASE = r"\\sos2\AuxShare\data\sos_datasets.csv"

# ============================================================================
# FUNCTIONS
# ============================================================================

def initialize_presentation(odp_path=None, run_show=True):
    """
    Initialize LibreOffice Impress with the specified presentation.
    
    Args:
        odp_path: Path to .odp file (uses ODP_FILE if None)
        run_show: If True, automatically start the slideshow
        
    Returns:
        PowerPointShowController: Initialized controller object, or None on failure
    """
    if not odp_path:
        odp_path = ODP_FILE
    
    if not os.path.exists(odp_path):
        print(f"ERROR: Presentation file not found: {odp_path}")
        return None
    
    # print(f"Initializing presentation: {odp_path}")
    
    try:
        pp = PowerPointShowController(odp_path)
        pp.launchpp(RunShow=run_show)
        # print(f"Presentation initialized successfully")
        return pp
    except Exception as e:
        print(f"ERROR: Failed to initialize presentation: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_slide_dictionary(csv_path=None):
    """
    Parse CSV file to create slide mapping dictionary.
    Maps clip names (Dataset Name) to slide numbers.
    
    CSV Format (sos_datasets.csv):
        Dataset Name (Auto),Spanish Title,English Title,Slide #,Major Categories
        Clouds - Real-time,Nubes en movimiento,Clouds on the Move,10,
    
    Args:
        csv_path: Path to CSV database file (uses SLIDE_DATABASE if None)
        
    Returns:
        dict: Mapping of {dataset_name: [slide_numbers]}, or None on failure
    """
    if not csv_path:
        csv_path = SLIDE_DATABASE
    
    if not os.path.exists(csv_path):
        print(f"ERROR: Database file not found: {csv_path}")
        return None
    
    # print(f"Loading slide mappings from: {csv_path}")
    
    mapping = {}
    
    try:
        # Try multiple encodings to handle special characters (Spanish accents, etc.)
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
            print("ERROR: Could not decode CSV file with any supported encoding")
            return None
        
        # print(f"Successfully read CSV using {used_encoding} encoding")
        
        # Parse the CSV content
        from io import StringIO
        reader = csv.DictReader(StringIO(file_content))
        
        for line_num, row in enumerate(reader, start=2):
            try:
                # Get Dataset Name - this is the actual clip name from SOS
                dataset_name = row.get('Dataset Name (Auto)', '').strip()
                slide_str = row.get('Slide #', '').strip()
                
                if not dataset_name or not slide_str:
                    print(f"  Skipping line {line_num}: Empty dataset name or slide number")
                    continue
                
                # Parse slide numbers (supports "1" or "1,2,3" format)
                slide_numbers = []
                for token in re.split(r'[;,]', slide_str):
                    token = token.strip()
                    if token:
                        try:
                            slide_numbers.append(int(float(token)))
                        except ValueError:
                            print(f"Warning: Invalid slide number '{token}' on line {line_num}")
                
                if dataset_name and slide_numbers:
                    mapping[dataset_name] = slide_numbers
                    # print(f"  Mapped: '{dataset_name}' -> {slide_numbers}")
            
            except Exception as e:
                print(f"Warning: Error parsing line {line_num}: {e}")
                continue
        
        if not mapping:
            print("ERROR: No valid clip-to-slide mappings found in CSV")
            return None
        
        # print(f"Loaded {len(mapping)} clip-to-slide mappings")
        return mapping
    
    except Exception as e:
        print(f"ERROR: Failed to parse CSV file: {e}")
        return None


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def initialize_all(odp_path=None, csv_path=None, run_show=True):
    """
    Initialize both presentation and slide dictionary in one call.
    
    Args:
        odp_path: Path to .odp file (uses ODP_FILE if None)
        csv_path: Path to CSV database (uses SLIDE_DATABASE if None)
        run_show: If True, automatically start the slideshow
        
    Returns:
        tuple: (pp_controller, slide_dictionary) or (None, None) on failure
    """
    pp = initialize_presentation(odp_path, run_show)
    if not pp:
        print("ERROR: Presentation initialization failed")
        return None, None
    
    slide_dict = create_slide_dictionary(csv_path)
    if not slide_dict:
        print("ERROR: Slide dictionary creation failed")
        pp.close()
        return None, None
    
    # print(f"SUCCESS: Initialized presentation with {len(slide_dict)} mappings")
    return pp, slide_dict