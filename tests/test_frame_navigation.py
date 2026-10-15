"""Real input and geometry of the shared neutral navigation row."""
import unittest
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QUrl, Qt
from PySide6.QtQml import QQmlEngine, QQmlComponent
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
import tests.test_sidebar_editor_qml as fixture
from thlib.ui.icon_font import qml_icon_bindings
ROOT=Path(__file__).resolve().parents[1]

class FrameNavigationTests(unittest.TestCase):
    def test_native_public_row_uses_shared_geometry_and_first_input(self):
        app=gui_test_application()
        engine=QQmlEngine(); warnings=[]
        engine.warnings.connect(lambda errors:warnings.extend(error.toString() for error in errors))
        for name,value in qml_icon_bindings(ROOT,app).items(): engine.rootContext().setContextProperty(name,value)
        component=QQmlComponent(engine)
        source=('import QtQuick\nimport QtQuick.Controls\nimport "'+(ROOT/'thlib/ui/qml').as_uri()+'" as TH\n'
                'ApplicationWindow{id:window;visible:true;width:320;height:200;property int calls:0;'
                'TH.Theme{id:theme;dark:true} TH.SidebarTreeRow{objectName:"testedNavigationRow";width:parent.width;height:implicitHeight;theme:theme;title:"Sample";glyph:"link";badge:7;selected:true;onActivated:window.calls++}}')
        component.setData(source.encode(),QUrl())
        self.assertTrue(component.isReady(),[error.toString() for error in component.errors()])
        window=component.create();self.assertIsNotNone(window)
        try:
            frame(window)
            rows={item.objectName():item for item in fixture.SidebarEditorQmlTests.descendants(window.contentItem())}
            row=rows['testedNavigationRow'];title=rows['sidebarRowTitle']
            self.assertEqual(row.implicitHeight(),56)
            self.assertEqual(title.width(),184)
            QTest.mouseClick(window,Qt.LeftButton,pos=QPoint(70,28));frame(window)
            self.assertEqual(window.property('calls'),1)
            row.forceActiveFocus();QTest.keyClick(window,Qt.Key_Space);frame(window)
            self.assertEqual(window.property('calls'),2)
            row.setProperty('rowType','section');frame(window)
            self.assertEqual(row.implicitHeight(),48)
            row.setProperty('rowType','separator');frame(window)
            self.assertEqual(row.implicitHeight(),16)
            self.assertEqual(warnings,[])
        finally:
            window.close();window.deleteLater();engine.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)

if __name__=='__main__':unittest.main()
