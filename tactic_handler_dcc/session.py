from __future__ import annotations

import base64
import threading


class RemoteObject:
    def __init__(self, session, handle, type_name="Object", module=""):
        self._session = session
        self._handle = str(handle)
        self._type_name = str(type_name or "Object")
        self._module = str(module or "")
        self._attributes = {}

    def __repr__(self):
        return f"<{self._type_name} remote:{self._handle[:8]}>"

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._attributes:
            value = self._session._request("tactic.object_getattr", {
                "handle": self._handle, "name": name,
            })
            self._attributes[name] = self._callable(name) if (
                isinstance(value, dict) and value.get("__remote_callable__")
            ) else value
        return self._attributes[name]

    def _callable(self, name):
        def invoke(*args, **kwargs):
            if self._type_name == "CheckinApi" and name == "checkin_from_maya":
                from .maya_functions import MayaFunctions

                selected_objects = kwargs.get("selected_objects")
                if selected_objects is None and len(args) > 5:
                    selected_objects = args[5]
                kwargs["_dcc_context"] = (
                    MayaFunctions.instance().prepare_checkin_scene(
                        selected_objects
                    )
                )
            return self._session._request("tactic.object_call", {
                "handle": self._handle,
                "name": name,
                "args": self._session._encode(list(args)),
                "kwargs": self._session._encode(kwargs),
            })
        invoke.__name__ = name
        return invoke

    def release(self):
        result = self._session._request("tactic.object_release", {
            "handle": self._handle,
        })
        return bool(result.get("released"))


class RemoteModule:
    def __init__(self, session, module):
        self._session = session
        self._module = str(module)
        self._attributes = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._attributes:
            value = self._session._request("tactic.module_getattr", {
                "module": self._module, "name": name,
            })
            self._attributes[name] = self._callable(name) if (
                isinstance(value, dict) and value.get("__remote_callable__")
            ) else value
        return self._attributes[name]

    def _callable(self, name):
        def invoke(*args, **kwargs):
            return self._session._request("tactic.module_call", {
                "module": self._module,
                "name": name,
                "args": self._session._encode(list(args)),
                "kwargs": self._session._encode(kwargs),
            })
        invoke.__name__ = name
        return invoke


class RemoteEnvironment:
    def __init__(self, session):
        self._session = session
        self._attributes = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._attributes:
            value = self._session._request("tactic.environment_getattr", {
                "name": name,
            })
            self._attributes[name] = self._callable(name) if (
                isinstance(value, dict) and value.get("__remote_callable__")
            ) else value
        return self._attributes[name]

    def _callable(self, name):
        def invoke(*args, **kwargs):
            return self._session._request("tactic.environment_call", {
                "name": name,
                "args": self._session._encode(list(args)),
                "kwargs": self._session._encode(kwargs),
            })
        invoke.__name__ = name
        return invoke


class TacticSession:
    def __init__(self, client, target="@modern_ui", timeout=60.0):
        self.client = client
        self.target = str(target)
        self.timeout = float(timeout)
        self._modules = {}
        self._environment = RemoteEnvironment(self)

    @property
    def environment(self):
        return self._environment

    def module(self, name):
        name = str(name)
        if name not in self._modules:
            self._modules[name] = RemoteModule(self, name)
        return self._modules[name]

    def _request(self, action, payload):
        result = self.client.request(
            self.target, action, payload, timeout=self.timeout
        )
        if set(result) == {"value"}:
            result = result["value"]
        return self._decode(result)

    def _encode(self, value):
        if isinstance(value, RemoteObject):
            if value._session is not self:
                raise ValueError("Remote objects belong to another TACTIC session")
            return {"__remote_handle__": value._handle}
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
            return {str(key): self._encode(item) for key, item in value.items()}
        return value

    def _decode(self, value):
        if isinstance(value, list):
            return [self._decode(item) for item in value]
        if not isinstance(value, dict):
            return value
        if value.get("__remote_object__"):
            return RemoteObject(
                self, value["handle"], value.get("type"), value.get("module")
            )
        if "__remote_bytes__" in value:
            return base64.b64decode(value["__remote_bytes__"])
        if "__remote_datetime__" in value:
            return value["__remote_datetime__"]
        if "__remote_container__" in value:
            items = [self._decode(item) for item in value.get("items") or []]
            return tuple(items) if value["__remote_container__"] == "tuple" else set(items)
        if "__remote_mapping__" in value:
            return {
                self._decode(key): self._decode(item)
                for key, item in value["__remote_mapping__"]
            }
        return {key: self._decode(item) for key, item in value.items()}


_session = None
_session_lock = threading.Lock()


def configure_session(client, target="@modern_ui", timeout=60.0):
    global _session
    with _session_lock:
        _session = TacticSession(client, target, timeout)
    return _session


def current_session():
    if _session is None:
        raise RuntimeError(
            "TACTIC DCC SDK is not configured. Call environment.configure(client)."
        )
    return _session
