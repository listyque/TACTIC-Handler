"""Asynchronous Repository Sync compatible with the original TACTIC workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
import threading
import time
import traceback
import urllib.request
import urllib.parse
import uuid

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    QRunnable,
    QThread,
    QThreadPool,
    Qt,
    Signal,
    Slot,
)

ROLES = (
    "taskId", "title", "process", "progress", "progressValue", "status",
    "checked", "bytesDone", "bytesTotal", "speed", "localPath", "webPath",
    "attempt", "error", "active", "phase", "alreadyExists",
)
TERMINAL_STATES = {"finished", "exists", "skipped", "failed", "cancelled"}


class RepositorySyncModel(QAbstractListModel):
    def __init__(self) -> None:
        super().__init__()
        self._role_ids = {
            name: Qt.UserRole + index + 1 for index, name in enumerate(ROLES)
        }
        self._records: list[dict] = []
        self._rows: dict[str, int] = {}

    def roleNames(self):
        return {
            role_id: name.encode("utf-8")
            for name, role_id in self._role_ids.items()
        }

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._records)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._records):
            return None
        name = next(
            (key for key, value in self._role_ids.items() if value == role),
            None,
        )
        return self._records[index.row()].get(name) if name else None

    def append(self, record: dict) -> None:
        row = len(self._records)
        self.beginInsertRows(QModelIndex(), row, row)
        self._records.append(dict(record))
        self._rows[record["taskId"]] = row
        self.endInsertRows()

    def update(self, task_id: str, **values) -> None:
        row = self._rows.get(task_id)
        if row is None:
            return
        record = self._records[row]
        changed_roles = []
        for name, value in values.items():
            if name in self._role_ids and record.get(name) != value:
                record[name] = value
                changed_roles.append(self._role_ids[name])
        if changed_roles:
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, changed_roles)

    def record(self, task_id: str) -> dict:
        row = self._rows.get(task_id)
        return self._records[row] if row is not None else {}

    def remove_ids(self, task_ids: set[str]) -> None:
        if not task_ids:
            return
        rows = [
            row for row, record in enumerate(self._records)
            if record["taskId"] in task_ids
        ]
        if not rows:
            return
        ranges = []
        first = last = rows[0]
        for row in rows[1:]:
            if row == last + 1:
                last = row
            else:
                ranges.append((first, last))
                first = last = row
        ranges.append((first, last))
        for first, last in reversed(ranges):
            self.beginRemoveRows(QModelIndex(), first, last)
            del self._records[first:last + 1]
            self.endRemoveRows()
        self._rows = {
            record["taskId"]: row
            for row, record in enumerate(self._records)
        }

    @Slot(int)
    def toggle_checked(self, row: int) -> None:
        if not 0 <= row < len(self._records):
            return
        record = self._records[row]
        record["checked"] = not bool(record.get("checked"))
        index = self.index(row, 0)
        self.dataChanged.emit(
            index, index, [self._role_ids["checked"]]
        )

    @Slot(int, result="QVariantMap")
    def get(self, row: int) -> dict:
        if not 0 <= row < len(self._records):
            return {}
        return dict(self._records[row])


class SyncHandle(QObject):
    downloaded = Signal(object)
    failed = Signal(object)

    def __init__(self, manager, task_id: str, file_object) -> None:
        super().__init__(manager)
        self.manager = manager
        self.task_id = task_id
        self.file_object = file_object

    @Slot()
    def download(self) -> None:
        if self.manager:
            self.manager.request_start(self.task_id)

    def is_download_in_progress(self) -> bool:
        return self.manager.status(self.task_id) in {"queued", "downloading"}

    def is_download_finished(self) -> bool:
        return self.manager.status(self.task_id) in {"finished", "exists"}


class WorkerSignals(QObject):
    progress = Signal(str, int, int, float)
    finished = Signal(str, object)
    failed = Signal(str, str, str)
    cancelled = Signal(str)


@dataclass
class SyncTask:
    task_id: str
    key: str
    file_object: object
    title: str
    process: str
    local_path: str
    web_path: str
    expected_size: int
    handle: SyncHandle | None = None
    signals: WorkerSignals | None = None
    cancel: threading.Event = field(default_factory=threading.Event)
    started_at: float = 0.0
    overwrite_policy: str = "overwrite"


class DownloadRunnable(QRunnable):
    def __init__(
        self,
        task: SyncTask,
        signals: WorkerSignals,
        retries: int = 2,
        chunk_size: int = 256 * 1024,
    ) -> None:
        super().__init__()
        self.task = task
        self.signals = signals
        self.retries = retries
        self.chunk_size = chunk_size
        self.setAutoDelete(True)

    def run(self) -> None:
        task = self.task
        partial = None
        try:
            destination = Path(task.file_object.prepare_repo())
            partial = destination.with_name(destination.name + ".part")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.is_file():
                current_size = destination.stat().st_size
                if task.expected_size <= 0 or current_size == task.expected_size:
                    self.signals.finished.emit(task.task_id, {
                        "path": str(destination),
                        "bytes": current_size,
                        "elapsed": 0.0,
                        "exists": True,
                    })
                    return
                if task.overwrite_policy == "skip":
                    self.signals.finished.emit(task.task_id, {
                        "path": str(destination),
                        "bytes": current_size,
                        "elapsed": 0.0,
                        "exists": True,
                        "skipped": True,
                    })
                    return
                if task.overwrite_policy == "cancel":
                    self.signals.cancelled.emit(task.task_id)
                    return

            last_error = None
            for attempt in range(1, self.retries + 2):
                if task.cancel.is_set():
                    self.signals.cancelled.emit(task.task_id)
                    return
                started = time.perf_counter()
                downloaded = 0
                last_emit = 0.0
                try:
                    request = urllib.request.Request(
                        urllib.parse.quote(
                            task.web_path, safe=":/?&=%#"
                        ),
                        headers={"User-Agent": "TACTIC-Handler/RepositorySync"},
                    )
                    with urllib.request.urlopen(request, timeout=15) as response:
                        header_size = int(
                            response.headers.get("Content-Length") or 0
                        )
                        total = header_size or task.expected_size
                        with partial.open("wb") as stream:
                            while True:
                                if task.cancel.is_set():
                                    raise InterruptedError("Download cancelled")
                                chunk = response.read(self.chunk_size)
                                if not chunk:
                                    break
                                stream.write(chunk)
                                downloaded += len(chunk)
                                now = time.perf_counter()
                                if now - last_emit >= 0.12:
                                    speed = downloaded / max(now - started, 0.001)
                                    self.signals.progress.emit(
                                        task.task_id, downloaded, total, speed
                                    )
                                    last_emit = now
                            stream.flush()
                            os.fsync(stream.fileno())
                    if header_size > 0 and downloaded != header_size:
                        raise IOError(
                            f"Incomplete file: {downloaded} of {header_size} bytes"
                        )
                    os.replace(partial, destination)
                    elapsed = time.perf_counter() - started
                    self.signals.progress.emit(
                        task.task_id, downloaded, total, downloaded / max(elapsed, .001)
                    )
                    self.signals.finished.emit(task.task_id, {
                        "path": str(destination),
                        "bytes": downloaded,
                        "elapsed": elapsed,
                        "exists": False,
                        "attempt": attempt,
                    })
                    return
                except InterruptedError:
                    try:
                        partial.unlink(missing_ok=True)
                    except OSError:
                        pass
                    self.signals.cancelled.emit(task.task_id)
                    return
                except Exception as error:
                    last_error = error
                    try:
                        partial.unlink(missing_ok=True)
                    except OSError:
                        pass
                    if attempt <= self.retries:
                        time.sleep(min(0.35 * 2 ** (attempt - 1), 1.5))
            self.signals.failed.emit(
                task.task_id,
                str(last_error or "Download failed"),
                traceback.format_exc(),
            )
        except Exception as error:
            if partial is not None:
                try:
                    partial.unlink(missing_ok=True)
                except OSError:
                    pass
            self.signals.failed.emit(
                task.task_id, str(error), traceback.format_exc()
            )


class RepositorySyncController(QObject):
    state_changed = Signal()
    visibility_requested = Signal(bool)
    task_finished = Signal(str, str)
    downloads_finished = Signal()
    file_download_done = Signal(object)
    task_failed = Signal(str)
    _schedule_requested = Signal(object)
    _start_requested = Signal(str)

    def __init__(self, debug_log=None, parent=None) -> None:
        super().__init__(parent)
        self.debug_log = debug_log
        self.model = RepositorySyncModel()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(4)
        self._tasks: dict[str, SyncTask] = {}
        self.queue_dict: dict[object, SyncHandle] = {}
        self._key_to_task: dict[str, str] = {}
        self._handles: dict[str, SyncHandle] = {}
        self._active = 0
        self._discovery_active = False
        self._discovery_state = "idle"
        self._discovery_error = ""
        self._discovery_metadata = ("default", False, 0.0)
        self._shutting_down = False
        self._hidden = True
        self.visibility_probe = None
        self._schedule_requested.connect(
            self._schedule_from_worker,
            Qt.ConnectionType.QueuedConnection,
        )
        self._start_requested.connect(
            self.start_task,
            Qt.ConnectionType.QueuedConnection,
        )

    def isHidden(self) -> bool:
        if self.visibility_probe:
            try:
                return not bool(self.visibility_probe())
            except (RuntimeError, TypeError):
                pass
        return self._hidden

    def setHidden(self, hidden: bool) -> None:
        self._hidden = bool(hidden)
        self.visibility_requested.emit(not self._hidden)

    def show(self) -> None:
        self.setHidden(False)

    def hide(self) -> None:
        self.setHidden(True)

    @staticmethod
    def presets(sobject) -> list[dict]:
        if not sobject:
            return []
        import thlib.global_functions as gf
        import thlib.tactic_classes as tc

        stype = sobject.get_stype()
        project = stype.get_project()
        records = tc.server_start().query(
            "sthpw/wdg_settings",
            [
                ("key", "like", f"search_type:{stype.get_code()}%"),
                ("project_code", project.get_code()),
            ],
            ["data"],
        )
        presets = []
        for record in records or []:
            preset = gf.from_json(record.get("data") or "")
            if isinstance(preset, dict):
                presets.append(preset)
        return presets or [{
            "pretty_preset_name": "Default",
            "preset_name": "default",
        }]

    @staticmethod
    def _pretty_bytes(value: float) -> str:
        value = float(value or 0)
        for suffix in ("B", "KB", "MB", "GB"):
            if value < 1024 or suffix == "GB":
                return f"{value:.0f} {suffix}" if suffix == "B" else f"{value:.1f} {suffix}"
            value /= 1024
        return "0 B"

    def _log(self, level: str, message: str, **kwargs) -> None:
        if self.debug_log:
            self.debug_log.log(
                level, message, group="repository_sync",
                source="RepositorySync", caller=2, **kwargs
            )

    def status(self, task_id: str) -> str:
        return str(self.model.record(task_id).get("status") or "")

    @staticmethod
    def previews_through_http_enabled() -> bool:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            value = gf.get_value_from_config(
                cfg_controls.get_checkin(),
                "getPreviewsThroughHttpCheckbox",
            )
        except (AttributeError, ImportError, KeyError, TypeError):
            return True
        return True if value is None else bool(value)

    def schedule_file_object(
        self,
        file_object,
        process: str = "",
        auto_start: bool = False,
        overwrite_policy: str = "overwrite",
    ) -> SyncHandle:
        overwrite_policy = (
            overwrite_policy
            if overwrite_policy in {"overwrite", "skip", "cancel"}
            else "overwrite"
        )
        if QThread.currentThread() != self.thread():
            request = {
                "file_object": file_object,
                "process": process,
                "auto_start": auto_start,
                "overwrite_policy": overwrite_policy,
                "event": threading.Event(),
                "result": None,
                "error": None,
                "cancelled": False,
            }
            self._schedule_requested.emit(request)
            if not request["event"].wait(30):
                request["cancelled"] = True
                raise TimeoutError(
                    "Timed out scheduling Repository Sync task on GUI thread"
                )
            if request["error"]:
                raise request["error"]
            return request["result"]
        return self._schedule_file_object(
            file_object, process, auto_start, overwrite_policy
        )

    @Slot(object)
    def _schedule_from_worker(self, request: dict) -> None:
        if request.get("cancelled"):
            request["event"].set()
            return
        try:
            request["result"] = self._schedule_file_object(
                request["file_object"],
                request["process"],
                request["auto_start"],
                request["overwrite_policy"],
            )
        except Exception as error:
            request["error"] = error
        finally:
            request["event"].set()

    def _schedule_file_object(
        self,
        file_object,
        process: str = "",
        auto_start: bool = False,
        overwrite_policy: str = "overwrite",
    ) -> SyncHandle:
        if self._shutting_down:
            raise RuntimeError("Repository Sync is shutting down")
        local_path = str(file_object.get_full_abs_path() or "")
        web_path = str(file_object.get_full_web_path() or "")
        if not local_path:
            raise ValueError("Local repository path is not configured")
        if not web_path.startswith(("http://", "https://")):
            raise ValueError("HTTP source is not available for this file")
        title = str(
            file_object.get_filename_with_ext()
            or Path(local_path).name or "File"
        )
        expected_size = int(file_object.get_file_size() or 0)
        key = f"{local_path}|{web_path}"
        existing_id = self._key_to_task.get(key)
        if existing_id and existing_id in self._handles:
            handle = self._handles[existing_id]
            self._tasks[existing_id].overwrite_policy = overwrite_policy
            unique_id = file_object.get_unique_id()
            if unique_id is not None:
                self.queue_dict[unique_id] = handle
            if auto_start:
                handle.download()
            return handle

        task_id = uuid.uuid4().hex
        task = SyncTask(
            task_id, key, file_object, title, process,
            local_path, web_path, expected_size,
            overwrite_policy=overwrite_policy,
        )
        handle = SyncHandle(self, task_id, file_object)
        task.handle = handle
        self._tasks[task_id] = task
        self._handles[task_id] = handle
        self._key_to_task[key] = task_id
        unique_id = file_object.get_unique_id()
        if unique_id is not None:
            self.queue_dict[unique_id] = handle
        self.model.append({
            "taskId": task_id, "title": title, "process": process,
            "progress": "Waiting", "progressValue": 0.0,
            "status": "waiting", "checked": True, "bytesDone": 0,
            "bytesTotal": expected_size, "speed": "", "localPath": local_path,
            "webPath": web_path, "attempt": 0, "error": "", "active": False,
            "phase": "queued", "alreadyExists": False,
        })
        self._log(
            "INFO", f"Queued {title}", command=web_path,
            details=f"Destination: {local_path}\nExpected: {expected_size} bytes",
        )
        self.state_changed.emit()
        if auto_start:
            handle.download()
        return handle

    def request_start(self, task_id: str) -> None:
        if QThread.currentThread() == self.thread():
            self.start_task(task_id)
        elif not self._shutting_down:
            self._start_requested.emit(task_id)

    @Slot(str)
    def start_task(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        status = self.status(task_id)
        if not task or status in {
            "queued", "downloading", "finished", "exists", "skipped"
        }:
            if task and status in {"finished", "exists", "skipped"}:
                task.handle.downloaded.emit(task.file_object)
            return
        task.cancel.clear()
        task.started_at = time.perf_counter()
        signals = WorkerSignals()
        signals.progress.connect(
            self._progress, Qt.ConnectionType.QueuedConnection
        )
        signals.finished.connect(
            self._finished, Qt.ConnectionType.QueuedConnection
        )
        signals.failed.connect(
            self._failed, Qt.ConnectionType.QueuedConnection
        )
        signals.cancelled.connect(
            self._cancelled, Qt.ConnectionType.QueuedConnection
        )
        # Keep signal objects alive only for the lifetime of the runnable.
        task.signals = signals
        self._active += 1
        self.model.update(
            task_id, status="queued", progress="Queued",
            active=True, error="", phase="queued", alreadyExists=False,
        )
        self._log("API", f"Starting download: {task.title}", command=task.web_path)
        self.pool.start(DownloadRunnable(task, signals))
        self.state_changed.emit()

    @Slot()
    def start_checked(self) -> None:
        for record in list(self.model._records):
            if record.get("checked") and record.get("status") not in {
                "queued", "downloading", "finished", "exists"
            }:
                self.start_task(record["taskId"])

    @Slot(int)
    def retry_row(self, row: int) -> None:
        record = self.model.get(row)
        if record:
            self.start_task(record["taskId"])

    @Slot(int)
    def cancel_row(self, row: int) -> None:
        record = self.model.get(row)
        task = self._tasks.get(record.get("taskId"))
        if task:
            task.cancel.set()
            self._log("WARNING", f"Cancel requested: {task.title}")

    @Slot(str)
    def cancel_task(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.cancel.set()
            self._log("WARNING", f"Cancel requested: {task.title}")

    @Slot(int)
    def remove_row(self, row: int) -> None:
        record = self.model.get(row)
        task_id = str(record.get("taskId") or "")
        task = self._tasks.get(task_id)
        if not task or record.get("status") in {"queued", "downloading"}:
            return
        self._release_task(task_id)
        self.model.remove_ids({task_id})
        self.state_changed.emit()

    def _release_task(self, task_id: str) -> None:
        """Drop every Python and QObject reference owned by a queue row."""
        task = self._tasks.pop(task_id, None)
        handle = self._handles.pop(task_id, None)
        if task:
            self._key_to_task.pop(task.key, None)
            if task.signals:
                task.signals.deleteLater()
                task.signals = None
            task.file_object = None
            task.handle = None
        self.queue_dict = {
            key: queued_handle
            for key, queued_handle in self.queue_dict.items()
            if queued_handle.task_id != task_id
        }
        if handle:
            handle.file_object = None
            handle.manager = None
            handle.setParent(None)
            handle.deleteLater()

    @staticmethod
    def _release_task_signals(task: SyncTask) -> None:
        signals = task.signals
        task.signals = None
        if signals:
            signals.deleteLater()

    @Slot()
    def clear_finished(self) -> None:
        removable = {
            record["taskId"] for record in self.model._records
            if record.get("status") in TERMINAL_STATES
        }
        for task_id in removable:
            self._release_task(task_id)
        self.model.remove_ids(removable)
        self.state_changed.emit()

    @Slot()
    def clear_queue(self) -> None:
        removable = {
            record["taskId"] for record in self.model._records
            if record.get("status") not in {"queued", "downloading"}
        }
        for task_id in removable:
            self._release_task(task_id)
        self.model.remove_ids(removable)
        self.state_changed.emit()

    def is_all_downloads_done(self) -> bool:
        return self._active == 0

    @Slot(str, int, int, float)
    def _progress(self, task_id: str, done: int, total: int, speed: float) -> None:
        ratio = min(1.0, done / total) if total > 0 else 0.0
        self.model.update(
            task_id, status="downloading", phase="downloading", active=True,
            bytesDone=done, bytesTotal=total, progressValue=ratio,
            progress=f"{self._pretty_bytes(done)} / {self._pretty_bytes(total)}"
                if total else self._pretty_bytes(done),
            speed=f"{self._pretty_bytes(speed)}/s",
        )

    def _complete_active(self) -> None:
        self._active = max(0, self._active - 1)
        if self._active == 0:
            self.downloads_finished.emit()
        self.state_changed.emit()

    @Slot(str, object)
    def _finished(self, task_id: str, result: dict) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        status = (
            "skipped" if result.get("skipped")
            else "exists" if result.get("exists") else "finished"
        )
        byte_count = int(result.get("bytes") or 0)
        elapsed = float(result.get("elapsed") or 0)
        self.model.update(
            task_id, status=status, active=False, progressValue=1.0,
            bytesDone=byte_count, bytesTotal=byte_count or task.expected_size,
            progress=(
                "Skipped" if status == "skipped"
                else "Already in repository" if status == "exists"
                else "Finished"
            ),
            speed="", phase="completed", alreadyExists=status == "exists",
        )
        self._log(
            "INFO", f"{task.title}: {self.model.record(task_id)['progress']}",
            command=task.web_path, duration=elapsed,
            size_kb=byte_count / 1024,
            details=f"Saved to: {result.get('path')}",
        )
        self._complete_active()
        task.handle.downloaded.emit(task.file_object)
        self.file_download_done.emit(task.file_object)
        self.task_finished.emit(task_id, str(result.get("path") or ""))
        self._release_task_signals(task)

    @Slot(str, str, str)
    def _failed(self, task_id: str, error: str, stacktrace: str) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        elapsed = time.perf_counter() - task.started_at
        self.model.update(
            task_id, status="failed", active=False,
            progress="Download failed", error=error, speed="", phase="failed",
        )
        self._log(
            "ERROR", f"Download failed: {task.title}: {error}",
            command=task.web_path, duration=elapsed,
            stacktrace=stacktrace,
            details=f"Destination: {task.local_path}",
        )
        self._complete_active()
        task.handle.failed.emit(task.file_object)
        self.task_failed.emit(task_id)
        self._release_task_signals(task)

    @Slot(str)
    def _cancelled(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        self.model.update(
            task_id, status="cancelled", active=False,
            progress="Cancelled", speed="", phase="cancelled",
        )
        self._log("WARNING", f"Download cancelled: {task.title}")
        self._complete_active()
        self.task_failed.emit(task_id)
        self._release_task_signals(task)

    @Property(int, notify=state_changed)
    def active_count(self) -> int:
        return self._active

    @Property(int, notify=state_changed)
    def queue_count(self) -> int:
        return len(self.model._records)

    @Property(bool, notify=state_changed)
    def discovery_active(self) -> bool:
        return self._discovery_active

    @Property(str, notify=state_changed)
    def discovery_state(self) -> str:
        return self._discovery_state

    @Property(str, notify=state_changed)
    def discovery_error(self) -> str:
        return self._discovery_error

    def start_sobject_sync(
        self, sobject, preset_name: str = "default", only_updates: bool = False
    ) -> None:
        from thlib.environment import env_inst
        if not sobject or self._discovery_active:
            return
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        self._discovery_active = True
        self._discovery_state = "discovery"
        self._discovery_error = ""
        started = time.perf_counter()
        self._log(
            "API", f"Discovering repository files: {preset_name}",
            details=str(sobject.get_search_key()),
        )
        worker = env_inst.server_pool.add_task(
            self._discover_files, sobject, preset_name, only_updates
        )
        worker.add_result_data((preset_name, only_updates, started))
        self._discovery_metadata = (preset_name, only_updates, started)
        worker.result.connect(
            self._publish_discovery,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            self._discovery_worker_error,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        self.state_changed.emit()

    @staticmethod
    def _preset_items(mapping: dict, suffix: str, enabled=False) -> dict:
        result = {}
        for key, value in (mapping or {}).items():
            if str(key).endswith(suffix):
                if not enabled or value.get("state"):
                    result[str(key).replace(suffix, "")] = value
        return result

    @classmethod
    def _load_preset(cls, sobject, preset_name: str) -> dict:
        import thlib.global_functions as gf
        import thlib.tactic_classes as tc
        stype = sobject.get_stype()
        key = f"search_type:{stype.get_code()}:preset_name:{preset_name}"
        records = tc.server_start().query(
            "sthpw/wdg_settings",
            [("key", key), ("project_code", stype.get_project().get_code())],
            ["data"],
        )
        if records:
            result = gf.from_json(records[0].get("data") or "")
            if isinstance(result, dict):
                return result
        return {
            "preset_name": "default", "pretty_preset_name": "Default",
            "get_versions": False,
            "publish:{b}": {"state": True},
            "attachment:{b}": {"state": True},
            "icon:{b}": {"state": True},
        }

    @classmethod
    def _collect_sobject(cls, sobject, preset: dict, files: dict) -> None:
        pipelines = cls._preset_items(preset, ":{pp}")
        builtins = cls._preset_items(preset, ":{b}", True)
        process_maps = [
            cls._preset_items(value.get("sub") or {}, ":{pr}", True)
            for value in pipelines.values()
        ] or [{}]
        for process_map in process_maps:
            enabled = set(process_map) | set(builtins)
            for process_name, process_object in (
                sobject.get_all_processes() or {}
            ).items():
                if process_name not in enabled:
                    continue
                for context_object in (process_object.get_contexts() or {}).values():
                    snapshots = list(
                        (context_object.get_versionless() or {}).values()
                    )
                    if preset.get("get_versions"):
                        snapshots.extend(
                            (context_object.get_versions() or {}).values()
                        )
                    for snapshot in snapshots:
                        for file_object in snapshot.get_files_objects() or []:
                            local = str(file_object.get_full_abs_path() or "")
                            web = str(file_object.get_full_web_path() or "")
                            files[f"{local}|{web}"] = (file_object, process_name)

        children = cls._preset_items(preset, ":{s}", True)
        stype = sobject.get_stype()
        project = stype.get_project()
        for child_code, child_preset in children.items():
            child_stype = project.stypes.get(child_code)
            if not child_stype:
                continue
            related, _query_info = sobject.get_related_sobjects(
                child_stype=child_stype,
                parent_stype=stype,
                get_all_snapshots=True,
            )
            for related_sobject in (related or {}).values():
                cls._collect_sobject(
                    related_sobject, child_preset.get("sub") or {}, files
                )

    @classmethod
    def _discover_files(
        cls, sobject, preset_name: str, only_updates: bool
    ) -> tuple[list]:
        preset = cls._load_preset(sobject, preset_name)
        from thlib.environment import env_read_config, env_write_config
        stype = sobject.get_stype()
        group_path = "ui_search/{}/{}/{}/sobjects_conf".format(
            stype.project.info["type"],
            stype.project.info["code"],
            stype.get_code().split("/")[1],
        )
        filters = None
        if only_updates:
            last_sync = env_read_config(
                filename=sobject.get_code(),
                unique_id=group_path,
                long_abs_path=True,
            )
            if last_sync:
                filters = [("timestamp", "is after", last_sync)]
        sobject.update_snapshots(filters=filters)
        files: dict[str, tuple] = {}
        cls._collect_sobject(sobject, preset, files)
        env_write_config(
            datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
            filename=sobject.get_code(),
            unique_id=group_path,
            long_abs_path=True,
        )
        # OperationWorker appends result metadata to tuple results.
        return (list(files.values()),)

    @Slot(object)
    def _publish_discovery(self, result) -> None:
        files, metadata = result
        preset_name, only_updates, started = metadata
        self._discovery_active = False
        self._discovery_state = "completed"
        self._discovery_error = ""
        for file_object, process in files:
            self.schedule_file_object(file_object, process)
        elapsed = time.perf_counter() - started
        self._log(
            "INFO", f"Repository discovery finished: {len(files)} files",
            duration=elapsed,
            details=f"Preset: {preset_name}; updates only: {only_updates}",
        )
        self.start_checked()
        self.state_changed.emit()

    @Slot(object)
    def _discovery_worker_error(self, error) -> None:
        preset_name, _only_updates, started = self._discovery_metadata
        self._discovery_active = False
        payload = error[0] if isinstance(error, tuple) else error
        self._discovery_state = "failed"
        self._discovery_error = str(payload)
        self._log(
            "ERROR", f"Repository discovery failed: {preset_name}",
            duration=time.perf_counter() - started,
            stacktrace=str(payload),
        )
        self.state_changed.emit()

    @Slot()
    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        for task in self._tasks.values():
            task.cancel.set()
        self.pool.clear()
        if not self.pool.waitForDone(16000):
            self._log(
                "WARNING",
                "Repository Sync shutdown timed out with active downloads",
            )
        for task_id in tuple(self._tasks):
            self._release_task(task_id)
        self._active = 0
        self._discovery_active = False
        self._discovery_state = "cancelled"
