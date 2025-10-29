import tkinter as tk
from PIL import Image, ImageTk
import socket
import time 

bgImageDir = "Now_Playing/bg.jpg"
SOSPort = 2468
SOSHost = "10.1.1.107"

class ImageApp:
    """ImageApp creates a GUI app to display the current playing title and playlist from SOS."""

    def __init__(self, root, image_path):
        self.root = root
        self.root.title("SOS Now Playing")

        # Load and display the image (what image???)
        image = Image.open(image_path)
        self.image_tk = ImageTk.PhotoImage(image)
        self.image = tk.Label(root, image=self.image_tk)
        self.image.pack()

        # Create a label for currently playing
        self.text_label = tk.Label(root, text="Current Title", font=("Times New Roman", 18))
        self.text_label.place(relx=0.5, rely=0.1, anchor="center")

        # Create a label for playlist
        self.playlist = tk.Label(root,text="BIG OL' Playlist ", font=("Comic Sans",16))
        self.playlist.place(relx=0.1, rely=0.3, anchor="center")

    def update_playing(self, current):
        """Updates the text on the label."""
        self.text_label.config(text=current)

    def create_playlist(self,clipCount,playlistClips):
        #create a playlist based on recording the list of items in sos playlist
        self.playlist.config(text=playlistClips)


def try_connect(host: str, port: int, timeout: float = 4.0):
    """Connect to the SOS TCP control socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        print(f"Connecting to SOS server {host}:{port} (timeout={timeout}s)...")
        sock.connect((host, port))
        print(":D Yay! TCP connection established")
        return sock
    except OSError as e:
        print(f">:[ Grr. Connection failed: {e}. Are you connected to the SOS network?")
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
        print(f"Failed to send handshake: {e}")
        return None

    data = recv_all(sock, timeout_idle=1.0)
    if not data:
        print("No reply after handshake.")
        return None

    reply = data.decode("utf-8", "ignore").strip()
    print(f"Handshake reply: {repr(reply)}")
    return reply

def probe_commands(sock: socket.socket, commands, timeout_idle: float = 1.0):
    """
    Sends a list of commands to the SOS server.
    Returns a list of replies in the same order as commands.
    """
    replies = []

    # print("\nProbing SOS server for information...\n")

    for cmd in commands:
        full = (cmd + "\n").encode("utf-8")
        # print(f"--> {cmd}")
        try:
            sock.sendall(full)
        except OSError as e:
            print(f"Failed to send: {e}")
            replies.append(None)
            continue

        data = recv_all(sock, timeout_idle=timeout_idle)
        if not data:
            print("BEEP! Error: No reply.\n")
            replies.append(None)
            continue

        text = data.decode("utf-8", "ignore").strip()
        # print(f"<-- Reply ({len(text)} bytes):\n{text}\n")
        replies.append(text)

    return replies

def main():
    host = "10.10.51.87"
    port = 2468

    # Step 1: Connect to SOS
    sock = try_connect(host, port)
    if not sock:
        print("Result: connection_failed")
        return

    # Step 2: Perform handshake
    reply = do_handshake(sock)
    if reply is None:
        print("Result: handshake_failed")
        sock.close()
        return

    # Step 3: Get clip count and playlist first
    commands = [
        "get_clip_count",
        "get_clip_info *"
    ]
    replies = probe_commands(sock, commands)
    clip_count, clip_list = replies

    # Step 4: Get current clip number
    print("Getting current clip number...")
    current_clip_number = probe_commands(sock, ["get_clip_number"])[0]
    print(f"Current clip number: {current_clip_number}")

    # Step 5: Use that number in get_clip_info <number>
    if current_clip_number:
        current_clip_number = current_clip_number.strip()
        get_info_cmd = f"get_clip_info {current_clip_number}"
        current_clip_title = probe_commands(sock, [get_info_cmd])[0]
    else:
        print("No clip number returned; cannot query current title.")
        current_clip_title = None

    # Step 6: Display results
    print("\n--- Parsed Replies ---")
    print(f"Clip Count: {clip_count}")
    print(f"Clip List: \n{clip_list}")
    print(f"Now Playing Clip Number: {current_clip_number}")
    print(f"Current Clip Title: {current_clip_title}")

    # Step 7: Send data to GUI generator


    # Step 8: Clean up
    sock.close()
    print("\nConnection closed.")

if __name__ == "__main__":
    main()

# def main():
#     root = tk.Tk()
#     app = ImageApp(root, bgImageDir)

#     # Start the socket communication thread
#     thread = threading.Thread(target=socket_thread, args=(app,))
#     thread.daemon = True
#     thread.start()

#     root.mainloop()