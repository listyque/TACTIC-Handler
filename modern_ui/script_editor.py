from __future__ import annotations

import code
import contextlib
import io
import json
import pprint
import time
import traceback
import uuid

from PySide6.QtCore import QObject, Property, QSettings, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication

from modern_ui.workspace_models.records import RecordListModel


class ScriptEditorController(QObject):
    stateChanged = Signal()
    confirmationRequested = Signal(str)
    deleteConfirmationRequested = Signal(str, str)
    closeAllConfirmationRequested = Signal(int)
    scriptsLoaded = Signal(str)
    newScriptRequested = Signal()
    editorChanged = Signal("QVariantMap")

    languages = [
        {"label": "Local Python", "value": "local_python", "runnable": True},
        {"label": "Server Python", "value": "python", "runnable": True},
        {"label": "JavaScript", "value": "javascript", "runnable": False},
        {"label": "Server JS", "value": "server_js", "runnable": True},
        {"label": "Expression", "value": "expression", "runnable": True},
        {"label": "XML", "value": "xml", "runnable": False},
    ]
    run_modes = [
        {"label": "Locally", "value": "local"},
        {"label": "Server-Side", "value": "server"},
    ]

    def __init__(self, application, debug_log, parent=None):
        super().__init__(parent)
        self._application = application
        self._debug_log = debug_log
        self._settings = QSettings("TACTIC-Handler", "modern-qml")
        self.model = RecordListModel((
            "token", "nodeType", "path", "folder", "title", "language",
            "depth", "expanded", "hasChildren",
        ))
        self.tabs = RecordListModel((
            "tabId", "token", "title", "dirty", "current",
        ))
        self._objects = {}
        self._scripts = []
        self._expanded = self._restore_expanded()
        self._busy = False
        self._loaded = False
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
        self._run_error_owner = "script-editor-run"
        self._run_error_output_active = False
        self._local_consoles = {}
        self._session_save_timer = QTimer(self)
        self._session_save_timer.setSingleShot(True)
        self._session_save_timer.setInterval(250)
        self._session_save_timer.timeout.connect(self._save_sessions)
        if self._application is not None:
            self._application.project_changed.connect(self._project_changed)
            if self._application.current_project_code:
                QTimer.singleShot(0, self.preload)

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

    @Property("QVariantList", constant=True)
    def languageOptions(self):
        return self.languages

    @Property("QVariantList", constant=True)
    def runModeOptions(self):
        return self.run_modes

    @Property(float, notify=stateChanged)
    def treeWidth(self):
        return max(160.0, self._settings.value(
            "scriptEditor/treeWidth", 220.0, type=float
        ))

    @Property(float, notify=stateChanged)
    def outputHeight(self):
        return max(90.0, self._settings.value(
            "scriptEditor/outputHeight", 150.0, type=float
        ))

    @staticmethod
    def _blank_editor_state(tab_id=""):
        return {
            "tabId": str(tab_id or ""), "token": "", "folder": "",
            "title": "", "language": "local_python", "source": "",
            "runMode": "local", "output": "", "dirty": False,
        }

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

    def _reset_to_new_session(self):
        self._sessions.clear()
        self._local_consoles.clear()
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
        raw = self._settings.value(self._sessions_key(), "[]", type=str)
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
            self._sessions[tab_id] = state
        if not self._sessions:
            state = self._new_editor_state()
            self._sessions[state["tabId"]] = state
        preferred = self._settings.value(
            self._active_session_key(), "", type=str
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
        self._settings.setValue(
            self._sessions_key(),
            json.dumps(list(self._sessions.values()), ensure_ascii=False),
        )
        self._settings.setValue(
            self._active_session_key(), self._current_tab_id
        )
        self._settings.sync()

    def _schedule_session_save(self):
        self._session_save_timer.start()

    def _refresh_tabs(self):
        self.tabs.replace([
            {
                "tabId": tab_id,
                "token": str(state.get("token") or ""),
                "title": str(state.get("title") or "Untitled"),
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
        self._request_load(False)

    def _request_load(self, force):
        if self._loaded and not force:
            return
        if self._busy:
            self._reload_after_busy = self._reload_after_busy or force
            return
        from thlib.environment import env_inst

        self._start(env_inst.server_pool, self._load_scripts)

    @Slot()
    def refresh_scripts_tree(self, async_run=True, revert=True):
        self._request_load(True)

    def fill_sctipts_tree_widget(self, async_run=True):
        self.load()

    @Slot(str, str)
    def _project_changed(self, project_code, _title):
        self._save_sessions()
        self._session_project_code = str(project_code or "default")
        self._loaded = False
        self._selected_token = ""
        self._current_tab_id = ""
        self._editor_state = self._blank_editor_state()
        self._restore_sessions()
        self.editorChanged.emit(dict(self._editor_state))
        if project_code:
            self._request_load(True)
        else:
            self._objects.clear()
            self._scripts.clear()
            self.model.clear()
            self.stateChanged.emit()

    @staticmethod
    def _load_scripts():
        import thlib.tactic_classes as tc

        items = tc.get_custom_scripts(store_locally=False) or []
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
            rows.append({
                "token": token,
                "folder": str(item.get_value("folder") or ""),
                "title": str(item.get_value("title") or ""),
                "language": str(item.get_value("language") or "local_python"),
            })
        return {"kind": "load", "rows": rows, "objects": objects}

    def _rebuild_tree(self):
        root = {"folders": {}, "scripts": []}
        for record in self._scripts:
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
                expanded = path in self._expanded
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
        tab_id = uuid.uuid4().hex
        self._sessions[tab_id] = {
            "tabId": tab_id, "token": token,
            "folder": str(item.get_value("folder") or ""),
            "title": str(item.get_value("title") or ""),
            "language": str(item.get_value("language") or "local_python"),
            "source": str(item.get_value("script") or ""),
            "runMode": "local" if str(
                item.get_value("language") or "local_python"
            ) == "local_python" else "server",
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
        if run_mode in {"local", "server"}:
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

    @Slot(str, str, str, str, str, result=bool)
    def save(self, token, folder, title, language, source):
        folder = str(folder or "").strip().strip("/")
        title = str(title or "").strip()
        language = str(language or "local_python")
        if self._busy or not folder or not title:
            self._error = "Folder and title are required"
            self.stateChanged.emit()
            return False
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

    @Slot(str, result="QVariantList")
    def scripts_context_menu(self, token):
        if str(token or "") not in self._objects:
            return []
        return [
            {"title": "Copy Script Runner", "icon": "content_copy",
             "command": "copy_runner"},
            {"separator": True},
            {"title": "Delete", "icon": "delete", "command": "delete"},
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
        item.delete_sobject(confirm=False)
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
            mode = "local" if language == "local_python" else "server"
        mode = str(mode or "")
        language = str(language or "")
        source = str(source or "").replace("\u2029", "\n").replace("\u2028", "\n")
        option = next((
            item for item in self.languages if item["value"] == language
        ), None)
        if self._busy or not source.strip():
            return
        if mode not in {"local", "server"}:
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
            mode = "local" if language == "local_python" else "server"
            source = self._editor_state["source"]
        self.request_run(mode, language, source)

    @Slot()
    def confirm_run(self):
        if not self._pending:
            return
        payload, self._pending = self._pending, {}
        from thlib.environment import env_inst

        self._operation_tab_id = payload["tabId"]
        self._begin_run_error_output()
        if payload["mode"] == "local":
            started = self._start(
                env_inst.local_pool, self._run_local,
                payload["source"], payload["tabId"],
            )
        else:
            started = self._start(
                env_inst.server_pool, self._run_server,
                payload["source"], payload["tabId"],
            )
        if not started:
            self._end_run_error_output()

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
            "local", self._editor_state["language"],
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
            "mode": "local" if language == "local_python" else "server",
            "runnable": bool(option.get("runnable")),
        }

    @Slot(float, float)
    def set_layout(self, tree_width, output_height):
        if float(tree_width) >= 120:
            self._settings.setValue("scriptEditor/treeWidth", float(tree_width))
        if float(output_height) >= 70:
            self._settings.setValue(
                "scriptEditor/outputHeight", float(output_height)
            )

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
            "scriptsTree": self.get_scripts_tree_state(),
        }

    @Slot("QVariantMap")
    def set_settings_from_dict(self, values=None):
        values = dict(values or {})
        self.set_layout(
            float(values.get("treeWidth") or self.treeWidth),
            float(values.get("outputHeight") or self.outputHeight),
        )
        if "scriptsTree" in values:
            self.revert_scripts_tree_state(str(values["scriptsTree"]))

    @Slot()
    def readSettings(self):
        self._expanded = self._restore_expanded()
        self._rebuild_tree()
        self.stateChanged.emit()

    @Slot()
    def writeSettings(self):
        self._save_expanded()
        self._save_sessions()
        self._settings.sync()

    def showEvent(self, _event=None):
        self.readSettings()
        self.load()

    def closeEvent(self, _event=None):
        self.writeSettings()

    def _restore_expanded(self):
        raw = self._settings.value(
            "scriptEditor/expandedFolders", "[]", type=str
        )
        try:
            values = json.loads(raw)
            return {str(value) for value in values if str(value)}
        except (TypeError, ValueError, json.JSONDecodeError):
            return set()

    def _save_expanded(self):
        self._settings.setValue(
            "scriptEditor/expandedFolders",
            json.dumps(sorted(self._expanded), ensure_ascii=False),
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

    @Slot(object)
    def _done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        result = result or {}
        kind = result.get("kind")
        if kind == "load":
            self._objects = result["objects"]
            self._scripts = result["rows"]
            self._loaded = True
            self._rebuild_tree()
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
            self._selected_token = selected
            self._refresh_tabs()
            self._schedule_session_save()
            self.scriptsLoaded.emit(selected)
        elif kind == "saved":
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
            self._reset_to_new_session()
        elif kind == "deleted":
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
        self._busy = False
        self._worker = None
        self.stateChanged.emit()
        if kind in {"saved", "bulk_saved", "deleted"}:
            self._loaded = False
            QTimer.singleShot(0, lambda: self._request_load(True))
        elif self._reload_after_busy:
            self._reload_after_busy = False
            self._loaded = False
            QTimer.singleShot(0, lambda: self._request_load(True))

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
        self._loaded = False
        self._worker = None
        self._error = ""
        details = str(stack or "").strip()
        if not details or details == "NoneType: None":
            details = str(error)
        self._append_output(details, self._operation_tab_id)
        self._operation_tab_id = ""
        self.stateChanged.emit()
