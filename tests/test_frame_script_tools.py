"""Exercise real native tool input against stateful private document owners."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
from PySide6.QtCore import QCoreApplication, QEvent, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from tests.profile_ui_responsiveness import frame
from tests.qt_application import gui_test_application

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class ScriptToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.engine = QQmlEngine()
        self.components = []
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        self.windows = []
        self.objects = []
        self.addCleanup(self.close)
        self.theme = self.create(
            QML / "Theme.qml",
            {
                "dark": True,
                "popupAnimationsEnabled": False,
                "clickAnimationsEnabled": False,
            },
        )
        self.owner = self.inline("""import QtQml
QtObject {
    property string current_project_code: "private"
    property string current_section_key: "private/assets"
    property string current_page_key: "tab"
    property var selected_result_node_ids: ["node-a", "node-b"]
    property var selected_result_records: [
        {nodeId: "node-a", title: "Asset A", code: "A", searchKey: "private/assets?code=A", status: "ready", type: "asset"},
        {nodeId: "node-b", title: "Asset B", code: "B", searchKey: "private/assets?code=B", status: "ready", type: "asset"}
    ]
    property int selected_result_count: selected_result_records.length
    property var selected_result_fields: ["name", "description"]
    property bool loading: false
    property var saved: []
    property var bulk: []
    signal selected_node_changed()
    signal project_changed(string code, string title)
    signal section_state_changed()
    function editable_result_field_records(nodeId) {
        const rows = [{fieldName: "name", fieldLabel: "Name", fieldValue: nodeId === "node-a" ? "Asset A" : "Asset B"}];
        for (let index = 0; index < 200; index++) rows.push({fieldName: "field_" + index, fieldLabel: "Field " + index, fieldValue: String(index)});
        return rows;
    }
    function update_selected_item_fields(nodeId, changes) { saved = saved.concat([{nodeId, changes}]); }
    function update_selected_items(field, value) { bulk = bulk.concat([{field, value, ids: selected_result_node_ids.slice()}]); }
}""")
        self.columns = self.inline("""import QtQml
QtObject {
    property int beginCalls: 0
    signal applied()
    function begin_session() { beginCalls++; }
    function order_field_records(rows) { return rows; }
}""")
        self.engine.rootContext().setContextProperty("appController", self.owner)
        self.engine.rootContext().setContextProperty(
            "columnsEditorController", self.columns
        )

    def close(self):
        for window in self.windows:
            window.close()
            window.deleteLater()
        for obj in self.objects:
            obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def inline(self, source, properties=None):
        component = QQmlComponent(self.engine)
        component.setData(source.encode(), QUrl())
        self.components.append(component)
        obj = component.createWithInitialProperties(properties or {})
        self.assertIsNotNone(obj, [error.toString() for error in component.errors()])
        self.objects.append(obj)
        return obj

    def create(self, path, properties):
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(path)))
        self.components.append(component)
        obj = component.createWithInitialProperties(properties)
        self.assertIsNotNone(obj, [error.toString() for error in component.errors()])
        self.objects.append(obj)
        return obj

    def show(self, name):
        view = self.create(
            QML / "features/tools" / name,
            {"theme": self.theme, "width": 900, "height": 650},
        )
        self.assertIsInstance(view, QQuickItem)
        window = QQuickWindow()
        window.resize(900, 650)
        view.setParentItem(window.contentItem())
        self.windows.append(window)
        window.show()
        frame(window)
        return window, view

    def item(self, view, name):
        items = [view]
        for item in items:
            items.extend(item.childItems())
            if item.objectName() == name:
                loaded = item.property("item")
                return loaded if isinstance(loaded, QQuickItem) else item
        self.fail("Missing control " + name + "\n" + "\n".join(self.warnings))

    def click(self, window, item):
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(window, Qt.LeftButton, pos=point.toPoint())
        frame(window)

    def fill(self, window, item, text):
        self.click(window, item)
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        for char in text:
            QTest.keyClick(window, char)
        frame(window)

    @staticmethod
    def value(obj, name):
        value = obj.property(name)
        return value.toVariant() if hasattr(value, "toVariant") else value

    def test_database_editor_input_selection_save_bulk_and_virtual_draft(self):
        window, view = self.show("DatabaseEditorView.qml")
        self.fill(window, self.item(view, "databaseFieldValue_name"), "Edited A")
        self.assertEqual(self.value(view, "pendingChanges"), {"name": "Edited A"})
        self.assertEqual(view.property("dirtyCount"), 1)
        fields = self.item(view, "databaseFields")
        fields.setProperty("contentY", 4000)
        frame(window)
        fields.setProperty("contentY", 0)
        frame(window)
        self.assertEqual(
            self.item(view, "databaseFieldValue_name").property("text"), "Edited A"
        )
        self.click(window, self.item(view, "databaseSave"))
        self.assertEqual(
            self.value(self.owner, "saved"),
            [{"nodeId": "node-a", "changes": {"name": "Edited A"}}],
        )
        self.click(window, self.item(view, "databaseObjectRow_node-b"))
        self.assertEqual(self.value(view, "activeRecord")["nodeId"], "node-b")
        self.fill(window, self.item(view, "databaseFieldValue_name"), "Edited B")
        self.click(window, self.item(view, "databaseSave"))
        self.assertEqual(
            self.value(self.owner, "saved")[-1],
            {"nodeId": "node-b", "changes": {"name": "Edited B"}},
        )
        self.fill(window, self.item(view, "databaseBulkValue"), "Shared name")
        self.click(window, self.item(view, "databaseBulkApply"))
        self.assertEqual(
            self.value(self.owner, "bulk"),
            [{"field": "name", "value": "Shared name", "ids": ["node-a", "node-b"]}],
        )
        self.owner.setProperty("loading", True)
        frame(window)
        self.assertFalse(self.item(view, "databaseSave").isEnabled())
        self.assertFalse(self.item(view, "databaseBulkApply").isEnabled())
        self.assertEqual(self.warnings, [])

    def test_array_list_can_clear_after_window_resize(self):
        window = self.inline(
            '''import QtQuick
import QtQuick.Window
import "'''
            + (QML / "tactic_frame").as_uri()
            + '''" as Frame
import "'''
            + (QML / "tactic_frame/core/frame.mjs").as_uri()
            + """" as UI
