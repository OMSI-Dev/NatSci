"""
Configuration and Slide Mapping Parser
Loads config.txt (SOS IP, port, paths) and slide mapping CSV (clip name -> slide numbers).
Clip metadata is now fetched dynamically from SOS via get_all_name_value_pairs.
"""

import csv
import re


def parseConfig(config_file):
    """
    Parse the configuration file.
    
    Args:
        config_file: Path to config.txt file
        
    Returns:
        tuple: (success, config_dict) where config_dict contains:
            - sos_ip: IP address of SOS system
            - port: Port number
            - default_path: Path to presentation files
            - default_name: Default presentation name
            - slide_timer: Timer value for slides
    """
    config_dict = {
        'sos_ip': None,
        'port': None,
        'default_path': None,
        'default_name': None,
        'slide_timer': None
    }
    
    try:
        with open(config_file, 'r') as f:
            for line_num, line in enumerate(f, start=1):
                # Remove comments
                line = line.split('#', 1)[0].strip()
                
                if not line or '=' not in line:
                    continue
                
                # Split on equals sign
                parts = line.split('=', 1)
                if len(parts) != 2:
                    continue
                
                key = parts[0].strip()
                value = parts[1].strip()
                
                # Only process known keys
                if key in config_dict:
                    # Convert port to integer
                    if key == 'port':
                        try:
                            config_dict[key] = int(value)
                        except ValueError:
                            print(f"Warning: Invalid port value on line {line_num}")
                    else:
                        config_dict[key] = value
        
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_file}")
        return (False, None)
    except Exception as e:
        print(f"Error reading config file: {e}")
        return (False, None)
    
    # Check for missing required fields
    missing = [key for key, value in config_dict.items() if value is None]
    
    if missing:
        print(f"Error: Config file missing required fields: {', '.join(missing)}")
        return (False, None)
    
    return (True, config_dict)


def parseSlideNames(slide_file):
    """
    Parse CSV file to map clip names to slide numbers.
    Only extracts clip names and their associated slide numbers.
    All other metadata (captions, duration, fps, etc.) is fetched from SOS dynamically.
    
    Supports two CSV formats:
    1. Headers format: name,slide_numbers
    2. Legacy format: clip_name,slide_numbers (comma or semicolon separated)
    
    Args:
        slide_file: Path to CSV file
        
    Returns:
        tuple: (success, mapping) where mapping is dict of {clip_name: [slide_numbers]}
    """
    mapping = {}
    
    try:
        with open(slide_file, 'r', encoding='utf-8-sig', newline='') as f:
            # Try to detect if this is the new format with headers
            first_line = f.readline().strip()
            f.seek(0)
            
            # Check if first line looks like a header (contains 'name' and 'slide_numbers')
            is_new_format = 'name' in first_line.lower() and ('slide' in first_line.lower() or 'caption' in first_line.lower())
            
            if is_new_format:
                # Parse as CSV with DictReader for new format
                reader = csv.DictReader(f)
                for line_num, row in enumerate(reader, start=2):  # Start at 2 because of header
                    try:
                        # Get clip name from 'name' column
                        clip_name = row.get('name', '').strip()
                        
                        if not clip_name:
                            continue
                        
                        # Get slide numbers
                        slide_str = row.get('slide_numbers', '').strip()
                        
                        if not slide_str:
                            continue
                        
                        # Parse slide numbers (e.g., "1,2,3" or "5")
                        slide_numbers = []
                        for token in re.split(r'[;,]', slide_str):
                            token = token.strip()
                            if token:
                                try:
                                    slide_numbers.append(int(float(token)))
                                except ValueError:
                                    print(f"Warning: Invalid slide number '{token}' on line {line_num}")
                        
                        if clip_name and slide_numbers:
                            mapping[clip_name] = slide_numbers
                            
                    except Exception as e:
                        print(f"Warning: Error parsing line {line_num}: {e}")
                        continue
            
            else:
                # Legacy format: clip_name,slide_numbers
                f.seek(0)
                delimiter = ';' if ';' in first_line else ','
                
                for line_num, raw_line in enumerate(f, start=1):
                    line = raw_line.split('#', 1)[0].strip()
                    if not line:
                        continue
                    
                    try:
                        fields = next(csv.reader([line], delimiter=delimiter))
                        if len(fields) < 2:
                            continue
                        
                        clip_name = fields[0].strip()
                        
                        # Extract slide numbers from remaining fields
                        slide_numbers = []
                        for field in fields[1:]:
                            for token in re.split(r'[;,]', field):
                                token = token.strip()
                                if token:
                                    try:
                                        slide_numbers.append(int(float(token)))
                                    except ValueError:
                                        print(f"Warning: Invalid slide number '{token}' on line {line_num}")
                        
                        if clip_name and slide_numbers:
                            mapping[clip_name] = slide_numbers
                            
                    except Exception as e:
                        print(f"Warning: Error parsing line {line_num}: {e}")
                        continue
        
    except FileNotFoundError:
        print(f"Error: Database file not found: {slide_file}")
        return (False, {})
    except Exception as e:
        print(f"Error reading database file: {e}")
        return (False, {})
    
    if not mapping:
        print("Warning: No clip-to-slide mappings found")
        print("Note: CSV must have 'slide_numbers' column populated")
        return (False, {})
    
    return (True, mapping)
