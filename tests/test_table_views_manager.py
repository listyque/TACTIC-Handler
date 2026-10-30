"""Real native manager controls; server access stays in its asynchronous owner."""
from copy import deepcopy
import unittest

from PySide6.QtCore import QObject, Property, Signal, Slot, Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from tests import test_frame_table as frames
from tests.profile_ui_responsiveness import frame


class Owner(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.state = dict(project='demo',searchType='demo/asset',current='table',revision='r1',busy=False,error='',views=[
            dict(view='table',title='Default table',protected=True,columns=2,sources=0),
            dict(view='artists',title='Artist review',protected=False,columns=2,sources=1)])
        self.calls = []

    @Property('QVariantMap', notify=changed)
    def model(self):
        return deepcopy(self.state)

    @Slot('QVariantMap')
    def run(self, command):
        self.calls.append(dict(command))
        if command['action']=='rename':
            self.state['views'][1]['title']=command['title']
            self.state['selected']='artists'
            self.state['revision']='r2'
            self.changed.emit()


class TableViewsManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frames.FrameTableTests.setUpClass()

    def setUp(self):
        self.surface = frames.FrameTableTests()
        self.addCleanup(self.surface.doCleanups)

    def test_native_manager_search_rename_and_protected_default(self):
        owner = Owner()
        window, view = self.surface.create('features/table/TableViewsManager.qml',dict(controller=owner),width=940,height=650)
        rename = self.surface.item(view,'tableViews_rename')
        self.assertFalse(rename.isEnabled())
        self.surface.click(window,self.surface.item(view,'tableView_artists'))
        self.surface.click(window,rename)
        field=self.surface.item(view,'tableViewsName')
        self.surface.click(window,field)
        QTest.keyClick(window,Qt.Key_A,Qt.ControlModifier)
        event = QInputMethodEvent(); event.setCommitString('Lighting review')
        QGuiApplication.sendEvent(window.activeFocusItem(), event)
        frame(window)
        self.surface.click(window,self.surface.item(view,'tableViewsApply'))
        self.assertEqual(owner.calls[-1],dict(action='rename',view='artists',title='Lighting review',revision='r1'))
        search=self.surface.item(view,'tableViewsSearch')
        self.surface.click(window,search)
        event = QInputMethodEvent(); event.setCommitString('Lighting')
        QGuiApplication.sendEvent(window.activeFocusItem(), event)
        frame(window)
        self.assertFalse(any(item.objectName()=='tableView_table' for item in frames._visual_items(view)))
