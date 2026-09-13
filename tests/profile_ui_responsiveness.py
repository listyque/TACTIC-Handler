"""Offline, real-frame benchmark. Run: py -3.14 -m tests.profile_ui_responsiveness."""

import json
import statistics
import time
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

from tests.test_workspace_result_item import ROOT, _WorkspaceAppController
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode
from thlib.ui.workspace_models.records import RecordListModel


def review_hot_paths_benchmark():
    """Offline medians for the approved review; not production frame rates."""
    from datetime import date
    from thlib.ui.script_editor_features import _safe_tree
    from thlib.ui.task_data import gantt_layout

    source = "import json\n" + "x = 1\n" * 9 + "broken =\n" + "x = 2\n" * 3000
    same_user = [{
        "taskCode": str(index), "assigned": "artist",
        "start": "2026-09-01", "end": "2026-09-14",
    } for index in range(2000)]
    different_users = [dict(record, assigned=str(index))
                       for index, record in enumerate(same_user)]
    samples = {"scriptColdMs": [], "scriptCachedMs": [],
               "gantt2000SameUserMs": [], "gantt2000DifferentUsersMs": []}
    for _ in range(7):
        _safe_tree.cache_clear()
        for name, operation in (
                ("scriptColdMs", lambda: _safe_tree(source)),
                ("scriptCachedMs", lambda: _safe_tree(source)),
                ("gantt2000SameUserMs", lambda: gantt_layout(same_user, today=date(2026, 9, 1))),
                ("gantt2000DifferentUsersMs", lambda: gantt_layout(different_users, today=date(2026, 9, 1)))):
            started = time.perf_counter()
            operation()
            samples[name].append((time.perf_counter() - started) * 1000)
    _safe_tree.cache_clear()
    return {name: round(statistics.median(values), 4) for name, values in samples.items()}


def task_selection_benchmark():
    from thlib.environment import env_mode
    from thlib.ui.tasks import TasksController
    from tests.test_tasks_controller import FakeApplication, FakeTask

    with TemporaryDirectory(prefix="tactic-task-profile-") as directory, patch.object(
        env_mode, "current_path", directory,
    ):
        application = FakeApplication()
        application.workspace_state._task_sobjects = [
            FakeTask(code=f"TASK{i}") for i in range(300)
        ]
        controller = TasksController(application)
        controller.use_current_object()
        samples = {"fullProjectionRebuild": [], "selectionOnly": []}
        for iteration in range(14):
            started = time.perf_counter()
            controller._rebuild_advanced_models()
            rebuild_ms = (time.perf_counter() - started) * 1000
            started = time.perf_counter()
            controller.activate_advanced_task(f"TASK{iteration}", 0)
            selection_ms = (time.perf_counter() - started) * 1000
            if iteration >= 4:
                samples["fullProjectionRebuild"].append(rebuild_ms)
                samples["selectionOnly"].append(selection_ms)
        controller.shutdown()
        return {key + "MedianMs": round(statistics.median(values), 2)
                for key, values in samples.items()}


def task_group_frame_benchmark(app):
    """Measure the real task table frame, not only Python projection time."""
    from thlib.environment import env_mode
    from thlib.ui.tasks import TasksController
    from tests.test_tasks_controller import FakeApplication, FakeTask

    with TemporaryDirectory(prefix="tactic-task-groups-") as directory, \
            patch.object(env_mode, "current_path", directory):
        application = FakeApplication()
        application.workspace_state._task_sobjects = [
            FakeTask(
                code=f"TASK{i:05d}",
                process=("model", "rig", "publish", "texture")[i % 4],
                status=("Ready", "Pending", "In Progress")[i % 3],
                assigned=("artist", "reviewer", "")[i % 3],
            )
            for i in range(300)
        ]
        controller = TasksController(application)
        controller.use_current_object()
        engine = QQmlEngine()
        qml = ROOT / "thlib/ui/qml"
        engine.addImportPath(str(qml))
        engine.rootContext().setContextProperty(
            "tasksController", controller
        )
        engine.rootContext().setContextProperty(
            "advancedTaskModel", controller.advanced_model
        )
        engine.rootContext().setContextProperty(
            "advancedTaskTableModel", controller.table_model
        )
        engine.rootContext().setContextProperty(
            "userListModel",
            RecordListModel((
                "login", "displayName", "initials", "avatarUrl",
            )),
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml / "TaskBrowserTable.qml"))
        )
        table = component.createWithInitialProperties({"theme": theme})
        if table is None:
            raise RuntimeError([
                error.toString() for error in component.errors()
            ])
        window = QQuickWindow()
        window.resize(1400, 900)
        table.setParentItem(window.contentItem())
        table.setProperty("width", 1400)
        table.setProperty("height", 900)
        window.show()
        app.processEvents()
        frame(window)

        samples = {"collapse": [], "regroup": []}
        for iteration in range(10):
            dispatch, elapsed = frame(
                window,
                lambda: controller.toggle_group_collapsed("model"),
            )
            if iteration >= 2:
                samples["collapse"].append((dispatch, elapsed))
        modes = ("status", "process") * 5
        for iteration, mode in enumerate(modes):
            dispatch, elapsed = frame(
                window,
                lambda value=mode: controller.set_group_mode(value),
            )
            if iteration >= 2:
                samples["regroup"].append((dispatch, elapsed))

        result = {
            key + "DispatchMedianMs": round(
                statistics.median(row[0] for row in values), 2
            )
            for key, values in samples.items()
        }
        result.update({
            key + "FrameMedianMs": round(
                statistics.median(row[1] for row in values), 2
            )
            for key, values in samples.items()
        })
        window.close()
        table.setParentItem(None)
        table.deleteLater()
        theme.deleteLater()
        controller.shutdown()
        app.processEvents()
        return result


