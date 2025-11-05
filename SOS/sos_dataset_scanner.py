"""
SOS Dataset Scanner
Standalone script to run on the SOS server to scan dataset directories
and identify movies with their associated .srt caption files.

This script generates a JSON cache file that can be read by remote computers.

Usage:
    python sos_dataset_scanner.py [sos_data_path] [output_file]
    
Example:
    python sos_dataset_scanner.py C:/sos/datasets/ dataset_cache.json
"""

import os
import sys
import json
from datetime import datetime


def scan_sos_datasets(sos_data_path, verbose=True):
    """
    Recursively scan SOS dataset directory structure for playlist.sos files
    to identify movies and locate associated .srt caption files.
    
    SOS typically organizes datasets as:
    sos_data_path/
        theme_folder/ (e.g., air, land, ocean, earth)
            dataset_folder/
                playlist.sos
                dataset.mp4 (or .mov, .avi)
                dataset.srt (optional)
    
    Args:
        sos_data_path: Root path to SOS datasets folder
        verbose: Print detailed scanning progress
        
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
    
    if not os.path.exists(sos_data_path):
        print(f"ERROR: SOS data path not found: {sos_data_path}")
        return None
    
    if verbose:
        print(f"\nScanning SOS datasets in: {sos_data_path}")
        print("=" * 70)
    
    video_extensions = ('.mp4', '.mov', '.avi', '.m4v', '.mpg', '.mpeg', '.wmv')
    themes_found = set()
    datasets_found = 0
    movies_found = 0
    
    try:
        # Walk through all subdirectories
        for root, dirs, files in os.walk(sos_data_path):
            # Check if this directory contains a playlist.sos file
            if 'playlist.sos' in files:
                datasets_found += 1
                
                # Extract dataset name (folder name)
                dataset_name = os.path.basename(root)
                
                # Extract theme (parent folder name)
                parent_dir = os.path.dirname(root)
                theme = os.path.basename(parent_dir) if parent_dir != sos_data_path else 'root'
                themes_found.add(theme)
                
                # Look for video files
                video_files = [f for f in files if f.lower().endswith(video_extensions)]
                
                # Look for .srt caption files
                srt_files = [f for f in files if f.lower().endswith('.srt')]
                
                # Check playlist.sos content for additional verification
                playlist_path = os.path.join(root, 'playlist.sos')
                has_video_ref = False
                try:
                    with open(playlist_path, 'r', encoding='utf-8', errors='ignore') as pf:
                        playlist_content = pf.read().lower()
                        # Check if playlist references video files
                        for ext in video_extensions:
                            if ext in playlist_content:
                                has_video_ref = True
                                break
                except:
                    pass
                
                # Determine if this is a movie dataset
                is_movie = len(video_files) > 0 or has_video_ref
                
                if is_movie:
                    movies_found += 1
                
                # Build dataset info
                dataset_info = {
                    'is_movie': is_movie,
                    'theme': theme,
                    'path': root,
                    'srt_files': srt_files,
                    'srt_path': os.path.join(root, srt_files[0]) if srt_files else None,
                    'video_files': video_files,
                    'has_captions': len(srt_files) > 0
                }
                
                dataset_cache[dataset_name] = dataset_info
                
                if verbose and is_movie:
                    srt_status = f"✓ {srt_files[0]}" if srt_files else "✗ No SRT"
                    video_name = video_files[0] if video_files else "referenced in playlist"
                    print(f"  [{theme:12s}] {dataset_name:40s} | {video_name:20s} | {srt_status}")
        
        # Summary
        print("\n" + "=" * 70)
        print(f"Scan Summary:")
        print(f"  Themes found:        {len(themes_found)} ({', '.join(sorted(themes_found))})")
        print(f"  Total datasets:      {datasets_found}")
        print(f"  Movie datasets:      {movies_found}")
        print(f"  Movies with SRT:     {sum(1 for d in dataset_cache.values() if d['is_movie'] and d['srt_path'])}")
        print(f"  Movies without SRT:  {sum(1 for d in dataset_cache.values() if d['is_movie'] and not d['srt_path'])}")
        print("=" * 70)
        
        return dataset_cache
        
    except Exception as e:
        print(f"ERROR: Exception during scan: {e}")
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
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"\n✓ Cache saved to: {output_file}")
        print(f"  File size: {os.path.getsize(output_file):,} bytes")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to save cache file: {e}")
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
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
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
        
        print(f"✓ CSV saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to save CSV file: {e}")
        return False


def main():
    """Main entry point."""
    
    print("\n" + "=" * 70)
    print("SOS Dataset Scanner")
    print("=" * 70)
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\nUsage: python sos_dataset_scanner.py <sos_data_path> [output_file]")
        print("\nExample:")
        print("  python sos_dataset_scanner.py C:/sos/datasets/")
        print("  python sos_dataset_scanner.py /usr/local/sos/datasets/ dataset_cache.json")
        print("\nDefault output: dataset_cache.json (in current directory)")
        
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
    
    # Scan datasets
    dataset_cache = scan_sos_datasets(sos_data_path, verbose=True)
    
    if not dataset_cache:
        print("\nERROR: Scan failed or no datasets found.")
        sys.exit(1)
    
    # Save to JSON
    if not save_cache_json(dataset_cache, output_file):
        sys.exit(1)
    
    # Also save CSV for easy viewing
    csv_file = output_file.rsplit('.', 1)[0] + '.csv'
    save_cache_csv(dataset_cache, csv_file)
    
    print("\n✓ Scan complete!")
    print("\nNext steps:")
    print(f"  1. Copy '{output_file}' to your remote computer")
    print(f"  2. Update your remote scripts to load this cache file")
    print(f"  3. Re-run scanner when datasets are added/changed")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
