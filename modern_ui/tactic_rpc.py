from __future__ import annotations

import base64
import importlib
import inspect
import threading
import uuid
from datetime import date, datetime
from pathlib import Path


class TacticObjectService:
    _MODULES = {
        "tactic_classes": "thlib.tactic_classes",
        "global_functions": "thlib.global_functions",
    }

    def __init__(self, max_objects=10000, gui_dispatch=None):
        self._max_objects = max(100, int(max_objects))
        self._objects = {}
        self._handles = {}
        self._lock = threading.RLock()
        self._gui_dispatch = gui_dispatch
        self._application = None
        self._checkin = None
        self._ui_api = None
        self._show_application = None

    def attach_application(
        self, application, checkin_controller, show_application=None
    ):
        self._application = application
        self._checkin = checkin_controller
        self._show_application = show_application
        self._ui_api = ApplicationUiApi(
            application, checkin_controller, self._gui_dispatch,
            show_application,
        )

    def register(self, registry):
        registry.register("tactic.module_getattr", self.module_getattr)
        registry.register("tactic.module_call", self.module_call)
        registry.register("tactic.object_getattr", self.object_getattr)
        registry.register("tactic.object_call", self.object_call)
        registry.register("tactic.object_release", self.object_release)
        registry.register("tactic.environment_getattr", self.environment_getattr)
        registry.register("tactic.environment_call", self.environment_call)

    def module_getattr(self, payload):
        module = self._module(payload.get("module"))
        name = self._public_name(payload.get("name"))
        value = getattr(module, name)
        return self._describe(value, name)

    def module_call(self, payload):
        module = self._module(payload.get("module"))
        name = self._public_name(payload.get("name"))
        callback = getattr(module, name)
        if not callable(callback):
            raise TypeError(f"TACTIC API attribute is not callable: {name}")
        return self._encode(callback(
            *self._decode(payload.get("args") or []),
            **self._decode(payload.get("kwargs") or {}),
        ))

    def object_getattr(self, payload):
        value = self._object(payload.get("handle"))
        name = self._public_name(payload.get("name"))
        attribute = getattr(value, name)
        return self._describe(attribute, name)

    def object_call(self, payload):
        value = self._object(payload.get("handle"))
        name = self._public_name(payload.get("name"))
        callback = getattr(value, name)
        if not callable(callback):
            raise TypeError(f"TACTIC object attribute is not callable: {name}")
        return self._encode(callback(
            *self._decode(payload.get("args") or []),
            **self._decode(payload.get("kwargs") or {}),
        ))

    def object_release(self, payload):
        handle = str(payload.get("handle") or "")
        with self._lock:
            value = self._objects.pop(handle, None)
            if value is not None:
                self._handles.pop(id(value), None)
        return {"released": value is not None}

    def environment_getattr(self, payload):
        from thlib import environment

        name = self._public_name(payload.get("name"))
        if name == "ui_main":
            if not self._ui_api:
                raise RuntimeError("The modern application UI is not attached")
            return self._encode(self._ui_api)
        value = getattr(environment.env_inst, name)
        return self._describe(value, name)

    def environment_call(self, payload):
        from thlib import environment

        name = self._public_name(payload.get("name"))
        if name == "get_check_tree":
            if not self._ui_api:
                raise RuntimeError("The modern check-in service is not attached")
            args = self._decode(payload.get("args") or [])
            kwargs = self._decode(payload.get("kwargs") or {})
            return self._encode(self._ui_api.get_check_tree(*args, **kwargs))
        callback = getattr(environment.env_inst, name)
        if not callable(callback):
            raise TypeError(f"Environment attribute is not callable: {name}")
        return self._encode(callback(
            *self._decode(payload.get("args") or []),
            **self._decode(payload.get("kwargs") or {}),
        ))

    def _module(self, name):
        module_name = self._MODULES.get(str(name or ""))
        if not module_name:
            raise LookupError(f"TACTIC API module is not exposed: {name}")
        return importlib.import_module(module_name)

    @staticmethod
    def _public_name(name):
        name = str(name or "")
        if not name or name.startswith("_") or "." in name:
            raise PermissionError(f"Private API access is not allowed: {name}")
        return name

    def _describe(self, value, name):
        if callable(value):
            return {
                "__remote_callable__": True,
                "name": name,
            }
        return self._encode(value)

    def _object(self, handle):
        with self._lock:
            value = self._objects.get(str(handle or ""))
        if value is None:
            raise ReferenceError("Remote TACTIC object has expired")
        return value

    def _store(self, value):
        identity = id(value)
        with self._lock:
            handle = self._handles.get(identity)
            if handle:
                return handle
            if len(self._objects) >= self._max_objects:
                raise RuntimeError("Remote TACTIC object limit reached")
            handle = uuid.uuid4().hex
            self._objects[handle] = value
            self._handles[identity] = handle
        return handle

    def _encode(self, value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, bytes):
            return {
                "__remote_bytes__": base64.b64encode(value).decode("ascii")
            }
        if isinstance(value, (datetime, date)):
            return {"__remote_datetime__": value.isoformat()}
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, list):
            return [self._encode(item) for item in value]
        if isinstance(value, tuple):
            return {
                "__remote_container__": "tuple",
                "items": [self._encode(item) for item in value],
            }
        if isinstance(value, set):
            return {
                "__remote_container__": "set",
                "items": [self._encode(item) for item in value],
            }
        if isinstance(value, dict):
            if all(isinstance(key, str) for key in value):
                return {key: self._encode(item) for key, item in value.items()}
            return {
                "__remote_mapping__": [
                    [self._encode(key), self._encode(item)]
                    for key, item in value.items()
                ]
            }
        module_name = type(value).__module__
        if (
            isinstance(value, RpcApiObject)
            or module_name.startswith(("thlib.", "tactic_client_lib"))
        ):
            return {
                "__remote_object__": True,
                "handle": self._store(value),
                "type": type(value).__name__,
                "module": module_name,
            }
        if inspect.isgenerator(value):
            return [self._encode(item) for item in value]
        raise TypeError(
            f"TACTIC API returned an unsupported value: "
            f"{type(value).__module__}.{type(value).__name__}"
        )

    def _decode(self, value):
        if isinstance(value, list):
            return [self._decode(item) for item in value]
        if not isinstance(value, dict):
            return value
        if "__remote_handle__" in value:
            return self._object(value["__remote_handle__"])
        if "__remote_container__" in value:
            items = [self._decode(item) for item in value.get("items") or []]
            return tuple(items) if value["__remote_container__"] == "tuple" else set(items)
        if "__remote_mapping__" in value:
            return {
                self._decode(key): self._decode(item)
                for key, item in value["__remote_mapping__"]
            }
        return {key: self._decode(item) for key, item in value.items()}


