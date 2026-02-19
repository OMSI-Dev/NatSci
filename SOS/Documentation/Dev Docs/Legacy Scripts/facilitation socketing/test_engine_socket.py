"""
Test Script for Engine Socket Server (B-link)
Tests receiving commands from HTTP server and forwarding to nowPlaying.

Usage:
    python test_engine_socket.py

Expected behavior:
    - Listens on port 5000 for commands from HTTP server
    - Processes facilitation toggle commands
    - Forwards PAUSE/UNPAUSE commands to nowPlaying (port 4096)
    - Handles volume control commands (simulated)
"""

import socket
import sys
import time
import json
import threading

# Configuration
HTTP_SERVER_PORT = 5000  # Port to receive commands from HTTP
PI_IP = "10.10.51.111"  # Raspberry Pi IP on network (use "localhost" for same-machine testing)
PI_PORT = 4096  # Port to send commands to nowPlaying

# State
facilitation_mode = False
audio_volume = 50
audio_muted = False


print("=" * 60)
print("Engine Configuration")
print("=" * 60)
print(f"HTTP Server Port: {HTTP_SERVER_PORT}")
print(f"nowPlaying Target: {PI_IP}:{PI_PORT}")
print(f"Note: Change PI_IP to 'localhost' for same-machine testing")
print("=" * 60)


def recv_data(sock: socket.socket, timeout_idle: float = 1.0) -> bytes:
    """Receive data from socket until idle timeout."""
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


def parse_http_request(data: bytes) -> tuple:
    """
    Parse HTTP request and extract JSON body.
    Returns (is_http, json_body, method, path)
    """
    try:
        request_text = data.decode('utf-8', errors='ignore')
        
        # Check if it's an HTTP request
        if not (request_text.startswith('POST') or request_text.startswith('GET') or request_text.startswith('OPTIONS')):
            # Not HTTP, return as-is
            return (False, request_text, None, None)
        
        # Split headers and body
        parts = request_text.split('\r\n\r\n', 1)
        if len(parts) < 2:
            parts = request_text.split('\n\n', 1)
        
        if len(parts) < 2:
            return (False, request_text, None, None)
        
        headers_text = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        
        # Parse first line for method and path
        first_line = headers_text.split('\n')[0]
        method = first_line.split(' ')[0] if ' ' in first_line else 'POST'
        path = first_line.split(' ')[1] if len(first_line.split(' ')) > 1 else '/'
        
        return (True, body, method, path)
        
    except Exception as e:
        print(f"[Engine] Error parsing HTTP request: {e}")
        return (False, data.decode('utf-8', errors='ignore'), None, None)


def send_http_response(conn: socket.socket, data: dict, status_code: int = 200):
    """Send HTTP response with CORS headers."""
    status_messages = {
        200: "OK",
        400: "Bad Request",
        500: "Internal Server Error"
    }
    
    status_message = status_messages.get(status_code, "OK")
    response_body = json.dumps(data)
    
    # Build HTTP response with CORS headers
    response = f"HTTP/1.1 {status_code} {status_message}\r\n"
    response += "Content-Type: application/json\r\n"
    response += f"Content-Length: {len(response_body)}\r\n"
    response += "Access-Control-Allow-Origin: *\r\n"
    response += "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
    response += "Access-Control-Allow-Headers: Content-Type\r\n"
    response += "Connection: close\r\n"
    response += "\r\n"
    response += response_body
    
    conn.sendall(response.encode('utf-8'))


