"""Offline real-QML table benchmark: python -m tests.profile_result_table.

No server or production configuration. Timings are diagnostics, not CI limits.
"""

import json
import ctypes
import os
import statistics
import sys
import time
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from tests.test_columns_table_view import (
    QML, _TableColumns, _TableController, _visual_items,
    gui_test_application, _Application, _SType,
)
from tests.profile_ui_responsiveness import frame
from PySide6.QtCore import QEvent, QMetaObject, QObject, QPointF, Qt, QUrl, Slot, Property, Signal
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from thlib.environment import env_mode
from thlib.ui.columns_editor import ColumnsEditorController
from thlib.ui.controllers.result_tree import ResultTreeMixin
from thlib.tactic_table_widgets import TacticTaskTableWidget
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


def render_phase(name):
    if os.environ.get("TH_TABLE_RENDER_TIMING") == "1":
        print(f"TABLE_RENDER_PHASE {name}", file=sys.stderr, flush=True)


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


class SurfaceTableController(GroupedTableController):
    viewModeChanged = Signal()

    def __init__(self, model):
        super().__init__(model)
        self.mode = "table"

    @Property(str, notify=viewModeChanged)
    def results_view_mode(self):
        return self.mode

    @Property(float, constant=True)
    def results_splitter_ratio(self):
        return .58

    @Property(bool, constant=True)
    def card_can_go_back(self):
        return False

    @Property(bool, constant=True)
    def card_compact_level(self):
        return False

    @Property(bool, constant=True)
    def description_limit_enabled(self):
        return False

    @Property(int, constant=True)
    def description_limit(self):
        return 200

    @Property(str, constant=True)
    def selected_dcc_application(self):
        return "standalone"

    @Slot(str, result=str)
    def get_acronym(self, value):
        return value[:2].upper()

    @Slot(str, result="QVariantList")
    def item_quick_actions(self, node_id):
        return []

    @Slot(str)
    def request_item_card_preview(self, node_id):
        pass


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


def benchmark(app, width=1600, height=900, grouped=False, surface=False, restore_y=None):
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
    controller = SurfaceTableController(model) if surface else GroupedTableController(model)
    engine.rootContext().setContextProperty("appController", controller)
    if grouped:
        model.set_organization(group_mode="column:category")
        model.show_table_rows()
    users = RecordListModel(("login", "displayName", "initials", "avatarUrl"))
    filename = "SearchResultSurface.qml" if surface else "SearchResultTable.qml"
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / filename)))
    window = QQuickWindow()
    window.resize(width, height)
    window.show()
    frame(window)
    memory_before = working_set_bytes()
    render_phase("initial")
    started = time.perf_counter()
    properties = {
        "theme": theme, "controller": controller, "columnsController": columns,
        "resultModel": model, "userModel": users, "presentationActive": True,
        "width": width, "height": height,
    }
    properties.update({"current": False, "viewMode": "table", "splitterRatio": .58}
                      if surface else {"rowHeight": 100})
    table = component.createWithInitialProperties(properties)
    if table is None:
        raise RuntimeError([error.toString() for error in component.errors()])
    table.setParentItem(window.contentItem())
    if surface:
        hidden_create_ms = (time.perf_counter() - started) * 1000
        hidden_rows = [table.findChild(QQuickItem, name).property("count") for name in (
            "searchResultsListView", "searchResultsGridView", "searchResultsTableView")]
        if restore_y is not None:
            restore = QQmlExpression(QQmlEngine.contextForObject(table), table,
                                     f"restoreContentY({float(restore_y)}, 0, true, false)")
            restore.evaluate()
            if restore.hasError():
                raise RuntimeError(restore.error().toString())
        table.setProperty("current", True)
    rows = table.findChild(QQuickItem, "searchResultsTableView")
    presentation = table.findChild(QObject, "initialTablePresentation")
    for _ in range(10):
        frame(window)
        if presentation.property("ready"):
            break
    else:
        raise RuntimeError("Table never presented")
    initial_ms = (time.perf_counter() - started) * 1000
    render_phase("settle")
    for _ in range(12 if os.environ.get("TH_TABLE_RENDER_TIMING") == "1" else 3):
        frame(window)
    memory_after = working_set_bytes()
    items = _visual_items(window.contentItem())
    task_cells = [item for item in items if item.objectName() == "tableTaskCell"]
    counts = {"graphicsApi": window.rendererInterface().graphicsApi().name,
              "dateDisplays": sum(item.objectName().startswith("tableTaskDatesContent_")
                                  for item in items),
              "visualItems": len(items), "rowDelegates": sum(
        item.objectName() == "searchResultTableRow" for item in items),
        "dateEditors": sum(len(item.findChildren(QObject, "tableTaskDateEditor"))
                           for item in task_cells),
        "taskCards": sum(item.objectName().startswith("tableTaskRecord_")
                         for item in items)}
    if surface:
        alternatives = [table.findChild(QQuickItem, name) for name in (
            "searchResultsListView", "searchResultsGridView")]
        counts["restoredContentY"] = rows.property("contentY")
        counts["hiddenCreateMs"] = round(hidden_create_ms, 2)
        counts["hiddenViewRows"] = hidden_rows
        counts["unopenedViewRows"] = [view.property("count") for view in alternatives]
        counts["unopenedViewItems"] = [len(_visual_items(view)) for view in alternatives]
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
    render_phase("scroll")
    scroll = []
    for index in range(24):
        def advance():
            rows.setProperty("contentY", (index + 1) * 100)
            QMetaObject.invokeMethod(rows, "forceLayout")
        scroll.append(frame(window, advance)[1])
    def refresh():
        columns._cell_revision += 1
        columns.cellRevisionChanged.emit()
    samples = 24 if os.environ.get("TH_TABLE_RENDER_TIMING") == "1" else 5
    render_phase("refresh")
    refresh_ms = [frame(window, refresh)[1] for _ in range(samples)]
    render_phase("state")
    state_ms = [frame(window, columns.stateChanged.emit)[1] for _ in range(samples)]
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
    if surface:
        render_phase("modes")
        retained = []
        for mode, view in (("continious", alternatives[0]), ("tiles", alternatives[1]), ("table", rows)):
            controller.mode = mode
            controller.viewModeChanged.emit()
            for _ in range(3):
                frame(window)
            content = view.property("contentItem")
            before_hide = {item for item in content.childItems()
                           if item.property("nodeId") is not None
                           and item.y() + item.height() > view.property("contentY")
                           and item.y() < view.property("contentY") + view.height()}
            old_y = view.property("contentY")
            table.setProperty("current", False)
            frame(window)
            hidden_model = view.property("model")
            table.setProperty("current", True)
            for _ in range(3):
                frame(window)
            if hasattr(hidden_model, "toQObject"):
                hidden_model = hidden_model.toQObject()
            retained.append({"model": hidden_model is model,
                             "delegates": before_hide <= {item for item in content.childItems()
                                                         if item.property("nodeId") is not None},
                             "scroll": abs(old_y - view.property("contentY")) < .5})
        result["retainedViews"] = retained
    render_phase("done")
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
                          "surface": [benchmark(app, surface=True) for _ in range(3)],
                          "grouped": benchmark(app, width=1800, height=1600, grouped=True)},
                         indent=2))
