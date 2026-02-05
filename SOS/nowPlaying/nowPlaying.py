import socket

PI_PORT = 4096
BUFFER_SIZE = 8192

english_titles = [None]
spanish_titles = [None]
durations = [None]
current_clip_number = None


def _parse_init_message(message: str) -> None:
    """Parse INIT message into numbered lists (index starts at 1)."""
    global english_titles, spanish_titles, durations

    lines = message.splitlines()
    if not lines:
        return

    data_lines = [line.strip() for line in lines[1:] if line.strip()]
    new_english = [None]
    new_spanish = [None]
    new_durations = [None]

    for line in data_lines:
        parts = line.split("|", 3)
        if len(parts) != 4:
            print(f"[Pi] Skipping malformed line: {line}")
            continue
        index_str, english, spanish, duration = [p.strip() for p in parts]
        if not index_str.isdigit():
            print(f"[Pi] Skipping non-numeric index: {line}")
            continue
        index = int(index_str)
        while len(new_english) <= index:
            new_english.append(None)
            new_spanish.append(None)
            new_durations.append(None)
        new_english[index] = english
        new_spanish[index] = spanish
        new_durations[index] = duration

    english_titles = new_english
    spanish_titles = new_spanish
    durations = new_durations

    print("[Pi] INIT received.")
    print(f"[Pi] English titles: {english_titles}")
    print(f"[Pi] Spanish titles: {spanish_titles}")
    print(f"[Pi] Durations: {durations}")


def _handle_clip_message(message: str) -> None:
    """Handle CLIP message and map to stored playlist data."""
    global current_clip_number

    clip_str = message.split(":", 1)[1].strip() if ":" in message else ""
    if not clip_str.isdigit():
        print(f"[Pi] Invalid CLIP message: {message}")
        return

    current_clip_number = int(clip_str)
    english = english_titles[current_clip_number] if current_clip_number < len(english_titles) else None
    spanish = spanish_titles[current_clip_number] if current_clip_number < len(spanish_titles) else None
    duration = durations[current_clip_number] if current_clip_number < len(durations) else None

    print(f"[Pi] Current clip number: {current_clip_number}")
    print(f"[Pi] Clip English: {english}")
    print(f"[Pi] Clip Spanish: {spanish}")
    print(f"[Pi] Clip Duration: {duration}")


def pi_socket_server() -> None:
    """Socket server that receives INIT and CLIP data from Beelink."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', PI_PORT))
    server_sock.listen(5)

    bound_addr = server_sock.getsockname()
    print(f"[Pi] Socket server bound to {bound_addr}")
    print(f"[Pi] Listening on port {PI_PORT}...")

    while True:
        conn, addr = server_sock.accept()
        print(f"[Pi] Connection from {addr}")

        data = bytearray()
        while True:
            chunk = conn.recv(BUFFER_SIZE)
            if not chunk:
                break
            data.extend(chunk)

        if data:
            message = data.decode('utf-8', 'ignore').strip()
            print(f"[Pi] Received: {message}")

            if message.startswith("INIT"):
                _parse_init_message(message)
            elif message.startswith("CLIP:"):
                _handle_clip_message(message)
            else:
                print(f"[Pi] Unknown message: {message}")

            conn.sendall(b"ACK\n")
        else:
            print("[Pi] No data received")

        conn.close()


def main() -> None:
    pi_socket_server()


if __name__ == "__main__":
    main()

