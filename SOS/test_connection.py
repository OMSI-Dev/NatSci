#simple test to check if port 2468 is open on SOS server with IP 10.10.51.87

import socket
import sys

def test_port(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(4)
    print(f"Testing connection to {host}:{port}")
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"Port {port} is open")
            return True
        else:
            print(f"Port {port} is closed or not responding (Error code: {result})")
            return False
    except socket.gaierror:
        print("Hostname could not be resolved")
    except socket.error as e:
        print(f"Error: {e}")
    finally:
        sock.close()
    return False

# Test the SOS server port
test_port("10.10.51.87", 2468)