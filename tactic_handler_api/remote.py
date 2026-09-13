"""One explicit domain API over an existing ThinClient connection."""

from copy import deepcopy
import logging
import threading
import uuid

from .api import HandlerAPI
from .contract import METHODS, PROPERTIES
from . import errors, wire
from .objects import SObject as BaseSObject


class Handle:
    def __init__(self, api, handle, type_name):
        self._api, self._handle, self._type_name = api, handle, type_name

    def __repr__(self):
        return f"<{self._type_name} {self._handle}>"

    def __dir__(self):
        return sorted(
            set(super().__dir__())
            | set(METHODS[self._type_name])
            | set(PROPERTIES.get(self._type_name, ()))
        )

    def __getattr__(self, name):
        if name in PROPERTIES.get(self._type_name, ()):
            return self._api._invoke(self._handle, name, read=True)
        if name in METHODS[self._type_name]:

            def call(*args, **kwargs):
                return self._api._invoke(self._handle, name, args, kwargs)

            call.__name__ = name
            return call
        raise AttributeError(f"{self._type_name} has no public member {name!r}")

    def release(self):
        self._api._request("handler.release", {"handle": self._handle})


class QueueItem(Handle):
    def submit(self):
        return self._api.submit(self.commit)


class SObject(BaseSObject):
    """Staging and cached field reads remain local, as in the headless API."""

    def __init__(self, api, handle, info, is_new):
        super().__init__(api, None, None if is_new else True, {} if is_new else info)
        self._handle = handle
        self._type_name = "SObject"
        if is_new:
            self._changes = deepcopy(info)

    def get_project(self):
        return self._api._invoke(self._handle, "get_project")

    def get_stype(self):
        return self._api._invoke(self._handle, "get_stype")

    def commit(self, *, triggers=True):
        changes = self._begin_write()
        try:
            result = self._api._invoke(
                self._handle,
                "commit",
                kwargs={"triggers": triggers},
                changes=changes,
            )
            with self._lock:
                self._info = deepcopy(result._info)
                self._changes.clear()
                self._native = True
            return self
        finally:
            with self._lock:
                self._busy = False

    def refresh(self):
        self._begin_write(require_clean=True)
        try:
            result = self._api._invoke(self._handle, "refresh")
            with self._lock:
                self._info = deepcopy(result._info)
            return self
        finally:
            with self._lock:
                self._busy = False

    def related(self, **kwargs):
        return self._api._invoke(self._handle, "related", kwargs=kwargs)

    def link(self, target, *, relation, path=None):
        return self._api._invoke(
            self._handle,
            "link",
            (target,),
            {"relation": relation, "path": path},
        )

    def tasks(self, process=None):
        return self._api._invoke(self._handle, "tasks", kwargs={"process": process})

    def notes(self, process=None, context=None):
        return self._api._invoke(
            self._handle, "notes", kwargs={"process": process, "context": context}
        )

    def snapshots(self, **kwargs):
        return self._api._invoke(self._handle, "snapshots", kwargs=kwargs)

    def dependencies(self):
        return self._api._invoke(self._handle, "dependencies")

    def delete(self, *, dependencies=()):
        self._begin_write(require_clean=True)
        try:
            return self._api._invoke(
                self._handle, "delete", kwargs={"dependencies": dependencies}
            )
        finally:
            with self._lock:
                self._busy = False

    def release(self):
        self._api._request("handler.release", {"handle": self._handle})


