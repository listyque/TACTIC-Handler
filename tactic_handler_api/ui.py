"""Optional UI commands that own dispatch; no Qt objects cross this boundary."""

from __future__ import annotations

from concurrent.futures import Future
from typing import TypeVar

from .errors import UIUnavailable
from .operations import Operation


_Target = TypeVar("_Target")


class UIAPI:
    def __init__(self, api, backend):
        self._api = api
        self._backend = backend

    def _show(self, target: _Target, *commands: tuple[str, ...]) -> Operation[_Target]:
        def execute():
            self._api._check()
            if self._backend is None:
                raise UIUnavailable("No UI is attached to this API session")
            backend = self._backend() if callable(self._backend) else self._backend
            if backend is None:
                raise UIUnavailable("The Handler UI is unavailable")
            for method, *args in commands:
                getattr(backend, method)(*args)
            return target

        if not self._api._executor.running_here:
            return self._api.submit(execute)
        # Data operations may finish by showing UI. They already own a worker;
        # keep their steps sequential without nesting work into the same pool.
        # The backend still marshals every UI mutation to its owning Qt thread.
        future = Future()
        try:
            future.set_result(execute())
        except Exception as error:
            future.set_exception(error)
        return Operation(future)

    def show(self) -> Operation[UIAPI]:
        """Show Handler without blocking the calling GUI/DCC thread."""
        return self._show(self, ("show",))

    def checkin_from_dcc(
        self,
        search_key: str,
        context: str,
        description: str,
        application_type: str,
        client_id: str,
    ) -> Operation[UIAPI]:
        if not search_key or not application_type or not client_id:
            raise ValueError(
                "A scene Search Key, DCC application and client id are required"
            )
        return self._show(
            self,
            (
                "checkin_from_dcc",
                search_key,
                context,
                description,
                application_type,
                client_id,
            ),
        )

    def checkin_from_maya(
        self, search_key: str, context: str, description: str, client_id: str
    ) -> Operation[UIAPI]:
        """Compatibility alias for existing Maya scripts."""
        if not search_key or not client_id:
            raise ValueError("A scene Search Key and Maya client id are required")
        return self._show(
            self,
            (
                "checkin_from_maya",
                search_key,
                context,
                description,
                client_id,
            ),
        )

    def checkin_files(
        self, search_key: str, context: str, description: str, paths
    ) -> Operation[UIAPI]:
        if isinstance(paths, (str, bytes)):
            raise TypeError("paths must be a collection of files")
        paths = [str(path) for path in paths]
        if not search_key or not paths:
            raise ValueError("An sObject Search Key and files are required")
        return self._show(
            self,
            ("checkin_files", search_key, context, description, paths),
        )

    def project(self, project_code: str):
        if not project_code:
            raise ValueError("Project code is required")
        return ProjectUI(self, project_code)

    def sobject(self, search_key_or_object):
        return SObjectUI(self, self._api._key(search_key_or_object))

    def window(self, window_id: str):
        if not window_id:
            raise ValueError("A registered window id is required")
        return WindowUI(self, window_id)

    def dock(self, dock_id: str):
        if not dock_id:
            raise ValueError("A registered dock id is required")
        return DockUI(self, dock_id)


class ProjectUI:
    def __init__(self, ui, project_code):
        self._ui = ui
        self.project_code = project_code

    def show(self) -> Operation[ProjectUI]:
        return self._ui._show(self, ("open_project", self.project_code))

    def commit_queue(self):
        return WindowUI(self._ui, "commit_queue", project_code=self.project_code)


class SObjectUI:
    def __init__(self, ui, identity):
        self._ui = ui
        self.identity = identity

    def show(self) -> Operation[SObjectUI]:
        return self._ui._show(self, ("open_search_key", str(self.identity)))

    def snapshots(self):
        return DockUI(self._ui, "snapshot", target=self)

    def notes(self):
        return DockUI(self._ui, "notes", target=self)

    def tasks(self):
        return DockUI(self._ui, "tasks", target=self)

    def commit_queue(self):
        return WindowUI(self._ui, "commit_queue", target=self)


class WindowUI:
    def __init__(self, ui, window_id, *, project_code=None, target=None):
        self._ui = ui
        self.id = window_id
        self._project_code = project_code
        self._target = target

    def show(self) -> Operation[WindowUI]:
        commands = []
        if self._target is not None:
            commands.append(("open_search_key", str(self._target.identity)))
        elif self._project_code is not None:
            commands.append(("open_project", self._project_code))
        commands.append(("show_window", self.id))
        return self._ui._show(self, *commands)


class DockUI:
    def __init__(self, ui, dock_id, *, target=None):
        self._ui = ui
        self.id = dock_id
        self._target = target

    def show(self) -> Operation[DockUI]:
        commands = []
        if self._target is not None:
            commands.append(("open_search_key", str(self._target.identity)))
        commands.append(("show_dock", self.id))
        return self._ui._show(self, *commands)
