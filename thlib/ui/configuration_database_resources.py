"""Configuration-owned asynchronous database resource documents."""

import json
from urllib.error import HTTPError
from urllib.request import Request

from PySide6.QtCore import Property, Signal, Slot

from .admin.editor import AdminDocumentEditor
from .server_address import normalize_tactic_server_url


class DatabaseResourcesEditor(AdminDocumentEditor):
    targetChanged = Signal()
    confirmationChanged = Signal()
    saveCancelled = Signal()

    def __init__(self, application, parent=None):
        super().__init__(application, None, parent)
        self._database = self._project_target = self._confirmation = ""
        self._server_key = self._connection_key()
        if hasattr(application, "server_state_changed"):
            application.server_state_changed.connect(self._session_changed)

    def _connection_key(self):
        return (
            getattr(self._application, "server_url", ""),
            getattr(self._application, "server_user", ""),
        )

    @Slot()
    def _session_changed(self):
        key = self._connection_key()
        if key != self._server_key or not self._application.can_manage_tools:
            self._server_key = key
            self.reset()
            self._database = self._project_target = self._confirmation = ""
            self.targetChanged.emit()
            self.confirmationChanged.emit()

    @Slot()
    def open(self):
        if self._application.can_manage_tools:
            self.activate("admin")

    @Property(str, notify=targetChanged)
    def database(self):
        return self._database

    @Property(str, notify=targetChanged)
    def projectTarget(self):
        return self._project_target

    @Property(str, notify=confirmationChanged)
    def confirmation(self):
        return self._confirmation

    @Slot(str)
    def set_database(self, value):
        if not self.busy:
            self._database = value
            self.targetChanged.emit()

    @Slot(str)
    def set_project(self, value):
        if not self.busy:
            self._project_target = value
            self._database = next(
                (
                    row["database"]
                    for row in self._metadata.get("projects", [])
                    if row["code"] == value
                ),
                "",
            )
            self.targetChanged.emit()

    def _document_loaded(self):
        bound = [
            row
            for row in self._metadata.get("projects", [])
            if row["resource"] == self.identity
        ]
        if not self._database:
            self._database = bound[0]["database"] if bound else ""
        if not self._project_target:
            self._project_target = bound[0]["code"] if bound else ""
        self.targetChanged.emit()

    def _execute_request(self, arguments, project, original):
        from thlib import tactic_classes as tc

        server = tc.server_start(project="admin")
        action = arguments.get("operation", arguments["action"])
        payload = {
            name: arguments[name]
            for name in (
                "identity",
                "expected_revision",
                "database",
                "project_code",
                "confirmation",
            )
            if name in arguments
        }
        if action in ("save", "test"):
            payload["document"] = (
                arguments["document"] if action == "save" else original
            )
        payload["ticket"] = server.login_ticket
        url = (
            normalize_tactic_server_url(server.get_server_name())
            + "/admin/configuration/database-resources/"
            + action
        )
        request = Request(
            url, json.dumps(payload).encode(), {"Content-Type": "application/json"}
        )
        try:
            with server.transport.open(request, timeout=30) as response:
                return json.load(response)["result"]
        except HTTPError as error:
            with error:
                message = json.load(error).get(
                    "error", "Database resource operation failed"
                )
            raise RuntimeError(message) from None

    @Slot()
    def reload(self):
        if self.writeUncertain:
            self.discard()
        super().reload()

    @Slot()
    def discard(self):
        if not self.busy:
            self._confirmation = ""
            self.confirmationChanged.emit()
            self.saveCancelled.emit()
            super().discard()

    @Slot(str)
    def choose(self, identity):
        if not self.busy and not self.dirty:
            self._database = self._project_target = ""
            self.select(identity)

    @Slot(str)
    def action(self, action):
        if self.busy:
            return
        if action == "reject":
            was_save = self._confirmation == "save"
            self._confirmation = ""
            self.confirmationChanged.emit()
            if was_save:
                self.saveCancelled.emit()
        elif action == "accept":
            operation, self._confirmation = self._confirmation, ""
            self.confirmationChanged.emit()
            if operation:
                self._request(
                    "save"
                    if operation in ("save", "delete", "bind", "unbind")
                    else operation,
                    self.identity,
                    operation=operation,
                    database=self._database,
                    project_code=self._project_target,
                    confirmation=operation,
                )
        elif not self.dirty and not self.writeUncertain:
            if action == "test":
                self._request(action, self.identity, database=self._database)
            elif action in ("delete", "bind", "unbind", "upgrade"):
                self._confirmation = action
                self.confirmationChanged.emit()

    @Slot()
    def save(self):
        if self.canWrite and self.dirty and not self.busy and not self.writeUncertain:
            bound = any(
                row["resource"] == self.identity
                for row in self._metadata.get("projects", [])
            )
            if bound:
                self._confirmation = "save"
                self.confirmationChanged.emit()
            else:
                super().save()
