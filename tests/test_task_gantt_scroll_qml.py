"""Native Gantt extents stay stable with empty data and fractional dock sizes."""
import json
import os
from pathlib import Path
import unittest

os.environ.setdefault('QT_QUICK_BACKEND','software')
if os.name=='nt':os.environ.setdefault('QT_QPA_FONTDIR','C:/Windows/Fonts')
from PySide6.QtCore import QObject, QSizeF, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest
from tests import test_task_section_retention_qml as retained
from shiboken6 import isValid
QML=retained.QML
frame=retained.frame
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.localization import CatalogTranslator


class GanttScrollTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.QtTextRendering)
        retained.TaskSectionRetentionQmlTests.setUpClass()

    def test_empty_and_populated_fractional_viewports_do_not_oscillate(self):
        fixture=retained.TaskSectionRetentionQmlTests();fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        translator=CatalogTranslator(QML.parent/'translations/ru.json')
        fixture.app.installTranslator(translator)
        self.addCleanup(fixture.app.removeTranslator,translator)
        for name,value in qml_icon_bindings(QML.parents[2],fixture.engine).items():
            fixture.engine.rootContext().setContextProperty(name,value)
        data=json.loads((Path(__file__).parent/'fixtures/task_schedule_scroll.json').read_text(encoding='utf-8'))['gantt']
        component=QQmlComponent(fixture.engine,QUrl.fromLocalFile(str(QML/'TaskGanttView.qml')))
        view=component.createWithInitialProperties({'theme':fixture.theme})
        self.assertIsNotNone(view,[error.toString() for error in component.errors()])
        window=QQuickWindow();window.resize(1200,1000)
        view.setParentItem(window.contentItem());window.show()
        self.addCleanup(window.close)
        self.addCleanup(lambda: view.deleteLater() if isValid(view) else None)
        task_list=view.findChild(QObject,'ganttTaskList')
        self.assertIsNotNone(task_list)
        for mode in ('empty','rows','overflow'):
            empty=mode=='empty'
            projection=({**data,'days':1,'records':[],'tickSets':{},'weekends':[],'milestones':[],'overview':[],
                         'todayDay':-1,'scheduled':0,'unscheduled':0,'rangeStart':'','rangeEnd':'','warnings':0} if empty else data)
            if mode=='overflow':
                projection={**data,'records':[{**data['records'][0],'taskCode':f'scroll-{index}',
                    'ganttSectionFirst':index==0,'groupFirst':False} for index in range(40)]}
            fixture.tasks._gantt=projection
            fixture.tasks.gantt_model.replace([{**record,'checked':False,'selected':False,
                'parentPreviewUrl':'','groupCollapsed':False,'processColor':record.get('statusColor',''),'groupColor':''} for record in projection['records']])
            fixture.tasks.advancedChanged.emit()
            for width,height in ((871.25,872.75),(1091.6,691.4)):
                with self.subTest(mode=mode,width=width):
                    view.setSize(QSizeF(width,height))
                    for _ in range(4):frame(window)
                    changes=QSignalSpy(task_list.contentHeightChanged)
                    samples=[]
                    for _ in range(30):
                        QTest.qWait(10)
                        samples.append((task_list.property('width'),task_list.property('height'),task_list.property('contentHeight')))
                    self.assertEqual(len(set(samples)),1)
                    self.assertEqual(changes.count(),0)
                    if empty:self.assertLessEqual(task_list.property('contentHeight'),task_list.property('height'))
                    output=os.environ.get('GANTT_SCROLL_OUTPUT')
                    if output:
                        Path(output).mkdir(parents=True,exist_ok=True)
                        self.assertTrue(window.grabWindow().save(str(Path(output)/f"handler-{os.environ.get('QT_SCALE_FACTOR','1')}-{mode}-{width}.png")))
        self.assertEqual(fixture.warnings,[])
