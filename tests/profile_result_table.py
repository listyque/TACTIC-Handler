"""Offline real-QML table benchmark: python -m tests.profile_result_table.

No server or production configuration. Timings are diagnostics, not CI limits.
"""

import json
import ctypes
import os
import statistics
import time
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from tests.test_columns_table_view import (
    QML, _TableColumns, _TableController, _visual_items,
    gui_test_application, _Application, _SType,
)
from tests.profile_ui_responsiveness import frame
from PySide6.QtCore import QEvent, QMetaObject, QObject, QPointF, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from thlib.environment import env_mode
from thlib.ui.columns_editor import ColumnsEditorController
from thlib.ui.controllers.result_tree import ResultTreeMixin
from thlib.tactic_table_widgets import TacticTaskTableWidget
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


def working_set_bytes():
    """Native process working set, including Qt allocations (Windows only)."""
    if os.name != "nt":
        return None

    class MemoryCounters(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in (
                "peak", "working", "peakPaged", "paged", "peakNonpaged",
                "nonpaged", "pagefile", "peakPagefile",
            )
        ]

    counters = MemoryCounters()
    size = ctypes.sizeof(counters)
    counters.size = size
    if not ctypes.windll.psapi.GetProcessMemoryInfo(
        ctypes.c_void_p(-1), ctypes.byref(counters), size,
    ):
        raise ctypes.WinError()
    return counters.working


class TableColumns(_TableColumns):
    def __init__(self):
        super().__init__()
        self.reads = 0
        self._columns[6]["width"] = 580

    @Slot(str, int, result="QVariantMap")
    def row_cells(self, search_key, revision):
        self.reads += 1
        cells = super().row_cells(search_key, revision)
        record = cells["tasks"]["tasks"][0]
        cells["tasks"]["tasks"] = [
            dict(record, process=f"process_{index}", taskCode=f"{search_key}:{index}",
                 taskSearchKey=f"sthpw/task?code={search_key}:{index}")
            for index in range(5)
        ]
        return cells


class GroupedTableController(_TableController):
    def __init__(self, model):
        super().__init__()
        self.workspace_model = model
        self.cache_saves = 0

    def _save_search_cache(self):
        self.cache_saves += 1

    @Slot(str)
    def toggle_result_node(self, node_id):
        ResultTreeMixin.toggle_result_node(self, node_id)


def projection_benchmark(count=2000):
    application = _Application(_SType())
    lookups = []

    def search_key(index):
        lookups.append(index)
        return str(index)

    objects = [SimpleNamespace(get_search_key=lambda i=i: search_key(i))
               for i in range(count)]
    application._current_tab = lambda: SimpleNamespace(sobjects=objects)
    tasks = SimpleNamespace(_process_choices_for=lambda target: [],
                            _login_label=lambda login: login)
    controller = ColumnsEditorController(application, tasks)
    controller._table_widgets = {"tasks": TacticTaskTableWidget({})}
    payload = {"rows": {str(i): {"tasks": {"tasks": []}} for i in range(count)}}
    samples = []
    for _ in range(3):
        lookups.clear()
        started = time.perf_counter()
        controller._map_rows(payload)
        samples.append((time.perf_counter() - started) * 1000)
    return {"rows": count, "medianMs": round(statistics.median(samples), 2),
            "identityReads": len(lookups)}


