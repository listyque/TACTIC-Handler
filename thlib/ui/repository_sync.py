"""Asynchronous Repository Sync using the native TACTIC workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import threading
import time
import traceback
import urllib.request
import urllib.parse
import uuid

from .repository_sync_presets import RepositoryPresetCache

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    QRunnable,
    QThread,
    QThreadPool,
    QTimer,
    Qt,
    Signal,
    Slot,
)

ROLES = (
    "taskId", "title", "process", "progress", "progressValue", "status",
    "checked", "bytesDone", "bytesTotal", "speed", "localPath", "webPath",
    "attempt", "error", "active", "phase", "alreadyExists",
    "transferredBytes", "speedValue",
)
TERMINAL_STATES = {"finished", "exists", "skipped", "failed", "cancelled"}
COMPLETED_STATES = {"finished", "exists", "skipped"}
FILE_TIME_TOLERANCE_SECONDS = 2.0


class RepositorySyncModel(QAbstractListModel):
    def __init__(self) -> None:
        super().__init__()
        self._role_ids = {
            name: Qt.UserRole + index + 1 for index, name in enumerate(ROLES)
        }
        self._role_names = {
            role_id: name for name, role_id in self._role_ids.items()
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
        name = self._role_names.get(role)
        return self._records[index.row()].get(name) if name else None

    def append(self, record: dict) -> None:
        row = len(self._records)
        self.beginInsertRows(QModelIndex(), row, row)
        self._records.append(dict(record))
        self._rows[record["taskId"]] = row
        self.endInsertRows()

    def extend(self, records: list[dict]) -> None:
        if not records:
            return
        first = len(self._records)
        last = first + len(records) - 1
        self.beginInsertRows(QModelIndex(), first, last)
        for offset, source in enumerate(records):
            record = dict(source)
            self._records.append(record)
            self._rows[record["taskId"]] = first + offset
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

    def update_many(self, task_ids, **values) -> None:
        rows = sorted(
            self._rows[task_id]
            for task_id in task_ids if task_id in self._rows
        )
        if not rows:
            return
        changed_roles = [
            self._role_ids[name]
            for name in values if name in self._role_ids
        ]
        if not changed_roles:
            return
        changed_rows = []
        for row in rows:
            record = self._records[row]
            changed = False
            for name, value in values.items():
                if name in self._role_ids and record.get(name) != value:
                    record[name] = value
                    changed = True
            if changed:
                changed_rows.append(row)
        if not changed_rows:
            return
        first = previous = changed_rows[0]
        for row in changed_rows[1:]:
            if row != previous + 1:
                self.dataChanged.emit(
                    self.index(first, 0), self.index(previous, 0),
                    changed_roles,
                )
                first = row
            previous = row
        self.dataChanged.emit(
            self.index(first, 0), self.index(previous, 0), changed_roles
        )

    def record(self, task_id: str) -> dict:
        row = self._rows.get(task_id)
        return self._records[row] if row is not None else {}

    def remove_ids(self, task_ids: set[str]) -> None:
        if not task_ids:
            return
        remaining = [
            record for record in self._records
            if record["taskId"] not in task_ids
        ]
        if len(remaining) == len(self._records):
            return
        # Auto-clean may remove several completed rows separated by failed
        # entries. Reset once so the ListView never renders intermediate row
        # indexes and visibly jumps through several layouts.
        self.beginResetModel()
        self._records = remaining
        self._rows = {
            record["taskId"]: row
            for row, record in enumerate(self._records)
        }
        self.endResetModel()

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
        self._terminal_status = ""

    @Slot()
    def download(self) -> None:
        if self.manager:
            self.manager.request_start(self.task_id)

    def is_download_in_progress(self) -> bool:
        return bool(self.manager) and self.manager.status(self.task_id) in {
            "queued", "downloading"
        }

    def is_download_finished(self) -> bool:
        status = (
            self.manager.status(self.task_id)
            if self.manager else self._terminal_status
        )
        return status in {"finished", "exists", "skipped"}

    def detach(self, status: str) -> None:
        self._terminal_status = str(status or "")
        self.manager = None


class WorkerSignals(QObject):
    progress = Signal(str, int, int, float)
    finished = Signal(str, object)
    failed = Signal(str, str, str)
    cancelled = Signal(str)


from thlib.repository_download import DownloadOperation, PreparedSyncEntry, SyncTask


class DownloadRunnable(QRunnable):
    def __init__(self, task, signals, retries=2, chunk_size=256 * 1024):
        super().__init__()
        self.task = task
        self.signals = signals
        self.retries = retries
        self.chunk_size = chunk_size
        self.setAutoDelete(True)

    def run(self):
        DownloadOperation.run(self)


class RepositorySyncController(QObject):
    state_changed = Signal()
    visibility_requested = Signal(bool)
    task_finished = Signal(str, str)
    task_updated = Signal(str)
    downloads_finished = Signal()
    file_download_done = Signal(object)
    task_failed = Signal(str)
    aggregate_changed = Signal()
    configuration_changed = Signal()
    activeRowChanged = Signal()
    _schedule_requested = Signal(object)
    _start_requested = Signal(str)
    _partial_publication_requested = Signal()
    _discovery_publication_requested = Signal()

    def __init__(self, debug_log=None, parent=None) -> None:
        super().__init__(parent)
        self.debug_log = debug_log
        self.model = RepositorySyncModel()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(4)
        self._tasks: dict[str, SyncTask] = {}
        self.queue_dict: dict[object, SyncHandle] = {}
        self._key_to_task: dict[str, str] = {}
        self._preview_key_to_task: dict[str, str] = {}
        self._handles: dict[str, SyncHandle] = {}
        self._active = 0
        self._visible_active = 0
        self._focused_task_id = ""
        self._pending_start_ids = deque()
        self._pending_start_set: set[str] = set()
        self._batch_task_ids: set[str] = set()
        self._batch_running = False
        self._batch_started_at = 0.0
        self._batch_finished_at = 0.0
        self._last_batch_summary: dict = {}
        self._batch_network_bytes = 0
        self._batch_speed_bps = 0.0
        self._batch_task_bytes: dict[str, int] = {}
        self._speed_samples = deque(maxlen=96)
        self._aggregate_cache: dict = {}
        self._aggregate_dirty = True
        self._discovery_active = False
        self._discovery_state = "idle"
        self._discovery_error = ""
        self._discovery_metadata = ("default", False, 0.0)
        self._publication_entries = deque()
        self._publication_handles: list[SyncHandle] = []
        self._publication_checkpoint: dict = {}
        self._publication_started = 0.0
        self._publication_count = 0
        self._discovery_scope_files = 0
        self._discovery_scope_bytes = 0
        self._discovery_processed_roots = 0
        self._discovery_total_roots = 0
        self._discovery_mode = "full"
        self._discovery_generation = 0
        self._discovery_cancel = threading.Event()
        self._discovery_worker = None
        self._preset_store = RepositoryPresetCache(self._log, self)
        self._preset_store.changed.connect(self.configuration_changed.emit)
        self._partial_publication_entries = deque()
        self._partial_publication_running = False
        self._partial_source_finished = False
        self._partial_checkpoint: dict = {}
        self._partial_task_ids: set[str] = set()
        self._partial_started = 0.0
        self._sync_checkpoints: list[dict] = []
        self._auto_close_on_success = False
        self._auto_close_task_ids: set[str] = set()
        self._shutting_down = False
        self._hidden = True
        self.visibility_probe = None
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._refresh_aggregate)
        self._aggregate_timer = QTimer(self)
        self._aggregate_timer.setSingleShot(True)
        # Aggregate properties scan the current batch. Coalesce rapid row
        # transitions so thousands of tiny files do not turn that scan into
        # O(n²) work on the GUI thread.
        self._aggregate_timer.setInterval(250)
        self._aggregate_timer.timeout.connect(self._refresh_aggregate)
        self._active_row_timer = QTimer(self)
        self._active_row_timer.setSingleShot(True)
        self._active_row_timer.timeout.connect(self._emit_active_row_changed)
        self._active_row_last_emit = 0.0
        self._auto_clean_timer = QTimer(self)
        self._auto_clean_timer.setSingleShot(True)
        self._auto_clean_timer.setInterval(3500)
        self._auto_clean_timer.timeout.connect(self.clear_finished)
        self.model.dataChanged.connect(self._mark_aggregate_dirty)
        self.model.rowsInserted.connect(self._mark_aggregate_dirty)
        self.model.rowsRemoved.connect(self._mark_aggregate_dirty)
        self.model.modelReset.connect(self._mark_aggregate_dirty)
        self._schedule_requested.connect(
            self._schedule_from_worker,
            Qt.ConnectionType.QueuedConnection,
        )
        self._start_requested.connect(
            self.start_task,
            Qt.ConnectionType.QueuedConnection,
        )
        self._partial_publication_requested.connect(
            self._publish_partial_queue_chunk,
            Qt.ConnectionType.QueuedConnection,
        )
        self._discovery_publication_requested.connect(
            self._publish_discovery_chunk,
            Qt.ConnectionType.QueuedConnection,
        )
        self._refresh_aggregate(emit_signal=False)

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

    def presets(self, source) -> list[dict]:
        return self._preset_store.records(source)

    def cache_presets(self, source, presets) -> None:
        self._preset_store.populate(source, presets)

    def request_presets(self, source, force: bool = False) -> None:
        self._preset_store.request(source, force)

    @staticmethod
    def _preset_settings_location(source, tab_name: str) -> tuple[str, str]:
        try:
            stype = source.get_stype()
        except AttributeError:
            stype = source
        project = stype.get_project()
        info = dict(getattr(project, "info", None) or {})
        project_type = str(info.get("type") or "project")
        project_code = str(
            info.get("code") or project.get_code() or "default"
        )
        return (
            f"ui_search/{project_type}/{project_code}/"
            f"{str(tab_name or 'default')}",
            "repo_sync",
        )

    @classmethod
    def selected_preset_index(cls, source, tab_name: str) -> int:
        try:
            from thlib.environment import env_read_config

            group, filename = cls._preset_settings_location(source, tab_name)
            values = env_read_config(
                filename=filename, unique_id=group, long_abs_path=True
            ) or {}
            return max(0, int(values.get("presets_combo_box", 0)))
        except (AttributeError, KeyError, TypeError, ValueError):
            return 0

    @classmethod
    def selected_preset_name(cls, source, tab_name: str) -> str:
        try:
            from thlib.environment import env_read_config

            group, filename = cls._preset_settings_location(source, tab_name)
            values = env_read_config(
                filename=filename, unique_id=group, long_abs_path=True
            ) or {}
            return str(values.get("preset_name") or "")
        except (AttributeError, KeyError, TypeError, ValueError):
            return ""

    @classmethod
    def store_selected_preset_index(
        cls, source, tab_name: str, index: int
    ) -> None:
        cls.store_selected_preset(source, tab_name, index, "")

    @classmethod
    def store_selected_preset(
        cls, source, tab_name: str, index: int, preset_name: str
    ) -> None:
        try:
            from thlib.environment import env_write_config

            group, filename = cls._preset_settings_location(source, tab_name)
            values = {"presets_combo_box": max(0, int(index))}
            if preset_name:
                values["preset_name"] = str(preset_name)
            env_write_config(values, filename=filename, unique_id=group,
                             long_abs_path=True)
        except (AttributeError, KeyError, TypeError, ValueError):
            pass

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
        record = self.model.record(task_id)
        if record:
            return str(record.get("status") or "")
        task = self._tasks.get(task_id)
        return str(task.state if task else "")

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

    @staticmethod
    def verify_repository_md5_enabled() -> bool:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            value = gf.get_value_from_config(
                cfg_controls.get_checkin(),
                "verifyRepositoryMd5CheckBox",
            )
        except (AttributeError, ImportError, KeyError, TypeError):
            return False
        return False if value is None else bool(value)

    @staticmethod
    def auto_clean_enabled() -> bool:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            value = gf.get_value_from_config(
                cfg_controls.get_checkin(),
                "autoCleanRepositorySyncCheckBox",
            )
        except (AttributeError, ImportError, KeyError, TypeError):
            return False
        return False if value is None else bool(value)

    @staticmethod
    def configured_scope_mode() -> str:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            value = gf.get_value_from_config(
                cfg_controls.get_checkin(),
                "repositorySyncScopeModeComboBox",
            )
        except (AttributeError, ImportError, KeyError, TypeError):
            value = 0
        try:
            return "partial" if int(value or 0) == 1 else "full"
        except (TypeError, ValueError):
            return "full"

    @staticmethod
    def configured_partial_chunk_size() -> int:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            value = gf.get_value_from_config(
                cfg_controls.get_checkin(),
                "repositorySyncPartialChunkSizeSpinBox",
            )
            return max(1, min(250, int(value or 10)))
        except (AttributeError, ImportError, KeyError, TypeError, ValueError):
            return 10

    @staticmethod
    def _store_checkin_bool(control: str, value: bool) -> None:
        import copy
        from thlib.environment import cfg_controls

        config = copy.deepcopy(cfg_controls.get_checkin() or {})
        bucket = config.setdefault(
            "QCheckBox", {"obj_name": [], "value": []}
        )
        names = list(bucket.get("obj_name") or [])
        values = list(bucket.get("value") or [])
        if control in names:
            index = names.index(control)
            while len(values) <= index:
                values.append(None)
            values[index] = int(bool(value))
        else:
            names.append(control)
            values.append(int(bool(value)))
        bucket["obj_name"] = names
        bucket["value"] = values
        cfg_controls.set_checkin(config)

    @staticmethod
    def _store_checkin_int(control: str, value: int) -> None:
        import copy
        from thlib.environment import cfg_controls

        config = copy.deepcopy(cfg_controls.get_checkin() or {})
        bucket = config.setdefault(
            "QSpinBox", {"obj_name": [], "value": []}
        )
        names = list(bucket.get("obj_name") or [])
        values = list(bucket.get("value") or [])
        if control in names:
            index = names.index(control)
            while len(values) <= index:
                values.append(None)
            values[index] = int(value)
        else:
            names.append(control)
            values.append(int(value))
        bucket["obj_name"] = names
        bucket["value"] = values
        cfg_controls.set_checkin(config)

    @Slot(int)
    def set_partial_chunk_size(self, value: int) -> None:
        value = max(1, min(250, int(value or 10)))
        if value == self.configured_partial_chunk_size():
            return
        self._store_checkin_int(
            "repositorySyncPartialChunkSizeSpinBox", value
        )
        self.configuration_changed.emit()

    @Slot(bool)
    def set_auto_clean(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self.auto_clean_enabled():
            return
        self._store_checkin_bool(
            "autoCleanRepositorySyncCheckBox", enabled
        )
        if not enabled:
            self._auto_clean_timer.stop()
        elif self._active == 0:
            self._schedule_auto_clean()
        self.configuration_changed.emit()

    @Slot()
    def reload_configuration(self) -> None:
        if self.auto_clean_enabled() and self._active == 0:
            self._schedule_auto_clean()
        else:
            self._auto_clean_timer.stop()
        self.configuration_changed.emit()

    @staticmethod
    def _prepare_file_object(
        file_object, process: str = "", is_ui_preview: bool = False,
    ) -> PreparedSyncEntry:
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
        expected_md5 = str(file_object.get_md5() or "").strip().lower()
        expected_mtime = 0.0
        try:
            timestamp = file_object.get_timestamp(obj=True)
            if isinstance(timestamp, datetime):
                expected_mtime = timestamp.timestamp()
        except (KeyError, TypeError, ValueError, OSError):
            expected_mtime = 0.0
        return PreparedSyncEntry(
            file_object=file_object,
            process=str(process or ""),
            local_path=local_path,
            web_path=web_path,
            title=title,
            expected_size=int(file_object.get_file_size() or 0),
            expected_md5=expected_md5,
            expected_mtime=expected_mtime,
            unique_id=file_object.get_unique_id(),
            is_ui_preview=bool(is_ui_preview),
        )

    def schedule_file_object(
        self,
        file_object,
        process: str = "",
        auto_start: bool = False,
        overwrite_policy: str = "overwrite",
        is_ui_preview: bool = False,
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
                "is_ui_preview": bool(is_ui_preview),
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
        return self._schedule_prepared_entry(
            self._prepare_file_object(
                file_object, process, is_ui_preview=is_ui_preview
            ),
            auto_start, overwrite_policy,
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
                request["is_ui_preview"],
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
        is_ui_preview: bool = False,
    ) -> SyncHandle:
        return self._schedule_prepared_entry(
            self._prepare_file_object(
                file_object, process, is_ui_preview=is_ui_preview
            ),
            auto_start, overwrite_policy,
        )

    def _schedule_prepared_entry(
        self,
        entry: PreparedSyncEntry,
        auto_start: bool = False,
        overwrite_policy: str = "overwrite",
        *,
        append_model: bool = True,
        write_log: bool = True,
    ) -> tuple[SyncHandle, dict | None] | SyncHandle:
        if self._shutting_down:
            raise RuntimeError("Repository Sync is shutting down")
        return_record = not append_model
        publish_model = append_model and not entry.is_ui_preview
        publish_log = write_log and not entry.is_ui_preview
        file_object = entry.file_object
        local_path = entry.local_path
        web_path = entry.web_path
        title = entry.title
        process = entry.process
        expected_size = entry.expected_size
        expected_md5 = entry.expected_md5
        expected_mtime = entry.expected_mtime
        verify_md5 = (
            self.verify_repository_md5_enabled()
            and not entry.is_ui_preview
        )
        key = entry.key
        key_index = (
            self._preview_key_to_task
            if entry.is_ui_preview else self._key_to_task
        )
        existing_id = key_index.get(key)
        if existing_id and existing_id in self._handles:
            existing_task = self._tasks[existing_id]
            terminal = self.status(existing_id) in TERMINAL_STATES
            if terminal:
                # A completed row belongs to the previous sync run. Reusing it
                # here silently drops the file from the new run: only paths not
                # seen before (usually freshly generated web/icon previews)
                # would be queued. The worker performs the cheap local
                # size/checksum check, so recreate every discovered terminal
                # entry and let the current run validate the complete scope.
                self._release_task(existing_id)
                self.model.remove_ids({existing_id})
            else:
                handle = self._handles[existing_id]
                existing_task.file_object = file_object
                existing_task.expected_size = expected_size
                existing_task.expected_md5 = expected_md5
                existing_task.expected_mtime = expected_mtime
                # Never downgrade an already queued full sync when a UI
                # preview asks for the same file while it is active.
                existing_task.is_ui_preview = (
                    existing_task.is_ui_preview and entry.is_ui_preview
                )
                existing_task.verify_md5 = (
                    self.verify_repository_md5_enabled()
                    and not existing_task.is_ui_preview
                )
                existing_task.overwrite_policy = overwrite_policy
                handle.file_object = file_object
                unique_id = entry.unique_id
                if unique_id is not None:
                    if not entry.is_ui_preview:
                        self.queue_dict[unique_id] = handle
                if auto_start:
                    handle.download()
                return (handle, None) if return_record else handle

        task_id = uuid.uuid4().hex
        task = SyncTask(
            task_id=task_id,
            key=key,
            file_object=file_object,
            title=title,
            process=process,
            local_path=local_path,
            web_path=web_path,
            expected_size=expected_size,
            expected_md5=expected_md5,
            expected_mtime=expected_mtime,
            is_ui_preview=entry.is_ui_preview,
            verify_md5=verify_md5,
            overwrite_policy=overwrite_policy,
        )
        handle = SyncHandle(self, task_id, file_object)
        task.handle = handle
        self._tasks[task_id] = task
        self._handles[task_id] = handle
        key_index[key] = task_id
        unique_id = entry.unique_id
        if unique_id is not None and not entry.is_ui_preview:
            self.queue_dict[unique_id] = handle
        record = {
            "taskId": task_id, "title": title, "process": process,
            "progress": "Waiting", "progressValue": 0.0,
            "status": "waiting", "checked": True, "bytesDone": 0,
            "bytesTotal": expected_size, "speed": "", "localPath": local_path,
            "webPath": web_path, "attempt": 0, "error": "", "active": False,
            "phase": "queued", "alreadyExists": False,
            "transferredBytes": 0, "speedValue": 0.0,
        }
        if publish_model:
            self.model.append(record)
        if publish_log:
            self._log(
                "INFO", f"Queued {title}", command=web_path,
                details=(
                    f"Destination: {local_path}\nExpected: {expected_size} bytes"
                ),
            )
        if publish_model:
            self.state_changed.emit()
            self._refresh_aggregate()
        if auto_start:
            handle.download()
        return (handle, record) if return_record else handle

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
            "downloading", "finished", "exists", "skipped"
        }:
            if task and status in {"finished", "exists", "skipped"}:
                task.handle.downloaded.emit(task.file_object)
            return
        if task_id in self._pending_start_set or status == "queued":
            return
        task.state = "queued"
        if task.is_ui_preview:
            self._pending_start_ids.append(task_id)
            self._pending_start_set.add(task_id)
            self._pump_downloads()
            return
        if not self._batch_running:
            self._begin_batch()
        self._batch_task_ids.add(task_id)
        self._pending_start_ids.append(task_id)
        self._pending_start_set.add(task_id)
        self.model.update(
            task_id, status="queued", progress="Queued", active=False,
            error="", phase="queued", alreadyExists=False, bytesDone=0,
            transferredBytes=0, speed="", speedValue=0.0,
        )
        self._pump_downloads()
        self.state_changed.emit()
        self._refresh_aggregate()

    def _begin_batch(self, started_at: float | None = None) -> None:
        self._batch_task_ids.clear()
        self._batch_running = True
        self._batch_started_at = (
            time.perf_counter() if started_at is None else started_at
        )
        self._batch_finished_at = 0.0
        self._last_batch_summary = {}
        self._batch_network_bytes = 0
        self._batch_speed_bps = 0.0
        self._batch_task_bytes.clear()
        self._speed_samples.clear()
        self._auto_clean_timer.stop()
        if not self._elapsed_timer.isActive():
            self._elapsed_timer.start()

    def _pump_downloads(self) -> None:
        capacity = max(0, self.pool.maxThreadCount() - self._active)
        while capacity and self._pending_start_ids:
            task_id = self._pending_start_ids.popleft()
            self._pending_start_set.discard(task_id)
            task = self._tasks.get(task_id)
            if not task:
                continue
            if task.cancel.is_set():
                task.state = "cancelled"
                if task.is_ui_preview:
                    file_object = task.file_object
                    handle = task.handle
                    handle.failed.emit(file_object)
                    self.task_failed.emit(task_id)
                    self._release_task(task_id)
                    continue
                self.model.update(
                    task_id, status="cancelled", active=False,
                    progress="Cancelled", phase="cancelled",
                )
                self.task_failed.emit(task_id)
                continue
            self._start_task_now(task)
            capacity -= 1

    def _start_task_now(self, task: SyncTask) -> None:
        task_id = task.task_id
        task.cancel.clear()
        task.verify_md5 = (
            self.verify_repository_md5_enabled()
            and not task.is_ui_preview
        )
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
        task.state = "queued"
        if not task.is_ui_preview:
            self._visible_active += 1
            self._focused_task_id = task_id
            self._request_active_row_refresh()
            self.model.update(
                task_id, status="queued", progress="Queued",
                active=True, error="", phase="queued", alreadyExists=False,
                bytesDone=0, transferredBytes=0, speed="", speedValue=0.0,
            )
            self._log(
                "API", f"Checking repository: {task.title}",
                command=task.web_path,
            )
        self.pool.start(DownloadRunnable(task, signals))

    @Slot()
    def start_checked(self) -> None:
        task_ids = [
            record["taskId"] for record in self.model._records
            if record.get("checked") and record.get("status") not in {
                "queued", "downloading", "finished", "exists", "skipped"
            }
        ]
        if not task_ids:
            self._commit_completed_checkpoints()
            return
        self._start_task_ids(task_ids)

    def _start_task_ids(self, task_ids) -> None:
        task_ids = list(dict.fromkeys(
            str(task_id) for task_id in task_ids if task_id
        ))
        if not task_ids:
            return
        if not self._batch_running:
            self._begin_batch()
        queued_ids = []
        for task_id in task_ids:
            task = self._tasks.get(task_id)
            if (
                not task or task_id in self._pending_start_set
                or self.status(task_id) in {
                    "queued", "downloading", "finished", "exists", "skipped"
                }
            ):
                continue
            task.cancel.clear()
            self._batch_task_ids.add(task_id)
            self._pending_start_ids.append(task_id)
            self._pending_start_set.add(task_id)
            queued_ids.append(task_id)
        self.model.update_many(
            queued_ids, status="queued", progress="Queued", active=False,
            error="", phase="queued", alreadyExists=False, bytesDone=0,
            transferredBytes=0, speed="", speedValue=0.0,
        )
        self._pump_downloads()
        self.state_changed.emit()
        self._refresh_aggregate()

    @Slot(int)
    def retry_row(self, row: int) -> None:
        record = self.model.get(row)
        if record:
            self.start_task(record["taskId"])

    @Slot(int)
    def cancel_row(self, row: int) -> None:
        record = self.model.get(row)
        task_id = str(record.get("taskId") or "")
        if task_id:
            self.cancel_task(task_id)

    @Slot(str)
    def cancel_task(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.cancel.set()
            if task_id in self._pending_start_set:
                self._pending_start_set.discard(task_id)
                self._pending_start_ids = deque(
                    pending for pending in self._pending_start_ids
                    if pending != task_id
                )
                task.state = "cancelled"
                if task.is_ui_preview:
                    file_object = task.file_object
                    handle = task.handle
                    handle.failed.emit(file_object)
                    self.task_failed.emit(task_id)
                    self._release_task(task_id)
                    return
                self.model.update(
                    task_id, status="cancelled", active=False,
                    progress="Cancelled", phase="cancelled",
                )
                self.task_failed.emit(task_id)
                batch_finished = self._finish_batch_if_idle()
                if batch_finished:
                    self.aggregate_changed.emit()
                else:
                    self._request_aggregate_refresh()
                self.state_changed.emit()
            if not task.is_ui_preview:
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
        terminal_status = self.status(task_id)
        task = self._tasks.pop(task_id, None)
        handle = self._handles.pop(task_id, None)
        if task:
            if self._key_to_task.get(task.key) == task_id:
                self._key_to_task.pop(task.key, None)
            if self._preview_key_to_task.get(task.key) == task_id:
                self._preview_key_to_task.pop(task.key, None)
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
            handle.detach(terminal_status)
            handle.setParent(None)

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
            if record.get("status") in COMPLETED_STATES
        }
        if removable and self._active == 0:
            # Preserve the completed batch before rows disappear. The summary
            # remains the stable result of the transfer instead of blinking
            # back to an empty queue.
            self._last_batch_summary = self._aggregate_summary()
        for task_id in removable:
            self._release_task(task_id)
        self.model.remove_ids(removable)
        self.state_changed.emit()
        self._refresh_aggregate()

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
        self._refresh_aggregate()

    def is_all_downloads_done(self) -> bool:
        return self._active == 0 and not self._pending_start_ids

    @Slot(str, int, int, float)
    def _progress(self, task_id: str, done: int, total: int, speed: float) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.state = "downloading"
        if task.is_ui_preview:
            return
        ratio = min(1.0, done / total) if total > 0 else 0.0
        self.model.update(
            task_id, status="downloading", phase="downloading", active=True,
            bytesDone=done, bytesTotal=total, progressValue=ratio,
            transferredBytes=done, speedValue=speed,
            progress=f"{self._pretty_bytes(done)} / {self._pretty_bytes(total)}"
                if total else self._pretty_bytes(done),
            speed=f"{self._pretty_bytes(speed)}/s",
        )
        self._track_batch_speed(task_id, done, speed)
        self.task_updated.emit(task_id)
        self._request_aggregate_refresh()

    def _track_batch_speed(
            self, task_id: str, done: int, reported_speed: float = 0.0
    ) -> None:
        """Track the combined transfer rate across concurrent downloads."""
        now = time.perf_counter()
        done = max(0, int(done or 0))
        previous = self._batch_task_bytes.get(task_id, 0)
        # A retry starts its byte counter from zero. Those bytes still crossed
        # the network, so count the new attempt instead of producing a negative
        # aggregate delta.
        delta = done - previous if done >= previous else done
        self._batch_task_bytes[task_id] = done
        self._batch_network_bytes += max(0, delta)
        self._speed_samples.append((now, self._batch_network_bytes))
        cutoff = now - 2.0
        while (
                len(self._speed_samples) > 2
                and self._speed_samples[1][0] <= cutoff):
            self._speed_samples.popleft()
        first_time, first_bytes = self._speed_samples[0]
        sample_duration = now - first_time
        if sample_duration >= 0.18:
            self._batch_speed_bps = max(
                0.0,
                (self._batch_network_bytes - first_bytes) / sample_duration,
            )
        else:
            active_speeds = sum(
                max(0.0, float(record.get("speedValue") or 0.0))
                for record in self.model._records if record.get("active")
            )
            self._batch_speed_bps = max(
                active_speeds, float(reported_speed or 0.0)
            )

    def _complete_active(self, task: SyncTask) -> None:
        previous_active = self._active
        self._active = max(0, self._active - 1)
        if not task.is_ui_preview:
            self._visible_active = max(0, self._visible_active - 1)
        self._pump_downloads()
        batch_finished = self._finish_batch_if_idle()
        if not task.is_ui_preview and self._active != previous_active:
            self.state_changed.emit()
        if batch_finished:
            # _finish_batch_if_idle() has already produced the exact final
            # cache; publish it without scanning all rows a second time.
            self.aggregate_changed.emit()
        elif self._batch_running:
            self._request_aggregate_refresh()

    def _finish_batch_if_idle(self) -> bool:
        if not self._batch_running:
            return False
        visible_pending = any(
            task_id in self._tasks
            and not self._tasks[task_id].is_ui_preview
            for task_id in self._pending_start_ids
        )
        if self._visible_active == 0 and not visible_pending:
            # Partial discovery deliberately overlaps server queries and file
            # transfers. An empty gap between two root chunks is not the end
            # of the batch: checkpoints, auto-close and the final summary must
            # wait until the source stream has finished as well.
            if self._discovery_active:
                return False
            self._batch_finished_at = time.perf_counter()
            self._elapsed_timer.stop()
            self._aggregate_timer.stop()
            self._refresh_aggregate(emit_signal=False)
            self._last_batch_summary = dict(self._aggregate_cache)
            self._batch_speed_bps = 0.0
            self._active_row_timer.stop()
            self._focused_task_id = ""
            self.activeRowChanged.emit()
            self._commit_completed_checkpoints()
            self._batch_running = False
            self.downloads_finished.emit()
            self._complete_auto_close_run()
            self._schedule_auto_clean()
            return True
        return False

    def _complete_auto_close_run(self, *, allow_empty: bool = False) -> None:
        """Close only a successful sync launched from a preset shortcut.

        The legacy item menu used an auto-closing Repo Sync dialog for preset
        actions, while ``Open Repo Sync`` created a persistent editor.  The
        application queue is shared, so track the exact task ids produced by the
        shortcut instead of tying this behaviour to global auto-clean.
        """
        if not self._auto_close_on_success:
            return
        task_ids = set(self._auto_close_task_ids)
        successful = bool(allow_empty and not task_ids) or bool(
            task_ids and all(
                self.status(task_id) in COMPLETED_STATES
                for task_id in task_ids
            )
        )
        self._auto_close_on_success = False
        self._auto_close_task_ids.clear()
        if successful:
            self.hide()

    def _commit_completed_checkpoints(self) -> None:
        remaining = []
        for checkpoint in self._sync_checkpoints:
            statuses = [
                self.status(task_id)
                for task_id in checkpoint.get("taskIds") or []
            ]
            if statuses and all(
                    status in COMPLETED_STATES for status in statuses):
                self._write_sync_checkpoint(checkpoint)
                continue
            remaining.append(checkpoint)
        self._sync_checkpoints = remaining

    def _schedule_auto_clean(self) -> None:
        if (
                self.auto_clean_enabled()
                and self.is_all_downloads_done()
                and not self._discovery_active
                and any(
            record.get("status") in COMPLETED_STATES
            for record in self.model._records
                )):
            self._auto_clean_timer.start()

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
        progress_text = (
            "Skipped" if status == "skipped"
            else "Already in repository" if status == "exists"
            else "Finished"
        )
        task.state = status
        if status == "finished" and not task.is_ui_preview:
            # The worker deliberately suppresses the redundant final progress
            # event. Account for the remaining bytes here before publishing
            # the single terminal row update.
            self._track_batch_speed(
                task_id, byte_count, byte_count / max(elapsed, 0.001)
            )
        if not task.is_ui_preview:
            self.model.update(
                task_id, status=status, active=False, progressValue=1.0,
                bytesDone=byte_count,
                bytesTotal=byte_count or task.expected_size,
                transferredBytes=(
                    0 if status in {"exists", "skipped"} else byte_count
                ),
                progress=progress_text,
                speed="", speedValue=0.0, phase="completed",
                alreadyExists=status == "exists",
            )
            self._log(
                "INFO",
                f"{task.title}: {progress_text}",
                command=task.web_path, duration=elapsed,
                size_kb=byte_count / 1024,
                details=f"Saved to: {result.get('path')}",
            )
        file_object = task.file_object
        handle = task.handle
        self._complete_active(task)
        handle.downloaded.emit(file_object)
        self.file_download_done.emit(file_object)
        self.task_finished.emit(task_id, str(result.get("path") or ""))
        self._release_task_signals(task)
        if task.is_ui_preview:
            self._release_task(task_id)

    @Slot(str, str, str)
    def _failed(self, task_id: str, error: str, stacktrace: str) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        elapsed = time.perf_counter() - task.started_at
        task.state = "failed"
        if not task.is_ui_preview:
            self.model.update(
                task_id, status="failed", active=False,
                progress="Download failed", error=error,
                speed="", phase="failed", speedValue=0.0,
            )
        self._log(
            "ERROR", f"Download failed: {task.title}: {error}",
            command=task.web_path, duration=elapsed,
            stacktrace=stacktrace,
            details=f"Destination: {task.local_path}",
        )
        file_object = task.file_object
        handle = task.handle
        self._complete_active(task)
        handle.failed.emit(file_object)
        self.task_failed.emit(task_id)
        self._release_task_signals(task)
        if task.is_ui_preview:
            self._release_task(task_id)

    @Slot(str)
    def _cancelled(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.state = "cancelled"
        if not task.is_ui_preview:
            self.model.update(
                task_id, status="cancelled", active=False,
                progress="Cancelled", speed="", phase="cancelled",
                speedValue=0.0,
            )
            self._log("WARNING", f"Download cancelled: {task.title}")
        file_object = task.file_object
        handle = task.handle
        self._complete_active(task)
        handle.failed.emit(file_object)
        self.task_failed.emit(task_id)
        self._release_task_signals(task)
        if task.is_ui_preview:
            self._release_task(task_id)

    @Property(int, notify=state_changed)
    def active_count(self) -> int:
        return self._visible_active

    @Property(int, notify=state_changed)
    def queue_count(self) -> int:
        return len(self.model._records)

    def _batch_records(self) -> list[dict]:
        if not self._batch_task_ids:
            return list(self.model._records)
        records = [
            self.model.record(task_id)
            for task_id in self._batch_task_ids
        ]
        return [record for record in records if record]

    def _compute_aggregate_summary(self) -> dict:
        if (
                not self._discovery_active
                and self._visible_active == 0
                and self._batch_finished_at > 0
                and self._last_batch_summary):
            return dict(self._last_batch_summary)
        records = (
            [] if self._discovery_active and not self._batch_task_ids
            else self._batch_records()
        )
        if not records and self._last_batch_summary and not self._discovery_active:
            return dict(self._last_batch_summary)
        total_files = len(records)
        completed = sum(
            record.get("status") in COMPLETED_STATES
            for record in records
        )
        processed = sum(
            record.get("status") in TERMINAL_STATES for record in records
        )
        failed = sum(
            record.get("status") == "failed" for record in records
        )
        cancelled = sum(
            record.get("status") == "cancelled" for record in records
        )
        bytes_total = sum(
            max(0, int(record.get("bytesTotal") or 0))
            for record in records
        )
        if self._discovery_active:
            # Discovery already knows the complete scope before thousands of
            # rows have been published to the GUI model in small chunks.
            # Keep the headline statistics stable while that publication is
            # still in progress instead of counting up 200 rows at a time.
            total_files = max(total_files, self._discovery_scope_files)
            bytes_total = max(bytes_total, self._discovery_scope_bytes)
        bytes_done = sum(
            min(
                max(0, int(record.get("bytesDone") or 0)),
                max(0, int(record.get("bytesTotal") or 0)),
            )
            for record in records
        )
        transferred = sum(
            max(0, int(record.get("transferredBytes") or 0))
            for record in records
        )
        reported_speed = sum(
            max(0.0, float(record.get("speedValue") or 0.0))
            for record in records if record.get("active")
        )
        if bytes_total > 0:
            progress = min(1.0, bytes_done / bytes_total)
        elif total_files:
            progress = min(1.0, processed / total_files)
        else:
            progress = 0.0
        ended = self._batch_finished_at or time.perf_counter()
        elapsed = (
            max(0.0, ended - self._batch_started_at)
            if self._batch_started_at else 0.0
        )
        average_speed = (
            transferred / elapsed if transferred > 0 and elapsed > 0 else 0.0
        )
        has_active_records = any(record.get("active") for record in records)
        speed = (
            max(self._batch_speed_bps, reported_speed)
            if has_active_records else average_speed
        )
        remaining = max(0, bytes_total - bytes_done)
        eta = remaining / speed if speed > 0 and remaining > 0 else 0.0
        return {
            "totalFiles": total_files,
            "completedFiles": completed,
            "processedFiles": processed,
            "failedFiles": failed,
            "cancelledFiles": cancelled,
            "bytesTotal": bytes_total,
            "bytesDone": bytes_done,
            "transferredBytes": transferred,
            "speed": speed,
            "averageSpeed": average_speed,
            "progress": progress,
            "elapsed": elapsed,
            "eta": eta,
        }

    def _aggregate_summary(self) -> dict:
        if self._aggregate_dirty:
            self._aggregate_cache = self._compute_aggregate_summary()
            self._aggregate_dirty = False
        return dict(self._aggregate_cache)

    @Slot()
    def _refresh_aggregate(self, emit_signal: bool = True) -> None:
        self._aggregate_cache = self._compute_aggregate_summary()
        self._aggregate_dirty = False
        if emit_signal:
            self.aggregate_changed.emit()

    def _mark_aggregate_dirty(self, *_args) -> None:
        self._aggregate_dirty = True

    def _request_aggregate_refresh(self) -> None:
        if not self._aggregate_timer.isActive():
            self._aggregate_timer.start()

    def _request_active_row_refresh(self) -> None:
        """Follow the current file without forcing a ListView jump per file."""
        now = time.perf_counter()
        remaining = 0.3 - (now - self._active_row_last_emit)
        if remaining <= 0:
            self._emit_active_row_changed()
        elif not self._active_row_timer.isActive():
            self._active_row_timer.start(max(1, int(remaining * 1000)))

    @Slot()
    def _emit_active_row_changed(self) -> None:
        self._active_row_last_emit = time.perf_counter()
        self.activeRowChanged.emit()

    @staticmethod
    def _pretty_duration(seconds: float) -> str:
        seconds = max(0, int(seconds or 0))
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @Property(bool, notify=configuration_changed)
    def auto_clean(self) -> bool:
        return self.auto_clean_enabled()

    @Property(float, notify=aggregate_changed)
    def overall_progress(self) -> float:
        return float(self._aggregate_summary().get("progress") or 0.0)

    @Property(int, notify=aggregate_changed)
    def batch_file_count(self) -> int:
        return int(self._aggregate_summary().get("totalFiles") or 0)

    @Property(int, notify=aggregate_changed)
    def processed_file_count(self) -> int:
        return int(self._aggregate_summary().get("processedFiles") or 0)

    @Property(int, notify=aggregate_changed)
    def completed_file_count(self) -> int:
        return int(self._aggregate_summary().get("completedFiles") or 0)

    @Property(int, notify=aggregate_changed)
    def failed_file_count(self) -> int:
        return int(self._aggregate_summary().get("failedFiles") or 0)

    @Property(int, notify=aggregate_changed)
    def cancelled_file_count(self) -> int:
        return int(self._aggregate_summary().get("cancelledFiles") or 0)

    @Property(int, notify=activeRowChanged)
    def active_row(self) -> int:
        return int(self.model._rows.get(self._focused_task_id, -1))

    @Property(str, notify=aggregate_changed)
    def processed_size_text(self) -> str:
        return self._pretty_bytes(
            self._aggregate_summary().get("bytesDone") or 0
        )

    @Property(str, notify=aggregate_changed)
    def total_size_text(self) -> str:
        return self._pretty_bytes(
            self._aggregate_summary().get("bytesTotal") or 0
        )

    @Property(str, notify=aggregate_changed)
    def remaining_size_text(self) -> str:
        summary = self._aggregate_summary()
        remaining = max(
            0,
            int(summary.get("bytesTotal") or 0)
            - int(summary.get("bytesDone") or 0),
        )
        return self._pretty_bytes(remaining)

    @Property(str, notify=aggregate_changed)
    def transferred_size_text(self) -> str:
        return self._pretty_bytes(
            self._aggregate_summary().get("transferredBytes") or 0
        )

    @Property(str, notify=aggregate_changed)
    def aggregate_speed_text(self) -> str:
        speed = self._aggregate_summary().get("speed") or 0
        return f"{self._pretty_bytes(speed)}/s" if speed else "—"

    @Property(str, notify=aggregate_changed)
    def elapsed_text(self) -> str:
        return self._pretty_duration(
            self._aggregate_summary().get("elapsed") or 0
        )

    @Property(str, notify=aggregate_changed)
    def eta_text(self) -> str:
        eta = self._aggregate_summary().get("eta") or 0
        return self._pretty_duration(eta) if eta else "—"

    @Property(bool, notify=state_changed)
    def discovery_active(self) -> bool:
        return self._discovery_active

    @Property(str, notify=state_changed)
    def discovery_state(self) -> str:
        return self._discovery_state

    @Property(str, notify=state_changed)
    def discovery_error(self) -> str:
        return self._discovery_error

    @Property(str, notify=state_changed)
    def discovery_mode(self) -> str:
        return self._discovery_mode

    @Property(int, notify=aggregate_changed)
    def discovery_processed_roots(self) -> int:
        return self._discovery_processed_roots

    @Property(int, notify=aggregate_changed)
    def discovery_total_roots(self) -> int:
        return self._discovery_total_roots

    def _begin_discovery(
        self, preset_name: str, only_updates: bool, mode: str,
    ) -> tuple[int, float]:
        self._discovery_generation += 1
        self._discovery_cancel.set()
        self._discovery_cancel = threading.Event()
        self._discovery_active = True
        self._discovery_state = "discovery"
        self._discovery_error = ""
        self._discovery_mode = (
            "partial" if str(mode or "").lower() == "partial" else "full"
        )
        self._discovery_scope_files = 0
        self._discovery_scope_bytes = 0
        self._discovery_processed_roots = 0
        self._discovery_total_roots = 0
        self._partial_publication_entries.clear()
        self._partial_publication_running = False
        self._partial_source_finished = False
        self._partial_checkpoint = {}
        self._partial_task_ids.clear()
        started = time.perf_counter()
        if not self._batch_running:
            self._begin_batch(started)
        self._partial_started = started
        self._discovery_metadata = (preset_name, only_updates, started)
        self._refresh_aggregate()
        return self._discovery_generation, started

    def start_sobject_sync(
        self, sobject, preset_name: str = "default", only_updates: bool = False,
        preset_data: dict | None = None,
        auto_close_on_success: bool = False,
        scope_mode: str | None = None,
        partial_chunk_size: int | None = None,
    ) -> None:
        from thlib.environment import env_inst
        if not sobject or self._discovery_active:
            return
        self._auto_close_on_success = bool(auto_close_on_success)
        self._auto_close_task_ids.clear()
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        mode = scope_mode or self.configured_scope_mode()
        generation, started = self._begin_discovery(
            preset_name, only_updates, mode,
        )
        self._log(
            "API", f"Discovering repository files: {preset_name}",
            details=str(sobject.get_search_key()),
        )
        if self._discovery_mode == "partial":
            worker = env_inst.server_pool.add_task(
                self._discover_files_partial, sobject, preset_name,
                only_updates, preset_data, generation, self._discovery_cancel,
            )
            worker.connect_progress(self._publish_discovery_progress)
            worker.result.connect(
                self._partial_discovery_finished,
                Qt.ConnectionType.QueuedConnection,
            )
        else:
            worker = env_inst.server_pool.add_task(
                self._discover_files, sobject, preset_name, only_updates,
                preset_data, generation,
            )
            worker.connect_progress(self._publish_discovery_progress)
            worker.add_result_data((preset_name, only_updates, started))
            worker.result.connect(
                self._publish_discovery,
                Qt.ConnectionType.QueuedConnection,
            )
        worker.error.connect(
            self._discovery_worker_error,
            Qt.ConnectionType.QueuedConnection,
        )
        self._discovery_worker = worker
        worker.start()
        self.state_changed.emit()

    def start_stype_sync(
        self, stype, preset_name: str = "default", only_updates: bool = False,
        preset_data: dict | None = None,
        auto_close_on_success: bool = False,
        scope_mode: str | None = None,
        partial_chunk_size: int | None = None,
    ) -> None:
        """Discover files for every sObject of a Search Type.

        This is the QML equivalent of ``Ui_repoSyncDialog`` opened from a
        Search Tab without one concrete sObject.
        """
        from thlib.environment import env_inst
        if not stype or self._discovery_active:
            return
        self._auto_close_on_success = bool(auto_close_on_success)
        self._auto_close_task_ids.clear()
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        mode = scope_mode or self.configured_scope_mode()
        generation, started = self._begin_discovery(
            preset_name, only_updates, mode,
        )
        try:
            details = str(stype.get_code())
        except AttributeError:
            details = ""
        self._log(
            "API", f"Discovering Search Type repository files: {preset_name}",
            details=details,
        )
        if self._discovery_mode == "partial":
            worker = env_inst.server_pool.add_task(
                self._discover_stype_files_partial, stype, preset_name,
                only_updates, preset_data,
                max(1, min(250, int(
                    partial_chunk_size or self.configured_partial_chunk_size()
                ))),
                env_inst.server_pool.max_threads,
                generation, self._discovery_cancel,
            )
            worker.connect_progress(self._publish_discovery_progress)
            worker.result.connect(
                self._partial_discovery_finished,
                Qt.ConnectionType.QueuedConnection,
            )
        else:
            worker = env_inst.server_pool.add_task(
                self._discover_stype_files, stype, preset_name, only_updates,
                preset_data, env_inst.server_pool.max_threads, generation,
            )
            worker.connect_progress(self._publish_discovery_progress)
            worker.add_result_data((preset_name, only_updates, started))
            worker.result.connect(
                self._publish_discovery,
                Qt.ConnectionType.QueuedConnection,
            )
        worker.error.connect(
            self._discovery_worker_error,
            Qt.ConnectionType.QueuedConnection,
        )
        self._discovery_worker = worker
        worker.start()
        self.state_changed.emit()

    @staticmethod
    def _preset_state(value) -> bool:
        """Interpret Repository Sync check states strictly."""
        if value is True:
            return True
        if value is False or value is None:
            return False
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.strip().lower() in {
                "1", "2", "true", "on", "yes", "checked", "enabled",
            }
        return False

    @classmethod
    def _preset_items(cls, mapping: dict, suffix: str, enabled=False) -> dict:
        result = {}
        for key, value in (mapping or {}).items():
            if not str(key).endswith(suffix) or not isinstance(value, dict):
                continue
            if not enabled or cls._preset_state(value.get("state")):
                result[str(key).removesuffix(suffix)] = value
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
    def _load_stype_preset(cls, stype, preset_name: str) -> dict:
        class _STypeSource:
            def get_stype(self):
                return stype

        return cls._load_preset(_STypeSource(), preset_name)

    @classmethod
    def _collect_sobject(
        cls, sobject, preset: dict, files: dict,
        include_versions: bool | None = None,
    ) -> None:
        cls._collect_sobjects(
            [sobject], preset, files, include_versions=include_versions,
        )

    @classmethod
    def _collect_sobjects(
        cls, sobjects, preset: dict, files: dict,
        include_versions: bool | None = None,
    ) -> None:
        """Collect one hierarchy level at a time instead of N+1 queries.

        Search Type sync may start with hundreds of parent sObjects.  Calling
        ``get_related_sobjects`` once for every parent made discovery grow with
        the number of roots and every nested branch.  Direct schema relations
        can be queried for the complete parent set in one batch; unusual
        instance relations retain the native per-parent fallback.
        """
        sobjects = cls._unique_sobjects(sobjects)
        if not sobjects:
            return
        if include_versions is None:
            include_versions = bool(preset.get("get_versions"))
        pipelines = cls._preset_items(preset, ":{pp}")
        builtins = cls._preset_items(preset, ":{b}", True)
        process_maps = [
            cls._preset_items(value.get("sub") or {}, ":{pr}", True)
            for value in pipelines.values()
        ] or [{}]
        enabled = set(builtins)
        for process_map in process_maps:
            enabled.update(process_map)
        for sobject in sobjects:
            for process_name, process_object in (
                sobject.get_all_processes() or {}
            ).items():
                if process_name not in enabled:
                    continue
                for context_object in (
                    process_object.get_contexts() or {}
                ).values():
                    snapshots = list(
                        (context_object.get_versionless() or {}).values()
                    )
                    if include_versions:
                        snapshots.extend(
                            (context_object.get_versions() or {}).values()
                        )
                    for snapshot in snapshots:
                        for file_object in snapshot.get_files_objects() or []:
                            entry = cls._prepare_file_object(
                                file_object, process_name
                            )
                            files[entry.key] = entry

        children = cls._preset_items(preset, ":{s}", True)
        stype = sobjects[0].get_stype()
        project = stype.get_project()
        for child_code, child_preset in children.items():
            child_stype = project.stypes.get(child_code)
            if not child_stype:
                continue
            related = cls._query_related_sobjects_batch(
                sobjects, child_stype, stype,
            )
            cls._collect_sobjects(
                related, child_preset.get("sub") or {}, files,
                include_versions=include_versions,
            )

    @staticmethod
    def _sobject_identity(sobject) -> str:
        try:
            search_key = str(sobject.get_search_key() or "")
        except (AttributeError, TypeError):
            search_key = ""
        if search_key:
            return search_key
        try:
            code = str(sobject.get_code() or "")
        except (AttributeError, TypeError):
            code = ""
        return code or f"object:{id(sobject)}"

    @classmethod
    def _unique_sobjects(cls, sobjects) -> list:
        unique = {}
        values = sobjects.values() if isinstance(sobjects, dict) else sobjects
        for sobject in values or []:
            if sobject is not None:
                unique.setdefault(cls._sobject_identity(sobject), sobject)
        return list(unique.values())

    @staticmethod
    def _sobject_relation_value(sobject, column: str):
        column = str(column or "code")
        if column == "code":
            try:
                return sobject.get_code()
            except AttributeError:
                return None
        try:
            return sobject.get_value(column)
        except AttributeError:
            try:
                return sobject.get_info(column)
            except (AttributeError, TypeError):
                return None

    @classmethod
    def _query_related_sobjects_batch(
        cls, parents: list, child_stype, parent_stype,
    ) -> list:
        """Resolve direct children in batched TACTIC queries.

        Schema-backed code, search_type, and instance relations are combined
        by their declared columns. Custom relations retain the native object
        API fallback.
        """
        relation = None
        try:
            relation = parent_stype.get_schema().get_child(
                child_stype.get_code(), parent_stype.get_code(),
            )
        except (AttributeError, KeyError, TypeError, ValueError):
            relation = None

        relationship = (
            str(relation.get("relationship") or "")
            if isinstance(relation, dict) else ""
        )
        if relationship == "instance":
            instance_type = str(relation.get("instance_type") or "")
            instance_parent_relation = None
            instance_child_relation = None
            try:
                instance_schema = parents[0].get_schema(instance_type)
                parent_code = parent_stype.get_code()
                child_code = child_stype.get_code()
                if parent_code == child_code:
                    instance_parent_relation = (
                        instance_schema.get_child_instance(
                            instance_type, parent_code,
                        )
                    )
                else:
                    instance_parent_relation = (
                        instance_schema.get_parent_instance(
                            instance_type, parent_code,
                        )
                    )
                instance_child_relation = (
                    instance_schema.get_parent_instance(
                        instance_type, child_code,
                    )
                )
            except (AttributeError, KeyError, TypeError, ValueError):
                instance_parent_relation = None
                instance_child_relation = None
            if (
                instance_type
                and isinstance(instance_parent_relation, dict)
                and isinstance(instance_child_relation, dict)
            ):
                instance_child_column = str(
                    instance_child_relation.get("from_col")
                    or f"{child_stype.get_code().split('/')[-1]}_code"
                )
                instance_parent_column = str(
                    instance_parent_relation.get("from_col")
                    or f"{parent_stype.get_code().split('/')[-1]}_code"
                )
                parent_values = []
                seen_values = set()
                for parent in parents:
                    value = str(parent.get_code() or "")
                    if value and value not in seen_values:
                        seen_values.add(value)
                        parent_values.append(value)
                if parent_values:
                    import thlib.tactic_classes as tc

                    project = child_stype.get_project()
                    child_values = []
                    seen_children = set()
                    for offset in range(0, len(parent_values), 500):
                        values = parent_values[offset:offset + 500]
                        relation_filter = (
                            (instance_parent_column, values[0])
                            if len(values) == 1 else (
                                instance_parent_column, "in",
                                "|".join(values),
                            )
                        )
                        result = tc.get_sobjects(
                            instance_type, [relation_filter],
                            project_code=project.get_code(),
                            include_snapshots=False,
                            include_info=False,
                            include_total_count=False,
                        )
                        result = (
                            result[0] if isinstance(result, tuple) else result
                        )
                        for instance in (result or {}).values():
                            child_value = str(
                                cls._sobject_relation_value(
                                    instance, instance_child_column,
                                ) or ""
                            )
                            if (
                                child_value
                                and child_value not in seen_children
                            ):
                                seen_children.add(child_value)
                                child_values.append(child_value)
                    related = []
                    for offset in range(0, len(child_values), 500):
                        values = child_values[offset:offset + 500]
                        child_filter = (
                            ("code", values[0])
                            if len(values) == 1
                            else ("code", "in", "|".join(values))
                        )
                        result = tc.get_sobjects(
                            child_stype.get_code(), [child_filter],
                            project_code=project.get_code(),
                            get_all_snapshots=True,
                            include_info=False,
                            include_total_count=False,
                        )
                        result = (
                            result[0] if isinstance(result, tuple) else result
                        )
                        related.extend((result or {}).values())
                    return cls._unique_sobjects(related)

        if relationship in {"code", "search_type"}:
            if relationship == "search_type":
                child_column = str(
                    relation.get("from_col") or "search_code"
                )
            else:
                parent_name = str(
                    parent_stype.get_code() or ""
                ).split("/")[-1]
                child_column = str(
                    relation.get("from_col") or f"{parent_name}_code"
                )
            parent_column = str(relation.get("to_col") or "code")
            parent_values = []
            seen_values = set()
            for parent in parents:
                value = cls._sobject_relation_value(parent, parent_column)
                value = str(value or "")
                if value and value not in seen_values:
                    seen_values.add(value)
                    parent_values.append(value)
            if parent_values:
                import thlib.tactic_classes as tc

                project = child_stype.get_project()
                related = []
                # Keep each IN filter bounded while retaining one query per
                # hierarchy level for ordinary project-sized scopes.
                for offset in range(0, len(parent_values), 500):
                    values = parent_values[offset:offset + 500]
                    relation_filter = (
                        (child_column, values[0])
                        if len(values) == 1
                        else (child_column, "in", "|".join(values))
                    )
                    result = tc.get_sobjects(
                        child_stype.get_code(), [relation_filter],
                        project_code=project.get_code(),
                        get_all_snapshots=True,
                        include_info=False,
                        include_total_count=False,
                    )
                    result = result[0] if isinstance(result, tuple) else result
                    related.extend((result or {}).values())
                return cls._unique_sobjects(related)

        related = []
        for parent in parents:
            result, _query_info = parent.get_related_sobjects(
                child_stype=child_stype,
                parent_stype=parent_stype,
                get_all_snapshots=True,
            )
            related.extend((result or {}).values())
        return cls._unique_sobjects(related)

    @classmethod
    def _discover_files(
        cls, sobject, preset_name: str, only_updates: bool,
        preset_data: dict | None = None, generation: int = 0,
        progress_signal=None,
    ) -> tuple[list]:
        preset = dict(
            preset_data
            if preset_data is not None
            else cls._load_preset(sobject, preset_name)
        )
        stype = sobject.get_stype()
        group_path = "ui_search/{}/{}/{}/sobjects_conf".format(
            stype.project.info["type"],
            stype.project.info["code"],
            stype.get_code().split("/")[1],
        )
        filters = None
        code = str(sobject.get_code() or "")
        sync_state = cls._read_sync_state(group_path, [code])
        if only_updates:
            last_sync = sync_state.get(code)
            if last_sync:
                filters = [("timestamp", "is after", last_sync)]
        cls._emit_discovery_progress(
            progress_signal, generation, [], 0, 1, 0, 0, "snapshots",
        )
        sobject.update_snapshots(filters=filters, force=True)
        files: dict[str, tuple] = {}
        cls._collect_sobject(sobject, preset, files)
        cls._emit_discovery_progress(
            progress_signal, generation, [], 1, 1, len(files),
            sum(max(0, int(entry.expected_size or 0))
                for entry in files.values()),
            "snapshots",
        )
        checkpoint = cls._checkpoint(group_path, [code])
        # OperationWorker appends result metadata to tuple results.
        return (list(files.values()), checkpoint)

    @classmethod
    def _discover_stype_files(
        cls, stype, preset_name: str, only_updates: bool,
        preset_data: dict | None = None, max_workers: int = 1,
        generation: int = 0, progress_signal=None,
    ) -> tuple[list]:
        result = cls._discover_stype_files_partial(
            stype, preset_name, only_updates, preset_data, 0, max_workers,
            generation, threading.Event(), progress_signal,
        )
        return (result["entries"], result["checkpoint"])

    @staticmethod
    def _emit_discovery_progress(
        progress_signal, generation: int, entries, processed_roots: int,
        total_roots: int, discovered_files: int, discovered_bytes: int,
        stage: str = "streaming",
    ) -> None:
        if progress_signal is None:
            return
        progress_signal.emit({
            "generation": int(generation),
            "entries": list(entries or []),
            "processedRoots": max(0, int(processed_roots or 0)),
            "totalRoots": max(0, int(total_roots or 0)),
            "discoveredFiles": max(0, int(discovered_files or 0)),
            "discoveredBytes": max(0, int(discovered_bytes or 0)),
            "stage": str(stage or "streaming"),
        })

    @classmethod
    def _discover_files_partial(
        cls, sobject, preset_name: str, only_updates: bool,
        preset_data: dict | None, generation: int,
        cancel_event: threading.Event, progress_signal=None,
    ) -> dict:
        """Stream the one-object scope through the partial-mode contract.

        A single root may still own a deep hierarchy, but keeping this path
        separate makes its publication/download lifecycle identical to Search
        Type streaming without changing the proven full-scope implementation.
        """
        if cancel_event.is_set():
            return {"generation": generation, "cancelled": True}
        files, checkpoint = cls._discover_files(
            sobject, preset_name, only_updates, preset_data,
        )
        if cancel_event.is_set():
            return {"generation": generation, "cancelled": True}
        discovered_bytes = sum(
            max(0, int(entry.expected_size or 0)) for entry in files
        )
        cls._emit_discovery_progress(
            progress_signal, generation, files, 1, 1,
            len(files), discovered_bytes,
        )
        return {
            "generation": generation,
            "checkpoint": checkpoint,
            "processedRoots": 1,
            "totalRoots": 1,
            "discoveredFiles": len(files),
            "discoveredBytes": discovered_bytes,
        }

    @classmethod
    def _discover_stype_files_partial(
        cls, stype, preset_name: str, only_updates: bool,
        preset_data: dict | None, chunk_size: int, max_workers: int,
        generation: int, cancel_event: threading.Event,
        progress_signal=None,
    ) -> dict:
        """Discover a fixed root scope in parallel XMLRPC waves."""
        import thlib.tactic_classes as tc

        project = stype.get_project()
        project_code = project.get_code()
        preset = dict(
            preset_data
            if preset_data is not None
            else cls._load_stype_preset(stype, preset_name)
        )
        group_path = "ui_search/{}/{}/{}/sobjects_conf".format(
            project.info["type"], project.info["code"],
            stype.get_code().split("/")[1],
        )
        requested_chunk_size = int(chunk_size or 0)
        max_workers = max(1, min(32, int(max_workers or 1)))
        cls._emit_discovery_progress(
            progress_signal, generation, [], 0, 0, 0, 0, "objects",
        )
        scope_result = tc.get_sobjects(
            stype.get_code(), [], order_bys=["code"],
            project_code=project_code, include_snapshots=False,
            include_info=False, include_total_count=False,
        )
        if scope_result is None:
            raise RuntimeError("TACTIC returned no Repository Sync scope")
        scope_map = (
            scope_result[0]
            if isinstance(scope_result, tuple) else scope_result
        ) or {}
        root_codes = []
        seen_codes = set()
        for root in scope_map.values():
            code = str(root.get_code() or "")
            if code and code not in seen_codes:
                seen_codes.add(code)
                root_codes.append(code)
        total_roots = len(root_codes)
        cls._emit_discovery_progress(
            progress_signal, generation, [], 0, total_roots, 0, 0, "scope",
        )
        chunk_size = (
            requested_chunk_size
            if requested_chunk_size > 0
            else (total_roots + max_workers - 1) // max_workers
        )
        chunk_size = max(1, min(250, chunk_size))
        processed_roots = 0
        all_codes: list[str] = []
        emitted_keys: set[str] = set()
        all_entries: list[PreparedSyncEntry] = []
        discovered_files = 0
        discovered_bytes = 0

        def discover_page(page_codes: list[str]) -> dict:
            if cancel_event.is_set():
                return {"codes": [], "files": {}}
            page_filter = (
                ("code", page_codes[0])
                if len(page_codes) == 1
                else ("code", "in", "|".join(page_codes))
            )
            snapshot_timestamps = []
            if only_updates:
                sync_state = cls._read_sync_state(group_path, page_codes)
                snapshot_timestamps = [
                    (code, timestamp)
                    for code, timestamp in sync_state.items() if timestamp
                ]
            root_result = tc.get_sobjects(
                stype.get_code(), [page_filter], order_bys=["code"],
                project_code=project_code, get_all_snapshots=True,
                include_info=False, include_total_count=False,
                snapshot_timestamps=snapshot_timestamps,
            )
            root_map = (
                root_result[0]
                if isinstance(root_result, tuple) else root_result
            ) or {}
            roots = list(root_map.values())
            codes = [
                str(root.get_code() or "") for root in roots
                if root.get_code()
            ]
            missing_codes = set(page_codes).difference(codes)
            if missing_codes:
                missing = ", ".join(sorted(missing_codes)[:5])
                raise RuntimeError(
                    "TACTIC omitted {0} Repository Sync objects: {1}".format(
                        len(missing_codes), missing,
                    )
                )
            if cancel_event.is_set():
                return {"codes": [], "files": {}}

            page_files: dict[str, PreparedSyncEntry] = {}
            cls._collect_sobjects(roots, preset, page_files)
            return {
                "codes": codes,
                "files": page_files,
            }

        pages = [
            root_codes[offset:offset + chunk_size]
            for offset in range(0, total_roots, chunk_size)
        ]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for wave_start in range(0, len(pages), max_workers):
                if cancel_event.is_set():
                    break
                wave = pages[wave_start:wave_start + max_workers]
                futures = [
                    executor.submit(discover_page, page_codes)
                    for page_codes in wave
                ]
                for future in futures:
                    page = future.result()
                    if cancel_event.is_set():
                        break
                    codes = page["codes"]
                    new_entries = []
                    for key, entry in page["files"].items():
                        if key in emitted_keys:
                            continue
                        emitted_keys.add(key)
                        new_entries.append(entry)
                        discovered_bytes += max(
                            0, int(entry.expected_size or 0)
                        )
                    discovered_files += len(new_entries)
                    all_entries.extend(new_entries)
                    all_codes.extend(codes)
                    processed_roots += len(codes)
                    cls._emit_discovery_progress(
                        progress_signal, generation, new_entries,
                        processed_roots, total_roots, discovered_files,
                        discovered_bytes,
                    )

        return {
            "generation": generation,
            "cancelled": cancel_event.is_set(),
            "checkpoint": cls._checkpoint(group_path, all_codes),
            "entries": all_entries,
            "processedRoots": processed_roots,
            "totalRoots": total_roots or processed_roots,
            "discoveredFiles": discovered_files,
            "discoveredBytes": discovered_bytes,
        }

    @staticmethod
    def _checkpoint(group_path: str, codes) -> dict:
        return {
            "groupPath": str(group_path or ""),
            "codes": sorted({str(code) for code in codes if code}),
            "timestamp": datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
        }

    @staticmethod
    def _read_sync_state(group_path: str, codes=()) -> dict:
        from thlib.environment import env_read_config

        state = env_read_config(
            filename="repository_sync_state", unique_id=group_path,
            long_abs_path=True,
        ) or {}
        if not isinstance(state, dict):
            return {}
        requested = {str(code) for code in codes if code}
        return {
            str(code): timestamp
            for code, timestamp in state.items()
            if timestamp and (not requested or str(code) in requested)
        }

    @staticmethod
    def _write_sync_checkpoint(checkpoint: dict) -> None:
        from thlib.environment import env_read_config, env_write_config

        group_path = str(checkpoint.get("groupPath") or "")
        timestamp = str(checkpoint.get("timestamp") or "")
        if not group_path or not timestamp:
            return
        state = env_read_config(
            filename="repository_sync_state", unique_id=group_path,
            long_abs_path=True,
        ) or {}
        if not isinstance(state, dict):
            state = {}
        for code in checkpoint.get("codes") or []:
            state[str(code)] = timestamp
        env_write_config(
            state, filename="repository_sync_state", unique_id=group_path,
            long_abs_path=True,
        )

    @Slot(object)
    def _publish_discovery_progress(self, payload) -> None:
        payload = dict(payload or {})
        if int(payload.get("generation") or -1) != self._discovery_generation:
            return
        self._discovery_processed_roots = max(
            self._discovery_processed_roots,
            int(payload.get("processedRoots") or 0),
        )
        self._discovery_total_roots = max(
            self._discovery_total_roots,
            int(payload.get("totalRoots") or 0),
        )
        self._discovery_scope_files = max(
            self._discovery_scope_files,
            int(payload.get("discoveredFiles") or 0),
        )
        self._discovery_scope_bytes = max(
            self._discovery_scope_bytes,
            int(payload.get("discoveredBytes") or 0),
        )
        self._discovery_state = str(payload.get("stage") or "streaming")
        self._refresh_aggregate()
        self.state_changed.emit()
        entries = payload.get("entries") or []
        if self._discovery_mode != "partial" or not entries:
            return
        self._partial_publication_entries.extend(entries)
        if not self._partial_publication_running:
            self._partial_publication_running = True
            self._partial_publication_requested.emit()

    def _publish_partial_queue_chunk(self) -> None:
        if self._discovery_mode != "partial":
            self._partial_publication_entries.clear()
            self._partial_publication_running = False
            return
        entries = [
            self._partial_publication_entries.popleft()
            for _index in range(min(200, len(self._partial_publication_entries)))
        ]
        stale_ids = {
            task_id
            for entry in entries
            for task_id in [self._key_to_task.get(entry.key)]
            if task_id and self.status(task_id) in TERMINAL_STATES
        }
        for task_id in stale_ids:
            self._release_task(task_id)
        self.model.remove_ids(stale_ids)
        records = []
        task_ids = []
        for entry in entries:
            handle, record = self._schedule_prepared_entry(
                entry, append_model=False, write_log=False,
            )
            self._partial_task_ids.add(handle.task_id)
            self._auto_close_task_ids.add(handle.task_id)
            if record:
                records.append(record)
                task_ids.append(handle.task_id)
        if records:
            self.model.extend(records)
        if task_ids:
            self._start_task_ids(task_ids)
        if self._partial_publication_entries:
            self._partial_publication_requested.emit()
            return
        self._partial_publication_running = False
        self._maybe_finish_partial_discovery()

    @Slot(object)
    def _partial_discovery_finished(self, result) -> None:
        result = dict(result or {})
        if int(result.get("generation") or -1) != self._discovery_generation:
            return
        self._partial_source_finished = True
        self._partial_checkpoint = dict(result.get("checkpoint") or {})
        self._discovery_processed_roots = max(
            self._discovery_processed_roots,
            int(result.get("processedRoots") or 0),
        )
        self._discovery_total_roots = max(
            self._discovery_total_roots,
            int(result.get("totalRoots") or 0),
        )
        self._discovery_scope_files = max(
            self._discovery_scope_files,
            int(result.get("discoveredFiles") or 0),
        )
        self._discovery_scope_bytes = max(
            self._discovery_scope_bytes,
            int(result.get("discoveredBytes") or 0),
        )
        if result.get("cancelled"):
            self._discovery_state = "cancelled"
        self._maybe_finish_partial_discovery()

    def _maybe_finish_partial_discovery(self) -> None:
        if (
            not self._partial_source_finished
            or self._partial_publication_running
            or self._partial_publication_entries
        ):
            return
        cancelled = self._discovery_state == "cancelled"
        checkpoint = dict(self._partial_checkpoint)
        checkpoint["taskIds"] = sorted(self._partial_task_ids)
        if checkpoint.get("taskIds") and not cancelled:
            self._sync_checkpoints.append(checkpoint)
        elif checkpoint and not cancelled:
            self._write_sync_checkpoint(checkpoint)
        self._discovery_active = False
        self._discovery_worker = None
        if not cancelled:
            self._discovery_state = "completed"
        preset_name, only_updates, started = self._discovery_metadata
        self._log(
            "INFO" if not cancelled else "WARNING",
            (
                "Partial repository discovery finished"
                if not cancelled else "Partial repository discovery cancelled"
            ),
            duration=time.perf_counter() - started,
            details=(
                f"Preset: {preset_name}; updates only: {only_updates}; "
                f"roots: {self._discovery_processed_roots}/"
                f"{self._discovery_total_roots}; "
                f"files: {self._discovery_scope_files}"
            ),
        )
        if cancelled:
            self._auto_close_on_success = False
            self._auto_close_task_ids.clear()
        if not checkpoint.get("taskIds") and not cancelled:
            self._complete_auto_close_run(allow_empty=True)
        self.state_changed.emit()
        self._refresh_aggregate()
        if self._finish_batch_if_idle():
            self.aggregate_changed.emit()

    @Slot()
    def cancel_discovery(self) -> None:
        if not self._discovery_active or self._discovery_mode != "partial":
            return
        self._discovery_cancel.set()
        self._discovery_state = "cancelling"
        self.state_changed.emit()

    @Slot(object)
    def _publish_discovery(self, result) -> None:
        files, checkpoint, metadata = result
        preset_name, only_updates, started = metadata
        self._discovery_scope_files = len(files)
        self._discovery_scope_bytes = sum(
            max(0, int(entry.expected_size or 0)) for entry in files
        )
        self._refresh_aggregate()
        # Replace terminal entries from an earlier run in one model operation.
        # Without this, path deduplication made a repeated sync skip originals
        # while newly generated JPEG/PNG previews were still queued.
        stale_ids = {
            task_id
            for entry in files
            for task_id in [self._key_to_task.get(entry.key)]
            if task_id and self.status(task_id) in TERMINAL_STATES
        }
        for task_id in stale_ids:
            self._release_task(task_id)
        self.model.remove_ids(stale_ids)
        self._discovery_active = True
        self._discovery_state = "publishing"
        self._discovery_error = ""
        self._publication_entries = deque(files)
        self._publication_handles = []
        self._publication_checkpoint = dict(checkpoint or {})
        self._publication_started = started
        self._publication_count = len(files)
        self._discovery_metadata = (preset_name, only_updates, started)
        self._publish_discovery_chunk()

    def _publish_discovery_chunk(self) -> None:
        records = []
        for _index in range(min(200, len(self._publication_entries))):
            entry = self._publication_entries.popleft()
            handle, record = self._schedule_prepared_entry(
                entry, append_model=False, write_log=False
            )
            self._publication_handles.append(handle)
            if record:
                records.append(record)
                self._batch_task_ids.add(handle.task_id)
        self.model.extend(records)
        if self._publication_entries:
            self.state_changed.emit()
            self._refresh_aggregate()
            self._discovery_publication_requested.emit()
            return
        preset_name, only_updates, started = self._discovery_metadata
        checkpoint = dict(self._publication_checkpoint)
        checkpoint["taskIds"] = sorted({
            handle.task_id for handle in self._publication_handles
        })
        self._auto_close_task_ids = set(checkpoint["taskIds"])
        if checkpoint.get("taskIds"):
            self._sync_checkpoints.append(checkpoint)
        else:
            self._write_sync_checkpoint(checkpoint)
        self._discovery_active = False
        self._discovery_worker = None
        self._discovery_state = "completed"
        elapsed = time.perf_counter() - started
        self._log(
            "INFO",
            f"Repository discovery finished: {self._publication_count} files",
            duration=elapsed,
            details=f"Preset: {preset_name}; updates only: {only_updates}",
        )
        self.start_checked()
        if not checkpoint["taskIds"]:
            self._complete_auto_close_run(allow_empty=True)
        self.state_changed.emit()
        if self._finish_batch_if_idle():
            self.aggregate_changed.emit()

    @Slot(object)
    def _discovery_worker_error(self, error) -> None:
        preset_name, _only_updates, started = self._discovery_metadata
        self._discovery_active = False
        self._discovery_worker = None
        self._discovery_cancel.set()
        self._partial_publication_entries.clear()
        self._partial_publication_running = False
        payload = error[0] if isinstance(error, tuple) else error
        self._discovery_state = "failed"
        self._discovery_error = str(payload)
        self._auto_close_on_success = False
        self._auto_close_task_ids.clear()
        self._log(
            "ERROR", f"Repository discovery failed: {preset_name}",
            duration=time.perf_counter() - started,
            stacktrace=str(payload),
        )
        self.state_changed.emit()
        if self._finish_batch_if_idle():
            self.aggregate_changed.emit()

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
        self._discovery_cancel.set()
        if self._discovery_worker is not None:
            try:
                self._discovery_worker.cancel()
            except RuntimeError:
                pass
            self._discovery_worker = None
        self._preset_store.shutdown()

        self._active = 0
        self._pending_start_ids.clear()
        self._pending_start_set.clear()
        self._elapsed_timer.stop()
        self._aggregate_timer.stop()
        self._active_row_timer.stop()
        self._auto_clean_timer.stop()
        self._discovery_active = False
        self._discovery_state = "cancelled"
