"""
SOS Dataset Scanner
Standalone script to run on the SOS server to scan dataset directories
and identify movies with their associated .srt caption files.

This script generates a JSON cache file that can be read by remote computers.

Compatible with Python 2.7+ and Python 3.x

Usage:
    python sos_dataset_scanner.py [sos_data_path] [output_file]
    
Example:
    python sos_dataset_scanner.py C:/sos/datasets/ dataset_cache.json
"""

from __future__ import print_function
import os
import sys
import json
from datetime import datetime

# Python 2/3 compatibility
try:
    input = raw_input  # Python 2
except NameError:
    pass  # Python 3


def scan_sos_datasets(sos_data_path, verbose=True, theme_filter=None):
    """
    Recursively scan SOS dataset directory structure for playlist.sos files
    to identify movies and locate associated .srt caption files.
    
    SOS typically organizes datasets as:
    sos_data_path/
        theme_folder/ (e.g., astronomy, atmosphere, land, oceans)
            dataset_folder/
                playlist.sos
                dataset.mp4 (or .mov, .avi)
                dataset.srt (optional)
    
    Args:
        sos_data_path: Root path to SOS datasets folder
        verbose: Print detailed scanning progress
        theme_filter: List of theme folder names to scan (None = scan all)
                     Example: ['astronomy', 'atmosphere', 'land', 'oceans']
        
    Returns:
        dict: Dataset cache with structure:
        {
            'dataset_name': {
                'is_movie': bool,
                'theme': str,           # Theme folder name (air, land, etc.)
                'path': str,            # Full path to dataset folder
                'srt_files': list,      # List of .srt filenames found
                'srt_path': str,        # Full path to first .srt file (or None)
                'video_files': list     # List of video filenames found
            }
        }
    """
    dataset_cache = {}
    
    # Note: theme_filter can be None (scan all), empty list (scan all), or a list of themes
    # We don't set a default here - that's done in main()
    
    if not os.path.exists(sos_data_path):
        print("ERROR: SOS data path not found: {0}".format(sos_data_path))
        return None
    
    if verbose:
        print("\nScanning SOS datasets in: {0}".format(sos_data_path))
        if theme_filter:
            print("Theme filter: {0}".format(', '.join(theme_filter)))
        print("=" * 70)
    
    video_extensions = ('.mp4', '.mov', '.avi', '.m4v', '.mpg', '.mpeg', '.wmv')
    themes_found = set()
    themes_skipped = set()
    datasets_found = 0
    movies_found = 0
    
    try:
        # Walk through all subdirectories
        for root, dirs, files in os.walk(sos_data_path):
            # Apply theme filter at the top level
            if root == sos_data_path and theme_filter:
                # Only descend into allowed theme folders
                dirs[:] = [d for d in dirs if d in theme_filter]
                themes_skipped = set(os.listdir(sos_data_path)) - set(dirs)
                if verbose and themes_skipped:
                    print("Skipping themes: {0}\n".format(', '.join(sorted(themes_skipped))))
            
            # Check if this directory contains a playlist.sos file
            if 'playlist.sos' in files:
                datasets_found += 1
                
                # Extract folder name
                folder_name = os.path.basename(root)
                
                # Extract theme (parent folder name)
                parent_dir = os.path.dirname(root)
                theme = os.path.basename(parent_dir) if parent_dir != sos_data_path else 'root'
                themes_found.add(theme)
                
                # Look for video files
                video_files = [f for f in files if f.lower().endswith(video_extensions)]
                
                # Look for .srt caption files
                srt_files = [f for f in files if f.lower().endswith('.srt')]
                
                # Parse playlist.sos to get the clip name
                playlist_path = os.path.join(root, 'playlist.sos')
                clip_name = None
                has_video_ref = False
                try:
                    with open(playlist_path, 'r') as pf:
                        playlist_content = pf.read()
                        
                        # Look for clip name in playlist.sos
                        # Format is usually: name=Clip Name Here
                        for line in playlist_content.split('\n'):
                            if line.strip().startswith('name='):
                                clip_name = line.split('=', 1)[1].strip()
                                break
                        
                        # Check if playlist references video files
                        playlist_lower = playlist_content.lower()
                        for ext in video_extensions:
                            if ext in playlist_lower:
                                has_video_ref = True
                                break
                except:
                    pass
                
                # Use clip name from playlist, fallback to folder name
                dataset_name = clip_name if clip_name else folder_name
                
                # Determine if this is a movie dataset
                is_movie = len(video_files) > 0 or has_video_ref
                
                if is_movie:
                    movies_found += 1
                
                # Build dataset info
                dataset_info = {
                    'is_movie': is_movie,
                    'theme': theme,
                    'path': root,
                    'folder_name': folder_name,  # Store folder name separately
                    'clip_name': dataset_name,    # The name from playlist.sos
                    'srt_files': srt_files,
                    'srt_path': os.path.join(root, srt_files[0]) if srt_files else None,
                    'video_files': video_files,
                    'has_captions': len(srt_files) > 0
                }
                
                # Store under the clip name (primary key)
                dataset_cache[dataset_name] = dataset_info
                
                # Also store under folder name if different
                if folder_name.lower() != dataset_name.lower():
                    dataset_cache[folder_name] = dataset_info
                
                # Also store normalized versions for fuzzy matching
                # Normalize: lowercase, replace underscores/hyphens with spaces
                normalized_name = dataset_name.lower().replace('_', ' ').replace('-', ' ')
                if normalized_name != dataset_name.lower():
                    dataset_cache[normalized_name] = dataset_info
                
                if verbose and is_movie:
                    srt_status = "OK {0}".format(srt_files[0]) if srt_files else "X No SRT"
                    video_name = video_files[0] if video_files else "referenced in playlist"
                    print("  [{0:12s}] {1:40s} | {2:20s} | {3}".format(
                        theme, dataset_name, video_name, srt_status))
        
        # Summary
        print("\n" + "=" * 70)
        print("Scan Summary:")
        if theme_filter:
            print("  Themes scanned:      {0}".format(', '.join(theme_filter)))
            if themes_skipped:
                print("  Themes skipped:      {0}".format(', '.join(sorted(themes_skipped))))
        print("  Themes found:        {0} ({1})".format(len(themes_found), ', '.join(sorted(themes_found))))
        print("  Total datasets:      {0}".format(datasets_found))
        print("  Movie datasets:      {0}".format(movies_found))
        print("  Movies with SRT:     {0}".format(sum(1 for d in dataset_cache.values() if d['is_movie'] and d['srt_path'])))
        print("  Movies without SRT:  {0}".format(sum(1 for d in dataset_cache.values() if d['is_movie'] and not d['srt_path'])))
        print("=" * 70)
        
        return dataset_cache
        
    except Exception as e:
        print("ERROR: Exception during scan: {0}".format(e))
        import traceback
        traceback.print_exc()
        return None


