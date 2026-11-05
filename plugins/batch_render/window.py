"""Batch scheduler QML view and window lifecycle."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, qmlEngine

from tactic_handler_api import get_api

from .controller import BatchDispatcherController

# QML view


QML_SOURCE = (Path(__file__).parent / 'ui/BatchWindow.qml').read_text(encoding='utf-8')
# Window lifecycle


_RUNTIME_WINDOWS = globals().get("_RUNTIME_WINDOWS", [])


def _handler_context(parent):
    if parent is None:
        raise RuntimeError("TACTIC Handler main window is not available")
    engine = qmlEngine(parent)
    if engine is None:
        raise RuntimeError("TACTIC Handler QML engine is not available")
    application = engine.rootContext().contextProperty("appController")
    if application is None:
        raise RuntimeError("TACTIC Handler application controller is unavailable")
    return engine, application


def _create_window(engine, application_root, parent, controller):
    source = QML_SOURCE.replace(
        "__APP_QML_URL__",
        QUrl.fromLocalFile(str(application_root / "thlib/ui/qml")).toString(),
    ).replace(
        "__CONTROLS_URL__",
        QUrl.fromLocalFile(str(application_root / "thlib/ui/qml/controls")).toString(),
    )
    source = source.replace('__FRAME_URL__',
        QUrl.fromLocalFile(str(application_root / 'thlib/ui/qml/tactic_frame')).toString()
    ).replace('__NODES_URL__',
        QUrl.fromLocalFile(str(application_root / 'thlib/ui/qml/tactic_frame/core/frame.mjs')).toString())
    # Qt caches modules for the engine's lifetime; temporary copies avoid stale UI.
    modules = {}
    with tempfile.TemporaryDirectory(prefix="th-batch-ui-") as directory:
        for property_name, name in (("summaryUI", "summary.mjs"), ("itemMetrics", "items.mjs")):
            module_path = Path(directory) / name
            module_path.write_bytes((Path(__file__).parent / "ui" / name).read_bytes())
        for property_name, name in (("summaryUI", "summary.mjs"), ("itemMetrics", "items.mjs")):
            module = engine.importModule(str(Path(directory) / name))
            if module.isError():
                raise RuntimeError(f"Cannot load Batch Render module {name}: {module.toString()}")
            modules[property_name] = module
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl.fromLocalFile(str(Path(__file__).parent / "ui/BatchWindow.qml")))
    if component.isError():
        details = "\n".join(error.toString() for error in component.errors())
        component.deleteLater()
        raise RuntimeError(f"Cannot load Batch Dispatcher QML:\n{details}")
    window = component.createWithInitialProperties(
        {"applicationRoot": parent, "controller": controller, **modules}
    )
    if window is None:
        details = "\n".join(error.toString() for error in component.errors())
        component.deleteLater()
        raise RuntimeError(f"Cannot create Batch Dispatcher window:\n{details}")
    return component, window


def _windows_to_hide(parent, application, enabled):
    if not enabled:
        return [], []
    hidden_windows = [parent] if parent.isVisible() else []
    window_model = getattr(application, "window_model", None)
    hidden_ids = []
    if window_model is not None and window_model.is_window_visible("script_editor"):
        hidden_ids.append("script_editor")
    return hidden_windows, hidden_ids


def show(parent=None, project_code=None, *, hide_handler=True):
    """Show the local batch scheduler backed by the public Handler API."""
    from thlib.environment import env_inst, env_mode

    if _RUNTIME_WINDOWS:
        window = _RUNTIME_WINDOWS[0]["window"]
        window.showNormal()
        window.requestActivate()
        return window

    parent = parent or env_inst.ui_main
    engine, application = _handler_context(parent)
    project_code = str(
        project_code or getattr(application, "current_project_code", "") or ""
    )
    if not project_code:
        raise RuntimeError("Select a project before opening Batch Dispatcher")

    controller = BatchDispatcherController(
        get_api(),
        project_code,
        offline=os.environ.get("TACTIC_QML_SMOKE_OFFLINE", "") == "1",
    )
    application_root = Path(env_mode.get_current_path())
    component, window = _create_window(engine, application_root, parent, controller)

    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    controller.setParent(window)
    hidden_windows, hidden_window_ids = _windows_to_hide(
        parent, application, hide_handler
    )
    entry = {
        "window": window,
        "component": component,
        "controller": controller,
        "application": application,
        "hidden_windows": hidden_windows,
        "hidden_window_ids": hidden_window_ids,
    }
    _RUNTIME_WINDOWS.append(entry)
    controller.windowCloseRequested.connect(lambda: _dispose_window(window))
    controller.attach_window(window)
    window.show()
    window.requestActivate()
    for hidden_window in hidden_windows:
        hidden_window.hide()
    for window_id in hidden_window_ids:
        application.window_model.close_window(window_id)
    controller.initialize()
    return window


def _dispose_window(window):
    entry = next((item for item in _RUNTIME_WINDOWS if item["window"] is window), None)
    if entry is None:
        return
    _RUNTIME_WINDOWS.remove(entry)
    entry["controller"].shutdown()
    window.hide()
    window.deleteLater()
    entry["component"].deleteLater()
    for hidden_window in entry["hidden_windows"]:
        hidden_window.show()
        hidden_window.raise_()
        hidden_window.requestActivate()
    for window_id in entry["hidden_window_ids"]:
        entry["application"].window_model.show_window(window_id)
