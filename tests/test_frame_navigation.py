"""Real input and geometry of the shared neutral navigation row."""

import unittest
from contextlib import contextmanager
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QUrl, Qt
from PySide6.QtQml import QQmlEngine, QQmlComponent, qmlEngine
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
import tests.test_sidebar_editor_qml as fixture
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.models import NavigationEntry, NavigationModel
from thlib.ui.localization import CatalogTranslator

ROOT = Path(__file__).resolve().parents[1]


class FrameNavigationTests(unittest.TestCase):
    def test_native_public_row_uses_shared_geometry_and_first_input(self):
        app = gui_test_application()
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        for name, value in qml_icon_bindings(ROOT, app).items():
            engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(engine)
        source = (
            'import QtQuick\nimport QtQuick.Controls\nimport "'
            + (ROOT / "thlib/ui/qml").as_uri()
            + '" as TH\n'
            "ApplicationWindow{id:window;visible:true;width:320;height:200;property int calls:0;"
            'TH.Theme{id:theme;dark:true} TH.SidebarTreeRow{objectName:"testedNavigationRow";width:parent.width;height:implicitHeight;theme:theme;title:"Sample";glyph:"link";badge:7;selected:true;onActivated:window.calls++}}'
        )
        component.setData(source.encode(), QUrl())
        self.assertTrue(
            component.isReady(), [error.toString() for error in component.errors()]
        )
        window = component.create()
        self.assertIsNotNone(window)
        try:
            frame(window)
            rows = {
                item.objectName(): item
                for item in fixture.SidebarEditorQmlTests.descendants(
                    window.contentItem()
                )
            }
            row = rows["testedNavigationRow"]
            title = rows["sidebarRowTitle"]
            self.assertEqual(row.implicitHeight(), 56)
            self.assertEqual(title.width(), 184)
            QTest.mouseClick(window, Qt.LeftButton, pos=QPoint(70, 28))
            frame(window)
            self.assertEqual(window.property("calls"), 1)
            row.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Space)
            frame(window)
            self.assertEqual(window.property("calls"), 2)
            row.setProperty("rowType", "section")
            frame(window)
            self.assertEqual(row.implicitHeight(), 48)
            row.setProperty("rowType", "separator")
            frame(window)
            self.assertEqual(row.implicitHeight(), 16)
            self.assertEqual(warnings, [])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    @contextmanager
    def drawer_fixture(self):
        app = gui_test_application()
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(e.toString() for e in errors)
        )
        for name, value in qml_icon_bindings(ROOT, app).items():
            engine.rootContext().setContextProperty(name, value)
        entries = [
            NavigationEntry("group", "Assets", "", "", "", entry_type="section"),
            NavigationEntry("first", "First asset", "cube", "", "open", depth=1),
            NavigationEntry(
                "missing", "Unavailable", "cube", "", "", depth=1, available=False
            ),
            NavigationEntry(
                "separator", "", "", "", "", entry_type="separator", depth=1
            ),
            *[
                NavigationEntry(f"entry{i}", f"Asset {i}", "cube", "", "open", depth=1)
                for i in range(30)
            ],
            NavigationEntry("last", "Last asset", "folder", "", "open"),
        ]
        model = NavigationModel(entries)
        engine.rootContext().setContextProperty("navModel", model)
        source = f'''import QtQuick
import QtQuick.Controls
import "{(ROOT / "thlib/ui/qml").as_uri()}" as TH
ApplicationWindow {{
    id: window; visible:true; width:900; height:640; property int calls:0
    TH.Theme {{id:theme;dark:true;fadeAnimationsEnabled:false;popupAnimationsEnabled:false}}
    Button {{id:opener;objectName:"opener";x:700;y:500;width:100;height:40;text:"Open";onClicked:drawer.open()}}
    TH.NavigationDrawer {{id:drawer;objectName:"drawer";model:navModel;theme:theme;sidebarEditingAvailable:true;onSelected:window.calls++}}
    function showDrawer() {{opener.forceActiveFocus();drawer.open()}}
}}'''
        component = QQmlComponent(engine)
        component.setData(source.encode(), QUrl())
        self.assertTrue(component.isReady(), [e.toString() for e in component.errors()])
        window = component.create()
        self.assertIsNotNone(window)
        try:
            frame(window)
            objects = {
                item.objectName(): item
                for item in fixture.SidebarEditorQmlTests.descendants(
                    window.contentItem()
                )
                if item.objectName()
            }
            yield window, model, objects
            self.assertEqual(warnings, [])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_drawer_keys_include_recycled_rows_and_return_focus(self):
        with self.drawer_fixture() as (window, model, objects):
            window.showDrawer()
            frame(window)
            drawer, view = objects["drawer"], objects["navigationList"]
            QTest.keyClick(window, Qt.Key_End)
            frame(window)
            self.assertEqual(view.property("currentIndex"), 34)
            self.assertGreater(view.property("contentY"), 500)
            saved_scroll = view.property("contentY")
            application = gui_test_application()
            translator = CatalogTranslator(ROOT / "thlib/ui/translations/ru.json")
            application.installTranslator(translator)
            try:
                qmlEngine(window).retranslate()
                frame(window)
                self.assertEqual(
                    next(
                        item
                        for item in fixture.SidebarEditorQmlTests.descendants(
                            window.contentItem()
                        )
                        if item.objectName() == "navigationTitle"
                    ).property("text"),
                    "Навигация",
                )
                self.assertEqual(view.property("contentY"), saved_scroll)
            finally:
                application.removeTranslator(translator)
                qmlEngine(window).retranslate()
                frame(window)
            self.assertEqual(
                next(
                    item
                    for item in fixture.SidebarEditorQmlTests.descendants(
                        window.contentItem()
                    )
                    if item.objectName() == "navigationTitle"
                ).property("text"),
                "Navigation",
            )
            QTest.keyClick(window, Qt.Key_Escape)
            window.showDrawer()
            frame(window)
            self.assertEqual(view.property("contentY"), saved_scroll)
            QTest.keyClick(window, Qt.Key_Home)
            frame(window)
            self.assertEqual(view.property("currentIndex"), 0)
            QTest.keyClick(window, Qt.Key_Left)
            frame(window)
            self.assertFalse(model.entry("first").visible)
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            self.assertEqual(view.property("currentIndex"), 34)
            QTest.keyClick(window, Qt.Key_Home)
            QTest.keyClick(window, Qt.Key_Right)
            frame(window)
            self.assertTrue(model.entry("first").visible)
            QTest.keyClick(window, Qt.Key_Right)
            frame(window)
            self.assertEqual(view.property("currentIndex"), 1)
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            self.assertEqual(view.property("currentIndex"), 4)
            QTest.keyClick(window, Qt.Key_Space)
            frame(window)
            self.assertEqual(window.property("calls"), 1)
            self.assertFalse(drawer.property("opened"))
            self.assertTrue(objects["opener"].hasActiveFocus())
            window.showDrawer()
            frame(window)
            QTest.keyClick(window, Qt.Key_Escape)
            frame(window)
            self.assertFalse(drawer.property("opened"))
            self.assertTrue(objects["opener"].hasActiveFocus())

    def test_drawer_mouse_exit_is_armed_only_after_enter_and_first_touch(self):
        with self.drawer_fixture() as (window, model, objects):
            drawer = objects["drawer"]
            QTest.mouseMove(window, QPoint(750, 520))
            frame(window)
            QTest.mouseClick(window, Qt.LeftButton, pos=QPoint(750, 520))
            frame(window)
            QTest.mouseMove(window, QPoint(765, 530))
            frame(window)
            self.assertTrue(drawer.property("opened"))
            QTest.mouseMove(window, QPoint(180, 300))
            frame(window)
            self.assertTrue(drawer.property("pointerEntered"))
            QTest.mouseMove(window, QPoint(480, 300))
            frame(window)
            self.assertTrue(drawer.property("opened"))
            QTest.mouseMove(window, QPoint(500, 300))
            frame(window)
            self.assertFalse(drawer.property("opened"))
            window.showDrawer()
            frame(window)
            device = QTest.createTouchDevice()
            point = QPoint(100, 161)
            QTest.touchEvent(window, device).press(0, point, window).commit()
            frame(window)
            QTest.touchEvent(window, device).release(0, point, window).commit()
            frame(window)
            self.assertEqual(window.property("calls"), 1)
            self.assertFalse(drawer.property("opened"))


if __name__ == "__main__":
    unittest.main()
