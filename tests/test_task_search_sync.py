"""Task dock lifecycle and active Search selection integration regressions."""

import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import (
    QCoreApplication, QEvent, QEventLoop, QObject, QPointF, Qt, QTimer, QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.environment import env_mode
from thlib.ui.application_composition import _wire_presentation_lifecycle
from thlib.ui.controller import ApplicationController
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.tasks import TasksController
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.results_types import WorkspaceNode
from tests.test_tasks_controller import FakeStype, FakeTarget, FakeTask


QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class TaskSearchSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, "current_path", directory))
        self.application = ApplicationController()
        self.addCleanup(self.application.shutdown)
        self.application._current_project_code = "test"
        self.application.dock_model.close_panel("notes")
        self.application.dock_model.close_panel("task_calendar")
        self.application.repository_sync.request_presets = Mock()
        self.application._save_search_cache = Mock()
        # Detail requests are delivered explicitly; no live TACTIC dependency.
        self.application._selection_load_timer.stop()
        self.application._selection_load_timer.timeout.disconnect()
        self.first = FakeTarget(code="ASSET0001", title="Robot")
        self.second = FakeTarget(code="ASSET0002", title="Chair")
        self.tab = SearchTabSession(
            tab_id="assets", title="In Progress", stype=FakeStype(),
            loaded=True,
        )
        self.section = SectionSession(
            entry_key="assets-in-progress", title="In Progress",
            search_type="prod/asset", accent="#ff5353", tabs=[self.tab],
            current_tab_id=self.tab.tab_id,
        )
        self.application._sessions[self.section.entry_key] = self.section
        self.application._current_section_key = self.section.entry_key
        self.nodes = [WorkspaceNode(
            node_id=target.code, node_type="sobject", source=target,
            search_key=target.get_search_key(), code=target.code,
            title=target.title, preview_requested=True,
            card_preview_requested=True,
        ) for target in (self.first, self.second)]
        self.application.workspace_model.replace_nodes(self.nodes)
        self.tab.selected_node_id = self.nodes[0].node_id
        self.tab.selected_node_ids = [self.tab.selected_node_id]
        self.deliver_details(self.first)
        self.tasks = TasksController(self.application)
        self.addCleanup(self.tasks.shutdown)
        self.tasks._ensure_task_field_catalog = Mock()
        self.tasks.refresh_advanced = Mock()
        _wire_presentation_lifecycle(
            SimpleNamespace(controller=self.application, debug_log=Mock()),
            SimpleNamespace(tasks=self.tasks), Mock(), Mock(),
        )

    def deliver_details(self, target):
        workspace = self.application.workspace_state
        workspace._selected_sobject = target
        workspace._task_sobjects = [FakeTask(
            code="TASK_" + target.code, search_code=target.code,
        )]
        workspace.selection_changed.emit()

    def select(self, index, modifiers=0):
        node = self.nodes[index]
        self.application.select_result_node(
            node.node_id, node.search_key, node.node_type, modifiers,
        )
        self.application._selection_load_timer.stop()

    def test_browser_dock_activates_selection_sync_without_old_window(self):
        self.tasks.open_workspace()
        self.assertTrue(self.tasks._advanced_visible)
        self.assertFalse(self.tasks._compact_visible)
        self.select(1)
        self.deliver_details(self.second)
        self.assertEqual(
            self.tasks._advanced_target_key, self.second.get_search_key(),
        )
        self.assertEqual(
            self.tasks.advanced_model.get(0)["taskCode"], "TASK_ASSET0002",
        )

    def test_surface_switch_updates_visibility_while_dock_stays_shown(self):
        self.tasks.open_quick_workspace()
        self.assertTrue(self.tasks._compact_visible)
        self.tasks.open_workspace()
        self.assertTrue(self.tasks._advanced_visible)
        self.assertFalse(self.tasks._compact_visible)
        self.tasks.open_quick_workspace()
        self.assertTrue(self.tasks._compact_visible)
        self.assertFalse(self.tasks._advanced_visible)

    def test_select_all_updates_scope_without_new_detail_payload(self):
        self.tasks.open_workspace()
        self.tasks.refresh_advanced.reset_mock()
        self.application.select_all_result_siblings()
        self.assertEqual(self.tasks.advancedScope, "multiple")
        self.assertCountEqual(self.tasks._multiple_targets, [self.first, self.second])
        self.tasks.refresh_advanced.assert_called_once_with()
        self.application.section_state_changed.emit()
        self.deliver_details(self.first)
        self.tasks.refresh_advanced.assert_called_once_with()

    def test_ctrl_deselection_uses_remaining_object_not_last_clicked_row(self):
        self.tasks.open_workspace()
        self.application.select_all_result_siblings()
        self.tasks.refresh_advanced.reset_mock()
        self.select(0, Qt.ControlModifier.value)
        self.assertEqual(self.tab.selected_node_ids, [self.second.code])
        self.assertEqual(self.tasks.advancedScope, "object")
        self.assertEqual(
            self.tasks._advanced_target_key, self.second.get_search_key(),
        )
        self.tasks.refresh_advanced.assert_called_once_with()
        self.deliver_details(self.first)
        self.assertEqual(
            self.tasks._advanced_target_key, self.second.get_search_key(),
        )
        self.tasks.refresh_advanced.assert_called_once_with()

    def test_empty_active_tab_provides_native_type_not_previous_object(self):
        stype = FakeStype()
        stype.get_code = lambda: "prod/episode"
        stype.get_pretty_name = lambda: "Episodes from server"
        self.tab.stype = stype
        self.tab.selected_node_id = ""
        self.tab.selected_node_ids = []
        self.application.workspace_model.replace_nodes([])
        self.application.section_state_changed.emit()
        self.assertTrue(self.tasks.searchTypeScopeAvailable)
        self.assertEqual(self.tasks.searchTypeScopeName, "Episodes from server")
        self.tasks.use_current_search_type()
        self.assertEqual(self.tasks._advanced_target_key, "prod/episode")

    def test_hidden_browser_defers_models_and_resumes_latest_selection(self):
        self.tasks.open_workspace()
        self.tasks.open_quick_workspace()
        with patch.object(self.tasks, "_rebuild_advanced_models") as rebuild:
            self.select(1)
            self.deliver_details(self.second)
            rebuild.assert_not_called()
        self.tasks.open_workspace()
        self.assertEqual(
            self.tasks._advanced_target_key, self.second.get_search_key(),
        )

    def test_equal_retained_object_details_do_not_rebuild_task_projections(self):
        self.tasks.open_workspace()
        before = self.tasks.performanceMetrics["projectionRebuilds"]

        with patch.object(
            self.tasks, "_rebuild_advanced_models",
            wraps=self.tasks._rebuild_advanced_models,
        ) as rebuild:
            self.application.workspace_state.selection_changed.emit()

        rebuild.assert_not_called()
        self.assertEqual(
            self.tasks.performanceMetrics["projectionRebuilds"], before,
        )
        self.assertEqual(
            self.tasks.advanced_model.get(0)["taskCode"], "TASK_ASSET0001",
        )

    def test_visible_section_switch_publishes_only_target_tasks_once(self):
        self.tasks.open_workspace()
        visible_layout = self.application.dock_model.capture_layout()
        self.tab.workspace_layout = visible_layout
        self.section.sidebar_presets_initialized = True
        target_tab = SearchTabSession(
            tab_id="shots", title="Shots", stype=FakeStype(), loaded=True,
            workspace_layout=visible_layout,
        )
        target_section = SectionSession(
            entry_key="shots-in-progress", title="Shots",
            search_type="prod/shot", accent="#4f6bed",
            tabs=[target_tab], current_tab_id=target_tab.tab_id,
            sidebar_presets_initialized=True,
        )
        self.application._sessions[target_section.entry_key] = target_section
        self.tasks.refresh_advanced.reset_mock()
        published_tasks = []
        self.tasks.advanced_model.contentReplaced.connect(
            lambda: published_tasks.append(
                self.tasks.advanced_model.get(0).get("taskCode")
            )
        )

        def show_target(section_key, _tab_id):
            target = (
                self.second
                if section_key == target_section.entry_key
                else self.first
            )
            self.deliver_details(target)

        with (
            patch.object(
                self.application,
                "_show_tab_if_current",
                side_effect=show_target,
            ),
            patch.object(
                self.tasks,
                "_rebuild_advanced_models",
                wraps=self.tasks._rebuild_advanced_models,
            ) as rebuild,
        ):
            self.application.activate_section(target_section.entry_key)

        rebuild.assert_called_once_with()
        self.assertEqual(published_tasks, ["TASK_ASSET0002"])
        self.assertEqual(
            self.tasks.advanced_model.get(0)["taskCode"],
            "TASK_ASSET0002",
        )
        self.tasks.refresh_advanced.assert_not_called()

    def test_closing_section_prehides_hidden_incoming_task_projection(self):
        self.tasks.open_workspace()
        visible_layout = self.application.dock_model.capture_layout()
        self.tab.workspace_layout = visible_layout
        self.section.sidebar_presets_initialized = True
        hidden_docks = type(self.application.dock_model)({})
        self.assertTrue(hidden_docks.apply_layout(visible_layout))
        hidden_docks.close_panel("tasks")
        hidden_docks.close_panel("task_calendar")
        hidden_layout = hidden_docks.capture_layout()
        target_tab = SearchTabSession(
            tab_id="shots", title="Shots", stype=FakeStype(), loaded=True,
            workspace_layout=hidden_layout,
        )
        target_section = SectionSession(
            entry_key="shots-in-progress", title="Shots",
            search_type="prod/shot", accent="#4f6bed",
            tabs=[target_tab], current_tab_id=target_tab.tab_id,
            sidebar_presets_initialized=True,
        )
        self.application._sessions[target_section.entry_key] = target_section
        self.tasks.refresh_advanced.reset_mock()
        publications = []
        self.tasks.advanced_model.contentReplaced.connect(
            lambda: publications.append(True)
        )

        with (
            patch.object(
                self.application,
                "_show_tab_if_current",
                side_effect=lambda _section_key, _tab_id: (
                    self.deliver_details(self.second)
                ),
            ),
            patch.object(
                self.tasks,
                "_rebuild_advanced_models",
                wraps=self.tasks._rebuild_advanced_models,
            ) as rebuild,
        ):
            self.application.close_section(self.section.entry_key)

        self.assertEqual(
            self.application._current_section_key,
            target_section.entry_key,
        )
        self.assertFalse(
            self.application.dock_model.is_panel_presented("tasks")
        )
        self.assertFalse(self.tasks._advanced_visible)
        self.assertEqual(
            self.tasks.advanced_model.get(0)["taskCode"],
            "TASK_ASSET0001",
        )
        self.assertEqual(publications, [])
        rebuild.assert_not_called()
        self.tasks.refresh_advanced.assert_not_called()

    def test_task_models_reconcile_rows_by_stable_domain_identity(self):
        self.assertEqual(self.tasks.process_model._identity_role, "process")
        self.assertEqual(self.tasks.advanced_model._identity_role, "taskCode")

    def test_chosen_independent_scopes_do_not_follow_selection(self):
        self.tasks.open_workspace()
        for scope in ("project", "user", "team", "search_type"):
            with self.subTest(scope=scope):
                self.tasks.task_store.set_scope(scope, target_key="prod/asset")
                self.tasks.refresh_advanced.reset_mock()
                self.select(1)
                self.deliver_details(self.second)
                self.assertEqual(self.tasks.advancedScope, scope)
                self.assertEqual(self.tasks._advanced_target_key, "prod/asset")
                self.tasks.refresh_advanced.assert_not_called()

    def test_selection_does_not_discard_task_drafts(self):
        self.tasks.open_workspace()
        self.tasks._advanced_drafts = {"TASK_ASSET0001": {"description": "Draft"}}
        self.select(1)
        self.deliver_details(self.second)
        self.assertEqual(
            self.tasks._advanced_target_key, self.first.get_search_key(),
        )
        self.assertEqual(
            self.tasks._advanced_drafts,
            {"TASK_ASSET0001": {"description": "Draft"}},
        )
        self.assertIn("Save or discard", self.tasks.advancedError)

    def test_detached_dock_and_calendar_keep_task_presentation_active(self):
        docks = self.application.dock_model
        self.tasks.open_workspace()
        docks.detach_panel("tasks")
        self.assertTrue(self.tasks._advanced_visible)
        docks.close_detached_panel("tasks")
        self.assertFalse(self.tasks._advanced_visible)
        self.select(1)
        self.deliver_details(self.second)
        self.tasks.open_calendar()
        self.assertTrue(self.tasks._advanced_visible)
        self.assertEqual(
            self.tasks._advanced_target_key, self.second.get_search_key(),
        )
        docks.close_panel("task_calendar")
        self.assertFalse(self.tasks._advanced_visible)

    def test_pending_details_do_not_attach_previous_objects_tasks(self):
        self.tasks.open_workspace()
        with patch.object(self.tasks, "_rebuild_advanced_models") as rebuild:
            self.select(1)
            rebuild.assert_not_called()
            self.tasks.refresh_advanced.assert_not_called()
        self.deliver_details(self.second)
        self.assertEqual(
            self.tasks.advanced_model.get(0)["taskCode"], "TASK_ASSET0002",
        )

    def test_visible_inspector_keeps_its_shared_process_editor_current(self):
        self.tasks.open_workspace()
        self.application.dock_model.show_panel("notes")
        self.select(1)
        self.deliver_details(self.second)
        self.assertEqual(
            self.tasks.task_inspector_record("TASK_ASSET0002")["process"],
            "model",
        )
        self.application.dock_model.close_panel("notes")
        self.assertFalse(self.tasks._compact_visible)

    def wait_frame(self, window, predicate=lambda: True):
        loop = QEventLoop()
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)

        def presented():
            if predicate():
                loop.quit()
            else:
                window.update()

        window.frameSwapped.connect(presented)
        window.update()
        timeout.start(2000)
        loop.exec()
        timeout.stop()
        window.frameSwapped.disconnect(presented)
        self.assertTrue(predicate(), "Expected QML state was not reached")

    @contextmanager
    def scene(self, width):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        users = RecordListModel(("login", "displayName", "initials", "avatarUrl"))
        bindings = {
            "appController": self.application,
            "tasksController": self.tasks,
            "advancedTaskModel": self.tasks.advanced_model,
            "advancedTaskTableModel": self.tasks.table_model,
            "taskGanttModel": self.tasks.gantt_model,
            "taskCalendarModel": self.tasks.calendar_model,
            "taskProcessModel": self.tasks.process_model,
            "userListModel": users,
            "searchModel": self.application.workspace_model,
        }
        for name, value in bindings.items():
            engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(engine)
        component.setData(b'''
            import QtQuick
            Item {
                id: root
                Theme {
                    id: theme
                    dark: true
                    clickAnimationsEnabled: false
                    hoverAnimationsEnabled: false
                    fadeAnimationsEnabled: false
                }
                SearchResultSurface {
                    id: results
                    width: root.width; height: 170
                    theme: theme
                    controller: appController
                    resultModel: searchModel
                    current: true; viewMode: "continious"
                    splitterRatio: 0.58; presentationActive: true
                }
                TaskDockView {
                    objectName: "tasksDock"
                    y: results.height
                    width: root.width; height: root.height - y
                    theme: theme
                }
            }
        ''', QUrl.fromLocalFile(str(QML / "TaskSearchSyncTest.qml")))
        view = component.create()
        self.assertIsNotNone(view, [error.toString() for error in component.errors()])
        window = QQuickWindow()
        window.resize(width, 760)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            self.wait_frame(window, lambda: view.findChild(
                QQuickItem, "quickTaskViewSwitcher",
            ) is not None)
            yield window, view
            self.assertEqual(warnings, [])
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def click(self, window, item, x_fraction=0.5, modifiers=Qt.NoModifier):
        point = item.mapToScene(QPointF(
            item.width() * x_fraction, item.height() / 2,
        )).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, modifiers, point)

    def visual_item(self, root, name):
        if root.objectName() == name:
            return root
        for child in root.childItems():
            found = self.visual_item(child, name)
            if found is not None:
                return found
        return None

    def test_qml_surface_switch_selection_and_search_type_scope(self):
        self.tasks.open_quick_workspace()
        with self.scene(1480) as (window, view):
            switcher = view.findChild(QQuickItem, "quickTaskViewSwitcher")
            self.click(window, switcher, 5 / 6)
            self.wait_frame(window, lambda: view.findChild(
                QQuickItem, "embeddedScopeSwitcher",
            ) is not None)
            self.assertEqual(self.tasks.workspaceSurface, "browser")
            self.assertTrue(self.tasks._advanced_visible)
            results = view.findChild(QQuickItem, "searchResultsListView")
            self.click(window, results, 0.35)
            self.application._selection_load_timer.stop()
            self.assertEqual(self.tab.selected_node_id, self.second.code)
            selected = self.application.workspace_model.node_for(
                self.tab.selected_node_id,
            ).source
            self.deliver_details(selected)
            self.assertEqual(self.tasks._advanced_target_key, selected.get_search_key())
            results.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
            self.assertEqual(self.tasks.advancedScope, "multiple")
            self.assertCountEqual(
                self.tasks._multiple_targets, [self.first, self.second],
            )

            stype = FakeStype()
            stype.get_code = lambda: "prod/episode"
            stype.get_pretty_name = lambda: "Episode"
            self.tab.stype = stype
            self.application.section_state_changed.emit()
            scope = view.findChild(QQuickItem, "embeddedScopeSwitcher")
            self.assertEqual(scope.property("model").toVariant()[1]["label"], "All Episode")
            self.wait_frame(window)
            segment = self.visual_item(scope, "segmentedButtonSegment_search_type")
            self.assertIsNotNone(segment)
            self.assertTrue(segment.isEnabled())
            self.assertTrue(segment.isVisible())
            self.click(window, segment)
            self.wait_frame(window)
            self.assertEqual(self.tasks.advancedScope, "search_type")
            self.assertEqual(self.tasks._advanced_target_key, "prod/episode")

    def test_qml_narrow_browser_keeps_scope_action_available(self):
        self.tasks.open_workspace()
        with self.scene(460) as (window, view):
            self.wait_frame(window, lambda: view.findChild(
                QQuickItem, "compactScopeButton",
            ) is not None)
            scope = view.findChild(QQuickItem, "compactScopeButton")
            self.assertTrue(scope.isVisible())
            self.assertGreater(scope.width(), 0)
            self.click(window, scope)
            self.wait_frame(window)
            browser = view.findChild(QObject, "tasksWorkspaceView")
            self.assertIsNotNone(browser)


if __name__ == "__main__":
    unittest.main()
