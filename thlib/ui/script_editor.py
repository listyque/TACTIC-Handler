from __future__ import annotations

import code
import contextlib
import io
import json
import pprint
import time
import traceback
import uuid
from pathlib import Path

from PySide6.QtCore import QObject, Property, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication

from thlib.environment import env_mode, env_read_config, env_write_config
from thlib.ui.activity import activity_timestamp_labels
from thlib.ui.script_history import script_history_request
from thlib.ui.script_editor_features import (
    PythonSyntaxHighlighter,
    completion_items,
    document_symbols,
    edit_command,
    find_matches,
)
from thlib.ui.workspace_models.records import RecordListModel


_SAVED_HISTORY_ROLES = (
    "revisionId", "timestampPretty", "timestampFull", "actor",
    "actorDisplay", "summary", "current", "selected",
)


class ScriptEditorController(QObject):
    stateChanged = Signal()
    executionTargetsChanged = Signal()
    confirmationRequested = Signal(str)
    deleteConfirmationRequested = Signal(str, str)
    closeAllConfirmationRequested = Signal(int)
    scriptsLoaded = Signal(str)
    newScriptRequested = Signal()
    editorChanged = Signal("QVariantMap")
    savedRevisionReady = Signal(str)
    outputAppended = Signal(str)
    _executeLocalRequested = Signal(object, str)

    languages = [
        {"label": "Local Python", "value": "local_python", "runnable": True},
        {"label": "DCC Python", "value": "dcc_python", "runnable": True},
        {"label": "Server Python", "value": "python", "runnable": True},
        {"label": "JavaScript", "value": "javascript", "runnable": False},
        {"label": "Server JS", "value": "server_js", "runnable": True},
        {"label": "Expression", "value": "expression", "runnable": True},
        {"label": "XML", "value": "xml", "runnable": False},
    ]
    def __init__(self, application, debug_log, parent=None):
        super().__init__(parent)
        self._application = application
        self._debug_log = debug_log
        self._settings = dict(env_read_config(
            filename="ui_script_editor",
            unique_id="ui_main",
            long_abs_path=True,
        ) or {})
        self.model = RecordListModel((
            "token", "nodeType", "path", "folder", "title", "language",
            "depth", "expanded", "hasChildren",
        ))
        self.tabs = RecordListModel((
            "tabId", "token", "title", "dirty", "current",
        ))
        self.saved_history = RecordListModel(_SAVED_HISTORY_ROLES)
        self._objects = {}
        self._scripts = []
        self._tree_filter = ""
        self._expanded = self._restore_expanded()
        self._busy = False
        self._loaded = False
        self._mirrored_project_code = ""
        self._reload_after_busy = False
        self._error = ""
        self._pending = {}
        self._pending_delete = ""
        self._pending_selection = None
        self._selected_token = ""
        self._sessions = {}
        self._current_tab_id = ""
        self._editor_state = self._blank_editor_state()
        self._session_project_code = self._project_code()
        self._restore_sessions()
        self._worker = None
        self._operation_tab_id = ""
        self._saved_history_records = []
        self._saved_history_token = ""
        self._saved_history_loading = False
        self._executeLocalRequested.connect(
            self._execute_local_on_gui,
            Qt.ConnectionType.QueuedConnection,
        )
        self._run_error_owner = "script-editor-run"
        self._run_error_output_active = False
        self._local_consoles = {}
        self._dcc_bridge = None
        self._dcc_runs = {}
        self._dcc_target_signature = ()
        self._syntax_highlighter = None
        self._session_save_timer = QTimer(self)
        self._session_save_timer.setSingleShot(True)
        self._session_save_timer.setInterval(250)
        self._session_save_timer.timeout.connect(self._save_sessions)
        if self._application is not None:
            self._application.project_changed.connect(self._project_changed)
            self._application.project_state_changed.connect(
                self._sync_project_sessions
            )
            if self._application.current_project_code:
                self.preload()

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(bool, notify=stateChanged)
    def loaded(self):
        return self._loaded

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(str, notify=stateChanged)
    def output(self):
        return str(self._editor_state.get("output") or "")

    @Property(str, notify=stateChanged)
    def currentTabId(self):
        return self._current_tab_id

    @Property("QVariantMap", notify=stateChanged)
    def currentEditor(self):
        return dict(self._editor_state)

    @Property(str, notify=stateChanged)
    def selectedToken(self):
        return self._selected_token

    @Property(QObject, constant=True)
    def savedHistoryModel(self):
        return self.saved_history

    @Property(bool, notify=stateChanged)
    def savedHistoryLoaded(self):
        token = str(self._editor_state.get("token") or "")
        return bool(token and self._saved_history_token == token)

    @Property(bool, notify=stateChanged)
    def savedHistoryLoading(self):
        return self._saved_history_loading

    @Property(int, notify=stateChanged)
    def savedHistoryCount(self):
        return len(self._saved_history_records)

    @Property("QVariantList", constant=True)
    def languageOptions(self):
        return self.languages

    @Property("QVariantList", notify=stateChanged)
    def shelfScriptOptions(self):
        runnable = {
            option["value"] for option in self.languages
            if option["runnable"]
        }
        options = []
        for record in self._scripts:
            language = str(record.get("language") or "local_python")
            if language not in runnable:
                continue
            path = "{}/{}".format(
                str(record.get("folder") or "").strip("/"),
                str(record.get("title") or ""),
            ).strip("/")
            options.append({
                "value": path,
                "label": path,
                "language": language,
            })
        return options

    @Property("QVariantList", notify=executionTargetsChanged)
    def runModeOptions(self):
        target = self._dcc_target()
        return [{
            "label": target.get("label") or "DCC (not connected)",
            "value": "dcc",
            "icon": "deployed_code",
        }, {
            "label": "TACTIC Handler",
            "value": "standalone",
            "icon": "computer",
        }, {
            "label": "TACTIC Server",
            "value": "server",
            "icon": "cloud",
        }]

    def _dcc_target(self):
        bridge = self._dcc_bridge
        if not bridge or not bridge.has_dcc_capability("execute_script_file"):
            return {}
        return {
            "clientId": str(getattr(bridge, "selectedClient", "") or ""),
            "label": str(
                getattr(bridge, "selectedClientLabel", "") or "DCC"
            ),
        }

    def _dcc_state_changed(self):
        target = self._dcc_target()
        signature = (
            target.get("clientId", ""), target.get("label", "")
        )
        if signature != self._dcc_target_signature:
            self._dcc_target_signature = signature
            self.executionTargetsChanged.emit()

    def attach_dcc_bridge(self, bridge):
        previous = self._dcc_bridge
        if previous:
            try:
                previous.commandFinished.disconnect(self._dcc_command_finished)
                previous.stateChanged.disconnect(self._dcc_state_changed)
            except (RuntimeError, TypeError):
                pass
        self._dcc_bridge = bridge
        if bridge:
            bridge.commandFinished.connect(self._dcc_command_finished)
            bridge.stateChanged.connect(self._dcc_state_changed)
        self._dcc_target_signature = ()
        self._dcc_state_changed()

    @Property(float, notify=stateChanged)
    def treeWidth(self):
        return max(160.0, float(
            self._settings.get("scriptEditor/treeWidth", 200.0) or 200.0
        ))

    @Property(float, notify=stateChanged)
    def outputHeight(self):
        return max(80.0, float(
            self._settings.get("scriptEditor/outputHeight", 120.0) or 120.0
        ))

    @Slot(QObject, "QVariantMap")
    def attach_editor_document(self, quick_document, colors=None):
        """Attach rich highlighting to QML's native QTextDocument."""
        if quick_document is None:
            return
        getter = getattr(quick_document, "textDocument", None)
        document = getter() if callable(getter) else quick_document
        if document is None:
            return
        if self._syntax_highlighter is not None:
            try:
                if self._syntax_highlighter.document() is document:
                    self._syntax_highlighter.set_colors(colors or {})
                    return
            except RuntimeError:
                # The QML editor owns the QTextDocument. Unloading its window
                # deletes the C++ highlighter before Python drops the wrapper.
                self._syntax_highlighter = None
        self._syntax_highlighter = PythonSyntaxHighlighter(document, colors or {})

    @Slot(str, str, "QVariantMap")
    def update_editor_highlights(self, selected_text, search, options=None):
        if self._syntax_highlighter is not None:
            try:
                self._syntax_highlighter.set_overlays(
                    selected_text, search, options or {}
                )
            except RuntimeError:
                self._syntax_highlighter = None

    @Slot(str, int, bool, result="QVariantList")
    def code_completions(self, source, cursor_position, manual=False):
        return completion_items(source, cursor_position, manual)

    @Slot(str, result="QVariantList")
    def code_symbols(self, source):
        return document_symbols(source)

    @Slot(str, str, "QVariantMap", result="QVariantList")
    def search_matches(self, source, query, options=None):
        return find_matches(source, query, options or {})

    @Slot(str, str, int, int, result="QVariantMap")
    def apply_editor_command(self, action, source, selection_start, selection_end):
        return edit_command(
            action, source, selection_start, selection_end
        )

    @staticmethod
    def _blank_editor_state(tab_id=""):
        return {
            "tabId": str(tab_id or ""), "token": "", "folder": "",
            "title": "", "language": "local_python", "source": "",
            "runMode": "standalone", "output": "", "dirty": False,
        }

    @staticmethod
    def _default_run_mode(language):
        if language == "dcc_python":
            return "dcc"
        if language == "local_python":
            return "standalone"
        return "server"

    def _clear_saved_history(self):
        self._saved_history_records = []
        self._saved_history_token = ""
        self._saved_history_loading = False
        self.saved_history.clear()

    def _new_editor_state(self):
        used_titles = {
            str(state.get("title") or "").casefold()
            for state in self._sessions.values()
        }
        used_titles.update(
            str(record.get("title") or "").casefold()
            for record in self._scripts
        )
        index = 1
        while f"new_script_{index}" in used_titles:
            index += 1
        state = self._blank_editor_state(uuid.uuid4().hex)
        state.update({"folder": "custom", "title": f"new_script_{index}"})
        return state

    @staticmethod
    def _dcc_script_path(tab_id):
        filename = f"{uuid.uuid5(uuid.NAMESPACE_URL, str(tab_id))}.py"
        return (
            Path(env_mode.get_current_path()).resolve()
            / "custom_scripts" / ".temp" / filename
        )

    def _remove_dcc_script(self, tab_id):
        if any(
            request["tabId"] == str(tab_id or "")
            for request in self._dcc_runs.values()
        ):
            return
        self._dcc_script_path(tab_id).unlink(missing_ok=True)

    def _reset_to_new_session(self):
        for tab_id in tuple(self._sessions):
            self._remove_dcc_script(tab_id)
        self._sessions.clear()
        self._local_consoles.clear()
        self._clear_saved_history()
        state = self._new_editor_state()
        self._sessions[state["tabId"]] = state
        self._current_tab_id = state["tabId"]
        self._editor_state = state
        self._selected_token = ""
        self._refresh_tabs()
        self._schedule_session_save()
        self.editorChanged.emit(dict(state))
        self.stateChanged.emit()

    def _project_code(self):
        if self._application is not None:
            return str(self._application.current_project_code or "default")
        return "default"

    def _sessions_key(self):
        return f"scriptEditor/sessions/{self._session_project_code}"

    def _active_session_key(self):
        return f"scriptEditor/activeSession/{self._session_project_code}"

    def _restore_sessions(self):
        raw = self._settings.get(self._sessions_key(), "[]")
        try:
            records = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            records = []
        self._sessions = {}
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict):
                continue
            tab_id = str(record.get("tabId") or uuid.uuid4().hex)
            state = self._blank_editor_state(tab_id)
            state.update({
                key: record.get(key, state[key])
                for key in state
                if key in record
            })
            state["tabId"] = tab_id
            state["dirty"] = bool(state.get("dirty"))
            if not state.get("token") and not str(
                state.get("title") or ""
            ).strip():
                fresh = self._new_editor_state()
                state["folder"] = str(state.get("folder") or fresh["folder"])
                state["title"] = fresh["title"]
            if state.get("runMode") not in {"dcc", "standalone", "server"}:
                state["runMode"] = self._default_run_mode(
                    state.get("language")
                )
            self._sessions[tab_id] = state
        if not self._sessions:
            state = self._new_editor_state()
            self._sessions[state["tabId"]] = state
        preferred = str(
            self._settings.get(self._active_session_key(), "") or ""
        )
        self._current_tab_id = (
            preferred if preferred in self._sessions
            else next(iter(self._sessions), "")
        )
        self._editor_state = self._sessions.get(
            self._current_tab_id, self._blank_editor_state()
        )
        self._refresh_tabs()

    def _save_sessions(self):
        self._settings[self._sessions_key()] = json.dumps(
            list(self._sessions.values()), ensure_ascii=False
        )
        self._settings[self._active_session_key()] = self._current_tab_id
        self._write_settings()

    def _schedule_session_save(self):
        self._session_save_timer.start()

    def _refresh_tabs(self):
        self.tabs.replace([
            {
                "tabId": tab_id,
                "token": str(state.get("token") or ""),
                "title": str(state.get("title") or ""),
                "dirty": bool(state.get("dirty")),
                "current": tab_id == self._current_tab_id,
            }
            for tab_id, state in self._sessions.items()
        ])

    def _activate_session(self, tab_id, notify=True):
        tab_id = str(tab_id or "")
        if tab_id not in self._sessions:
            return {}
        self._current_tab_id = tab_id
        self._editor_state = self._sessions[tab_id]
        self._selected_token = str(self._editor_state.get("token") or "")
        if self._saved_history_token != self._selected_token:
            self._clear_saved_history()
        self._refresh_tabs()
        self._schedule_session_save()
        state = dict(self._editor_state)
        if notify:
            self.editorChanged.emit(state)
            self.stateChanged.emit()
        return state

    def _start(self, pool, callback, *args):
        if self._busy:
            return False
        if pool.is_stopped:
            pool.start()
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        worker = pool.add_task(callback, *args)
        worker.result.connect(self._done)
        worker.error.connect(self._failed)
        self._worker = worker
        worker.start()
        return True

    @Slot()
    def load(self):
        self._request_load(False)

    @Slot()
    def preload(self):
        self._request_sync()

    def _request_load(self, force):
        if self._loaded and not force:
            return
        if force:
            self._clear_saved_history()
        if self._busy:
            self._reload_after_busy = self._reload_after_busy or force
            return
        from thlib.environment import env_inst

        self._start(
            env_inst.server_pool, self._load_scripts, self._project_code()
        )

    def _request_sync(self):
        if self._busy:
            self._reload_after_busy = True
            return
        from thlib.environment import env_inst

        self._start(
            env_inst.server_pool, self._sync_scripts, self._project_code()
        )

    @Slot()
    def refresh_scripts_tree(self, async_run=True, revert=True):
        self._request_load(True)

    @Slot(object)
    def apply_server_batch(self, batch):
        project_code = self._project_code()
        records = [
            *list((batch or {}).get("cacheChanges") or []),
            *list((batch or {}).get("cacheRetired") or []),
        ]
        if any(
            str(record.get("searchType") or "").split("?", 1)[0]
            == "config/custom_script"
            and str(record.get("projectCode") or "") == project_code
            for record in records
        ):
            self._request_sync()

    def fill_sctipts_tree_widget(self, async_run=True):
        self.load()

    @Slot(str, str)
    def _project_changed(self, project_code, _title):
        project_code = str(project_code or "")
        if project_code == self._session_project_code:
            if (
                    project_code
                    and project_code != self._mirrored_project_code
                    and not self._busy):
                self._request_sync()
            return
        self._save_sessions()
        self._session_project_code = project_code or "default"
        self._loaded = False
        self._selected_token = ""
        self._clear_saved_history()
        self._current_tab_id = ""
        self._editor_state = self._blank_editor_state()
        self._restore_sessions()
        self.editorChanged.emit(dict(self._editor_state))
        if project_code:
            self._request_sync()
        else:
            self._objects.clear()
            self._scripts.clear()
            self.model.clear()
            self.stateChanged.emit()

    @Slot()
    def _sync_project_sessions(self):
        project_code = self._project_code()
        if project_code != self._session_project_code:
            self._project_changed(project_code, "")

    @staticmethod
    def _script_load_result(items, project_code):
        import thlib.tactic_classes as tc

        if isinstance(items, dict):
            items = list(items.values())
        rows = []
        objects = {}
        for item in items:
            token = ""
            for method_name in ("get_search_key", "get_code"):
                method = getattr(item, method_name, None)
                if callable(method):
                    token = str(method() or "")
                    if token:
                        break
            token = token or uuid.uuid4().hex
            while token in objects:
                token = f"{token}:{uuid.uuid4().hex[:8]}"
            objects[token] = item
            folder, title = tc.normalize_custom_script_path(
                item.get_value("folder"), item.get_value("title")
            )
            rows.append({
                "token": token,
                "folder": folder,
                "title": title,
                "language": str(item.get_value("language") or "local_python"),
            })
        return {
            "kind": "load", "rows": rows, "objects": objects,
            "projectCode": project_code,
        }

    @classmethod
    def _load_scripts(cls, project_code=""):
        import thlib.tactic_classes as tc

        items = tc.get_custom_scripts(
            store_locally=True, project=project_code or None
        ) or []
        return cls._script_load_result(items, project_code)

    @classmethod
    def _sync_scripts(cls, project_code):
        import thlib.tactic_classes as tc

        items, changed = tc.sync_custom_scripts(project_code)
        if not changed:
            items = tc.get_custom_scripts(
                store_locally=False, project=project_code
            )
        return cls._script_load_result(items or [], project_code)

    def _rebuild_tree(self):
        root = {"folders": {}, "scripts": []}
        records = self._scripts
        if self._tree_filter:
            records = [
                record for record in records
                if self._tree_filter in "{}/{}".format(
                    record["folder"], record["title"]
                ).replace("\\", "/").casefold()
            ]
        for record in records:
            node = root
            parts = [
                part for part in record["folder"].replace("\\", "/").split("/")
                if part
            ]
            for part in parts:
                node = node["folders"].setdefault(
                    part, {"folders": {}, "scripts": []}
                )
            node["scripts"].append(record)

        rows = []

        def append_node(node, parent_path="", depth=0):
            for name, child in sorted(
                node["folders"].items(), key=lambda item: item[0].casefold()
            ):
                path = f"{parent_path}/{name}".strip("/")
                expanded = bool(self._tree_filter) or path in self._expanded
                rows.append({
                    "token": f"folder:{path}", "nodeType": "folder",
                    "path": path, "folder": parent_path, "title": name,
                    "language": "", "depth": depth,
                    "expanded": expanded, "hasChildren": True,
                })
                if expanded:
                    append_node(child, path, depth + 1)
            for record in sorted(
                node["scripts"], key=lambda item: item["title"].casefold()
            ):
                rows.append({
                    **record, "nodeType": "script", "path": record["folder"],
                    "depth": depth, "expanded": False,
                    "hasChildren": False,
                })

        append_node(root)
        self.model.replace(rows)

    @Slot(str)
    def set_tree_filter(self, value):
        value = str(value or "").replace("\\", "/").strip().casefold()
        if value == self._tree_filter:
            return
        self._tree_filter = value
        self._rebuild_tree()

    @Slot(str)
    def toggle_folder(self, path):
        path = str(path or "").strip("/")
        if not path:
            return
        if path in self._expanded:
            self._expanded.remove(path)
        else:
            self._expanded.add(path)
        self._save_expanded()
        self._rebuild_tree()

    @Slot(str, result="QVariantMap")
    def script(self, token):
        token = str(token or "")
        item = self._objects.get(token)
        if not item:
            return {}
        existing = next((
            tab_id for tab_id, state in self._sessions.items()
            if state.get("token") == token
        ), "")
        if existing:
            return self._activate_session(existing)
        import thlib.tactic_classes as tc

        tab_id = uuid.uuid4().hex
        language = str(item.get_value("language") or "local_python")
        folder, title = tc.normalize_custom_script_path(
            item.get_value("folder"), item.get_value("title")
        )
        self._sessions[tab_id] = {
            "tabId": tab_id, "token": token,
            "folder": folder, "title": title,
            "language": language,
            "source": str(item.get_value("script") or ""),
            "runMode": self._default_run_mode(language),
            "output": "", "dirty": False,
        }
        return self._activate_session(tab_id)

    @Slot(str, result="QVariantMap")
    def select_tab(self, tab_id):
        return self._activate_session(tab_id)

    @Slot(str)
    def close_tab(self, tab_id):
        tab_id = str(tab_id or "")
        if tab_id not in self._sessions:
            return
        tab_ids = list(self._sessions)
        closed_row = tab_ids.index(tab_id)
        self._sessions.pop(tab_id)
        self._local_consoles.pop(tab_id, None)
        self._remove_dcc_script(tab_id)
        if tab_id == self._current_tab_id:
            remaining = list(self._sessions)
            next_row = min(closed_row, len(remaining) - 1)
            self._current_tab_id = remaining[next_row] if remaining else ""
            self._editor_state = self._sessions.get(
                self._current_tab_id, self._blank_editor_state()
            )
            self._selected_token = str(
                self._editor_state.get("token") or ""
            )
            self.editorChanged.emit(dict(self._editor_state))
        if not self._sessions:
            self._reset_to_new_session()
            return
        self._refresh_tabs()
        self._schedule_session_save()
        self.stateChanged.emit()

    @Slot(str, result="QVariantMap")
    def fill_by_sobject(self, token):
        return self.script(token)

    def scripts_tree_widget_items_selection_changed(self, token):
        return self.script(token)

    @Slot(str, str, str, str, str)
    @Slot(str, str, str, str, str, str)
    def update_editor_state(
        self, token, folder, title, language, source, run_mode=None
    ):
        if not self._current_tab_id:
            return
        state = self._sessions[self._current_tab_id]
        changed = any((
            str(state.get("token") or "") != str(token or ""),
            str(state.get("folder") or "") != str(folder or ""),
            str(state.get("title") or "") != str(title or ""),
            str(state.get("language") or "") != str(language or "local_python"),
            str(state.get("source") or "") != str(source or ""),
            run_mode is not None
            and str(state.get("runMode") or "") != str(run_mode or ""),
        ))
        state.update({
            "token": str(token or ""), "folder": str(folder or ""),
            "title": str(title or ""),
            "language": str(language or "local_python"),
            "source": str(source or ""),
        })
        if run_mode in {"dcc", "standalone", "server"}:
            state["runMode"] = str(run_mode)
        if changed:
            state["dirty"] = True
            self._refresh_tabs()
            self._schedule_session_save()
            self.stateChanged.emit()

    def get_current_script_language(self):
        value = self._editor_state["language"]
        option = next((
            item for item in self.languages if item["value"] == value
        ), self.languages[0])
        return option["label"], option["value"]

    def get_current_script(self):
        return self._editor_state["source"]

    def get_current_script_sobject(self):
        return self._objects.get(self._editor_state["token"])

    @Slot()
    def create_new_script(self):
        state = self._new_editor_state()
        self._sessions[state["tabId"]] = state
        self._activate_session(state["tabId"], notify=False)
        self.newScriptRequested.emit()
        self.editorChanged.emit(dict(self._editor_state))
        self.stateChanged.emit()

    @Slot()
    def request_close_all(self):
        dirty_count = sum(
            bool(state.get("dirty")) for state in self._sessions.values()
        )
        if dirty_count:
            self.closeAllConfirmationRequested.emit(dirty_count)
            return
        self._reset_to_new_session()

    @Slot()
    def confirm_close_all_discard(self):
        self._reset_to_new_session()

    @Slot(result=bool)
    def confirm_close_all_save(self):
        if self._busy:
            return False
        payloads = []
        valid_languages = {item["value"] for item in self.languages}
        for tab_id, state in self._sessions.items():
            if not state.get("dirty"):
                continue
            folder = str(state.get("folder") or "").strip().strip("/")
            title = str(state.get("title") or "").strip()
            language = str(state.get("language") or "local_python")
            if not folder or not title:
                self._error = "Folder and title are required"
                self.stateChanged.emit()
                return False
            location = self._validated_script_location(folder, title)
            if location is None:
                return False
            folder, title = location
            if language not in valid_languages:
                self._error = "Unsupported script language"
                self.stateChanged.emit()
                return False
            payloads.append((
                tab_id, str(state.get("token") or ""), folder, title,
                language, str(state.get("source") or ""),
            ))
        if not payloads:
            self._reset_to_new_session()
            return True
        from thlib.environment import env_inst

        return self._start(
            env_inst.server_pool, self._save_all_scripts, payloads
        )

    def _save_all_scripts(self, payloads):
        return {
            "kind": "bulk_saved",
            "items": [self._save_script(payload) for payload in payloads],
        }

    def _validated_script_location(self, folder, title):
        import thlib.tactic_classes as tc

        try:
            return tc.normalize_custom_script_path(folder, title)
        except ValueError as error:
            self._error = str(error)
            self.stateChanged.emit()
            return None

    @Slot(str, str, str, str, str, result=bool)
    def save(self, token, folder, title, language, source):
        folder = str(folder or "").strip().strip("/")
        title = str(title or "").strip()
        language = str(language or "local_python")
        if self._busy or not folder or not title:
            self._error = "Folder and title are required"
            self.stateChanged.emit()
            return False
        location = self._validated_script_location(folder, title)
        if location is None:
            return False
        folder, title = location
        if language not in {item["value"] for item in self.languages}:
            self._error = "Unsupported script language"
            self.stateChanged.emit()
            return False
        from thlib.environment import env_inst

        payload = (
            self._current_tab_id, str(token or ""), folder, title,
            language, str(source or ""),
        )
        return self._start(env_inst.server_pool, self._save_script, payload)

    @Slot(str, str, str, str, str, result=bool)
    def save_current_script(self, token, folder, title, language, source):
        return self.save(token, folder, title, language, source)

    def _save_script(self, payload):
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        tab_id, token, folder, title, language, source = payload
        item = self._objects.get(token)
        if item:
            for key, value in {
                "script": source, "language": language,
                "folder": folder, "title": title,
            }.items():
                item.set_value(key, value)
            item.commit(False)
        else:
            search_type = tc.server_start().build_search_type(
                "config/custom_script",
                project_code=env_inst.get_current_project(),
            )
            tc.server_start().insert(search_type, {
                "script": source, "folder": folder,
                "title": title, "language": language,
            })
        return {
            "kind": "saved", "tabId": tab_id,
            "folder": folder, "title": title,
        }

    def _saved_history_summary(self, record):
        if str(record.get("action") or "") == "create":
            return self.tr("Script created")
        labels = {
            "script": self.tr("Source"),
            "folder": self.tr("Folder"),
            "title": self.tr("Title"),
            "language": self.tr("Language"),
        }
        changed = [
            labels.get(str(field), str(field).replace("_", " "))
            for field in record.get("changedFields") or []
        ]
        changed = list(dict.fromkeys(filter(None, changed)))
        if not changed:
            return self.tr("Saved version")
        return self.tr("Changed: {fields}").format(
            fields=", ".join(changed)
        )

    def _refresh_saved_history_model(self):
        records = []
        for raw_record in self._saved_history_records:
            record = dict(raw_record)
            pretty, full = activity_timestamp_labels(
                record.get("timestamp")
            )
            record.update({
                "timestampPretty": pretty or self.tr("Saved version"),
                "timestampFull": full or pretty,
                "actorDisplay": str(record.get("actor") or ""),
                "summary": self._saved_history_summary(record),
                "selected": False,
            })
            records.append(record)
        self.saved_history.replace(records)

    @staticmethod
    def _request_saved_history(
        action, project_code, tab_id, token, revision_id=""
    ):
        import thlib.tactic_classes as tc

        result = tc.execute_procedure_serverside(
            script_history_request,
            {
                "action": action,
                "project_code": project_code,
                "search_key": token,
                "revision_id": revision_id,
            },
            project=project_code,
        )
        payload = dict(result or {})
        payload.update({
            "kind": "saved_history" if action == "history" else "saved_revision",
            "tabId": tab_id,
            "token": token,
        })
        return payload

    @Slot(result=bool)
    def load_saved_history(self):
        token = str(self._editor_state.get("token") or "")
        if not token or token not in self._objects:
            return False
        if self.savedHistoryLoaded:
            return True
        if self._busy:
            return False
        from thlib.environment import env_inst

        self._saved_history_loading = True
        started = self._start(
            env_inst.server_pool,
            self._request_saved_history,
            "history",
            self._project_code(),
            self._current_tab_id,
            token,
        )
        if not started:
            self._saved_history_loading = False
        self.stateChanged.emit()
        return started

    @Slot(str, result=bool)
    def restore_saved_revision(self, revision_id):
        revision_id = str(revision_id or "")
        token = str(self._editor_state.get("token") or "")
        if (
            self._busy
            or not revision_id
            or not token
            or token != self._saved_history_token
            or not any(
                str(record.get("revisionId") or "") == revision_id
                for record in self._saved_history_records
            )
        ):
            return False
        from thlib.environment import env_inst

        self._saved_history_loading = True
        started = self._start(
            env_inst.server_pool,
            self._request_saved_history,
            "revision",
            self._project_code(),
            self._current_tab_id,
            token,
            revision_id,
        )
        if not started:
            self._saved_history_loading = False
        self.stateChanged.emit()
        return started

    @Slot(str, result="QVariantList")
    def scripts_context_menu(self, token):
        if str(token or "") not in self._objects:
            return []
        return [
            {"title": "Copy Script Runner", "icon": "content_copy",
             "command": "copy_runner"},
            {"separator": True},
            {"title": "Delete from server", "icon": "delete",
             "command": "delete", "enabled": not self._busy},
        ]

    @Slot(str, result="QVariantList")
    def open_menu(self, token):
        return self.scripts_context_menu(token)

    def create_scripts_tree_context_menu(self, token=""):
        return self.scripts_context_menu(token or self._selected_token)

    @Slot(str, result=str)
    def create_execution_script(self, token):
        item = self._objects.get(str(token or ""))
        if not item:
            return ""
        project = item.get_project()
        project_code = project.get_code() if project else ""
        folder = str(item.get_value("folder") or "")
        title = str(item.get_value("title") or "")
        script_path = f"{folder}/{title}".strip("/")
        procedure = (
            "import thlib.environment as thenv\n"
            "thenv.tc().execute_custom_script("
            f"{script_path!r}, project={str(project_code)!r})"
        )
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(procedure)
        self._append_output("Script runner copied to clipboard.")
        return procedure

    @Slot(str)
    def request_delete_script(self, token):
        item = self._objects.get(str(token or ""))
        if not item or self._busy:
            return
        self._pending_delete = str(token)
        title = str(item.get_value("title") or "script")
        self.deleteConfirmationRequested.emit(str(token), title)

    def delete_script_sobject(self, token=""):
        self.request_delete_script(token or self._selected_token)

    @Slot()
    def confirm_delete_script(self):
        token, self._pending_delete = self._pending_delete, ""
        item = self._objects.get(token)
        if not item:
            return
        from thlib.environment import env_inst

        self._start(env_inst.server_pool, self._delete_script, token, item)

    @staticmethod
    def _delete_script(token, item):
        item.delete_sobject()
        return {"kind": "deleted", "token": token}

    @Slot()
    def cancel_delete_script(self):
        self._pending_delete = ""

    @Slot(str, str, str)
    @Slot(str, str)
    def request_run(self, mode, language, source=None):
        if source is None:
            source = language
            language = mode
            mode = self._default_run_mode(language)
        mode = str(mode or "")
        language = str(language or "")
        source = str(source or "").replace("\u2029", "\n").replace("\u2028", "\n")
        option = next((
            item for item in self.languages if item["value"] == language
        ), None)
        if self._busy or not source.strip():
            return
        if mode not in {"dcc", "standalone", "server"}:
            self._error = "Choose a valid execution mode"
            self.stateChanged.emit()
            return
        if not option or not option["runnable"]:
            self._error = "This language is editable but not executable"
            self.stateChanged.emit()
            return
        self._pending = {
            "mode": mode, "language": language, "source": source,
            "tabId": self._current_tab_id,
        }
        self.confirm_run()

    @Slot()
    @Slot(str, str, str)
    def run_script(self, mode=None, language=None, source=None):
        if mode is None:
            language = self._editor_state["language"]
            mode = self._editor_state.get("runMode")
            if mode not in {"dcc", "standalone", "server"}:
                mode = self._default_run_mode(language)
            source = self._editor_state["source"]
        self.request_run(mode, language, source)

    @Slot(str, result=bool)
    def run_saved_script(self, path):
        path = str(path or "").strip("/")
        record = next((
            row for row in self._scripts
            if "{}/{}".format(
                str(row.get("folder") or "").strip("/"),
                str(row.get("title") or ""),
            ).strip("/") == path
        ), {})
        item = self._objects.get(str(record.get("token") or ""))
        if self._busy or not item:
            return False
        language = str(item.get_value("language") or "local_python")
        option = next((
            value for value in self.languages
            if value["value"] == language
        ), None)
        if not option or not option["runnable"]:
            return False
        source = str(item.get_value("script") or "")
        if not source.strip():
            self._error = self.tr("The saved script is empty")
            self.stateChanged.emit()
            return False
        self._pending = {
            "mode": self._default_run_mode(language),
            "language": language,
            "source": source,
            "tabId": self._current_tab_id,
            "savedScript": path,
        }
        self.confirm_run()
        return self._busy

    def saved_script_definition(self, path: str) -> dict:
        """Return one saved executable script without changing editor state."""
        path = str(path or "").strip("/")
        record = next((
            row for row in self._scripts
            if "{}/{}".format(
                str(row.get("folder") or "").strip("/"),
                str(row.get("title") or ""),
            ).strip("/") == path
        ), {})
        item = self._objects.get(str(record.get("token") or ""))
        if not item:
            return {}
        language = str(item.get_value("language") or "local_python")
        option = next((
            value for value in self.languages
            if value["value"] == language
        ), {})
        source = str(item.get_value("script") or "")
        if not option.get("runnable") or not source.strip():
            return {}
        return {"path": path, "language": language, "source": source}

    @Slot()
    def confirm_run(self):
        if not self._pending:
            return
        payload, self._pending = self._pending, {}
        from thlib.environment import env_inst

        self._operation_tab_id = payload["tabId"]
        self._begin_run_error_output()
        if payload["mode"] == "dcc":
            started = self._start_dcc(
                payload["source"], payload["tabId"],
                payload.get("savedScript", ""),
            )
        elif payload["mode"] == "standalone":
            started = self._start_local(
                payload["source"], payload["tabId"]
            )
        else:
            started = self._start(
                env_inst.server_pool, self._run_server,
                payload["source"], payload["tabId"],
            )
        if not started:
            self._operation_tab_id = ""
            self._end_run_error_output()

    def _start_dcc(self, source, tab_id, saved_script=""):
        if self._busy:
            return False
        if not self._dcc_target():
            message = self.tr("No capable DCC client is selected")
            self._error = message
            self._append_output(message, tab_id)
            return False
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        state = self._sessions.get(str(tab_id or ""), {})
        if not saved_script and state.get("token") and not state.get("dirty"):
            if source == str(state.get("source") or ""):
                saved_script = "{}/{}".format(
                    str(state.get("folder") or "").strip("/"),
                    str(state.get("title") or ""),
                ).strip("/")
        path = None
        try:
            if saved_script and self._dcc_bridge.has_dcc_capability(
                "execute_custom_script"
            ):
                action = "execute_custom_script"
                command = {
                    "project": self._project_code(),
                    "script": saved_script,
                }
            else:
                action = "execute_script_file"
                path = self._dcc_script_path(tab_id)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(str(source or ""), encoding="utf-8")
                command = {"path": str(path)}
            request_id = self._dcc_bridge.send_active_command(
                action, command, 300.0
            )
        except (OSError, RuntimeError) as error:
            self._busy = False
            self._append_output(str(error), tab_id)
            self.stateChanged.emit()
            return False
        if not request_id:
            self._busy = False
            self._append_output(
                str(getattr(self._dcc_bridge, "error", "") or
                    "The DCC script could not be started"),
                tab_id,
            )
            self.stateChanged.emit()
            return False
        self._dcc_runs[str(request_id)] = {
            "tabId": str(tab_id or ""), "path": path,
        }
        return True

    @Slot(str, bool, "QVariantMap", str)
    def _dcc_command_finished(self, request_id, success, payload, error):
        request = self._dcc_runs.pop(str(request_id or ""), None)
        if not request:
            return
        if request["tabId"] not in self._sessions:
            if request["path"]:
                request["path"].unlink(missing_ok=True)
            self._operation_tab_id = ""
            self._end_run_error_output()
            self._busy = False
            self.stateChanged.emit()
            return
        if success:
            self._done({
                "kind": "run",
                "tabId": request["tabId"],
                "output": str(dict(payload or {}).get("output") or ""),
            })
            return
        self._failed({
            "exception": RuntimeError(str(error or "DCC script failed")),
            "stacktrace": str(error or "DCC script failed"),
        })

    def _start_local(self, source, tab_id):
        """Run native Local Python on Qt's GUI thread, as the legacy editor did."""
        if self._busy:
            return False
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        self._executeLocalRequested.emit(source, tab_id)
        return True

    def _execute_local_on_gui(self, source, tab_id):
        try:
            result = self._run_local(source, tab_id)
        except BaseException as error:
            self._failed({
                "exception": error,
                "stacktrace": traceback.format_exc(),
            })
        else:
            self._done(result)

    @Slot()
    def hide(self):
        if self._application is not None:
            self._application.window_model.close_window("script_editor")

    def _begin_run_error_output(self):
        if self._run_error_output_active:
            return
        self._run_error_output_active = True
        begin = getattr(self._debug_log, "begin_inline_error_output", None)
        if callable(begin):
            begin(self._run_error_owner)

    def _end_run_error_output(self):
        if not self._run_error_output_active:
            return
        self._run_error_output_active = False
        end = getattr(self._debug_log, "end_inline_error_output", None)
        if callable(end):
            end(self._run_error_owner)

    def execute_source_code(self, source_code):
        return self._run_local(
            str(source_code or ""), self._current_tab_id
        )

    def _run_local(self, source, tab_id=""):
        output = io.StringIO()
        console = self._local_consoles.setdefault(
            str(tab_id or "default"),
            code.InteractiveConsole({"__name__": "__main__"}),
        )
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            console.runsource(
                source, "<TACTIC Script Editor>", "exec"
            )
        return {
            "kind": "run", "tabId": str(tab_id or ""),
            "output": output.getvalue(),
        }

    def _run_server(self, source, tab_id=""):
        import thlib.tactic_classes as tc

        started = time.monotonic()
        output_scope = getattr(
            self._debug_log, "script_editor_output", contextlib.nullcontext
        )
        with output_scope():
            result = tc.execute_procedure_serverside(
                lambda: None, {"code": source}
            )
        elapsed = time.monotonic() - started
        return {
            "kind": "run", "tabId": str(tab_id or ""),
            "output": (
                f"Server-Side execution time: {elapsed:.3f}s\n"
                f"{pprint.pformat(result)}"
            ),
        }

    def run_locally(self, whole=False, source=None):
        if isinstance(whole, str) and source is None:
            source = whole
        self.request_run(
            "standalone", self._editor_state["language"],
            self._editor_state["source"] if source is None else source,
        )

    def run_serverside(self, whole=True, source=None):
        if isinstance(whole, str) and source is None:
            source = whole
        self.request_run(
            "server", self._editor_state["language"],
            self._editor_state["source"] if source is None else source,
        )

    @Slot()
    def cancel_run(self):
        self._pending = {}

    @Slot()
    def clear_output(self):
        if self._current_tab_id in self._sessions:
            self._sessions[self._current_tab_id]["output"] = ""
            self._schedule_session_save()
        self._error = ""
        self.stateChanged.emit()

    @Slot()
    def cleanup_output(self):
        self.clear_output()

    @Slot(str, result="QVariantMap")
    def handle_scripts_language_combo_box(self, language):
        language = str(language or "")
        option = next((
            item for item in self.languages if item["value"] == language
        ), {})
        return {
            "mode": self._default_run_mode(language),
            "runnable": bool(option.get("runnable")),
        }

    @Slot(float, float)
    def set_layout(self, tree_width, output_height):
        if float(tree_width) >= 120:
            self._settings["scriptEditor/treeWidth"] = float(tree_width)
        if float(output_height) >= 70:
            self._settings["scriptEditor/outputHeight"] = float(output_height)
        self._write_settings()

    @Slot(result=str)
    def get_scripts_tree_state(self):
        return json.dumps(sorted(self._expanded), ensure_ascii=False)

    @Slot(str)
    def revert_scripts_tree_state(self, state_raw):
        try:
            values = json.loads(str(state_raw or "[]"))
            self._expanded = {str(value) for value in values if str(value)}
        except (TypeError, ValueError, json.JSONDecodeError):
            self._expanded = set()
        self._save_expanded()
        self._rebuild_tree()

    @Slot(result="QVariantMap")
    def get_settings_dict(self):
        return {
            "treeWidth": self.treeWidth,
            "outputHeight": self.outputHeight,
            "treeCollapsed": bool(self._settings.get(
                "scriptEditor/treeCollapsed", False
            )),
            "outputCollapsed": bool(self._settings.get(
                "scriptEditor/outputCollapsed", False
            )),
            "outputWrap": bool(self._settings.get(
                "scriptEditor/outputWrap", False
            )),
            "sidePanelMode": str(self._settings.get(
                "scriptEditor/sidePanelMode", "scripts"
            ) or "scripts"),
            "editorFontSize": float(self._settings.get(
                "scriptEditor/editorFontSize", 9.25
            ) or 9.25),
            "scriptsTree": self.get_scripts_tree_state(),
        }

    @Slot("QVariantMap")
    def set_settings_from_dict(self, values=None):
        values = dict(values or {})
        for name in ("treeCollapsed", "outputCollapsed", "outputWrap"):
            if name in values:
                self._settings[f"scriptEditor/{name}"] = bool(values[name])
        side_panel = str(values.get("sidePanelMode") or "")
        if side_panel in {"scripts", "outline"}:
            self._settings["scriptEditor/sidePanelMode"] = side_panel
        if "editorFontSize" in values:
            self._settings["scriptEditor/editorFontSize"] = max(
                6.0, min(32.0, float(values["editorFontSize"]))
            )
        if "scriptsTree" in values:
            self.revert_scripts_tree_state(str(values["scriptsTree"]))
        self.set_layout(
            float(values.get("treeWidth") or self.treeWidth),
            float(values.get("outputHeight") or self.outputHeight),
        )

    @Slot()
    def readSettings(self):
        self._expanded = self._restore_expanded()
        self._rebuild_tree()
        self.stateChanged.emit()

    @Slot()
    def writeSettings(self):
        self._save_expanded()
        self._save_sessions()
        self._write_settings()

    @Slot()
    def shutdown(self):
        self._session_save_timer.stop()
        self.writeSettings()

    def showEvent(self, _event=None):
        self.readSettings()
        self.load()

    def closeEvent(self, _event=None):
        self.writeSettings()

    def _restore_expanded(self):
        raw = self._settings.get("scriptEditor/expandedFolders", "[]")
        try:
            values = json.loads(raw)
            return {str(value) for value in values if str(value)}
        except (TypeError, ValueError, json.JSONDecodeError):
            return set()

    def _save_expanded(self):
        self._settings["scriptEditor/expandedFolders"] = json.dumps(
            sorted(self._expanded), ensure_ascii=False
        )

    def _write_settings(self):
        env_write_config(
            self._settings,
            filename="ui_script_editor",
            unique_id="ui_main",
            long_abs_path=True,
        )

    def _append_output(self, value, tab_id=""):
        value = str(value or "").rstrip()
        if not value:
            return
        target_id = str(tab_id or self._current_tab_id)
        state = self._sessions.get(target_id)
        if not state:
            target_id = target_id or uuid.uuid4().hex
            state = self._blank_editor_state(target_id)
            self._sessions[target_id] = state
            self._activate_session(target_id, notify=False)
        state["output"] = (
            f"{str(state.get('output') or '').rstrip()}\n{value}".lstrip()
        )
        self._schedule_session_save()
        self.stateChanged.emit()
        self.outputAppended.emit(target_id)

    @Slot(str, str)
    def append_trigger_output(self, script_path, value):
        """Write hook diagnostics to the matching open script console."""
        script_path = str(script_path or "").strip("/")
        tab_id = next((
            session_id
            for session_id, state in self._sessions.items()
            if "{}/{}".format(
                str(state.get("folder") or "").strip("/"),
                str(state.get("title") or ""),
            ).strip("/") == script_path
        ), self._current_tab_id)
        self._append_output(value, tab_id)

    @Slot(object)
    def _done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        result = result or {}
        kind = result.get("kind")
        if kind == "load":
            self._mirrored_project_code = str(
                result.get("projectCode") or self._project_code()
            )
            self._objects = result["objects"]
            self._scripts = result["rows"]
            self._loaded = True
            self._rebuild_tree()
            current_refreshed = False
            rows_by_token = {row["token"]: row for row in self._scripts}
            for tab_id, state in self._sessions.items():
                token = str(state.get("token") or "")
                item = self._objects.get(token)
                if item is None or state.get("dirty"):
                    continue
                record = rows_by_token[token]
                language = str(
                    item.get_value("language") or "local_python"
                )
                state.update({
                    "folder": record["folder"], "title": record["title"],
                    "language": language,
                    "source": str(item.get_value("script") or ""),
                    "runMode": self._default_run_mode(language),
                })
                current_refreshed = current_refreshed or (
                    tab_id == self._current_tab_id
                )
            selected = self._selected_token if self._selected_token in self._objects else ""
            if self._pending_selection:
                pending_tab_id, folder, title = self._pending_selection
                matched_token = next((
                    item["token"] for item in self._scripts
                    if item["folder"] == folder and item["title"] == title
                ), "")
                self._pending_selection = None
                state = self._sessions.get(pending_tab_id)
                if state and matched_token:
                    state["token"] = matched_token
                    state["dirty"] = False
                    if pending_tab_id == self._current_tab_id:
                        selected = matched_token
                        current_refreshed = True
            self._selected_token = selected
            self._refresh_tabs()
            self._schedule_session_save()
            if current_refreshed:
                self.editorChanged.emit(dict(self._editor_state))
            self.scriptsLoaded.emit(selected)
        elif kind == "saved":
            self._clear_saved_history()
            tab_id = str(result.get("tabId") or self._current_tab_id)
            state = self._sessions.get(tab_id)
            if state:
                state["dirty"] = False
                self._refresh_tabs()
            self._append_output("Script saved.", tab_id)
            self._pending_selection = (
                tab_id, result["folder"], result["title"]
            )
        elif kind == "bulk_saved":
            self._clear_saved_history()
            self._reset_to_new_session()
        elif kind == "deleted":
            self._clear_saved_history()
            if result.get("token") == self._selected_token:
                self._selected_token = ""
                self.newScriptRequested.emit()
            target_id = next((
                tab_id for tab_id, state in self._sessions.items()
                if state.get("token") == result.get("token")
            ), self._current_tab_id)
            self._append_output("Script deleted.", target_id)
        elif kind == "run":
            self._end_run_error_output()
            self._append_output(
                result.get("output") or "Completed without output.",
                str(result.get("tabId") or self._operation_tab_id),
            )
            self._operation_tab_id = ""
        elif kind == "saved_history":
            tab_id = str(result.get("tabId") or "")
            token = str(result.get("token") or "")
            if (
                not result.get("entryMissing")
                and tab_id == self._current_tab_id
                and token == str(self._editor_state.get("token") or "")
            ):
                self._saved_history_records = [
                    dict(record) for record in result.get("history") or []
                ]
                self._saved_history_token = token
                self._refresh_saved_history_model()
            elif result.get("entryMissing"):
                self._error = self.tr(
                    "The custom script no longer exists on the server"
                )
        elif kind == "saved_revision":
            tab_id = str(result.get("tabId") or "")
            token = str(result.get("token") or "")
            revision = dict(result.get("revision") or {})
            if (
                tab_id == self._current_tab_id
                and token == str(self._editor_state.get("token") or "")
                and "script" in revision
            ):
                self.savedRevisionReady.emit(str(revision.get("script") or ""))
        self._saved_history_loading = False
        self._busy = False
        self._worker = None
        self.stateChanged.emit()
        if kind in {"saved", "bulk_saved", "deleted"}:
            self._loaded = False
            self._request_load(True)
        elif self._reload_after_busy:
            self._reload_after_busy = False
            self._loaded = False
            self._request_load(True)

    @Slot(object)
    def _failed(self, payload):
        self._end_run_error_output()
        worker_payload = payload[0] if isinstance(payload, tuple) else payload
        if isinstance(worker_payload, dict):
            error = worker_payload.get("exception") or "Script execution failed"
            stack = worker_payload.get("stacktrace") or str(error)
        else:
            error = worker_payload
            stack = traceback.format_exc()
        self._busy = False
        self._saved_history_loading = False
        self._loaded = False
        self._worker = None
        self._error = ""
        details = str(stack or "").strip()
        if not details or details == "NoneType: None":
            details = str(error)
        self._append_output(details, self._operation_tab_id)
        self._operation_tab_id = ""
        self.stateChanged.emit()
