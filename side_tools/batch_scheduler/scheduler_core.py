"""Batch queue state and command controller."""

from __future__ import annotations

import threading
import time
import traceback
import uuid
from concurrent.futures import Future
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue

from PySide6.QtCore import Property, QObject, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication

from tactic_handler_api.operations import Operation
from thlib.ui.window_geometry import (
    current_screens,
    resolve_window_state,
    screen_for_window_rect,
)
from thlib.ui.workspace_models.records import RecordListModel

from .scheduler_domain import (
    BATCH_DISPATCHER_CONFIG,
    _discover_queue,
    _duration,
    _episode_filter_statuses,
    _finalize_preparation_log,
    _finalize_shot,
    _format_frame_ranges,
    _job_frame_count,
    _job_ranges,
    _parse_frame_spec,
    _prepare_episode,
    _prepare_shot,
    _query_episodes,
    _queue_entry,
    _render_native,
    _set_episode_task_status,
    _shot_job,
    _total_eta,
    _ui_text,
)
from .scheduler_web import BatchWebServer



# Queue controller


_TERMINAL = {"completed", "failed", "cancelled", "skipped"}
_ACTIVE = {"preparing", "rendering", "paused", "saving", "stopping"}
_IDLE = {"waiting", "held"}
_RETRYABLE = {"failed", "cancelled"}
_RUNNABLE = _IDLE | _RETRYABLE


