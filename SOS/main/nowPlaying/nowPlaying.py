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
        self.root.title("Science on a Sphere - Now Playing")
        
        # Make fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Bind escape key to exit fullscreen
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', True))
        
        # Background - load geo.png
        self.bg_frame = tk.Frame(root, bg="#0a0e27")
        self.bg_frame.place(relwidth=1, relheight=1)
        
        # Try to load geo.png from same directory as script
        bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo.png")
        if os.path.exists(bg_path):
            try:
                image = Image.open(bg_path)
                image = image.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
                self.image_tk = ImageTk.PhotoImage(image)
                self.bg_label = tk.Label(self.bg_frame, image=self.image_tk)
                self.bg_label.place(relwidth=1, relheight=1)
                print(f"✅ Loaded background image: {bg_path}")
            except Exception as e:
                print(f"Could not load background image: {e}")
        else:
            print(f"⚠️ Background image not found: {bg_path}")
        
        # Header frame with semi-transparent background
        # Create a translucent overlay effect
        header_canvas = tk.Canvas(root, bg="#f0f0f0", highlightthickness=0)
        header_canvas.place(relx=0.5, rely=0.08, anchor="center", relwidth=0.9, height=100)
        
        # Draw semi-transparent rectangle
        header_canvas.create_rectangle(
            0, 0, screen_width, 100,
            fill="#f5f5f5",
            stipple="gray50",  # Creates transparency effect
            outline=""
        )
        
        header_frame = tk.Frame(header_canvas, bg="#f0f0f0", highlightthickness=0)
        header_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # "Now Playing" label - smaller, elegant header
        now_playing_header = tk.Label(
            header_frame,
            text="N O W   P L A Y I N G",
            font=("Helvetica Neue", 16, "bold"),
            fg="#2c3e50",
            bg="#f0f0f0"
        )
        now_playing_header.pack(pady=(10, 0))
        
        # Current title label - large and prominent
        self.text_label = tk.Label(
            header_frame,
            text="Waiting for data...",
            font=("Helvetica Neue", 32, "bold"),
            fg="#1a1a1a",
            bg="#f0f0f0",
            wraplength=int(screen_width * 0.85)
        )
        self.text_label.pack(pady=(5, 10))
        
        # Playlist container frame with semi-transparent background
        playlist_canvas_bg = tk.Canvas(root, bg="#f0f0f0", highlightthickness=0)
        playlist_canvas_bg.place(relx=0.5, rely=0.55, anchor="center", relwidth=0.85, relheight=0.7)
        
        # Draw semi-transparent rectangle for playlist
        playlist_canvas_bg.create_rectangle(
            0, 0, int(screen_width * 0.85), int(screen_height * 0.7),
            fill="#f5f5f5",
            stipple="gray50",  # Creates transparency effect
            outline=""
        )
        
        playlist_frame = tk.Frame(playlist_canvas_bg, bg="#f0f0f0", highlightthickness=0)
        playlist_frame.place(relwidth=1, relheight=1)
        
        # Playlist header
        playlist_header = tk.Label(
            playlist_frame,
            text="UPCOMING IN PLAYLIST",
            font=("Helvetica Neue", 14, "bold"),
            fg="#2c3e50",
            bg="#f0f0f0",
            anchor="w"
        )
        playlist_header.pack(fill="x", padx=40, pady=(30, 15))
        
        # Playlist content with scrollable frame
        self.playlist_canvas = tk.Canvas(playlist_frame, bg="#f0f0f0", highlightthickness=0)
        self.playlist_canvas.pack(fill="both", expand=True, padx=40, pady=(0, 30))
        
        # Playlist label
        self.playlist_label = tk.Label(
            self.playlist_canvas,
            text="Playlist will appear here",
            font=("Helvetica Neue", 18),
            fg="#1a1a1a",
            bg="#f0f0f0",
            justify="left",
            anchor="nw"
        )
        self.playlist_canvas.create_window(0, 0, window=self.playlist_label, anchor="nw")

    def update_playing(self, current_title: str):
        """Updates the current playing label."""
        self.text_label.config(text=current_title)

    def update_playlist(self, playlist_items: list):
        """Updates the playlist display with a formatted list."""
        if not playlist_items:
            playlist_text = "No upcoming items"
        else:
            # Create a beautiful numbered list with proper spacing
            lines = []
            for i, item in enumerate(playlist_items):
                # Add visual separator between items
                if i > 0:
                    lines.append("")  # Blank line for spacing
                lines.append(f"{i+1}.  {item}")
            
            playlist_text = "\n".join(lines)
        
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
            
            data = conn.recv(4096)
            if data:
                msg = data.decode('utf-8', 'ignore').strip()
                print(f"[Pi] Received: {msg}")
                
                # Parse the message
                if msg.startswith("CLIP:"):
                    clip_name = msg[5:].strip()
                    print(f"[Pi] Updating current clip to: {clip_name}")
                    app.root.after(0, lambda cn=clip_name: app.update_playing(cn))
                    
                elif msg.startswith("PLAYLIST:"):
                    playlist_str = msg[9:].strip()
                    playlist_items = [item.strip() for item in playlist_str.split(',')]
                    print(f"[Pi] Updating playlist with {len(playlist_items)} items")
                    app.root.after(0, lambda items=playlist_items: app.update_playlist(items))
                
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
    
    # No need for image_path parameter anymore - uses geo.png from script directory
    app = ImageApp(root)

    # Start socket server in background thread
    socket_thread = threading.Thread(target=pi_socket_server, args=(app,), daemon=True)
    socket_thread.start()

    root.mainloop()

if __name__ == "__main__":
    main()