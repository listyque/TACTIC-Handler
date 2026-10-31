"""Native region selection uses the real editor and local history without window hosts."""
import copy
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from tests import test_frame_table as frames
from tests.test_layout_editor import Pool
from thlib.environment import env_inst
from thlib.ui.admin.dashboard import DashboardEditor


class PageRegions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    click = frames.FrameTableTests.click
    item = frames.FrameTableTests.item

    def test_region_picker_and_undo_change_only_the_local_document(self):
        pool = Pool()
        self.enterContext(patch.object(env_inst, 'server_pool', pool))
        host = DashboardEditor(SimpleNamespace(is_stream_server=True, can_manage_tools=True, debug_log=None))
        self.addCleanup(host.shutdown)
        host._project = 'demo'
        host._can_write = host._loaded = True
        host._identity = 'regions'
        host._metadata = dict(revision='R1', searchTypes=[])
        host._document = dict(name='regions', title='Regions', blocks=[
            dict(kind='button', title='Open project', href='https://example.com', region='footer')])
        host._original = copy.deepcopy(host._document)
        window, view = self.create('features/administration/layouts/PageLayoutEditorView.qml',
                                   dict(controller=host), width=1500, height=950)
        self.click(window, self.item(view, 'pageBlock_0'))
        picker = self.item(view, 'pageProperty_region')
        self.assertEqual(picker.property('currentValue'), 'footer')
        picker.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(window, Qt.Key_Up); QTest.keyClick(window, Qt.Key_Up)
        frames.frame(window)
        self.assertEqual(host.document['blocks'][0]['region'], 'header')
        self.click(window, self.item(view, 'pageAction_undo'))
        self.assertEqual(host.document['blocks'][0]['region'], 'content')
        self.click(window, self.item(view, 'pageAction_undo'))
        self.assertEqual(host.document, host._original)
        self.assertFalse(host.dirty)
        self.assertIsNone(host._pending_save)


if __name__ == '__main__':
    unittest.main()
