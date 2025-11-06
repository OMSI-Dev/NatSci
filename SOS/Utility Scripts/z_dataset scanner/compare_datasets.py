#!/usr/bin/env python
"""
Compare dataset_folders.txt with dataset_cache.json
Find missing or extra folders
"""

import json

def parse_folder_list(txt_file):
    """Parse dataset_folders.txt and extract all folder names by theme."""
    folders_by_theme = {}
    current_theme = None
    
    with open(txt_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or line.startswith('=') or line.startswith('Total') or line.startswith('SOS Dataset'):
                continue
            
            # Check if this is a theme header
            if line.endswith('datasets)') and '(' in line:
                # Extract theme name (remove the count info)
                theme = line.split('(')[0].strip()
                current_theme = theme.lower()
                folders_by_theme[current_theme] = []
            elif line.startswith('-'):
                # Skip separator lines
                continue
            elif current_theme and line.startswith('  '):
                # This is a folder name
                folder = line.strip()
                folders_by_theme[current_theme].append(folder)
    
    return folders_by_theme


def get_cache_folders(json_file):
    """Extract all folder names from dataset_cache.json."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    datasets = data.get('datasets', {})
    folders_by_theme = {}
    
    for entry in datasets.values():
        if isinstance(entry, dict):
            theme = entry.get('theme', 'unknown').lower()
            folder = entry.get('folder_name', '')
            
            if theme not in folders_by_theme:
                folders_by_theme[theme] = set()
            
            if folder:
                folders_by_theme[theme].add(folder)
    
    return folders_by_theme


def compare_datasets():
    """Compare the two files and report differences."""
    print("Loading dataset_folders.txt...")
    txt_folders = parse_folder_list('dataset_folders.txt')
    
    print("Loading dataset_cache.json...")
    cache_folders = get_cache_folders('dataset_cache.json')
    
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    
    # Convert txt folders to sets for comparison
    txt_folders_sets = {theme: set(folders) for theme, folders in txt_folders.items()}
    
    # Track totals
    total_txt = sum(len(folders) for folders in txt_folders_sets.values())
    total_cache = sum(len(folders) for folders in cache_folders.values())
    
    print(f"\nTotal folders in txt file: {total_txt}")
    print(f"Total unique folders in cache: {total_cache}")
    print(f"Difference: {total_txt - total_cache}")
    
    # Find missing folders by theme
    missing_by_theme = {}
    extra_by_theme = {}
    
    all_themes = set(txt_folders_sets.keys()) | set(cache_folders.keys())
    
    for theme in sorted(all_themes):
        txt_set = txt_folders_sets.get(theme, set())
        cache_set = cache_folders.get(theme, set())
        
        missing = txt_set - cache_set
        extra = cache_set - txt_set
        
        if missing:
            missing_by_theme[theme] = sorted(missing)
        if extra:
            extra_by_theme[theme] = sorted(extra)
    
    # Report missing folders
    if missing_by_theme:
        print("\n" + "=" * 80)
        print("MISSING FROM CACHE (in txt but not in cache)")
        print("=" * 80)
        
        total_missing = 0
        for theme in sorted(missing_by_theme.keys()):
            folders = missing_by_theme[theme]
            total_missing += len(folders)
            print(f"\n{theme.upper()} - {len(folders)} missing:")
            for folder in folders:
                print(f"  - {folder}")
        
        print(f"\nTotal missing: {total_missing}")
    
    # Report extra folders
    if extra_by_theme:
        print("\n" + "=" * 80)
        print("EXTRA IN CACHE (in cache but not in txt)")
        print("=" * 80)
        
        total_extra = 0
        for theme in sorted(extra_by_theme.keys()):
            folders = extra_by_theme[theme]
            total_extra += len(folders)
            print(f"\n{theme.upper()} - {len(folders)} extra:")
            for folder in folders:
                print(f"  - {folder}")
        
        print(f"\nTotal extra: {total_extra}")
    
    if not missing_by_theme and not extra_by_theme:
        print("\n✓ Perfect match! All folders are accounted for.")
    
    # Save detailed report
    with open('dataset_comparison_report.txt', 'w') as f:
        f.write("Dataset Comparison Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total folders in txt file: {total_txt}\n")
        f.write(f"Total folders in cache: {total_cache}\n")
        f.write(f"Difference: {total_txt - total_cache}\n\n")
        
        if missing_by_theme:
            f.write("\nMISSING FROM CACHE:\n")
            f.write("-" * 80 + "\n")
            for theme in sorted(missing_by_theme.keys()):
                f.write(f"\n{theme.upper()}:\n")
                for folder in missing_by_theme[theme]:
                    f.write(f"  - {folder}\n")
        
        if extra_by_theme:
            f.write("\n\nEXTRA IN CACHE:\n")
            f.write("-" * 80 + "\n")
            for theme in sorted(extra_by_theme.keys()):
                f.write(f"\n{theme.upper()}:\n")
                for folder in extra_by_theme[theme]:
                    f.write(f"  - {folder}\n")
    
    print(f"\nDetailed report saved to: dataset_comparison_report.txt")


if __name__ == '__main__':
    compare_datasets()