def send_to_nowplaying(command: str) -> bool:
    """Send command to nowPlaying via socket (matches original engine.py pattern)."""
    print(f"[Engine] Attempting to connect to nowPlaying at {PI_IP}:{PI_PORT}...")
    try:
        # Use create_connection like original engine.py
        with socket.create_connection((PI_IP, PI_PORT), timeout=3.0) as sock:
            print(f"[Engine] Connected! Sending command: {command}")
            sock.sendall(command.encode('utf-8'))
            
            # Wait for acknowledgment
            sock.settimeout(2.0)
            try:
                response = sock.recv(1024)
                if response:
                    print(f"[Engine] nowPlaying responded: {response.decode('utf-8', errors='ignore').strip()}")
                    return True
            except socket.timeout:
                print(f"[Engine] No response from nowPlaying (timeout)")
                return True  # Command was sent, just no response
        
        return True
        
    except ConnectionRefusedError:
        print(f"[Engine] ⚠ Connection refused by {PI_IP}:{PI_PORT}")
        print(f"[Engine] ⚠ Make sure test_nowplaying.py is running on the Pi")
        print(f"[Engine] ⚠ Check firewall rules on the Pi")
        return False
    except socket.timeout:
        print(f"[Engine] ⚠ Connection timeout to {PI_IP}:{PI_PORT}")
        print(f"[Engine] ⚠ Check network connectivity and firewall")
        return False
    except socket.error as e:
        print(f"[Engine] ⚠ Network error: {e}")
        print(f"[Engine] ⚠ Make sure Pi is reachable at {PI_IP}")
        print(f"[Engine] ⚠ Facilitation mode changed in engine, but display NOT updated")
        return False


def handle_facilitation_toggle(enable: bool):
    """Handle facilitation mode toggle."""
    global facilitation_mode
    
    facilitation_mode = enable
    
    if enable:
        print("[Engine] ▶ FACILITATION MODE ON")
        print("[Engine]   → Pausing nowPlaying")
        print("[Engine]   → Muting audio")
        
        # Send pause command to nowPlaying
        send_to_nowplaying("PAUSE")
        
        # Mute audio (simulated for now)
        print("[Engine]   → Audio muted (simulated)")
        
    else:
        print("[Engine] ▶ FACILITATION MODE OFF")
        print("[Engine]   → Unpausing nowPlaying")
        print("[Engine]   → Unmuting audio")
        
        # Send unpause command to nowPlaying
        send_to_nowplaying("UNPAUSE")
        
        # Unmute audio (simulated)
        print("[Engine]   → Audio unmuted (simulated)")


def handle_volume_control(action: str):
    """Handle volume control commands."""
    global audio_volume, audio_muted
    
    if action == "UP":
        audio_volume = min(100, audio_volume + 10)
        print(f"[Engine] ▶ Volume UP → {audio_volume}%")
    elif action == "DOWN":
        audio_volume = max(0, audio_volume - 10)
        print(f"[Engine] ▶ Volume DOWN → {audio_volume}%")
    elif action == "MUTE":
        audio_muted = not audio_muted
        status = "MUTED" if audio_muted else "UNMUTED"
        print(f"[Engine] ▶ Audio {status}")
    
    # In production, send MPV IPC commands here
    print(f"[Engine] (MPV command would be sent here)")


def handle_command(message: str) -> dict:
    """Process received command and return response."""
    try:
        # Strip whitespace and try to parse as JSON
        message = message.strip()
        if not message:
            return {"status": "error", "message": "Empty command"}
        
        data = json.loads(message)
        command = data.get("command", "").upper()
        
        if command == "FACILITATION_TOGGLE":
            enable = data.get("enable", False)
            handle_facilitation_toggle(enable)
            return {"status": "ok", "facilitation_mode": facilitation_mode}
        
        elif command == "VOLUME_CONTROL":
            action = data.get("action", "").upper()
            handle_volume_control(action)
            return {"status": "ok", "volume": audio_volume, "muted": audio_muted}
        
        elif command == "GET_STATE":
            return {
                "status": "ok",
                "facilitation_mode": facilitation_mode,
                "volume": audio_volume,
                "muted": audio_muted
            }
        
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}
            
    except json.JSONDecodeError as e:
        # Handle simple text commands
        message = message.strip().upper()
        
        if message == "FACILITATION_ON":
            handle_facilitation_toggle(True)
            return {"status": "ok", "facilitation_mode": True}
        elif message == "FACILITATION_OFF":
            handle_facilitation_toggle(False)
            return {"status": "ok", "facilitation_mode": False}
        else:
            return {"status": "error", "message": f"Invalid JSON: {str(e)}"}


