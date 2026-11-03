"""Native installer composer; employees still sign in with their own accounts."""

from pathlib import Path

from PySide6.QtCore import QObject, Property, QStandardPaths, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from tactic_handler_dcc.connectors import plugin_catalog
from thlib.environment import env_inst
from .setup_package import DEFAULTS, build_installer, read_installer


class SetupBuilderController(QObject):
    stateChanged = Signal()

    def __init__(self, root: Path, parent=None):
        super().__init__(parent)
        self.root = root
        self._closed = False
        self._worker = None
        self._defaults_edited = False
        self._state = {
            "template": "",
            "output": "",
            "version": "",
            "busy": False,
            "error": "",
            "result": "",
            "defaults": dict(DEFAULTS),
            "plugins": plugin_catalog(),
        }
        template = root.parent / "setup-template.bin"
        if template.is_file():
            self._load(template)

    @Property("QVariantMap", notify=stateChanged)
    def state(self):
        return dict(self._state)

    @Slot(str, "QVariant")
    def edit(self, key, value):
        if not self._state["busy"] and key in DEFAULTS and key != "plugins":
            self._state["defaults"] = {**self._state["defaults"], key: value}
            self._defaults_edited = True
            self._state["result"] = ""
            self.stateChanged.emit()

    @Slot(str, bool)
    def toggle_plugin(self, identity, enabled):
        if self._state["busy"] or identity not in {
            row["id"] for row in self._state["plugins"]
        }:
            return
        selected = set(self._state["defaults"]["plugins"] or [])
        selected.add(identity) if enabled else selected.discard(identity)
        self._state["defaults"] = {
            **self._state["defaults"],
            "plugins": sorted(selected),
        }
        self._defaults_edited = True
        self.stateChanged.emit()

    @Slot()
    def browse_template(self):
        path, _ = QFileDialog.getOpenFileName(
            None, self.tr("Base TH installer"), "", self.tr("EXE files (*.exe)")
        )
        if path:
            self._load(Path(path))

    def _load(self, path):
        self._state.update(template=str(path), version="", result="")
        self._run("template", lambda: read_installer(path)[0])

    @Slot()
    def browse_output(self):
        desktop = Path(QStandardPaths.writableLocation(QStandardPaths.DesktopLocation))
        path, _ = QFileDialog.getSaveFileName(
            None,
            self.tr("Save your installer"),
            self._state["output"] or str(desktop / "TACTIC-Handler-Setup.exe"),
            self.tr("EXE files (*.exe)"),
        )
        if path:
            target = Path(path).with_suffix(".exe").resolve()
            if target.is_relative_to(self.root.parent.resolve()):
                self._state["error"] = self.tr(
                    "Save the installer outside the TH application folder"
                )
            else:
                self._state.update(output=str(target), result="", error="")
            self.stateChanged.emit()

    @Slot()
    def build(self):
        if self._state["busy"] or not self._state["version"]:
            return
        if not self._state["output"]:
            self.browse_output()
        if not self._state["output"]:
            return
        source, target = Path(self._state["template"]), Path(self._state["output"])
        if target.resolve().is_relative_to(self.root.parent.resolve()):
            self._failed("Save the installer outside the TH application folder")
            return
        values = dict(self._state["defaults"])
        self._run("build", lambda: build_installer(source, target, values))

    @Slot()
    def open_output(self):
        if self._state["result"]:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(Path(self._state["result"]).parent))
            )

    def _run(self, operation, function):
        if self._closed or self._state["busy"]:
            return
        self._state.update(busy=True, error="", result="")
        self.stateChanged.emit()
        worker = env_inst.local_pool.add_task(lambda: (operation, function()))
        if worker is None:
            self._failed("The local worker pool is shutting down")
            return
        self._worker = worker
        worker.result.connect(self._finished)
        worker.error.connect(self._failed)
        worker.start()

    @Slot(object)
    def _finished(self, result):
        if self._closed:
            return
        operation, value = result
        if operation == "template":
            defaults = dict(value["defaults"])
            if defaults["plugins"] is None:
                defaults["plugins"] = [row["id"] for row in self._state["plugins"]]
            self._state["version"] = value["version"]
            if not self._defaults_edited:
                self._state["defaults"] = defaults
        else:
            self._state["result"] = value["path"]
        self._state["busy"] = False
        self._worker = None
        self.stateChanged.emit()

    @Slot(object)
    def _failed(self, error):
        if self._closed:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        message = str(
            payload.get("exception", payload) if isinstance(payload, dict) else payload
        )
        self._state.update(busy=False, error=self.tr(message))
        self._worker = None
        self.stateChanged.emit()

    def shutdown(self):
        self._closed = True
