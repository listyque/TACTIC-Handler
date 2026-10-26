"""Actual Frame list virtualization, stable editor identity and font units."""

import json
from pathlib import Path
from time import perf_counter
import unittest

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, QUrl, Qt
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests import test_sidebar_editor_qml as sidebar_fixture

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class FramePlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        self.component = QQmlComponent(self.engine)
        source = """
import QtQuick
import QtQuick.Controls
import "QML" as TH
import "QML/tactic_frame" as Frame
import "QML/tactic_frame/core/frame.mjs" as Contract
import "QML/tactic_frame/controls/lists/tree.ui.mjs" as ListControls
ApplicationWindow {
    id: window
    visible: true; width: 640; height: 360
    property var rows: []
    property var lastSource: null
    property string lastCommand: ""
    function showAction() {
        view.describeRow = function(list, record) {
            return {nodes:[Contract.node('Box','probeBox',Contract.rect(0,0,80,40), {
                children:[Contract.button('probeButton',Contract.rect(0,0,76,36), 'Probe', '', {type:'probe'}, true)]
            })]};
        };
        populate(1);
    }
    function showRowActions() {
        view.describeRow = function(list, record) {
            return {nodes:[
                ListControls.listAction('rowPrimary', Contract.rect(0,0,300,36), 'Select', '', {type:'select'}),
                ListControls.listAction('rowMenu', Contract.rect(300,0,36,36), 'Menu', '', {type:'menu'}, true, {revealOnRowInteraction:true})
            ]};
        };
        populate(1);
    }
    TH.Theme { id: palette; dark: true }
    function populate(count) {
        const next=[];
        for(let index=0;index<count;index++) next.push({id:String(index), text:'Draft '+index});
        rows=next;
    }
    function reverse() { rows=rows.slice().reverse(); }
    function focus(name) { return view.focusControl(name); }
    function blur() { outsideFocus.forceActiveFocus(); }
    Item { id: outsideFocus }
    function edit(action) {
        rows=rows.map(row=>row.id===action.id ? {id:row.id,text:action.value} : row);
    }
    Frame.FrameView {
        id: view; anchors.fill: parent; theme: palette
        models: ({rows: window.rows})
        scene: ({nodes:[Contract.node('List','arrayRows',Contract.rect(0,0,width,height), {
            source:'rows',keyField:'id',rowHeight:40,scrollbarId:'arrayScroll'
        })]})
        describeRow: function(list, record) {
            return {nodes:[Contract.node('Field','edit_'+record.id,Contract.rect(0,0,300,36), {
                text:record.text, action:{type:'edit',id:record.id}
            })]};
        }
        onEvent: (action, source) => {
            window.lastSource = source;
            window.lastCommand = action.type;
            if (action.type === 'edit') window.edit(action);
        }
    }
}
""".replace("QML", QML.as_uri())
        self.component.setData(source.encode(), QUrl())
        self.assertTrue(
            self.component.isReady(),
            [error.toString() for error in self.component.errors()],
        )
        self.window = self.component.create()
        self.assertIsNotNone(self.window)
        self.addCleanup(self.close)
        frame(self.window)

    def close(self):
        self.window.close()
        self.window.deleteLater()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def evaluate(self, expression):
        call = QQmlExpression(self.engine.rootContext(), self.window, expression)
        result, undefined = call.evaluate()
        self.assertFalse(call.hasError(), call.error().toString())
        return result.toVariant() if hasattr(result, "toVariant") else result

    def item(self, name):
        return next(
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem()
            )
            if item.objectName() == name
        )

    def test_large_list_updates_only_visible_rows_and_clamps_after_clear(self):
        self.evaluate("populate(10000)")
        frame(self.window)
        view = self.item("arrayRows")
        self.assertEqual(view.property("count"), 10000)
        start = perf_counter()
        self.evaluate("reverse()")
        frame(self.window)
        self.assertLess(
            perf_counter() - start,
            1.0,
            "A viewport update must not reconcile all record pairs",
        )
        editors = [
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(view)
            if item.objectName().startswith("edit_")
        ]
        self.assertLess(len(editors), 30)
        view.setProperty("contentY", 200000)
        frame(self.window)
        self.evaluate("rows=[]")
        frame(self.window)
        self.assertEqual(view.property("count"), 0)
        self.assertEqual(view.property("contentY"), 0)
        self.evaluate("populate(20)")
        frame(self.window)
        self.assertTrue(self.item("edit_0").isVisible())
        self.assertEqual(self.warnings, [])

    def test_reverse_keeps_editor_focus_selection_draft_and_identity(self):
        self.evaluate("populate(1000)")
        frame(self.window)
        editor = self.item("edit_0")
        editor.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_End)
        QTest.keyClick(self.window, Qt.Key_X)
        frame(self.window)
        self.assertEqual(editor.property("text"), "Draft 0x")
        editor.setProperty("cursorPosition", 2)
        QTest.keyClick(self.window, Qt.Key_Right, Qt.ShiftModifier)
        selection = editor.property("selectedText")
        cursor = editor.property("cursorPosition")
        self.evaluate("reverse()")
        frame(self.window)
        self.assertIs(self.item("edit_0"), editor)
        self.assertTrue(editor.property("activeFocus"))
        self.assertEqual(editor.property("selectedText"), selection)
        self.assertEqual(editor.property("cursorPosition"), cursor)
        self.assertEqual(editor.property("text"), "Draft 0x")
        self.assertEqual(editor.property("font").pixelSize(), 13)
        self.assertEqual(self.warnings, [])

    def test_ime_preedit_survives_sort_until_explicit_commit(self):
        self.evaluate("populate(1000)")
        frame(self.window)
        editor = self.item("edit_0")
        editor.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_End)
        QCoreApplication.sendEvent(editor, QInputMethodEvent("Ж", []))
        self.assertTrue(editor.property("inputMethodComposing"))
        self.assertEqual(self.evaluate("rows[0].text"), "Draft 0")
        self.evaluate("reverse()")
        frame(self.window)
        self.assertIs(self.item("edit_0"), editor)
        self.assertTrue(editor.property("inputMethodComposing"))
        commit = QInputMethodEvent()
        commit.setCommitString("Ж")
        QCoreApplication.sendEvent(editor, commit)
        frame(self.window)
        self.assertEqual(editor.property("text"), "Draft 0Ж")
        self.assertEqual(
            self.evaluate("rows.find(row => row.id === '0').text"), "Draft 0Ж"
        )
        self.assertEqual(self.warnings, [])

    def test_nested_list_button_preserves_the_actual_event_source(self):
        self.evaluate("showAction()")
        frame(self.window)
        button = self.item("probeButton")
        point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, point.toPoint())
        frame(self.window)
        self.assertEqual(self.window.property("lastCommand"), "probe")
        self.assertEqual(self.window.property("lastSource"), button)
        self.assertEqual(self.warnings, [])

    def test_control_names_are_not_limited_to_css_identifiers(self):
        identity = 'id/"[]:ю'
        self.evaluate("rows=" + json.dumps([dict(id=identity, text="Named editor")]))
        frame(self.window)
        self.assertTrue(self.evaluate("focus(" + json.dumps("edit_" + identity) + ")"))
        self.assertTrue(self.item("edit_" + identity).property("activeFocus"))
        self.assertEqual(self.warnings, [])

    def test_secondary_row_action_reveals_for_hover_focus_and_no_hover(self):
        hints = self.app.styleHints()
        previous = hints.useHoverEffects()
        self.addCleanup(hints.setUseHoverEffects, previous)
        hints.setUseHoverEffects(True)
        self.evaluate('showRowActions()')
        self.window.requestActivate()
        QTest.mouseMove(self.window, QPoint(600, 300))
        frame(self.window)
        menu = self.item('rowMenu')
        def opacity():
            result, current = 1, menu
            while current:
                result *= current.opacity()
                current = current.parentItem()
            return result
        self.assertEqual(opacity(), 0)
        QTest.mouseMove(self.window, QPoint(100, 20))
        frame(self.window)
        self.assertEqual(opacity(), 1)
        self.item('rowPrimary').forceActiveFocus()
        QTest.mouseMove(self.window, QPoint(600, 300))
        frame(self.window)
        self.assertEqual(opacity(), 1)
        self.evaluate('blur()')
        QTest.qWait(200)
        frame(self.window)
        self.assertEqual(opacity(), 0)
        hints.setUseHoverEffects(False)
        frame(self.window)
        self.assertEqual(opacity(), 1)
        self.assertEqual(self.warnings, [])

    def test_removing_the_edited_row_never_writes_to_its_successor(self):
        self.evaluate("populate(10)")
        frame(self.window)
        self.item("edit_0").forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_End)
        QTest.keyClick(self.window, Qt.Key_X)
        frame(self.window)
        self.evaluate("rows=rows.filter(row => row.id !== '0')")
        frame(self.window)
        self.assertEqual(self.evaluate("rows[0].id"), "1")
        self.assertEqual(self.evaluate("rows[0].text"), "Draft 1")
        self.assertFalse(self.evaluate("rows.some(row => row.id === '0')"))
        self.assertEqual(self.warnings, [])


if __name__ == "__main__":
    unittest.main()