Window {
    id: root
    required property var theme
    property var rows: []
    width:640; height:580; visible:true
    Frame.FrameView {
        anchors.fill:parent
        theme:root.theme
        models:({rows:root.rows})
        scene:({nodes:[UI.node("List","arrayClearRows",UI.rect(0,0,width,height-48),{source:"rows",keyField:"id",fields:["id","title"],rowHeight:38}),UI.button("clearArrayRows",UI.rect(16,height-42,110,32),"Clear","clear",{type:"clear"},root.rows.length>0)]})
        describeRow:(list,record)=>({nodes:[UI.label("clearRow_"+record.id,UI.rect(8,0,list.width-24,34),record.title)]})
        onEvent:action=>root.rows=[]
    }
}""",
            {
                "theme": self.theme,
                "rows": [
                    {"id": str(index), "title": "Row " + str(index)}
                    for index in range(100)
                ],
            },
        )
        frame(window)
        window.resize(420, 400)
        frame(window)
        self.click(window, self.item(window.contentItem(), "clearArrayRows"))
        self.assertEqual(self.value(window, "rows"), [])
        self.assertEqual(self.warnings, [])

    def test_native_number_accepts_grouped_russian_input(self):
        from PySide6.QtGui import QInputMethodEvent

        spin = self.create(
            QML / "controls/SpinBox.qml",
            {
                "theme": self.theme,
                "width": 240,
                "height": 44,
                "language": "ru",
                "decimals": 2,
                "from": -999999,
                "to": 999999,
            },
        )
        window = QQuickWindow()
        self.windows.append(window)
        window.resize(300, 80)
        spin.setParentItem(window.contentItem())
        window.show()
        frame(window)
        field = self.item(spin, "spinBoxTextInput")
        self.click(window, field)
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        event = QInputMethodEvent()
        event.setCommitString("1\u202f234,50")
        self.app.sendEvent(field, event)
        QTest.keyClick(window, Qt.Key_Return)
        frame(window)
        self.assertEqual(spin.property("value"), 123450)
        self.assertFalse(spin.property("errorState"))
        self.assertEqual(self.warnings, [])

    def test_script_created_frame_tool_input_preview_clear_and_release(self):
        from side_tools.frame_tool.showcase import _windows, create_window

        parent = self.inline("""import QtQuick.Window
