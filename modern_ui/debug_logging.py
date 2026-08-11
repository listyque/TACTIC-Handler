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
import sys
import threading
import time
import traceback
from typing import Any

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    QTimer,
    QSettings,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication


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

    ENTRY_ROLES = (
        "eventId", "timestamp", "level", "message", "module", "functionName",
        "line", "group", "source", "command", "stacktrace", "duration",
        "sizeKb", "thread", "details", "selected",
    )
    GROUP_ROLES = ("label", "key", "count", "depth", "selected")
    SESSION_ROLES = ("label", "path", "modified", "sizeKb", "current")

    def __init__(self, root_path: Path) -> None:
        super().__init__()
        self._settings = QSettings("TACTIC-Handler", "modern-qml")
        self._group_panel_width = max(
            170.0,
            min(
                520.0,
                float(self._settings.value(
                    "debugLog/groupPanelWidth", 230.0
                )),
            ),
        )
        self._detail_panel_height = max(
            110.0,
            min(
                620.0,
                float(self._settings.value(
                    "debugLog/detailPanelHeight", 220.0
                )),
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
        self._text_log = self._log_dir / f"modern_session_{stamp}.log"
        self._json_log = self._log_dir / f"modern_session_{stamp}.jsonl"
        self._text_stream = None
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
            "Modern diagnostics bus installed",
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
            for stream in (self._text_stream, self._json_stream):
                if stream:
                    try:
                        stream.close()
                    except OSError:
                        pass
            self._text_stream = None
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

    def hide(self) -> None:
        # DebugLog calls hide(); QML owns the window visibility.
        return

    def fill_modules_tree(self) -> None:
        self._rebuild_groups()

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
        if write:
            self._write_record(record)
        self.entry_queued.emit(record)

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
            location = "{} / {}(): {:04d}".format(
                record.get("module") or "?",
                record.get("functionName") or "?",
                int(record.get("line") or 0),
            )
            text = (
                "[{timestamp}] [{level}] [{group}]\n"
                "    Message: {message}\n"
                "    {location}\n"
            ).format(location=location, **record)
            if record.get("command"):
                text += f"    Runtime: {record['command']}\n"
            if record.get("stacktrace"):
                text += f"{record['stacktrace'].rstrip()}\n"
            with self._file_lock:
                if self._text_stream is None:
                    self._text_stream = self._text_log.open(
                        "a", encoding="utf-8"
                    )
                if self._json_stream is None:
                    self._json_stream = self._json_log.open(
                        "a", encoding="utf-8"
                    )
                self._text_stream.write(text)
                self._text_stream.flush()
                self._json_stream.write(
                    json.dumps(record, ensure_ascii=False, default=str) + "\n"
                )
                self._json_stream.flush()
        except OSError:
            for stream in (self._text_stream, self._json_stream):
                if stream:
                    try:
                        stream.close()
                    except OSError:
                        pass
            self._text_stream = None
            self._json_stream = None

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
        self._settings.setValue(
            "debugLog/groupPanelWidth", self._group_panel_width
        )
        self._settings.setValue(
            "debugLog/detailPanelHeight", self._detail_panel_height
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
            "modern_session_", ""
        ).replace("_", " ")

    @Property(str, constant=True)
    def session_log_path(self) -> str:
        return str(self._text_log)

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
        QGuiApplication.clipboard().setText(str(self._text_log))

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
            paths = sorted(
                self._log_dir.glob("modern_session_*.jsonl"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            for path in paths:
                stat = path.stat()
                records.append({
                    "label": path.stem.replace(
                        "modern_session_", ""
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
        if path.suffix.lower() == ".log" and path.with_suffix(".jsonl").is_file():
            path = path.with_suffix(".jsonl")
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
                "Structured session log (.jsonl) is required to restore "
                "levels, groups and stack traces."
            )
        records = []
        with path.open("r", encoding="utf-8-sig") as stream:
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
                record = {
                    role: values.get(role, "")
                    for role in self.ENTRY_ROLES
                }
                self._sequence += 1
                record.update({
                    "eventId": self._sequence,
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
        if (
            retry_worker is not None
            and not bool(getattr(retry_worker, "can_retry", True))
        ):
            message = f"{message}\nRetry limit reached (3 attempts)."
        error_type = self.classify_error(exception)
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
            "unknown_error": "Unexpected application error",
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
        self._error_title = titles.get(error_type, "Application error")
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
    def classify_error(exception) -> str:
        message = str(exception or "").lower()
        if "no project" in message:
            return "no_project_error"
        if "cannot login with key:" in message or "session may have expired" in message:
            return "ticket_error"
        if any(value in message for value in (
            "timed out", "timeout", "did not properly respond",
        )):
            return "connection_timeout"
        if any(value in message for value in (
            "connection refused", "actively refused", "getaddrinfo failed",
            "no connection could be made",
        )):
            return "connection_refused"
        if "login/password combination incorrect" in message:
            return "login_pass_error"
        if "connect to mysql server" in message:
            return "sql_connection_error"
        if "protocolerror" in message or "xmlrpc.client.fault" in message:
            return "protocol_error"
        if any(value in message for value in (
            "http error 5", "internal server error", "bad gateway",
            "service unavailable", "gateway timeout", "remote end closed",
            "connection reset", "network is unreachable",
        )):
            return "server_error"
        if "object has no attribute" in message:
            return "attribute_error"
        return "unknown_error"

    @Property(bool, notify=error_changed)
    def error_visible(self) -> bool:
        return self._error_visible

    @Property(str, notify=error_changed)
    def error_type(self) -> str:
        return self._error_type

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
            if getattr(original, "_modern_logged", False):
                continue
            wrapped = self._server_wrapper(name, original)
            wrapped._modern_logged = True
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
            command = self._runtime_command(server, name, original, args, kwargs)
            try:
                result = original(server, *args, **kwargs)
                duration = time.perf_counter() - started_at
                size_kb = self._payload_size_kb(result)
                self.log(
                    "API",
                    f"{name} completed in {duration:.3f} s ({size_kb:.1f} KB)",
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
                stacktrace = traceback.format_exc()
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
            if any(secret in lowered for secret in ("ticket", "password", "secret")):
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
    def _safe_repr(value, limit: int = 3000) -> str:
        text = repr(value)
        if len(text) > limit:
            return text[:limit] + "...<truncated>"
        return text

    @classmethod
    def _redact(cls, value, depth: int = 0):
        if depth > 6:
            return "<truncated>"
        if isinstance(value, dict):
            result = {}
            for key, nested in value.items():
                normalized_key = str(key).lower()
                if any(
                    secret in normalized_key
                    for secret in ("ticket", "password", "secret", "token")
                ):
                    result[key] = "<redacted>"
                elif (
                    normalized_key in {"code", "script", "script_body"}
                    and isinstance(nested, str)
                    and len(nested) > 600
                ):
                    result[key] = (
                        nested[:600]
                        + f"...<truncated {len(nested) - 600} chars>"
                    )
                else:
                    result[key] = cls._redact(nested, depth + 1)
            return result
        if isinstance(value, list):
            return [cls._redact(item, depth + 1) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._redact(item, depth + 1) for item in value)
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