def save_cache_json(dataset_cache, output_file):
    """
    Save dataset cache to JSON file.
    
    Args:
        dataset_cache: Dictionary from scan_sos_datasets()
        output_file: Path to output JSON file
    """
    try:
        cache_data = {
            'scan_timestamp': datetime.now().isoformat(),
            'total_datasets': len(dataset_cache),
            'total_movies': sum(1 for d in dataset_cache.values() if d['is_movie']),
            'datasets': dataset_cache
        }
        
        with open(output_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print("\n[OK] Cache saved to: {0}".format(output_file))
        print("  File size: {0:,} bytes".format(os.path.getsize(output_file)))
        return True
        
    except Exception as e:
        print("ERROR: Failed to save cache file: {0}".format(e))
        return False


def save_cache_csv(dataset_cache, output_file):
    """
    Save dataset cache to CSV file for easy viewing.
    
    Args:
        dataset_cache: Dictionary from scan_sos_datasets()
        output_file: Path to output CSV file
    """
    import csv
    
    try:
        with open(output_file, 'w') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['Dataset Name', 'Theme', 'Is Movie', 'Has Captions', 'SRT File', 'Video Files', 'Path'])
            
            # Sort by theme then name
            sorted_datasets = sorted(dataset_cache.items(), 
                                    key=lambda x: (x[1]['theme'], x[0]))
            
            for dataset_name, info in sorted_datasets:
                writer.writerow([
                    dataset_name,
                    info['theme'],
                    'Yes' if info['is_movie'] else 'No',
                    'Yes' if info['srt_path'] else 'No',
                    info['srt_files'][0] if info['srt_files'] else '',
                    '; '.join(info['video_files']) if info['video_files'] else '',
                    info['path']
                ])
        
        print("[OK] CSV saved to: {0}".format(output_file))
        return True
        
    except Exception as e:
        print("ERROR: Failed to save CSV file: {0}".format(e))
        return False


def main():
    """Main entry point."""
    
    print("\n" + "=" * 70)
    print("SOS Dataset Scanner")
    print("=" * 70)
    
    # Set to None to scan ALL folders, or specify list to filter
    DEFAULT_THEMES = None  # Scans all folders
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\nUsage: python sos_dataset_scanner.py <sos_data_path> [output_file]")
        print("\nExample:")
        print("  python sos_dataset_scanner.py C:/sos/datasets/")
        print("  python sos_dataset_scanner.py /usr/local/sos/datasets/ dataset_cache.json")
        print("\nScans ALL theme folders")
        print("Default output: dataset_cache.json (in current directory)")
        
        # Use default path if none provided
        sos_data_path = input("\nEnter SOS datasets path (or press Enter to exit): ").strip()
        if not sos_data_path:
            sys.exit(0)
    else:
        sos_data_path = sys.argv[1]
    
    # Determine output file
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        output_file = "dataset_cache.json"
    
    # Normalize path
    sos_data_path = os.path.normpath(sos_data_path)
    
    # Scan datasets with theme filter
    dataset_cache = scan_sos_datasets(sos_data_path, verbose=True, theme_filter=DEFAULT_THEMES)
    
    if not dataset_cache:
        print("\nERROR: Scan failed or no datasets found.")
        sys.exit(1)
    
    # Save to JSON
    if not save_cache_json(dataset_cache, output_file):
        sys.exit(1)
    
    # Also save CSV for easy viewing
    csv_file = output_file.rsplit('.', 1)[0] + '.csv'
    save_cache_csv(dataset_cache, csv_file)
    
    print("\n[OK] Scan complete!")
    print("\nNext steps:")
    print("  1. Copy '{0}' to your remote computer".format(output_file))
    print("  2. Update your remote scripts to load this cache file")
    print("  3. Re-run scanner when datasets are added/changed")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
