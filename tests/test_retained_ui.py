"""Real QML lifecycle tests for warm workspaces and hidden consumers."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from tests import test_process_menu_latency as process_menus

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import (
    QCoreApplication, QEvent, QMetaObject, QObject, QPoint, QPointF, Qt, QUrl,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from thlib.environment import env_mode
from thlib.ui.controller import ApplicationController
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.communication_feed import MessagesController
from thlib.ui.filter_editor import FilterEditorController
from thlib.ui.quick_filter_editor import QuickFilterEditorController
from thlib.ui.user import UserController
from thlib.ui.workspace_models.docks import DockPanelModel
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.windows import FloatingWindowModel, VisibleFloatingWindowModel
from tests.profile_ui_responsiveness import frame

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class RetainedUiTests(TestCase):
    maxDiff = None
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        temporary = TemporaryDirectory(prefix="tactic-retained-ui-")
        self.addCleanup(temporary.cleanup)
        redirect = patch.object(env_mode, "current_path", temporary.name)
        redirect.start()
        self.addCleanup(redirect.stop)
        self.engine = QQmlEngine()
        self.components = []
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(e.toString() for e in errors)
        )
        self.theme_component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        self.theme = self.theme_component.createWithInitialProperties({"dark": True})
        self.application = ApplicationController()
        self.addCleanup(self.application.shutdown)

    def _show(self, component, properties):
        self.components.append(component)
        view = component.createWithInitialProperties(properties)
        self.assertIsNotNone(view, [e.toString() for e in component.errors()])
        window = QQuickWindow()
        window.resize(900, 650)
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

    def _click(self, window, item):
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        frame(window, lambda: QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point))

    def _show_search_workspace(self):
        controller = self.application
        users = UserController(controller)
        filters = FilterEditorController(
            controller.workspace_state.filter_model, lambda: [], lambda: [], lambda *_: None,
        )
        editor = QuickFilterEditorController(controller, users)
        tab = SearchTabSession(tab_id="assets", title="Assets", loaded=True)
        section = SectionSession(
            entry_key="test/assets", title="Assets", accent="#987654",
            search_type="test/assets", tabs=[tab], current_tab_id="assets",
        )
        controller._sessions = {section.entry_key: section}
        controller._current_section_key = section.entry_key
        controller._request_quick_filter_catalog = Mock()
        controller._request_quick_filter_tasks = Mock()
        controller._active_stype = lambda: None
        groups = Mock(return_value=[{
            "key": "column:category", "title": "Category", "source": "column",
            "accent": "#987654", "allSelected": True,
            "options": [{"key": "props", "title": "Props", "selected": False, "accent": "#987654", "showAccentMarker": False}],
        }])
        controller._quick_filters.groups = groups
        state = controller.workspace_state
        bindings = {
            "appController": controller, "workspaceState": state,
            "workspaceTabsModel": state.tabs_model,
            "workspaceResultSurfacesModel": state.result_surfaces_model,
            "searchSuggestionModel": state.search_suggestion_model,
            "versionsModel": controller.versions_model,
            "filterEditorController": filters, "filterPresetModel": filters.presets,
            "quickFilterEditorController": editor, "userController": users,
            "userPickerModel": users.users, "userListModel": users.users,
            "windowModel": controller.window_model,
            "dockModel": controller.dock_model,
        }
        for name, value in bindings.items():
            self.engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(QML / "SearchWorkspaceView.qml"))
        )
        window, view = self._show(component, {"theme": self.theme, "pageTitle": "Search", "shelfController": None})
        return controller, state, groups, window, view, (users, filters, editor)

    def test_closed_quick_filters_do_not_read_or_build_the_catalog(self):
        (
            controller, _state, groups, window, view, _resources,
        ) = self._show_search_workspace()
        frame(window, controller.quick_filters_changed.emit)
        groups.assert_not_called()
        button = process_menus.visual_control(view, "searchQuickFilterButton")
        self._click(window, button)
        self.assertGreater(groups.call_count, 0)
        popup = view.findChild(QObject, "searchQuickFilterPopup")
        self.assertIsNotNone(popup)
        closed = QSignalSpy(popup.closed)
        QMetaObject.invokeMethod(popup, "close")
        if not closed.count():
            self.assertTrue(closed.wait(1000))
        frame(window)
        groups.reset_mock()
        frame(window, controller.quick_filters_changed.emit)
        groups.assert_not_called()

    def test_search_tab_width_changes_settle_synchronously(self):
        (
            _controller, state, _groups, window, view, _resources,
        ) = self._show_search_workspace()
        result_model = RecordListModel(("id",))

        def tab_records(current_key):
            return [
                {
                    "entryKey": key,
                    "title": title,
                    "closable": True,
                    "current": key == current_key,
                    "resultModel": result_model,
                    "viewMode": "grid",
                    "splitterRatio": 0.5,
                }
                for key, title in (
                    ("first", "A" * 80),
                    ("second", "B" * 80),
                )
            ]

        frame(window, lambda: state.set_tabs(tab_records("first")))

        def find_visual(parent, object_name):
            if parent.objectName() == object_name:
                return parent
            for child in parent.childItems():
                found = find_visual(child, object_name)
                if found is not None:
                    return found
            return None

        first_tab = find_visual(view, "searchTabDelegate_first")
        second_tab = find_visual(view, "searchTabDelegate_second")
        self.assertIsNotNone(first_tab, self.warnings)
        self.assertIsNotNone(second_tab, self.warnings)
        previous_widths = (first_tab.width(), second_tab.width())

        state.set_tabs(tab_records("second"))
        synchronous_widths = (first_tab.width(), second_tab.width())
        frame(window)

        self.assertNotEqual(synchronous_widths, previous_widths)
        self.assertEqual(
            (first_tab.width(), second_tab.width()), synchronous_widths
        )
        self.assertEqual(self.warnings, [])

    def test_database_editor_retains_dirty_state_for_the_same_context(self):
        app_component = QQmlComponent(self.engine)
        app_component.setData(b'''import QtQml
QtObject {
    property string current_project_code: "demo"
    property string current_section_key: "demo/assets"
    property string current_page_key: "tab-b"
    property var selected_result_node_ids: ["node-b"]
    property var selected_result_records: [{
        "nodeId": "node-b", "searchKey": "skey://demo/assets?code=B",
        "title": "Asset B", "code": "B", "type": "asset",
        "values": {"name": "Asset B"}
    }]
    property int selected_result_count: selected_result_records.length
    property var selected_result_fields: ["name"]
    property bool loading: false
    signal selected_node_changed()
    signal project_changed(string projectCode, string title)
    signal section_state_changed()
    function editable_result_field_records(nodeId) {
        return [{
            "fieldName": "name", "fieldLabel": "Name",
            "fieldValue": nodeId === "node-a" ? "Asset A" : "Asset B"
        }]
    }
    function update_selected_item_fields(nodeId, changes) {}
    function update_selected_items(field, value) {}
}
''', QUrl())
        app_stub = app_component.create()
        self.assertIsNotNone(app_stub, app_component.errors())

        columns_component = QQmlComponent(self.engine)
        columns_component.setData(b'''import QtQml
QtObject {
    property int beginCalls: 0
    signal applied()
    function begin_session() { beginCalls += 1 }
    function order_field_records(records) { return records }
}
''', QUrl())
        columns_stub = columns_component.create()
        self.assertIsNotNone(columns_stub, columns_component.errors())
        self.engine.rootContext().setContextProperty("appController", app_stub)
        self.engine.rootContext().setContextProperty(
            "columnsEditorController", columns_stub
        )

        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "." as App
Item {
    id: harness
    required property var theme
    App.DatabaseEditorView {
        id: editor
        objectName: "retainedDatabaseEditor"
        anchors.fill: parent
        theme: harness.theme
    }
}
''', QUrl.fromLocalFile(str(QML / "RetainedDatabaseHarness.qml")))
        window, harness = self._show(
            component, {"theme": self.theme}
        )
        editor = harness.findChild(QObject, "retainedDatabaseEditor")
        self.assertIsNotNone(editor, self.warnings)

        def active_record():
            value = editor.property("activeRecord")
            return value.toVariant() if hasattr(value, "toVariant") else value

        initial_begin_calls = columns_stub.property("beginCalls")
        self.assertGreaterEqual(initial_begin_calls, 1)

        dock_model = DockPanelModel({})
        dock_model.show_panel("db_table")
        layout_b = dock_model.capture_layout()
        layout_a = DockPanelModel({}).capture_layout()
        self.assertTrue(dock_model.is_panel_presented("db_table"))

        def sync_database_presentation(panel_id, presented):
            if panel_id == "db_table":
                harness.setVisible(presented)

        dock_model.panelPresentationChanged.connect(
            sync_database_presentation
        )

        editor.setProperty("pendingChanges", {"name": "Edited B"})
        editor.setProperty("dirtyCount", 1)
        self.assertTrue(dock_model.prehide_for_layout(layout_a))
        QCoreApplication.processEvents()
        self.assertFalse(harness.isVisible())
        self.assertEqual(
            columns_stub.property("beginCalls"), initial_begin_calls
        )

        app_stub.setProperty("current_page_key", "tab-a")
        app_stub.setProperty("selected_result_node_ids", ["node-a"])
        app_stub.setProperty("selected_result_records", [{
            "nodeId": "node-a",
            "searchKey": "skey://demo/assets?code=A",
            "title": "Asset A",
            "code": "A",
            "type": "asset",
            "values": {"name": "Asset A"},
        }])
        self.assertTrue(QMetaObject.invokeMethod(
            app_stub, "selected_node_changed"
        ))
        QCoreApplication.processEvents()
        self.assertEqual(
            columns_stub.property("beginCalls"), initial_begin_calls
        )
        self.assertEqual(editor.property("dirtyCount"), 1)
        self.assertEqual(active_record()["nodeId"], "node-b")
        self.assertTrue(dock_model.apply_layout(layout_a))
        QCoreApplication.processEvents()
        self.assertFalse(harness.isVisible())
        self.assertEqual(
            columns_stub.property("beginCalls"), initial_begin_calls
        )

        self.assertTrue(dock_model.prehide_for_layout(layout_b))
        app_stub.setProperty("current_page_key", "tab-b")
        app_stub.setProperty("selected_result_node_ids", ["node-b"])
        app_stub.setProperty("selected_result_records", [{
            "nodeId": "node-b",
            "searchKey": "skey://demo/assets?code=B",
            "title": "Asset B",
            "code": "B",
            "type": "asset",
            "values": {"name": "Asset B"},
        }])
        self.assertTrue(QMetaObject.invokeMethod(
            app_stub, "selected_node_changed"
        ))
        QCoreApplication.processEvents()
        self.assertFalse(harness.isVisible())
        self.assertEqual(
            columns_stub.property("beginCalls"), initial_begin_calls
        )

        self.assertTrue(dock_model.apply_layout(layout_b))
        QCoreApplication.processEvents()
        self.assertTrue(harness.isVisible())
        self.assertEqual(
            columns_stub.property("beginCalls"), initial_begin_calls
        )
        self.assertEqual(editor.property("dirtyCount"), 1)
        self.assertEqual(editor.property("pendingChanges"), {"name": "Edited B"})
        self.assertEqual(active_record()["nodeId"], "node-b")

        app_stub.setProperty("current_page_key", "tab-a")
        app_stub.setProperty("selected_result_node_ids", ["node-a"])
        app_stub.setProperty("selected_result_records", [{
            "nodeId": "node-a",
            "searchKey": "skey://demo/assets?code=A",
            "title": "Asset A",
            "code": "A",
            "type": "asset",
            "values": {"name": "Asset A"},
        }])
        self.assertTrue(QMetaObject.invokeMethod(
            app_stub, "selected_node_changed"
        ))
        QCoreApplication.processEvents()
        self.assertEqual(
            columns_stub.property("beginCalls"), initial_begin_calls + 1
        )
        self.assertEqual(editor.property("dirtyCount"), 0)
        self.assertEqual(active_record()["nodeId"], "node-a")
        self.assertEqual(self.warnings, [])

    def test_unsnapped_dock_title_drag_keeps_the_dock_in_its_layout(self):
        controller = self.application
        for name, value in {
            "dockModel": controller.dock_model,
            "visibleDockModel": [],
            "detachedDockModel": [],
            "windowModel": controller.window_model,
            "workspaceState": controller.workspace_state,
        }.items():
            self.engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "." as App
Item {
    id: harness
    required property var theme
    property bool resizeOwnerHighlighted: false
    property bool resizeNeighborHighlighted: false
    property bool resizeUnrelatedHighlighted: false
    function releaseWithoutTarget() {
        dockHost.beginDockDrag("tasks")
        dockHost.finishDockDrag("tasks", 280, 120, 360, 400, false)
    }
    function inspectSharedResize() {
        dockHost.beginDockResize(
            "results", "vertical", 300, 0, 600, true)
        resizeOwnerHighlighted = dockHost.dockSharesActiveResize(
            "results", 0, 0, 300, 600)
        resizeNeighborHighlighted = dockHost.dockSharesActiveResize(
            "tasks", 300, 0, 400, 600)
        resizeUnrelatedHighlighted = dockHost.dockSharesActiveResize(
            "notes", 700, 0, 200, 600)
        dockHost.updateDockResizeBoundary(360, 0, 600)
        resizeNeighborHighlighted = resizeNeighborHighlighted
            && dockHost.dockSharesActiveResize(
                "tasks", 360, 0, 340, 600)
        dockHost.endDockResize()
    }
    App.DockHost {
        id: dockHost
        anchors.fill: parent
        theme: harness.theme
        projectTitle: "Demo"
        pageTitle: "Search"
    }
}''', QUrl.fromLocalFile(str(QML / "DockDropHarness.qml")))
        window, view = self._show(component, {"theme": self.theme})
        before = controller.dock_model.capture_layout()

        self.assertTrue(QMetaObject.invokeMethod(
            view, "releaseWithoutTarget"
        ))
        frame(window)

        self.assertEqual(controller.dock_model.capture_layout(), before)
        self.assertTrue(QMetaObject.invokeMethod(
            view, "inspectSharedResize"
        ))
        self.assertTrue(view.property("resizeOwnerHighlighted"))
        self.assertTrue(view.property("resizeNeighborHighlighted"))
        self.assertFalse(view.property("resizeUnrelatedHighlighted"))
        self.assertEqual(self.warnings, [])

    def test_empty_search_workspace_hides_previous_docks_and_prompts_for_menu(self):
        controller = self.application
        for name, value in {
            "dockModel": controller.dock_model,
            "visibleDockModel": controller.visible_dock_model,
            "detachedDockModel": controller.detached_dock_model,
            "windowModel": controller.window_model,
            "workspaceState": controller.workspace_state,
        }.items():
            self.engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "." as App
Item {
    id: harness
    required property var theme
    property bool searchOpened: false
    App.DockHost {
        anchors.fill: parent
        theme: harness.theme
        projectTitle: "Demo"
        pageTitle: "Search"
        workspaceActive: harness.searchOpened
    }
}''', QUrl.fromLocalFile(str(QML / "EmptySearchWorkspaceHarness.qml")))
        window, view = self._show(component, {"theme": self.theme})
        empty = view.findChild(QQuickItem, "workspaceNoSearchType")
        canvas = view.findChild(QQuickItem, "dockCanvas")
        self.assertIsNotNone(empty)
        self.assertIsNotNone(canvas)
        self.assertTrue(empty.isVisible())
        self.assertFalse(canvas.isVisible())
        self.assertIn("menu", empty.findChild(
            QObject, "emptyStateMessage"
        ).property("text").lower())
        for width in (420, 1400):
            window.resize(width, 650)
            view.setSize(window.size())
            frame(window)
            self.assertEqual(empty.width(), view.width())
        self.assertEqual(self.warnings, [])

    def test_dock_layout_switch_keeps_delegate_and_loaded_content(self):
        from tests.dock_layout_fixture import three_column_settings

        controller = self.application
        baseline = DockPanelModel(three_column_settings()).capture_layout()
        hidden = DockPanelModel(three_column_settings())
        hidden.close_panel("tasks")
        hidden_layout = hidden.capture_layout()
        controller.dock_model.apply_layout(hidden_layout)
        self.engine.rootContext().setContextProperty(
            "dockModel", controller.dock_model
        )
        self.engine.rootContext().setContextProperty(
            "visibleDockModel", controller.visible_dock_model
        )
        self.engine.rootContext().setContextProperty(
            "windowModel", controller.window_model
        )
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "." as App
Item {
    id: harness
    required property var theme
    property bool dockResizeActive: false
    property bool windowResizeActive: false
    property int taskContentCreations: 0
    property int taskDelegateCreations: 0
    property int taskDelegateDestructions: 0
    function beginDockDrag(panelId) {}
    function updateDockDrag(panelId, pointerX, pointerY) {}
    function finishDockDrag(panelId, x, y, width, height) {}
    function beginDockResize() { dockResizeActive = true }
    function endDockResize() { dockResizeActive = false }

    QtObject { id: retainedUiModel }
    Component {
        id: retainedContent
        Item {
            objectName: "retainedDockContent"
            property var retainedModel: retainedUiModel
            readonly property bool taskContent: parent && parent.objectName
                === "dockPanelContentLoader_tasks"
            ListView {
                objectName: "retainedTaskList"
                property bool taskContent: parent.taskContent
                anchors.fill: parent
                model: 8
                delegate: Item {
                    required property int index
                    objectName: "retainedTaskDelegate_" + index
                    width: ListView.view.width
                    height: 24
                    Component.onCompleted: {
                        if (ListView.view.taskContent)
                            harness.taskDelegateCreations += 1
                    }
                    Component.onDestruction: {
                        if (ListView.view.taskContent)
                            harness.taskDelegateDestructions += 1
                    }
                }
            }
            Component.onCompleted: {
                if (parent && parent.objectName
                        === "dockPanelContentLoader_tasks")
                    harness.taskContentCreations += 1
            }
        }
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
                objectName: "retainedDockPanel_" + panelId
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
                contentComponent: retainedContent
            }
        }
    }
}''', QUrl.fromLocalFile(str(QML / "DockRetentionHarness.qml")))
        window, view = self._show(
            component, {"theme": self.theme}
        )

        def find_item(parent, object_name):
            if parent.objectName() == object_name:
                return parent
            for child in parent.childItems():
                found = find_item(child, object_name)
                if found is not None:
                    return found
            return None

        panel = find_item(view, "retainedDockPanel_tasks")
        if panel is not None:
            hidden_loader = find_item(
                panel, "dockPanelContentLoader_tasks"
            )
            self.assertIsNone(hidden_loader.property("item"))

        frame(window, lambda: controller.dock_model.apply_layout(baseline))
        panel = find_item(view, "retainedDockPanel_tasks")
        self.assertIsNotNone(panel, self.warnings)
        loader = find_item(
            panel, "dockPanelContentLoader_tasks"
        )
        self.assertIsNotNone(loader)
        for _attempt in range(8):
            if loader.property("item") is not None:
                break
            frame(window)
        content = loader.property("item")
        self.assertIsNotNone(content, self.warnings)
        retained_model = content.property("retainedModel")
        self.assertIsNotNone(retained_model)
        self.assertEqual(view.property("taskContentCreations"), 1)
        for _attempt in range(8):
            if view.property("taskDelegateCreations") == 8:
                break
            frame(window)
        self.assertEqual(view.property("taskDelegateCreations"), 8)
        retained_list = find_item(content, "retainedTaskList")
        retained_delegate = find_item(
            retained_list, "retainedTaskDelegate_0"
        )
        self.assertIsNotNone(retained_delegate)
        loader_status_changes = QSignalSpy(loader.statusChanged)
        self.assertIsNone(find_item(
            panel, "dockPanelContentRelease_tasks"
        ))

        swapped = DockPanelModel(three_column_settings())
        swapped.place_panel("results", "tasks", "swap")
        swapped_layout = swapped.capture_layout()
        results_panel = find_item(view, "retainedDockPanel_results")
        self.assertIsNotNone(results_panel)
        results_panel.setProperty(
            "localX", results_panel.property("localX") + 120
        )
        synchronous_layout_state = {}

        def apply_swapped_layout():
            controller.dock_model.apply_layout(swapped_layout)
            synchronous_layout_state.update({
                "x": results_panel.x(),
                "y": results_panel.y(),
                "width": results_panel.width(),
                "height": results_panel.height(),
            })

        frame(window, apply_swapped_layout)
        results_record = next(
            value for value in controller.dock_model._panels
            if value.panel_id == "results"
        )
        expected_x = round(results_record.x * view.width())
        expected_y = round(results_record.y * view.height())
        expected_right = (
            view.width()
            if results_record.x + results_record.width >= 0.999999
            else round(
                (results_record.x + results_record.width) * view.width()
            )
        )
        expected_bottom = (
            view.height()
            if results_record.y + results_record.height >= 0.999999
            else round(
                (results_record.y + results_record.height) * view.height()
            )
        )
        final_layout_state = {
            "x": expected_x,
            "y": expected_y,
            "width": expected_right - expected_x,
            "height": expected_bottom - expected_y,
        }
        self.assertEqual(synchronous_layout_state, final_layout_state)
        self.assertEqual({
            "x": results_panel.x(),
            "y": results_panel.y(),
            "width": results_panel.width(),
            "height": results_panel.height(),
        }, final_layout_state)

        frame(window, lambda: controller.dock_model.apply_layout(baseline))
        first_tab = SearchTabSession(
            tab_id="layout-visible",
            title="Visible docks",
            loaded=True,
            workspace_layout=baseline,
        )
        second_tab = SearchTabSession(
            tab_id="layout-hidden",
            title="Hidden task dock",
            loaded=True,
            workspace_layout=hidden_layout,
        )
        section = SectionSession(
            entry_key="test/layouts",
            title="Layouts",
            accent="#78909c",
            search_type="test/assets",
            tabs=[first_tab, second_tab],
            current_tab_id=first_tab.tab_id,
            sidebar_presets_initialized=True,
        )
        controller._sessions = {section.entry_key: section}
        controller._current_section_key = section.entry_key
        controller._sync_search_tabs()

        frame(
            window,
            lambda: controller._activate_workspace_tab(
                second_tab.tab_id, second_tab.title
            ),
        )

        hidden_panel = find_item(view, "retainedDockPanel_tasks")
        hidden_loader = find_item(
            hidden_panel, "dockPanelContentLoader_tasks"
        )
        self.assertIs(hidden_panel, panel)
        self.assertIs(hidden_loader, loader)
        self.assertTrue(hidden_loader.property("active"))
        self.assertFalse(hidden_loader.property("visible"))
        self.assertIs(hidden_loader.property("item"), content)
        self.assertIs(find_item(content, "retainedTaskList"), retained_list)
        self.assertIs(
            find_item(retained_list, "retainedTaskDelegate_0"),
            retained_delegate,
        )
        self.assertEqual(view.property("taskDelegateCreations"), 8)
        self.assertEqual(view.property("taskDelegateDestructions"), 0)
        self.assertFalse(
            controller.visible_dock_model._removal_timer.isActive()
        )

        for tab in (first_tab, second_tab, first_tab):
            frame(
                window,
                lambda value=tab: controller._activate_workspace_tab(
                    value.tab_id, value.title
                ),
            )

        restored_panel = find_item(view, "retainedDockPanel_tasks")
        restored_loader = find_item(
            restored_panel, "dockPanelContentLoader_tasks"
        )
        self.assertIs(restored_panel, panel)
        self.assertIs(restored_loader, loader)
        self.assertTrue(restored_loader.property("visible"))
        self.assertIs(restored_loader.property("item"), content)
        self.assertIs(content.property("retainedModel"), retained_model)
        self.assertEqual(view.property("taskContentCreations"), 1)
        self.assertIs(find_item(content, "retainedTaskList"), retained_list)
        self.assertIs(
            find_item(retained_list, "retainedTaskDelegate_0"),
            retained_delegate,
        )
        self.assertEqual(view.property("taskDelegateCreations"), 8)
        self.assertEqual(view.property("taskDelegateDestructions"), 0)
        self.assertEqual(loader_status_changes.count(), 0)
        self.assertEqual(self.warnings, [])

    def test_stacked_search_dock_keeps_move_grip_at_fixed_position(self):
        self.engine.rootContext().setContextProperty(
            "dockModel", self.application.dock_model
        )
        self.engine.rootContext().setContextProperty(
            "windowModel", self.application.window_model
        )
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "." as App
Item {
    id: harness
    required property var theme
    property bool dockResizeActive: false
    property bool windowResizeActive: false
    property int dragStarts: 0
    property int stackCount: 1
    function beginDockDrag(panelId) { dragStarts += 1 }
    function updateDockDrag(panelId, pointerX, pointerY) {}
    function finishDockDrag(panelId, x, y, width, height) {}
    function beginDockResize() {}
    function endDockResize() {}
    App.DockPanel {
        anchors.fill: parent
        host: harness
        theme: harness.theme
        panelId: "results"
        title: "Search"
        kind: "results"
        panelX: 0
        panelY: 0
        panelWidth: 1
        panelHeight: 1
        modelVisible: true
        panelOpen: true
        stackActive: true
        closable: false
        stackOrder: 1
        dockArea: "left"
        canResizeLeft: false
        canResizeRight: false
        canResizeTop: false
        canResizeBottom: false
        stackPanels: [
            {"panelId": "results", "title": "Search",
             "kind": "results", "active": true},
            {"panelId": "snapshot", "title": "Snapshots",
             "kind": "snapshot", "active": false}
        ]
        stackSize: harness.stackCount
        contentComponent: Component { Item {} }
    }
}''', QUrl.fromLocalFile(str(QML / "StackedSearchDockHarness.qml")))
        window, view = self._show(component, {"theme": self.theme})

        def find_item(parent, object_name):
            if parent.objectName() == object_name:
                return parent
            for child in parent.childItems():
                found = find_item(child, object_name)
                if found is not None:
                    return found
            return None

        grip = find_item(view, "dockTitleDrag_results")
        self.assertIsNotNone(grip, self.warnings)
        self.assertTrue(grip.isVisible())
        original_position = grip.mapToScene(QPointF(0, 0))

        view.setProperty("stackCount", 2)
        frame(window)

        self.assertTrue(grip.isVisible())
        self.assertEqual(grip.mapToScene(QPointF(0, 0)), original_position)
        center = grip.mapToScene(QPointF(
            grip.width() / 2, grip.height() / 2
        )).toPoint()
        frame(window, lambda: QTest.mousePress(
            window, Qt.LeftButton, Qt.NoModifier, center
        ))
        frame(window, lambda: QTest.mouseMove(
            window, center + QPointF(12, 0).toPoint()
        ))
        frame(window, lambda: QTest.mouseRelease(
            window, Qt.LeftButton, Qt.NoModifier,
            center + QPointF(12, 0).toPoint(),
        ))
        self.assertEqual(view.property("dragStarts"), 1)
        self.assertEqual(self.warnings, [])

    def test_dock_content_reflows_live_during_resize(self):
        self.engine.rootContext().setContextProperty(
            "dockModel", self.application.dock_model
        )
        self.engine.rootContext().setContextProperty(
            "windowModel", self.application.window_model
        )
        component = QQmlComponent(self.engine)
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
        id: retainedContent
        Item {
            objectName: "knowledgeResizeContent"
            property int widthChangeCount: 0
            property bool dockResizeActive: false
            onWidthChanged: widthChangeCount += 1
        }
    }
    App.DockPanel {
        objectName: "knowledgeResizePanel"
        host: harness
        theme: harness.theme
        panelId: "knowledge"
        title: "Knowledge Base"
        kind: "knowledge"
        panelX: 0
        panelY: 0
        panelWidth: 0.7
        panelHeight: 1
        modelVisible: true
        panelOpen: true
        stackActive: true
        closable: true
        stackOrder: 1
        dockArea: "floating"
        canResizeLeft: true
        canResizeRight: true
        canResizeTop: true
        canResizeBottom: true
        stackPanels: []
        stackSize: 1
        contentComponent: retainedContent
    }
}''', QUrl.fromLocalFile(str(QML / "KnowledgeResizeHarness.qml")))
        window, view = self._show(component, {"theme": self.theme})

        def find_item(parent, object_name):
            if parent.objectName() == object_name:
                return parent
            for child in parent.childItems():
                found = find_item(child, object_name)
                if found is not None:
                    return found
            return None

        panel = find_item(view, "knowledgeResizePanel")
        loader = find_item(view, "dockPanelContentLoader_knowledge")
        right_edge = find_item(panel, "dockResizeEdge_right")
        self.assertIsNotNone(panel, self.warnings)
        self.assertIsNotNone(loader, self.warnings)
        self.assertIsNotNone(right_edge, self.warnings)
        grip = find_item(right_edge, "dockResizeGripVisual")
        self.assertEqual(right_edge.width(), 10)
        self.assertAlmostEqual(
            right_edge.x() + right_edge.width() / 2, panel.width()
        )
        self.assertAlmostEqual(
            grip.x() + grip.width() / 2, right_edge.width() / 2
        )
        self.assertGreaterEqual(grip.width(), 3)
        for _attempt in range(8):
            if loader.property("item") is not None:
                break
            frame(window)
        content = loader.property("item")
        self.assertIsNotNone(content, self.warnings)
        initial_loader_width = loader.width()
        changes = QSignalSpy(content.widthChanged)
        press_point = panel.mapToScene(QPointF(
            panel.width() + 3,
            panel.height() / 2,
        )).toPoint()
        frame(
            window,
            lambda: QTest.mousePress(
                window, Qt.LeftButton, Qt.NoModifier, press_point
            ),
        )
        self.assertTrue(panel.property("resizing"))
        self.assertTrue(content.property("dockResizeActive"))
        for offset in range(20, 181, 20):
            frame(
                window,
                lambda value=offset: QTest.mouseMove(
                    window, press_point + QPointF(value, 0).toPoint()
                ),
            )

        self.assertGreater(loader.width(), initial_loader_width)
        self.assertAlmostEqual(content.width(), loader.width())
        self.assertGreater(changes.count(), 0)
        self.assertIs(loader.property("item"), content)

        release_point = press_point + QPointF(180, 0).toPoint()
        frame(
            window,
            lambda: QTest.mouseRelease(
                window, Qt.LeftButton, Qt.NoModifier, release_point
            ),
        )
        self.assertGreater(loader.width(), initial_loader_width)
        self.assertAlmostEqual(content.width(), loader.width())
        self.assertIs(loader.property("item"), content)
        self.assertFalse(content.property("dockResizeActive"))
        self.assertEqual(self.warnings, [])

    def test_shared_dock_resize_grip_starts_on_first_press(self):
        self.application.dock_model.place_panel("notes", "results", "right")
        self.application.dock_model.place_panel("snapshot", "notes", "bottom")
        self.application.dock_model.place_panel(
            "drop_plate", "snapshot", "bottom"
        )
        self.engine.rootContext().setContextProperty(
            "dockModel", self.application.dock_model
        )
        self.engine.rootContext().setContextProperty(
            "visibleDockModel", self.application.visible_dock_model
        )
        self.engine.rootContext().setContextProperty(
            "windowModel", self.application.window_model
        )
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "." as App
Item {
    id: harness
    required property var theme
    property int resizeStarts: 0
    function beginDockResize() { resizeStarts += 1 }
    function updateDockResizeBoundary() {}
    function endDockResize() {}
    function dockSharesActiveResize() { return false }
    function beginDockDrag() {}
    function updateDockDrag() {}
    function finishDockDrag() {}
    Component { id: content; Item {} }
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
            App.DockPanel {
                host: harness
                theme: harness.theme
                panelId: parent.panelId
                title: parent.title
                kind: parent.kind
                panelX: parent.panelX
                panelY: parent.panelY
                panelWidth: parent.panelWidth
                panelHeight: parent.panelHeight
                modelVisible: parent.panelVisible && parent.stackActive && !parent.detached
                panelOpen: modelVisible
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
                contentComponent: content
            }
        }
    }
}''', QUrl.fromLocalFile(str(QML / "DockResizePressHarness.qml")))
        window, view = self._show(component, {"theme": self.theme})
        def find_item(item, name):
            if item.objectName() == name:
                return item
            for child in item.childItems():
                found = find_item(child, name)
                if found is not None:
                    return found
            return None

        panel = find_item(view, "dockPanel_results")
        self.assertIsNotNone(panel, self.warnings)
        edge = find_item(panel, "dockResizeEdge_right")
        grip = find_item(edge, "dockResizeGripVisual")
        grip_center = grip.mapToItem(panel, QPointF(
            grip.width() / 2, grip.height() / 2
        ))
        self.assertAlmostEqual(grip_center.x(), panel.width())
        self.assertAlmostEqual(grip_center.y(), panel.height() / 2)
        point = grip.mapToScene(QPointF(grip.width() / 2, grip.height() / 2)).toPoint()

        frame(window, lambda: QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, point))
        self.assertEqual(view.property("resizeStarts"), 1, self.warnings)
        frame(window, lambda: QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, point))
        content_point = panel.mapToScene(QPointF(
            panel.width() - 10, panel.height() / 2
        )).toPoint()
        frame(window, lambda: QTest.mouseClick(
            window, Qt.LeftButton, Qt.NoModifier, content_point
        ))
        self.assertEqual(view.property("resizeStarts"), 1, self.warnings)

        panel = find_item(view, "dockPanel_notes")
        self.assertIsNotNone(panel, self.warnings)
        edge = find_item(panel, "dockResizeEdge_bottom")
        grip = find_item(edge, "dockResizeGripVisual")
        grip_center = grip.mapToItem(panel, QPointF(
            grip.width() / 2, grip.height() / 2
        ))
        self.assertAlmostEqual(grip_center.x(), panel.width() / 2)
        self.assertAlmostEqual(grip_center.y(), panel.height())
        point = grip.mapToScene(QPointF(grip.width() / 2, grip.height() / 2)).toPoint()
        frame(window, lambda: QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, point))
        self.assertEqual(view.property("resizeStarts"), 2, self.warnings)
        frame(window, lambda: QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, point))
        self.assertEqual(self.warnings, [])

    def test_search_tab_selection_visual_changes_without_late_motion(self):
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "controls" as Controls
Item {
    id: harness
    required property var theme
    property alias current: tabVisual.current
    width: 200
    height: 40
    Controls.WorkspaceTabVisual {
        id: tabVisual
        anchors.fill: parent
        theme: harness.theme
        title: "Assets"
        animateSelection: false
    }
}''', QUrl.fromLocalFile(str(QML / "SearchTabMotionHarness.qml")))
        window, view = self._show(component, {"theme": self.theme})
        def find_visual(parent, name):
            if parent.objectName() == name:
                return parent
            for child in parent.childItems():
                found = find_visual(child, name)
                if found is not None:
                    return found
            return None

        # Recycled Frame delegates belong to the visual tree, not QObject children.
        indicator = find_visual(view, "workspaceTabSelectionIndicator")
        label = find_visual(view, "workspaceTabSelectionLabel")
        self.assertIsNotNone(indicator, self.warnings)
        self.assertIsNotNone(label, self.warnings)

        view.setProperty("current", True)
        synchronous = (
            indicator.width(), indicator.opacity(), label.property("color")
        )
        frame(window)

        self.assertEqual(synchronous[:2], (view.width() - 24, 1.0))
        self.assertEqual(synchronous[2], self.theme.property("action"))
        self.assertEqual(
            (indicator.width(), indicator.opacity(), label.property("color")),
            synchronous,
        )
        self.assertEqual(self.warnings, [])

    def test_recent_chat_keeps_model_delegate_and_scroll_on_return(self):
        controller = MessagesController(self.application)
        controller._remember_conversation = Mock()
        controller._activate_draft_context = Mock()
        controller._load_messages = Mock()
        self.addCleanup(controller.shutdown)
        controller.conversations.replace([
            {"conversationId": value, "title": value, "lastTimestamp": "", "selected": index == 0}
            for index, value in enumerate(("first", "second"))
        ])
        for conversation in ("first", "second"):
            controller._conversation_id = conversation
            controller._clear_active_history()
            records = [controller._message_record({
                "code": f"{conversation}-{row}", "login": "artist",
                "message": f"Message {row}", "timestamp": "2026-08-20 10:00:00",
            }, "", "artist") for row in range(40)]
            controller.messages.replace(controller._group_message_records(records))
            controller._loaded_conversation_id = conversation
            controller._cache_current_history()
        controller.select_conversation(0)
        first_model = controller.messages
        self.engine.rootContext().setContextProperty("messagesController", controller)
        self.engine.rootContext().setContextProperty("messageSurfaceModel", controller.message_surfaces)
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "." as App
import "controls" as Controls
Item {
    id: timelineHost
    required property var theme
    property bool messagePresentationReady: true
    property var timelineReactions: ({messageId: ""})
    property var currentTimeline: null
    Connections {
        target: messagesController
        function onVisibilityChanged(visible) {
            if (visible)
                Qt.callLater(function() { timelineHost.currentTimeline.revealLatestOnce() })
        }
        function onMessageFocusRequested(messageId) {
            Qt.callLater(function() {
                timelineHost.currentTimeline.focusMessage(messagesController.message_index(messageId))
            })
        }
    }
    Row {
        Controls.Button { objectName: "chatFirst"; theme: timelineHost.theme; text: "First"; onClicked: messagesController.select_conversation(0) }
        Controls.Button { objectName: "chatSecond"; theme: timelineHost.theme; text: "Second"; onClicked: messagesController.select_conversation(1) }
    }
    Item {
        anchors.fill: parent
        anchors.topMargin: 50
        Repeater {
            model: messageSurfaceModel
            delegate: App.MessagesTimeline {
                required property var messageModel
                required property string conversationId
                id: timeline
                theme: timelineHost.theme
                host: timelineHost
                controller: messagesController
                timelineModel: messageModel
                onCurrentChanged: if (current) timelineHost.currentTimeline = timeline
                Component.onCompleted: if (current) timelineHost.currentTimeline = timeline
            }
        }
    }
}''', QUrl.fromLocalFile(str(QML / "RetainedTimelineTest.qml")))
        window, view = self._show(component, {"theme": self.theme})
        first_timeline = view.property("currentTimeline")
        self.assertIsNotNone(first_timeline, self.warnings)
        frame(window, lambda: first_timeline.setProperty("contentY", 300.))
        original_y = first_timeline.property("contentY")
        first_item = first_timeline.property("contentItem").childItems()[0]
        self._click(window, view.findChild(QQuickItem, "chatSecond"))
        self.assertIsNot(controller.messages, first_model)
        self.assertIsNot(view.property("currentTimeline"), first_timeline)
        self._click(window, view.findChild(QQuickItem, "chatFirst"))
        self.assertIs(controller.messages, first_model)
        self.assertIs(view.property("currentTimeline"), first_timeline)
        self.assertAlmostEqual(first_timeline.property("contentY"), original_y)
        self.assertIn(first_item, first_timeline.property("contentItem").childItems())
        controller._load_messages.assert_not_called()
        self.assertEqual(self.warnings, [])

        # The active-chat poll refreshes the latest page, not the loaded past.
        controller._history_request_id = "poll"
        controller._history_background = True
        controller._offset = 40
        controller._has_more = False
        refreshed = [{
            "code": f"first-{row}", "login": "artist",
            "message": f"Message {row}", "timestamp": "2026-08-20 10:00:00",
        } for row in range(39, 8, -1)]
        frame(window, lambda: controller._messages_ready(
            "poll", {"messages": refreshed}, True, 0, "first",
        ))
        self.assertEqual(controller.messages.rowCount(), 40)
        self.assertEqual(controller._offset, 40)
        self.assertFalse(controller._has_more)
        self.assertAlmostEqual(first_timeline.property("contentY"), original_y)
        self.assertIn(first_item, first_timeline.property("contentItem").childItems())
        self.assertEqual(self.warnings, [])

        # A thumb drag must take ownership from an in-flight wheel animation.
        point = first_timeline.mapToScene(QPointF(200, 200))
        wheel = QWheelEvent(
            point, point, QPoint(), QPoint(0, -120),
            Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False,
        )
        QCoreApplication.sendEvent(window, wheel)
        animations = [item for item in first_timeline.findChildren(QObject)
                      if item.property("property") == "contentY"]
        self.assertTrue(any(item.property("running") for item in animations))
        scrollbar = next(item for item in first_timeline.childItems()
                         if item.property("reservedExtent") is not None)
        thumb_y = scrollbar.height() * (
            scrollbar.property("visualPosition") + scrollbar.property("visualSize") / 2
        )
        thumb = scrollbar.mapToScene(QPointF(scrollbar.width() / 2, thumb_y)).toPoint()
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, thumb)
        self.assertTrue(scrollbar.property("pressed"))
        self.assertFalse(any(item.property("running") for item in animations))
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, thumb)
        self.assertEqual(self.warnings, [])

        controller._mark_read = Mock()
        controller._conversation_opened = True
        frame(window, lambda: first_timeline.setProperty("contentY", 300.))
        controller._append_live_message({
            "code": "first-new", "login": "colleague", "message": "New in background",
            "timestamp": "2026-09-21 12:00:00",
        })
        frame(window, lambda: controller.set_visible(True))
        self.assertEqual(first_timeline.property("currentIndex"), -1)
        self.assertTrue(first_timeline.property("atYEnd"))
        self.assertEqual(first_timeline.property("lastRevealedMessageId"), "first-new")

        # Reopening without a new message preserves the reader's position.
        for row in range(controller.messages.rowCount()):
            controller.messages.update_record(row, {"unread": False})
        controller.set_visible(False)
        frame(window, lambda: first_timeline.setProperty("contentY", 300.))
        frame(window, lambda: controller.set_visible(True))
        self.assertEqual(first_timeline.property("currentIndex"), -1)
        self.assertAlmostEqual(first_timeline.property("contentY"), 300.)
        self.assertEqual(self.warnings, [])

    def test_messages_window_keeps_each_chat_position_when_switching(self):
        from thlib.ui.emoji import EmojiCatalog
        from thlib.ui.message_attachments import ChatAttachmentController

        users = UserController(self.application)
        attachments = ChatAttachmentController(self.application)
        self.addCleanup(attachments.shutdown)
        emoji = EmojiCatalog(QML.parents[2])
        controller = MessagesController(self.application)
        self.addCleanup(controller.shutdown)
        controller.load = Mock()
        controller._load_messages = Mock()
        controller._mark_read = Mock()
        controller._remember_conversation = Mock()
        controller._activate_draft_context = Mock()
        controller._initialized = True
        controller.conversations.replace([
            {"conversationId": value, "title": value, "lastTimestamp": "", "selected": False,
             "avatarUrl": "", "acronym": value[0], "canRename": value == "first",
             "canClearPersonal": value == "second", "isPersonalNotes": value == "second"}
            for value in ("first", "second")
        ])
        for name, value in {
            "messagesController": controller,
            "messageConversationModel": controller.conversations,
            "messageSurfaceModel": controller.message_surfaces,
            "messageAttachments": attachments,
            "messageAttachmentDraftModel": attachments.model,
            "userController": users,
            "userListModel": users.users,
            "emojiCatalog": emoji, "emojiCatalogModel": emoji,
        }.items():
            self.engine.rootContext().setContextProperty(name, value)

        def load_chat_history(count):
            controller._history_request_id = "load"
            conversation = controller._conversation_id
            controller._messages_ready("load", {"messages": [{
                "code": f"{conversation}-{index}", "login": "artist",
                "message": ("Message " + str(index) + "\n") * (1 + index % 7),
                "timestamp": "2026-09-21 10:00:00",
            } for index in reversed(range(count))]}, True, 0, conversation)
            for row in range(controller.messages.rowCount()):
                controller.messages.update_record(row, {"reactions": [{
                    "emoji": "😆", "count": 1, "reactedByMe": True,
                    "namesText": "Artist",
                }]})
                if row % 5 == 0:
                    controller.messages.update_record(row, {
                        "body": "😆", "displayHtml": "😆",
                    })
                elif row % 5 == 1:
                    controller.messages.update_record(row, {"skeyPreviews": [{
                        "kind": "knowledge", "status": "error",
                        "title": "Missing article", "error": "TACTIC item was not found",
                    }]})
                elif row % 5 == 2:
                    controller.messages.update_record(row, {"replyTo": {
                        "messageId": "previous", "senderDisplay": "Artist",
                        "body": "Earlier message being quoted",
                    }})
                elif row % 5 == 3:
                    controller.messages.update_record(row, {"attachments": [{
                        "token": "fixture", "size": 1234, "title": "Picture",
                        "extension": "PNG", "previewUrl": "", "local": False,
                    }]})
                else:
                    controller.messages.update_record(row, {"reactions": []})

        # Production can preload the selected conversation before opening its window.
        controller.select_conversation(0)
        load_chat_history(30)
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import QtQuick.Controls
import "." as App
ApplicationWindow {
    id: window
    required property var theme
    width: 900; height: 650; visible: true
    Loader {
        anchors.fill: parent
        Component.onCompleted: setSource(Qt.resolvedUrl("shell/windows/WindowContent.qml"), {
            "theme": window.theme,
            "contentSource": "MessagesView.qml",
            "contentProperties": {"objectName": "testedMessagesView"}
        })
    }
}''', QUrl.fromLocalFile(str(QML / "MessagesWindowTest.qml")))
        self.components.append(component)
        window = component.createWithInitialProperties({"theme": self.theme})
        self.assertIsNotNone(window, [e.toString() for e in component.errors()])
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)
        frame(window)
        view = window.findChild(QQuickItem, "testedMessagesView")
        controller.load.assert_called_once()

        def select_chat(row):
            conversations = view.findChild(QQuickItem, "messagesConversationListView")
            delegate = next(item for item in conversations.property("contentItem").childItems()
                            if item.property("index") == row)
            self._click(window, delegate)

        def open_chat(row, count):
            controller._load_messages.side_effect = lambda **_: setattr(controller, "_history_busy", True)
            select_chat(row)
            load_chat_history(count)

        open_chat(0, 30)
        frame(window)
        first = view.property("messages")
        frame(window)
        self.assertTrue(first.property("atYEnd"), (
            first.property("contentY"), first.property("maximumContentY"),
            first.property("count"), first.property("height"), first.property("contentHeight")))
        measured_height = first.property("contentHeight")
        for _ in range(3):
            point = first.mapToScene(QPointF(150, 150))
            event = QWheelEvent(point, point, QPoint(), QPoint(0, 1200),
                                Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
            frame(window, lambda: QCoreApplication.sendEvent(window, event))
            self.assertAlmostEqual(first.property("contentHeight"), measured_height, delta=0.5)
        QMetaObject.invokeMethod(first, "cancelWheelScroll")
        frame(window, lambda: first.setProperty("contentY", 300.))
        retained_y = first.property("contentY")
        geometry_changes = []
        first.contentHeightChanged.connect(lambda: geometry_changes.append((
            first.property("current"), first.property("contentY"),
            first.property("contentHeight"),
        )))
        card_height_changes = []
        column = first.findChild(QQuickItem, "messageCardsColumn")
        for card in column.childItems():
            if card.property("messageId"):
                card.heightChanged.connect(lambda item=card: card_height_changes.append(
                    (item.property("messageId"), item.height())))
        open_chat(1, 0)
        frame(window)
        select_chat(0)
        self.assertIs(view.property("messages"), first)
        self.assertAlmostEqual(first.property("contentY"), retained_y, msg=str(geometry_changes))
        self.assertEqual(geometry_changes, [])
        self.assertEqual(card_height_changes, [])
        movements = []
        first.contentYChanged.connect(lambda: movements.append(first.property("contentY")))
        extents = []
        first.contentHeightChanged.connect(lambda: extents.append(first.property("contentHeight")))
        for _ in range(3):
            select_chat(1)
            select_chat(0)
        self.assertEqual(extents, [])
        self.assertEqual(card_height_changes, [])
        self.assertEqual(movements, [])
        self.assertEqual(controller._load_messages.call_count, 2)

        # Server updates invalidate data, not the hidden chat's QML surface.
        select_chat(1)
        frame(window, lambda: controller.apply_cache_invalidation({"sthpw": ["messages"]}))
        select_chat(0)
        self.assertIs(view.property("messages"), first)
        controller._load_messages.assert_called_with(
            reset=True, background=True, bypass_cache=True,
        )
        load_chat_history(30)
        frame(window)
        self.assertAlmostEqual(first.property("contentY"), retained_y)
        self.assertEqual(movements, [])

        # Taking a screenshot/reactivating the window is not a new message.
        focus_requests = QSignalSpy(controller.messageFocusRequested)
        controller.set_visible(False)
        frame(window, lambda: controller.set_visible(True))
        self.assertEqual(focus_requests.count(), 0)
        self.assertAlmostEqual(first.property("contentY"), retained_y)
        self.assertEqual(movements, [])

        frame(window, lambda: QMetaObject.invokeMethod(first, "settleAtLatest"))
        retained_end = first.property("contentY")
        movements.clear()
        select_chat(1)
        select_chat(0)
        self.assertTrue(first.property("atYEnd"))
        self.assertAlmostEqual(first.property("contentY"), retained_end)
        self.assertEqual(movements, [])
        self.assertEqual(self.warnings, [])

        # A hidden arrival is revealed once, without selecting the message.
        window.hide()
        self.app.processEvents()
        controller._append_live_message({
            "code": "first-new", "login": "colleague", "message": "Background arrival",
            "timestamp": "2026-09-21 12:00:00",
        })
        self.app.processEvents()
        self.assertNotEqual(first.property("lastRevealedMessageId"), "first-new")
        window.show()
        window.requestActivate()
        frame(window)
        self.assertTrue(window.isActive())
        self.assertTrue(first.property("atYEnd"))
        self.assertEqual(first.property("lastRevealedMessageId"), "first-new")
        self.assertEqual(first.property("currentIndex"), -1)
        self.assertEqual(focus_requests.count(), 0)

        frame(window, lambda: first.setProperty("contentY", 300.))
        movements.clear()
        for _ in range(2):
            select_chat(1)
            select_chat(0)
            controller.messageAppendedForConversation.emit("first")
            controller.conversationLoaded.emit()
            frame(window)
        window.hide()
        self.app.processEvents()
        window.show()
        window.requestActivate()
        frame(window)
        self.assertEqual(first.property("currentIndex"), -1)
        self.assertAlmostEqual(first.property("contentY"), 300.)
        self.assertEqual(movements, [])
        self.assertEqual(focus_requests.count(), 0)

        menu = view.findChild(QObject, "chatActionsMenu")
        conversations = view.findChild(QQuickItem, "messagesConversationListView")
        for row, command in ((1, "clear"), (0, "delete")):
            delegate = next(item for item in conversations.property("contentItem").childItems()
                            if item.property("index") == row)
            point = delegate.mapToScene(QPointF(40, 30)).toPoint()
            frame(window, lambda: QTest.mouseClick(window, Qt.RightButton, Qt.NoModifier, point))
            self.assertTrue(menu.property("visible"))
            self.assertEqual(controller.conversationId, ("first", "second")[row])
            actions = menu.property("actions").toVariant()
            self.assertEqual(actions[-1]["command"], command)
            self.assertEqual(actions[0]["enabled"], row == 0)
            QMetaObject.invokeMethod(menu, "close")
            frame(window)
        self.assertEqual(self.warnings, [])

        column = first.findChild(QQuickItem, "messageCardsColumn")
        last_card = next(item for item in column.childItems()
                         if item.property("messageId") == "first-new")
        frame(window, lambda: QMetaObject.invokeMethod(first, "settleAtLatest"))
        frame(window, lambda: window.resize(760, 560))
        frame(window)
        self.assertTrue(first.property("atYEnd"))
        self.assertAlmostEqual(
            last_card.mapToItem(first, QPointF(0, last_card.height())).y(),
            first.height() - 12, delta=1,
        )
        frame(window, lambda: controller.messages.update_record(
            controller.messages.rowCount() - 1,
            {"displayHtml": "More lines<br>after<br>layout<br>changes"},
        ))
        frame(window)
        self.assertAlmostEqual(
            last_card.mapToItem(first, QPointF(0, last_card.height())).y(),
            first.height() - 12, delta=1,
        )

        frame(window, lambda: first.setProperty("contentY", 300.))
        anchor = first.property("viewportAnchor")
        anchor_y = anchor.mapToItem(first, QPointF()).y()
        earlier = controller._message_record({
            "code": "earlier", "login": "artist", "message": "Earlier\nmessage",
            "timestamp": "2026-09-20 12:00:00",
        }, "", "artist")
        frame(window, lambda: controller.messages.replace(
            controller._group_message_records([earlier] + controller.messages.records())))
        frame(window)
        self.assertAlmostEqual(anchor.mapToItem(first, QPointF()).y(), anchor_y, delta=1)
        retained_y = first.property("contentY")
        geometry_changes.clear()
        card_height_changes.clear()
        movements.clear()
        select_chat(1)
        select_chat(0)
        self.assertAlmostEqual(first.property("contentY"), retained_y)
        self.assertEqual(geometry_changes, [])
        self.assertEqual(card_height_changes, [])
        self.assertEqual(movements, [])
        self.assertEqual(self.warnings, [])

    def test_conversation_selection_keeps_list_scroll_position(self):
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "." as App
Item {
    id: harness
    required property var theme
    function switchConversation() { conversations.selectConversation(12) }
    ListModel {
        id: chats
        Component.onCompleted: {
            for (let row = 0; row < 30; ++row)
                chats.append({
                    conversationId: "chat-" + row,
                    title: "Chat " + row,
                    status: "",
                    lastMessage: "Message",
                    lastMessageSummary: "Message",
                    lastMessageLinkedCount: 0,
                    lastSender: "artist",
                    unread: 0,
                    mentionCount: 0,
                    selected: row === 0,
                    avatarUrl: "",
                    initials: "A",
                    participantCount: 2,
                    memberSummary: "",
                    acronym: "C",
                    colorIndex: 0,
                    isPersonalNotes: false
                })
        }
    }
    App.MessagesConversationList {
        id: conversations
        anchors.fill: parent
        theme: harness.theme
        conversationModel: chats
        onConversationSelected: {
            chats.clear()
            for (let row = 0; row < 30; ++row)
                chats.append({
                    conversationId: "chat-" + row,
                    title: "Chat " + row,
                    status: "",
                    lastMessage: "Message",
                    lastMessageSummary: "Message",
                    lastMessageLinkedCount: 0,
                    lastSender: "artist",
                    unread: 0,
                    mentionCount: 0,
                    selected: row === index,
                    avatarUrl: "",
                    initials: "A",
                    participantCount: 2,
                    memberSummary: "",
                    acronym: "C",
                    colorIndex: 0,
                    isPersonalNotes: false
                })
        }
    }
}''', QUrl.fromLocalFile(str(QML / "ConversationScrollTest.qml")))
        window, view = self._show(component, {"theme": self.theme})
        conversations = view.findChild(
            QQuickItem, "messagesConversationListView"
        )
        self.assertIsNotNone(conversations, self.warnings)
        frame(window, lambda: conversations.setProperty("contentY", 480.))
        retained_y = conversations.property("contentY")

        self.assertTrue(QMetaObject.invokeMethod(view, "switchConversation"))
        frame(window)

        self.assertAlmostEqual(conversations.property("contentY"), retained_y)
        self.assertEqual(self.warnings, [])

    def test_notes_scroll_is_restored_after_context_change_and_reopen(self):
        model = RecordListModel(("body",), [{"body": str(i)} for i in range(100)])
        self.engine.rootContext().setContextProperty("historyModel", model)
        component = QQmlComponent(self.engine)
        component.setData(b'''import QtQuick
import "." as App
Item {
    id: host
    property alias context: context
    property bool presented: true
    QtObject {
        id: context
        property var selectedObject: ({searchKey: "asset-a"})
        property string process: "publish"
        property bool loading: false
        property bool hasTarget: true
        signal stateChanged()
    }
    ListView {
        id: history
        objectName: "history"
        anchors.fill: parent
        model: historyModel
        delegate: Rectangle { width: history.width; height: 40 }
    }
    App.NotesTimelinePosition {
        view: history
        controller: context
        model: historyModel
        presented: host.presented
    }
}''', QUrl.fromLocalFile(str(QML / "NotePositionTest.qml")))
        window, view = self._show(component, {})
        history = view.findChild(QQuickItem, "history")
        frame(window, lambda: history.setProperty("contentY", 600.))
        context = view.property("context")
        frame(window, lambda: context.setProperty("selectedObject", {"searchKey": "asset-b"}))
        frame(window, lambda: history.setProperty("contentY", 300.))
        frame(window, lambda: context.setProperty("selectedObject", {"searchKey": "asset-a"}))
        self.assertAlmostEqual(history.property("contentY"), 600.)
        frame(window, lambda: view.setProperty("presented", False))
        frame(window, lambda: view.setProperty("presented", True))
        self.assertAlmostEqual(history.property("contentY"), 600.)
        self.assertEqual(self.warnings, [])

    def test_only_primary_workspaces_stay_in_native_window_model(self):
        source = FloatingWindowModel({})
        proxy = VisibleFloatingWindowModel(source)
        source.show_window("messages")
        source.show_window("help")
        self.assertEqual(proxy.rowCount(), 2)
        source.close_window("messages")
        source.close_window("help")
        proxy._removal_timer.stop()
        proxy._release_hidden_rows()
        self.assertEqual(proxy.rowCount(), 1)
        self.assertEqual(proxy.index(0, 0).data(FloatingWindowModel.IdRole), "messages")
