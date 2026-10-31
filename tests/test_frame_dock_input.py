"""Native dock gestures: real mouse path, cancellation and floating title movement."""
import unittest
import os
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication,QEvent,QPoint,QPointF,QUrl,Qt,QMetaObject,QObject,Slot
from PySide6.QtQml import QQmlEngine,QQmlComponent
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
import tests.test_sidebar_editor_qml as fixture
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.workspace_models.docks import DockPanelModel
ROOT=Path(__file__).resolve().parents[1]

class HelpCommands(QObject):
    def __init__(self):
        super().__init__()
        self.topics=[]

    @Slot(str)
    def open_help(self, topic):
        self.topics.append(topic)

class FrameDockInputTests(unittest.TestCase):
    def test_grip_cancel_and_floating_title_have_separate_commits(self):
        app=gui_test_application();engine=QQmlEngine();model=DockPanelModel({});warnings=[]
        help_commands=HelpCommands()
        model.float_panel('notes',.2,.2,.6,.6)
        engine.warnings.connect(lambda errors:warnings.extend(error.toString() for error in errors))
        for name,value in dict(qml_icon_bindings(ROOT,app),dockModel=model,windowModel=help_commands).items():engine.rootContext().setContextProperty(name,value)
        component=QQmlComponent(engine)
        source=('import QtQuick\nimport QtQuick.Controls\nimport "'+(ROOT/'thlib/ui/qml').as_uri()+'" as TH\n'
            'ApplicationWindow{id:window;visible:true;width:1000;height:700;property bool testDark:true;property int commits:0;property int cancels:0;'
            'TH.Theme{id:theme;dark:window.testDark;clickAnimationsEnabled:false;hoverAnimationsEnabled:false;fadeAnimationsEnabled:false;popupAnimationsEnabled:false}'
            'Item{id:host;anchors.fill:parent;'
            'function focusDockTab(id){} function beginDockDrag(id){} function updateDockDrag(id,x,y){}'
            'function finishDockDrag(id,x,y,w,h,floating){window.commits++}'
            'function cancelDockDrag(id){window.cancels++}'
            'function beginDockResize(id,orientation,boundary,spanStart,spanEnd,shared){} function endDockResize(){}'
            'function updateDockResizeBoundary(boundary,start,end){}'
            'TH.DockPanel{id:panel;objectName:"testedDock";host:host;theme:theme;panelId:"notes";kind:"notes";title:"Inspector";'
            'panelX:0.2;panelY:0.2;panelWidth:0.6;panelHeight:0.6;modelVisible:true;panelOpen:true;stackActive:true;closable:true;stackOrder:0;stackPanels:[];stackSize:1;'
            'dockArea:"floating";canResizeLeft:false;canResizeRight:false;canResizeTop:false;canResizeBottom:false;contentComponent:Component{Item{}}}}}')
        component.setData(source.encode(),QUrl());self.assertTrue(component.isReady(),[error.toString() for error in component.errors()])
        window=component.create();self.assertIsNotNone(window,[error.toString() for error in component.errors()])
        try:
            frame(window)
            items={item.objectName():item for item in fixture.SidebarEditorQmlTests.descendants(window.contentItem())}
            panel=items['testedDock'];grip=items['dockStackDrag_notes']
            actions={item.property('frameId'):item for item in fixture.SidebarEditorQmlTests.descendants(panel) if item.property('frameId') in ('dockHelp','dockDetach','dockClose')}
            self.assertEqual(set(actions),{'dockHelp','dockDetach','dockClose'})
            for identity,action in actions.items():
                self.assertTrue(action.property('round'),identity)
                self.assertEqual(action.width(),action.height())
                surface=next(item for item in fixture.SidebarEditorQmlTests.descendants(action) if item.property('radius') and item.property('width'))
                self.assertEqual(surface.property('radius'),surface.width()/2,identity)
            if os.environ.get('WINDOW_HEADER_CAPTURE'):
                capture=Path(os.environ['WINDOW_HEADER_CAPTURE']);capture.mkdir(parents=True,exist_ok=True)
                for mode in ('dark','light'):
                    window.setProperty('testDark',mode=='dark');frame(window)
                    self.assertTrue(window.grabWindow().copy(200,140,600,60).save(str(capture/f'native-{mode}.png')))
                window.setProperty('testDark',True);frame(window)
            point=grip.mapToScene(QPointF(grip.width()/2,grip.height()/2)).toPoint()
            QTest.mousePress(window,Qt.LeftButton,pos=point)
            QTest.mouseMove(window,point+QPoint(40,25));frame(window)
            self.assertTrue(grip.property('dragActive'))
            QMetaObject.invokeMethod(grip,'cancel');QTest.mouseRelease(window,Qt.LeftButton,pos=point+QPoint(40,25));frame(window)
            self.assertEqual(window.property('commits'),0)
            self.assertEqual(window.property('cancels'),1)
            self.assertAlmostEqual(panel.x(),200)
            title=items['testedDock'].mapToScene(QPointF(80,24)).toPoint()
            before=(panel.x(),panel.y())
            with patch.object(model,'set_geometry',wraps=model.set_geometry) as commit:
                QTest.mousePress(window,Qt.LeftButton,pos=title)
                QTest.mouseMove(window,title+QPoint(30,20));frame(window)
                self.assertAlmostEqual(panel.x(),before[0]+30,delta=1)
                QTest.mouseRelease(window,Qt.LeftButton,pos=title+QPoint(30,20));frame(window)
                commit.assert_called_once()
            self.assertEqual(window.property('commits'),0,'Title movement does not enter the docking path')
            def click(action):
                point=action.mapToScene(QPointF(action.width()/2,action.height()/2)).toPoint()
                QTest.mouseClick(window,Qt.LeftButton,pos=point);frame(window)
            click(actions['dockHelp'])
            self.assertEqual(help_commands.topics,['dock.notes'])
            with patch.object(model,'detach_panel') as detach:
                click(actions['dockDetach']);detach.assert_called_once_with('notes')
            with patch.object(model,'close_panel') as close:
                actions['dockClose'].forceActiveFocus()
                QTest.keyClick(window,Qt.Key_Space);frame(window)
                close.assert_called_once_with('notes')
            self.assertEqual(warnings,[])
        finally:
            window.close();window.deleteLater();engine.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)

if __name__=='__main__':unittest.main()