def benchmark(app, width=1600, height=900, grouped=False):
    engine = QQmlEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(
        error.toString() for error in errors))
    theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / "Theme.qml")))
    theme = theme_component.createWithInitialProperties({"dark": True})
    model = WorkspaceItemModel()
    model.replace_nodes([
        WorkspaceNode(node_id=f"asset{index}", node_type="sobject",
                      search_key=f"demo/asset?code={index}", code=str(index),
                      title=f"Asset {index}", preview_requested=True, tasks=5,
                      values={"category": str(index // 50)})
        for index in range(500)
    ])
    columns = TableColumns()
    controller = GroupedTableController(model)
    if grouped:
        model.set_organization(group_mode="column:category")
        model.show_table_rows()
    users = RecordListModel(("login", "displayName", "initials", "avatarUrl"))
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / "SearchResultTable.qml")))
    window = QQuickWindow()
    window.resize(width, height)
    window.show()
    frame(window)
    memory_before = working_set_bytes()
    started = time.perf_counter()
    table = component.createWithInitialProperties({
        "theme": theme, "controller": controller, "columnsController": columns,
        "resultModel": model, "userModel": users, "presentationActive": True,
        "width": width, "height": height, "rowHeight": 100,
    })
    if table is None:
        raise RuntimeError([error.toString() for error in component.errors()])
    table.setParentItem(window.contentItem())
    rows = table.findChild(QQuickItem, "searchResultsTableView")
    presentation = table.findChild(QObject, "initialTablePresentation")
    for _ in range(10):
        frame(window)
        if presentation.property("ready"):
            break
    else:
        raise RuntimeError("Table never presented")
    initial_ms = (time.perf_counter() - started) * 1000
    for _ in range(3):
        frame(window)
    memory_after = working_set_bytes()
    items = _visual_items(window.contentItem())
    task_cells = [item for item in items if item.objectName() == "tableTaskCell"]
    counts = {"visualItems": len(items), "rowDelegates": sum(
        item.objectName() == "searchResultTableRow" for item in items),
        "dateEditors": sum(len(item.findChildren(QObject, "tableTaskDateEditor"))
                           for item in task_cells),
        "taskCards": sum(item.objectName().startswith("tableTaskRecord_")
                         for item in items)}
    if grouped:
        rows.setProperty("contentY", rows.property("originY"))
        QMetaObject.invokeMethod(rows, "forceLayout")
        frame(window)
        group = model._root_groups[0]
        samples = {"collapse": [], "expand": []}
        created_cards = {"collapse": [], "expand": []}
        for _ in range(12):
            item = next(item for item in _visual_items(table)
                        if item.objectName() == "searchResultTableRow"
                        and item.property("nodeId") == group.node_id)
            point = item.mapToScene(QPointF(70, item.height() / 2)).toPoint()
            mode = "collapse" if group.expanded else "expand"
            old_cards = [item for item in _visual_items(table)
                         if item.objectName().startswith("tableTaskRecord_")]
            samples[mode].append(frame(window, lambda: QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier, point)))
            if group.expanded != (mode == "expand"):
                raise AssertionError("Group header click did not toggle its group")
            new_cards = [item for item in _visual_items(table)
                         if item.objectName().startswith("tableTaskRecord_")]
            created_cards[mode].append(sum(item not in old_cards for item in new_cards))
        group_clicks = {
            key: {"dispatchMedianMs": round(statistics.median(v[0] for v in values), 2),
                  "frameMedianMs": round(statistics.median(v[1] for v in values), 2),
                  "frameMaxMs": round(max(v[1] for v in values), 2),
                  "newCards": created_cards[key],
                  "frames": [round(max(v), 2) for v in values]}
            for key, values in samples.items()
        }
    scroll = []
    for index in range(24):
        def advance():
            rows.setProperty("contentY", (index + 1) * 100)
            QMetaObject.invokeMethod(rows, "forceLayout")
        scroll.append(frame(window, advance)[1])
    def refresh():
        columns._cell_revision += 1
        columns.cellRevisionChanged.emit()
    refresh_ms = [frame(window, refresh)[1] for _ in range(5)]
    state_ms = [frame(window, columns.stateChanged.emit)[1] for _ in range(5)]
    result = dict(counts, initialMs=round(initial_ms, 2),
                  workingSetDeltaMiB=round((memory_after - memory_before) / 2**20, 2)
                  if memory_before is not None else None,
                  scrollMedianMs=round(statistics.median(scroll), 2),
                  scrollMaxMs=round(max(scroll), 2),
                  refreshMedianMs=round(statistics.median(refresh_ms), 2),
                  stateMedianMs=round(statistics.median(state_ms), 2),
                  rowReads=columns.reads, previewRequests=len(controller.preview_requests))
    if grouped:
        result["groupClicks"] = group_clicks
    window.close()
    table.setParentItem(None)
    table.deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    engine.deleteLater()
    window.deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    if warnings:
        raise RuntimeError("\n".join(warnings))
    return result


if __name__ == "__main__":
    app = gui_test_application()
    with TemporaryDirectory(prefix="table-profile-") as directory, patch.object(
        env_mode, "current_path", directory,
    ):
        print(json.dumps({"projection": projection_benchmark(),
                          "frames": [benchmark(app) for _ in range(3)],
                          "grouped": benchmark(app, width=1800, height=1600, grouped=True)},
                         indent=2))
