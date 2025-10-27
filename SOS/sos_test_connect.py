
import socket
import argparse
import time


def try_connect(host: str, port: int, timeout: float = 4.0, verbose: bool = True):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        if verbose:
            print(f"Connecting to {host}:{port} (timeout={timeout}s)")
        sock.connect((host, port))
        if verbose:
            print("-> TCP connection established")
        return sock
    except OSError as e:
        if verbose:
            print(f"-> Connection failed: {e} (errno={getattr(e, 'errno', None)})")
        sock.close()
        return None


def recv_all(sock: socket.socket, timeout_idle: float = 1.0, chunk: int = 4096, verbose: bool = False) -> bytes:
    """Receive data until the socket is idle for `timeout_idle` seconds.

    This helps collect large server replies sent in multiple TCP segments
    without depending on a single recv() size.
    """
    buffer = bytearray()
    # temporarily set a small timeout for chunk reads
    orig_timeout = sock.gettimeout()
    try:
        sock.settimeout(0.2)
        idle = 0.0
        start = time.time()
        while True:
            try:
                chunk_data = sock.recv(chunk)
                if chunk_data:
                    buffer.extend(chunk_data)
                    # reset idle timer
                    start = time.time()
                    if verbose:
                        print(f"recv_all: got {len(chunk_data)} bytes (total {len(buffer)})")
                    continue
                else:
                    # remote closed the socket
                    if verbose:
                        print("recv_all: remote closed socket")
                    break
            except socket.timeout:
                # check how long we've been idle
                idle = time.time() - start
                if idle >= timeout_idle:
                    break
                # else, continue trying until timeout_idle reached
                continue
    finally:
        try:
            sock.settimeout(orig_timeout)
        except Exception:
            pass
    return bytes(buffer)


def do_handshake(sock: socket.socket, timeout: float = 4.0, verbose: bool = True):
    """Send enable handshake and return decoded reply (or None on error)"""
    sock.settimeout(timeout)
    try:
        if verbose:
            print("Sending handshake: 'enable\\n'")
        sock.sendall(b'enable\n')
    except OSError as e:
        if verbose:
            print(f"-> Failed to send handshake: {e}")
        return None

    # use recv_all to collect a complete reply
    try:
        data = recv_all(sock, timeout_idle=1.0, verbose=(verbose and False))
        if not data:
            if verbose:
                print("-> No data received after handshake (socket closed?)")
            return None
        text = data.decode('utf-8', 'ignore').strip()
        if verbose:
            print(f"<- Handshake reply: {repr(text)}")
        return text
    except socket.timeout:
        if verbose:
            print("-> Timed out waiting for handshake reply")
        return None
    except OSError as e:
        if verbose:
            print(f"-> Error receiving handshake reply: {e}")
        return None


def ask_clip_number(sock: socket.socket, timeout: float = 4.0, verbose: bool = True):
    try:
        if verbose:
            print("Requesting current clip number: 'get_clip_number\\n'")
        sock.sendall(b'get_clip_number\n')
    except OSError as e:
        if verbose:
            print(f"-> Failed to send get_clip_number: {e}")
        return None

    try:
        data = recv_all(sock, timeout_idle=0.8)
        if not data:
            if verbose:
                print("-> No data received for clip number")
            return None
        text = data.decode('utf-8', 'ignore').strip()
        if verbose:
            print(f"<- get_clip_number reply: {repr(text)}")
        return text
    except socket.timeout:
        if verbose:
            print("-> Timed out waiting for get_clip_number reply")
        return None
    except OSError as e:
        if verbose:
            print(f"-> Error receiving clip number: {e}")
        return None


def ask_clip_info(sock: socket.socket, clipnum: str, timeout: float = 4.0, verbose: bool = True):
    try:
        cmd = f"get_clip_info *\n".encode('utf-8')
        if verbose:
            print(f"Requesting clip info: {cmd!r}")
        sock.sendall(cmd)
    except OSError as e:
        if verbose:
            print(f"-> Failed to send get_clip_info: {e}")
        return None

    try:
        data = recv_all(sock, timeout_idle=1.0)
        if not data:
            if verbose:
                print("-> No data received for clip info")
            return None
        text = data.decode('utf-8', 'ignore').strip()
        if verbose:
            print(f"<- get_clip_info reply: {repr(text)}")
        return text
    except socket.timeout:
        if verbose:
            print("-> Timed out waiting for get_clip_info reply")
        return None
    except OSError as e:
        if verbose:
            print(f"-> Error receiving clip info: {e}")
        return None


