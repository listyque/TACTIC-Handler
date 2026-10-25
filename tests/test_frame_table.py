"""Real input for the shared table editor, summary and column drag lifecycle."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

import unittest
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QUrl, Qt, QMetaObject
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.test_columns_table_view import _TableController, _TableColumns, _visual_items
from tests.profile_ui_responsiveness import frame
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode
from thlib import tactic_table_widgets

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class FrameTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def create(self, name, values, width=360, height=120, context=None):
        engine = QQmlEngine()
        for key,value in (context or {}).items():
            engine.rootContext().setContextProperty(key,value)
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / "Theme.qml")))
        theme = component.createWithInitialProperties({"dark": True})
        theme.setParent(engine)
        theme_component = component
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / name)))
        view = component.createWithInitialProperties(
            dict(theme=theme, width=width, height=height, **values)
        )
        self.assertIsNotNone(view, [error.toString() for error in component.errors()])
        window = QQuickWindow()
        view.setParentItem(window.contentItem())
        window.resize(width, height)
        window.show()
        frame(window)
        self.addCleanup(
            self.close,
            window,
            view,
            engine,
            warnings,
            [component, theme_component, theme, values, context],
        )
        return window, view

    def close(self, window, view, engine, warnings, owners):
        window.close()
        view.setParentItem(None)
        view.deleteLater()
        window.deleteLater()
        self.app.processEvents()
        engine.deleteLater()
        self.assertEqual(warnings, [])

    def item(self, view, name):
        return next(item for item in _visual_items(view) if item.objectName() == name)

    def click(self, window, item):
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
        frame(window)

    def test_inline_ime_commits_latest_text_once(self):
        window, view = self.create(
            "features/table/ValueEditor.qml",
            dict(
                mode="text",
                descriptor=dict(
                    fieldName="Name", fieldValue="Old name", fieldOptions=[]
                ),
            ),
            height=44,
        )
        saved = []
        view.saved.connect(saved.append)
        field = self.item(view, "tableInlineValue")
        self.click(window, field)
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        event = QInputMethodEvent()
        event.setCommitString("Модель")
        QGuiApplication.sendEvent(field, event)
        QTest.keyClick(window, Qt.Key_Return)
        frame(window)
        self.assertEqual(saved, ["Модель"])

    def test_tags_keep_draft_until_save_and_remove_without_writing(self):
        window, view = self.create(
            "features/table/ValueEditor.qml",
            dict(mode="tags", descriptor=dict(fieldName="keywords", fieldValue="robot, body",
                 fieldOptions=[dict(value="rig", label="rig")])), height=240)
        saved = []
        view.saved.connect(saved.append)
        combo = self.item(view, "tableInlineValue")
        combo.forceActiveFocus()
        frame(window)
        field = window.activeFocusItem()
        event = QInputMethodEvent()
        event.setCommitString("rig, robot")
        QGuiApplication.sendEvent(field, event)
        QTest.keyClick(window, Qt.Key_Return)
        frame(window)
        self.assertEqual(saved, [])
        self.assertEqual(view.property("value"), "robot, body, rig")
        self.click(window, self.item(view, "tableInlineTag_1"))
        self.assertEqual(view.property("value"), "robot, rig")
        self.assertEqual(saved, [])
        combo = self.item(view, "tableInlineValue")
        combo.forceActiveFocus()
        frame(window)
        event = QInputMethodEvent()
        event.setCommitString(" final ")
        QGuiApplication.sendEvent(window.activeFocusItem(), event)
        self.click(window, self.item(view, "tableInlineSave"))
        self.assertEqual(saved, ["robot, rig, final"])

    def test_service_actions_use_first_click_and_preserve_configured_view(self):
        controller = _TableController()
        window, view = self.create('features/table/ServiceCell.qml',
            dict(controller=controller, services=None, administration=None, nodeId='asset',
                 cell={'text':'','actions':[{'name':'edit','label':'Edit','icon':'edit','view':'edit_review'}]}),
            width=160, height=58)
        self.click(window, self.item(view,'tableServiceAction_0'))
        self.assertEqual(controller.table_widget_actions[-1],
            ('edit','asset',{'text':'','actions':[{'name':'edit','label':'Edit','icon':'edit','view':'edit_review'}], 'actionView':'edit_review'}))
        view.setProperty('editable',False)
        frame(window)
        self.click(window,self.item(view,'tableServiceAction_0'))
        self.assertEqual(len(controller.table_widget_actions),1)

    def test_boolean_uses_first_pointer_click(self):
        window, view = self.create(
            "features/table/ValueEditor.qml",
            dict(
                mode="bool",
                descriptor=dict(fieldName="Enabled", fieldValue=False, fieldOptions=[]),
            ),
            height=44,
        )
        saved = []
        view.saved.connect(saved.append)
        self.click(window, self.item(view, "tableInlineValue"))
        self.assertEqual(saved, [True])

    def test_multiline_enter_is_newline_until_save(self):
        window, view = self.create(
            "features/table/ValueEditor.qml",
            dict(
                mode="multiline",
                descriptor=dict(
                    fieldName="Description", fieldValue="Line", fieldOptions=[]
                ),
            ),
            height=336,
        )
        saved = []
        view.saved.connect(saved.append)
        field = self.item(view, "tableInlineValue")
        self.click(window, field)
        QTest.keyClick(window, Qt.Key_End, Qt.ControlModifier)
        QTest.keyClick(window, Qt.Key_Return)
        self.assertEqual(saved, [])
        self.click(window, self.item(view, "tableInlineSave"))
        self.assertEqual(saved, ["Line\n"])

    def test_dates_colors_and_multi_values_have_explicit_save(self):
        for mode, value, options in [
            ("date", "2030-05-01", []),
            ("datetime", "2030-05-01T12:30", []),
            ("color", "#607d8b", []),
            ("multi", ["one"], [dict(value="one", label="One")]),
        ]:
            with self.subTest(mode=mode):
                window, view = self.create(
                    "features/table/ValueEditor.qml",
                    dict(
                        mode=mode,
                        descriptor=dict(
                            fieldName="Value", fieldValue=value, fieldOptions=options
                        ),
                    ),
                    height=100,
                )
                saved = []
                view.saved.connect(saved.append)
                self.click(window, self.item(view, "tableInlineSave"))
                self.assertEqual(saved, [value])

    def test_task_summary_opens_the_exact_task_on_first_click(self):
        controller = _TableController()
        record = dict(
            process="model",
            context="model/main",
            taskCode="TASK01",
            status="Pending",
            processColor="#607d8b",
        )
        window, view = self.create(
            "features/table/TaskSummaryCell.qml",
            dict(controller=controller, nodeId="asset", records=[record]),
            width=180,
            height=58,
        )
        self.click(window, self.item(view, "tableTaskSummary_0"))
        self.assertEqual(
            controller.task_details, [("asset", "tasks", "model", "TASK01")]
        )

    def test_cancelled_header_drag_never_saves_order(self):
        controller, columns, model = (
            _TableController(),
            _TableColumns(),
            WorkspaceItemModel(),
        )
        model.replace_nodes(
            [
                WorkspaceNode(
                    node_id="asset",
                    node_type="sobject",
                    search_key="asset",
                    code="A",
                    title="Asset",
                )
            ]
        )
        window, table = self.create(
            "SearchResultTable.qml",
            dict(controller=controller, columnsController=columns, resultModel=model),
            width=1000,
            height=200,
        )
        area = self.item(table, "tableColumnContextArea_code")
        start = area.mapToScene(QPointF(20, 16)).toPoint()
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, start + QPointF(45, 0).toPoint())
        frame(window)
        header = table.findChild(QObject, "searchResultTableHeader")
        self.assertGreaterEqual(header.property("draggedColumn"), 0)
        area.ungrabMouse()
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, start)
        frame(window)
        self.assertEqual(header.property("draggedColumn"), -1)
        self.assertEqual(columns.move_calls, [])

    def test_selection_count_excludes_group_rows(self):
        model = WorkspaceItemModel()
        model.replace_nodes(
            [
                WorkspaceNode(
                    node_id="group",
                    node_type="group",
                    search_key="",
                    code="",
                    title="Group",
                ),
                WorkspaceNode(
                    node_id="one",
                    node_type="sobject",
                    search_key="one",
                    code="ONE",
                    title="One",
                    parent_id="group",
                ),
                WorkspaceNode(
                    node_id="two",
                    node_type="sobject",
                    search_key="two",
                    code="TWO",
                    title="Two",
                    parent_id="group",
                ),
            ]
        )
        self.assertEqual(model.selectableCount, 2)

    def test_selection_count_excludes_loaded_hidden_children(self):
        child = WorkspaceNode(
            node_id="child",
            node_type="sobject",
            search_key="child",
            code="CHILD",
            title="Child",
            parent_id="root",
        )
        root = WorkspaceNode(
            node_id="root",
            node_type="sobject",
            search_key="root",
            code="ROOT",
            title="Root",
            children=[child],
            expanded=False,
        )
        model = WorkspaceItemModel()
        model.replace_nodes([root])
        model.show_table_rows()
        self.assertIsNotNone(model.node_for("child"))
        self.assertEqual(model.selectableCount, 1)

    def test_table_values_are_plain_text(self):
        text = "User <b>value</b>\nSecond line"
        window, view = self.create(
            "TacticTableCellDisplay.qml",
            dict(
                controller=None,
                columnsController=None,
                userModel=None,
                nodeId="row",
                kind="text",
                cell={"text": text, "multiline": True},
                textValue=text,
                columnIndex=1,
                previewActive=False,
                previewUrl="",
                previewRevealed=False,
                title="Value",
                accent="#78a6c4",
                comments=0,
                tasks=0,
                displayOptions={},
            ),
        )
        label = next(
            item
            for item in _visual_items(view)
            if item.property("text") == text
            and item.metaObject().indexOfProperty("textFormat") >= 0
        )
        expression = QQmlExpression(
            QQmlEngine.contextForObject(label), label, "Number(textFormat) === 0"
        )
        result, undefined = expression.evaluate()
        self.assertFalse(expression.hasError(), expression.error().toString())
        self.assertFalse(undefined)
        self.assertTrue(result)
        self.assertEqual(label.property("lineCount"), 2)

    def test_vfx_text_input_uses_the_real_native_keyboard_editor(self):
        from thlib.ui.sobject_editor import SObjectEditorController
        from tests.test_sobject_editor import _EditorStype
        descriptor = SObjectEditorController.describe_field(
            _EditorStype({'name': 'varchar'}), {},
            dict(name='name', class_name='tactic.ui.input.text_input_wdg.TextInputWdg',
                 __display_values__=['Original'], kwargs={}, action_options={}), mode='insert')
        window, view = self.create('SObjectValueEditor.qml',
            dict(fieldType=descriptor['fieldType'], fieldValue=descriptor['fieldValue'], fieldOptions=[]),
            width=360, height=48)
        edited = []
        view.valueEdited.connect(edited.append)
        field = self.item(view, 'sobjectValueTextEditor')
        self.click(window, field)
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        QTest.keyClick(window, Qt.Key_Z)
        frame(window)
        self.assertEqual(edited[-1], 'z')
        self.assertEqual(field.property('text'), 'z')

    def test_embedded_message_uses_plain_text_and_shared_progress(self):
        from thlib.ui.workspace_models.records import RecordListModel
        text = '<b>Literal message</b>'
        window, view = self.create(
            "TacticTableCellDisplay.qml",
            dict(controller=_TableController(), columnsController=_TableColumns(),
                 userModel=RecordListModel(["login", "displayName", "avatarUrl"]), nodeId="asset", kind="message",
                 cell={"text": text, "author": "artist", "messageLabel": "Note added", "progress": 37},
                 textValue=text, columnIndex=1, previewActive=False, previewUrl="",
                 previewRevealed=False, title="Message", accent="#78a6c4", comments=0,
                 tasks=0, displayOptions={}),
        )
        body = self.item(view, "tableMessageBody")
        self.assertEqual(body.property("text"), text)
        self.click(window, body)
        track = self.item(view, "tableMessageTrack")
        fill = self.item(view, "tableMessageProgress")
        self.assertAlmostEqual(fill.width() / track.width(), 0.37, places=4)
        expression = QQmlExpression(QQmlEngine.contextForObject(body), body, "Number(textFormat) === 0")
        self.assertTrue(expression.evaluate()[0])

    def test_legacy_task_assignment_and_dates_respect_cell_options(self):
        from thlib.ui.workspace_models.records import RecordListModel
        window, view = self.create(
            "TacticTaskCards.qml",
            dict(controller=_TableController(), columnsController=_TableColumns(),
                 userModel=RecordListModel(["login", "displayName", "avatarUrl"]), nodeId="asset", records=[
                     {"taskCode":"L02_TASK", "process":"model", "assigned":"admin",
                      "editAssigned":False, "editDates":False, "simpleDates":True,
                      "bidStart":"2030-01-01", "bidEnd":"2030-01-03"}]),
            height=90,
        )
        assignee = self.item(view, "tableTaskAssignee_0")
        self.assertFalse(assignee.property("editingAllowed"))
        self.click(window, assignee)
        self.assertFalse(any(item.objectName() == "tableTaskAssigneeEditor_0" for item in _visual_items(view)))
        self.click(window, self.item(view, "tableTaskDates_0"))
        self.assertFalse(any(item.objectName() == "tableTaskDateEditor" for item in _visual_items(view)))

    def test_empty_configured_note_context_opens_on_first_click(self):
        from thlib.ui.workspace_models.records import RecordListModel
        controller = _TableController()
        window, view = self.create(
            "TacticTableCellDisplay.qml",
            dict(controller=controller, columnsController=_TableColumns(),
                 userModel=RecordListModel(["login"]), nodeId="asset", kind="notes",
                 cell={"text":"0", "count":0, "processes":[{"process":"review", "label":"Review phase", "count":0}]},
                 textValue="0", columnIndex=1, previewActive=False, previewUrl="",
                 previewRevealed=False, title="Notes", accent="#78a6c4", comments=99,
                 tasks=0, displayOptions={}),
        )
        self.click(window, self.item(view, "tableNoteRecord_0"))
        self.assertEqual(controller.process_details, [("asset", "notes", "review")])

    def test_unknown_widget_is_explicitly_unsupported(self):
        widget = tactic_table_widgets.create_widget(
            {"resolvedClass": "custom.UnknownWdg"}
        )
        self.assertEqual(widget.get_cell_kind("boolean"), "unsupported")

    def test_catalogue_and_option_kinds(self):
        import json

        catalog = json.loads(
            (QML / "tactic_frame/features/table/widgets.json").read_text(
                encoding="utf-8"
            )
        )
        aliases = [alias for entry in catalog for alias in entry["aliases"] if alias]
        self.assertEqual(len(aliases), len(set(aliases)))
        self.assertEqual(
            set(aliases), set(tactic_table_widgets.table_classes["tactic"])
        )
        self.assertTrue(
            all(
                isinstance(name, str)
                for name in tactic_table_widgets.table_classes["handler"]
            )
        )
        for alias in aliases:
            widget = tactic_table_widgets.create_widget({"displayClass": alias})
            self.assertNotEqual(widget.get_cell_kind(), "unsupported", alias)
        for alias, options, expected in (
            ("tactic.ui.table.FormatElementWdg", {"format": "Checkbox"}, "boolean"),
            ("tactic.ui.table.ExpressionElementWdg", {"mode": "check"}, "check"),
            ("tactic.ui.table.ExpressionElementWdg", {"mode": "boolean"}, "boolean"),
            ("tactic.ui.table.TaskElementWdg", {}, "tasks"),
            ("tactic.ui.table.CheckinButtonElementWdg", {}, "checkin"),
        ):
            widget = tactic_table_widgets.create_widget(
                {"displayClass": alias, "displayOptions": options}
            )
            self.assertEqual(widget.get_cell_kind("boolean"), expected, alias)


if __name__ == "__main__":
    unittest.main()
