"""Run the portable dock geometry in Qt's JavaScript runtime, without QML UI."""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QThread
from PySide6.QtQml import QJSEngine


class DockProjection:
    def __init__(self, application):
        self.engine = QJSEngine(application)
        source = (
            Path(__file__).resolve().parents[1]
            / "qml/tactic_frame/shell/dock.layout.mjs"
        )
        self.module = self.engine.importModule(str(source))
        if self.module.isError():
            raise RuntimeError(self.module.toString())

    def call(self, name, *arguments):
        if QThread.currentThread() != self.engine.thread():
            raise RuntimeError("Dock layout must run on its owning UI thread")
        result = self.module.property(name).call(
            [self.engine.toScriptValue(value) for value in arguments]
        )
        if result.isError():
            raise RuntimeError(f"Dock layout {name}: {result.toString()}")
        return result.toVariant()


def runtime() -> DockProjection:
    application = QCoreApplication.instance()
    if application is None:
        raise RuntimeError("Dock layout requires a Qt application")
    if QThread.currentThread() != application.thread():
        raise RuntimeError("Dock layout must run on the UI thread")
    # One evaluator per application; it owns no layout, settings or UI objects.
    if not hasattr(application, "_dock_projection"):
        application._dock_projection = DockProjection(application)
    return application._dock_projection


def decode(node):
    from .docks_tree import DockSplit, DockStack

    if node is None:
        return None
    if node["type"] == "stack":
        return DockStack(tuple(node["panels"]), node["active"])
    return DockSplit(
        node["orientation"],
        node["ratio"],
        decode(node["first"]),
        decode(node["second"]),
    )
