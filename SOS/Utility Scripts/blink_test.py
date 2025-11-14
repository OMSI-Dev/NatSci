"""
Simple socket client to test connection to Raspberry Pi from B-link.
Runs with connect.py on the Pi.
"""
import socket
import time

PI_IP = "10.10.51.97"  # Pi's IP address
PI_PORT = 4096         # Must match the port in nowPlaying.py

def main():
    print(f"Attempting to connect to Pi at {PI_IP}:{PI_PORT}...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # Increased timeout
            print(f"Connecting...")
            s.connect((PI_IP, PI_PORT))
            print("✅ Connected!")
            
            msg = "BLINK_TEST\n"
            s.sendall(msg.encode('utf-8'))
            print(f"Sent: '{msg.strip()}'")
            
            ack = s.recv(1024)
            response = ack.decode('utf-8', 'ignore').strip()
            print(f"✅ Received from Pi: '{response}'")
            
    except socket.timeout:
        print("❌ Connection timed out - Pi may not be reachable")
    except ConnectionRefusedError:
        print("❌ Connection refused - Pi server may not be running or firewall blocking")
    except Exception as e:
        print(f"❌ Error connecting to Pi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()