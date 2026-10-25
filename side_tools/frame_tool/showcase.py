"""A small script-created native Frame window; no scheduler or browser host."""

from collections.abc import Iterable, Mapping
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, qmlEngine
from PySide6.QtQuick import QQuickWindow

from thlib.ui.workspace_models.records import RecordListModel

_windows = []


def create_window(
    engine: QQmlEngine,
    parent: QQuickWindow | None,
    records: Iterable[Mapping[str, object]],
    *, modal: bool = False,
) -> QQuickWindow:
    """Create from an existing GUI engine; records are explicit selected identities."""
    component = QQmlComponent(
        engine, QUrl.fromLocalFile(str(Path(__file__).with_name("Main.qml")))
    )
    selection = RecordListModel(("id", "title"), list(records), identity_role="id")
    window = component.createWithInitialProperties(
        {"applicationRoot": parent, "selectionModel": selection, "modal": modal}
    )
    if window is None:
        errors = "\n".join(error.toString() for error in component.errors())
        component.deleteLater()
        raise RuntimeError(errors)
    selection.setParent(window)
    QQmlEngine.setObjectOwnership(window, QQmlEngine.CppOwnership)
    _windows.append((window, component))

    def release():
        if (window, component) not in _windows:
            return
        _windows.remove((window, component))
        window.deleteLater()
        component.deleteLater()

    window.disposeRequested.connect(lambda: QTimer.singleShot(0, release))
    window.show()
    return window


def show(
    records: Iterable[Mapping[str, object]] = (), parent: QQuickWindow | None = None,
    *, modal: bool = False,
) -> QQuickWindow:
    """Call on the Handler GUI thread, like existing script-created QML tools."""
    from thlib.environment import env_inst

    parent = parent or env_inst.ui_main
    engine = qmlEngine(parent) if parent is not None else None
    if engine is None:
        raise RuntimeError("Open this example from the Handler GUI")
    return create_window(engine, parent, records, modal=modal)