class RpcApiObject:
    pass


class ApplicationUiApi(RpcApiObject):
    def __init__(
        self, application, checkin_controller, dispatch,
        show_application=None,
    ):
        self._application = application
        self._checkin = checkin_controller
        self._dispatch = dispatch
        self._show_application = show_application

    def _gui(self, callback, *args):
        if not self._dispatch:
            raise RuntimeError("Application UI dispatch is unavailable")
        return self._dispatch(callback, *args)

    def create_project_dock(self, project_code, _force=False):
        self.show()
        self._gui(self._application.select_project, str(project_code or ""))
        return True

    def show(self):
        if self._show_application:
            self._show_application({})
        return True

    def raise_(self):
        return self.show()

    def activateWindow(self):
        return self.show()

    def open_project(self, project_code):
        return self.create_project_dock(project_code, False)

    def open_search_key(self, search_key):
        self._gui(self._application.open_search_key, str(search_key or ""))
        return True

    def select_sobject(self, search_key):
        self._gui(self._application.select_sobject, str(search_key or ""))
        return True

    def show_dock(self, panel_id):
        self._gui(self._application.dock_model.show_panel, str(panel_id or ""))
        return True

    def show_window(self, window_id):
        self._gui(self._application.window_model.show_window, str(window_id or ""))
        return True

    def get_check_tree(self, project_code, tab_code, wdg_code):
        return CheckinApi(
            self._application, self._checkin, self._dispatch,
            str(project_code or ""), str(tab_code or ""), str(wdg_code or ""),
            self._show_application,
        )


