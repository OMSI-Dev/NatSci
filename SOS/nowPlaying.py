import tkinter as tk
from PIL import Image, ImageTk
import socket
import time
import threading  # for background network thread

# bgImageDir = "Now_Playing/bg.jpg"
SOSPort = 2468
SOSHost = "10.10.51.87"


# ---------------------------
# GUI CLASS
# ---------------------------

import os
import tkinter as tk
from PIL import Image, ImageTk

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
            text="Current Title",
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

    def update_playlist(self, playlist: str):
        """Updates the playlist display."""
        self.playlist_label.config(text=playlist)

# ---------------------------
# NETWORK / SOS COMMUNICATION
# ---------------------------

def try_connect(host: str, port: int, timeout: float = 4.0):
    """Connect to the SOS TCP control socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        print(f"Connecting to SOS server {host}:{port} (timeout={timeout}s)...")
        sock.connect((host, port))
        print("✅ TCP connection established.")
        return sock
    except OSError as e:
        print(f"❌ Connection failed: {e}")
        sock.close()
        return None


def recv_all(sock: socket.socket, timeout_idle: float = 1.0, chunk: int = 4096) -> bytes:
    """Receive data until the socket is idle for `timeout_idle` seconds."""
    buffer = bytearray()
    orig_timeout = sock.gettimeout()
    sock.settimeout(0.2)
    start = time.time()
    try:
        while True:
            try:
                data = sock.recv(chunk)
                if data:
                    buffer.extend(data)
                    start = time.time()
                else:
                    break
            except socket.timeout:
                if time.time() - start >= timeout_idle:
                    break
    finally:
        sock.settimeout(orig_timeout)
    return bytes(buffer)


def do_handshake(sock: socket.socket, timeout: float = 4.0):
    """Perform the standard SOS handshake (send 'enable')."""
    sock.settimeout(timeout)
    try:
        print("Sending handshake: 'enable\\n'")
        sock.sendall(b'enable\n')
    except OSError as e:
        print(f"❌ Failed to send handshake: {e}")
        return None

    data = recv_all(sock, timeout_idle=1.0)
    if not data:
        print("❌ No reply after handshake.")
        return None

    reply = data.decode("utf-8", "ignore").strip()
    print(f"↩ Handshake reply: {repr(reply)}")
    return reply


def probe_commands(sock: socket.socket, commands, timeout_idle: float = 1.0):
    """Sends a list of commands to the SOS server and returns their replies."""
    replies = []

    for cmd in commands:
        full = (cmd + "\n").encode("utf-8")
        try:
            sock.sendall(full)
        except OSError as e:
            print(f"❌ Failed to send {cmd}: {e}")
            replies.append(None)
            continue

        data = recv_all(sock, timeout_idle=timeout_idle)
        if not data:
            print(f"⚠️ No reply for {cmd}")
            replies.append(None)
            continue

        text = data.decode("utf-8", "ignore").strip()
        replies.append(text)

    return replies


# ---------------------------
# APP LOGIC
# ---------------------------

def fetch_now_playing():
    """Fetches SOS playlist and now playing info."""
    sock = try_connect(SOSHost, SOSPort)
    if not sock:
        return None, None, None

    if not do_handshake(sock):
        sock.close()
        return None, None, None

    # Get playlist and current clip
    commands = ["get_clip_count", "get_clip_info *"]
    clip_count, clip_list = probe_commands(sock, commands)

    current_clip_number = probe_commands(sock, ["get_clip_number"])[0]
    if current_clip_number:
        current_clip_number = current_clip_number.strip()
        title_cmd = f"get_clip_info {current_clip_number}"
        current_clip_title = probe_commands(sock, [title_cmd])[0]
    else:
        current_clip_title = "Unknown"

    sock.close()
    return clip_count, clip_list, current_clip_title


def update_gui_periodically(app: ImageApp, interval=5):
    """Background thread to periodically refresh SOS info."""
    while True:
        clip_count, clip_list, current_title = fetch_now_playing()
        if clip_list:
            app.root.after(0, lambda: app.update_playlist(clip_list))
        if current_title:
            app.root.after(0, lambda: app.update_playing(current_title))
        time.sleep(interval)


# ---------------------------
# MAIN
# ---------------------------

def main():
    root = tk.Tk()
    app = ImageApp(root)

    # Run the socket update in a background thread
    thread = threading.Thread(target=update_gui_periodically, args=(app, 10))
    thread.daemon = True
    thread.start()

    root.mainloop()


if __name__ == "__main__":
    main()
