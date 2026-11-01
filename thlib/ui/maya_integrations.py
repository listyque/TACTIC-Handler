"""Configuration owner for local Maya integration discovery and file operations."""

from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot

from tactic_handler_dcc import maya_integration
from thlib.environment import env_inst


class MayaIntegrationsController(QObject):
    stateChanged = Signal()

    def __init__(self, parent=None, *, handler_root=None):
        super().__init__(parent)
        self._root = Path(handler_root or Path(__file__).resolve().parents[2])
        self._rows = []
        self._selected = ""
        self._busy = self._closed = False
        self._message = self._error = ""
        self._worker = None

    @Property("QVariantList", notify=stateChanged)
    def rows(self):
        return self._rows

    @Property("QVariantMap", notify=stateChanged)
    def selected(self):
        return next((row for row in self._rows if row["id"] == self._selected), {})

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=stateChanged)
    def message(self):
        return self._message

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Slot(str)
    def choose(self, identity):
        if not self._busy and any(row["id"] == identity for row in self._rows):
            self._selected = identity
            self.stateChanged.emit()

    @Slot()
    def reload(self):
        self._run("scan")

    @Slot()
    def install(self):
        self._run("install")

    @Slot()
    def remove(self):
        self._run("remove")

    def _run(self, operation):
        if self._closed or self._busy:
            return
        row = dict(self.selected)
        if operation != "scan" and (not row or not row["supported"]):
            return
        if operation == "remove" and not row.get("managed"):
            return
        if operation == "remove" and row.get("pids"):
            self._error = "Close Maya before removing its integration to prevent shelf files being saved again."
            self.stateChanged.emit()
            return
        self._busy, self._error, self._message = True, "", "Working…"
        self.stateChanged.emit()
        if env_inst.local_pool.is_stopped:
            env_inst.local_pool.reopen()
            env_inst.local_pool.start()
        worker = env_inst.local_pool.add_task(self._operate, operation, row, self._root)
        if worker is None:
            self._failed("The local worker pool is shutting down")
            return
        self._worker = worker
        worker.result.connect(self._finished)
        worker.error.connect(self._failed)
        worker.start()

    @staticmethod
    def _operate(operation, row, root):
        if operation == "install":
            maya_integration.install(row["profile"], root)
        elif operation == "remove":
            current = maya_integration.discover()
            if any(item["id"] == row["id"] and item["pids"] for item in current):
                raise RuntimeError("Close Maya before removing its integration to prevent shelf files being saved again.")
            maya_integration.remove(row["profile"])
        return operation, maya_integration.discover()

    @Slot(object)
    def _finished(self, result):
        if self._closed:
            return
        operation, self._rows = result
        if not any(row["id"] == self._selected for row in self._rows):
            self._selected = self._rows[0]["id"] if self._rows else ""
        self._busy, self._worker = False, None
        self._message = {
            "scan": "Search complete" if self._rows else "No Maya installations or profiles found",
            "install": "Integration installed. Restart Maya to apply it.",
            "remove": "Integration removed.",
        }[operation]
        self.stateChanged.emit()

    @Slot(object)
    def _failed(self, error):
        if self._closed:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        self._error = str(payload.get("exception", payload) if isinstance(payload, dict) else payload)
        self._busy, self._worker, self._message = False, None, ""
        self.stateChanged.emit()

    def shutdown(self):
        if self._closed:
            return
        self._closed = True
        worker, self._worker = self._worker, None
        if worker is not None:
            worker.result.disconnect(self._finished)
            worker.error.disconnect(self._failed)
