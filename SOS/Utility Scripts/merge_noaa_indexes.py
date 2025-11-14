"""
This is a legacy script used to merge existing noaa_042013.csv with the new index generated from sos-index_generator.py

- The index takes precendence in the merging. 
- Fuzzy matching is used to assign existing slide numbers 
- Fuzzy accuracy is reported in new columns for review
"""

import csv
import re
from difflib import SequenceMatcher
from collections import defaultdict

def normalize_name(name):
    """Normalize a name for better matching - remove special chars, lowercase, etc."""
    if not name:
        return ""
    # Convert to lowercase
    name = name.lower()
    # Remove common punctuation and special characters
    name = re.sub(r'[:\-\(\)""",\.]', ' ', name)
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    # Strip leading/trailing whitespace
    name = name.strip()
    return name

def similarity_score(str1, str2):
    """Calculate similarity between two strings (0-1 scale)"""
    return SequenceMatcher(None, normalize_name(str1), normalize_name(str2)).ratio()

def find_best_match(target_name, candidates, threshold=0.7):
    """
    Find the best matching name from candidates
    Returns (best_match, score) or (None, 0) if no good match
    """
    best_match = None
    best_score = 0
    
    normalized_target = normalize_name(target_name)
    
    for candidate in candidates:
        candidate_name = candidate['name']
        score = similarity_score(target_name, candidate_name)
        
        if score > best_score:
            best_score = score
            best_match = candidate
    
    if best_score >= threshold:
        return best_match, best_score
    return None, 0

