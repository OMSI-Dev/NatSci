"""
Simplified Parsers
Functions to parse configuration and slide database files.
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
    Parse the slide database file mapping clip names to slide numbers.
    
    The file format is CSV with:
    - First column: clip name
    - Remaining columns: slide number(s)
    - Comments start with '#'
    - Auto-detects delimiter (';' or ',')
    
    Args:
        slide_file: Path to CSV database file
        
    Returns:
        tuple: (success, mapping) where mapping is a dict of 
               {clip_name: [slide_numbers]}
    """
    mapping = {}
    
    try:
        with open(slide_file, 'r', encoding='utf-8-sig', newline='') as f:
            # Auto-detect delimiter
            sample = f.read()
            f.seek(0)
            delimiter = ';' if ';' in sample else ','
            
            for line_num, raw_line in enumerate(f, start=1):
                # Remove comments
                line = raw_line.split('#', 1)[0].strip()
                
                if not line:
                    continue
                
                try:
                    # Parse CSV fields
                    fields = next(csv.reader([line], delimiter=delimiter))
                    
                    if len(fields) < 2:
                        continue
                    
                    clip_name = fields[0].strip()
                    
                    # Extract all numeric values from remaining fields
                    # Handles formats like: "1,2,3" or "1; 2; 3" or separate columns
                    slide_numbers = []
                    for field in fields[1:]:
                        # Split on commas and semicolons
                        tokens = re.split(r'[;,]', field)
                        for token in tokens:
                            token = token.strip()
                            if token:
                                try:
                                    # Handle both int and float representations
                                    if token.isdigit():
                                        slide_numbers.append(int(token))
                                    else:
                                        slide_numbers.append(int(float(token)))
                                except ValueError:
                                    print(f"Warning: Invalid slide number '{token}' on line {line_num}")
                    
                    # Add to mapping if we have valid data
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
        print("Warning: No valid clip-to-slide mappings found")
        return (False, {})
    
    return (True, mapping)
