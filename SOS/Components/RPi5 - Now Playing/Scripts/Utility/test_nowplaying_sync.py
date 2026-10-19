"""
Tests for the SOS-polling nowPlaying logic (no display, no network: pygame is stubbed,
SOS is a local fake server, the title fetch is injected).
Run: python3 test_nowplaying_sync.py
"""
import importlib.util
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock

sys.modules.setdefault('pygame', MagicMock())

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)

spec = importlib.util.spec_from_file_location('nowPlaying', os.path.join(SCRIPTS, 'nowPlaying.py'))
np = importlib.util.module_from_spec(spec)
spec.loader.exec_module(np)

CSV_UTF8 = ("Dataset Name (Auto),Spanish Title,English Title\n"
            "Bee_Movie,Película de abejas ¿Sí?,Bee Movie\n"
            "Sun,Sol,Sun\n").encode('utf-8')


class ParserTests(unittest.TestCase):
    def test_pairs_braced_and_plain(self):
        pairs = np.parse_pairs("name {Bee Movie} duration 95 movie-title {The Bee} caption {}")
        self.assertEqual(pairs['name'], 'Bee Movie')
        self.assertEqual(pairs['duration'], '95')
        self.assertEqual(pairs['movie-title'], 'The Bee')
        self.assertEqual(pairs['caption'], '')
        self.assertNotIn('title', pairs)  # not split out of 'movie-title'

    def test_pairs_ignores_ack_prefix_and_unicode(self):
        pairs = np.parse_pairs("R\nname {Sun} spanish-translation {Pingüino ñandú}")
        self.assertEqual(pairs['name'], 'Sun')
        self.assertEqual(pairs['spanish-translation'], 'Pingüino ñandú')

    def test_ints_and_names(self):
        self.assertEqual(np.parse_int("R\n7\n"), 7)
        self.assertEqual(np.parse_int("12"), 12)
        self.assertIsNone(np.parse_int("R"))
        self.assertEqual(np.parse_playlist_name("R\n/home/sos/sosrc/Batch1.sos\n"), "/home/sos/sosrc/Batch1.sos")

    def test_seconds(self):
        self.assertEqual(np.parse_seconds("65"), 65.0)
        self.assertEqual(np.parse_seconds("2:30"), 150.0)
        self.assertEqual(np.parse_seconds("2m 30s"), 150.0)
        for bad in (None, "", "0", "N/A", "0m 0s"):
            self.assertIsNone(np.parse_seconds(bad))


class CsvTests(unittest.TestCase):
    def test_utf8_accents_survive(self):
        titles = np.parse_titles_csv(np.decode_csv_bytes(CSV_UTF8))
        self.assertEqual(titles['Bee_Movie'], ('Bee Movie', 'Película de abejas ¿Sí?'))

    def test_utf8_bom(self):
        titles = np.parse_titles_csv(np.decode_csv_bytes(b'\xef\xbb\xbf' + CSV_UTF8))
        self.assertIn('Bee_Movie', titles)  # BOM must not corrupt the first column name

    def test_cp1252_fallback(self):
        data = "Dataset Name (Auto),Spanish Title,English Title\nX,Año,Year\n".encode('cp1252')
        self.assertEqual(np.parse_titles_csv(np.decode_csv_bytes(data))['X'][1], 'Año')

    def test_never_latin1_mojibake(self):
        self.assertNotIn('Ã', np.decode_csv_bytes(CSV_UTF8))


