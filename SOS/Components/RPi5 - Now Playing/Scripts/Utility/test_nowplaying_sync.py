"""
Tests for the nowPlaying sync logic (no display needed: pygame is stubbed).
Run: python3 test_nowplaying_sync.py
"""
import importlib.util
import json
import os
import socket
import sys
import threading
import time
import unittest
from unittest.mock import MagicMock

sys.modules.setdefault('pygame', MagicMock())

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
BEELINK_MAIN = os.path.normpath(os.path.join(SCRIPTS, '..', '..', 'Beelink - SOS Ring', 'main'))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


np = _load('nowPlaying', os.path.join(SCRIPTS, 'nowPlaying.py'))

BODY = ["1|Alpha|Alfa|90", "2|Beta|Beta es|120", "3|Gamma|Gama|0"]


def init_text(entries=BODY, digest=None, count=None):
    digest = digest or np._digest(entries)
    count = len(entries) if count is None else count
    return "\n".join([f"INIT {digest} {count}"] + entries) + "\n"


class FakeCache:
    current_playlist = {'clips': [{'name': 'a'}, {'name': 'b'}]}

    def get_clip_titles(self, name):
        return ({'a': 'Alfa'}.get(name), {'a': 'Alpha'}.get(name))

    def get(self, name):
        return {'a': {'duration': 90.4}, 'b': {'movie-title': 'Bee | Movie', 'timer': '120'}}[name]


class ParseTests(unittest.TestCase):
    def test_init_clip_pause_in_one_payload(self):
        p = np.parse_payload(init_text() + "PAUSE\n\nCLIP:2\n")
        self.assertEqual(len(p['init']['entries']), 3)
        self.assertTrue(p['pause'])
        self.assertEqual(p['clip'], 2)

    def test_legacy_init_without_header(self):
        p = np.parse_payload("INIT\n" + "\n".join(BODY))
        self.assertEqual(len(p['init']['entries']), 3)
        self.assertIsNone(p['init']['header_digest'])

    def test_malformed_lines_counted(self):
        p = np.parse_payload("INIT\n1|a|b|1\ngarbage\n0|x|y|1\n")
        self.assertEqual(len(p['init']['entries']), 1)
        self.assertEqual(len(p['init']['malformed']), 2)

    def test_bad_clip_and_state(self):
        self.assertEqual(np.parse_payload("CLIP:abc")['clip'], np.INVALID_CLIP)
        self.assertEqual(np.parse_payload("STATE abcd1234 - 1")['state'], ('abcd1234', None, True))
        self.assertIsNone(np.parse_payload("STATE abcd1234 x 1")['state'])

    def test_digest_matches_beelink_module(self):
        proto = _load('nowplaying_protocol', os.path.join(BEELINK_MAIN, 'nowplaying_protocol.py'))
        message, digest, count = proto.build_init_message(FakeCache())
        parsed = np.parse_payload(message)
        self.assertEqual(count, 2)
        self.assertEqual(parsed['init']['digest'], digest)
        self.assertEqual(parsed['init']['header_digest'], digest)
        self.assertEqual(parsed['init']['entries'][1][1].split(), ['Bee', 'Movie'])  # '|' sanitized
        line = proto.build_state_line(digest, 2, True)
        self.assertEqual(np.parse_payload(line)['state'], (digest, 2, True))


class StateTests(unittest.TestCase):
    def setUp(self):
        self.s = np.SyncState()

    def test_push_applies_and_heartbeat_ok(self):
        self.s.apply_payload(init_text() + "CLIP:2\n", 'push', sender=np.ENGINE_IP)
        snap = self.s.snapshot()
        self.assertEqual(snap.english[2], 'Beta')
        self.assertEqual(snap.clip, 2)
        _, reply = self.s.apply_payload(f"STATE {self.s.digest} 2 0", 'push')
        self.assertTrue(reply.startswith('ACK OK'))
        self.assertTrue(self.s.status()['in_sync'])

    def test_heartbeat_mismatch_debounced(self):
        self.s.apply_payload(init_text(), 'push')
        self.s.apply_payload("STATE deadbeef - 0", 'push')
        self.assertFalse(self.s.resync_requested.is_set())
        self.s.apply_payload("STATE deadbeef - 0", 'push')
        self.assertTrue(self.s.resync_requested.is_set())
        self.assertFalse(self.s.status()['in_sync'])

    def test_empty_init_does_not_wipe_playlist(self):
        self.s.apply_payload(init_text(), 'push')
        self.s.apply_payload("INIT 00000000 0\n", 'push')
        self.assertEqual(self.s.status()['items'], 3)
        self.assertEqual(self.s.stats['init_rejected'], 1)

    def test_damaged_init_requests_resync(self):
        self.s.apply_payload(init_text(digest='00000000', count=5), 'push')
        self.assertTrue(self.s.resync_requested.is_set())

    def test_clip_outside_playlist_requests_resync(self):
        self.s.apply_payload("CLIP:7", 'push')
        self.assertTrue(self.s.resync_requested.is_set())

    def test_stale_pull_never_overwrites_newer_push(self):
        self.s.apply_payload(init_text(), 'push')
        baseline = self.s.baseline()
        self.s.apply_payload("CLIP:3", 'push')  # push lands while the pull is in flight
        old = init_text(["1|Old|Viejo|5"]) + "UNPAUSE\n\nCLIP:1\n"
        self.s.apply_payload(old, 'pull', baseline=baseline)
        snap = self.s.snapshot()
        self.assertEqual(snap.clip, 3)               # newer push kept
        self.assertEqual(snap.english[1], 'Old')     # untouched part (init) taken from pull
        self.assertEqual(self.s.stats['pull_parts_skipped_stale'], 1)

    def test_pause_state(self):
        self.s.apply_payload("PAUSE", 'push')
        self.assertTrue(self.s.snapshot().paused)
        self.s.apply_payload("UNPAUSE", 'push')
        self.assertFalse(self.s.snapshot().paused)

    def test_unknown_message_recorded(self):
        self.s.apply_payload("HELLO", 'push')
        self.assertEqual(self.s.stats['unknown_messages'], 1)


class SocketTests(unittest.TestCase):
    def test_server_roundtrip_and_status(self):
        np.state = np.SyncState()
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', 0))
        server.listen(5)
        port = server.getsockname()[1]
        np.running = True
        threading.Thread(target=np.socket_server_loop, args=(server,), daemon=True).start()

        def send(text):
            with socket.create_connection(('127.0.0.1', port), timeout=3) as c:
                c.sendall(text.encode())
                c.shutdown(socket.SHUT_WR)
                return c.recv(65536).decode()

        try:
            self.assertEqual(send(init_text() + "CLIP:1\n").strip(), 'ACK')
            status = json.loads(send("STATUS"))
            self.assertEqual(status['items'], 3)
            self.assertEqual(status['clip'], 1)
            self.assertIn('stats', status)
        finally:
            np.running = False
            server.close()


if __name__ == '__main__':
    unittest.main()