class CheckinApi(RpcApiObject):
    def __init__(
        self, application, checkin_controller, dispatch,
        project_code, tab_code, wdg_code, show_application=None,
    ):
        self._application = application
        self._checkin = checkin_controller
        self._dispatch = dispatch
        self.project_code = project_code
        self.tab_code = tab_code
        self.wdg_code = wdg_code
        self._show_application = show_application

    def _gui(self, callback, *args):
        if not self._dispatch:
            raise RuntimeError("Check-in UI dispatch is unavailable")
        return self._dispatch(callback, *args)

    def do_creating_ui(self):
        if self._show_application:
            self._show_application({})
        self._gui(self._application.select_project, self.project_code)
        self._gui(self._application.window_model.show_window, "commit_queue")
        self._gui(self._checkin.set_mode, "checkin")
        return True

    def open(self):
        return self.do_creating_ui()

    @staticmethod
    def _sobject(search_key):
        import thlib.tactic_classes as tc

        split = tc.split_search_key(str(search_key or ""))
        asset_code = split.get("asset_code")
        if not asset_code:
            raise ValueError(f"Invalid sObject search key: {search_key}")
        sobjects, _info = tc.get_sobjects_new(
            search_type=split["search_type"],
            filters=[("code", asset_code)],
            limit=1,
        )
        source = next(iter((sobjects or {}).values()), None)
        if source is None:
            raise LookupError(f"sObject was not found: {search_key}")
        return source, split

    @staticmethod
    def _file_paths(files_objects):
        paths = []
        for file_object in files_objects or []:
            if hasattr(file_object, "get_all_files_list"):
                values = file_object.get_all_files_list() or []
            elif hasattr(file_object, "get_full_abs_path"):
                values = [file_object.get_full_abs_path()]
            else:
                values = [file_object]
            if isinstance(values, (str, Path)):
                values = [values]
            paths.extend(str(value) for value in values if value)
        return paths

    def _prepare(
        self, search_key, context, description, paths,
        save_revision=False, snapshot_version=None,
        keep_file_name=False, update_versionless=None,
    ):
        source, split = self._sobject(search_key)
        title = source.get_title() if hasattr(source, "get_title") else ""
        code = source.get_code() if hasattr(source, "get_code") else ""
        self.do_creating_ui()
        return self._gui(
            self._checkin.prepare_external_checkin,
            str(search_key or ""), source,
            str(split.get("project_code") or self.project_code),
            str(title or code or "sObject"), str(code or ""),
            str(context or "publish"), str(description or ""),
            list(paths), bool(save_revision), snapshot_version,
            bool(keep_file_name), update_versionless, True,
        )

    def checkin_from_maya(
        self, search_key, context, description, save_revision=False,
        snapshot_version=None, selected_objects=None, _dcc_context=None,
    ):
        scene = dict(_dcc_context or {})
        path = str(scene.get("path") or "")
        if not path:
            raise ValueError("The current DCC scene must be saved before check-in")
        result = self._prepare(
            search_key, context, description, [path],
            save_revision, snapshot_version,
        )
        result["dccScene"] = scene
        result["selectedObjects"] = bool(selected_objects)
        return result

    def checkin_file_objects(
        self, search_key, context, description, save_revision=False,
        snapshot_version=None, create_icon=True, files_objects=None,
        checkin_type=None, keep_file_name=None, commit_silently=False,
        run_before_checkin=None, run_after_checkin=None,
        single_threaded=False, update_versionless=None,
    ):
        if run_before_checkin or run_after_checkin:
            raise NotImplementedError(
                "DCC callbacks require the command callback channel"
            )
        paths = self._file_paths(files_objects)
        return self._prepare(
            search_key, context, description, paths,
            save_revision, snapshot_version,
            bool(keep_file_name), update_versionless,
        )