def start_server():
    """Start socket server to receive commands from HTTP."""
    print("=" * 60)
    print("Engine Test Server (B-link)")
    print("=" * 60)
    print(f"Listening on port {HTTP_SERVER_PORT} (HTTP → Engine)")
    print(f"Will forward to {PI_IP}:{PI_PORT} (Engine → nowPlaying)")
    print("Waiting for commands from HTTP server...")
    print("Press Ctrl+C to exit")
    print("=" * 60)
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind(('0.0.0.0', HTTP_SERVER_PORT))
    except OSError as e:
        print(f"[ERROR] Cannot bind to port {HTTP_SERVER_PORT}")
        print(f"[ERROR] {e}")
        print("\nTroubleshooting:")
        print("  1. Check if another instance is running")
        print("  2. Try a different port")
        print("  3. Wait a moment and try again")
        sys.exit(1)
    
    server_sock.listen(5)
    server_sock.settimeout(1.0)  # Non-blocking with timeout
    
    print(f"[Engine] Server started successfully")
    print(f"[Engine] Bound to 0.0.0.0:{HTTP_SERVER_PORT} (HTTP commands)")
    print(f"[Engine] Will forward commands to {PI_IP}:{PI_PORT} (nowPlaying)")
    print(f"[Engine] Current state:")
    print(f"  - Facilitation mode: {'ON' if facilitation_mode else 'OFF'}")
    print(f"  - Volume: {audio_volume}%")
    print(f"  - Muted: {'YES' if audio_muted else 'NO'}")
    print(f"\n[Engine] Ready to receive commands...\n")
    
    try:
        while True:
            try:
                conn, addr = server_sock.accept()
                print(f"\n[Engine] Connection from {addr[0]}:{addr[1]}")
                
                # Receive data
                data = recv_data(conn)
                
                if data:
                    # Parse HTTP request
                    is_http, body, method, path = parse_http_request(data)
                    
                    if is_http:
                        print(f"[Engine] HTTP {method} request to {path}")
                        
                        # Handle OPTIONS preflight request
                        if method == "OPTIONS":
                            print("[Engine] Handling CORS preflight (OPTIONS)")
                            response = "HTTP/1.1 200 OK\r\n"
                            response += "Access-Control-Allow-Origin: *\r\n"
                            response += "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
                            response += "Access-Control-Allow-Headers: Content-Type\r\n"
                            response += "Content-Length: 0\r\n"
                            response += "Connection: close\r\n"
                            response += "\r\n"
                            conn.sendall(response.encode('utf-8'))
                            conn.close()
                            continue
                        
                        # Handle POST/GET with body
                        if body:
                            print(f"[Engine] Received: {body}")
                            
                            # Process command
                            response_data = handle_command(body)
                            
                            # Send HTTP response with CORS headers
                            send_http_response(conn, response_data)
                            print(f"[Engine] Sent response: {json.dumps(response_data)}")
                        else:
                            print("[Engine] No body in HTTP request")
                            send_http_response(conn, {"status": "error", "message": "No data in request"}, 400)
                    else:
                        # Non-HTTP request (raw socket from Python client)
                        print(f"[Engine] Received: {body}")
                        
                        # Process command
                        response_data = handle_command(body)
                        
                        # Send JSON response (not HTTP)
                        response_json = json.dumps(response_data)
                        conn.sendall(response_json.encode('utf-8'))
                        print(f"[Engine] Sent response: {response_json}")
                else:
                    print("[Engine] No data received")
                
                conn.close()
                
            except socket.timeout:
                # No connection, continue waiting
                pass
            except KeyboardInterrupt:
                print("\n\n[Engine] Shutting down...")
                break
                
    finally:
        server_sock.close()
        print("[Engine] Server closed")


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n[Engine] Interrupted by user")
        sys.exit(0)
