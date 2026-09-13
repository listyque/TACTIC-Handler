"""Fixed high-level Handler API transport, with session-owned object handles."""

from __future__ import annotations

import threading
import time
import traceback
import uuid

from tactic_handler_api import local, ConcurrentEdit, UIUnavailable
from tactic_handler_api.contract import METHODS, PROPERTIES
from tactic_handler_api import wire


class HandlerApiService:
    def __init__(self, max_objects=4096, gui_dispatch=None):
        self._max_objects = max_objects
        self._gui_dispatch = gui_dispatch
        self._checkin = None
        self._ui_api = None
        self._api_runtime = None
        self._lock = threading.RLock()
        self._sessions = {}

    def attach_application(
        self, application, checkin_controller, show_application=None
    ):
        self._checkin = checkin_controller
        self._ui_api = UICommands(
            application,
            self._gui_dispatch,
            show_application,
            checkin_controller,
        )

    def register(self, registry):
        registry.register("handler.call", self.call)
        registry.register("handler.release", self.release)
        registry.register("handler.close", self.close_session)

    def _public_api(self):
        with self._lock:
            if self._api_runtime is None:
                gateway = None
                queue = getattr(self._checkin, "_commit_queue", None)
                if queue is not None:
                    from .api_bridge import DesktopQueue

                    gateway = DesktopQueue(queue, self._gui_dispatch)
                self._api_runtime = local(ui=self._ui_api, queue_gateway=gateway)
            return self._api_runtime

    @staticmethod
    def _type(value):
        name = type(value).__name__
        module = type(value).__module__
        if module in ("thlib.tactic_classes", "thlib.global_functions"):
            name = "Native" + name
        elif not (
            module.startswith("tactic_handler_api.") or isinstance(value, UICommands)
        ):
            raise TypeError(f"Not a public Handler API object: {module}.{name}")
        if name not in METHODS:
            raise TypeError(f"Not a public Handler API object: {name}")
        return name

    def _scope(self, session_id):
        if not isinstance(session_id, str) or len(session_id) != 32:
            raise ValueError("A valid API session id is required")
        uuid.UUID(hex=session_id)
        with self._lock:
            now = time.monotonic()
            for key, scope in tuple(self._sessions.items()):
                if not scope["active"] and now - scope["used"] > 1800:
                    del self._sessions[key]
            scope = self._sessions.get(session_id)
            if scope is None:
                if len(self._sessions) >= 64:
                    raise RuntimeError(
                        "API session limit reached; close unused runtimes"
                    )
                scope = {
                    "objects": {},
                    "handles": {},
                    "locks": {},
                    "active": 0,
                    "closed": False,
                    "used": now,
                }
                self._sessions[session_id] = scope
            if scope["closed"]:
                raise ReferenceError("The API session is closing")
            scope["active"] += 1
            scope["used"] = now
            return scope

    def _object(self, scope, handle):
        api = self._public_api()
        if handle == "root":
            return api
        if handle == "files":
            return api.files
        if handle == "repositories":
            return api.repositories
        if handle == "ui":
            if self._ui_api is None:
                raise UIUnavailable("The Handler UI is unavailable")
            return self._ui_api
        if isinstance(handle, str) and handle.startswith("queue:"):
            return api.commit_queue(handle.partition(":")[2] or None)
        with self._lock:
            value = scope["objects"].get(handle)
        if value is None:
            raise ReferenceError("API object expired or belongs to another session")
        return value

    def _store(self, scope, value):
        type_name = self._type(value)
        with self._lock:
            handle = scope["handles"].get(id(value))
            if handle is None:
                if len(scope["objects"]) >= self._max_objects:
                    raise RuntimeError(
                        "API object limit reached; release unused handles"
                    )
                handle = uuid.uuid4().hex
                scope["objects"][handle] = value
                scope["handles"][id(value)] = handle
        result = {"kind": "ref", "id": handle, "type": type_name}
        if type_name == "SObject":
            result["info"] = wire.encode(
                value.get_info(), lambda obj: self._store(scope, obj)
            )
            result["new"] = value._native is None
        return result

    def call(self, payload):
        scope = None
        try:
            scope = self._scope(payload.get("session"))
            handle, member = payload.get("handle"), payload.get("member")
            target = self._object(scope, handle)
            type_name = self._type(target)
            read = bool(payload.get("read"))
            allowed = PROPERTIES.get(type_name, ()) if read else METHODS[type_name]
            if member not in allowed:
                raise PermissionError(
                    f"{type_name}.{member} is not a public API command"
                )
            restore = lambda value: self._object(scope, value["id"])
            args = wire.decode(payload.get("args"), restore)
            kwargs = wire.decode(payload.get("kwargs"), restore)
            if not isinstance(args, list) or not isinstance(kwargs, dict):
                raise ValueError(
                    "Expected a list of arguments and a mapping of keywords"
                )
            with self._lock:
                lock = scope["locks"].setdefault(handle, threading.Lock())
            if not lock.acquire(blocking=False):
                raise ConcurrentEdit("A command on this API handle is already running")
            try:
                if type_name == "SObject" and member in ("commit", "refresh"):
                    # The DCC owns staged fields. Do not retain a previous failed
                    # attempt as a second, unsynchronized editing state.
                    target.discard_changes()
                    if member == "commit":
                        changes = wire.decode(payload.get("changes"), restore)
                        if not isinstance(changes, dict):
                            raise ValueError(
                                "A commit must include staged field values"
                            )
                        for column, value in changes.items():
                            target.set_value(column, value)
                result = (
                    getattr(target, member)
                    if read
                    else getattr(target, member)(*args, **kwargs)
                )
                return {
                    "value": wire.encode(
                        result, lambda value: self._store(scope, value)
                    )
                }
            finally:
                lock.release()
        except Exception as error:
            # This is the transport boundary, not a silent fallback. Preserve the
            # complete cause for the caller and Handler's existing redacted log.
            return {
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "traceback": traceback.format_exc(),
                }
            }
        finally:
            if scope is not None:
                with self._lock:
                    scope["active"] -= 1
                    scope["used"] = time.monotonic()
                    if scope["closed"] and not scope["active"]:
                        self._sessions.pop(payload["session"], None)

    def release(self, payload):
        with self._lock:
            scope = self._sessions.get(payload.get("session"))
            handle = payload.get("handle")
            if scope is not None:
                lock = scope["locks"].get(handle)
                if lock is not None and lock.locked():
                    raise ConcurrentEdit("Cannot release a running API handle")
                value = scope["objects"].pop(handle, None)
                if value is not None:
                    scope["handles"].pop(id(value), None)
                scope["locks"].pop(handle, None)
        return {"value": None}

    def close_session(self, payload):
        with self._lock:
            scope = self._sessions.get(payload.get("session"))
            if scope is not None:
                scope["closed"] = True
                if not scope["active"]:
                    self._sessions.pop(payload["session"], None)
        return {"value": None}

    def close_api(self):
        if self._api_runtime is not None:
            gateway = self._api_runtime._queue_gateway
            if gateway is not None and hasattr(gateway, "close"):
                gateway.close()
            self._api_runtime.close(wait=False)
            self._api_runtime = None
        with self._lock:
            self._sessions.clear()