class API(HandlerAPI):
    def __init__(self, client, target, timeout, **limits):
        super().__init__(None, None, **limits)
        self._client, self._target, self._timeout = client, target, timeout
        self._session_id = uuid.uuid4().hex
        self._ui_backend = Handle(self, "ui", "UICommands")
        self._closing_thread = None
        self._used = False

    def _reference(self, value):
        if (
            not isinstance(value, (Handle, SObject))
            or value._api is not self
        ):
            raise TypeError(
                "Expected a domain value or an object from this API session"
            )
        return {"kind": "ref", "id": value._handle}

    def _restore(self, value):
        type_name = value["type"]
        if type_name not in METHODS:
            raise ValueError("Handler returned an unsupported API object")
        if type_name == "SObject":
            info = wire.decode(value["info"], self._restore)
            return SObject(self, value["id"], info, value["new"])
        cls = QueueItem if type_name == "QueueItem" else Handle
        return cls(self, value["id"], type_name)

    def _request(self, action, payload):
        self._check()
        self._used = True
        response = self._client.request(
            self._target,
            action,
            {
                "session": self._session_id,
                **payload,
            },
            timeout=self._timeout,
        )
        if "error" in response:
            detail = response["error"]
            error_types = {
                name: getattr(errors, name)
                for name in (
                    "ApiError",
                    "NotFound",
                    "DirtyObject",
                    "ConcurrentEdit",
                    "UIUnavailable",
                    "BlockingCallError",
                    "QueueFull",
                    "NotReady",
                )
            }
            error_types.update(
                ValueError=ValueError,
                TypeError=TypeError,
                OSError=OSError,
                TimeoutError=TimeoutError,
                RuntimeError=RuntimeError,
                ReferenceError=ReferenceError,
                PermissionError=PermissionError,
            )
            error = error_types.get(detail["type"], RuntimeError)(detail["message"])
            remote_traceback = detail.get("traceback")
            add_note = getattr(error, "add_note", None)
            if remote_traceback and callable(add_note):
                add_note(remote_traceback)
            elif remote_traceback:
                error.args = (
                    "{}\n\nRemote traceback:\n{}".format(
                        detail["message"], remote_traceback
                    ),
                )
            raise error
        return wire.decode(response["value"], self._restore)

    def _invoke(
        self, handle, member, args=(), kwargs=None, *, read=False, changes=None
    ):
        payload = {
            "handle": handle,
            "member": member,
            "read": read,
            "args": wire.encode(list(args), self._reference),
            "kwargs": wire.encode(kwargs or {}, self._reference),
        }
        if changes is not None:
            payload["changes"] = wire.encode(changes, self._reference)
        return self._request("handler.call", payload)

    def projects(self):
        return self._invoke("root", "projects")

    def project(self, project_code):
        return self._invoke("root", "project", [project_code])

    def sobject(self, search_key):
        return self._invoke("root", "sobject", [str(self._key(search_key))])

    def snapshot(self, search_key):
        return self._invoke("root", "snapshot", [search_key])

    def logins(self):
        return self._invoke("root", "logins")

    def login(self, login_name):
        return self._invoke("root", "login", [login_name])

    @property
    def files(self):
        return Handle(self, "files", "FilesAPI")

    @property
    def repositories(self):
        return Handle(self, "repositories", "RepositoriesAPI")

    def commit_queue(self, project_code=None):
        return Handle(self, "queue:" + (project_code or ""), "CommitQueue")

    def close(self, *, wait=True):
        from .api import _unbind_current

        _unbind_current(self)
        if self._closed:
            if wait and self._closing_thread is not None:
                from .operations import check_blocking_call

                check_blocking_call()
                self._closing_thread.join()
            return
        if wait:
            from .operations import check_blocking_call

            check_blocking_call()
        self._executor.close(wait=False)
        self._closed = True

        def finish():
            self._executor.close(wait=True)
            if not self._used:
                return
            try:
                self._client.request(
                    self._target,
                    "handler.close",
                    {"session": self._session_id},
                    timeout=5,
                )
            except (OSError, RuntimeError, TimeoutError) as error:
                logging.getLogger(__name__).warning(
                    "API handle cleanup failed (%s)", type(error).__name__
                )

        if wait:
            finish()
        else:
            self._closing_thread = threading.Thread(
                target=finish, name="handler-api-close", daemon=True
            )
            self._closing_thread.start()
