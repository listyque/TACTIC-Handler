"""Project script hooks for explicit TACTIC Handler actions."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import time
import traceback
import types
import uuid
from collections.abc import Callable, Mapping

from PySide6.QtCore import QObject, Property, Signal, Slot

from tactic_handler_dcc.connectors import dcc_trigger_actions
from thlib.ui.workspace_models.records import RecordListModel


SCRIPT_TRIGGER_TYPE = "handler_script_hook"
SCRIPT_TRIGGER_EVENT_PREFIX = "handler|"

_RULE_ROLES = (
    "ruleId", "code", "title", "description", "action", "phase",
    "searchType", "searchKeysText", "process", "context", "script",
    "enabled", "ruleEnabled", "order", "valid", "error", "summary",
)

_ACTIONS = (
    *dcc_trigger_actions(),
    ("snapshot.open", "Open snapshot", "folder_open", False),
    ("snapshot.save", "Save snapshot", "save", False),
    ("object.create", "Create object", "add", False),
    ("object.update", "Update object", "edit", False),
    ("object.delete", "Delete object", "delete", False),
    ("object.duplicate", "Duplicate object", "control-point-duplicate", False),
    ("relation.update", "Update relations", "link", False),
    ("task.create", "Create task", "add-task", False),
    ("task.update", "Update task", "task", False),
    ("task.delete", "Delete task", "delete", False),
)

_HANDLER_LANGUAGES = {"local_python", "python", "server_js"}


def _event_name(action: str, phase: str) -> str:
    return SCRIPT_TRIGGER_EVENT_PREFIX + "|".join((phase, *action.split(".")))


def _search_type(search_key: str) -> str:
    return str(search_key or "").removeprefix("skey://").split("?", 1)[0]


def _search_keys(value: object) -> list[str]:
    if isinstance(value, str):
        values = value.replace(",", "\n").splitlines()
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = ()
    return list(dict.fromkeys(
        str(item or "").strip() for item in values if str(item or "").strip()
    ))


def _rule_payload(rule: Mapping) -> dict:
    return {
        "version": 1,
        "action": str(rule.get("action") or ""),
        "phase": str(rule.get("phase") or "after"),
        "search_type": str(rule.get("searchType") or ""),
        "search_keys": _search_keys(rule.get("searchKeysText")),
        "process": str(rule.get("process") or ""),
        "context": str(rule.get("context") or ""),
        "order": int(rule.get("order") or 0),
    }


def _revision(records: list[dict]) -> str:
    owned = [{
        key: record.get(key)
        for key in (
            "code", "title", "description", "event", "script_path",
            "trigger_type", "data", "s_status", "timestamp",
        )
    } for record in records if str(record.get("trigger_type") or "") == SCRIPT_TRIGGER_TYPE]
    owned.sort(key=lambda item: str(item.get("code") or ""))
    return hashlib.sha256(json.dumps(
        owned, sort_keys=True, default=str, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def _project_rule(record: Mapping, index: int) -> dict:
    raw_data = record.get("data") or {}
    if isinstance(raw_data, Mapping):
        data = dict(raw_data)
    else:
        try:
            data = json.loads(str(raw_data))
        except (TypeError, ValueError, json.JSONDecodeError):
            data = {}
    if not isinstance(data, dict):
        data = {}
    valid = data.get("version") == 1
    action = str(data.get("action") or "") if valid else ""
    phase = str(data.get("phase") or "") if valid else ""
    if action not in {item[0] for item in _ACTIONS} or phase not in {"before", "after"}:
        valid = False
    script = str(record.get("script_path") or "").strip().strip("/")
    if not script:
        valid = False
    try:
        order = int(data.get("order", index))
    except (TypeError, ValueError):
        order = index
        valid = False
    error = "" if valid else "Invalid Handler script trigger"
    title = str(record.get("title") or script or "")
    search_type = str(data.get("search_type") or "")
    keys = _search_keys(data.get("search_keys"))
    summary = " · ".join(filter(None, (
        phase,
        action,
        search_type or "All Search Types",
        script,
    )))
    return {
        "ruleId": str(record.get("code") or uuid.uuid4().hex),
        "code": str(record.get("code") or ""),
        "title": title,
        "description": str(record.get("description") or ""),
        "action": action,
        "phase": phase,
        "searchType": search_type,
        "searchKeysText": "\n".join(keys),
        "process": str(data.get("process") or ""),
        "context": str(data.get("context") or ""),
        "script": script,
        "enabled": str(record.get("s_status") or "") != "retired",
        "order": order,
        "valid": valid,
        "error": error,
        "summary": summary,
    }


class ScriptTriggerController(QObject):
    """Own server-backed hook rules and their sequential execution."""

    stateChanged = Signal()
    outputReady = Signal(str, str)

    def __init__(
        self, application, users, script_editor, server_pool, debug_log,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._application = application
        self._users = users
        self._script_editor = script_editor
        self._server_pool = server_pool
        self._debug_log = debug_log
        self._dcc_bridge = None
        self._project_code = ""
        self._generation = 0
        self._workers = set()
        self._script_workers = set()
        self._busy = False
        self._error = ""
        self._selected = -1
        self._revision = ""
        self._original: list[dict] = []
        self._dcc_runs: dict[str, tuple[dict, Callable]] = {}
        self._active_hook_runs = 0
        self.rules = RecordListModel(_RULE_ROLES, identity_role="ruleId")
        application.project_changed.connect(self._project_changed)
        application.window_model.windowVisibilityChanged.connect(
            self._window_visibility_changed
        )
        script_editor.stateChanged.connect(self._scripts_changed)
        self.outputReady.connect(script_editor.append_trigger_output)
        self._project_changed(
            str(getattr(application, "current_project_code", "") or ""), ""
        )

    @Property(QObject, constant=True)
    def model(self):
        return self.rules

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(bool, notify=stateChanged)
    def canManage(self) -> bool:
        try:
            return bool(self._users.canManageUsers)
        except (AttributeError, RuntimeError):
            return False

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return self._document() != self._original

    @Property(int, notify=stateChanged)
    def selectedRow(self) -> int:
        return self._selected

    @Property("QVariantMap", notify=stateChanged)
    def selectedRule(self) -> dict:
        rows = self.rules.records()
        return dict(rows[self._selected]) if 0 <= self._selected < len(rows) else {}

    @Property("QVariantList", constant=True)
    def actionOptions(self) -> list[dict]:
        return [{
            "value": value, "label": self.tr(label), "icon": icon,
            "dcc": dcc,
        } for value, label, icon, dcc in _ACTIONS]

    @Property("QVariantList", constant=True)
    def phaseOptions(self) -> list[dict]:
        return [
            {"value": "before", "label": self.tr("Before")},
            {"value": "after", "label": self.tr("After")},
        ]

    @Property("QVariantList", notify=stateChanged)
    def scriptOptions(self) -> list[dict]:
        return [dict(item) for item in self._script_editor.shelfScriptOptions]

    @Property("QVariantList", notify=stateChanged)
    def compatibleScriptOptions(self) -> list[dict]:
        options = self.scriptOptions
        if str(self.selectedRule.get("action") or "").startswith("dcc."):
            return [item for item in options if item.get("language") == "dcc_python"]
        return [
            item for item in options
            if item.get("language") in _HANDLER_LANGUAGES
        ]

    @Property("QVariantList", notify=stateChanged)
    def searchTypeOptions(self) -> list[dict]:
        values = []
        try:
            from thlib.environment import env_inst

            project = env_inst.projects.get(self._project_code)
            stypes = (project.get_stypes() or {}).values() if project else ()
            values = [{
                "value": str(stype.get_code() or ""),
                "label": str(stype.get_pretty_name() or stype.get_code() or ""),
            } for stype in stypes if stype.get_code()]
        except (AttributeError, TypeError):
            pass
        values.sort(key=lambda item: item["label"].casefold())
        return [{"value": "", "label": self.tr("All Search Types")}, *values]

    def attach_dcc_bridge(self, bridge) -> None:
        if bridge is self._dcc_bridge:
            return
        if self._dcc_bridge is not None:
            try:
                self._dcc_bridge.commandFinished.disconnect(self._dcc_finished)
            except (RuntimeError, TypeError):
                pass
        self._dcc_bridge = bridge
        if bridge is not None:
            bridge.commandFinished.connect(self._dcc_finished)
        self.stateChanged.emit()

    @Slot()
    def open_editor(self) -> None:
        self._application.window_model.show_child_window(
            "script_trigger_editor", "script_editor"
        )
        self.refresh()

    @Slot(int)
    def select(self, row: int) -> None:
        if -1 <= row < len(self.rules.records()):
            self._selected = row
            self.stateChanged.emit()

    @Slot()
    def add(self) -> None:
        if not self.canManage or self._busy:
            return
        rows = self.rules.records()
        rows.append({
            "ruleId": uuid.uuid4().hex,
            "code": "",
            "title": self.tr("New trigger"),
            "description": "",
            "action": "object.update",
            "phase": "after",
            "searchType": "",
            "searchKeysText": "",
            "process": "",
            "context": "",
            "script": "",
            "enabled": False,
            "order": len(rows),
            "valid": True,
            "error": "",
            "summary": "",
        })
        self.rules.replace(self._present(rows))
        self._selected = len(rows) - 1
        self.stateChanged.emit()

    @Slot(str, "QVariant")
    def update(self, field: str, value) -> None:
        allowed = {
            "title", "description", "action", "phase", "searchType",
            "searchKeysText", "process", "context", "script", "enabled",
        }
        if not self.canManage or self._busy or field not in allowed:
            return
        rows = self.rules.records()
        if not 0 <= self._selected < len(rows):
            return
        normalized = bool(value) if field == "enabled" else str(value or "")
        rows[self._selected][field] = normalized
        self.rules.replace(self._present(rows))
        self.stateChanged.emit()

    @Slot(int)
    def move(self, offset: int) -> None:
        if not self.canManage or self._busy:
            return
        rows = self.rules.records()
        target = self._selected + int(offset)
        if not 0 <= self._selected < len(rows) or not 0 <= target < len(rows):
            return
        rows.insert(target, rows.pop(self._selected))
        for order, row in enumerate(rows):
            row["order"] = order
        self._selected = target
        self.rules.replace(self._present(rows))
        self.stateChanged.emit()

    @Slot()
    def remove(self) -> None:
        if not self.canManage or self._busy:
            return
        rows = self.rules.records()
        if not 0 <= self._selected < len(rows):
            return
        rows.pop(self._selected)
        for order, row in enumerate(rows):
            row["order"] = order
        self._selected = min(self._selected, len(rows) - 1)
        self.rules.replace(self._present(rows))
        self.stateChanged.emit()

    @Slot()
    def discard(self) -> None:
        if self._busy:
            return
        self.rules.replace(self._present(self._original))
        self._selected = min(self._selected, len(self._original) - 1)
        self._error = ""
        self.stateChanged.emit()

    @Slot()
    def refresh(self) -> None:
        if not self._project_code or self._busy:
            return
        project_code = self._project_code
        generation = self._generation

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            records = server.query(
                "config/trigger",
                [("trigger_type", SCRIPT_TRIGGER_TYPE)],
                show_retired=True,
            ) or []
            if isinstance(records, dict):
                records = [records]
            return project_code, generation, records, _revision(records)

        self._run_server(operation, self._refreshed)

    @Slot()
    def save(self) -> None:
        if not self.canManage or self._busy or not self._project_code:
            return
        rules = self._document()
        try:
            self._validate(rules)
        except ValueError as error:
            self._set_error(str(error))
            return
        project_code = self._project_code
        generation = self._generation
        expected_revision = self._revision

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            current = server.query(
                "config/trigger",
                [("trigger_type", SCRIPT_TRIGGER_TYPE)],
                show_retired=True,
            ) or []
            if isinstance(current, dict):
                current = [current]
            if _revision(current) != expected_revision:
                raise RuntimeError(
                    self.tr(
                        "Script triggers changed on the server. Reload before saving."
                    )
                )
            native = {str(item.get("code") or ""): item for item in current}
            retained = set()
            for rule in rules:
                data = {
                    "title": rule["title"].strip(),
                    "description": rule["description"].strip(),
                    "event": _event_name(rule["action"], rule["phase"]),
                    "script_path": rule["script"].strip().strip("/"),
                    "trigger_type": SCRIPT_TRIGGER_TYPE,
                    "data": json.dumps(
                        _rule_payload(rule), ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    "s_status": "" if rule["enabled"] else "retired",
                }
                code = str(rule.get("code") or "")
                if code:
                    key = server.build_search_key(
                        "config/trigger", code, project_code=project_code
                    )
                    server.insert_update(key, data, triggers=True)
                    retained.add(code)
                else:
                    created = server.insert(
                        "config/trigger", data, triggers=True
                    ) or {}
                    retained.add(str(created.get("code") or ""))
            for code in set(native) - retained:
                key = server.build_search_key(
                    "config/trigger", code, project_code=project_code
                )
                server.delete_sobject(key)
            records = server.query(
                "config/trigger",
                [("trigger_type", SCRIPT_TRIGGER_TYPE)],
                show_retired=True,
            ) or []
            if isinstance(records, dict):
                records = [records]
            return project_code, generation, records, _revision(records)

        self._run_server(operation, self._saved)

    def run_before(
        self, action: str, context: Mapping | None,
        finished: Callable[[bool, str], None],
    ) -> None:
        self._run_hooks(action, "before", context, finished)

    def run_after(
        self, action: str, context: Mapping | None,
        finished: Callable[[bool, str], None] | None = None,
    ) -> None:
        self._run_hooks(
            action, "after", context, finished or (lambda _ok, _error: None)
        )

    def _run_hooks(
        self, action: str, phase: str, context: Mapping | None,
        finished: Callable[[bool, str], None],
    ) -> None:
        payload = self._context(action, phase, context)
        if int(payload.get("trigger_depth") or 0) > 0 or self._active_hook_runs:
            finished(True, "")
            return
        matches = [
            rule for rule in self.rules.records()
            if self._matches(rule, payload)
        ]
        if not matches:
            finished(True, "")
            return
        matches.sort(key=lambda rule: (int(rule.get("order") or 0), rule["ruleId"]))
        payload["trigger_depth"] = 1
        self._active_hook_runs += 1

        def complete(success: bool, error: str) -> None:
            self._active_hook_runs = max(0, self._active_hook_runs - 1)
            finished(success, error)

        self._run_sequence(matches, payload, phase, complete)

    def _run_sequence(
        self, rules: list[dict], payload: dict, phase: str,
        finished: Callable[[bool, str], None],
    ) -> None:
        if not rules:
            finished(True, "")
            return
        rule = rules[0]

        def next_rule(success: bool, error: str) -> None:
            if not success and phase == "before":
                finished(False, error)
                return
            self._run_sequence(rules[1:], payload, phase, finished)

        self._execute_rule(rule, payload, next_rule)

    def _execute_rule(
        self, rule: dict, payload: dict,
        finished: Callable[[bool, str], None],
    ) -> None:
        definition = self._script_editor.saved_script_definition(rule["script"])
        if not definition:
            self._hook_failed(
                rule, self.tr("The saved script is unavailable"), finished
            )
            return
        language = str(definition.get("language") or "")
        started = time.monotonic()
        callback = lambda success, result, error: self._execution_finished(
            rule, started, success, result, error, finished
        )
        if language == "dcc_python":
            bridge = self._dcc_bridge
            client_id = str(payload.get("client_id") or "")
            sender = getattr(bridge, "send_client_command", None)
            if not bridge or not callable(sender):
                self._hook_failed(
                    rule, self.tr("A DCC client is not connected"), finished
                )
                return
            if not client_id:
                client_id = str(getattr(bridge, "selectedClient", "") or "")
            request_id = sender(
                client_id,
                "execute_custom_script",
                {
                    "project": self._project_code,
                    "script": rule["script"],
                    "kwargs": payload,
                },
                300.0,
            )
            if not request_id:
                self._hook_failed(
                    rule,
                    str(
                        getattr(bridge, "error", "")
                        or self.tr("DCC script could not be started")
                    ),
                    finished,
                )
                return
            self._dcc_runs[str(request_id)] = (rule, callback)
            return

        def operation():
            if language == "local_python":
                return self._execute_local(definition, payload)
            return self._execute_server(definition, payload)

        self._run_script_worker(operation, callback)

    @staticmethod
    def _execute_local(definition: dict, payload: dict) -> dict:
        source = str(definition.get("source") or "")
        path = str(definition.get("path") or "custom-script")
        output = io.StringIO()
        module_name = "_tactic_handler_hook_" + uuid.uuid4().hex
        module = types.ModuleType(module_name)
        module.__file__ = "<{}>".format(path)
        module.TACTIC_PROJECT_CODE = str(payload.get("project_code") or "")
        module.TACTIC_SCRIPT_KWARGS = dict(payload)
        sys.modules[module_name] = module
        try:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                exec(compile(source, module.__file__, "exec"), module.__dict__)
            return {"result": getattr(module, "RESULT", None), "output": output.getvalue()}
        finally:
            sys.modules.pop(module_name, None)

    @staticmethod
    def _execute_server(definition: dict, payload: dict):
        import thlib.tactic_classes as tc

        project_code = str(payload.get("project_code") or "")
        script_kwargs = {
            **dict(payload),
            "TACTIC_PROJECT_CODE": project_code,
            "TACTIC_SCRIPT_KWARGS": dict(payload),
        }
        server = tc.server_start(project=project_code or None)
        path = str(definition.get("path") or "")
        if definition.get("language") == "server_js":
            return server.execute_js_script(path, kwargs=script_kwargs)
        return server.execute_python_script(path, kwargs=script_kwargs)

    def _run_script_worker(self, operation: Callable, callback: Callable) -> None:
        try:
            if self._server_pool is None:
                raise RuntimeError(self.tr("Script worker is unavailable"))
            if self._server_pool.is_stopped:
                self._server_pool.start()
            worker = self._server_pool.add_task(operation)
            if worker is None:
                raise RuntimeError(self.tr("Script worker is unavailable"))
            self._script_workers.add(worker)
            worker.result.connect(lambda result: callback(True, result, ""))
            worker.error.connect(lambda error: callback(
                False, {}, self._worker_traceback(error)
            ))
            worker.settled.connect(
                lambda _worker: self._script_workers.discard(worker)
            )
            worker.start()
        except Exception as error:
            callback(False, {}, str(error))

    @Slot(str, bool, "QVariantMap", str)
    def _dcc_finished(
        self, request_id: str, success: bool, payload: dict, error: str,
    ) -> None:
        current = self._dcc_runs.pop(str(request_id or ""), None)
        if current:
            _rule, callback = current
            callback(bool(success), dict(payload or {}), str(error or ""))

    def _execution_finished(
        self, rule: dict, started: float, success: bool, result,
        error: str, finished: Callable[[bool, str], None],
    ) -> None:
        elapsed = max(0.0, time.monotonic() - started)
        if success:
            message = self.tr("Script trigger completed: %1").replace(
                "%1", rule["title"]
            )
            output = self._execution_output(result)
            if self._debug_log:
                self._debug_log.log(
                    "LOG",
                    message,
                    group="ui/script-triggers",
                    source=rule["script"],
                    details=output or str(result or ""),
                    duration=elapsed,
                )
            if output:
                self.outputReady.emit(
                    rule["script"], "{} · {}\n{}".format(
                        message, rule["script"], output
                    )
                )
            finished(True, "")
            return
        self._hook_failed(
            rule, error or self.tr("Script trigger failed"), finished
        )

    @staticmethod
    def _execution_output(result) -> str:
        if isinstance(result, Mapping):
            output = str(result.get("output") or "").rstrip()
            if output:
                return output
            if "result" in result:
                result = result.get("result")
            elif "info" in result:
                result = result.get("info")
                if isinstance(result, Mapping) and "spt_ret_val" in result:
                    result = result.get("spt_ret_val")
            else:
                return ""
        return "" if result is None else str(result).rstrip()

    def _hook_failed(
        self, rule: dict, message: str,
        finished: Callable[[bool, str], None],
    ) -> None:
        text = "{}: {}".format(rule.get("title") or rule.get("script"), message)
        self.outputReady.emit(
            str(rule.get("script") or ""),
            "{}\n{}".format(self.tr("Script trigger failed"), text),
        )
        if self._debug_log:
            self._debug_log.log(
                "ERROR", text, group="ui/script-triggers",
                source=str(rule.get("script") or "Script trigger"),
                stacktrace=str(message or ""), caller=2,
            )
        self._application._notify(text)
        finished(False, text)

    def _context(self, action: str, phase: str, source: Mapping | None) -> dict:
        payload = dict(source or {})
        targets = []
        for item in payload.get("targets") or []:
            if isinstance(item, Mapping):
                search_key = str(item.get("search_key") or item.get("searchKey") or "")
                targets.append({
                    "search_key": search_key,
                    "search_type": str(item.get("search_type") or item.get("searchType") or _search_type(search_key)),
                })
        search_key = str(payload.get("search_key") or payload.get("searchKey") or "")
        if search_key and not targets:
            targets.append({"search_key": search_key, "search_type": _search_type(search_key)})
        search_type = str(payload.get("search_type") or payload.get("searchType") or "")
        if search_type and not targets:
            targets.append({"search_key": "", "search_type": search_type})
        payload.update({
            "event": str(action),
            "phase": str(phase),
            "operation_id": str(payload.get("operation_id") or uuid.uuid4().hex),
            "project_code": str(
                payload.get("project_code")
                or payload.get("projectCode")
                or self._project_code
            ),
            "client_id": str(payload.get("client_id") or payload.get("clientId") or ""),
            "source": str(payload.get("source") or "handler"),
            "targets": targets,
        })
        return payload

    @staticmethod
    def _matches(rule: dict, payload: dict) -> bool:
        if not rule.get("enabled") or not rule.get("valid"):
            return False
        if rule.get("action") != payload.get("event") or rule.get("phase") != payload.get("phase"):
            return False
        targets = list(payload.get("targets") or [])
        search_type = str(rule.get("searchType") or "")
        if search_type and not any(item.get("search_type") == search_type for item in targets):
            return False
        wanted_keys = set(_search_keys(rule.get("searchKeysText")))
        if wanted_keys and not wanted_keys.intersection(
            str(item.get("search_key") or "") for item in targets
        ):
            return False
        for rule_key, payload_key in (("process", "process"), ("context", "context")):
            expected = str(rule.get(rule_key) or "")
            if expected and expected != str(payload.get(payload_key) or ""):
                return False
        return True

    def _validate(self, rules: list[dict]) -> None:
        script_definitions = {
            option["value"]: self._script_editor.saved_script_definition(option["value"])
            for option in self.scriptOptions
        }
        for index, rule in enumerate(rules, 1):
            title = str(rule.get("title") or "").strip()
            if not title:
                raise ValueError(self.tr("Enter a name for trigger %1").replace("%1", str(index)))
            action = str(rule.get("action") or "")
            if action not in {item[0] for item in _ACTIONS}:
                raise ValueError(self.tr("Choose an action for every trigger"))
            if rule.get("phase") not in {"before", "after"}:
                raise ValueError(self.tr("Choose before or after for every trigger"))
            script = str(rule.get("script") or "")
            definition = script_definitions.get(script)
            if not definition:
                raise ValueError(self.tr("Choose an available script for every trigger"))
            if action.startswith("dcc.") and definition.get("language") != "dcc_python":
                raise ValueError(self.tr("DCC actions require a DCC Python script"))
            if (
                not action.startswith("dcc.")
                and definition.get("language") not in _HANDLER_LANGUAGES
            ):
                raise ValueError(self.tr("Handler actions require a local or server script"))

    def _present(self, rules: list[dict]) -> list[dict]:
        available = {
            item["value"]: item for item in self.scriptOptions
        }
        actions = {item[0] for item in _ACTIONS}
        result = []
        for order, source in enumerate(rules):
            rule = dict(source)
            rule["order"] = order
            if not str(rule.get("title") or "").strip():
                rule["title"] = self.tr("Untitled trigger")
            action_value = str(rule.get("action") or "")
            phase_value = str(rule.get("phase") or "")
            definition = available.get(str(rule.get("script") or ""))
            if action_value not in actions:
                error = self.tr("Choose an action for every trigger")
            elif phase_value not in {"before", "after"}:
                error = self.tr("Choose before or after for every trigger")
            elif definition is None:
                error = self.tr("Saved script is unavailable")
            elif (
                action_value.startswith("dcc.")
                and definition.get("language") != "dcc_python"
            ):
                error = self.tr("DCC actions require a DCC Python script")
            elif (
                not action_value.startswith("dcc.")
                and definition.get("language") not in _HANDLER_LANGUAGES
            ):
                error = self.tr("Handler actions require a local or server script")
            else:
                error = ""
            rule["valid"] = not error
            rule["error"] = error
            rule["ruleEnabled"] = bool(rule.get("enabled"))
            action = next((
                self.tr(label) for value, label, _icon, _dcc in _ACTIONS
                if value == rule.get("action")
            ), str(rule.get("action") or ""))
            phase = self.tr("Before") if rule.get("phase") == "before" else self.tr("After")
            rule["summary"] = " · ".join(filter(None, (
                phase, action, str(rule.get("searchType") or self.tr("All Search Types")),
                str(rule.get("script") or self.tr("No script")),
            )))
            result.append(rule)
        return result

    def _document(self) -> list[dict]:
        return [{key: row.get(key) for key in _RULE_ROLES if key not in {
                    "ruleEnabled", "valid", "error", "summary",
                }}
                for row in self.rules.records()]

    def _run_server(self, operation: Callable, handler: Callable) -> None:
        try:
            if self._server_pool is None:
                raise RuntimeError(self.tr("Server worker is unavailable"))
            if self._server_pool.is_stopped:
                self._server_pool.start()
            worker = self._server_pool.add_task(operation)
            if worker is None:
                raise RuntimeError(self.tr("Server worker is unavailable"))
            self._workers.add(worker)
            self._busy = True
            self._error = ""
            worker.result.connect(handler)
            worker.error.connect(self._failed)
            worker.settled.connect(lambda _worker: self._release_worker(worker))
            self.stateChanged.emit()
            worker.start()
        except Exception as error:
            self._set_error(str(error))

    def _release_worker(self, worker) -> None:
        self._workers.discard(worker)
        self._busy = bool(self._workers)
        self.stateChanged.emit()

    @Slot(object)
    def _refreshed(self, payload) -> None:
        project_code, generation, records, revision = payload
        if project_code != self._project_code or generation != self._generation:
            return
        rules = [_project_rule(record, index) for index, record in enumerate(records)]
        rules.sort(key=lambda item: (item["order"], item["ruleId"]))
        self.rules.replace(self._present(rules))
        self._original = self._document()
        self._revision = revision
        self._selected = 0 if rules else -1
        self.stateChanged.emit()

    @Slot(object)
    def _saved(self, payload) -> None:
        self._refreshed(payload)
        self._application._notify(self.tr("Script triggers saved"))

    @Slot(object)
    def _failed(self, error) -> None:
        payload = error[0] if isinstance(error, tuple) and error else error
        message = self._worker_error(error)
        stacktrace = str(payload.get("traceback") or payload.get("stacktrace") or "") if isinstance(payload, Mapping) else traceback.format_exc()
        if self._debug_log:
            self._debug_log.log(
                "ERROR", message, group="ui/script-triggers",
                source="ScriptTriggerController", stacktrace=stacktrace,
                caller=2,
            )
        self._set_error(message)

    @staticmethod
    def _worker_error(error) -> str:
        payload = error[0] if isinstance(error, tuple) and error else error
        if isinstance(payload, Mapping):
            return str(payload.get("exception") or payload.get("message") or payload)
        return str(payload or error)

    @staticmethod
    def _worker_traceback(error) -> str:
        payload = error[0] if isinstance(error, tuple) and error else error
        if isinstance(payload, Mapping):
            return str(
                payload.get("stacktrace")
                or payload.get("traceback")
                or payload.get("exception")
                or payload
            )
        return str(payload or error)

    def _set_error(self, message: str) -> None:
        self._error = str(message or "")
        self.stateChanged.emit()
        if self._error:
            self._application._notify(self._error)

    @Slot(str, str)
    def _project_changed(self, project_code: str, _title: str) -> None:
        self._generation += 1
        self._project_code = str(project_code or "")
        self._revision = ""
        self._original = []
        self._selected = -1
        self._error = ""
        self.rules.clear()
        if self._project_code:
            self.refresh()
        else:
            self.stateChanged.emit()

    @Slot(str, bool)
    def _window_visibility_changed(self, window_id: str, visible: bool) -> None:
        if window_id == "script_trigger_editor" and visible and not self.dirty:
            self.refresh()

    @Slot()
    def _scripts_changed(self) -> None:
        self.rules.replace(self._present(self.rules.records()))
        self.stateChanged.emit()

    def apply_server_batch(self, batch) -> None:
        records = [
            *list((batch or {}).get("cacheChanges") or []),
            *list((batch or {}).get("cacheRetired") or []),
        ]
        if any(
            str(record.get("searchType") or "").split("?", 1)[0] == "config/trigger"
            and str(record.get("projectCode") or "") == self._project_code
            for record in records
        ) and not self.dirty:
            self.refresh()

    def shutdown(self) -> None:
        self.attach_dcc_bridge(None)
        for worker in tuple(self._workers):
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        for worker in tuple(self._script_workers):
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