def merge_csv_files(server_index_path, legacy_path, output_path):
    """
    Merge the two CSV files with server_index taking precedence
    """
    print("=" * 80)
    print("NOAA CSV Merge Tool")
    print("=" * 80)
    print(f"\nReading server index: {server_index_path}")
    print(f"Reading legacy data: {legacy_path}")
    print(f"Output will be written to: {output_path}\n")
    
    # Read the server index (master data)
    server_data = []
    with open(server_index_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            server_data.append(row)
    
    print(f"✓ Loaded {len(server_data)} records from server index")
    
    # Read the legacy data (slide numbers)
    legacy_data = []
    legacy_by_name = {}
    
    with open(legacy_path, 'r', encoding='utf-8') as f:
        # Use csv.reader to properly handle quoted fields with commas
        reader = csv.reader(f)
        
        for row in reader:
            if len(row) >= 2:
                name = row[0].strip()
                slide_nums = row[1].strip()
                
                if name and slide_nums:
                    legacy_data.append({'name': name, 'slide_numbers': slide_nums})
                    # Store by normalized name for quick lookup
                    normalized = normalize_name(name)
                    if normalized not in legacy_by_name:
                        legacy_by_name[normalized] = []
                    legacy_by_name[normalized].append({'name': name, 'slide_numbers': slide_nums})
    
    print(f"✓ Loaded {len(legacy_data)} records from legacy file\n")
    
    # Track matches and anomalies
    exact_matches = 0
    fuzzy_matches = 0
    no_matches = 0
    multiple_matches = []
    anomalies = []
    
    # Prepare merged output
    merged_data = []
    
    print("Processing records...")
    print("-" * 80)
    
    for idx, server_row in enumerate(server_data, 1):
        server_name = server_row.get('name', '') or server_row.get('pretty_name', '')
        
        # Try exact match first (normalized)
        normalized_server = normalize_name(server_name)
        matched = False
        slide_numbers = ""
        match_type = "no_match"
        match_score = 0.0
        legacy_name = ""
        
        # Check for exact normalized match
        if normalized_server in legacy_by_name:
            candidates = legacy_by_name[normalized_server]
            if len(candidates) == 1:
                slide_numbers = candidates[0]['slide_numbers']
                legacy_name = candidates[0]['name']
                exact_matches += 1
                matched = True
                match_type = "exact"
                match_score = 1.0
            else:
                # Multiple exact matches - flag as anomaly
                multiple_matches.append({
                    'server_name': server_name,
                    'candidates': [c['name'] for c in candidates]
                })
                slide_numbers = candidates[0]['slide_numbers']  # Take first one
                legacy_name = candidates[0]['name']
                exact_matches += 1
                matched = True
                match_type = "exact_multiple"
                match_score = 1.0
        
        # If no exact match, try fuzzy matching
        if not matched:
            best_match, score = find_best_match(server_name, legacy_data, threshold=0.7)
            if best_match:
                slide_numbers = best_match['slide_numbers']
                legacy_name = best_match['name']
                fuzzy_matches += 1
                matched = True
                match_type = f"fuzzy_{score:.2f}"
                match_score = score
            else:
                no_matches += 1
                match_type = "no_match"
        
        # Create merged row
        merged_row = server_row.copy()
        merged_row['slide_numbers'] = slide_numbers
        merged_row['match_type'] = match_type
        merged_row['match_score'] = f"{match_score:.3f}"
        merged_row['legacy_name'] = legacy_name
        merged_data.append(merged_row)
        
        # Print progress every 50 records
        if idx % 50 == 0:
            print(f"  Processed {idx}/{len(server_data)} records...")
    
    print(f"  Processed {len(server_data)}/{len(server_data)} records...")
    print()
    
    # Write merged output
    print(f"Writing merged data to: {output_path}")
    fieldnames = ['pretty_name', 'name', 'category', 'majorcategory', 'is_movie', 
                  'caption', 'path', 'slide_numbers', 'match_type', 'match_score', 'legacy_name']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_data)
    
    print(f"✓ Wrote {len(merged_data)} records to output file\n")
    
    # Print summary statistics
    print("=" * 80)
    print("MERGE SUMMARY")
    print("=" * 80)
    print(f"Total records processed: {len(server_data)}")
    print(f"  Exact matches:         {exact_matches}")
    print(f"  Fuzzy matches:         {fuzzy_matches}")
    print(f"  No matches found:      {no_matches}")
    print()
    
    # Report anomalies
    if multiple_matches:
        print("⚠ ANOMALY: Multiple exact matches found")
        print("-" * 80)
        for item in multiple_matches[:10]:  # Show first 10
            print(f"  Server: '{item['server_name']}'")
            print(f"  Matched: {item['candidates']}")
            print()
        if len(multiple_matches) > 10:
            print(f"  ... and {len(multiple_matches) - 10} more\n")
    
    # Show records with no matches
    if no_matches > 0:
        print("⚠ ANOMALY: Records with no slide numbers assigned")
        print("-" * 80)
        count = 0
        for row in merged_data:
            if row['match_type'] == 'no_match':
                name = row.get('name', '') or row.get('pretty_name', '')
                print(f"  No match: '{name}'")
                count += 1
                if count >= 20:  # Show first 20
                    print(f"  ... and {no_matches - 20} more")
                    break
        print()
    
    # Show fuzzy matches for review
    if fuzzy_matches > 0:
        print("ℹ INFO: Fuzzy matches (review recommended)")
        print("-" * 80)
        count = 0
        for row in merged_data:
            if row['match_type'].startswith('fuzzy'):
                server_name = row.get('name', '') or row.get('pretty_name', '')
                legacy_name = row.get('legacy_name', '')
                score = row.get('match_score', '0')
                print(f"  Score {score}: '{server_name}' → '{legacy_name}'")
                print(f"             Slide(s): {row['slide_numbers']}")
                count += 1
                if count >= 15:  # Show first 15
                    remaining = fuzzy_matches - 15
                    if remaining > 0:
                        print(f"  ... and {remaining} more fuzzy matches")
                    break
        print()
    
    print("=" * 80)
    print("✓ Merge complete!")
    print("=" * 80)

if __name__ == "__main__":
    # File paths (assumes they're in the same directory as the script)
    server_index = "noaa_server-index.csv"
    legacy_file = "noaa_042013.csv"
    output_file = "noaa_merged.csv"
    
    try:
        merge_csv_files(server_index, legacy_file, output_file)
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: Could not find file - {e}")
        print("\nMake sure both CSV files are in the same directory as this script:")
        print("  - noaa_server_index.csv")
        print("  - noaa_042013.csv")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
