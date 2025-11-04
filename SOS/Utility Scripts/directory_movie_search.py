import os

SOS_MEDIA_ROOT = "/shared/sos/media"
PROJECT_FOLDER = "acidifying-oceans"

def find_playlist_for_project(project_folder):
    """
    Written for Python 2.7.17 to run on the SOS server via ssh connection.     
    File is currently located in /home/sosdemo
        First run: ssh sosdemo@10.10.51.87
        Then run: python directory_movie_search.py
    
    """
    project_path = os.path.join(SOS_MEDIA_ROOT, "extras", project_folder)
    
    if not os.path.isdir(project_path):
        print("Project folder not found:", project_path)
        return None

    for root, dirs, files in os.walk(project_path):
        for file_name in files:
            if file_name.lower() == "playlist.sos":
                playlist_path = os.path.join(root, file_name)
                
                is_movie = False
                try:
                    with open(playlist_path, "r") as f:
                        print("\n--- Contents of playlist.sos ---")
                        for line in f:
                            line = line.strip()
                            print(line)
                            
                            # Robust parsing of "data = ..."
                            if line.lower().startswith("data"):
                                parts = line.split("=", 1)
                                if len(parts) == 2:
                                    filenames = parts[1].strip().replace('"','').split(',')
                                    for filename in filenames:
                                        if filename.strip().lower().endswith(".mp4"):
                                            is_movie = True
                        print("--- End of file ---\n")
                    
                    print("Playlist found:", playlist_path)
                    print("Type:", "movie" if is_movie else "image")
                    return playlist_path, "movie" if is_movie else "image"
                except Exception as e:
                    print("Error reading playlist:", e)
                    return playlist_path, "unknown"

    print("No playlist.sos found in project folder:", project_path)
    return None, None

# --- Test ---
if __name__ == "__main__":
    find_playlist_for_project(PROJECT_FOLDER)
