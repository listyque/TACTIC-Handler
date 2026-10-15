from __future__ import annotations

from datetime import datetime, timezone
import time

from PySide6.QtCore import QObject, Signal

from thlib.global_functions import parce_timestamp


class ServerClock(QObject):
    """Present TACTIC's UTC timestamps with optional server-clock correction."""

    changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._session = None
        self._synchronized = False
        self._client_minus_server_seconds = 0.0
        self._best_round_trip_seconds = float("inf")
        self._observed_at = 0.0

    @staticmethod
    def _aware_utc(value) -> datetime:
        text = str(value or "").strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def reset(self, session=None) -> None:
        was_synchronized = self._synchronized
        self._session = session
        self._synchronized = False
        self._client_minus_server_seconds = 0.0
        self._best_round_trip_seconds = float("inf")
        self._observed_at = 0.0
        if was_synchronized:
            self.changed.emit()

    def observe(
            self, sample, client_started_epoch, client_received_epoch,
            *, session=None) -> bool:
        """Accept one four-timestamp sample without risking the update poll."""
        if session != self._session:
            self.reset(session)
        sample = dict(sample or {})
        try:
            client_started = float(client_started_epoch)
            client_received = float(client_received_epoch)
            server_started = self._aware_utc(
                sample.get("utcStarted")
            ).timestamp()
            server_ended_utc = self._aware_utc(
                sample.get("utcEnded")
            )
            server_ended = server_ended_utc.timestamp()
        except (TypeError, ValueError, OverflowError):
            return False
        if client_received < client_started or server_ended < server_started:
            return False

        server_processing = server_ended - server_started
        round_trip = max(
            0.0,
            (client_received - client_started) - server_processing,
        )
        observed_at = time.monotonic()
        should_accept = (
            not self._synchronized
            or round_trip <= self._best_round_trip_seconds * 1.5 + 0.020
            or observed_at - self._observed_at >= 300.0
        )
        if not should_accept:
            return False

        client_minus_server = (
            (client_started - server_started)
            + (client_received - server_ended)
        ) / 2.0
        changed = (
            not self._synchronized
            or abs(
                client_minus_server - self._client_minus_server_seconds
            ) >= 0.5
        )
        self._synchronized = True
        self._client_minus_server_seconds = client_minus_server
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
        if self._synchronized:
            return datetime.fromtimestamp(
                parsed.timestamp() + self._client_minus_server_seconds,
                tz=timezone.utc,
            ).astimezone()
        return parsed
