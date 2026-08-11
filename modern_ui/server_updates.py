from __future__ import annotations

import time
import traceback
from urllib.error import HTTPError, URLError

from PySide6.QtCore import (
    QObject, Property, QSettings, QTimer, Qt, Signal, Slot,
)

from .request_metrics import request_metrics


class ServerUpdateService(QObject):
    batchReady = Signal(object)
    stateChanged = Signal()
    errorRaised = Signal(str, str)
    warningRaised = Signal(str, str)

    _transient_http_codes = {408, 429, 500, 502, 503, 504}
    _silent_retry_limit = 5
    _allowed_poll_intervals = {5, 10, 30, 60}

    def __init__(self, application, parent=None) -> None:
        super().__init__(parent or application)
        self._application = application
        self._settings = QSettings("TACTIC-Handler", "modern-qml")
        self._poll_interval = self._settings.value(
            "network/serverUpdateInterval", 30, type=int
        )
        if self._poll_interval not in self._allowed_poll_intervals:
            self._poll_interval = 30
        self._presence_interval = self._settings.value(
            "network/presenceHeartbeatInterval", 120, type=int
        )
        if self._presence_interval not in {30, 60, 120, 300}:
            self._presence_interval = 120
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(self._poll_interval * 1000)
        self._timer.timeout.connect(self.poll)
        self._worker = None
        self._running = False
        self._busy = False
        self._initial_messages = True
        self._initial_activity = True
        self._message_cursor = ""
        self._activity_cursor = ""
        self._reaction_cursor = ""
        self._failure_count = 0
        self._failure_reported = False
        self._session = None
        self._activity_enabled = False
        self._messages_visible = False
        self._tasks_visible = False
        self._request_included_activity = False
        self._request_included_presence = False
        self._last_presence_at = 0.0
        self._request_generation = 0
        application.project_changed.connect(self._project_changed)

    @Property(bool, notify=stateChanged)
    def running(self) -> bool:
        return self._running

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(int, notify=stateChanged)
    def poll_interval(self) -> int:
        return self._poll_interval

    @Slot(int)
    def set_poll_interval(self, seconds: int) -> None:
        seconds = int(seconds)
        if seconds not in self._allowed_poll_intervals:
            return
        if self._poll_interval == seconds:
            return
        self._poll_interval = seconds
        self._settings.setValue("network/serverUpdateInterval", seconds)
        if self._running and not self._busy:
            self._schedule(self._poll_delay())
        self.stateChanged.emit()

    @Property(int, notify=stateChanged)
    def presence_interval(self) -> int:
        return self._presence_interval

    @Slot(int)
    def set_presence_interval(self, seconds: int) -> None:
        seconds = int(seconds)
        if seconds not in {30, 60, 120, 300}:
            return
        if self._presence_interval == seconds:
            return
        self._presence_interval = seconds
        self._settings.setValue(
            "network/presenceHeartbeatInterval", seconds
        )
        self._last_presence_at = 0.0
        if self._running and not self._busy:
            self._schedule(0)
        self.stateChanged.emit()

    def _poll_delay(self) -> int:
        return self._poll_interval * 1000

    @Slot()
    def start(self) -> None:
        if self._running:
            return
        self._failure_count = 0
        self._failure_reported = False
        self._running = True
        self.stateChanged.emit()
        self._schedule(0)

    @Slot()
    def stop(self) -> None:
        self._request_generation += 1
        self._running = False
        self._timer.stop()
        cancel = getattr(self._worker, "cancel", None)
        if callable(cancel):
            cancel()
        self._worker = None
        self._busy = False
        self.stateChanged.emit()

    def _project_changed(self, *_args) -> None:
        self._request_generation += 1
        cancel = getattr(self._worker, "cancel", None)
        if callable(cancel):
            cancel()
        self._worker = None
        self._busy = False
        self._activity_cursor = ""
        self._initial_activity = True
        self._failure_count = 0
        self._failure_reported = False
        if self._running:
            self._schedule(0)

    def _schedule(self, delay: int | None = None) -> None:
        if not self._running:
            return
        if delay is None:
            delay = self._poll_delay()
        self._timer.start(max(0, int(delay)))

    @Slot(bool)
    def set_activity_enabled(self, value: bool) -> None:
        self._activity_enabled = bool(value)

    @Slot(bool)
    def set_messages_visible(self, value: bool) -> None:
        self._messages_visible = bool(value)

    @Slot(bool)
    def set_tasks_visible(self, value: bool) -> None:
        self._tasks_visible = bool(value)

    @Slot()
    def poll(self) -> None:
        if not self._running or self._busy:
            return
        from thlib.environment import env_inst, env_server

        if not env_server.get_ticket() or not env_inst.logins:
            self._schedule()
            return
        session = (
            str(env_server.get_server() or ""),
            str(env_server.get_user() or ""),
            str(env_server.get_ticket() or ""),
        )
        if session != self._session:
            self._session = session
            self._message_cursor = ""
            self._activity_cursor = ""
            self._reaction_cursor = ""
            self._initial_messages = True
            self._initial_activity = True
            self._failure_count = 0
            self._failure_reported = False
            self._last_presence_at = 0.0
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        project_code = str(self._application.current_project_code or "")
        message_cursor = self._message_cursor
        activity_cursor = self._activity_cursor
        reaction_cursor = self._reaction_cursor
        # Messages and project activity share the same 30-second batch.  Do
        # not silently slow activity to a multi-minute cadence when its dock
        # is closed: badges and task state depend on the same cursor.
        include_activity = bool(project_code)
        include_reactions = self._messages_visible
        include_presence = (
            not self._last_presence_at
            or time.monotonic() - self._last_presence_at
            >= self._presence_interval
        )
        self._request_included_activity = include_activity
        self._request_included_presence = include_presence

        def operation():
            import thlib.tactic_classes as tc

            try:
                with request_metrics.measure("server.poll") as metric:
                    result = tc.get_server_updates(
                        message_after=message_cursor,
                        activity_after=activity_cursor,
                        reaction_after=reaction_cursor,
                        project_code=project_code,
                        limit=101,
                        include_activity=include_activity,
                        include_reactions=include_reactions,
                        include_presence=include_presence,
                        presence_ttl=max(360, self._presence_interval * 3),
                    )
                    metric["response_bytes"] = len(
                        repr(result).encode("utf-8", errors="replace")
                    )
                    return result
            except Exception as error:
                if not self._is_transient_error(error):
                    raise
                return {
                    "__transient_error__": True,
                    "message": str(error or "Temporary server error"),
                    "stacktrace": traceback.format_exc(),
                }

        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._schedule(10000)
            return
        self._worker = worker
        self._request_generation += 1
        request_generation = self._request_generation
        self._busy = True
        self.stateChanged.emit()
        worker.result.connect(
            lambda result, generation=request_generation:
                self._ready_for(generation, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error, generation=request_generation:
                self._failed_for(generation, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _ready_for(self, generation: int, result) -> None:
        if generation != self._request_generation or not self._running:
            return
        self._ready(result)

    def _failed_for(self, generation: int, error) -> None:
        if generation != self._request_generation or not self._running:
            return
        self._failed(error)

    @staticmethod
    def _value(result):
        return result[0] if isinstance(result, tuple) and len(result) == 1 else result

    @classmethod
    def _is_transient_error(cls, error) -> bool:
        if isinstance(error, HTTPError):
            return int(error.code or 0) in cls._transient_http_codes
        if isinstance(error, (URLError, TimeoutError, ConnectionError)):
            return True
        if isinstance(error, OSError):
            return getattr(error, "winerror", None) in {
                10051, 10053, 10054, 10060, 10061,
            }
        return False

    def _retry_delay(self) -> int:
        if self._failure_count >= self._silent_retry_limit:
            return 30000
        return min(30000, 2000 * (2 ** max(0, self._failure_count - 1)))

    def _transient_failed(self, value: dict) -> None:
        self._worker = None
        self._busy = False
        self._failure_count += 1
        self.stateChanged.emit()
        if (
            self._failure_count >= self._silent_retry_limit
            and not self._failure_reported
        ):
            self._failure_reported = True
            self.warningRaised.emit(
                "Server updates remain unavailable after "
                f"{self._failure_count} attempts: "
                f"{value.get('message') or 'temporary server error'}",
                str(value.get("stacktrace") or ""),
            )
        self._schedule(self._retry_delay())

    @Slot(object)
    def _ready(self, result) -> None:
        value = self._value(result) or {}
        if value.get("__transient_error__"):
            self._transient_failed(value)
            return
        messages = list(value.get("messages") or [])
        reactions = list(value.get("reactions") or [])
        activity = list(value.get("activity") or [])
        presence = list(value.get("presence") or [])
        if messages:
            self._message_cursor = max(
                str(
                    record.get("__event_timestamp__")
                    or record.get("timestamp") or ""
                )
                for record in messages
            )
        if activity:
            activity_timestamps = [
                str(record.get("__event_timestamp__") or "")
                for record in activity
                if record.get("__event_timestamp__")
            ]
            if activity_timestamps:
                self._activity_cursor = max(activity_timestamps)
        reaction_cursor = str(value.get("reactionCursor") or "")
        if reaction_cursor:
            self._reaction_cursor = reaction_cursor
        batch = {
            "messages": messages,
            "reactions": reactions,
            "activity": activity,
            "initialMessages": self._initial_messages,
            "initialActivity": self._initial_activity,
            "presence": presence,
        }
        self._initial_messages = False
        if self._request_included_activity:
            self._initial_activity = False
        if self._request_included_presence:
            self._last_presence_at = time.monotonic()
        self._worker = None
        self._busy = False
        self._failure_count = 0
        self._failure_reported = False
        self.stateChanged.emit()
        if messages or reactions or activity or presence:
            self.batchReady.emit(batch)
        self._schedule()

    @Slot(object)
    def _failed(self, error) -> None:
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        self._worker = None
        self._busy = False
        self._failure_count += 1
        self.stateChanged.emit()
        if not self._failure_reported:
            self._failure_reported = True
            self.errorRaised.emit(
                str(payload or "Server update failed"), stacktrace
            )
        self._schedule(30000)

    @Slot()
    def shutdown(self) -> None:
        self.stop()
