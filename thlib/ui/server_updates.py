from __future__ import annotations

import time
import json
import random
import traceback
from urllib.error import HTTPError, URLError

from PySide6.QtCore import (
    QObject, Property, QTimer, Qt, Signal, Slot,
)

from thlib.request_retry import (
    defer_transient_error_reporting,
    is_transient_read_error,
)

from .request_metrics import request_metrics
from .server_clock import ServerClock


class ServerUpdateService(QObject):
    batchReady = Signal(object)
    stateChanged = Signal()
    errorRaised = Signal(str, str)
    warningRaised = Signal(str, str)
    connectionChecked = Signal(bool)

    _transient_http_codes = {408, 429, 500, 502, 503, 504}
    _silent_retry_limit = 5
    _allowed_poll_intervals = {5, 10, 30, 60}

    def __init__(self, application, parent=None, clock=None) -> None:
        super().__init__(parent or application)
        self._application = application
        self.clock = clock or ServerClock(self)
        self._settings = application._settings
        self._poll_interval = int(
            self._settings.get("network/serverUpdateInterval", 30) or 30
        )
        if self._poll_interval not in self._allowed_poll_intervals:
            self._poll_interval = 30
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(self._poll_interval * 1000)
        self._timer.timeout.connect(self.poll)
        self._worker = None
        self._stream = None
        self._update_mode = "sse" if self._settings.get("network/serverUpdateMode") == "sse" else "poll"
        self._batch_delay = self._settings.get("network/serverUpdateBatchDelay", 200)
        if type(self._batch_delay) is not int or self._batch_delay not in {100, 200, 500, 1000}:
            self._batch_delay = 200
        self._search_type = ""
        self._notes_visible = False
        self._activity_notifications = True
        self._running = False
        self._busy = False
        self._initial_messages = True
        self._initial_activity = True
        self._message_cursor = ""
        self._activity_cursor = ""
        self._reaction_cursor = ""
        self._cache_cursor = ""
        self._failure_count = 0
        self._failure_reported = False
        self._session = None
        self._activity_enabled = False
        self._messages_visible = False
        self._tasks_visible = False
        self._request_included_activity = False
        self._request_generation = 0
        self._checkin_active = False
        self._deferred_result = None
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
        self._settings["network/serverUpdateInterval"] = seconds
        self._application._write_settings()
        if self._running and not self._busy:
            self._schedule(self._poll_delay())
        self.stateChanged.emit()

    @Property(str, notify=stateChanged)
    def update_mode(self) -> str:
        return self._update_mode

    @Slot(str)
    def set_update_mode(self, value: str) -> None:
        if value not in {"poll", "sse"} or value == self._update_mode:
            return
        running = self._running
        self.stop()
        self._update_mode = value
        self._settings["network/serverUpdateMode"] = value
        self._application._write_settings()
        self.stateChanged.emit()
        if running:
            self.start()

    @Property(int, notify=stateChanged)
    def batch_delay(self) -> int:
        return self._batch_delay

    @Slot(int)
    def set_batch_delay(self, milliseconds: int) -> None:
        if milliseconds not in {100, 200, 500, 1000} or milliseconds == self._batch_delay:
            return
        self._batch_delay = milliseconds
        self._settings["network/serverUpdateBatchDelay"] = milliseconds
        self._application._write_settings()
        if self._stream is not None:
            self._stream.batch_delay = milliseconds
        self.stateChanged.emit()

    def _cancel_stream(self) -> None:
        if self._stream is not None:
            self._stream.cancel()
            self._stream.deleteLater()
            self._stream = None

    def _restart_stream(self) -> None:
        if self._update_mode != "sse" or not self._running:
            return
        if self._failure_count and self._stream is None:
            return
        self._request_generation += 1
        self._cancel_stream()
        self._busy = False
        self.poll()

    @Slot(str)
    def set_search_type(self, value: str) -> None:
        value = str(value or "").split("?", 1)[0]
        if self._search_type != value:
            self._search_type = value
            self._restart_stream()

    @Slot(bool)
    def set_notes_visible(self, value: bool) -> None:
        if self._notes_visible != bool(value):
            self._notes_visible = bool(value)
            self._restart_stream()

    @Slot(bool)
    def set_activity_notifications(self, value: bool) -> None:
        if self._activity_notifications != bool(value):
            self._activity_notifications = bool(value)
            self._restart_stream()

    def _start_stream(self, session, project_code: str) -> None:
        from thlib.environment import env_server
        from .server_event_stream import ServerEventStream

        channels = ["messages", "reactions"]
        if project_code and (self._activity_enabled or self._activity_notifications):
            channels.append("activity")
        types = {"sthpw/task", "sthpw/note", "sthpw/snapshot", "sthpw/file", "sthpw/connection", "sthpw/status_log"} if self._search_type else set()
        types.update({
            "sthpw/message", "sthpw/message_log", "sthpw/subscription",
            "config/widget_config", "config/custom_script", "config/trigger", "config/process",
            "sthpw/project", "sthpw/schema", "sthpw/search_object", "sthpw/pipeline",
            "sthpw/login", "sthpw/login_group", "sthpw/login_in_group",
        })
        if self._search_type:
            types.add(self._search_type)
        if self._tasks_visible or self._notes_visible:
            types.update({"sthpw/task", "sthpw/note", "sthpw/work_hour"})
        if types:
            channels.append("cache")
        payload = dict(ticket=session[2], project=project_code,
                       message_after=self._message_cursor, activity_after=self._activity_cursor,
                       reaction_after=self._reaction_cursor, cache_after=self._cache_cursor,
                       channels=channels, search_types=sorted(types), presence_ttl=90)
        self._request_included_activity = "activity" in channels
        self._request_generation += 1
        generation = self._request_generation
        stream = ServerEventStream(session[0], payload, env_server.get_proxy(), self, batch_delay=self._batch_delay)
        self._stream = stream
        self._busy = True
        stream.batchReady.connect(lambda value: self._ready_for(generation, value))
        stream.failed.connect(lambda error: self._stream_failed(generation, error))
        self.stateChanged.emit()
        stream.start()

    def _stream_failed(self, generation: int, error) -> None:
        if generation != self._request_generation or not self._running:
            return
        self._cancel_stream()
        failure = error.get("exception")
        code = getattr(failure, "code", "")
        transient = code in {"stream_closed", "transport_error"} or getattr(failure, "status", 0) in self._transient_http_codes or (
            not getattr(failure, "status", 0) and self._is_transient_error(failure))
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log is not None:
            debug_log.log(
                "ERROR",
                str(failure), group="communication/server-updates", source="Server updates",
                stacktrace=str(error.get("stacktrace") or ""),
                details=json.dumps(dict(error.get("details") or {}, attempt=self._failure_count + 1), ensure_ascii=False),
            )
        if code == "authentication_failed":
            self.stop()
            self._application.request_authentication()
        elif transient:
            self._transient_failed(dict(message=str(failure), stacktrace=error.get("stacktrace", "")))
        else:
            self._failed(error)

    def _poll_delay(self) -> int:
        return self._poll_interval * 1000

    @Slot()
    def start(self) -> None:
        if getattr(self._application, "authentication_required", False):
            return
        if self._running:
            return
        self._failure_count = 0
        self._failure_reported = False
        self._running = True
        self.stateChanged.emit()
        self.poll()

    @Slot()
    def sync_authentication(self) -> None:
        """Start, wake, or stop polling with the authenticated session."""
        from thlib.environment import env_inst, env_server

        ticket = str(env_server.get_ticket() or "")
        if (getattr(self._application, "authentication_required", False)
                or not ticket or not env_inst.logins):
            if self._running:
                self.stop()
            return
        session = (
            str(env_server.get_server() or ""),
            str(env_server.get_user() or ""),
            ticket,
        )
        if self._session and session != self._session:
            self.stop()
        if not self._running:
            self.start()
        elif not self._busy:
            self.poll()

    @Slot()
    def stop(self) -> None:
        self._request_generation += 1
        self._running = False
        self._deferred_result = None
        self._timer.stop()
        self._cancel_stream()
        cancel = getattr(self._worker, "cancel", None)
        if callable(cancel):
            cancel()
        self._worker = None
        self._busy = False
        self.stateChanged.emit()

    def _project_changed(self, *_args) -> None:
        self._cancel_stream()
        self._deferred_result = None
        self._request_generation += 1
        cancel = getattr(self._worker, "cancel", None)
        if callable(cancel):
            cancel()
        self._worker = None
        self._busy = False
        self._activity_cursor = ""
        self._cache_cursor = ""
        self._initial_activity = True
        self._failure_count = 0
        self._failure_reported = False
        if self._running:
            self.poll()

    def _schedule(self, delay: int | None = None) -> None:
        if not self._running or self._stream is not None:
            return
        if delay is None:
            delay = self._poll_delay()
        self._timer.start(max(1, int(delay)))

    @Slot(bool)
    def set_activity_enabled(self, value: bool) -> None:
        if self._activity_enabled != bool(value):
            self._activity_enabled = bool(value)
            self._restart_stream()

    @Slot(bool)
    def set_messages_visible(self, value: bool) -> None:
        self._messages_visible = bool(value)

    @Slot(bool)
    def set_tasks_visible(self, value: bool) -> None:
        if self._tasks_visible != bool(value):
            self._tasks_visible = bool(value)
            self._restart_stream()

    @Slot(bool)
    def set_checkin_active(self, active: bool) -> None:
        active = bool(active)
        if self._checkin_active == active:
            return
        self._checkin_active = active
        if active:
            self._timer.stop()
            self._cancel_stream()
            self._busy = False
            return
        result, self._deferred_result = self._deferred_result, None
        if result is not None:
            self._ready(result)
        if self._running:
            self.poll()

    @Slot()
    def poll(self) -> None:
        if getattr(self._application, "authentication_required", False):
            if self._running:
                self.stop()
            return
        if not self._running or self._busy or self._checkin_active or self._stream is not None:
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
            self.clock.reset(session)
            self._message_cursor = ""
            self._activity_cursor = ""
            self._reaction_cursor = ""
            self._cache_cursor = ""
            self._initial_messages = True
            self._initial_activity = True
            self._failure_count = 0
            self._failure_reported = False
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        project_code = str(self._application.current_project_code or "")
        if self._update_mode == "sse":
            self._start_stream(session, project_code)
            return
        message_cursor = self._message_cursor
        activity_cursor = self._activity_cursor
        reaction_cursor = self._reaction_cursor
        cache_cursor = self._cache_cursor
        # Project activity remains part of the shared batch because badges and
        # task state depend on its cursor. Chat is global notification state:
        # it must be polled even before the Messages window is instantiated.
        include_activity = bool(project_code)
        include_messages = True
        # This stream also carries delivery and read receipts, which must keep
        # advancing while the Messages window is hidden.
        include_reactions = True
        self._request_included_activity = include_activity

        def operation():
            import thlib.tactic_classes as tc
            from thlib import server_cache

            try:
                if not self._running or self._session != session:
                    return None
                client_clock_started = time.time()
                effective_cache_cursor = (
                    cache_cursor
                    or server_cache.read_cursor(
                        "server_changes", project_code
                    )
                )
                if not self._running or self._session != session:
                    return None
                with request_metrics.measure("server.poll") as metric:
                    with defer_transient_error_reporting():
                        result = tc.get_server_updates(
                            message_after=message_cursor,
                            activity_after=activity_cursor,
                            reaction_after=reaction_cursor,
                            project_code=project_code,
                            limit=101,
                            include_activity=include_activity,
                            include_messages=include_messages,
                            include_reactions=include_reactions,
                            include_presence=True,
                            heartbeat_presence=True,
                            presence_ttl=max(90, self._poll_interval * 3),
                            cache_after=effective_cache_cursor,
                        )
                    client_clock_received = time.time()
                    result = dict(result or {})
                    result["__clientClockStartedEpoch"] = (
                        client_clock_started
                    )
                    result["__clientClockReceivedEpoch"] = (
                        client_clock_received
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
        if is_transient_read_error(error):
            return True
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
        delay = min(30000, 2000 * (2 ** max(0, self._failure_count - 1)))
        return int(delay * random.uniform(.75, 1.25)) if self._update_mode == "sse" else delay

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
            self.connectionChecked.emit(False)
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
        if self._checkin_active:
            self._deferred_result = value
            self._worker = None
            self._busy = False
            self.stateChanged.emit()
            return
        if value.get("__transient_error__"):
            self._transient_failed(value)
            return
        self.clock.observe(
            value.get("serverClock"),
            value.get("__clientClockStartedEpoch"),
            value.get("__clientClockReceivedEpoch"),
            session=self._session,
        )
        messages = list(value.get("messages") or [])
        reactions = list(value.get("reactions") or [])
        activity = list(value.get("activity") or [])
        presence = list(value.get("presence") or [])
        cache_changes = list(value.get("cacheChanges") or [])
        cache_retired = list(value.get("cacheRetired") or [])
        cache_cursor = str(value.get("cacheCursor") or "")
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
        if cache_cursor:
            self._cache_cursor = cache_cursor
        batch = {
            "messages": messages,
            "reactions": reactions,
            "activity": activity,
            "initialMessages": self._initial_messages,
            "initialActivity": self._initial_activity,
            "presence": presence,
            "cacheChanges": cache_changes,
            "cacheRetired": cache_retired,
        }
        self._initial_messages = False
        if self._request_included_activity:
            self._initial_activity = False
        self._worker = None
        self._busy = False
        self._failure_count = 0
        self._failure_reported = False
        self.stateChanged.emit()
        self.connectionChecked.emit(True)
        if (
                messages or reactions or activity or presence
                or cache_changes or cache_retired):
            self.batchReady.emit(batch)
        if cache_cursor:
            from thlib import server_cache

            # Deferred batches must not advance the persisted cursor before delivery.
            server_cache.write_cursor(
                'server_changes', cache_cursor,
                str(self._application.current_project_code or ''),
            )
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
