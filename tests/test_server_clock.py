from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from thlib.ui.activity import activity_record
from thlib.ui.server_clock import ServerClock
from thlib.ui.communication_permissions import can_change_published_text
from thlib.ui.sobject_delete import can_delete_recent_sobject


class ServerClockTests(unittest.TestCase):
    def setUp(self):
        timer = patch("thlib.ui.server_clock.time.monotonic", return_value=100.2)
        self.monotonic = timer.start()
        self.addCleanup(timer.stop)
        self.clock = ServerClock()
        self.sample = {
            "utcStarted": "2026-10-28T00:30:00.050000Z",
            "utcEnded": "2026-10-28T00:30:00.150000Z",
        }

    def sync(self):
        return self.clock.observe(self.sample, 100, 100.2, session="server")

    def test_actual_utc_instant_does_not_move_when_clock_synchronizes(self):
        before = self.clock.presentation_datetime("2026-10-28 00:30:00")
        self.assertTrue(self.sync())
        for text in ("2026-10-28 00:30:00", "2026-10-28T00:30:00Z",
                     "2026-10-28T03:30:00+03:00"):
            self.assertEqual(self.clock.presentation_datetime(text), before)
        self.assertEqual(before.astimezone(timezone.utc),
                         datetime(2026, 10, 28, 0, 30, tzinfo=timezone.utc))

    def test_now_excludes_server_processing_and_ignores_workstation_clock(self):
        self.sync()
        self.assertAlmostEqual(self.clock.now().timestamp(),
                               datetime(2026, 10, 28, 0, 30, 0, 200000,
                                        tzinfo=timezone.utc).timestamp(), places=5)
        self.monotonic.return_value += 90
        self.assertEqual(activity_record({"timestamp": "2026-10-28 00:30:00"},
                                         clock=self.clock)["timestampPretty"], "1 min ago")

    def test_transport_cursor_is_raw_and_full_label_is_local(self):
        self.sync()
        record = activity_record({"timestamp": "2026-10-28 00:30:00"}, clock=self.clock)
        self.assertEqual(record["timestamp"], "2026-10-28 00:30:00")
        self.assertEqual(record["timestampPretty"], "Just now")
        self.assertIn(self.clock.presentation_datetime(record["timestamp"]).strftime("%H:%M:%S"),
                      record["timestampFull"])

    def test_invalid_out_of_order_and_slow_samples_do_not_replace_good_clock(self):
        self.assertFalse(self.clock.observe({}, None, None, session="server"))
        self.sync()
        before = self.clock.now()
        for started, received in ((float("nan"), 101), (100, 99), (100, 100.1), (100, 102)):
            self.assertFalse(self.clock.observe(self.sample, started, received, session="server"))
            self.assertEqual(self.clock.now(), before)
        self.assertFalse(self.clock.observe({"utcStarted": "bad", "utcEnded": "bad"},
                                           100, 101, session="server"))

    def test_long_server_work_is_not_network_uncertainty(self):
        self.sample["utcEnded"] = "2026-10-28T00:30:20.150000Z"
        self.monotonic.return_value = 120.2
        self.assertTrue(self.clock.observe(self.sample, 100, 120.2, session="server"))
        self.assertAlmostEqual(self.clock.now().second + self.clock.now().microsecond / 1e6,
                               20.2, places=5)

    def test_first_hour_permissions_use_server_now(self):
        self.sync()
        source = {"login": "artist", "timestamp": "2026-10-28 00:00:00"}
        self.assertTrue(can_delete_recent_sobject(source, "artist", self.clock))
        self.assertTrue(can_change_published_text("artist", source["timestamp"], "artist", False, self.clock))
        self.monotonic.return_value += 3600
        self.assertFalse(can_delete_recent_sobject(source, "artist", self.clock))
        self.assertFalse(can_change_published_text("artist", source["timestamp"], "artist", False, self.clock))
        self.clock.reset("other-server")
        self.assertEqual(self.clock.presentation_datetime(source["timestamp"]).astimezone(timezone.utc),
                         datetime(2026, 10, 28, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
