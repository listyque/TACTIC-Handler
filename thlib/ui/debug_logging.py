"""Structured diagnostics compatible with the original TACTIC-Handler log API."""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import datetime
import functools
import inspect
import json
import logging
from pathlib import Path
import re
import sys
import threading
import time
import traceback
from typing import Any
from urllib.error import URLError

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    QTimer,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication

from thlib.environment import env_read_config, env_write_config
from thlib.request_retry import (
    is_transient_read_error,
    transient_error_reporting_deferred,
)
from .request_metrics import request_metrics


LEVELS = (
    "LOG", "INFO", "WARNING", "MISSING", "EXCEPTION", "ERROR", "CRITICAL", "API",
)
LEVEL_ALIASES = {
    "[ LOG ]": "LOG",
    "[ INF ]": "INFO",
    "[ WRN ]": "WARNING",
    "[ EXC ]": "EXCEPTION",
    "[ ERR ]": "ERROR",
    "[ CRL ]": "CRITICAL",
}

# Session files are optimized for append-only machine storage.  The UI model
# continues to use the descriptive ENTRY_ROLES names; only the JSONL boundary
# translates them to compact keys.
SESSION_SCHEMA_VERSION = 1
SESSION_FIELD_KEYS = {
    "eventId": "id",
    "timestamp": "t",
    "level": "l",
    "message": "m",
    "module": "o",
    "functionName": "f",
    "line": "n",
    "group": "g",
    "source": "s",
    "command": "c",
    "stacktrace": "x",
    "duration": "d",
    "sizeKb": "z",
    "thread": "h",
    "details": "e",
}
SESSION_KEY_FIELDS = {
    key: field for field, key in SESSION_FIELD_KEYS.items()
}

# These calls only prepare local client state and can occur for every short-
# lived TACTIC server object. Successful calls add no diagnostic value, while
# their failures must still retain the runtime command and traceback.
SILENT_SERVER_SUCCESSES = frozenset({"set_server"})


class MappingListModel(QAbstractListModel):
    def __init__(self, roles: tuple[str, ...]) -> None:
        super().__init__()
        self._roles = roles
        self._role_ids = {
            role: Qt.UserRole + index + 1
            for index, role in enumerate(roles)
        }
        self._records: list[dict] = []

    def roleNames(self) -> dict[int, bytes]:
        return {
            role_id: role.encode("utf-8")
            for role, role_id in self._role_ids.items()
        }

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._records):
            return None
        role_name = next(
            (name for name, role_id in self._role_ids.items() if role_id == role),
            None,
        )
        return self._records[index.row()].get(role_name) if role_name else None

    def replace(self, records: list[dict]) -> None:
        new_records = [dict(record) for record in records]
        old_count = len(self._records)
        new_count = len(new_records)
        common_count = min(old_count, new_count)
        first_changed = None
        last_changed = None

        for row in range(common_count):
            if self._records[row] == new_records[row]:
                continue
            self._records[row] = new_records[row]
            first_changed = row if first_changed is None else first_changed
            last_changed = row

        if first_changed is not None:
            self.dataChanged.emit(
                self.index(first_changed, 0),
                self.index(last_changed, 0),
                list(self._role_ids.values()),
            )

        if new_count < old_count:
            self.beginRemoveRows(QModelIndex(), new_count, old_count - 1)
            del self._records[new_count:]
            self.endRemoveRows()
        elif new_count > old_count:
            self.beginInsertRows(QModelIndex(), old_count, new_count - 1)
            self._records.extend(new_records[old_count:])
            self.endInsertRows()

    def append(self, record: dict) -> None:
        row = len(self._records)
        self.beginInsertRows(QModelIndex(), row, row)
        self._records.append(dict(record))
        self.endInsertRows()

    def select_event(self, event_id: int) -> None:
        role_id = self._role_ids.get("selected")
        if role_id is None:
            return
        for row, record in enumerate(self._records):
            selected = int(record.get("eventId") or 0) == event_id
            if bool(record.get("selected")) == selected:
                continue
            record["selected"] = selected
            model_index = self.index(row, 0)
            self.dataChanged.emit(model_index, model_index, [role_id])

    @Slot(int, result="QVariantMap")
    def get(self, row: int) -> dict:
        if not 0 <= row < len(self._records):
            return {}
        return dict(self._records[row])


