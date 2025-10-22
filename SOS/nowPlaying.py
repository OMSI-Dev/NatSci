import tkinter as tk
from PIL import Image, ImageTk
import socket
import threading
import time as sleep

bgImageDir = "Now_Playing/bg.jpg"
SOSPort = 2468
SOSHost = "10.1.1.107"


class ImageApp:
    def __init__(self, root, image_path):
        self.root = root
        self.root.title("SOS Now Playing")

        # Load and display the image
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


    def __init_socket__(self,attempts=1,debug=False):

        nowSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        nowSocket.settimeout(4)
        i = 0
        while i < attempts:
            try:
                nowSocket.connect((SOSHost, SOSPort))
                #Send Enable Signal
                nowSocket.sendall(b'enable\n')
                #Check to see if we got the 'R' reply
                data = nowSocket.recv(1024).decode()   
                if data.strip() == "R":
                    print("Recieved awknowledgement")
                break
            except socket.error:
                if debug:
                    print ("NETWORK START FAIL")
                    print ("Will display last known playlist.")
                    return (False,None)               
            i += 1
            if attempts:
                if attempts < i:
                    return (False,None)
                
        return (True,nowSocket)

def socket_thread(app):
    """Thread to handle socket communication."""
    success, sock = app.__init_socket__(attempts=1, debug=True)
    if success:
        try:
            while True:               
                #I dont think you need to send enable twice leaving as comment for testing
                #sock.sendall(b'enable\n')
                
                """
                Start with identify the number of videos in the playlist.
                Then get all the names of clips in the list.
                Create a playlist to be displayed.
                
                """
                sock.sendall("get_clip_count").encode()
                clipCount = sock.recv(1024).decode()
                print("current clip count:" + str(clipCount.strip()))
                sock.sendall("get_clip_info *").encode()
                playlistClips = sock.recv(1024).decode()
                print("Titles in current playlist: " + str(playlistClips.strip()))
                app.create_playlist(clipCount,playlistClips)
                # app.update_playing(f"Now Playing: {data.strip()}")
        except Exception as e:
            print(f"Socket Error: {e}")
        finally:
            sock.close()
    else:
        play = "Kevin\nPickles\njohn\nSPACE!\n"
        num = 10
        app.create_playlist(num,play)
        print("Failed to connect to SOS")

def main():
    root = tk.Tk()
    app = ImageApp(root, bgImageDir)

    # Start the socket communication thread
    thread = threading.Thread(target=socket_thread, args=(app,))
    thread.daemon = True
    thread.start()

    root.mainloop()


if __name__ == "__main__":
    main()
