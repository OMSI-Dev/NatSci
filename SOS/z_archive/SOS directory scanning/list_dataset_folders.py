#!/usr/bin/env python
"""
List All Dataset Folders on SOS Server
========================================
This utility script walks through the SOS media directory and lists all
dataset folder names (folders containing playlist.sos files).

Usage:
    python list_dataset_folders.py /shared/sos/media/

Output:
    - Prints all dataset folder names to console
    - Saves list to dataset_folders.txt
    - Shows count by theme

Compatible with Python 2.7+ and Python 3.x
"""

import os
import sys

def list_dataset_folders(base_path):
    """
    Walk through SOS directory and find all folders with playlist.sos files.
    
    Args:
        base_path: Root path to scan (e.g., /shared/sos/media/)
    
    Returns:
        dict: Theme names mapped to lists of dataset folder names
    """
    datasets_by_theme = {}
    total_count = 0
    
    print("Scanning SOS directory structure...")
    print("Base path: {}".format(base_path))
    print("")
    
    # Walk through all theme folders
    for theme_name in os.listdir(base_path):
        theme_path = os.path.join(base_path, theme_name)
        
        # Skip if not a directory
        if not os.path.isdir(theme_path):
            continue
        
        datasets_by_theme[theme_name] = []
        
        # Walk through each theme folder looking for playlist.sos files
        for root, dirs, files in os.walk(theme_path):
            if 'playlist.sos' in files:
                # This is a dataset folder
                folder_name = os.path.basename(root)
                datasets_by_theme[theme_name].append(folder_name)
                total_count += 1
    
    return datasets_by_theme, total_count


def save_to_file(datasets_by_theme, total_count, output_file='dataset_folders.txt'):
    """
    Save the dataset folder list to a text file.
    
    Args:
        datasets_by_theme: Dictionary of theme -> folder list
        total_count: Total number of datasets found
        output_file: Output filename
    """
    with open(output_file, 'w') as f:
        f.write("SOS Dataset Folders\n")
        f.write("=" * 80 + "\n")
        f.write("Total datasets found: {}\n\n".format(total_count))
        
        # Sort themes alphabetically
        for theme in sorted(datasets_by_theme.keys()):
            folders = datasets_by_theme[theme]
            f.write("\n{} ({} datasets)\n".format(theme.upper(), len(folders)))
            f.write("-" * 80 + "\n")
            
            # Sort folder names alphabetically
            for folder_name in sorted(folders):
                f.write("  {}\n".format(folder_name))
    
    print("\nSaved to: {}".format(output_file))


def print_summary(datasets_by_theme, total_count):
    """
    Print a summary to console.
    
    Args:
        datasets_by_theme: Dictionary of theme -> folder list
        total_count: Total number of datasets found
    """
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("Total datasets found: {}".format(total_count))
    print("")
    
    # Sort themes alphabetically and show counts
    for theme in sorted(datasets_by_theme.keys()):
        folder_count = len(datasets_by_theme[theme])
        print("  {}: {} datasets".format(theme, folder_count))
    
    print("\nRun with --verbose to see all folder names")


def print_all_folders(datasets_by_theme):
    """
    Print all folder names grouped by theme.
    
    Args:
        datasets_by_theme: Dictionary of theme -> folder list
    """
    print("\n" + "=" * 80)
    print("ALL DATASET FOLDERS")
    print("=" * 80)
    
    # Sort themes alphabetically
    for theme in sorted(datasets_by_theme.keys()):
        folders = datasets_by_theme[theme]
        print("\n{} ({} datasets)".format(theme.upper(), len(folders)))
        print("-" * 80)
        
        # Sort folder names alphabetically
        for folder_name in sorted(folders):
            print("  {}".format(folder_name))


def main():
    """Main entry point."""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python list_dataset_folders.py <path_to_sos_media> [--verbose]")
        print("")
        print("Example:")
        print("  python list_dataset_folders.py /shared/sos/media/")
        print("  python list_dataset_folders.py /shared/sos/media/ --verbose")
        sys.exit(1)
    
    base_path = sys.argv[1]
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    # Check if path exists
    if not os.path.exists(base_path):
        print("ERROR: Path does not exist: {}".format(base_path))
        sys.exit(1)
    
    if not os.path.isdir(base_path):
        print("ERROR: Path is not a directory: {}".format(base_path))
        sys.exit(1)
    
    # Scan the directory
    datasets_by_theme, total_count = list_dataset_folders(base_path)
    
    # Print results
    if verbose:
        print_all_folders(datasets_by_theme)
    else:
        print_summary(datasets_by_theme, total_count)
    
    # Save to file
    save_to_file(datasets_by_theme, total_count)
    
    print("\nDone!")


if __name__ == '__main__':
    main()
