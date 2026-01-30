import json
import os

cache_path = 'dev/clip_metadata_cache.JSON'

if not os.path.exists(cache_path):
    print(f"File not found: {cache_path}")
    exit(1)

try:
    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    keys_to_remove = ['fade-out-delay', 'fade-out-delay-value']
    modified_count = 0

    for clip_name, metadata in data.items():
        for key in keys_to_remove:
            if key in metadata:
                del metadata[key]
                modified_count += 1
                
    if modified_count > 0:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Successfully cleaned up {modified_count} occurrences of fade-out-delay keys.")
    else:
        print("No fade-out-delay keys found.")

except Exception as e:
    print(f"Error during cleanup: {e}")
