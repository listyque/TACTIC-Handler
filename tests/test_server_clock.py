from datetime import datetime, timezone
import unittest

from PySide6.QtCore import QLocale

from thlib.ui.activity import activity_record
from thlib.ui.server_clock import ServerClock


class ServerClockTests(unittest.TestCase):
    @staticmethod
    def _epoch(value: str) -> float:
        return datetime.fromisoformat(value).replace(
            tzinfo=timezone.utc
        ).timestamp()

    def test_server_timezone_and_clock_drift_are_both_corrected(self):
        clock = ServerClock()
        client_started = self._epoch("2026-08-30 10:00:00")
        changed = clock.observe(
            {
                # The server UTC clock is two hours fast and its local
                # timezone is UTC+3.
                "utcStarted": "2026-08-30T12:00:00.050000Z",
                "utcEnded": "2026-08-30T12:00:00.150000Z",
                "localEnded": "2026-08-30T15:00:00.150000",
            },
            client_started,
            client_started + 0.2,
            session=("server", "artist"),
        )

        self.assertTrue(changed)
        naive_event = clock.presentation_datetime(
            "2026-08-30 15:10:00"
        )
        aware_event = clock.presentation_datetime(
            "2026-08-30T12:10:00Z"
        )
        self.assertEqual(
            naive_event.astimezone(timezone.utc),
            datetime(2026, 8, 30, 10, 10, tzinfo=timezone.utc),
        )
        self.assertEqual(
            aware_event.astimezone(timezone.utc),
            datetime(2026, 8, 30, 10, 10, tzinfo=timezone.utc),
        )

    def test_activity_keeps_raw_cursor_time_and_uses_local_presentation_time(self):
        clock = ServerClock()
        client_started = self._epoch("2026-08-30 10:00:00")
        clock.observe(
            {
                "utcStarted": "2026-08-30T12:00:00.050000Z",
                "utcEnded": "2026-08-30T12:00:00.150000Z",
                "localEnded": "2026-08-30T15:00:00.150000",
            },
            client_started,
            client_started + 0.2,
            session=("server", "artist"),
        )

        previous_locale = QLocale()
        try:
            QLocale.setDefault(QLocale("en_US"))
            record = activity_record({
                "eventId": "snapshot:SNAPSHOT00001",
                "timestamp": "2026-08-30 15:10:00",
            }, clock=clock)
        finally:
            QLocale.setDefault(previous_locale)

        self.assertEqual(record["timestamp"], "2026-08-30 15:10:00")
        self.assertTrue(record["timestampPretty"])
        local_time = clock.presentation_datetime(
            "2026-08-30 15:10:00"
        ).strftime("%H:%M:%S")
        self.assertIn(local_time, record["timestampFull"])

    def test_database_timezone_wins_over_python_process_timezone(self):
        clock = ServerClock()
        client_started = self._epoch("2026-08-30 12:00:00")
        clock.observe(
            {
                "utcStarted": "2026-08-30T12:00:00.050000Z",
                "utcEnded": "2026-08-30T12:00:00.150000Z",
                # The Python process runs in UTC while its database session,
                # which owns TACTIC object timestamps, runs in UTC+3.
                "localEnded": "2026-08-30T12:00:00.150000",
                "databaseEnded": "2026-08-30T15:00:00.150000",
            },
            client_started,
            client_started + 0.2,
            session=("server", "artist"),
        )

        event = clock.presentation_datetime("2026-08-30 15:10:00")

        self.assertEqual(
            event.astimezone(timezone.utc),
            datetime(2026, 8, 30, 12, 10, tzinfo=timezone.utc),
        )

    def test_invalid_clock_sample_keeps_naive_timestamp_unchanged(self):
        clock = ServerClock()

        self.assertFalse(clock.observe({}, None, None, session="server"))
        self.assertEqual(
            clock.presentation_datetime("2026-08-30 15:10:00"),
            datetime(2026, 8, 30, 15, 10),
        )


if __name__ == "__main__":
    unittest.main()
