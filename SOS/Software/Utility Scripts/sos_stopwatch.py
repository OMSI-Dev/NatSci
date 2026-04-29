"""
Executes on the B-link device in the SOS network.
This is a standalone script for debugging that probes the SOS server for clip changes. 
Measures and prints the duration of each clip after it plays.
"""

import socket
import time
import sys

DEFAULT_SOS_IP = "10.0.0.16"  
DEFAULT_SOS_PORT = 2468        

def recv_data(sock: socket.socket, timeout_idle: float = 1.0) -> bytes:
    buffer = bytearray()
    orig_timeout = sock.gettimeout()
    try:
        sock.settimeout(0.2)
        start = time.time()
        while True:
            try:
                chunk = sock.recv(4096)
                if chunk:
                    buffer.extend(chunk)
                    start = time.time()
                else:
                    break
            except socket.timeout:
                if time.time() - start >= timeout_idle:
                    break
    finally:
        sock.settimeout(orig_timeout)
    return bytes(buffer)

class SOSStopwatch:
    def __init__(self, sos_ip=DEFAULT_SOS_IP, sos_port=DEFAULT_SOS_PORT):
        self.sos_ip = sos_ip
        self.sos_port = sos_port
        self.sock = None
        self.running = True
        self.clip_start_time = None
        self.last_clip = ""

    def connect_to_sos(self, timeout=4):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            print(f"Connecting to SOS at {self.sos_ip}:{self.sos_port}...")
            self.sock.connect((self.sos_ip, self.sos_port))
            print("[Success] Connected to SOS server")
            self.sock.sendall(b'enable\n')
            data = self.sock.recv(1024)
            response = data.decode('utf-8', 'ignore').strip()
            if response == 'R':
                print("[Success] SOS Handshake successful\n")
                return True
            else:
                print(f"⚠ Unexpected handshake response: {response}")
                return True
        except Exception as e:
            print(f"✗ Error during SOS connection: {e}")
            return False

    def get_current_clip_name(self):
        if not self.sock:
            return ""
        try:
            self.sock.sendall(b'get_clip_number\n')
            data = self.sock.recv(1024)
            clip_number = data.decode('utf-8', 'ignore').strip()
            if not clip_number or not clip_number.isdigit():
                return ""
            cmd = f"get_clip_info {clip_number}\n".encode('utf-8')
            self.sock.sendall(cmd)
            data = self.sock.recv(2048)
            clip_name = data.decode('utf-8', 'ignore').strip()
            return clip_name
        except Exception:
            return ""

    def run(self, poll_interval=0.5):
        if not self.connect_to_sos():
            print("Failed to connect to SOS. Exiting.")
            return
        print("\nStopwatch measurement loop running...")
        self.clip_start_time = time.time()
        while self.running:
            time.sleep(poll_interval)
            clip_name = self.get_current_clip_name()
            if clip_name and clip_name != self.last_clip:
                if self.clip_start_time is not None and self.last_clip:
                    elapsed = time.time() - self.clip_start_time
                    print(f"[Stopwatch] '{self.last_clip}' duration: {elapsed:.2f}s\n")
                print(f"[Clip Change] Now playing: '{clip_name}'")
                self.clip_start_time = time.time()
                self.last_clip = clip_name
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        print("\nStopwatch script stopped.")

if __name__ == "__main__":
    # Use defaults unless overridden by command line
    sos_ip = DEFAULT_SOS_IP
    sos_port = DEFAULT_SOS_PORT
    if len(sys.argv) >= 3:
        sos_ip = sys.argv[1]
        sos_port = int(sys.argv[2])
    print(f"Using SOS IP: {sos_ip}, Port: {sos_port}")
    stopwatch = SOSStopwatch(sos_ip, sos_port)
    stopwatch.run()