class TitleSourceTests(unittest.TestCase):
    def setUp(self):
        self.cache = os.path.join(tempfile.mkdtemp(), 'titles.csv')

    def test_fetch_caches_and_falls_back_to_cache(self):
        good = np.TitleSource(fetch=lambda: CSV_UTF8, cache_path=self.cache)
        self.assertTrue(good.refresh(0.0))
        self.assertEqual(good.source, 'ssh')
        self.assertEqual(good.lookup('bee_movie')[0], 'Bee Movie')  # case-insensitive fallback

        def boom():
            raise np.SosError("down")
        offline = np.TitleSource(fetch=boom, cache_path=self.cache)
        self.assertTrue(offline.load_cache())
        self.assertFalse(offline.refresh(1.0))
        self.assertEqual(offline.source, 'cache')
        self.assertEqual(offline.lookup('Bee_Movie')[1], 'Película de abejas ¿Sí?')

    def test_bad_fetch_keeps_old_titles(self):
        source = np.TitleSource(fetch=lambda: CSV_UTF8, cache_path=self.cache)
        source.refresh(0.0)
        source.fetch = lambda: b"<html>nope</html>"
        self.assertFalse(source.refresh(1.0))
        self.assertEqual(len(source.titles), 2)

    def test_build_entries_fallback_order(self):
        source = np.TitleSource(fetch=lambda: CSV_UTF8, cache_path=self.cache)
        source.refresh(0.0)
        clips = [
            np.Clip(1, 'Bee_Movie', '95', None, None),
            np.Clip(2, 'Other', None, 'Other Movie', 'Otra película'),
            np.Clip(3, 'Bare', '0', None, None),
        ]
        en, es, du = np.build_entries(clips, source)
        self.assertEqual((en[1], es[1], du[1]), ('Bee Movie', 'Película de abejas ¿Sí?', '1m 35s'))
        self.assertEqual((en[2], es[2]), ('Other Movie', 'Otra película'))
        self.assertEqual((en[3], es[3], du[3]), ('Bare', '', np.DEFAULT_DURATION_DISPLAY))


