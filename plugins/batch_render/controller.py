"""Batch presentation state and worker coordination."""
from __future__ import annotations

import threading
import json
import time
import traceback
from concurrent.futures import Future
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Property, QObject, Qt, QTimer, QUrl, Signal, Slot
from tactic_handler_api.operations import Operation
from thlib.ui.workspace_models.records import RecordListModel
from .domain import (
    BATCH_DISPATCHER_CONFIG,
    _duration,
    _episode_filter_statuses,
    _format_frame_ranges,
    _job_frame_count,
    _job_ranges,
    _total_eta,
)
from .queue_state import _TERMINAL, _ACTIVE, _IDLE, _RETRYABLE, _RUNNABLE


from .web_control import WebControlMixin
from .settings import SettingsMixin
from .execution import ExecutionMixin
from .queue_actions import QueueActionsMixin
from .catalog_controller import CatalogControllerMixin


class BatchDispatcherController(WebControlMixin, SettingsMixin, ExecutionMixin, QueueActionsMixin, CatalogControllerMixin, QObject):
    stateChanged = Signal()

    settingsChanged = Signal()

    queueChanged = Signal()

    episodeFiltersChanged = Signal()

    catalogFilterChanged = Signal()

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
        self._language = "en"
        self._translations = json.loads((Path(__file__).parent / "strings.ru.json").read_text(encoding="utf-8"))
        self._offline = offline
        self._ready = offline
        self._closing = False
        self._close_requested = False
        self._operations = {}
        self._entries = []
        self._hidden_episodes = {}
        self._catalog = []
        self._filter_preferences = None
        self._episode_search = ""
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
        self._refresh_pending = False
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
        self._web_lock = threading.Lock()
        self._web_pending = set()
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

    @Slot(str, str, result=str)
    def translate(self, value, language):
        return self._translations.get(value, value) if language == 'ru' else value

    def _text(self, value):
        return '\n'.join(self.translate(line, self._language) for line in str(value or '').split('\n'))

    @Slot(str)
    def setLanguage(self, language):
        if self._language != language:
            self._language = language
            self._publish_queue()
            self.stateChanged.emit()

    @Slot(object)
    def _invoke(self, callback):
        if not self._closing:
            callback()

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
        return self._web_server.url if self._web_server and self._web_server.alive else ""

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

    @Slot(bool)
    def setAutoClearFinished(self, enabled):
        self._auto_clear_finished = bool(enabled)
        if enabled:
            self.clearCompleted()
        self.stateChanged.emit()

    @Property(str, notify=stateChanged)
    def statusText(self):
        return self._text(self._status)

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
            "webSecurity": self._config.get("web_security", True),
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
            "stage": self._text(row.get("stage", "")),
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
            "stage": self._text(entry["stage"]),
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
            "stage": self._text(job["stage"]),
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
