#!/usr/bin/env python
"""
Find missing folders between dataset_folders.txt and dataset_cache.json
"""

import json

# Parse txt file - folders are indented with 2 spaces
txt_folders = set()
with open('dataset_folders.txt', 'r') as f:
    for line in f:
        # Folder names are indented with 2 spaces
        if line.startswith('  ') and not line.strip().startswith('-'):
            folder = line.strip()
            if folder:  # Skip empty lines
                txt_folders.add(folder)

print(f"Folders in dataset_folders.txt: {len(txt_folders)}")

# Parse JSON cache
with open('dataset_cache.json', 'r') as f:
    data = json.load(f)

datasets = data.get('datasets', {})
cache_folders = set()
for entry in datasets.values():
    folder = entry.get('folder_name', '')
    if folder:
        cache_folders.add(folder)

print(f"Unique folder_name values in cache: {len(cache_folders)}")
print(f"Total dataset entries in cache: {len(datasets)}")

# Find missing
missing = txt_folders - cache_folders
extra = cache_folders - txt_folders

print(f"\n{'='*80}")
print(f"MISSING FROM CACHE: {len(missing)} folders")
print(f"{'='*80}")

if missing:
    for folder in sorted(missing):
        print(f"  - {folder}")
else:
    print("  None! All folders are in the cache.")

print(f"\n{'='*80}")
print(f"EXTRA IN CACHE (not in folder list): {len(extra)} folders")
print(f"{'='*80}")

if extra:
    print("First 20:")
    for folder in sorted(extra)[:20]:
        print(f"  - {folder}")
    if len(extra) > 20:
        print(f"  ... and {len(extra) - 20} more")
else:
    print("  None!")

# Save report
with open('missing_folders.txt', 'w') as f:
    f.write(f"MISSING FROM CACHE ({len(missing)} folders)\n")
    f.write("="*80 + "\n")
    f.write("These folders exist on the SOS server (found by list_dataset_folders.py)\n")
    f.write("but were NOT captured in dataset_cache.json (by sos_dataset_scanner.py)\n\n")
    for folder in sorted(missing):
        f.write(f"{folder}\n")

print(f"\nMissing folders saved to: missing_folders.txt")