class SchedulerTests(unittest.TestCase):
    def simulate(self, sched, clip_count, clip_len, horizon):
        """Clip advances every clip_len seconds; poll whenever the scheduler says."""
        now, seen = 0.0, []
        while now <= horizon:
            clip = int(now // clip_len) % clip_count + 1
            sched.observe(clip, now)
            seen.append((now, clip))
            now += sched.next_delay(now)[0]
        return seen

    def test_starts_at_base_interval(self):
        s = np.PollScheduler()
        s.count = 5
        s.observe(1, 0.0)
        self.assertEqual(s.next_delay(0.0), (np.BASE_POLL_INTERVAL, 'base'))

    def test_learns_duration(self):
        s = np.PollScheduler()
        s.count = 5
        s.observe(1, 0.0)
        s.observe(2, 20.0)  # clip 2 starts at ~10
        for t in (40.0, 60.0, 80.0, 100.0):
            s.observe(2, t)
        s.observe(3, 120.0)  # clip 3 starts at ~110
        seconds, err, source = s.estimate(2)
        self.assertEqual(source, 'learned')
        self.assertAlmostEqual(seconds, 100.0)
        self.assertAlmostEqual(err, 20.0)

    def test_converges_to_tight_detection(self):
        s = np.PollScheduler()
        s.count = 4
        seen = self.simulate(s, 4, 100.0, 4000)
        late = [(t, c) for t, c in seen if t > 2000]
        detected = 0
        for (t0, c0), (t1, c1) in zip(late, late[1:]):
            if c1 != c0:
                detected += 1
                self.assertLessEqual(t1 - (t1 // 100) * 100, 3.5, f"late detection at {t1}")
        self.assertGreater(detected, 5)

    def test_converges_to_fewer_polls_for_long_clips(self):
        s = np.PollScheduler()
        s.count = 4
        seen = self.simulate(s, 4, 300.0, 8000)
        late = [t for t, _ in seen if t > 4000]
        self.assertLess(len(late), 0.7 * 4000 / np.BASE_POLL_INTERVAL)

    def test_safety_poll_cap(self):
        s = np.PollScheduler()
        s.count = 3
        s.learned[2] = (600.0, 1.0)
        s.observe(1, 0.0)
        s.observe(2, 10.0)
        delay, mode = s.next_delay(10.0)
        self.assertEqual(mode, 'predict')
        self.assertEqual(delay, np.SAFETY_POLL_INTERVAL)

    def test_miss_falls_back_to_base(self):
        s = np.PollScheduler()
        s.count = 3
        s.observe(1, 0.0)
        s.observe(2, 2.0)  # clip 2 starts at 1
        s.learned[2] = (30.0, 1.0)
        self.assertEqual(s.next_delay(20.0)[1], 'predict')
        self.assertEqual(s.next_delay(30.5)[1], 'catch')
        self.assertEqual(s.next_delay(60.0)[1], 'lost')
        s.observe(2, 60.0)
        self.assertEqual(s.misses, 1)

    def test_manual_skip_does_not_poison_duration(self):
        s = np.PollScheduler()
        s.count = 5
        s.learned[2] = (100.0, 1.0)
        s.observe(1, 0.0)
        s.observe(2, 2.0)
        s.observe(3, 22.0)  # left clip 2 after ~20s: shorter sample is held back
        self.assertEqual(s.learned[2][0], 100.0)
        self.assertIn(2, s.pending_short)

    def test_non_sequential_change_not_learned(self):
        s = np.PollScheduler()
        s.count = 5
        s.observe(1, 0.0)
        s.observe(2, 2.0)
        s.observe(5, 50.0)
        self.assertNotIn(2, s.learned)

    def test_hint_used_then_dropped_on_miss(self):
        s = np.PollScheduler()
        s.count = 3
        s.set_hints({2: 10.0})
        s.observe(1, 0.0)
        s.observe(2, 2.0)
        self.assertEqual(s.estimate(2)[2], 'hint')
        s.observe(2, 100.0)
        self.assertNotIn(2, s.hints)

    def test_wraparound_is_sequential(self):
        s = np.PollScheduler()
        s.count = 3
        s.observe(2, 0.0)
        s.observe(3, 2.0)
        s.observe(1, 102.0)
        self.assertIn(3, s.learned)


class FakeSos:
    """Minimal SOS: handshake 'R', canned replies, records every command received."""

    def __init__(self):
        self.playlist_name = "/home/sos/sosrc/Test.sos"
        self.clips = [
            "name {Bee_Movie} duration 95 spanish-translation {Pingüino}",
            "name {Sun} duration 60",
            "name {Credits: Everyone}",
        ]
        self.current = 1
        self.commands = []
        self.server = socket.socket()
        self.server.bind(('127.0.0.1', 0))
        self.server.listen(5)
        self.port = self.server.getsockname()[1]
        self.running = True
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        self.server.settimeout(0.2)
        while self.running:
            try:
                conn, _ = self.server.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _serve(self, conn):
        buf = b""
        while self.running:
            try:
                chunk = conn.recv(1024)
            except OSError:
                return
            if not chunk:
                return
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                cmd = line.decode().strip()
                self.commands.append(cmd)
                conn.sendall(self._reply(cmd).encode('utf-8'))

    def _reply(self, cmd):
        if cmd == 'enable':
            return "R"
        if cmd == 'get_playlist_name':
            return self.playlist_name + "\n"
        if cmd == 'get_clip_count':
            return f"{len(self.clips)}\n"
        if cmd == 'get_clip_number':
            return f"{self.current}\n"
        if cmd.startswith('get_all_name_value_pairs'):
            return self.clips[int(cmd.split()[1]) - 1] + "\n"
        return ""

    def stop(self):
        self.running = False
        self.server.close()


class SyncIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.sos = FakeSos()
        np.SOS_IDLE_TIMEOUT = 0.05
        np.SOS_FIRST_REPLY_TIMEOUT = 1.0
        self.clock_value = 0.0
        self.state = np.SyncState()
        self.titles = np.TitleSource(fetch=lambda: CSV_UTF8,
                                     cache_path=os.path.join(tempfile.mkdtemp(), 't.csv'))
        self.sync = np.SosSync(self.state, np.SosClient('127.0.0.1', self.sos.port), self.titles,
                               np.PollScheduler(), clock=lambda: self.clock_value)

    def tearDown(self):
        self.sos.stop()

    def test_first_step_loads_playlist_with_correct_accents(self):
        delay = self.sync.step()
        snap = self.state.snapshot()
        self.assertEqual(delay, np.BASE_POLL_INTERVAL)
        self.assertEqual(snap.english[1], 'Bee Movie')
        self.assertEqual(snap.spanish[1], 'Película de abejas ¿Sí?')
        self.assertEqual(snap.spanish[2], 'Sol')
        self.assertEqual(snap.english[3], 'Credits: Everyone')
        self.assertEqual(snap.clip, 1)
        self.assertEqual(self.state.status()['titles']['source'], 'ssh')

    def test_polling_follows_sos_clip(self):
        self.sync.step()
        self.sos.current = 2
        self.clock_value = 20.0
        self.sync.step()
        self.assertEqual(self.state.snapshot().clip, 2)

    def test_only_read_only_commands_are_sent(self):
        self.sync.step()
        self.clock_value = 20.0
        self.sync.step()
        allowed = {'enable', 'get_playlist_name', 'get_clip_count', 'get_clip_number'}
        for cmd in self.sos.commands:
            self.assertTrue(cmd in allowed or cmd.startswith('get_all_name_value_pairs'), cmd)

    def test_identity_change_triggers_full_refresh(self):
        self.sync.step()
        self.sos.playlist_name = "/home/sos/sosrc/Other.sos"
        self.sos.clips = ["name {Moon} duration 30"]
        self.clock_value = np.IDENTITY_CHECK_INTERVAL + 1
        self.assertEqual(self.sync.step(), 0.0)
        self.sync.step()
        self.assertEqual(self.state.status()['items'], 1)
        self.assertEqual(self.state.snapshot().english[1], 'Moon')
        self.assertEqual(self.state.stats['playlist_changes'], 1)

    def test_sos_down(self):
        self.sos.stop()
        self.assertEqual(self.sync.step(), np.FAILURE_RETRY_DELAY)
        self.assertFalse(self.state.loaded())
        self.assertIsNotNone(self.state.status()['last_error'])

    def test_titles_arriving_late_update_menu(self):
        calls = {'n': 0}

        def flaky():
            calls['n'] += 1
            if calls['n'] == 1:
                raise np.SosError("ssh down")
            return CSV_UTF8
        self.titles.fetch = flaky
        self.sync.step()
        self.assertEqual(self.state.snapshot().spanish[2], '')  # no titles yet: SOS metadata fallback
        self.clock_value = np.TITLES_RETRY_INTERVAL + 1
        self.sync.step()
        self.assertEqual(self.state.snapshot().spanish[2], 'Sol')


class StatusServerTests(unittest.TestCase):
    def test_status_json_and_legacy_ignored(self):
        status = json.loads(np.process_message('STATUS').decode())
        for key in ('in_sync', 'items', 'clip', 'polling', 'titles', 'stats'):
            self.assertIn(key, status)
        self.assertEqual(np.process_message('CLIP:3'), b"ACK IGNORED\n")

    def test_socket_round_trip(self):
        server = socket.socket()
        server.bind(('127.0.0.1', 0))
        server.listen(1)
        np.running = True
        threading.Thread(target=np.socket_server_loop, args=(server,), daemon=True).start()
        try:
            c = socket.create_connection(server.getsockname(), timeout=3)
            c.sendall(b'STATUS')
            c.shutdown(socket.SHUT_WR)
            self.assertIn('in_sync', json.loads(c.recv(65536).decode()))
            c.close()
        finally:
            np.running = False
            time.sleep(0.6)
            server.close()


class FormatTests(unittest.TestCase):
    def test_format_duration(self):
        self.assertEqual(np.format_duration("65"), "1m 5s")
        self.assertEqual(np.format_duration(None), np.DEFAULT_DURATION_DISPLAY)


if __name__ == '__main__':
    unittest.main(verbosity=2)
