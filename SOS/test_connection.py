import os
import configparser

def find_sos_playlist(clip_name, sos_media_root="/shared/sos/media/"):
    """
    Finds the full path to a playlist.sos file given a clip name.

    Args:
        clip_name (str): The name of the SOS clip to search for.
        sos_media_root (str): The root directory where SOS media is stored.

    Returns:
        str: The full path to the playlist.sos file, or None if not found.
    """
    # Standard NOAA-provided directories to search
    subdirectories = ["atmosphere", "astronomy", "land", "oceans", "site-custom"]
    
    # Construct the full paths to the directories
    search_paths = [os.path.join(sos_media_root, sub) for sub in subdirectories]
    
    for search_path in search_paths:
        if not os.path.isdir(search_path):
            continue

        # os.walk() generates the file names in a directory tree
        for root, dirs, files in os.walk(search_path):
            # Check for any playlist.sos files in the current directory
            for file_name in files:
                if file_name.endswith(".sos"):
                    playlist_path = os.path.join(root, file_name)
                    
                    # Read the playlist.sos file to find the clip name
                    # Note: .sos files are in a simple key-value INI-style format
                    config = configparser.ConfigParser()
                    try:
                        config.read(playlist_path)
                        # The clip name is in the default section, under the 'name' key
                        if 'name' in config['DEFAULT'] and config['DEFAULT']['name'] == clip_name:
                            print(f"Found match: {playlist_path}")
                            return playlist_path
                    except configparser.Error:
                        # Skip files that are not correctly formatted
                        continue

    print(f"Could not find playlist.sos file for clip: {clip_name}")
    return None

# --- How to use the function ---
if __name__ == "__main__":
    # Example 1: Find the "Blue Marble" clip
    blue_marble_path = find_sos_playlist("Blue Marble")
    if blue_marble_path:
        print(f"Blue Marble playlist path: {blue_marble_path}")
    
    # Example 2: Find a known clip that isn't custom
    hurricane_path = find_sos_playlist("Hurricane Florence (Aug - Sep 2018)")
    if hurricane_path:
        print(f"Hurricane Florence playlist path: {hurricane_path}")
