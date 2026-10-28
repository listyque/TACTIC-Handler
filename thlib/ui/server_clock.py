from __future__ import annotations

from datetime import datetime, timezone
import math
import time

from PySide6.QtCore import QObject, Signal

from thlib.global_functions import parce_timestamp


class ServerClock(QObject):
    """Extrapolate server UTC with a monotonic clock; preserve event instants."""

    changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._session = None
        self._synchronized = False
        self._utc_at_receive = 0.0
        self._best_round_trip_seconds = float("inf")
        self._observed_at = 0.0

    @staticmethod
    def _aware_utc(value) -> datetime:
        text = str(value or "").strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            raise ValueError("Clock observations require an explicit UTC offset")
        return parsed.astimezone(timezone.utc)

    def reset(self, session=None) -> None:
        was_synchronized = self._synchronized
        self._session = session
        self._synchronized = False
        self._utc_at_receive = 0.0
        self._best_round_trip_seconds = float("inf")
        self._observed_at = 0.0
        if was_synchronized:
            self.changed.emit()

    def observe(
            self, sample, client_started_monotonic, client_received_monotonic,
            *, session=None) -> bool:
        """Accept one four-timestamp sample without risking the update poll."""
        if session != self._session:
            self.reset(session)
        try:
            sample = dict(sample or {})
            client_started = float(client_started_monotonic)
            client_received = float(client_received_monotonic)
            server_started = self._aware_utc(
                sample.get("utcStarted")
            ).timestamp()
            server_ended_utc = self._aware_utc(
                sample.get("utcEnded")
            )
            server_ended = server_ended_utc.timestamp()
        except (TypeError, ValueError, OverflowError):
            return False
        if not all(math.isfinite(value) for value in (
                client_started, client_received, server_started, server_ended)):
            return False
        server_processing = server_ended - server_started
        round_trip = client_received - client_started - server_processing
        if (client_received < client_started or server_processing < 0
                or round_trip < -0.002
                or (self._synchronized and client_received < self._observed_at)):
            return False
        round_trip = max(0.0, round_trip)
        observed_at = client_received
        should_accept = (
            not self._synchronized
            or round_trip <= self._best_round_trip_seconds * 1.5 + 0.020
            or observed_at - self._observed_at >= 300.0
        )
        if not should_accept:
            return False

        utc_at_receive = server_ended + round_trip / 2.0
        changed = (
            not self._synchronized
            or abs(utc_at_receive - self._utc_at_receive
                   - (observed_at - self._observed_at)) >= 0.5
        )
        self._synchronized = True
        self._utc_at_receive = utc_at_receive
        self._best_round_trip_seconds = min(
            self._best_round_trip_seconds, round_trip
        )
        self._observed_at = observed_at
        if changed:
            self.changed.emit()
        return changed

    def presentation_datetime(self, value) -> datetime:
        """Return an event instant in the workstation's local timezone."""
        parsed = parce_timestamp(value)
        if parsed is None:
            raise ValueError("Timestamp is empty")
        return parsed

    def now(self) -> datetime:
        """Return server UTC, independent of workstation wall-clock changes."""
        if not self._synchronized:
            return datetime.now(timezone.utc)
        return datetime.fromtimestamp(
            self._utc_at_receive + time.monotonic() - self._observed_at,
            tz=timezone.utc,
        )
