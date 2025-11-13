import tkinter as tk
from PIL import Image, ImageTk
import socket
import threading
import os

PI_PORT = 4096

# ---------------------------
# GUI CLASS
# ---------------------------

class ImageApp:
    """GUI app to display the currently playing title and playlist from SOS."""

    def __init__(self, root, image_path=None):
        self.root = root
        self.root.title("SOS Now Playing")
        self.root.geometry("800x600")

        # Try to load background image, if available
        if image_path and os.path.exists(image_path):
            image = Image.open(image_path).resize((800, 600))
            self.image_tk = ImageTk.PhotoImage(image)
            self.bg_label = tk.Label(root, image=self.image_tk)
            self.bg_label.place(relwidth=1, relheight=1)
            bg_color = "#00000000"  # transparent background for labels
        else:
            # fallback solid color background
            self.bg_label = tk.Label(root, bg="black")
            self.bg_label.place(relwidth=1, relheight=1)
            bg_color = "black"

        # Title label (Now Playing)
        self.text_label = tk.Label(
            root,
            text="Waiting for data...",
            font=("Times New Roman", 22, "bold"),
            fg="white",
            bg=bg_color,
        )
        self.text_label.place(relx=0.5, rely=0.1, anchor="center")

        # Playlist label
        self.playlist_label = tk.Label(
            root,
            text="Playlist will appear here",
            font=("Courier", 14),
            fg="yellow",
            bg=bg_color,
            justify="left",
            anchor="nw",
        )
        self.playlist_label.place(relx=0.05, rely=0.3, anchor="nw")

    def update_playing(self, current_title: str):
        """Updates the current playing label."""
        self.text_label.config(text=f"Now Playing: {current_title}")

    def update_playlist(self, playlist_items: list):
        """Updates the playlist display with a formatted list."""
        if not playlist_items:
            playlist_text = "No playlist available"
        else:
            # Format as numbered list
            playlist_text = "Playlist:\n" + "\n".join(
                f"  {i+1}. {item}" for i, item in enumerate(playlist_items)
            )
        self.playlist_label.config(text=playlist_text)


# ---------------------------
# SOCKET SERVER
# ---------------------------

def pi_socket_server(app: ImageApp):
    """Socket server that receives CLIP and PLAYLIST data from Beelink."""
    print("[Pi] Socket server thread starting...")
    server_sock = None
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('0.0.0.0', PI_PORT))
        server_sock.listen(5)
        
        bound_addr = server_sock.getsockname()
        print(f"[Pi] Socket server successfully bound to {bound_addr}")
        print(f"[Pi] Listening on port {PI_PORT}...")
        
    except Exception as e:
        print(f"[Pi] Socket server failed to start: {e}")
        if server_sock:
            server_sock.close()
        return

    while True:
        try:
            print("[Pi] Waiting for connection...")
            conn, addr = server_sock.accept()
            print(f"[Pi] ✅ Connection from {addr}")
            
            data = conn.recv(4096)  # Increased buffer for playlist data
            if data:
                msg = data.decode('utf-8', 'ignore').strip()
                print(f"[Pi] Received: {msg}")
                
                # Parse the message
                if msg.startswith("CLIP:"):
                    # Extract clip name and update GUI
                    clip_name = msg[5:].strip()  # Remove "CLIP:" prefix
                    print(f"[Pi] Updating current clip to: {clip_name}")
                    app.root.after(0, lambda: app.update_playing(clip_name))
                    
                elif msg.startswith("PLAYLIST:"):
                    # Extract playlist and split by comma
                    playlist_str = msg[9:].strip()  # Remove "PLAYLIST:" prefix
                    playlist_items = [item.strip() for item in playlist_str.split(',')]
                    print(f"[Pi] Updating playlist with {len(playlist_items)} items")
                    app.root.after(0, lambda items=playlist_items: app.update_playlist(items))
                
                # Send acknowledgment
                conn.sendall(b"ACK\n")
                print(f"[Pi] Sent acknowledgment")
            else:
                print("[Pi] No data received")
            
            conn.close()
            print("[Pi] Connection closed")
            
        except Exception as e:
            print(f"[Pi] Error in socket loop: {e}")
            import traceback
            traceback.print_exc()


# ---------------------------
# MAIN
# ---------------------------

def main():
    root = tk.Tk()
    
    # You can specify a background image path here if you have one
    # app = ImageApp(root, image_path="Now_Playing/bg.jpg")
    app = ImageApp(root)

    # Start socket server in background thread, passing the app instance
    socket_thread = threading.Thread(target=pi_socket_server, args=(app,), daemon=True)
    socket_thread.start()

    root.mainloop()

if __name__ == "__main__":
    main()