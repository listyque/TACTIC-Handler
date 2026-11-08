"""Related objects use native windows, scoped queries and the house controls."""
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Property, Signal
from thlib.ui.related_objects import RelatedObjectsController
from thlib.ui.table.services import TableServicesController
from thlib.ui.workspace_models.windows import FloatingWindowModel
import tests.test_table_service_workflows as workflows
import tests.test_frame_table as frames
from tests.test_columns_table_view import _TableController, _TableColumns


class Locale(QObject):
    changed = Signal()
    value = 'en'

    @Property(str, notify=changed)
    def current_language(self):
        return self.value


class CatalogWorker(QObject):
    result = Signal(object)
    error = Signal(object)

    def __init__(self):
        super().__init__()
        self.cancel = Mock()

    def start(self):
        pass


class RelatedObjectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item
    click = frames.FrameTableTests.click

    def prepare(self):
        app = workflows.Application()
        app.window_model = FloatingWindowModel({})
        app._sessions = {'test': SimpleNamespace(tabs=[app.tab])}
        app.open_window = app.window_model.show_window
        source = Mock()
        owner = Mock()
        owner.get_project.return_value.stypes = {'demo/shot': Mock(), 'demo/asset': Mock()}
        source.get_stype.return_value = owner
        source.get_related_sobjects_tel_string.side_effect = lambda **kw: '@SOBJECT(' + ('demo/shot' if kw['child_stype'] is owner.get_project.return_value.stypes['demo/shot'] else 'demo/asset') + ')'
        app.node = SimpleNamespace(node_id='A', node_type='sobject', title='Episode 01',
            search_key='demo/episode?project=demo&code=EP01', source=source)
        app.relation_menu_actions = lambda key: [
            dict(title='Shots', icon='sobject', command='related:child:demo/shot', canCreate=True),
            dict(title='Assets', icon='sobject', command='related:child:demo/asset', canCreate=False),
            dict(title='Related objects', command='open_related_objects')]
        services = TableServicesController(app)
        related = RelatedObjectsController(app, services)
        self.addCleanup(services.shutdown)
        self.addCleanup(related.close)
        self.enterContext(patch('thlib.ui.table.nested.NestedTableController.reload'))
        self.enterContext(patch.object(related, '_load_relations'))
        related.open('A')
        return app, services, related

    def test_standalone_scope_keeps_parent_and_does_not_expand_main_table(self):
        app, services, related = self.prepare()
        self.assertTrue(app.window_model.is_window_visible('related_objects'))
        self.assertTrue(services.scope_visible(related.scope))
        self.assertIsNone(services.nested_row('A'))
        original = related.scope
        self.assertEqual(original.descriptor['parentKey'], app.node.search_key)
        self.assertEqual(original.descriptor['searchType'], 'demo/shot')
        self.assertEqual(original.descriptor['expression'], '@SOBJECT(demo/shot)')
        related.select_relation('related:child:demo/asset')
        self.assertFalse(original.open and services.scope_visible(original))
        self.assertEqual(related.scope.descriptor['searchType'], 'demo/asset')
        self.assertEqual(len(services._nested_scopes), 1)
        app.window_model.close_window('related_objects')
        self.assertIsNone(related.scope)
        self.assertEqual(services._nested_scopes, {})
        self.assertFalse(original._workers)

    def test_context_change_releases_scope_and_window_is_not_restored_open(self):
        app, services, related = self.prepare()
        state = dict(app.window_model._settings)
        restored = FloatingWindowModel(state)
        self.assertFalse(restored.is_window_visible('related_objects'))
        app.tab = object()
        app.results_view_changed.emit()
        self.assertFalse(app.window_model.is_window_visible('related_objects'))
        self.assertIsNone(related.scope)

    def test_context_change_also_releases_descendant_tables(self):
        from thlib.ui.table.nested import NestedTableController
        app, services, related = self.prepare()
        owner = related.scope
        owner._nodes['nested:child'] = SimpleNamespace(search_key='demo/shot?code=CHILD')
        child = NestedTableController(services, 'nested:child', dict(searchType='demo/asset', parentKey='demo/shot?code=CHILD'))
        child.open = True
        services._nested_scopes['child'] = child
        app.tab = object()
        app.results_view_changed.emit()
        self.assertFalse(child.open)
        self.assertEqual(services._nested_scopes, {})

    def test_schema_catalog_adds_general_relations_and_ignores_late_results(self):
        app, services, related = self.prepare()
        original = related.scope
        worker = CatalogWorker()
        pool = SimpleNamespace(is_stopped=False, add_task=lambda *arguments: worker)
        with patch('thlib.tactic_classes.server_start', return_value=object()), \
             patch('thlib.environment.env_inst.server_pool', pool):
            RelatedObjectsController._load_relations(related)
            worker.result.emit([dict(title='Notes', command='related:child:sthpw/note', expression='', canCreate=True)])
            self.app.processEvents()
            self.assertIs(related.scope, original)
            self.assertFalse(related.model['canCreate'])
            related.select_relation('related:child:sthpw/note')
            self.assertEqual(related.scope.descriptor['parentKey'], app.node.search_key)
            self.assertEqual(related.scope.descriptor['searchType'], 'sthpw/note')
            related.close()
            worker.result.emit([dict(title='Late objects', command='related:child:demo/late')])
            self.app.processEvents()
            self.assertEqual(related.model['relations'], [])
            self.assertIsNone(related.scope)
            worker.cancel.assert_not_called()

    def test_stream_relation_catalog_uses_existing_http_read(self):
        import io
        import json
        from types import SimpleNamespace
        from unittest.mock import Mock
        from thlib.ui.related_objects import read_stream_relations

        transport = Mock()
        transport.open.return_value = io.BytesIO(json.dumps({'result': {'relations': [
            dict(search_type='demo/asset', title='Assets', available=True, can_create=False),
            dict(search_type='sthpw/file', title='Files', available=False, can_create=False)
        ]}}).encode())
        server = SimpleNamespace(get_server_name=lambda: 'http://127.0.0.1:1', login_ticket='fixture', transport=transport)
        rows = read_stream_relations(server, 'demo/shot?code=SHOT1', 'demo')
        self.assertEqual(rows, [dict(title='Assets', command='related:child:demo/asset', expression='', canCreate=False)])
        request = transport.open.call_args.args[0]
        self.assertTrue(request.full_url.endswith('/admin/object-relations'))
        self.assertEqual(json.loads(request.data)['search_type'], 'demo/shot')

    def test_real_qml_toolbar_reflows_translates_and_creates_in_own_scope(self):
        app, services, related = self.prepare()
        scope = related.scope
        class Columns(_TableColumns):
            def shutdown(self):
                pass
        self.enterContext(patch('thlib.ui.table.nested_columns.NestedColumnsController', side_effect=lambda _scope: Columns()))
        from thlib.ui.workspace_models.results_types import WorkspaceNode
        scope.tableModel.replace_nodes([WorkspaceNode('nested:SHOT01', 'sobject', 'demo/shot?code=SHOT01', 'SHOT01', 'SH010')])
        scope._model.update(columns=[dict(name='name', title='Name', width=240, cell=dict(kind='text'))],
            rows=[dict(key='SHOT01', nodeId='nested:SHOT01', record=dict(name='SH010'), cells=dict(name=dict(text='SH010')))], loaded=True)
        locale = Locale()
        context = dict(localizationController=locale, appController=_TableController(),
            columnsEditorController=_TableColumns(), userModel=None,
            administrationController=None, tableServicesController=services)
        from thlib.ui.icon_font import qml_icon_bindings
        context.update(qml_icon_bindings(Path(__file__).resolve().parents[1], self.app))
        window, view = self.create('features/objects/RelatedObjectsView.qml',
            dict(relatedController=related), width=1120, height=700, context=context)
        window.setColor(view.property('theme').property('workspace'))
        view.property('theme').setProperty('popupAnimationsEnabled', False)
        with patch.object(scope, '_edit') as edit:
            self.click(window, self.item(view, 'relatedCreate'))
            edit.assert_called_once_with(None)
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtTest import QTest
        row = self.item(view, 'searchResultTableRow')
        QTest.mouseClick(window, Qt.RightButton, pos=row.mapToScene(QPointF(20, row.height() / 2)).toPoint())
        frames.frame(window)
        menu = view.findChild(QObject, 'nestedRowMenu')
        self.assertTrue(menu.property('visible'))
        self.assertTrue(menu.property('actions'))
        from PySide6.QtGui import QGuiApplication
        popup = next((candidate for candidate in QGuiApplication.allWindows() if candidate is not window and candidate.isVisible()), window)
        QTest.keyClick(popup, Qt.Key_Down)
        QTest.keyClick(popup, Qt.Key_Return)
        frames.frame(window)
        self.assertEqual(context['appController'].actions[-1], ('open', 'nested:SHOT01'))
        window.requestActivate()
        frames.frame(window)
        for language in ('en', 'ru'):
            locale.value = language
            locale.changed.emit()
            for width in (1120, 600):
                window.resize(width, 700)
                view.setWidth(width)
                frames.frame(window)
                button = self.item(view, 'relatedCreate')
                self.assertGreaterEqual(button.x(), 0)
                self.assertLessEqual(button.x() + button.width(), width)
                if os.environ.get('RELATED_OBJECTS_OUTPUT'):
                    path = Path(os.environ['RELATED_OBJECTS_OUTPUT'])
                    path.mkdir(parents=True, exist_ok=True)
                    window.grabWindow().save(str(path / f'native-{language}-{width}.png'))
        choice = self.item(view, 'relatedType')
        self.click(window, choice)
        from PySide6.QtQml import QQmlEngine, QQmlExpression
        popup_open = QQmlExpression(QQmlEngine.contextForObject(choice), choice, 'popup.opened')
        from time import monotonic
        deadline = monotonic() + 1
        while not popup_open.evaluate()[0] and monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(popup_open.evaluate()[0])
        choice_window = QGuiApplication.focusWindow() or window
        QTest.keyClick(choice_window, Qt.Key_Down)
        QTest.keyClick(choice_window, Qt.Key_Return)
        frames.frame(window)
        self.assertEqual(related.scope.descriptor['searchType'], 'demo/asset')


if __name__ == '__main__':
    unittest.main()