class BatchDispatcherController(QObject):
    stateChanged = Signal()
    settingsChanged = Signal()
    queueChanged = Signal()
    episodeFiltersChanged = Signal()
    queueSelected = Signal(int, bool)
    episodeSelected = Signal(int)
    logChanged = Signal()
    logScopeChanged = Signal()
    windowStateChanged = Signal()
    webChanged = Signal()
    windowCloseRequested = Signal()
    _dispatchRequested = Signal(object)

    def __init__(
        self,
        api,
        project_code: str,
        manifest: dict | None = None,
        *,
        settings: dict | None = None,
        offline: bool = False,
    ):
        super().__init__()
        self._api = api
        self._project_code = project_code
        self._config = deepcopy((manifest or BATCH_DISPATCHER_CONFIG)["project_config"])
        self._config.update(settings or {})
        self._offline = offline
        self._ready = offline
        self._closing = False
        self._close_requested = False
        self._operations = {}
        self._entries = []
        self._hidden_episodes = {}
        self._events = []
        self._selected_episode = ""
        self._selected_queue = ""
        self._run_only = ""
        self._pending_removal = ""
        self._active_entry = None
        self._active_job = None
        self._discovery_entry = None
        self._stage_operation = None
        self._cancel = threading.Event()
        self._render_pause = threading.Event()
        self._cancel_job_only = False
        self._paused = True
        self._auto_clear_finished = False
        self._watch_server = False
        self._server_seen = set()
        self._generation = 0
        self._busy = False
        self._status = "Queue paused"
        self._error = ""
        self._window = None
        self._window_state = {
            "x": 80,
            "y": 60,
            "width": 1440,
            "height": 920,
            "maximized": False,
            "episodeWidth": 350,
            "detailHeight": 235,
            "logPanelVisible": True,
            "detailPage": "log",
            "followLog": True,
            "freezeLog": False,
            "episodeStatuses": [
                status
                for status in _episode_filter_statuses(self._config)
                if status != self._config["terminal_status"]
            ],
        }
        self._tray = None
        self._web_server = None
        self._web_error = ""
        self._web_theme = {}
        self._last_tick = time.monotonic()
        self._pending_save = None
        self._saving = False
        self._write_blocked = False
        self.episodes = RecordListModel(
            (
                "title",
                "searchKey",
                "code",
                "selected",
                "subtitle",
                "previewUrl",
                "renderStatus",
                "statusColor",
                "statusChoices",
                "queued",
            ),
            identity_role="searchKey",
        )
        self.queue = RecordListModel(
            (
                "jobId",
                "parentId",
                "title",
                "subtitle",
                "state",
                "stage",
                "selected",
                "expanded",
                "progress",
                "frames",
                "elapsed",
                "eta",
                "depth",
                "test",
                "attempt",
                "pid",
                "error",
                "indeterminate",
                "previewUrl",
                "included",
                "actions",
            ),
            identity_role="jobId",
        )
        self.episode_filters = RecordListModel(
            ("value", "title", "statusAccent", "count", "active")
        )
        self.episode_filters.replace(
            [
                {
                    "value": status,
                    "title": status,
                    "statusAccent": "",
                    "count": 0,
                    "active": status != self._config["terminal_status"],
                }
                for status in _episode_filter_statuses(self._config)
            ]
        )
        self._dispatchRequested.connect(
            self._invoke, Qt.ConnectionType.QueuedConnection
        )
        self._poll_timer = QTimer(self)
        self._poll_timer.setSingleShot(True)
        self._poll_timer.timeout.connect(self.refresh)
        self._clock = QTimer(self)
        self._clock.setInterval(1000)
        self._clock.timeout.connect(self._tick)
        self._clock.start()

    @Slot(object)
    def _invoke(self, callback):
        if not self._closing:
            callback()

    def _web_dispatch(self, request):
        reply = Queue(maxsize=1)

        def handle():
            try:
                reply.put(self._handle_web_request(request))
            except Exception as error:
                reply.put(error)

        self._dispatchRequested.emit(handle)
        try:
            result = reply.get(timeout=10)
        except Empty as error:
            raise TimeoutError("Batch Dispatcher did not answer") from error
        if isinstance(result, Exception):
            raise result
        return result

    def _handle_web_request(self, request):
        request_type = request.get("type")
        if request_type == "state":
            return self._web_state(str(request.get("selected") or ""))
        if request_type == "preview":
            return self._web_preview(
                str(request.get("job") or ""), int(request.get("index", -1))
            )
        if request_type == "thumb":
            return self._web_thumb(str(request.get("identity") or ""))
        if request_type != "action":
            raise ValueError("Unknown web request")
        return self._web_action(request)

    def _web_state(self, identity):
        frame_seconds = self._frame_seconds()
        queue = [
            {
                "episode": self._episode_record(entry, frame_seconds),
                "shots": [
                    self._shot_record(entry, job, frame_seconds)
                    for job in entry["jobs"]
                ],
            }
            for entry in self._entries
        ]
        job = self._preview_job(identity)
        previews = [
            {"jobId": job["id"], "title": Path(path).name}
            for path in (job or {}).get("renderFiles", [])
        ]
        return {
            "ready": self._ready,
            "busy": self._busy,
            "running": self.running,
            "paused": self._paused,
            "watchServer": self._watch_server,
            "autoClear": self._auto_clear_finished,
            "status": self.statusText,
            "error": self._error,
            "summary": self.summary,
            "settings": self.settings,
            "theme": self._web_theme,
            "filters": self.episode_filters.records(),
            "episodes": self.episodes.records(),
            "queue": queue,
            "selected": self._detail(identity),
            "log": self._log_text(identity),
            "previews": previews,
        }

    def _web_preview(self, identity, index):
        job = self._preview_job(identity)
        files = (job or {}).get("renderFiles", [])
        if not 0 <= index < len(files):
            raise ValueError("Preview is no longer available")
        return files[index]

    def _web_thumb(self, identity):
        entry, job = self._find(identity)
        row = job or entry
        if row is None:
            row = self.episodes.lookup("searchKey", identity)
        url = str((row or {}).get("previewUrl") or "")
        if url.startswith(("http://", "https://")):
            return url
        path = QUrl(url).toLocalFile()
        if not path or not Path(path).is_file():
            raise ValueError("Preview is no longer available")
        return path

    def _web_action(self, request):
        action = str(request.get("action") or "")
        simple = {
            "toggle": self.toggleScheduler,
            "stop": self.interruptRender,
            "refresh": self.refresh,
            "clear": self.clearCompleted,
            "open-root-output": self.showDestination,
        }
        if action in simple:
            simple[action]()
            return {"ok": True}
        if action == "watch":
            self.watchServer(not self._watch_server)
            return {"ok": True}
        if action == "auto":
            self.setAutoClearFinished(not self._auto_clear_finished)
            return {"ok": True}
        if action == "filter":
            status = str(request.get("value") or "")
            if status not in {row["value"] for row in self.episode_filters.records()}:
                raise ValueError("Unknown episode status")
            self.toggleEpisodeStatusFilter(status)
            return {"ok": True}
        if action == "settings":
            values = request.get("values") or {}
            if not isinstance(values, dict):
                raise ValueError("Invalid render settings")
            web_security = values.get(
                "webSecurity", self._config.get("web_security", False)
            )
            self.saveSettings(
                str(values.get("mayaPath") or ""),
                str(values.get("savePath") or ""),
                str(values.get("camera") or ""),
                bool(values.get("stopOnError")),
                int(values.get("timeout") or 0),
                str(values.get("logCheckin") or "always"),
                bool(values.get("skipDependencyErrors")),
                int(values.get("pollInterval") or 10),
                bool(values.get("webEnabled", True)),
                int(values.get("webPort") or 92),
                bool(web_security),
            )
            return {"ok": True}

        identity = str(request.get("id") or "")
        if action == "add":
            row = next(
                (
                    index
                    for index, episode in enumerate(self.episodes.records())
                    if episode["searchKey"] == identity
                ),
                -1,
            )
            if row < 0:
                raise ValueError("Episode is no longer available")
            self.renderEpisode(row, False)
            return {"ok": True}
        if action == "status":
            row = next(
                (
                    index
                    for index, episode in enumerate(self.episodes.records())
                    if episode["searchKey"] == identity
                ),
                -1,
            )
            if row < 0:
                raise ValueError("Episode is no longer available")
            status = str(request.get("value") or "")
            allowed = {
                choice.get("title") for choice in self.episodeStatusChoices(row)
            }
            if status not in allowed:
                raise ValueError("Unknown episode status")
            self.setEpisodeStatus(row, status)
            return {"ok": True}
        if action == "open-output":
            self.showQueueDestination(identity)
            return {"ok": True}
        if action == "open-log":
            path = self._detail(identity).get("logPath")
            if not path:
                raise ValueError("Render log is not available yet")
            self.openPath(path)
            return {"ok": True}

        commands = {
            "test": self.testQueue,
            "only": self.runOnly,
            "hold": self.holdQueue,
            "retry": self.retryQueue,
            "cancel": self.cancelQueue,
            "remove": self.removeEpisode,
            "include": self.toggleIncluded,
        }
        if action in commands:
            commands[action](identity)
        elif action in {"top", "up", "down", "bottom"}:
            delta = {"top": -1000000, "up": -1, "down": 1, "bottom": 1000000}
            self.moveQueue(identity, delta[action])
        elif action == "move-to":
            self.moveQueueTo(identity, str(request.get("target") or ""))
        elif action == "frames":
            if not self.setFrameSpec(identity, str(request.get("value") or "")):
                raise ValueError(self._error or "Cannot change frame selection")
        else:
            raise ValueError("Unknown batch action")
        return {"ok": True}

    def _submit(self, function, done, failed=None, progress=None):
        try:
            operation = self._api.submit(function)
        except Exception as error:
            future = Future()
            future.set_exception(error)
            operation = Operation(future)
        subscriptions = []
        self._operations[operation.id] = (operation, subscriptions)

        def finish(callback, value):
            entry = self._operations.pop(operation.id, None)
            if entry:
                for subscription in entry[1]:
                    subscription.close()
            if self._closing:
                return
            try:
                callback(value)
            except Exception as error:
                if callback is done and failed is not None:
                    failed(error)
                else:
                    self._error_message(error)
            self._maybe_close()

        subscriptions.append(
            operation.on_done(
                lambda value: finish(done, value),
                dispatch=self._dispatchRequested.emit,
            )
        )
        subscriptions.append(
            operation.on_error(
                lambda error: finish(failed or self._error_message, error),
                dispatch=self._dispatchRequested.emit,
            )
        )
        if progress:
            # Capture progress before Operation closes its subscriptions on
            # completion. Already-posted final output must still reach Qt.
            def received(value):
                self._dispatchRequested.emit(
                    lambda: (
                        progress(value) if operation.id in self._operations else None
                    )
                )

            subscriptions.append(operation.on_progress(received))
        return operation

    # QML state

    @Property(QObject, constant=True)
    def episodesModel(self):
        return self.episodes

    @Property(QObject, constant=True)
    def queueModel(self):
        return self.queue

    @Property(bool, notify=stateChanged)
    def ready(self):
        return self._ready

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(bool, notify=stateChanged)
    def running(self):
        return self._stage_operation is not None

    @Property(bool, notify=stateChanged)
    def paused(self):
        return self._paused

    @Property(bool, notify=stateChanged)
    def schedulerRunning(self):
        return self._watch_server

    @Property(bool, notify=stateChanged)
    def autoClearFinished(self):
        return self._auto_clear_finished

    @Property(str, notify=webChanged)
    def webUrl(self):
        return self._web_server.url if self._web_server else ""

    @Property(str, notify=webChanged)
    def webError(self):
        return self._web_error

    @Property(QObject, constant=True)
    def episodeFiltersModel(self):
        return self.episode_filters

    @Property("QVariantList", notify=episodeFiltersChanged)
    def visibleEpisodeStatuses(self):
        return [
            row["value"]
            for row in self.episode_filters.records()
            if row["active"]
        ]

    @Property("QVariantList", notify=episodeFiltersChanged)
    def episodeFilterChoices(self):
        return self.episode_filters.records()

    def _replace_episode_filters(self, records):
        current = {
            row["value"]: row["active"]
            for row in self.episode_filters.records()
        }
        self.episode_filters.replace(
            [
                {
                    **record,
                    "active": current.get(
                        record["value"],
                        record["value"] != self._config["terminal_status"],
                    ),
                }
                for record in records
            ]
        )
        self.episodeFiltersChanged.emit()

    @Slot(str)
    def toggleEpisodeStatusFilter(self, status):
        records = self.episode_filters.records()
        row = next(
            (index for index, value in enumerate(records) if value["value"] == status),
            -1,
        )
        if row < 0:
            return
        self.episode_filters.set_value(row, "active", not records[row]["active"])
        self.episodeFiltersChanged.emit()
        self.refresh()

    @Slot(bool)
    def setAutoClearFinished(self, enabled):
        self._auto_clear_finished = bool(enabled)
        if enabled:
            self.clearCompleted()
        self.stateChanged.emit()

    @Property(str, notify=stateChanged)
    def statusText(self):
        return _ui_text(self._status)

    @Property(str, notify=stateChanged)
    def errorText(self):
        return self._error

    @Property(bool, notify=stateChanged)
    def closePending(self):
        return self._close_requested

    @Slot(int, result="QVariantList")
    def episodeStatusChoices(self, row):
        return self.episodes.get(row).get("statusChoices") or [
            {"title": value} for value in self._config["status_options"]
        ]

    @Property("QVariantMap", notify=settingsChanged)
    def settings(self):
        return {
            "mayaPath": self._config["maya_render_executable"],
            "savePath": self._config["output_directory"],
            "camera": self._config["camera"],
            "stopOnError": self._config.get("stop_on_error", False),
            "timeout": self._config.get("render_timeout_minutes", 0),
            "logCheckin": self._config.get("log_checkin", "always"),
            "skipDependencyErrors": self._config.get(
                "skip_dependency_errors", False
            ),
            "pollInterval": self._config.get("update_interval", 10),
            "webEnabled": self._config.get("web_enabled", True),
            "webPort": self._config.get("web_port", 92),
            "webSecurity": self._config.get("web_security", False),
        }

    @Property("QVariantMap", notify=windowStateChanged)
    def windowState(self):
        return dict(self._window_state)

    @Property("QVariantMap", notify=queueChanged)
    def summary(self):
        jobs = [job for entry in self._entries for job in entry["jobs"]]
        pending = sum(job["state"] not in _TERMINAL for job in jobs)
        completed = sum(job["state"] == "completed" for job in jobs)
        failed = sum(job["state"] == "failed" for job in jobs)
        total = sum(_job_frame_count(job) for job in jobs if job["state"] != "skipped")
        done = sum(
            _job_frame_count(job) * self._job_fraction(job)
            for job in jobs
            if job["state"] != "skipped"
        )
        frame_seconds = self._frame_seconds()
        estimates = [
            self._job_eta(job, frame_seconds)
            for job in jobs
            if job["state"] not in _TERMINAL
        ]
        eta = _total_eta(estimates)
        return {
            "episodes": len(self._entries),
            "shots": len(jobs),
            "pending": pending,
            "completed": completed,
            "failed": failed,
            "progress": done / total if total else 0,
            "elapsed": _duration(
                sum(entry.get("elapsed", 0) for entry in self._entries)
            ),
            "eta": ("~" + _duration(eta)) if eta is not None else "—",
        }

    def _find(self, identity):
        for entry in self._entries:
            if entry["id"] == identity:
                return entry, None
            for job in entry["jobs"]:
                if job["id"] == identity:
                    return entry, job
        return None, None

    @Property("QVariantMap", notify=queueChanged)
    def selectedDetail(self):
        return self._detail(self._selected_queue)

    def _detail(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return {}
        row = job or entry
        frame_spec = (
            row.get("frameSpec") or _format_frame_ranges(_job_ranges(row))
            if job
            else ""
        )
        return {
            "id": row["id"],
            "title": row["title"],
            "state": row["state"],
            "stage": _ui_text(row.get("stage", "")),
            "error": row.get("error", ""),
            "command": row.get("command", ""),
            "scene": row.get("scene", ""),
            "output": row.get("renderOutput")
            or row.get("output", self._config["output_directory"]),
            "logPath": row.get("logPath", ""),
            "exitCode": row.get("exitCode", ""),
            "pid": row.get("pid", ""),
            "attempt": row.get("attempt", 1),
            "elapsed": _duration(row.get("elapsed", 0)),
            "frameSpec": frame_spec,
            "frames": f"{row.get('frame', '—')} / {frame_spec}" if job else "",
            "test": entry["test"],
            "child": bool(job),
            "actions": self._allowed_actions(entry, job),
        }

    def _preview_job(self, identity=None):
        entry, job = self._find(
            self._selected_queue if identity is None else identity
        )
        if job is not None:
            return job
        if entry is self._active_entry and self._active_job is not None:
            return self._active_job
        if entry is not None:
            return next(
                (row for row in reversed(entry["jobs"]) if row.get("renderFiles")),
                None,
            )
        return self._active_job

    @Property("QVariantList", notify=queueChanged)
    def renderPreviews(self):
        job = self._preview_job()
        previews = []
        for path in (job or {}).get("renderFiles", []):
            url = QUrl.fromLocalFile(path)
            try:
                url.setQuery(f"changed={Path(path).stat().st_mtime_ns}")
            except OSError:
                pass
            previews.append(
                {
                    "jobId": job["id"],
                    "path": path,
                    "url": url.toString(),
                    "title": Path(path).name,
                }
            )
        return previews

    def _allowed_actions(self, entry, job=None):
        if not self._ready or self._close_requested:
            return []

        row = job or entry
        state = row["state"]
        targets = [job] if job else entry["jobs"]
        entry_busy = entry["state"] in _ACTIVE | {"discovering"}
        allowed = set()

        active_render = (
            entry is self._active_entry
            and self._active_job is not None
            and self._active_job["state"] in {"rendering", "paused"}
            and (job is None or job is self._active_job)
        )
        if active_render:
            allowed.add("hold")
        elif state in _IDLE:
            allowed.add("hold")
            if (job is None and entry["state"] not in _ACTIVE) or (
                job is not None and job is not self._active_job
            ):
                allowed.add("move")
        if state not in _TERMINAL:
            allowed.add("cancel")
        if job is not None and state in _IDLE | {"skipped"}:
            include_locked = entry["state"] == "saving" or entry.get("saveFailed")
            if not include_locked:
                allowed.add("include")

        if job is None and (
            self._entry_is_removable(entry) or entry is self._active_entry
        ):
            allowed.add("remove")

        save_failed = entry.get("saveFailed") or any(
            target.get("saveFailed") for target in targets
        )
        if not save_failed and not entry_busy:
            allowed.update(self._rerun_actions(entry, job, targets))
        if not entry["test"] and targets:
            allowed.add("test")
        return sorted(allowed)

    def _rerun_actions(self, entry, job, targets):
        state = (job or entry)["state"]
        allowed = set()
        retryable = state in _RETRYABLE
        if job is None:
            retryable |= any(target["state"] in _RETRYABLE for target in targets)
        if retryable:
            allowed.add("retry")

        if job is not None and not entry["test"] and state in _RUNNABLE | {"skipped"}:
            allowed.add("frames")

        runnable = any(target["state"] in _RUNNABLE for target in targets)
        runnable |= job is not None and state == "skipped"
        if not self.running and runnable:
            allowed.add("only")
        return allowed

    def _entry_is_removable(self, entry):
        if entry["state"] in _ACTIVE | {"discovering"}:
            return False
        if entry is self._active_entry or entry is self._discovery_entry:
            return False
        identities = {entry["id"]}
        identities.update(job["id"] for job in entry["jobs"])
        return self._run_only not in identities

    @Property(str, notify=logChanged)
    def logText(self):
        return self._log_text(self._selected_queue)

    def _log_text(self, identity):
        entry, job = self._find(identity)
        return "\n".join(
            text
            for entry_id, job_id, text in self._events
            if entry is None
            or (entry_id == entry["id"] and (job is None or job_id == job["id"]))
        )

    def _log(self, text, entry=None, job=None):
        text = str(text).rstrip()
        if not text:
            return
        self._events.append(
            (
                (entry or {}).get("id", ""),
                (job or {}).get("id", ""),
                f"[{datetime.now().strftime('%H:%M:%S')}] {text}",
            )
        )
        # The UI retains complete events; renderer output is also kept on disk.
        self._events = self._events[-1000:]
        self.logChanged.emit()

    def _error_message(self, error):
        self._error = str(error)
        self._log(
            "".join(traceback.format_exception(error)).strip(),
            self._active_entry,
            self._active_job,
        )
        self.stateChanged.emit()

    # Persistence and TACTIC discovery

    def initialize(self):
        if self._offline:
            self.stateChanged.emit()
            return
        self._submit(
            self._load_saved_state,
            self._state_loaded,
            self._state_load_failed,
        )

    def _load_saved_state(self):
        # Scope durable work to the same endpoint and project.
        import hashlib

        from thlib.environment import env_read_config, env_server
        from thlib.ui.server_address import normalize_tactic_server_url

        endpoint = normalize_tactic_server_url(env_server.get_server())
        scope = (
            hashlib.sha256(endpoint.encode()).hexdigest()[:16]
            + "/"
            + self._project_code
        )
        settings = (
            env_read_config(
                filename="ui_batch_dispatcher",
                unique_id=self._project_code,
                long_abs_path=True,
            )
            or {}
        )
        window_state = (
            env_read_config(
                filename="ui_batch_dispatcher_window",
                unique_id=self._project_code,
                long_abs_path=True,
            )
            or {}
        )
        queue = (
            env_read_config(
                filename="batch_queue",
                unique_id="cache/" + scope,
                long_abs_path=True,
            )
            or {}
        )
        return settings, window_state, queue, scope

    def _state_loaded(self, payload):
        settings, window_state, queue, self._scope = payload
        previous_web = (
            self._config.get("web_enabled", True),
            self._config.get("web_port", 92),
            self._config.get("web_security", False),
        )
        self._config.update(
            {key: value for key, value in settings.items() if key in self._config}
        )
        if (
            self._window is not None
            and (
                self._config.get("web_enabled", True),
                self._config.get("web_port", 92),
                self._config.get("web_security", False),
            ) != previous_web
        ):
            self._restart_web_server()
        self._window_state = self._resolved_window_state(window_state)
        visible_statuses = set(self._window_state["episodeStatuses"])
        self.episode_filters.replace([
            {**row, "active": row["value"] in visible_statuses}
            for row in self.episode_filters.records()
        ])
        self.episodeFiltersChanged.emit()
        if queue and queue.get("version") != 1:
            raise ValueError(
                "Unknown batch queue format; saved queue has not been overwritten"
            )
        self._entries = queue.get("entries", [])
        for entry in self._entries:
            if entry["state"] not in _TERMINAL:
                entry.update(
                    state="held",
                    restored=True,
                    stage="Restored · resume or retry explicitly",
                )
            for job in entry["jobs"]:
                if job["state"] in _ACTIVE:
                    job.update(
                        state="failed",
                        stage="Interrupted session",
                        pid="",
                        error="Interrupted session; verify output before retrying",
                    )
            entry["prepared"] = False
        self._server_seen = set(queue.get("serverSeen", []))
        self._ready = True
        self._publish_queue()
        self.settingsChanged.emit()
        self.windowStateChanged.emit()
        self.stateChanged.emit()
        self.refresh()

    def _state_load_failed(self, error):
        self._write_blocked = True
        self._error_message(error)

    def _persist(self):
        if self._offline or not self._ready or self._write_blocked:
            return
        self._pending_save = {
            "version": 1,
            "entries": deepcopy(self._entries),
            "serverSeen": sorted(self._server_seen),
        }
        self._save_next()

    def _flush_queue(self):
        self._publish_queue()
        self._persist()

    def _save_next(self):
        if self._saving or self._pending_save is None:
            return
        from thlib.environment import env_write_config

        payload, self._pending_save = self._pending_save, None
        self._saving = True
        self._submit(
            lambda: env_write_config(
                payload,
                filename="batch_queue",
                unique_id="cache/" + self._scope,
                long_abs_path=True,
            ),
            self._queue_saved,
            self._queue_save_failed,
        )

    def _queue_saved(self, _value):
        self._saving = False
        self._save_next()
        self._maybe_close()

    def _queue_save_failed(self, error):
        self._saving = False
        self._paused = True
        self._error_message(error)
        self._maybe_close()

    @Slot()
    def refresh(self):
        if self._offline or self._busy or not self._ready or self._close_requested:
            return
        self._poll_timer.stop()
        self._generation += 1
        generation = self._generation
        self._busy = True
        self.stateChanged.emit()
        config = dict(self._config)
        visible_statuses = tuple(self.visibleEpisodeStatuses)
        watch_server = self._watch_server
        self._submit(
            lambda: _query_episodes(
                self._api,
                self._project_code,
                config,
                visible_statuses,
                watch_server,
            ),
            lambda payload: self._episodes_ready(generation, payload),
            lambda error: self._refresh_failed(generation, error),
        )

    def _refresh_failed(self, generation, error):
        if generation != self._generation:
            return
        self._busy = False
        self._error_message(error)
        self._schedule_poll()

    def _schedule_poll(self):
        if self._watch_server and not self._close_requested:
            self._poll_timer.start(max(5, int(self._config["update_interval"])) * 1000)

    def _episodes_ready(self, generation, payload):
        if generation != self._generation:
            return
        records = payload["episodes"]
        queued_records = payload["queuedEpisodes"]
        local_queue = {
            entry["episodeKey"]
            for entry in self._entries
            if entry["state"] not in _TERMINAL
        }
        queued_keys = {entry["episodeKey"] for entry in self._entries}
        visible_records = []
        for index, row in enumerate(records):
            row["selected"] = row["searchKey"] == self._selected_episode
            row["queued"] = row["searchKey"] in local_queue
            if row["searchKey"] in queued_keys:
                self._hidden_episodes[row["searchKey"]] = (index, row)
            else:
                visible_records.append(row)
        self._replace_episode_filters(payload["filters"])
        previews = {
            row["searchKey"]: row.get("previewUrl", "")
            for row in [*records, *queued_records]
        }
        for entry in self._entries:
            if entry["episodeKey"] in previews:
                entry["previewUrl"] = previews[entry["episodeKey"]]
        if self._entries:
            self._publish_queue()
        self.episodes.replace(visible_records)
        self._busy = False
        previous_seen = set(self._server_seen)
        queued = {row["searchKey"] for row in queued_records}
        self._server_seen.intersection_update(
            queued
            | {
                entry["episodeKey"]
                for entry in self._entries
                if entry["state"] not in _TERMINAL
            }
        )
        if self._watch_server:
            for row in queued_records:
                if row["searchKey"] not in self._server_seen:
                    self._server_seen.add(row["searchKey"])
                    self._enqueue(
                        row["searchKey"], False, origin="server", episode=row
                    )
        if self._server_seen != previous_seen:
            self._persist()
        self.stateChanged.emit()
        self._schedule_poll()

    @Slot(int)
    def selectEpisode(self, row):
        key = self.episodes.get(row).get("searchKey")
        if not key:
            return
        entry = next(
            (entry for entry in reversed(self._entries) if entry["episodeKey"] == key),
            None,
        )
        if entry:
            self.selectQueue(entry["id"], True)
        else:
            self._selected_queue = ""
            self._select_episode(key)
            self._publish_queue()
            self.queueSelected.emit(-1, False)
            self.logScopeChanged.emit()
            self.logChanged.emit()
            self._status = "Use + to add this episode to the queue"
            self.stateChanged.emit()

    @Slot(int, bool)
    def renderEpisode(self, row, test_render=False):
        key = self.episodes.get(row).get("searchKey")
        if key:
            self._enqueue(key, bool(test_render))

    def _enqueue(self, key, test_render, origin="manual", episode=None):
        if not self._ready or self._close_requested:
            return
        existing = next(
            (
                entry
                for entry in self._entries
                if entry["episodeKey"] == key and entry["state"] not in _TERMINAL
            ),
            None,
        )
        if existing:
            self.selectQueue(existing["id"])
            self._status = "Episode already queued"
            self.stateChanged.emit()
            return
        if len(self._entries) >= 200:
            self._error_message(
                ValueError("Queue history is full; clear completed entries")
            )
            return
        episode = episode or self.episodes.lookup("searchKey", key)
        entry = _queue_entry(key, episode, test_render, origin)
        self._entries.append(entry)
        for row, record in enumerate(self.episodes.records()):
            if record["searchKey"] == key:
                self._hidden_episodes[key] = (row, record)
                self.episodes.remove(row)
                break
        if not test_render:
            self._server_seen.add(key)
        self.selectQueue(entry["id"])
        self._discover_entry(entry)

    def _discover_entry(self, entry):
        config = dict(self._config)
        entry.update(state="discovering", stage="Loading shot list", error="")
        self._flush_queue()
        if self._discovery_entry is not None:
            return
        self._discovery_entry = entry
        status = config["queue_statuses"][-1] if (entry["origin"] == "manual") else ""
        self._submit(
            lambda: _discover_queue(
                self._api, entry["episodeKey"], config, entry["test"], status
            ),
            lambda records: self._discovery_finished(entry, records),
            lambda error: self._discovery_failed(entry, error),
        )

    def _discovery_finished(self, entry, records):
        try:
            if entry not in self._entries or entry["state"] == "cancelled":
                return
            jobs = [_shot_job(row, entry["test"]) for row in records]
            if not jobs:
                raise ValueError("No shots to render")
            entry.update(jobs=jobs, state="waiting", stage="Waiting")
            self._log(f"{entry['title']}: {len(jobs)} shots queued", entry)
            self._flush_queue()
            self._pump()
        except Exception as error:
            self._mark_discovery_failed(entry, error)
        finally:
            self._continue_discovery(entry)

    def _discovery_failed(self, entry, error):
        try:
            self._mark_discovery_failed(entry, error)
        finally:
            self._continue_discovery(entry)

    def _mark_discovery_failed(self, entry, error):
        if entry not in self._entries or entry["state"] == "cancelled":
            return
        entry.update(state="failed", stage="Discovery failed", error=str(error))
        self._error_message(error)
        self._flush_queue()
        self._pump()

    def _continue_discovery(self, entry):
        if self._discovery_entry is entry:
            self._discovery_entry = None
        pending = next(
            (row for row in self._entries if row["state"] == "discovering"),
            None,
        )
        if pending is not None and not self._close_requested:
            self._discover_entry(pending)

    # Queue execution

    @Slot()
    def startScheduler(self):
        if not self._ready or self._close_requested:
            return
        self._run_only = ""
        self._paused = False
        self._status = "Queue running"
        self._error = ""
        for entry in self._entries:
            if entry["state"] == "held" and entry.pop("restored", False):
                entry["state"] = "waiting"
        self.stateChanged.emit()
        self._publish_queue()
        self._pump()

    @Slot()
    def stopScheduler(self):
        self._paused = True
        self._status = "Pause after current shot" if self.running else "Queue paused"
        self.stateChanged.emit()

    @Slot()
    def toggleScheduler(self):
        self.startScheduler() if self._paused else self.stopScheduler()

    @Slot(str)
    def testQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None or "test" not in self._allowed_actions(entry, job):
            return
        jobs = deepcopy([job] if job else entry["jobs"])
        for test_job in jobs:
            self._reset_for_retry(test_job)
            test_job.update(
                start=1, end=1, frameSpec="1", frameRanges=[[1, 1]], attempt=1
            )
        test = _queue_entry(entry["episodeKey"], entry, True, "manual")
        test.update(
            title=f"{entry['title']} · тест",
            state="waiting",
            stage="Тестовый рендер",
            jobs=jobs,
        )
        self._entries.append(test)
        self._flush_queue()
        self.selectQueue(test["id"])
        self._pump()

    @Slot(str)
    def runOnly(self, identity):
        entry, job = self._find(identity)
        if entry is None or "only" not in self._allowed_actions(entry, job):
            return
        self.stopScheduler()
        self._run_only = ""
        self._active_entry = None
        self.retryQueue(identity)
        row = job or entry
        if job and job["state"] == "skipped":
            self.toggleIncluded(job["id"])
        for target in [job] if job else entry["jobs"]:
            if target["state"] == "held":
                self.holdQueue(target["id"])
        if entry["state"] == "held":
            self.holdQueue(entry["id"])
        if entry["state"] in _TERMINAL:
            entry.update(state="waiting", stage="Waiting", prepared=False, error="")
        self._run_only = row["id"]
        self._paused = False
        self._status = f"Запуск только: {row['title']}"
        self._error = ""
        self.selectQueue(row["id"])
        self.stateChanged.emit()
        self._pump()

    @Slot(bool)
    def watchServer(self, enabled):
        self._watch_server = bool(enabled)
        self.stateChanged.emit()
        if enabled:
            self.refresh()
        else:
            self._poll_timer.stop()

    def _pause_finished_run_only(self, entry, job) -> bool:
        if not self._run_only:
            return False
        unfinished = (
            entry is not None
            and entry["state"] not in _TERMINAL | {"held"}
            and (job is None or job["state"] not in _TERMINAL | {"held"})
        )
        if unfinished:
            return False
        self._run_only = ""
        if entry is not None and job is not None:
            entry["prepared"] = False
        self._active_entry = None
        self._paused = True
        self._status = "Selected work finished · queue paused"
        self._flush_queue()
        self.stateChanged.emit()
        return True

    def _start_episode_preparation(self, entry, single_shot: bool) -> None:
        entry.update(state="preparing", stage="Synchronizing episode")
        config = dict(self._config)
        saved = deepcopy(entry)
        saved["singleShot"] = single_shot
        self._run_stage(
            lambda: _prepare_episode(self._api, saved, config, self._cancel),
            self._episode_prepared,
        )

    def _start_shot_preparation(self, entry, job) -> None:
        self._active_job = job
        job.update(state="preparing", stage="Preparing shot", error="")
        entry.update(
            state="preparing",
            stage=f"Подготовка: {job['title']}",
        )
        config = dict(self._config)
        saved_entry = deepcopy(entry)
        saved_job = deepcopy(job)
        self._run_stage(
            lambda: _prepare_shot(
                self._api, saved_entry, saved_job, config, self._cancel
            ),
            self._shot_prepared,
        )

    def _next_entry(self, preferred):
        entry = preferred or next(
            (row for row in self._entries if row["state"] == "waiting"), None
        )
        if entry is None:
            self._show_idle_status()
            return None
        self._active_entry = entry
        self._cancel = threading.Event()
        self._cancel_job_only = False
        return entry

    def _show_idle_status(self):
        states = {entry["state"] for entry in self._entries}
        if "discovering" in states:
            self._status = "Loading queued shots"
        elif "held" in states:
            self._status = "Waiting · held jobs remain"
        elif self._watch_server:
            self._status = "Waiting for jobs"
        else:
            self._status = "Queue finished"
        self.stateChanged.emit()

    def _finish_or_hold_entry(self, entry):
        if any(job["state"] == "held" for job in entry["jobs"]):
            entry.update(state="held", stage="Contains held shots")
            self._active_entry = None
            self._flush_queue()
            self._pump()
            return
        self._finish_entry()

    def _run_scope(self):
        if not self._run_only:
            return None, None
        return self._find(self._run_only)

    @staticmethod
    def _entry_finished(entry):
        return (
            entry is not None
            and bool(entry["jobs"])
            and all(job["state"] in _TERMINAL for job in entry["jobs"])
        )

    @staticmethod
    def _next_job(entry, preferred):
        if preferred is not None:
            return preferred
        return next((job for job in entry["jobs"] if job["state"] == "waiting"), None)

    def _pump(self):
        if self._stage_operation is not None:
            return
        scope_entry, scope_job = self._run_scope()
        if self._pause_finished_run_only(scope_entry, scope_job):
            return

        entry = self._active_entry
        # Pausing prevents the next shot, not finalizing work already finished.
        if self._entry_finished(entry):
            self._finish_entry()
            return
        if entry is not None and entry["state"] == "held":
            self._active_entry = entry = None
        if self._paused or self._close_requested:
            return
        if entry is None:
            entry = self._next_entry(scope_entry)
            if entry is None:
                return
        if not entry["jobs"]:
            self._active_entry = None
            self._discover_entry(entry)
            return
        pending = self._next_job(entry, scope_job)
        if pending is None:
            self._finish_or_hold_entry(entry)
            return
        if not entry["prepared"]:
            self._start_episode_preparation(entry, scope_job is not None)
            return
        self._start_shot_preparation(entry, pending)

    def _run_stage(self, function, done):
        self._last_tick = time.monotonic()
        self._flush_queue()

        def execute():
            try:
                return function()
            except InterruptedError as cancellation:
                return cancellation

        def completed(value):
            self._tick()
            self._stage_operation = None
            try:
                if isinstance(value, InterruptedError):
                    self._stage_failed(value)
                else:
                    done(value)
            except Exception as error:
                self._stage_failed(error)
            self.stateChanged.emit()
            self._maybe_close()

        def failed(error):
            self._tick()
            self._stage_operation = None
            self._stage_failed(error)
            self._maybe_close()

        self._stage_operation = self._submit(
            execute, completed, failed, self._stage_progress
        )
        self.stateChanged.emit()

    def _stage_progress(self, payload):
        entry, job = self._active_entry, self._active_job
        if entry is None:
            return
        row = job or entry
        preparation_error = payload.get("preparationError")
        if preparation_error:
            row.setdefault("preparationErrors", []).append(preparation_error)
        if "stage" in payload and not self._cancel.is_set():
            row["stage"] = _ui_text(payload["stage"]) + (
                " · " + payload["detail"] if payload.get("detail") else ""
            )
        if job is not None:
            self._update_job_progress(job, payload)
        if payload.get("text"):
            if job is not None:
                job["lastOutput"] = time.time()
            self._log(payload["text"], entry, job)
        if payload.get("file"):
            self._show_transfer_progress(row, payload)
        self._publish_queue()

    def _update_job_progress(self, job, payload):
        for key in (
            "pid", "frame", "framesDone", "progress",
            "renderOutput", "renderFiles",
        ):
            if key in payload:
                job[key] = payload[key]
        if "elapsed" in payload:
            job["renderElapsed"] = payload["elapsed"]
        if payload.get("renderError"):
            job.update(
                state="stopping",
                stage="Render failed · stopping process",
                error=payload["renderError"],
            )
            return
        if job["state"] == "paused":
            if payload.get("pauseState") == "paused":
                job["stage"] = "Render paused"
            return
        if job["state"] != "rendering" or self._cancel.is_set():
            return
        last_output = job.get("lastOutput", job.get("started", time.time()))
        silence = max(0, int(time.time() - last_output))
        phase = (
            "Рендеринг шота"
            if job.get("frame") not in (None, "")
            else "Рендер запущен · Maya работает"
        )
        job["stage"] = (
            f"{phase} · PID {job.get('pid') or 'запуск'} · ожидание вывода {silence} с"
        )

    def _show_transfer_progress(self, row, payload):
        row["stage"] = f"Загрузка: {Path(payload['file']).name}"
        total = payload.get("bytes_total", 0)
        if total:
            row["stage"] += f" · {payload.get('bytes_done', 0) / total:.0%}"

    def _episode_prepared(self, payload):
        entry = self._active_entry
        errors = entry.setdefault("preparationErrors", [])
        for error in payload.get("preparationErrors") or []:
            if error not in errors:
                errors.append(error)
        entry["prepared"] = True
        entry.update(state="waiting", stage="Ready to render")
        if self._cancel.is_set():
            self._after_cancel()
        else:
            self._publish_queue()
            self._pump()

    def _shot_prepared(self, payload):
        job = self._active_job
        job.update(payload)
        if self._cancel.is_set():
            job.update(state="cancelled", stage="Cancelled")
            self._active_job = None
            self._after_cancel()
            return
        # Pause requested during download/preparation must also prevent launch.
        if self._paused:
            job.update(state="waiting", stage="Ready · queue paused")
            self._active_job = None
            self._flush_queue()
            return
        self._render_pause.clear()
        job.update(state="rendering", stage="Rendering shot", started=time.time())
        self._active_entry.update(state="rendering", stage=job["title"])
        self._log(job["command"], self._active_entry, job)
        saved = deepcopy(job)
        self._run_stage(
            lambda: _render_native(
                saved,
                int(self._config.get("render_timeout_minutes", 0)),
                self._cancel,
                self._render_pause,
            ),
            self._render_done,
        )

    def _render_done(self, result):
        entry, job = self._active_entry, self._active_job
        self._render_pause.clear()
        error = result.get("error", "")
        if result["cancelled"]:
            state = "cancelled"
        elif result["exitCode"] == 0 and not result["timedOut"] and not error:
            state = "completed"
        else:
            state = "failed"

        if result["timedOut"]:
            error = "Render timeout"
        elif state == "failed" and not error:
            error = f"Render exited with code {result['exitCode']}"
        job.update(
            result=state,
            exitCode=result["exitCode"],
            renderElapsed=result["elapsed"],
            pid="",
            finished=time.time(),
            error=error,
        )
        if state == "completed":
            job.update(progress=1.0, framesDone=_job_frame_count(job))
        self._log(f"{job['title']}: {state}, exit {job['exitCode']}", entry, job)
        if entry["test"]:
            self._shot_saved(None)
            return
        job.update(state="saving", stage="Saving result and render log")
        entry.update(state="saving", stage=job["stage"])
        config, saved, rendered = dict(self._config), deepcopy(entry), deepcopy(job)
        self._run_stage(
            lambda: _finalize_shot(self._api, saved, rendered, config),
            self._shot_saved,
        )

    def _shot_saved(self, log_path):
        entry, job = self._active_entry, self._active_job
        if log_path:
            job["logPath"] = log_path
        job.update(state=job["result"], stage=job["result"].capitalize())
        entry.update(state="waiting", stage="Waiting for next shot")
        self._active_job = None
        if job["state"] == "failed" and self._config.get("stop_on_error"):
            self._paused = True
        self._flush_queue()
        if self._cancel.is_set():
            self._after_cancel()
        else:
            self._pump()

    def _stage_failed(self, error):
        entry, job = self._active_entry, self._active_job
        if entry is None:
            self._error_message(error)
            return
        cancelled = isinstance(error, InterruptedError) or self._cancel.is_set()
        if not cancelled:
            self._error_message(error)
        if job is None and self._run_only:
            _scope_entry, job = self._find(self._run_only)
        if job is not None:
            self._fail_job(entry, job, error, cancelled)
        else:
            self._fail_episode(entry, error, cancelled)

    def _fail_job(self, entry, job, error, cancelled):
        saving = job["state"] == "saving"
        error_text = str(error)
        job.update(
            state="cancelled" if cancelled else "failed",
            stage="Cancelled" if cancelled else "Failed",
            error=error_text,
            pid="",
            saveFailed=saving,
        )
        if saving:
            # A write may have reached TACTIC. Never automatically retry it.
            self._paused = True
            self._active_job = None
            entry.update(state="waiting", stage="Waiting for next shot")
        if cancelled:
            self._active_job = None
            entry.update(state="waiting", stage="Waiting for next shot")
            self._after_cancel()
            return
        if saving:
            self._flush_queue()
            self._pump()
            return
        preparation_errors = list(job.get("preparationErrors") or [])
        if error_text not in preparation_errors:
            preparation_errors.append(error_text)
        job.update(
            result="failed",
            state="saving",
            stage="Saving preparation error",
            preparationErrors=preparation_errors,
        )
        self._active_job = job
        entry.update(state="saving", stage=job["stage"])
        if entry["test"]:
            self._shot_saved(None)
            return
        config, saved, failed_job = dict(self._config), deepcopy(entry), deepcopy(job)
        self._run_stage(
            lambda: _finalize_shot(self._api, saved, failed_job, config),
            self._shot_saved,
        )

    def _fail_episode(self, entry, error, cancelled):
        entry["error"] = str(error)
        state = "cancelled" if cancelled else "failed"
        stage = "Cancelled" if cancelled else "Episode preparation failed"
        for job in entry["jobs"]:
            if job["state"] not in _TERMINAL:
                job.update(state=state, stage=stage)
                if not cancelled:
                    job["error"] = str(error)
        if not cancelled:
            errors = entry.setdefault("preparationErrors", [])
            if str(error) not in errors:
                errors.append(str(error))
        if not cancelled and self._config.get("stop_on_error"):
            self._paused = True
        self._finish_entry()

    def _finish_entry(self):
        entry = self._active_entry
        states = {job["state"] for job in entry["jobs"]}
        if "failed" in states:
            result = "failed"
        elif "cancelled" in states:
            result = "cancelled"
        else:
            result = "completed"
        entry["result"] = result
        if entry["test"]:
            self._entry_saved(None)
            return

        entry.update(state="saving", stage="Saving episode status")
        key = entry["episodeKey"]
        status_key = "complete_status" if result == "completed" else "failed_status"
        status = self._config[status_key]
        process = self._config["render_process"]
        saved, config = deepcopy(entry), dict(self._config)

        def save_episode():
            episode = self._api.sobject(key)
            _set_episode_task_status(episode, process, status)
            return _finalize_preparation_log(self._api, saved, config)

        self._flush_queue()
        self._stage_operation = self._submit(
            save_episode,
            self._entry_saved,
            lambda error: self._entry_save_failed(entry, error),
        )

    def _entry_save_failed(self, entry, error):
        self._stage_operation = None
        if self._pending_removal == entry["id"]:
            self._pending_removal = ""
        entry.update(
            state="failed",
            stage="Could not save episode status",
            error=str(error),
            saveFailed=True,
        )
        self._paused = True
        self._error_message(error)
        self._active_entry = None
        self._flush_queue()
        self._maybe_close()

    def _entry_saved(self, log_path):
        self._stage_operation = None
        entry = self._active_entry
        if log_path:
            entry["logPath"] = log_path
        entry.update(
            state=entry["result"],
            stage=entry["result"].capitalize(),
            finished=time.time(),
        )
        self._log(f"Episode {entry['title']}: {entry['state']}", entry)
        self._active_entry = None
        if self._pending_removal == entry["id"]:
            self._pending_removal = ""
            self._remove_entries([entry])
        elif self._auto_clear_finished and entry["state"] in {"completed", "cancelled"}:
            self._remove_entries([entry])
        else:
            self._flush_queue()
        self.stateChanged.emit()
        self.refresh()
        self._pump()
        self._maybe_close()

    def _cancel_remainder(self):
        entry = self._active_entry
        if entry is None:
            return
        for job in entry["jobs"]:
            if job["state"] not in _TERMINAL:
                job.update(state="cancelled", stage="Cancelled", pid="")
        self._active_job = None
        self._finish_entry()

    def _after_cancel(self):
        if self._cancel_job_only:
            self._cancel_job_only = False
            self._cancel = threading.Event()
            self._flush_queue()
            self._pump()
        else:
            self._cancel_remainder()

    # Queue commands

    @Slot(str)
    def cancelQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return
        if entry is self._active_entry and (
            job is None or job is self._active_job or job["id"] == self._run_only
        ):
            self._render_pause.clear()
            self._cancel_job_only = job is not None
            self._cancel.set()
            entry.update(stage="Stopping · waiting for active operation")
            if self._active_job:
                self._active_job["stage"] = (
                    "Stopping renderer / finishing current transfer"
                )
            elif job:
                job.update(state="cancelled", stage="Cancelled")
            if self._stage_operation is None:
                self._cancel_remainder()
        else:
            for row in [job] if job else [entry, *entry["jobs"]]:
                if row["state"] not in _TERMINAL:
                    row.update(state="cancelled", stage="Cancelled")
        self._flush_queue()

    @Slot()
    def interruptRender(self):
        self._paused = True
        self._render_pause.clear()
        self._run_only = ""
        self._status = "Stopping queue" if self._active_entry else "Queue stopped"
        if self._active_entry:
            self.cancelQueue(self._active_entry["id"])
        else:
            self.stateChanged.emit()

    @Slot(str)
    def retryQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None or entry["state"] in _ACTIVE:
            return
        if entry is self._active_entry and self._stage_operation is not None:
            return
        if entry.get("saveFailed") or any(
            row.get("saveFailed") for row in ([job] if job else entry["jobs"])
        ):
            self._error_message(
                ValueError(
                    "Server save was not confirmed. Check TACTIC before rerendering; add a new run explicitly."
                )
            )
            return
        if not entry["jobs"]:
            self._discover_entry(entry)
            return
        targets = [
            row
            for row in ([job] if job else entry["jobs"])
            if row["state"] in {"failed", "cancelled"}
        ]
        if not targets:
            return
        for row in targets:
            self._reset_for_retry(row)
        entry.update(
            state="waiting",
            stage="Retry queued",
            prepared=False,
            error="",
            logPath="",
            preparationErrors=[],
        )
        self.selectQueue(entry["id"])
        self._persist()
        self._pump()

    @staticmethod
    def _reset_for_retry(job):
        job.update(
            id=uuid.uuid4().hex,  # Keep the previous attempt's log file.
            state="waiting",
            stage="Waiting",
            progress=0.0,
            error="",
            frame="",
            framesDone=0,
            renderElapsed=0.0,
            pid="",
            logPath="",
            renderOutput="",
            renderFiles=[],
            preparationErrors=[],
            command="",
            exitCode="",
            attempt=job.get("attempt", 1) + 1,
        )

    @Slot(str)
    def holdQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return
        active_job = self._active_job
        if (
            entry is self._active_entry
            and active_job is not None
            and (job is None or job is active_job)
            and active_job["state"] in {"rendering", "paused"}
        ):
            paused = not self._render_pause.is_set()
            state = "paused" if paused else "rendering"
            stage = "Render pause requested" if paused else "Resuming render"
            if paused:
                self._render_pause.set()
                self._status = f"Рендер на паузе: {active_job['title']}"
            else:
                self._render_pause.clear()
                self._status = (
                    "Pause after current shot" if self._paused else "Queue running"
                )
            active_job.update(state=state, stage=stage)
            entry.update(state=state, stage=stage)
            self._flush_queue()
            self.stateChanged.emit()
            return
        row = job or entry
        if row["state"] not in {"waiting", "held"}:
            return
        row["state"] = "waiting" if row["state"] == "held" else "held"
        row["stage"] = row["state"].capitalize()
        if job is not None and entry["state"] == "held" and row["state"] == "waiting":
            entry.update(state="waiting", stage="Waiting")
        self._flush_queue()
        self._pump()

    @Slot(str, int)
    def moveQueue(self, identity, delta):
        movable = self._movable_queue_row(identity)
        if movable is None:
            return
        values, row = movable
        index = values.index(row)
        destination = max(0, min(len(values) - 1, index + delta))
        values.insert(destination, values.pop(index))
        self._flush_queue()

    @Slot(str, str)
    def moveQueueTo(self, identity, target_identity):
        movable = self._movable_queue_row(identity)
        _target_entry, target_job = self._find(target_identity)
        if movable is None:
            return
        values, row = movable
        target = _target_entry if values is self._entries else target_job
        if target not in values or target is row:
            return
        destination = values.index(target)
        values.insert(destination, values.pop(values.index(row)))
        self._flush_queue()

    def _movable_queue_row(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return None
        row = job or entry
        if "move" not in self._allowed_actions(entry, job):
            return None
        return (entry["jobs"] if job else self._entries), row

    def _remove_entries(self, entries):
        if not entries:
            return
        identities = {
            identity
            for entry in entries
            for identity in [entry["id"], *(job["id"] for job in entry["jobs"])]
        }
        discarded = {id(entry) for entry in entries}
        removed_ids = {entry["id"] for entry in entries}
        if self._pending_removal in removed_ids:
            self._pending_removal = ""
        self._entries = [entry for entry in self._entries if id(entry) not in discarded]
        queued_keys = {entry["episodeKey"] for entry in self._entries}
        restored = self.episodes.records()
        restored_rows = []
        for entry in entries:
            key = entry["episodeKey"]
            if key in queued_keys:
                continue
            hidden = self._hidden_episodes.pop(key, None)
            if hidden:
                row, episode = hidden
                episode.update(selected=False, queued=False)
                restored_rows.append((row, episode))
        for row, episode in sorted(restored_rows):
            restored.insert(min(row, len(restored)), episode)
        self.episodes.replace(restored)
        self._events = [event for event in self._events if event[0] not in identities]
        if self._selected_queue in identities:
            self._selected_queue = ""
            self.logScopeChanged.emit()
            self.logChanged.emit()
        self._flush_queue()

    @Slot()
    def clearCompleted(self):
        self._remove_entries(
            [
                entry
                for entry in self._entries
                if entry["state"] in {"completed", "cancelled"}
            ]
        )

    @Slot(str, result=bool)
    def removeEpisode(self, identity):
        entry, job = self._find(identity)
        if (
            entry is None
            or job is not None
            or "remove" not in self._allowed_actions(entry)
        ):
            return False
        if entry is self._active_entry:
            self._pending_removal = entry["id"]
            self.cancelQueue(entry["id"])
            self._status = f"Остановка и удаление: {entry['title']}"
            self.stateChanged.emit()
            return True
        self._remove_entries([entry])
        self._status = f"Удалено из очереди: {entry['title']}"
        self.stateChanged.emit()
        self._pump()
        return True

    @Slot(str)
    def selectQueue(self, identity, align_top=False):
        self._selected_queue = identity
        entry, _job = self._find(identity)
        self._select_episode(entry["episodeKey"] if entry else "")
        self._publish_queue()
        self.queueSelected.emit(
            next(
                (
                    index
                    for index, row in enumerate(self.queue.records())
                    if row["jobId"] == identity
                ),
                -1,
            ),
            align_top,
        )
        self.logScopeChanged.emit()
        self.logChanged.emit()

    def _select_episode(self, key):
        self._selected_episode = key
        episode_index = -1
        for index, row in enumerate(self.episodes.records()):
            selected = row["searchKey"] == key
            self.episodes.set_value(index, "selected", selected)
            if selected:
                episode_index = index
        self.episodeSelected.emit(episode_index)

    @Slot(str)
    def toggleExpanded(self, identity):
        entry, job = self._find(identity)
        if entry is not None and job is None:
            entry["expanded"] = not entry["expanded"]
            self._publish_queue()

    @Slot(str)
    def toggleIncluded(self, identity):
        entry, job = self._find(identity)
        if entry is None or "include" not in self._allowed_actions(entry, job):
            return
        state = "waiting" if job["state"] == "skipped" else "skipped"
        job.update(state=state, stage="Waiting" if state == "waiting" else "Excluded")
        if state == "waiting" and entry["state"] in _TERMINAL:
            entry.update(state="waiting", stage="Waiting", prepared=False, error="")
        self._flush_queue()
        self._pump()

    @Slot(str, str, result=bool)
    def setFrameSpec(self, identity, value):
        entry, job = self._find(identity)
        if entry is None or "frames" not in self._allowed_actions(entry, job):
            return False
        try:
            ranges = _parse_frame_spec(value, job["start"], job["end"])
        except ValueError as error:
            self._error_message(error)
            return False
        job["frameRanges"] = [list(pair) for pair in ranges]
        job["frameSpec"] = value.strip()
        self._error = ""
        self._flush_queue()
        self.stateChanged.emit()
        return True

    # Queue presentation

    def _job_fraction(self, job):
        if job["state"] == "skipped":
            return 0.0
        return 1.0 if job["state"] == "completed" else job.get("progress", 0.0)

    def _job_eta(self, job, frame_seconds=None):
        if job["state"] in _TERMINAL:
            return 0
        progress = job.get("progress", 0)
        if job["state"] in {"rendering", "paused"} and progress > 0:
            return job.get("renderElapsed", 0) * (1 - progress) / progress
        if frame_seconds is None:
            return None
        return frame_seconds * _job_frame_count(job) * (1 - progress)

    def _frame_seconds(self):
        # ponytail: recent mean estimates render time only, not downloads or
        # per-scene complexity; replace with scene-specific samples if needed.
        samples = [
            row["renderElapsed"] / _job_frame_count(row)
            for entry in self._entries
            for row in entry["jobs"]
            if row["state"] == "completed" and row.get("renderElapsed", 0) > 0
        ]
        if not samples:
            return None
        return sum(samples[-20:]) / len(samples[-20:])

    def _episode_record(self, entry, frame_seconds):
        jobs = entry["jobs"]
        included = [job for job in jobs if job["state"] != "skipped"]
        total = sum(_job_frame_count(job) for job in included)
        done = sum(self._job_fraction(job) * _job_frame_count(job) for job in included)
        estimates = [self._job_eta(job, frame_seconds) for job in jobs]
        eta = _total_eta(estimates)
        return {
            "jobId": entry["id"],
            "parentId": "",
            "title": entry["title"],
            "previewUrl": entry.get("previewUrl", ""),
            "subtitle": (
                f"{len(jobs)} шотов · завершено "
                f"{sum(job['state'] == 'completed' for job in jobs)}"
            ),
            "state": entry["state"],
            "stage": _ui_text(entry["stage"]),
            "selected": entry["id"] == self._selected_queue,
            "expanded": entry["expanded"],
            "progress": done / total if total else 0,
            "frames": f"{int(done)}/{total}",
            "elapsed": _duration(entry["elapsed"]),
            "eta": "~" + _duration(eta) if eta is not None else "—",
            "depth": 0,
            "test": entry["test"],
            "attempt": 0,
            "pid": "",
            "included": False,
            "actions": self._allowed_actions(entry),
            "error": entry["error"],
            "indeterminate": entry["state"] in {"discovering", "preparing", "saving"},
        }

    def _shot_record(self, entry, job, frame_seconds):
        eta = self._job_eta(job, frame_seconds)
        default_spec = _format_frame_ranges([(job["start"], job["end"])])
        frame_spec = job.get("frameSpec") or default_spec
        frame_label = "Кадры: " if frame_spec != default_spec else ""
        return {
            "jobId": job["id"],
            "parentId": entry["id"],
            "title": job["title"],
            "previewUrl": job.get("previewUrl", ""),
            "subtitle": f"{frame_label}{frame_spec} · попытка {job['attempt']}",
            "state": job["state"],
            "stage": _ui_text(job["stage"]),
            "selected": job["id"] == self._selected_queue,
            "expanded": False,
            "progress": self._job_fraction(job),
            "frames": f"{job.get('framesDone', 0)}/{_job_frame_count(job)}",
            "frameSpec": frame_spec,
            "elapsed": _duration(job["elapsed"]),
            "eta": "~" + _duration(eta) if eta is not None else "—",
            "depth": 1,
            "test": entry["test"],
            "attempt": job["attempt"],
            "included": job["state"] != "skipped",
            "actions": self._allowed_actions(entry, job),
            "pid": job.get("pid", ""),
            "error": job["error"],
            "indeterminate": job["state"] in {"preparing", "saving"}
            or (job["state"] == "rendering" and not job.get("progress")),
        }

    def _publish_queue(self):
        records = []
        frame_seconds = self._frame_seconds()
        for entry in self._entries:
            records.append(self._episode_record(entry, frame_seconds))
            if entry["expanded"]:
                records.extend(
                    self._shot_record(entry, job, frame_seconds)
                    for job in entry["jobs"]
                )
        self.queue.replace(records)
        queued = {
            entry["episodeKey"]
            for entry in self._entries
            if entry["state"] not in _TERMINAL
        }
        for index, episode in enumerate(self.episodes.records()):
            value = episode["searchKey"] in queued
            if episode.get("queued") != value:
                self.episodes.set_value(index, "queued", value)
        self.queueChanged.emit()

    def _tick(self):
        now = time.monotonic()
        delta, self._last_tick = now - self._last_tick, now
        if self._stage_operation is not None and self._active_entry:
            self._active_entry["elapsed"] += delta
            if self._active_job:
                self._active_job["elapsed"] += delta
            self._publish_queue()

    @Slot(int, str)
    def setEpisodeStatus(self, row, status):
        key = self.episodes.get(row).get("searchKey")
        if key:
            process = self._config["render_process"]
            self._submit(
                lambda: _set_episode_task_status(
                    self._api.sobject(key), process, status
                ),
                lambda _value: self.refresh(),
            )

    # Settings and window lifecycle

    def _resolved_window_state(self, values):
        state = {**self._window_state, **(values or {})}
        state["width"] = max(950, int(state["width"]))
        state["height"] = max(650, int(state["height"]))
        saved_statuses = state.get("episodeStatuses")
        if not isinstance(saved_statuses, (list, tuple)):
            saved_statuses = self.visibleEpisodeStatuses
        selected_statuses = {
            status for status in saved_statuses if isinstance(status, str)
        }
        screens, primary = current_screens()
        geometry = resolve_window_state(state, screens, primary)
        geometry.update(
            episodeWidth=max(250, int(state.get("episodeWidth", 350))),
            detailHeight=max(120, int(state.get("detailHeight", 235))),
            logPanelVisible=bool(state.get("logPanelVisible", True)),
            detailPage=(
                state.get("detailPage")
                if state.get("detailPage") in {"log", "preview", "details"}
                else "log"
            ),
            followLog=bool(state.get("followLog", True)),
            freezeLog=bool(state.get("freezeLog", False)),
            episodeStatuses=[
                status
                for status in _episode_filter_statuses(self._config)
                if status in selected_statuses
            ],
        )
        return geometry

    @Slot("QVariantMap")
    def saveWindowState(self, values):
        values = dict(values or {})
        maximized = bool(values.get("maximized", False))
        state = dict(self._window_state)
        if not maximized:
            state.update(values)
        for key in (
            "episodeWidth",
            "detailHeight",
            "logPanelVisible",
            "detailPage",
            "followLog",
            "freezeLog",
            "episodeStatuses",
        ):
            if key in values:
                state[key] = values[key]
        state["maximized"] = maximized
        screen = screen_for_window_rect(
            int(state["x"]),
            int(state["y"]),
            int(state["width"]),
            int(state["height"]),
        )
        if screen:
            state.update(
                screen_identity=screen.identity,
                screen_name=screen.name,
                screen_x=screen.x,
                screen_y=screen.y,
                screen_width=screen.width,
                screen_height=screen.height,
            )
        self._window_state = self._resolved_window_state(state)
        if self._offline:
            return
        from thlib.environment import env_write_config

        self._submit(
            lambda: env_write_config(
                self._window_state,
                filename="ui_batch_dispatcher_window",
                unique_id=self._project_code,
                long_abs_path=True,
            ),
            lambda _value: None,
        )

    @Slot(str, str, str, bool, int, str, bool, int, bool, int, bool)
    def saveSettings(
        self,
        maya_path,
        save_path,
        camera,
        stop_on_error,
        timeout,
        log_checkin,
        skip_dependency_errors,
        update_interval,
        web_enabled,
        web_port,
        web_security,
    ):
        if self.running:
            self._error_message(
                ValueError(
                    "Pause the queue and wait for the current shot before changing render settings"
                )
            )
            return
        values = {
            "maya_render_executable": maya_path.strip(),
            "output_directory": save_path.strip(),
            "camera": camera.strip(),
            "stop_on_error": bool(stop_on_error),
            "render_timeout_minutes": max(0, timeout),
            "log_checkin": str(log_checkin),
            "skip_dependency_errors": bool(skip_dependency_errors),
            "update_interval": max(5, int(update_interval)),
            "web_enabled": bool(web_enabled),
            "web_port": int(web_port),
            "web_security": bool(web_security),
        }
        if not values["maya_render_executable"] or not values["output_directory"]:
            self._error_message(
                ValueError("Render executable and output directory are required")
            )
            return
        if values["log_checkin"] not in {"always", "failed", "never"}:
            self._error_message(ValueError("Неизвестный режим чек-ина лога"))
            return
        if not 1 <= values["web_port"] <= 65535:
            self._error_message(
                ValueError("Порт веб-диспетчера должен быть от 1 до 65535")
            )
            return
        from thlib.environment import env_write_config

        self._submit(
            lambda: env_write_config(
                values,
                filename="ui_batch_dispatcher",
                unique_id=self._project_code,
                long_abs_path=True,
            ),
            lambda _value: self._settings_saved(values),
        )

    @Slot("QVariantMap")
    def setWebTheme(self, values):
        self._web_theme = dict(values or {})

    def _settings_saved(self, values):
        restart_web = any(
            values[key] != self._config.get(key)
            for key in ("web_enabled", "web_port", "web_security")
        )
        restart_poll = values["update_interval"] != self._config.get(
            "update_interval"
        )
        self._config.update(values)
        if restart_web:
            self._restart_web_server()
        if restart_poll:
            self._schedule_poll()
        self.settingsChanged.emit()

    @Slot(str)
    def openPath(self, path):
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    @Slot()
    def openSelectedLog(self):
        detail = self.selectedDetail
        if detail.get("logPath"):
            self.openPath(detail["logPath"])
            return
        self._status = (
            "Render log is available after the shot starts"
            if detail.get("child")
            else "Select a shot to open its render log"
        )
        self.stateChanged.emit()

    @Slot(QUrl, result=str)
    def localPath(self, url):
        return url.toLocalFile()

    @Slot()
    def showDestination(self):
        self.openPath(self._config["output_directory"])

    @Slot()
    def openWeb(self):
        if self.webUrl:
            QDesktopServices.openUrl(QUrl(self.webUrl))

    @Slot()
    def copyWebUrl(self):
        if not self.webUrl:
            return
        QGuiApplication.clipboard().setText(self.webUrl)
        self._status = "LAN-ссылка скопирована"
        self.stateChanged.emit()

    @Slot(str)
    def showQueueDestination(self, identity):
        entry, job = self._find(identity)
        if entry is self._active_entry and self._active_job is not None:
            job = self._active_job
        elif entry is not None and job is None:
            job = next(
                (row for row in reversed(entry["jobs"]) if row.get("renderOutput")),
                None,
            )
        self.openPath(
            (job or {}).get("renderOutput")
            or (job or {}).get("output")
            or self._config["output_directory"]
        )

    def attach_window(self, window) -> None:
        self._window = window
        self._create_tray()
        self._restart_web_server()

    def _restart_web_server(self):
        if self._web_server:
            self._web_server.stop()
            self._web_server = None
        self._web_error = ""
        if not self._config.get("web_enabled", True):
            self.webChanged.emit()
            return
        try:
            port = int(self._config.get("web_port", 92))
            self._web_server = BatchWebServer(
                self._web_dispatch,
                port=port,
                require_token=self._config.get("web_security", False),
            )
            self._web_server.start()
        except OSError as error:
            self._web_server = None
            self._web_error = f"Не удалось запустить веб-диспетчер: {error}"
        self.webChanged.emit()

    def _create_tray(self) -> None:
        try:
            from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

            if not isinstance(QApplication.instance(), QApplication):
                return
            tray = QSystemTrayIcon(QGuiApplication.windowIcon(), self)
            menu = QMenu()
            start = QAction("Start Scheduler", menu)
            stop = QAction("Stop Scheduler", menu)
            show = QAction("Show Dispatcher", menu)
            hide = QAction("Hide Dispatcher", menu)
            close = QAction("Exit", menu)
            start.triggered.connect(self.startScheduler)
            stop.triggered.connect(self.stopScheduler)
            show.triggered.connect(self.showWindow)
            hide.triggered.connect(self.hideWindow)
            close.triggered.connect(self.closeWindow)
            menu.addActions((start, stop))
            menu.addSeparator()
            menu.addActions((show, hide))
            menu.addSeparator()
            menu.addAction(close)
            tray.setContextMenu(menu)
            tray.activated.connect(
                lambda reason: (
                    self.showWindow()
                    if reason
                    in {
                        QSystemTrayIcon.ActivationReason.Trigger,
                        QSystemTrayIcon.ActivationReason.DoubleClick,
                    }
                    else None
                )
            )
            tray.show()
            self._tray = tray
            self._tray_menu = menu
        except (ImportError, RuntimeError):
            self._tray = None

    @Slot()
    def showWindow(self) -> None:
        if self._window:
            self._window.show()
            self._window.requestActivate()

    @Slot()
    def hideWindow(self) -> None:
        if self._window:
            self._window.hide()

    @Slot()
    def closeWindow(self):
        self._close_requested = True
        self._paused = True
        self._watch_server = False
        self._poll_timer.stop()
        if self._active_entry:
            self.interruptRender()
        self.stateChanged.emit()
        self._maybe_close()

    def _maybe_close(self):
        if (
            not self._close_requested
            or self._stage_operation is not None
            or self._saving
        ):
            return
        # Discovery may still carry an authorized status write. Wait for its
        # completion, then persist before disposing the QObject.
        if self._operations:
            return
        self.shutdown()
        self.windowCloseRequested.emit()

    def shutdown(self):
        if self._closing:
            return
        self._closing = True
        self._cancel.set()
        if self._web_server:
            self._web_server.stop()
            self._web_server = None
            self.webChanged.emit()
        self._poll_timer.stop()
        self._clock.stop()
        for operation, subscriptions in self._operations.values():
            operation.cancel()
            for subscription in subscriptions:
                subscription.close()
        self._operations.clear()
        if self._tray:
            self._tray.hide()


