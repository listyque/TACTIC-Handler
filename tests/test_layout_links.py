"""Real native editor links, return navigation and canvas/tree selection."""
import copy
import os
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

os.environ.setdefault('QSG_RENDER_LOOP', 'basic')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')

from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent
from pathlib import Path
from tests.profile_ui_responsiveness import frame
from tests import test_administration_qml as native_fixture
from tests.qt_application import gui_test_application


class LayoutLinksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()
        native_fixture.AdministrationQmlTests.setUpClass()

    def setUp(self):
        self.fixture = native_fixture.AdministrationQmlTests()
        from thlib.ui.administration import AdministrationController
        open_admin = AdministrationController.open

        def open_compiled(controller):
            path = Path(__file__).resolve().parents[1] / 'thlib/ui/qml/features/administration/AdministrationView.qml'
            component = QQmlComponent(self.fixture.fixture.engine, QUrl.fromLocalFile(str(path)))
            self.assertTrue(component.isReady(), [error.toString() for error in component.errors()])
            open_admin(controller)

        with patch.object(AdministrationController, 'open', open_compiled):
            self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.window.resize(1400, 900)
        self.editor = self.fixture.admin.dashboardEditor
        self.enterContext(patch.object(self.editor, 'load_source'))

    def seed(self, document, compiled=None):
        compiled = dict(targetSearchKey='sthpw/project?code=demo', **(compiled or dict(layoutNodes=[])))
        self.fixture.seed(self.editor, document['name'], document, dict(
            project='demo', revision='R1', checkedDocument=copy.deepcopy(document),
            searchTypes=[dict(value='demo/asset', label='Assets')],
            dataSource=dict(searchType='demo/asset', fields=[], itemViews=[dict(value='hub_items', label='hub_items')],
                            tableViews=[dict(value='production', label='production')]),
            compiled=compiled))
        self.fixture.admin.select_section('dashboards')
        frame(self.fixture.window)

    def click_property(self, name):
        field = self.fixture.item(name)
        scroll = self.fixture.item('pageProperties')
        offset = field.mapToItem(scroll, QPointF()).y()
        if offset < 0 or offset + field.height() > scroll.height():
            scroll.setProperty('contentY', max(0, scroll.property('contentY') + offset - 50))
            frame(self.fixture.window)
        self.fixture.click(name)

    def test_canvas_unfolds_and_reveals_selected_tree_row_without_stealing_focus(self):
        blocks = [dict(kind='text', text=str(index)) for index in range(25)]
        blocks.append(dict(kind='column', children=[dict(kind='text', text='Target')]))
        self.seed(dict(name='work', title='Work', blocks=blocks), dict(layoutNodes=[
            dict(kind='group', height=240, editorPath=[25], children=[
                dict(kind='text', text='Target', height=60, editorPath=[25, 0])])]))
        self.fixture.click('pageTreeToggle_page')
        self.fixture.click('canvasTarget_25.0')
        row = self.fixture.item('pageBlock_25.0')
        self.assertTrue(row.property('selected'))
        scroll = self.fixture.item('pageBlocks')
        position = row.mapToItem(scroll, QPointF())
        self.assertGreaterEqual(position.y(), -1)
        self.assertLessEqual(position.y() + row.height(), scroll.height() + 1)
        QTest.keyClick(self.fixture.window, Qt.Key_Right, Qt.ShiftModifier)
        frame(self.fixture.window)
        self.assertEqual(self.editor.document['blocks'][25]['children'][0]['offset_x'], 10)
        self.fixture.click('pageAction_undo')
        self.assertFalse(self.editor.dirty)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_saved_card_and_table_links_preserve_page_draft_and_return_selection(self):
        document = dict(name='work', title='Work', blocks=[dict(kind='column', search_type='demo/asset', children=[
            dict(kind='items', search_type='demo/asset', view='hub_items'), dict(kind='table', search_type='demo/asset', view='production')])])
        self.seed(document)
        self.fixture.click('pageBlock_0.0')
        draft = copy.deepcopy(document)
        draft['title'] = 'Unsaved source'
        self.editor.replace_document(draft)
        frame(self.fixture.window)
        with patch.object(self.fixture.admin.layoutEditor, 'preview_scope') as focus:
            self.click_property('pageProperty_viewOpen')
            focus.assert_called_once_with('demo', 'demo/asset', 'hub_items')
        self.assertEqual(self.fixture.admin.section, 'layouts')
        self.assertEqual(self.fixture.admin.layoutParent['name'], 'work')
        self.fixture.click('adminReturnToLayout')
        self.assertEqual(self.fixture.admin.section, 'dashboards')
        self.assertEqual(self.editor.document, draft)
        self.assertTrue(self.fixture.item('pageBlock_0.0').property('selected'))
        self.fixture.click('pageBlock_0.1')
        columns = self.fixture.fixture.columns
        with patch.object(columns, 'open_scoped_definition') as focus, patch.object(columns, 'load_definition_catalog'):
            self.click_property('pageProperty_viewOpen')
            focus.assert_called_once_with('demo/asset', 'production', 'demo')
            self.assertEqual(self.fixture.admin.section, 'columns')
            self.fixture.click('adminReturnToLayout')
        self.assertEqual(self.editor.document, draft)
        self.assertTrue(self.editor.dirty)
        self.assertTrue(self.fixture.item('pageBlock_0.1').property('selected'))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_linked_pages_restore_selected_widget_and_reject_dirty_replacement(self):
        source = dict(name='work', title='Work', blocks=[dict(kind='link', text='Report', href='/projects/demo/dashboard/report')])
        target = dict(name='report', title='Report', blocks=[dict(kind='text', text='Report body')])
        self.seed(source)
        self.editor._catalog.append(dict(identity='report', label='Report'))
        self.editor.stateChanged.emit()
        self.fixture.click('pageBlock_0')

        def load(action, identity):
            self.assertEqual(action, 'load')
            document = source if identity == 'work' else target
            self.editor._identity = identity
            self.editor._document = copy.deepcopy(document)
            self.editor._original = copy.deepcopy(document)
            self.editor.stateChanged.emit()

        with patch.object(self.editor, '_request', side_effect=load):
            self.click_property('pageProperty_hrefOpen')
            self.assertEqual(self.editor.identity, 'report')
            self.fixture.click('pageBlock_0')
            draft = dict(target, title='Unsaved report')
            self.editor.replace_document(draft)
            frame(self.fixture.window)
            self.fixture.click('adminReturnToLayout')
            self.assertEqual(self.editor.document, draft)
            self.assertEqual(len(self.fixture.admin._layout_links), 1)
            self.editor.discard()
            frame(self.fixture.window)
            self.fixture.click('adminReturnToLayout')
        self.assertEqual(self.editor.identity, 'work')
        self.assertTrue(self.fixture.item('pageBlock_0').property('selected'))
        self.assertEqual(self.fixture.admin.layoutParent, {})
        self.assertEqual(self.fixture.fixture.warnings, [])


class LayoutLinkGuardTests(unittest.TestCase):
    def test_same_dirty_card_is_reused_and_another_scope_is_not_replaced(self):
        from thlib.ui.administration import AdministrationController
        host = SimpleNamespace(_loaded_scope=('demo', 'demo/asset', 'hub_items'),
            _configuration={'sources': []}, dirty=True, busy=False, preview_scope=Mock())
        owner = SimpleNamespace(canManage=True, _project='demo', _layout_editor=host,
            _dashboard_editor=SimpleNamespace(fail=Mock()),
            remember_page_layout=Mock(), select_section=Mock(), tr=lambda value: value)
        AdministrationController.open_page_card(owner, 'demo/asset', 'hub_items')
        host.preview_scope.assert_not_called()
        owner.select_section.assert_called_once_with('layouts')
        owner.select_section.reset_mock()
        AdministrationController.open_page_card(owner, 'demo/shot', 'hub_items')
        owner.select_section.assert_not_called()
        owner._dashboard_editor.fail.assert_called_once()


if __name__ == '__main__':
    unittest.main()
