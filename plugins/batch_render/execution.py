"""Batch execution owner."""
from __future__ import annotations

import threading
import time
from copy import deepcopy
from pathlib import Path
from PySide6.QtCore import Slot
from .domain import (
    _finalize_preparation_log,
    _finalize_shot,
    _job_frame_count,
    _prepare_episode,
    _prepare_shot,
    _queue_entry,
    _render_native,
    _set_episode_task_status,
)
from .queue_state import _TERMINAL


class ExecutionMixin:
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
            row["stage"] = self._text(payload["stage"]) + (
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

    def _tick(self):
        now = time.monotonic()
        delta, self._last_tick = now - self._last_tick, now
        if self._stage_operation is not None and self._active_entry:
            self._active_entry["elapsed"] += delta
            if self._active_job:
                self._active_job["elapsed"] += delta
            self._publish_queue()