Window {
    property bool dark: true
    property string applicationThemeStyleName: "md3"
    property color applicationThemeBaseColor: "#292d30"
    property color applicationThemeAccentColor: "#78a6c4"
}""")
        records = [
            {"id": "asset-" + str(index), "title": "Asset " + str(index)}
            for index in range(100)
        ]
        window = create_window(self.engine, parent, records)
        frame(window)
        self.fill(window, self.item(window.contentItem(), "exampleName"), "My batch")
        self.click(window, self.item(window.contentItem(), "exampleBuild"))
        import json

        self.assertEqual(
            json.loads(window.property("preview")),
            {"name": "My batch", "ids": [row["id"] for row in records]},
        )
        self.assertTrue(self.item(window.contentItem(), "exampleScrollBar").isVisible())
        QTest.mouseMove(window, QPointF(2, 2).toPoint())
        window.resize(420, 400)
        frame(window)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        frame(window)
        self.click(window, self.item(window.contentItem(), "exampleClear"))
        self.assertFalse(self.item(window.contentItem(), "exampleBuild").isEnabled())
        window.hide()
        self.app.processEvents()
        self.assertEqual(len(_windows), 1)
        window.show()
        frame(window)
        window.close()
        QTest.qWait(10)
        self.assertEqual(_windows, [])
        self.assertEqual(self.warnings, [])

    def test_handler_server_real_input_failure_recovery_and_shutdown(self):
        from tests.test_handler_server_controller import HandlerServerControllerTests

        fixture = HandlerServerControllerTests()
        fixture.setUpClass()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        controller = fixture.controller
        context = self.engine.rootContext()
        for name, value in {
            "handlerServerController": controller,
            "handlerClientModel": controller.clients,
            "handlerCapabilityModel": controller.capabilities,
            "handlerResultModel": controller.results,
        }.items():
            context.setContextProperty(name, value)
        window, view = self.show("HandlerServerView.qml")
        self.click(window, self.item(view, "handlerStart"))
        fixture._wait(lambda: controller.state == "running")
        fixture._wait(lambda: self.item(view, "handlerDemo").isEnabled())
        self.click(window, self.item(view, "handlerDemo"))
        fixture._wait(lambda: controller.clients.count() == 1)
        frame(window)
        self.click(window, self.item(view, "handlerClientSurface"))
        self.assertEqual(controller.selectedClient, "demo-maya")
        fixture._wait(
            lambda: len(self.value(self.item(view, "handlerCommand"), "model")) > 0
        )
        choice = self.item(view, "handlerCommand")
        options = self.value(choice, "model")
        target = next(
            index for index, row in enumerate(options) if row["value"] == "ping"
        )
        choice.forceActiveFocus()
        for _ in range((target - choice.property("currentIndex")) % len(options)):
            QTest.keyClick(window, Qt.Key_Down)
        frame(window)
        self.fill(window, self.item(view, "handlerPayload"), "{bad")
        self.click(window, self.item(view, "handlerSend"))
        self.assertTrue(controller.error)
        self.fill(window, self.item(view, "handlerPayload"), '{"value":7}')
        self.click(window, self.item(view, "handlerSend"))
        fixture._wait(
            lambda: any(
                row.get("status") == "completed" for row in controller.results.records()
            )
        )
        self.assertFalse(controller.error)
        controller.stop_demo()
        controller.stop_server()
        fixture._wait(lambda: controller.state == "stopped")
        self.assertEqual(self.warnings, [])

    def test_database_batch_uses_exact_selection_and_disables_busy_writes(self):
        window, view = self.show("DatabaseBatchEditorView.qml")
        self.fill(window, self.item(view, "databaseBulkValue"), "Batch name")
        self.click(window, self.item(view, "databaseBulkApply"))
        self.assertEqual(
            self.value(self.owner, "bulk"),
            [{"field": "name", "value": "Batch name", "ids": ["node-a", "node-b"]}],
        )
        self.owner.setProperty("loading", True)
        frame(window)
        self.assertFalse(self.item(view, "databaseBulkApply").isEnabled())
        self.assertEqual(self.warnings, [])

    def test_database_candidate_keeps_existing_dock_session_contract(self):
        from tests import test_retained_ui as retained

        with tempfile.TemporaryDirectory(prefix="database-candidate-") as temporary:
            folder = Path(temporary)
            native = QUrl.fromLocalFile(str(QML)).toString()
            for name, target in [
                ("Theme", native),
                ("DatabaseEditorView", native + "/features/tools"),
            ]:
                (folder / (name + ".qml")).write_text(
                    'import QtQuick\nimport "'
                    + target
                    + '" as Native\nNative.'
                    + name
                    + " {}\n",
                    encoding="utf-8",
                )
            with patch.object(retained, "QML", folder):
                suite = unittest.TestSuite(
                    [
                        retained.RetainedUiTests(
                            "test_database_editor_retains_dirty_state_for_the_same_context"
                        )
                    ]
                )
                result = unittest.TestResult()
                suite.run(result)
                self.assertTrue(result.wasSuccessful(), result.errors + result.failures)


if __name__ == "__main__":
    unittest.main()