class DebugLogController(QObject):
    """Single event bus for dl.*, Python, Qt/QML and TACTIC API calls."""

    entry_queued = Signal(object)
    state_changed = Signal()
    error_changed = Signal()
    show_requested = Signal()
    authentication_requested = Signal()
    error_dismissed = Signal(str)
    configuration_requested = Signal()
    configuration_changed = Signal()

    DEFAULT_RECORDING_LEVELS = frozenset({"ERROR", "CRITICAL"})
    RECORDING_LEVELS_KEY = "debugLog/enabledLevels"

    ENTRY_ROLES = (
        "eventId", "timestamp", "level", "message", "module", "functionName",
        "line", "group", "source", "command", "stacktrace", "duration",
        "sizeKb", "thread", "details", "selected",
    )
    GROUP_ROLES = ("label", "key", "count", "depth", "selected")
    SESSION_ROLES = ("label", "path", "modified", "sizeKb", "current")

    def __init__(self, root_path: Path) -> None:
        super().__init__()
        self._settings = dict(env_read_config(
            filename="ui_debug_log",
            unique_id="ui_main",
            long_abs_path=True,
        ) or {})
        self._recording_levels = self._load_recording_levels()
        self._group_panel_width = max(
            170.0,
            min(
                520.0,
                float(self._settings.get(
                    "debugLog/groupPanelWidth", 230.0
                ) or 230.0),
            ),
        )
        self._detail_panel_height = max(
            110.0,
            min(
                620.0,
                float(self._settings.get(
                    "debugLog/detailPanelHeight", 220.0
                ) or 220.0),
            ),
        )
        self.entries_model = MappingListModel(self.ENTRY_ROLES)
        self.groups_model = MappingListModel(self.GROUP_ROLES)
        self.sessions_model = MappingListModel(self.SESSION_ROLES)
        self._live_entries: list[dict] = []
        self._all_entries = self._live_entries
        self._viewing_session_path = ""
        self._levels = set(LEVELS)
        self._group_filter = ""
        self._search = ""
        self._selected_event_id = 0
        self._visible = False
        self._sequence = 0
        self._error_visible = False
        self._error_type = ""
        self._error_kind = ""
        self._error_title = ""
        self._error_message = ""
        self._error_stacktrace = ""
        self._error_command = ""
        self._retry_worker = None
        self._last_error_signature = ""
        self._last_error_group = ""
        self._last_error_at = 0.0
        self._root_path = Path(root_path)
        self._session_start = datetime.now()
        self._file_lock = threading.Lock()
        self._thread_state = threading.local()
        self._inline_error_lock = threading.Lock()
        self._inline_error_owners = set()
        self._original_excepthook = sys.excepthook
        self._python_handler = None
        stamp = self._session_start.strftime("%d_%m_%Y_%H_%M_%S")
        self._log_dir = self._root_path / "log"
        self._json_log = self._log_dir / f"session_{stamp}.jsonl"
        self._json_stream = None
        self._group_rebuild_timer = QTimer(self)
        self._group_rebuild_timer.setSingleShot(True)
        self._group_rebuild_timer.setInterval(120)
        self._group_rebuild_timer.timeout.connect(self._rebuild_groups)
        self.entry_queued.connect(self._append_entry)
        self.refresh_session_history()

    def install(self) -> None:
        """Install compatibility bridges before the application bootstraps."""
        from thlib.environment import dl, env_inst
        import thlib.global_functions as gf

        self._ingest_existing_history(dl)
        env_inst.ui_debuglog = self
        gf.error_handle = self.handle_worker_error
        sys.excepthook = self.capture_exception
        self._python_handler = _PythonLoggingHandler(self)
        logging.getLogger().addHandler(self._python_handler)
        self._instrument_tactic_server()
        self.log(
            "INFO",
            "Diagnostics bus installed",
            group="startup/debug_log",
            source="Runtime",
        )

    def shutdown(self) -> None:
        self._dispose_retry_worker()
        if sys.excepthook == self.capture_exception:
            sys.excepthook = self._original_excepthook
        if self._python_handler:
            logging.getLogger().removeHandler(self._python_handler)
            self._python_handler = None
        with self._file_lock:
            if self._json_stream:
                try:
                    self._json_stream.close()
                except OSError:
                    pass
            self._json_stream = None

    def _ingest_existing_history(self, debug_log) -> None:
        buckets = (
            ("INFO", debug_log.info_dict),
            ("WARNING", debug_log.warning_dict),
            ("LOG", debug_log.log_dict),
            ("EXCEPTION", debug_log.exception_dict),
            ("ERROR", debug_log.error_dict),
            ("CRITICAL", debug_log.critical_dict),
        )
        traces = []
        for level, modules in buckets:
            for values in modules.values():
                traces.extend((order, level, payload) for order, payload in values)
        for _order, level, payload in sorted(traces, key=lambda item: item[0]):
            self._queue_record(self._record_from_existing(payload, level), write=False)

    def add_debuglog(self, debuglog, message_type, write_log=False) -> None:
        """Compatibility method used directly by thlib.environment.DebugLog."""
        _order, payload = debuglog
        level = LEVEL_ALIASES.get(str(message_type), str(message_type).strip(" []"))
        self._queue_record(
            self._record_from_existing(payload, level),
            write=bool(write_log),
        )

    @Slot()
    def show(self) -> None:
        self.show_requested.emit()

    def _record_from_existing(self, payload: dict, level: str) -> dict:
        timestamp = payload.get("datetime")
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat(timespec="milliseconds")
        message = str(payload.get("message_text") or "")
        command = ""
        stripped = message.strip()
        if stripped.startswith((
            "thenv.", "env_inst.", "tc.", "tactic_classes.",
        )):
            command = stripped.replace("thenv.get_tc()", "thenv.tc()")
            if command.startswith("thenv."):
                command = "import thlib.environment as thenv\n" + command
        return self._make_record(
            level=level,
            message=message,
            timestamp=str(timestamp or ""),
            module=str(payload.get("module_path") or ""),
            functionName=str(payload.get("function_name") or ""),
            line=int(payload.get("line_number") or 0),
            group=str(payload.get("unique_id") or ""),
            source="Existing log",
            command=command,
            stacktrace=message if level in {"EXCEPTION", "ERROR", "CRITICAL"} else "",
        )

    def log(
        self,
        level: str,
        message: Any,
        *,
        group: str = "",
        source: str = "Python",
        command: str = "",
        stacktrace: str = "",
        module: str = "",
        function: str = "",
        line: int = 0,
        duration: float = 0.0,
        size_kb: float = 0.0,
        details: str = "",
        caller: int = 1,
    ) -> None:
        level = str(level or "LOG").upper()
        if self._is_missing_file_message(str(message), stacktrace):
            level = "MISSING"
        if level not in LEVELS:
            level = "LOG"
        if not self._accepts_level(level):
            return
        if not module:
            frame = None
            try:
                frame = inspect.currentframe()
                for _index in range(caller + 1):
                    frame = frame.f_back if frame else None
                if frame:
                    module = Path(frame.f_code.co_filename).name
                    function = frame.f_code.co_name
                    line = frame.f_lineno
            except (AttributeError, OSError):
                pass
            finally:
                del frame
        record = self._make_record(
            level=level,
            message=str(message),
            module=module,
            functionName=function,
            line=line,
            group=group,
            source=source,
            command=command,
            stacktrace=stacktrace,
            duration=duration,
            size_kb=size_kb,
            details=details,
        )
        self._queue_record(record, write=True)

    def _make_record(self, **values) -> dict:
        self._sequence += 1
        timestamp = values.pop(
            "timestamp",
            datetime.now().isoformat(timespec="milliseconds"),
        )
        record = {role: "" for role in self.ENTRY_ROLES}
        record.update(values)
        record.update({
            "eventId": self._sequence,
            "timestamp": timestamp,
            "line": int(values.get("line") or 0),
            "duration": float(values.get("duration") or 0.0),
            "sizeKb": float(values.get("size_kb") or 0.0),
            "thread": threading.current_thread().name,
            "selected": False,
        })
        record.pop("size_kb", None)
        return record

    def _queue_record(self, record: dict, write: bool) -> None:
        if self._is_missing_file_message(
            str(record.get("message") or ""),
            str(record.get("stacktrace") or ""),
        ):
            record["level"] = "MISSING"
        if not self._accepts_level(str(record.get("level") or "LOG")):
            return
        if write:
            self._write_record(record)
        self.entry_queued.emit(record)

    def _accepts_level(self, level: str) -> bool:
        return str(level or "").upper() in self._recording_levels

    def accepts_level(self, level: str) -> bool:
        """Return whether a producer should build and retain this event."""
        return self._accepts_level(level)

    def _load_recording_levels(self) -> set[str]:
        raw = self._settings.get(self.RECORDING_LEVELS_KEY)
        if raw is None:
            return set(self.DEFAULT_RECORDING_LEVELS)
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (TypeError, ValueError, json.JSONDecodeError):
                raw = [part.strip() for part in raw.split(",")]
        if not isinstance(raw, (list, tuple, set)):
            return set(self.DEFAULT_RECORDING_LEVELS)
        return {
            str(level or "").upper() for level in raw
            if str(level or "").upper() in LEVELS
        }

    @Property("QVariantList", notify=configuration_changed)
    def recording_levels(self) -> list[str]:
        return [level for level in LEVELS if level in self._recording_levels]

    @Slot("QVariantList")
    def set_recording_levels(self, levels) -> None:
        normalized = {
            str(level or "").upper() for level in (levels or [])
            if str(level or "").upper() in LEVELS
        }
        if normalized == self._recording_levels:
            return
        self._recording_levels = normalized
        ordered = [level for level in LEVELS if level in normalized]
        self._settings[self.RECORDING_LEVELS_KEY] = json.dumps(ordered)
        self._write_settings()
        self.configuration_changed.emit()

    @Slot(object)
    def _append_entry(self, record: dict) -> None:
        self._live_entries.append(dict(record))
        trimmed = False
        if len(self._live_entries) > 10000:
            self._live_entries = self._live_entries[-10000:]
            trimmed = True
        if self._viewing_session_path:
            return
        self._all_entries = self._live_entries
        if not self._visible:
            return
        if trimmed:
            self._apply_filters()
        elif self._matches(record):
            visible = dict(record)
            visible["selected"] = visible["eventId"] == self._selected_event_id
            self.entries_model.append(visible)
        self._group_rebuild_timer.start()
        self.state_changed.emit()

    @Slot(bool)
    def set_visible(self, value: bool) -> None:
        value = bool(value)
        if value == self._visible:
            return
        self._visible = value
        if not value:
            self._group_rebuild_timer.stop()
            return
        if not self._viewing_session_path:
            self._all_entries = self._live_entries
        self._apply_filters()
        self._rebuild_groups()
        self.state_changed.emit()

    def _write_record(self, record: dict) -> None:
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            with self._file_lock:
                if self._json_stream is None:
                    self._json_stream = self._json_log.open(
                        "a", encoding="utf-8"
                    )
                    if self._json_stream.tell() == 0:
                        self._json_stream.write(json.dumps(
                            {"v": SESSION_SCHEMA_VERSION},
                            separators=(",", ":"),
                        ) + "\n")
                self._json_stream.write(
                    json.dumps(
                        self._compact_session_record(record),
                        ensure_ascii=False,
                        default=str,
                        separators=(",", ":"),
                    ) + "\n"
                )
                self._json_stream.flush()
        except OSError:
            if self._json_stream:
                try:
                    self._json_stream.close()
                except OSError:
                    pass
            self._json_stream = None

    @staticmethod
    def _compact_session_record(record: dict) -> dict:
        compact = {}
        for field, key in SESSION_FIELD_KEYS.items():
            value = record.get(field)
            # Missing values and UI/default state add no information to an
            # append-only session.  The reader restores the complete model.
            if value in (None, "", False, 0, 0.0):
                continue
            compact[key] = value
        return compact

    @staticmethod
    def _expand_session_record(values: dict) -> dict:
        return {
            SESSION_KEY_FIELDS[key]: value
            for key, value in values.items()
            if key in SESSION_KEY_FIELDS
        }

    def _matches(self, record: dict) -> bool:
        if record.get("level") not in self._levels:
            return False
        group = str(record.get("group") or "")
        module = str(record.get("module") or "")
        if self._group_filter and not (
            group == self._group_filter
            or group.startswith(self._group_filter + "/")
            or module == self._group_filter
        ):
            return False
        if self._search:
            haystack = "\n".join(str(record.get(key) or "") for key in (
                "message", "group", "module", "functionName", "command", "stacktrace",
            )).lower()
            if self._search not in haystack:
                return False
        return True

    def _apply_filters(self) -> None:
        records = [dict(record) for record in self._all_entries if self._matches(record)]
        for record in records:
            record["selected"] = record["eventId"] == self._selected_event_id
        self.entries_model.replace(records)

    def _rebuild_groups(self) -> None:
        module_counts = Counter()
        group_counts = Counter()
        for record in self._all_entries:
            if record.get("module"):
                module_counts[str(record["module"])] += 1
            group = str(record.get("group") or "")
            parts = [part for part in group.split("/") if part]
            for depth in range(len(parts)):
                group_counts["/".join(parts[:depth + 1])] += 1
        records = [{
            "label": "FULL LOG",
            "key": "",
            "count": len(self._all_entries),
            "depth": 0,
            "selected": not self._group_filter,
        }]
        records.extend({
            "label": module,
            "key": module,
            "count": count,
            "depth": 0,
            "selected": self._group_filter == module,
        } for module, count in sorted(module_counts.items()))
        records.extend({
            "label": path.rsplit("/", 1)[-1],
            "key": path,
            "count": count,
            "depth": path.count("/") + 1,
            "selected": self._group_filter == path,
        } for path, count in sorted(group_counts.items()))
        self.groups_model.replace(records)

    @Slot(str)
    def select_group(self, group: str) -> None:
        self._group_filter = str(group or "")
        self._apply_filters()
        self._rebuild_groups()
        self.state_changed.emit()

    @Slot(str)
    def set_search(self, value: str) -> None:
        normalized = str(value or "").strip().lower()
        if normalized == self._search:
            return
        self._search = normalized
        self._apply_filters()
        self.state_changed.emit()

    @Slot(str, bool)
    def set_level_enabled(self, level: str, enabled: bool) -> None:
        level = str(level or "").upper()
        if enabled:
            self._levels.add(level)
        else:
            self._levels.discard(level)
        self._apply_filters()
        self.state_changed.emit()

    @Slot(int)
    def select_entry(self, row: int) -> None:
        record = self.entries_model.get(row)
        self._selected_event_id = int(record.get("eventId") or 0)
        self.entries_model.select_event(self._selected_event_id)
        self.state_changed.emit()

    @Property(float, constant=True)
    def group_panel_width(self) -> float:
        return self._group_panel_width

    @Property(float, constant=True)
    def detail_panel_height(self) -> float:
        return self._detail_panel_height

    @Slot(float, float)
    def save_layout(self, group_width: float, detail_height: float) -> None:
        self._group_panel_width = max(170.0, min(520.0, float(group_width)))
        self._detail_panel_height = max(
            110.0, min(620.0, float(detail_height))
        )
        self._settings["debugLog/groupPanelWidth"] = self._group_panel_width
        self._settings["debugLog/detailPanelHeight"] = self._detail_panel_height
        self._write_settings()

    def _write_settings(self) -> None:
        env_write_config(
            self._settings,
            filename="ui_debug_log",
            unique_id="ui_main",
            long_abs_path=True,
        )

    def _selected_record(self) -> dict:
        return next(
            (
                record for record in self._all_entries
                if record.get("eventId") == self._selected_event_id
            ),
            {},
        )

    @Property("QVariantMap", notify=state_changed)
    def selected_entry(self) -> dict:
        return dict(self._selected_record())

    @Property("QVariantList", constant=True)
    def levels(self) -> list[str]:
        return list(LEVELS)

    @Property(QObject, constant=True)
    def session_history_model(self) -> QObject:
        return self.sessions_model

    @Property(bool, notify=state_changed)
    def viewing_history(self) -> bool:
        return bool(self._viewing_session_path)

    @Property(str, notify=state_changed)
    def active_session_label(self) -> str:
        if not self._viewing_session_path:
            return "Live session"
        return Path(self._viewing_session_path).stem.replace(
            "session_", ""
        ).replace("_", " ")

    @Property(str, constant=True)
    def session_log_path(self) -> str:
        return str(self._json_log)

    @Property(int, notify=state_changed)
    def entry_count(self) -> int:
        return len(self._all_entries)

    @Slot()
    def copy_selected(self) -> None:
        record = self._selected_record()
        if not record:
            return
        QGuiApplication.clipboard().setText(self._format_record(record))

    @Slot()
    def copy_selected_command(self) -> None:
        command = str(self._selected_record().get("command") or "")
        if command:
            QGuiApplication.clipboard().setText(command)

    @Slot()
    def copy_session_path(self) -> None:
        QGuiApplication.clipboard().setText(str(self._json_log))

    @Slot()
    def clear(self) -> None:
        if self._viewing_session_path:
            self.show_live_session()
            return
        self._live_entries.clear()
        self._all_entries = self._live_entries
        self._selected_event_id = 0
        self._apply_filters()
        self._rebuild_groups()
        self.state_changed.emit()

    @staticmethod
    def _format_record(record: dict) -> str:
        text = (
            f"[{record.get('timestamp')}] [{record.get('level')}] "
            f"[{record.get('group')}]\n{record.get('message')}\n"
            f"{record.get('module')} / {record.get('functionName')}():"
            f"{int(record.get('line') or 0):04d}"
        )
        if record.get("details"):
            text += f"\n\nDetails:\n{record['details']}"
        if record.get("command"):
            text += f"\n\nRuntime command:\n{record['command']}"
        if record.get("stacktrace"):
            text += f"\n\nStacktrace:\n{record['stacktrace']}"
        return text

    def log_qt_message(self, level: str, source: str, message: str) -> None:
        self.log(level, message, group="qt/runtime", source=source, caller=2)

    @staticmethod
    def _is_missing_file_message(message: str, stacktrace: str = "") -> bool:
        text = f"{message}\n{stacktrace}".lower()
        return (
            ("qquickimage" in text and "not found" in text)
            or "filenotfounderror" in text
            or "no such file or directory" in text
            or "[errno 2]" in text
        )

    @Slot()
    def refresh_session_history(self) -> None:
        records = []
        try:
            paths = sorted((
                path for path in self._log_dir.glob("session_*.jsonl")
                if self._has_current_session_schema(path)
            ),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            for path in paths:
                stat = path.stat()
                records.append({
                    "label": path.stem.replace(
                        "session_", ""
                    ).replace("_", " "),
                    "path": str(path),
                    "modified": datetime.fromtimestamp(
                        stat.st_mtime
                    ).isoformat(timespec="seconds"),
                    "sizeKb": round(stat.st_size / 1024.0, 1),
                    "current": path == self._json_log,
                })
        except OSError as error:
            self.log(
                "WARNING",
                f"Cannot read debug log history: {error}",
                group="debug_log/history",
                source="Debug Log",
            )
        self.sessions_model.replace(records)
        self.state_changed.emit()

    @staticmethod
    def _has_current_session_schema(path: Path) -> bool:
        try:
            with path.open("r", encoding="utf-8-sig") as stream:
                header = json.loads(stream.readline())
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return False
        return header == {"v": SESSION_SCHEMA_VERSION}

    @Slot(int, result=bool)
    def load_session_row(self, row: int) -> bool:
        record = self.sessions_model.get(row)
        path = str(record.get("path") or "")
        if not path:
            return False
        if Path(path) == self._json_log:
            self.show_live_session()
            return True
        return self._load_session_path(Path(path))

    @Slot(str, result=bool)
    def load_session_file(self, value: str) -> bool:
        url = QUrl(str(value or ""))
        path = Path(url.toLocalFile() if url.isLocalFile() else str(value))
        if path == self._json_log:
            self.show_live_session()
            return True
        return self._load_session_path(path)

    def _load_session_path(self, path: Path) -> bool:
        try:
            records = self._read_session_records(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self.raise_error(
                error,
                group="debug_log/history",
            )
            return False
        self._viewing_session_path = str(path)
        self._all_entries = records[-10000:]
        self._selected_event_id = 0
        self._group_filter = ""
        self._apply_filters()
        self._rebuild_groups()
        self.state_changed.emit()
        return True

    def _read_session_records(self, path: Path) -> list[dict]:
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.suffix.lower() != ".jsonl":
            raise ValueError(
                "A compact Debug Log session (.jsonl) is required."
            )
        records = []
        with path.open("r", encoding="utf-8-sig") as stream:
            try:
                header = json.loads(stream.readline())
            except json.JSONDecodeError as error:
                raise ValueError("Invalid Debug Log session header") from error
            if header != {"v": SESSION_SCHEMA_VERSION}:
                raise ValueError(
                    "Unsupported Debug Log session schema"
                )
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    values = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Invalid JSONL record at line {line_number}: {error}"
                    ) from error
                if not isinstance(values, dict):
                    continue
                values = self._expand_session_record(values)
                record = {
                    role: values.get(role, "")
                    for role in self.ENTRY_ROLES
                }
                event_id = int(values.get("eventId") or len(records) + 1)
                record.update({
                    "eventId": event_id,
                    "line": int(values.get("line") or 0),
                    "duration": float(values.get("duration") or 0.0),
                    "sizeKb": float(values.get("sizeKb") or 0.0),
                    "selected": False,
                })
                level = str(record.get("level") or "LOG").upper()
                record["level"] = (
                    "MISSING"
                    if self._is_missing_file_message(
                        str(record.get("message") or ""),
                        str(record.get("stacktrace") or ""),
                    )
                    else level if level in LEVELS else "LOG"
                )
                records.append(record)
        return records

    @Slot()
    def show_live_session(self) -> None:
        self._viewing_session_path = ""
        self._all_entries = self._live_entries
        self._selected_event_id = 0
        self._group_filter = ""
        self._apply_filters()
        self._rebuild_groups()
        self.state_changed.emit()

    def capture_exception(self, exception_type, exception, tb) -> None:
        stacktrace = "".join(traceback.format_exception(exception_type, exception, tb))
        self.raise_error(exception, stacktrace=stacktrace, group="exceptions/unhandled")
        if self._original_excepthook:
            self._original_excepthook(exception_type, exception, tb)

    @Slot(object)
    def handle_worker_error(self, args) -> None:
        payload, worker = args
        exception = payload.get("exception") if isinstance(payload, dict) else payload
        stacktrace = payload.get("stacktrace", "") if isinstance(payload, dict) else ""
        self.raise_error(
            exception,
            stacktrace=stacktrace,
            group="exceptions/worker",
            retry_worker=worker,
        )

    def raise_error(
        self,
        exception,
        *,
        stacktrace: str = "",
        group: str = "exceptions",
        command: str = "",
        retry_worker=None,
    ) -> None:
        with self._inline_error_lock:
            inline_error_active = bool(self._inline_error_owners)
        if (
            inline_error_active
            or getattr(self._thread_state, "script_editor_output", False)
        ):
            return
        message = str(exception or "Unknown error")
        retry_exhausted = (
            retry_worker is not None
            and not bool(getattr(retry_worker, "can_retry", True))
        )
        if retry_exhausted:
            message = f"{message}\nRetry limit reached (3 attempts)."
        error_type = self.classify_error(exception, stacktrace)
        error_kind = self.exception_kind(exception, stacktrace)
        signature = f"{type(exception).__name__}:{message}"
        now = time.monotonic()
        duplicate = (
            signature == self._last_error_signature
            and now - self._last_error_at < 1.5
        )
        titles = {
            "ticket_error": "TACTIC session expired",
            "connection_timeout": "TACTIC connection timed out",
            "connection_refused": "Cannot connect to TACTIC",
            "login_pass_error": "Incorrect login or password",
            "sql_connection_error": "TACTIC database connection error",
            "protocol_error": "TACTIC protocol error",
            "server_error": "TACTIC server request failed",
            "no_project_error": "Project is unavailable",
            "attribute_error": "Application attribute error",
            "database_query_error": "TACTIC database query failed",
            "type_error": "Application type error",
            "value_error": "Invalid application value",
            "key_error": "Required application data is missing",
            "index_error": "Application index error",
            "file_not_found_error": "File was not found",
            "permission_error": "Permission denied",
            "import_error": "Application component could not be loaded",
            "runtime_error": "Application runtime error",
            "assertion_error": "Application assertion failed",
            "os_error": "Operating system error",
            "qml_error": "Interface error",
        }
        if not duplicate or group == self._last_error_group:
            self.log(
                "EXCEPTION",
                message,
                group=group,
                source="Error handler",
                command=command,
                stacktrace=stacktrace,
                caller=2,
            )
        if error_type in {"ticket_error", "login_pass_error"}:
            self._last_error_signature = signature
            self._last_error_group = group
            self._last_error_at = now
            self.authentication_requested.emit()
            return
        if duplicate:
            if (
                retry_worker is not None
                and self._retry_worker is None
                and bool(getattr(retry_worker, "can_retry", True))
            ):
                self._retry_worker = retry_worker
                self.error_changed.emit()
            return
        self._last_error_signature = signature
        self._last_error_group = group
        self._last_error_at = now
        self._error_type = error_type
        self._error_kind = error_kind
        self._error_title = titles.get(error_type) or (
            self._humanize_exception_kind(error_kind)
            if error_kind else "Application error"
        )
        self._error_message = message
        self._error_stacktrace = stacktrace
        self._error_command = command
        if self._retry_worker is not retry_worker:
            self._dispose_retry_worker()
        self._retry_worker = (
            retry_worker
            if retry_worker is not None
            and bool(getattr(retry_worker, "can_retry", True))
            else None
        )
        self._error_visible = True
        self.error_changed.emit()

    @contextmanager
    def script_editor_output(self):
        previous = bool(getattr(
            self._thread_state, "script_editor_output", False
        ))
        self._thread_state.script_editor_output = True
        try:
            yield
        finally:
            self._thread_state.script_editor_output = previous

    def begin_inline_error_output(self, owner: str) -> None:
        with self._inline_error_lock:
            self._inline_error_owners.add(str(owner))

    def end_inline_error_output(self, owner: str) -> None:
        with self._inline_error_lock:
            self._inline_error_owners.discard(str(owner))

    @staticmethod
    def exception_kind(exception, stacktrace: str = "") -> str:
        if isinstance(exception, BaseException):
            return type(exception).__name__
        for line in reversed(str(stacktrace or "").splitlines()):
            candidate = line.partition(":")[0].strip().rsplit(".", 1)[-1]
            if candidate.endswith(("Error", "Exception", "Fault", "Warning")):
                return candidate
        return ""

    @staticmethod
    def _humanize_exception_kind(exception_kind: str) -> str:
        return re.sub(
            r"(?<!^)(?=[A-Z])", " ", str(exception_kind or "")
        )

    @staticmethod
    def classify_error(exception, stacktrace: str = "") -> str:
        detail = f"{exception or ''}\n{stacktrace or ''}".lower()
        transport_reason = (
            getattr(exception, "reason", None)
            if isinstance(exception, URLError)
            else exception
        ) or exception
        winerror = getattr(transport_reason, "winerror", None)
        if (
            "no project" in detail
            or ("database [" in detail and "] does not exist" in detail)
        ):
            return "no_project_error"
        if (
            "cannot login with key:" in detail
            or "session may have expired" in detail
        ):
            return "ticket_error"
        if (
            isinstance(transport_reason, TimeoutError)
            or winerror == 10060
            or any(value in detail for value in (
                "timed out", "timeout", "did not properly respond",
            ))
        ):
            return "connection_timeout"
        if (
            isinstance(transport_reason, ConnectionRefusedError)
            or winerror in {10051, 10061, 10065}
            or any(value in detail for value in (
                "connection refused", "actively refused",
                "getaddrinfo failed", "no connection could be made",
            ))
        ):
            return "connection_refused"
        if "login/password combination incorrect" in detail:
            return "login_pass_error"
        if "do_query error" in detail or "database query" in detail:
            return "database_query_error"
        if "connect to mysql server" in detail:
            return "sql_connection_error"
        if isinstance(exception, PermissionError) or any(value in detail for value in (
            "permissionerror:", "permission denied",
            "tactic administrator access is required",
            "only a tactic administrator can change access rules",
        )):
            return "permission_error"
        if "protocolerror" in detail or "xmlrpc.client.fault" in detail:
            return "protocol_error"
        if (
            isinstance(exception, ConnectionError)
            or any(value in detail for value in (
                "http error 5", "internal server error", "bad gateway",
                "service unavailable", "gateway timeout",
                "remote end closed", "connection reset",
                "network is unreachable",
            ))
        ):
            return "server_error"
        if any(value in detail for value in (
            "binding loop detected", "qml error", "qml type",
        )):
            return "qml_error"
        if isinstance(exception, AttributeError) or any(
            value in detail
            for value in ("attributeerror:", "object has no attribute")
        ):
            return "attribute_error"
        exception_types = (
            (TypeError, "type_error"),
            (ValueError, "value_error"),
            (KeyError, "key_error"),
            (IndexError, "index_error"),
            (FileNotFoundError, "file_not_found_error"),
            (PermissionError, "permission_error"),
            (ImportError, "import_error"),
            (AssertionError, "assertion_error"),
            (RuntimeError, "runtime_error"),
            (OSError, "os_error"),
        )
        for exception_class, error_type in exception_types:
            if isinstance(exception, exception_class):
                return error_type
        traceback_types = (
            ("typeerror:", "type_error"),
            ("valueerror:", "value_error"),
            ("keyerror:", "key_error"),
            ("indexerror:", "index_error"),
            ("filenotfounderror:", "file_not_found_error"),
            ("permissionerror:", "permission_error"),
            ("modulenotfounderror:", "import_error"),
            ("importerror:", "import_error"),
            ("assertionerror:", "assertion_error"),
            ("runtimeerror:", "runtime_error"),
            ("oserror:", "os_error"),
        )
        for marker, error_type in traceback_types:
            if marker in detail:
                return error_type
        if "no such file or directory" in detail:
            return "file_not_found_error"
        if "permission denied" in detail:
            return "permission_error"
        return "unknown_error"

    @Property(bool, notify=error_changed)
    def error_visible(self) -> bool:
        return self._error_visible

    @Property(str, notify=error_changed)
    def error_type(self) -> str:
        return self._error_type

    @Property(str, notify=error_changed)
    def error_kind(self) -> str:
        return self._error_kind

    @Property(str, notify=error_changed)
    def error_title(self) -> str:
        return self._error_title

    @Property(str, notify=error_changed)
    def error_message(self) -> str:
        return self._error_message

    @Property(str, notify=error_changed)
    def error_stacktrace(self) -> str:
        return self._error_stacktrace

    @Property(str, notify=error_changed)
    def error_command(self) -> str:
        return self._error_command

    @Slot(result=bool)
    def copy_error_stacktrace(self) -> bool:
        stacktrace = self._error_stacktrace
        if not stacktrace:
            return False
        QGuiApplication.clipboard().setText(stacktrace)
        return True

    @Property(bool, notify=error_changed)
    def can_retry(self) -> bool:
        worker = self._retry_worker
        return (
            worker is not None
            and bool(getattr(worker, "can_retry", True))
        )

    @Slot()
    def dismiss_error(self) -> None:
        error_type = self._error_type
        self._dispose_retry_worker()
        self._error_visible = False
        self.error_changed.emit()
        self.error_dismissed.emit(error_type)

    @Slot()
    def retry_error(self) -> None:
        worker = self._retry_worker
        self._retry_worker = None
        self._error_visible = False
        self.error_changed.emit()
        if worker and not worker.retry():
            self.raise_error(
                RuntimeError("Retry limit reached for this request."),
                group="server/retry",
            )

    def _dispose_retry_worker(self) -> None:
        worker = self._retry_worker
        self._retry_worker = None
        if worker and hasattr(worker, "dispose"):
            worker.dispose()

    @Slot()
    def primary_error_action(self) -> None:
        error_type = self._error_type
        self.dismiss_error()
        if error_type in {"ticket_error", "login_pass_error"}:
            self.authentication_requested.emit()
        elif error_type in {
            "connection_refused", "connection_timeout", "sql_connection_error",
            "protocol_error", "no_project_error",
        }:
            self.configuration_requested.emit()

    def _instrument_tactic_server(self) -> None:
        try:
            from thlib.side.client.tactic_client_lib.tactic_server_stub import (
                TacticServerStub,
            )
        except ImportError:
            return
        method_names = {
            "query", "insert", "update", "update_multiple", "delete_sobject",
            "simple_checkin", "group_query", "get_ticket", "execute_cmd",
            "execute_python_script", "execute_js_script", "eval",
            "get_unique_sobject", "get_base_dirs", "start", "finish", "abort",
        }
        for name, original in list(vars(TacticServerStub).items()):
            if name.startswith("_") or not inspect.isfunction(original):
                continue
            code_names = set(getattr(original, "__code__", None).co_names or ())
            if name not in method_names and "server" not in code_names:
                continue
            if getattr(original, "_handler_logged", False):
                continue
            wrapped = self._server_wrapper(name, original)
            wrapped._handler_logged = True
            setattr(TacticServerStub, name, wrapped)

    def _server_wrapper(self, name: str, original):
        @functools.wraps(original)
        def wrapped(server, *args, **kwargs):
            depth = int(getattr(self._thread_state, "server_depth", 0))
            self._thread_state.server_depth = depth + 1
            if depth:
                try:
                    return original(server, *args, **kwargs)
                finally:
                    self._thread_state.server_depth = depth
            started_at = time.perf_counter()
            command = ""
            if name not in SILENT_SERVER_SUCCESSES:
                command = self._runtime_command(
                    server, name, original, args, kwargs
                )
            try:
                result = original(server, *args, **kwargs)
                duration = time.perf_counter() - started_at
                size_kb = self._payload_size_kb(result)
                if name not in SILENT_SERVER_SUCCESSES:
                    request_metrics.record_request(
                        f"xmlrpc.{name}", duration, int(size_kb * 1024)
                    )
                    self.log(
                        "API",
                        f"{name} completed in {duration:.3f} s "
                        f"({size_kb:.1f} KB)",
                        group=f"server/{name}",
                        source="TACTIC API",
                        command=command,
                        duration=duration,
                        size_kb=size_kb,
                        caller=2,
                    )
                return result
            except Exception as exception:
                duration = time.perf_counter() - started_at
                if name not in SILENT_SERVER_SUCCESSES:
                    request_metrics.record_request(
                        f"xmlrpc.{name}", duration, failed=True
                    )
                if not command:
                    command = self._runtime_command(
                        server, name, original, args, kwargs
                    )
                stacktrace = traceback.format_exc()
                if not (
                    transient_error_reporting_deferred()
                    and is_transient_read_error(exception)
                ):
                    self.raise_error(
                        exception,
                        stacktrace=stacktrace,
                        group=f"server/{name}",
                        command=command,
                    )
                raise
            finally:
                self._thread_state.server_depth = depth
        return wrapped

    @staticmethod
    def _payload_size_kb(payload) -> float:
        total = 0
        seen = set()
        pending = [(payload, 0)]
        while pending and total < 64 * 1024 * 1024:
            value, depth = pending.pop()
            identity = id(value)
            if identity in seen:
                continue
            seen.add(identity)
            try:
                total += sys.getsizeof(value)
            except TypeError:
                continue
            if depth >= 5:
                continue
            if isinstance(value, dict):
                pending.extend((item, depth + 1) for item in value.keys())
                pending.extend((item, depth + 1) for item in value.values())
            elif isinstance(value, (list, tuple, set, frozenset)):
                pending.extend((item, depth + 1) for item in value)
        return total / 1024.0

    def _runtime_command(self, server, name, original, args, kwargs) -> str:
        project = getattr(server, "project_code", None) or "sthpw"
        try:
            signature = inspect.signature(original)
            bound = signature.bind_partial(server, *args, **kwargs)
            values = [
                (key, value, signature.parameters[key].kind)
                for key, value in bound.arguments.items()
                if key != "self"
            ]
        except (TypeError, ValueError):
            values = [
                (
                    f"arg{index}",
                    value,
                    inspect.Parameter.POSITIONAL_ONLY,
                )
                for index, value in enumerate(args)
            ]
            values.extend(
                (key, value, inspect.Parameter.KEYWORD_ONLY)
                for key, value in kwargs.items()
            )
        rendered = []
        for key, value, parameter_kind in values:
            lowered = key.lower()
            if any(
                secret in lowered
                for secret in ("ticket", "password", "secret", "token")
            ):
                value = "<redacted>"
            else:
                value = self._redact(value)
            if parameter_kind == inspect.Parameter.VAR_POSITIONAL:
                rendered.extend(self._safe_repr(item) for item in value)
            elif parameter_kind == inspect.Parameter.VAR_KEYWORD:
                rendered.extend(
                    f"{nested_key}={self._safe_repr(self._redact(nested_value))}"
                    for nested_key, nested_value in value.items()
                )
            elif parameter_kind == inspect.Parameter.POSITIONAL_ONLY:
                rendered.append(self._safe_repr(value))
            else:
                rendered.append(f"{key}={self._safe_repr(value)}")
        return (
            "import thlib.environment as thenv\n"
            "thenv.tc().server_start(project={project}).{method}({args})"
            .format(
                project=repr(project),
                method=name,
                args=", ".join(rendered),
            )
        )

    @staticmethod
    def _safe_repr(value) -> str:
        return repr(value)

    @classmethod
    def _redact(cls, value, active: set[int] | None = None):
        if active is None:
            active = set()
        if isinstance(value, dict):
            identity = id(value)
            if identity in active:
                return "<recursive reference>"
            active.add(identity)
            try:
                result = {}
                for key, nested in value.items():
                    normalized_key = str(key).lower()
                    if any(
                        secret in normalized_key
                        for secret in (
                            "ticket", "password", "secret", "token",
                        )
                    ):
                        result[key] = "<redacted>"
                    else:
                        result[key] = cls._redact(nested, active)
                return result
            finally:
                active.remove(identity)
        if isinstance(value, list):
            identity = id(value)
            if identity in active:
                return "<recursive reference>"
            active.add(identity)
            try:
                return [cls._redact(item, active) for item in value]
            finally:
                active.remove(identity)
        if isinstance(value, tuple):
            identity = id(value)
            if identity in active:
                return "<recursive reference>"
            active.add(identity)
            try:
                return tuple(cls._redact(item, active) for item in value)
            finally:
                active.remove(identity)
        return value


class _PythonLoggingHandler(logging.Handler):
    def __init__(self, controller: DebugLogController) -> None:
        super().__init__()
        self.controller = controller

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = record.levelname.upper()
            if level == "DEBUG":
                level = "LOG"
            if level not in LEVELS:
                level = "LOG"
            stacktrace = ""
            if record.exc_info:
                stacktrace = "".join(traceback.format_exception(*record.exc_info))
            self.controller.log(
                level,
                record.getMessage(),
                group=f"python/{record.name}",
                source="logging",
                module=record.module,
                function=record.funcName,
                line=record.lineno,
                stacktrace=stacktrace,
            )
        except Exception:
            self.handleError(record)
