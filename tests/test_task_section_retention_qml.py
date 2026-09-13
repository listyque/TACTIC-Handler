"""Runtime coverage for a retained Tasks dock across Search Type sections."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Slot, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy

from tests.profile_ui_responsiveness import frame
from tests.test_tasks_controller import FakeTarget, FakeTask
from thlib.environment import env_mode
from thlib.ui.controller import ApplicationController
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.tasks import TasksController
from thlib.ui.workspace_models.docks import DockPanelModel
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class _MilestoneController(QObject):
    @Slot()
    def open_manager(self) -> None:
        pass


class TaskSectionRetentionQmlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        temporary = TemporaryDirectory(prefix="tactic-task-retention-")
        self.addCleanup(temporary.cleanup)
        redirect = patch.object(env_mode, "current_path", temporary.name)
        redirect.start()
        self.addCleanup(redirect.stop)

        self.engine = QQmlEngine()
        self.components: list[QQmlComponent] = []
        self.warnings: list[str] = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(
                error.toString() for error in errors
            )
        )
        self.application = ApplicationController()
        self.tasks = TasksController(self.application)
        self.tasks._workspace_surface = "browser"
        self.tasks._group_mode = "none"
        self.tasks.refresh_advanced = Mock()
        self.addCleanup(self.tasks.shutdown)
        self.addCleanup(self.application.shutdown)

        self.application.dock_model.panelPresentationChanged.connect(
            self.tasks.sync_presentation
        )

        self.users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ), [{
            "login": "artist",
            "displayName": "Artist",
            "initials": "AR",
            "avatarUrl": "",
        }])
        self.milestones = _MilestoneController()
        bindings = {
            "appController": self.application,
            "dockModel": self.application.dock_model,
            "visibleDockModel": self.application.visible_dock_model,
            "windowModel": self.application.window_model,
            "tasksController": self.tasks,
            "advancedTaskModel": self.tasks.advanced_model,
            "advancedTaskTableModel": self.tasks.table_model,
            "taskGanttModel": self.tasks.gantt_model,
            "userListModel": self.users,
            "milestoneController": self.milestones,
        }
        for name, value in bindings.items():
            self.engine.rootContext().setContextProperty(name, value)

        theme_component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        self.components.append(theme_component)
        self.theme = theme_component.createWithInitialProperties({
            "dark": True,
        })
        self.assertIsNotNone(
            self.theme,
            [error.toString() for error in theme_component.errors()],
        )

    @staticmethod
    def _section(
        key: str,
        target: FakeTarget,
        task: FakeTask,
        layout: dict,
    ) -> SectionSession:
        node_id = f"sobject:{key}"
        node = WorkspaceNode(
            node_id=node_id,
            node_type="sobject",
            search_key=target.get_search_key(),
            code=target.get_code(),
            title=target.get_title(),
            source=target,
        )
        tab = SearchTabSession(
            tab_id=key,
            title=target.get_title(),
            loaded=True,
            workspace_layout=layout,
            sobjects=[target],
            workspace_roots=[node],
            selected_node_id=node_id,
            selected_node_ids=[node_id],
            details_node_id=node_id,
            details_payload=(target, [task], [], []),
        )
        return SectionSession(
            entry_key=key,
            title=target.get_title(),
            accent="#78909c",
            search_type="prod/asset",
            sidebar_presets_initialized=True,
            tabs=[tab],
            current_tab_id=tab.tab_id,
        )

    @staticmethod
    def _find_item(parent: QQuickItem, object_name: str):
        if parent.objectName() == object_name:
            return parent
        for child in parent.childItems():
            found = TaskSectionRetentionQmlTests._find_item(
                child, object_name
            )
            if found is not None:
                return found
        return None

    @staticmethod
    def _list_delegate(task_list: QQuickItem, descendant: QQuickItem):
        content_item = task_list.property("contentItem")
        candidate = descendant
        while (
            candidate is not None
            and candidate.parentItem() is not content_item
        ):
            candidate = candidate.parentItem()
        return candidate

    def _show_task_dock(self):
        component = QQmlComponent(self.engine)
        self.components.append(component)
        component.setData(b'''import QtQuick
import "." as App
Item {
    id: harness
    required property var theme
    property bool dockResizeActive: false
    property bool windowResizeActive: false
    function beginDockDrag(panelId) {}
    function updateDockDrag(panelId, pointerX, pointerY) {}
    function finishDockDrag(panelId, x, y, width, height) {}
    function beginDockResize() { dockResizeActive = true }
    function endDockResize() { dockResizeActive = false }

    Component {
        id: emptyContent
        Item {}
    }
    Component {
        id: taskContent
        App.TaskDockView { theme: harness.theme }
    }
    Repeater {
        model: visibleDockModel
        delegate: Item {
            required property string panelId
            required property string title
            required property string kind
            required property real panelX
            required property real panelY
            required property real panelWidth
            required property real panelHeight
            required property bool panelVisible
            required property bool closable
            required property int stackOrder
            required property string dockArea
            required property bool canResizeLeft
            required property bool canResizeRight
            required property bool canResizeTop
            required property bool canResizeBottom
            required property bool detached
            required property bool stackActive
            required property var stackPanels
            required property int stackSize
            width: harness.width
            height: harness.height

            App.DockPanel {
                objectName: "retainedTaskPanel_" + parent.panelId
                host: harness
                theme: harness.theme
                panelId: parent.panelId
                title: parent.title
                kind: parent.kind
                panelX: parent.panelX
                panelY: parent.panelY
                panelWidth: parent.panelWidth
                panelHeight: parent.panelHeight
                modelVisible: parent.panelVisible
                    && parent.stackActive && !parent.detached
                panelOpen: parent.panelVisible
                    && parent.stackActive && !parent.detached
                stackActive: parent.stackActive
                closable: parent.closable
                stackOrder: parent.stackOrder
                dockArea: parent.dockArea
                canResizeLeft: parent.canResizeLeft
                canResizeRight: parent.canResizeRight
                canResizeTop: parent.canResizeTop
                canResizeBottom: parent.canResizeBottom
                stackPanels: parent.stackPanels
                stackSize: parent.stackSize
                contentComponent: parent.panelId === "tasks"
                    ? taskContent : emptyContent
            }
        }
    }
}''', QUrl.fromLocalFile(str(QML / "TaskSectionRetentionHarness.qml")))
        self.assertNotEqual(
            component.status(), QQmlComponent.Status.Error,
            "\n".join(error.toString() for error in component.errors()),
        )
        view = component.createWithInitialProperties({"theme": self.theme})
        self.assertIsNotNone(
            view, "\n".join(error.toString() for error in component.errors())
        )
        window = QQuickWindow()
        window.resize(1400, 760)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        frame(window)

        def dispose():
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        self.addCleanup(dispose)
        return window, view

    def test_hidden_section_keeps_loaded_task_model_and_delegate(self):
        visible_layout = self.application.dock_model.capture_layout()
        hidden_model = DockPanelModel({})
        self.assertTrue(hidden_model.apply_layout(visible_layout))
        hidden_model.close_panel("tasks")
        hidden_model.close_panel("task_calendar")
        hidden_layout = hidden_model.capture_layout()

        task_b = FakeTask(code="TASK_B", search_code="ASSET_B")
        target_b = FakeTarget([task_b], code="ASSET_B", title="Asset B")
        task_a = FakeTask(code="TASK_A", search_code="ASSET_A")
        target_a = FakeTarget([task_a], code="ASSET_A", title="Asset A")
        section_b = self._section("section-b", target_b, task_b, visible_layout)
        section_a = self._section("section-a", target_a, task_a, hidden_layout)
        self.application._sessions = {
            section_b.entry_key: section_b,
            section_a.entry_key: section_a,
        }

        self.application.activate_section(section_b.entry_key)
        self.tasks.sync_presentation()
        self.assertEqual(self.tasks.table_model.count(), 1)
        self.assertEqual(
            self.tasks.table_model.get(0)["taskCode"], "TASK_B"
        )
        self.assertTrue(self.tasks._advanced_visible)
        self.tasks.refresh_advanced.assert_not_called()

        window, view = self._show_task_dock()
        task_list = None
        task_surface = None
        for _attempt in range(24):
            task_list = self._find_item(view, "taskBrowserList")
            task_surface = self._find_item(
                view, "taskRowSurface_TASK_B"
            )
            if task_list is not None and task_surface is not None:
                break
            frame(window)
        self.assertIsNotNone(task_list, self.warnings)
        self.assertIsNotNone(task_surface, self.warnings)
        self.assertEqual(task_list.property("count"), 1)
        self.assertGreater(task_list.property("liveDelegateCount"), 0)
        task_delegate = self._list_delegate(task_list, task_surface)
        self.assertIsNotNone(task_delegate)
        original_live_delegates = task_list.property("liveDelegateCount")

        model_spies = {
            f"{model_name}.{signal_name}": QSignalSpy(signal)
            for model_name, model in (
                ("advanced", self.tasks.advanced_model),
                ("table", self.tasks.table_model),
            )
            for signal_name, signal in (
                ("modelReset", model.modelReset),
                ("rowsInserted", model.rowsInserted),
                ("rowsRemoved", model.rowsRemoved),
                ("dataChanged", model.dataChanged),
                ("contentReplaced", model.contentReplaced),
            )
        }
        baseline_server_queries = self.tasks.performanceMetrics[
            "serverQueries"
        ]

        self.application.activate_section(section_a.entry_key)
        frame(window)
        self.assertFalse(
            self.application.dock_model.is_panel_presented("tasks")
        )
        self.assertFalse(self.tasks._advanced_visible)
        self.assertIs(
            self._find_item(view, "taskBrowserList"), task_list
        )
        self.assertIs(
            self._find_item(view, "taskRowSurface_TASK_B"), task_surface
        )
        self.assertIs(
            self._list_delegate(task_list, task_surface), task_delegate
        )

        self.application.activate_section(section_b.entry_key)
        frame(window)
        self.assertTrue(
            self.application.dock_model.is_panel_presented("tasks")
        )
        self.assertTrue(self.tasks._advanced_visible)
        self.assertIs(
            self._find_item(view, "taskBrowserList"), task_list
        )
        self.assertIs(
            self._find_item(view, "taskRowSurface_TASK_B"), task_surface
        )
        self.assertIs(
            self._list_delegate(task_list, task_surface), task_delegate
        )
        self.assertEqual(
            {name: spy.count() for name, spy in model_spies.items()},
            {name: 0 for name in model_spies},
        )
        self.assertEqual(
            task_list.property("liveDelegateCount"), original_live_delegates
        )
        self.assertEqual(self.tasks.table_model.count(), 1)
        self.assertEqual(
            self.tasks.table_model.get(0)["taskCode"], "TASK_B"
        )
        self.tasks.refresh_advanced.assert_not_called()
        self.assertEqual(
            self.tasks.performanceMetrics["serverQueries"],
            baseline_server_queries,
        )
        self.assertEqual(self.warnings, [])
