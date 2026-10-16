"""Real native input for the shared project chooser and workspace tabs."""

from contextlib import contextmanager
from pathlib import Path
import unittest
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests.test_project_catalog import _Project
import tests.test_sidebar_editor_qml as fixture
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.models import ProjectModel
from thlib.ui.workspace_models.sections import SectionTab, SectionTabModel

ROOT = Path(__file__).resolve().parents[1]


class FrameProjectsTests(unittest.TestCase):
    @contextmanager
    def scene(self, body, model=None):
        app = gui_test_application()
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        for name, value in qml_icon_bindings(ROOT, app).items():
            engine.rootContext().setContextProperty(name, value)
        if model is not None:
            engine.rootContext().setContextProperty("catalog", model)
        source = f'''import QtQuick
import QtQuick.Controls
import "{(ROOT / "thlib/ui/qml").as_uri()}" as TH
import "{(ROOT / "thlib/ui/qml/controls").as_uri()}" as Controls
ApplicationWindow{{id:window;visible:true;width:900;height:800;property int calls:0;TH.Theme{{id:uiTheme;dark:true;popupAnimationsEnabled:false;fadeAnimationsEnabled:false;hoverAnimationsEnabled:false}} {body.replace("theme:theme", "theme:uiTheme")}}}'''
        component = QQmlComponent(engine)
        component.setData(source.encode(), QUrl())
        self.assertTrue(
            component.isReady(), [error.toString() for error in component.errors()]
        )
        window = component.create()
        self.assertIsNotNone(window)
        try:
            frame(window)
            yield window
            self.assertEqual(warnings, [])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    @staticmethod
    def find(window, name):
        return next(
            item
            for item in fixture.SidebarEditorQmlTests.descendants(window.contentItem())
            if item.objectName() == name
        )

    @staticmethod
    def point(item):
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        return QPoint(round(point.x()), round(point.y()))

    def test_filters_keyboard_and_first_mouse_choose(self):
        model = ProjectModel()
        model.replace(
            [
                _Project("one"),
                _Project("two"),
                _Project("retired", retired=True),
                _Project("template", template=True),
                _Project("builtin", builtin=True),
            ]
        )
        body = """TH.ProjectChooser{id:chooser;objectName:"chooser";model:catalog;theme:theme;usePopupWindow:false;onProjectSelected:window.calls++}function showChooser(){chooser.openCenteredIn(window.contentItem)}function chooserIsOpen(){return chooser.opened}"""
        with self.scene(body, model) as window:
            window.showChooser()
            frame(window)
            self.assertEqual(model.visibleCount, 2)
            for name, count in [
                ("projectFilterRetiredToggle", 3),
                ("projectFilterTemplatesToggle", 4),
                ("projectFilterBuiltinsToggle", 5),
            ]:
                QTest.mouseClick(
                    window, Qt.LeftButton, pos=self.point(self.find(window, name))
                )
                frame(window)
                self.assertEqual(model.visibleCount, count)
            cards = [
                item
                for item in fixture.SidebarEditorQmlTests.descendants(
                    window.contentItem()
                )
                if item.objectName() == "projectCard" and item.isVisible()
            ]
            cards[0].forceActiveFocus()
            frame(window)
            QTest.keyClick(window, Qt.Key_End)
            frame(window)
            self.assertEqual(
                window.activeFocusItem().property("details")["code"], "builtin"
            )
            QTest.keyClick(window, Qt.Key_Home)
            frame(window)
            self.assertEqual(
                window.activeFocusItem().property("details")["code"], "one"
            )
            QTest.mouseClick(
                window, Qt.LeftButton, pos=self.point(window.activeFocusItem())
            )
            frame(window)
            self.assertEqual(window.property("calls"), 1)
            self.assertFalse(window.chooserIsOpen())

    def test_first_touch_and_escape(self):
        model = ProjectModel()
        model.replace([_Project("one")])
        body = """TH.ProjectChooser{id:chooser;objectName:"chooser";model:catalog;theme:theme;usePopupWindow:false;onProjectSelected:window.calls++}function showChooser(){chooser.openCenteredIn(window.contentItem)}function chooserIsOpen(){return chooser.opened}"""
        with self.scene(body, model) as window:
            window.showChooser()
            frame(window)
            card = self.find(window, "projectCard")
            point = self.point(card)
            device = QTest.createTouchDevice()
            QTest.touchEvent(window, device).press(0, point, window).commit()
            frame(window)
            QTest.touchEvent(window, device).release(0, point, window).commit()
            frame(window)
            self.assertEqual(window.property("calls"), 1)
            window.showChooser()
            frame(window)
            QTest.keyClick(window, Qt.Key_Escape)
            frame(window)
            self.assertFalse(window.chooserIsOpen())

    def test_tab_keys_reorder_close_and_surviving_focus(self):
        body = """property var records:[{id:"a",title:"Assets"},{id:"b",title:"Second"},{id:"c",title:"Third"}]
property string current:"a"
function apply(action){calls++;if(action.type==="select")current=action.id;else if(action.type==="close"){records=records.filter(record=>record.id!==action.id);if(!records.some(record=>record.id===current))current=records[0]?.id||""}else{const items=records.slice();const moved=items.splice(action.source,1)[0];items.splice(action.target,0,moved);records=items}Qt.callLater(()=>{for(let i=0;i<tabs.count;i++){const item=tabs.itemAt(i);if(item.identity===window.current)item.forceActiveFocus()}})}
Row{Repeater{id:tabs;model:window.records;delegate:Controls.WorkspaceTabInput{required property var modelData;objectName:"tab_"+modelData.id;width:180;height:50;identity:modelData.id;label:modelData.title;selected:window.current===modelData.id;recordsProvider:()=>window.records;onCommand:action=>window.apply(action);Controls.WorkspaceTabVisual{anchors.fill:parent;theme:theme;title:parent.label;current:parent.selected;closable:true;onCloseRequested:window.apply({type:"close",id:parent.identity})}}}}"""
        with self.scene(body) as window:
            self.find(window, "tab_a").forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Right)
            frame(window)
            self.assertEqual(window.property("current"), "b")
            QTest.keyClick(window, Qt.Key_Right, Qt.ControlModifier | Qt.ShiftModifier)
            frame(window)
            self.assertEqual(
                [row["id"] for row in window.property("records").toVariant()],
                ["a", "c", "b"],
            )
            QTest.keyClick(window, Qt.Key_Delete)
            frame(window)
            self.assertEqual(window.property("current"), "a")
            self.assertTrue(self.find(window, "tab_a").hasActiveFocus())
            QTest.mouseClick(window, Qt.LeftButton, pos=QPoint(160, 25))
            frame(window)
            self.assertEqual(len(window.property("records").toVariant()), 1)

    def test_tab_selection_animates_and_can_settle_immediately(self):
        body = """property bool current:false
property bool animate:true
Controls.WorkspaceTabVisual {objectName:"visual";theme:theme;width:180;height:50;current:window.current;animateSelection:window.animate;title:"Assets"}"""
        with self.scene(body) as window:
            indicator = self.find(window, "workspaceTabSelectionIndicator")
            wrapper = indicator.parentItem().parentItem()
            widths = []
            wrapper.widthChanged.connect(lambda: widths.append(wrapper.width()))
            window.setProperty("current", True)
            QTest.qWait(150)
            frame(window)
            self.assertTrue(any(0 < width < 156 for width in widths), widths)
            self.assertEqual(indicator.width(), 156)
            window.setProperty("animate", False)
            window.setProperty("current", False)
            self.assertEqual(indicator.width(), 0)

    def test_section_keys_focus_then_activate(self):
        model = SectionTabModel()
        model.replace(
            [
                SectionTab("one", "Assets", "#6f9fc1", True, "assets"),
                SectionTab("two", "Shots", "#9f80c1", False, "movie"),
            ]
        )
        body = """property string selectedSection:""
TH.SectionTabRail {theme:theme;model:catalog;height:600;onSelected:key=>{window.selectedSection=key;window.calls++};onClosed:window.calls++;onReordered:window.calls++}"""
        with self.scene(body, model) as window:
            tabs = [
                item
                for item in fixture.SidebarEditorQmlTests.descendants(
                    window.contentItem()
                )
                if item.objectName() == "sectionTabDelegate"
            ]
            tabs[0].forceActiveFocus()
            frame(window)
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            self.assertTrue(tabs[1].hasActiveFocus())
            self.assertEqual(window.property("calls"), 0)
            QTest.keyClick(window, Qt.Key_Return)
            frame(window)
            self.assertEqual(window.property("selectedSection"), "two")
            QTest.keyClick(window, Qt.Key_Home)
            frame(window)
            QTest.keyClick(window, Qt.Key_Down, Qt.ControlModifier | Qt.ShiftModifier)
            frame(window)
            self.assertEqual(window.property("calls"), 2)


if __name__ == "__main__":
    unittest.main()
