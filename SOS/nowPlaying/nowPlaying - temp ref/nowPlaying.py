import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import socket
import threading
import os

PI_PORT = 4096

# ---------------------------
# GUI CLASS
# ---------------------------

class ImageApp:
    """GUI app to display the currently playing title and playlist from SOS."""

    def __init__(self, root):
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
        
        # Load and prepare background with transparent overlays
        bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo.png")
        
        if os.path.exists(bg_path):
            try:
                # Load background image
                bg_image = Image.open(bg_path).convert('RGBA')
                bg_image = bg_image.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
                
                # Create a transparent overlay layer
                overlay = Image.new('RGBA', (screen_width, screen_height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)
                
                # Draw semi-transparent header box with rounded corners
                header_width = int(screen_width * 0.85)
                header_height = 140
                header_x = (screen_width - header_width) // 2
                header_y = int(screen_height * 0.20) - header_height // 2
                draw.rounded_rectangle(
                    [header_x, header_y, header_x + header_width, header_y + header_height],
                    radius=25,  # Corner radius
                    fill=(255, 255, 255, 120)  # White with ~47% opacity
                )
                
                # Draw semi-transparent playlist box with rounded corners
                playlist_width = int(screen_width * 0.85)
                playlist_height = int(screen_height * 0.53)
                playlist_x = (screen_width - playlist_width) // 2
                playlist_y = int(screen_height * 0.60) - playlist_height // 2
                draw.rounded_rectangle(
                    [playlist_x, playlist_y, playlist_x + playlist_width, playlist_y + playlist_height],
                    radius=25,  # Corner radius
                    fill=(255, 255, 255, 120)  # White with ~47% opacity
                )
                
                # Composite overlay onto background
                bg_with_overlay = Image.alpha_composite(bg_image, overlay)
                self.bg_image_tk = ImageTk.PhotoImage(bg_with_overlay)
                
                print(f"✅ Loaded background image with overlays: {bg_path}")
                
            except Exception as e:
                print(f"Could not load background image: {e}")
                # Fallback - create solid color background
                bg_with_overlay = Image.new('RGB', (screen_width, screen_height), (10, 14, 39))
                self.bg_image_tk = ImageTk.PhotoImage(bg_with_overlay)
        else:
            print(f"⚠️ Background image not found: {bg_path}")
            # Fallback - create solid color background
            bg_with_overlay = Image.new('RGB', (screen_width, screen_height), (10, 14, 39))
            self.bg_image_tk = ImageTk.PhotoImage(bg_with_overlay)
        
        # Create a canvas to place everything
        canvas = tk.Canvas(root, highlightthickness=0)
        canvas.place(relwidth=1, relheight=1)
        
        # Place the background image on the canvas
        canvas.create_image(0, 0, image=self.bg_image_tk, anchor="nw")
        
        # "Now Playing" header text
        canvas.create_text(
            screen_width // 2,
            int(screen_height * 0.20) - 32,
            text="NOW PLAYING...",
            font=("Helvetica Neue", 16, "bold"),
            fill="#2c3e50"
        )
        
        # Current title text
        self.title_text_id = canvas.create_text(
            screen_width // 2,
            int(screen_height * 0.20) + 10,
            text="Waiting for data...",
            font=("Helvetica Neue", 28, "bold"),
            fill="#1a1a1a",
            width=int(screen_width * 0.75)
        )
        
        # Playlist header text
        canvas.create_text(
            int(screen_width * 0.075) + 60,
            int(screen_height * 0.38) + 20,
            text="UPCOMING IN PLAYLIST",
            font=("Helvetica Neue", 14, "bold"),
            fill="#2c3e50",
            anchor="w"
        )
        
        # Playlist content text
        self.playlist_text_id = canvas.create_text(
            int(screen_width * 0.075) + 60,
            int(screen_height * 0.38) + 60,
            text="Playlist will appear hereeeee",
            font=("Helvetica Neue", 15),
            fill="#1a1a1a",
            anchor="nw",
            width=int(screen_width * 0.70)
        )
        
        # Store canvas reference and current title for updates
        self.canvas = canvas
        self.current_playing_title = None

    def update_playing(self, current_title: str):
        """Updates the current playing label."""
        self.canvas.itemconfig(self.title_text_id, text=current_title)
        self.current_playing_title = current_title
        # Refresh playlist to bold the current item
        if hasattr(self, 'last_playlist_items'):
            self.update_playlist(self.last_playlist_items)

    def update_playlist(self, playlist_items: list):
        """Updates the playlist display with a formatted list."""
        self.last_playlist_items = playlist_items  # Store for re-rendering
        
        if not playlist_items:
            playlist_text = "No upcoming items"
        else:
            # Create a beautiful numbered list with proper spacing
            lines = []
            for i, item in enumerate(playlist_items):
                # Add visual separator between items
                if i > 0:
                    lines.append("")  # Blank line for spacing
                
                # Check if this item is currently playing
                if self.current_playing_title and item == self.current_playing_title:
                    lines.append(f"{i+1}.  ► {item}  ◄")  # Add arrow indicators for now playing
                else:
                    lines.append(f"{i+1}.  {item}")
            
            playlist_text = "\n".join(lines)
        
        self.canvas.itemconfig(self.playlist_text_id, text=playlist_text)


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
                
                elif msg.startswith("INIT:"):
                    print(f"[Pi] Received init message: {msg}")
                
                else:
                    print(f"[Pi] Unknown message format: {msg}")
                
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
    app = ImageApp(root)
    
    # Start socket server in background thread
    socket_thread = threading.Thread(target=pi_socket_server, args=(app,), daemon=True)
    socket_thread.start()
    
    root.mainloop()

if __name__ == "__main__":
    main()

