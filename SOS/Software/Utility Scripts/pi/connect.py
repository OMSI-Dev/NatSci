"""
Executes on the Raspberry Pi in the SOS network.
Simple socket server for Raspberry Pi communication, to run on the Pi side.
Runs with blink_test.py on the B-link.
"""
import socket
import traceback

PI_PORT = 4096

def pi_socket_server():
    print("[Pi] Socket server thread starting...")
    server_sock = None
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to all interfaces explicitly
        server_sock.bind(('0.0.0.0', PI_PORT))
        server_sock.listen(5)
        
        # Get the actual bound address
        bound_addr = server_sock.getsockname()
        print(f"[Pi] Socket server successfully bound to {bound_addr}")
        print(f"[Pi] Listening on all interfaces, port {PI_PORT}...")
        
    except Exception as e:
        print(f"[Pi] Socket server failed to start: {e}")
        if server_sock:
            server_sock.close()
        return

    while True:
        try:
            print("[Pi] Waiting for connection...")
            conn, addr = server_sock.accept()
            print(f"[Pi] ✅ Connection accepted from {addr}")
            
            data = conn.recv(1024)
            if data:
                msg = data.decode('utf-8', 'ignore').strip()
                print(f"[Pi] Received: '{msg}'")
                response = f"ACK: Received '{msg}'\n"
                conn.sendall(response.encode('utf-8'))
                print(f"[Pi] Sent acknowledgment")
            else:
                print("[Pi] No data received")
            
            conn.close()
            print("[Pi] Connection closed")
            
        except Exception as e:
            print(f"[Pi] Error in socket loop: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    pi_socket_server()