class UICommands:
    def __init__(
        self, application, dispatch, show_application=None, checkin=None
    ):
        self._application = application
        self._dispatch = dispatch
        self._show_application = show_application
        self._checkin = checkin

    def _gui(self, callback, *args):
        if self._dispatch is None:
            raise UIUnavailable("Application UI dispatch is unavailable")
        return self._dispatch(callback, *args)

    def show(self):
        if self._show_application:
            self._show_application({})
        return True

    def open_project(self, project_code):
        self.show()
        self._gui(self._application.select_project, str(project_code))
        return True

    def open_search_key(self, search_key):
        self._gui(self._application.open_search_key, str(search_key))
        return True

    def show_dock(self, panel_id):
        self._gui(self._application.dock_model.show_panel, str(panel_id))
        return True

    def show_window(self, window_id):
        self._gui(self._application.window_model.show_window, str(window_id))
        return True

    def checkin_from_dcc(
        self, search_key, context, description, application_type, client_id
    ):
        if self._checkin is None:
            raise UIUnavailable("Commit Queue is unavailable")
        application_type = str(application_type or "").strip().lower()
        if not application_type:
            raise ValueError("A DCC application type is required")
        parsed, source = self._application._resolve_search_key(search_key)
        if not parsed or source is None:
            raise ValueError("The DCC scene is not linked to a TACTIC object")
        project_code = str(
            parsed.get("project") or parsed.get("project_code") or ""
        )
        if not project_code:
            raise ValueError("The DCC scene has no TACTIC project")
        context = str(context or "publish")
        code = str(source.get_code() or "")
        target = {
            "searchKey": str(source.get_search_key() or ""),
            "source": source,
            "projectCode": project_code,
            "title": str(source.get_title() or code or "sObject"),
            "code": code,
            "process": context.split("/", 1)[0],
            "context": context,
            "description": str(description or ""),
            "version": 0,
        }
        payload = {
            "client_id": str(client_id or ""),
            "application_type": application_type,
            "generate_previews": True,
            "update_versionless": True,
        }
        self.show()
        started = self._gui(
            self._checkin.start_dcc_scene_checkin,
            target,
            payload,
            "prepare_checkin",
        )
        if not started:
            raise RuntimeError("DCC scene preparation could not be started")
        return True

    def checkin_from_maya(
        self, search_key, context, description, client_id
    ):
        """Compatibility alias for existing Maya scripts."""
        return self.checkin_from_dcc(
            search_key, context, description, "maya", client_id
        )

    def checkin_files(self, search_key, context, description, paths):
        if self._checkin is None:
            raise UIUnavailable("Commit Queue is unavailable")
        if not isinstance(paths, (list, tuple)):
            raise TypeError("paths must be a collection of files")
        paths = [str(path or "") for path in paths if str(path or "")]
        if not paths:
            raise ValueError("At least one file is required for check-in")
        parsed, source = self._application._resolve_search_key(search_key)
        if not parsed or source is None:
            raise ValueError("The file target is not a valid TACTIC object")
        project_code = str(
            parsed.get("project") or parsed.get("project_code") or ""
        )
        if not project_code:
            raise ValueError("The file target has no TACTIC project")

        def prepare():
            code = str(source.get_code() or "")
            return self._checkin.prepare_external_checkin(
                search_key=str(source.get_search_key() or ""),
                source=source,
                project_code=project_code,
                title=str(source.get_title() or code or "sObject"),
                code=code,
                context=str(context or "publish"),
                description=str(description or ""),
                paths=paths,
                file_types=["main"] * len(paths),
                queue_before_naming=True,
            )

        self.show()
        return self._gui(prepare)
