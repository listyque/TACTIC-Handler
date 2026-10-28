"""Nested Item layouts use native input and the existing readonly request owner."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QSG_RENDER_LOOP', 'basic')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
from PySide6.QtCore import QCoreApplication, QPointF, Qt
from PySide6.QtTest import QTest, QSignalSpy
from tests import test_layout_links as navigation
from tests import test_layout_editor as layouts
from tests.profile_ui_responsiveness import frame
from thlib.environment import env_inst
from thlib import tactic_classes as tc
from thlib.ui.layout_editor import layout_tree

PARENT = '<config><parent layout="sobject-layout"><element name="title"><display class="title"/></element><element name="nested"><display class="view"><view>child</view></display></element></parent></config>'
CHILD = '<config><child layout="sobject-layout"><element name="leaf"><display class="title"/></element></child></config>'


class NestedLayoutLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        navigation.LayoutLinksTests.setUpClass()

    def setUp(self):
        self.fixture = navigation.LayoutLinksTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.native = self.fixture.fixture
        self.host = self.native.admin.layoutEditor
        self.pool = layouts.Pool()
        self.enterContext(patch.object(env_inst, 'server_pool', self.pool))
        self.enterContext(patch.object(tc, 'server_start', return_value=object()))
        self.read = self.enterContext(patch.object(tc, '_execute_read_only_procedure_serverside'))
        self.write = self.enterContext(patch.object(tc, 'execute_procedure_serverside'))
        self.host._types = [dict(value='demo/asset', label='Assets'), dict(value='demo/shot', label='Shots')]
        self.host._search_type, self.host._view = 'demo/asset', 'parent'
        self.host._configuration = self.config('parent', PARENT, 7)
        self.host._loaded_scope = ('demo', 'demo/asset', 'parent')
        self.host._source = 7
        self.host._xml = self.host._baseline = PARENT
        self.host._parse()
        self.host.stateChanged.emit()
        self.native.admin.select_section('layouts')
        frame(self.native.window)

    @staticmethod
    def config(view, xml, identity):
        return dict(revision='R1', sources=[dict(id=identity, xml=xml, priority=0)],
            layers=[], layout_templates=[], layout_views=[view], views=[view], resolved=dict(configured=True))

    def open_nested(self):
        self.native.click('layoutElement_nested')
        self.assertTrue(self.native.item('layoutElement_nested').property('selected'))
        target = self.native.item('layoutProperty_option_viewOpen')
        scroll = self.native.item('layoutSettingsScroll')
        y = target.mapToItem(scroll, QPointF()).y()
        scroll.setProperty('contentY', max(0, scroll.property('contentY') + y - 50))
        frame(self.native.window)
        self.native.click('layoutProperty_option_viewOpen')

    def reply(self, view, xml, identity):
        worker = self.host._worker
        self.assertIsNotNone(worker)
        configuration = self.config(view, xml, identity)
        if view == 'parent':
            configuration['sources'].insert(0, dict(id=9, xml=xml.replace('name="nested"', 'name="different"'), priority=1))
        worker.result.emit(dict(configuration=configuration, sampleItems=[]))
        QCoreApplication.processEvents()
        frame(self.native.window)

    def test_exact_nested_scope_return_and_dirty_back_guard(self):
        self.open_nested()
        self.assertEqual(self.host.model['view'], 'child')
        self.reply('child', CHILD, 8)
        self.host.set_xml(CHILD.replace('name="leaf"', 'name="edited"'))
        frame(self.native.window)
        self.native.click('adminReturnToLayout')
        self.assertEqual(self.host.model['view'], 'child')
        self.assertTrue(self.host.dirty)
        self.assertIsNone(self.host._worker)
        self.host.discard()
        frame(self.native.window)
        self.native.click('adminReturnToLayout')
        self.reply('parent', PARENT, 7)
        self.assertEqual(self.host.model['source'], 7)
        self.assertTrue(self.native.item('layoutElement_nested').property('selected'))
        self.assertFalse(self.host.dirty)
        self.write.assert_not_called()
        self.assertEqual(self.native.fixture.warnings, [])

    def test_cross_type_and_missing_view_still_allow_return(self):
        xml = PARENT.replace('name="nested"', 'name="nested" search_type="demo/shot"')
        self.host._xml = self.host._baseline = xml
        self.host._configuration = self.config('parent', xml, 7)
        self.host._parse()
        self.host.stateChanged.emit()
        frame(self.native.window)
        self.open_nested()
        self.assertEqual(self.host.model['searchType'], 'demo/shot')
        self.reply('other', CHILD, 8)
        self.assertEqual(self.host.model['error'], self.host.tr('Referenced item layout is unavailable'))
        self.assertIsNone(self.host._configuration)
        self.native.click('adminReturnToLayout')
        self.assertEqual(self.host.model['searchType'], 'demo/asset')
        self.reply('parent', xml, 7)
        self.assertTrue(self.native.item('layoutElement_nested').property('selected'))
        self.write.assert_not_called()
        self.assertEqual(self.native.fixture.warnings, [])


class DragRowInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.qt_application import gui_test_application
        cls.app = gui_test_application()

    def test_drag_row_activates_once_and_keeps_drag_drop(self):
        from tests import test_frame_table as frames
        self.close = frames.FrameTableTests.close.__get__(self)
        scene = dict(nodes=[dict(kind='Action', id='source', x=10, y=10, width=180, height=46,
            text='Widget', fontRole='body', fontSize=13, opacity=1, enabled=True, dragValue='widget', action=dict(type='pick'),
            dragStartAction=dict(type='start'), children=[]),
            dict(kind='Box', id='destination', x=220, y=10, width=160, height=100,
                 enabled=True, fontRole='body', fontSize=13, opacity=1, dropAction=dict(type='drop'), children=[])])
        window, view = frames.FrameTableTests.create(self, 'tactic_frame/core/FrameView.qml',
            dict(scene=scene), width=420, height=180)
        meta = view.metaObject()
        spy = QSignalSpy(view, meta.method(meta.indexOfSignal('event(QVariant,QVariant)')))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPointF(50, 30).toPoint())
        frame(window)
        self.assertEqual(spy.count(), 1)
        self.assertEqual(spy.at(0)[0].toVariant()['type'], 'pick')
        QTest.keyClick(window, Qt.Key_Space)
        frame(window)
        self.assertEqual(spy.count(), 2)
        device = QTest.createTouchDevice()
        QTest.touchEvent(window, device).press(0, QPointF(50, 30).toPoint(), window).commit()
        QTest.touchEvent(window, device).release(0, QPointF(50, 30).toPoint(), window).commit()
        frame(window)
        self.assertEqual(spy.count(), 3)
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, QPointF(50, 30).toPoint())
        QTest.mouseMove(window, QPointF(80, 30).toPoint(), 20)
        QTest.mouseMove(window, QPointF(260, 30).toPoint(), 20)
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, QPointF(260, 30).toPoint())
        frame(window)
        self.assertEqual([spy.at(index)[0].toVariant()['type'] for index in range(spy.count())],
                         ['pick', 'pick', 'pick', 'start', 'drop'])


if __name__ == '__main__':
    unittest.main()