def frame(window, action=lambda: None):
    loop = QEventLoop()
    guard = QTimer()
    guard.setSingleShot(True)
    guard.timeout.connect(loop.quit)
    elapsed = []
    started = time.perf_counter()

    def presented():
        elapsed.append((time.perf_counter() - started) * 1000)
        loop.quit()

    window.frameSwapped.connect(presented)
    action()
    dispatch = (time.perf_counter() - started) * 1000
    window.update()
    guard.start(3000)
    loop.exec()
    guard.stop()
    window.frameSwapped.disconnect(presented)
    if not elapsed:
        raise RuntimeError("No rendered benchmark frame")
    return dispatch, elapsed[0]


def main():
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlEngine()
    controller = _WorkspaceAppController()
    engine.rootContext().setContextProperty("appController", controller)
    qml = ROOT / "thlib/ui/qml"
    theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / "Theme.qml")))
    theme = theme_component.createWithInitialProperties({"dark": True})
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / "SearchResultSurface.qml")))
    window = QQuickWindow()
    window.resize(1100, 1440)
    window.show()
    surfaces, models = [], []
    for label, controls in (("assets", 0), ("episodes", 6)):
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(
            node_id=f"{label}:{row}", node_type="sobject", search_key="",
            code=str(row), title=f"{label} {row}", preview_requested=True,
            controls_cache=[{
                "command": f"action_{i}", "icon": "description", "persistent": True,
                "tip": "Script", "success": False,
            } for i in range(controls)],
        ) for row in range(100)])
        # The benchmark has no server objects: supply the configured controls
        # at the native presentation boundary, not by performing server calls.
        model._controls_for = lambda node: node.controls_cache
        surface = component.createWithInitialProperties({
            "theme": theme, "controller": controller, "resultModel": model,
            "current": False, "viewMode": "continious", "splitterRatio": .58,
            "width": 1100, "height": 1440, "presentationActive": True,
        })
        if surface is None:
            raise RuntimeError([error.toString() for error in component.errors()])
        surface.setParentItem(window.contentItem())
        surfaces.append(surface)
        models.append(model)
    samples = {"assets": [], "episodes": []}
    for iteration in range(14):
        index = iteration % 2

        def switch():
            surfaces[1 - index].setProperty("current", False)
            surfaces[index].setProperty("current", True)

        dispatch, elapsed = frame(window, switch)
        if iteration >= 4:
            samples[("assets", "episodes")[index]].append((dispatch, elapsed))
    report = {key: {
        "dispatchMedianMs": round(statistics.median(row[0] for row in rows), 2),
        "frameMedianMs": round(statistics.median(row[1] for row in rows), 2),
        "frameMaxMs": round(max(row[1] for row in rows), 2),
    } for key, rows in samples.items()}
    scroll_samples = {"assets": [], "episodes": []}
    for index, label in enumerate(("assets", "episodes")):
        surfaces[1 - index].setProperty("current", False)
        surfaces[index].setProperty("current", True)
        frame(window)
        view = surfaces[index].findChild(QObject, "searchResultsListView")
        if view is None:
            raise RuntimeError("Search result ListView is unavailable")
        view.setProperty("contentY", 0.0)
        frame(window)
        for _iteration in range(10):
            _dispatch, elapsed = frame(
                window,
                lambda target=view: target.setProperty(
                    "contentY", float(target.property("contentY")) + 148.0
                ),
            )
            scroll_samples[label].append(elapsed)
    for label, values in scroll_samples.items():
        report[label]["scrollFrameMedianMs"] = round(
            statistics.median(values), 2
        )
        report[label]["scrollFrameMaxMs"] = round(max(values), 2)
    report["tasks300Controller"] = task_selection_benchmark()
    report["reviewHotPaths"] = review_hot_paths_benchmark()
    report["tasks300Table"] = task_group_frame_benchmark(app)
    print(json.dumps(report, indent=2))
    window.close()
    for surface in surfaces:
        surface.setParentItem(None)
        surface.deleteLater()
    app.processEvents()


if __name__ == "__main__":
    main()
