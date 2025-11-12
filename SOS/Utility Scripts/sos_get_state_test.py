"""
Test SOS get_state Command

Connects to the SOS server via socket, sends the get_state command, and prints the raw response.
"""

import socket
import time

SOS_HOST = "10.10.51.87"
SOS_PORT = 2468


def main():
    print(f"Connecting to SOS at {SOS_HOST}:{SOS_PORT}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)  # Use the original timeout
    s.connect((SOS_HOST, SOS_PORT))
    # Send enable handshake
    s.sendall(b"enable\n")
    handshake = s.recv(1024).decode('utf-8').strip()
    print(f"Handshake response: {handshake}")
    print("Sending get_state command...")
    s.sendall(b"get_all_name_value_pairs 2\n")
    time.sleep(0.2)
    # Read all data until socket closes or timeout
    full_response = ""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            full_response += chunk.decode('utf-8', errors='replace')
            if '}' in full_response or ']' in full_response:
                break
    except socket.timeout:
        pass
    print("Raw get_state response:")
    print(full_response)
    s.close()

if __name__ == "__main__":
    main()