def main():
    p = argparse.ArgumentParser(description="SOS lightweight connection tester")
    p.add_argument("--host", default="10.10.51.87", help="SOS server IP or hostname")
    p.add_argument("--port", type=int, default=2468, help="SOS server port to test")
    p.add_argument("--timeout", type=float, default=4.0, help="socket timeout seconds")
    p.add_argument("--no-handshake", action='store_true', help="Skip sending 'enable' handshake (for manual servers)")
    p.add_argument("--verbose", action='store_true', default=True, help="Verbose output")
    p.add_argument("--make-list", metavar='FILE', help="Write the output of `get_clip_info *` to FILE")
    p.add_argument("--apply-list", metavar='FILE', help="Send `get_clip_list_from_file FILE` to the server after creating FILE")
    p.add_argument("--fetch-all", action='store_true', help="Force fetching per-clip info by iterating get_clip_info <n>")
    p.add_argument("--probe", action='store_true', help="Probe the server with a set of likely commands and print replies")
    args = p.parse_args()

    verbose = args.verbose

    sock = try_connect(args.host, args.port, timeout=args.timeout, verbose=verbose)
    if not sock:
        print("Result: connection_failed")
        return

    def get_clip_info_all(sock: socket.socket, timeout: float = 4.0, verbose: bool = True):
        """Request the full playlist info via `get_clip_info *` and return raw text or None."""
        try:
            if verbose:
                print("Requesting full playlist: 'get_clip_info *\\n'")
            sock.sendall(b'get_clip_info *\n')
        except OSError as e:
            if verbose:
                print(f"-> Failed to send get_clip_info *: {e}")
            return None

        try:
            data = sock.recv(16384)
            if not data:
                if verbose:
                    print("-> No data received for get_clip_info *")
                return None
            text = data.decode('utf-8', 'ignore').strip()
            if verbose:
                print(f"<- get_clip_info * reply length={len(text)}")
            return text
        except socket.timeout:
            if verbose:
                print("-> Timed out waiting for get_clip_info * reply")
            return None
        except OSError as e:
            if verbose:
                print(f"-> Error receiving get_clip_info * reply: {e}")
            return None

    def write_list_file(path: str, content: str):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Wrote playlist output to {path}")
            return True
        except Exception as e:
            print(f"Failed to write file {path}: {e}")
            return False

    def send_get_clip_list_from_file(sock: socket.socket, path: str, timeout: float = 4.0, verbose: bool = True):
        cmd = f"get_clip_list_from_file {path}\n".encode('utf-8')
        try:
            if verbose:
                print(f"Sending command: {cmd!r}")
            sock.sendall(cmd)
        except OSError as e:
            if verbose:
                print(f"-> Failed to send get_clip_list_from_file: {e}")
            return None

        try:
            data = recv_all(sock, timeout_idle=1.0)
            if not data:
                if verbose:
                    print("-> No data received after get_clip_list_from_file")
                return None
            text = data.decode('utf-8', 'ignore').strip()
            if verbose:
                print(f"<- get_clip_list_from_file reply: {repr(text)}")
            return text
        except socket.timeout:
            if verbose:
                print("-> Timed out waiting for get_clip_list_from_file reply")
            return None
        except OSError as e:
            if verbose:
                print(f"-> Error receiving get_clip_list_from_file reply: {e}")
            return None

    def ask_clip_count(sock: socket.socket, timeout: float = 4.0, verbose: bool = True):
        try:
            if verbose:
                print("Requesting clip count: 'get_clip_count\\n'")
            sock.sendall(b'get_clip_count\n')
        except OSError as e:
            if verbose:
                print(f"-> Failed to send get_clip_count: {e}")
            return None

        try:
            data = recv_all(sock, timeout_idle=0.8)
            if not data:
                if verbose:
                    print("-> No data received for get_clip_count")
                return None
            text = data.decode('utf-8', 'ignore').strip()
            if verbose:
                print(f"<- get_clip_count reply: {repr(text)}")
            try:
                return int(text)
            except ValueError:
                return None
        except socket.timeout:
            if verbose:
                print("-> Timed out waiting for get_clip_count reply")
            return None
        except OSError as e:
            if verbose:
                print(f"-> Error receiving get_clip_count reply: {e}")
            return None

    def ask_clip_info_num(sock: socket.socket, clipnum: int, timeout: float = 4.0, verbose: bool = True):
        try:
            cmd = f"get_clip_info {clipnum}\n".encode('utf-8')
            if verbose:
                print(f"Requesting clip info for #{clipnum}: {cmd!r}")
            sock.sendall(cmd)
        except OSError as e:
            if verbose:
                print(f"-> Failed to send get_clip_info {clipnum}: {e}")
            return None

        try:
            data = sock.recv(2048)
            if not data:
                if verbose:
                    print(f"-> No data received for get_clip_info {clipnum}")
                return None
            text = data.decode('utf-8', 'ignore').strip()
            if verbose:
                print(f"<- get_clip_info {clipnum} reply: {repr(text)}")
            return text
        except socket.timeout:
            if verbose:
                print(f"-> Timed out waiting for get_clip_info {clipnum} reply")
            return None
        except OSError as e:
            if verbose:
                print(f"-> Error receiving get_clip_info {clipnum} reply: {e}")
            return None

    def probe_commands(sock: socket.socket, commands, timeout_idle: float = 1.0, verbose: bool = True):
        """Send a list of textual commands to the server and print replies.

        Useful to discover undocumented API commands that may expose file paths.
        """
        results = {}
        for cmd in commands:
            full = (cmd + '\n').encode('utf-8')
            try:
                if verbose:
                    print(f"--> {cmd}")
                sock.sendall(full)
            except OSError as e:
                results[cmd] = f"send_error: {e}"
                continue
            try:
                data = recv_all(sock, timeout_idle=timeout_idle)
                if not data:
                    results[cmd] = ''
                    if verbose:
                        print("   (no reply)")
                else:
                    text = data.decode('utf-8', 'ignore')
                    results[cmd] = text
                    if verbose:
                        print(text)
            except Exception as e:
                results[cmd] = f"recv_error: {e}"
        return results

    try:
        if not args.no_handshake:
            reply = do_handshake(sock, timeout=args.timeout, verbose=verbose)
            if reply is None:
                print("Result: handshake_failed")
                return
            if reply != 'R':
                print("Result: handshake_unexpected_reply")
                # continue to try commands anyway — some SOS builds reply differently

        # If user requested a probe, run a set of likely commands and exit
        if args.probe:
            # candidate commands to probe for file-path or metadata responses
            probe_list = [
                'help', '?', 'list_commands', 'get_commands',
                'get_clip_filename', 'get_clip_path', 'get_clip_filepath',
                'get_clip_info_full', 'get_clip_details', 'get_clip_meta',
                'get_clip_list', 'get_clip_list_full', 'get_clip_data',
                'get_dataset_file', 'get_media_path', 'get_file_path',
                'get_file_name', 'get_clip_attributes', 'get_clip_files',
                'get_media_info', 'get_media_list'
            ]
            print("Probing server for additional commands (this may take a few seconds)...")
            results = probe_commands(sock, probe_list, timeout_idle=1.0, verbose=True)
            print("\nProbe results summary:\n")
            for cmd, out in results.items():
                print(f"--- {cmd} ---\n{out}\n")
            return

        # If requested, fetch the full playlist and optionally write it to a file
        if args.make_list:
            # Prefer `get_clip_info *` output unless user forced per-clip fetching
            full = None
            if not args.fetch_all:
                full = get_clip_info_all(sock, timeout=args.timeout, verbose=verbose)

            # If get_clip_info * failed or doesn't contain obvious file paths, fall back to per-clip
            need_per_clip = False
            if full is None:
                need_per_clip = True
            else:
                # heuristic: presence of path separators or common media extensions
                lowered = full.lower()
                has_pathsep = ('\\' in full) or ('/' in full)
                has_ext = any(ext in lowered for ext in ('.mp4', '.mov', '.mp3', '.png', '.jpg', '.tif', '.tiff'))
                if not (has_pathsep or has_ext):
                    need_per_clip = True

            if need_per_clip:
                if verbose:
                    print("Falling back to per-clip fetch (get_clip_count + get_clip_info <n>)")
                count = ask_clip_count(sock, timeout=args.timeout, verbose=verbose)
                if count is None or count <= 0:
                    print("Result: failed_get_clip_count")
                    return
                items = []
                for n in range(1, count+1):
                    info = ask_clip_info_num(sock, n, timeout=args.timeout, verbose=verbose)
                    items.append(info or '')
                full = '\n'.join(items)

            if full is None:
                print("Result: failed_get_clip_info_all")
                return

            if not write_list_file(args.make_list, full):
                print("Result: failed_write_list_file")
                return

            # If user also requested applying the list, send the command now
            if args.apply_list:
                resp = send_get_clip_list_from_file(sock, args.apply_list, timeout=args.timeout, verbose=verbose)
                if resp is None:
                    print("Result: failed_apply_list")
                else:
                    print("Result: applied_list")
            else:
                print("Result: wrote_list")
            return

        clipnum = ask_clip_number(sock, timeout=args.timeout, verbose=verbose)
        if clipnum is None:
            print("Result: no_clip_number")
            return

        # If clipnum looks numeric, request info
        if clipnum.strip().isdigit():
            info = ask_clip_info(sock, clipnum.strip(), timeout=args.timeout, verbose=verbose)
            if info is None:
                print("Result: no_clip_info")
                return
            print("Result: success")
            print(f"Current clip name: {info}")
        else:
            print("Result: clip_number_not_numeric_or_empty")
            print(f"get_clip_number returned: {clipnum!r}")

    finally:
        try:
            sock.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
