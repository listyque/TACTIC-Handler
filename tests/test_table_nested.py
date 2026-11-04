"""Real input and lifecycle checks for the expanded table renderer."""
import unittest
from types import SimpleNamespace
from PySide6.QtCore import QObject, Property, Signal, Slot, QCoreApplication, QEvent
import tests.test_frame_table as frames
from tests.test_columns_table_view import _TableController, _TableColumns, _visual_items


class Scope(QObject):
    changed = Signal()
    search_text_changed = Signal()
    def __init__(self):
        super().__init__()
        self.state = dict(columns=[dict(name='name', title='Name', width=180, cell=dict(kind='text'))],
            rows=[dict(key='A', nodeId='nested:A', record=dict(name='Robot'), cells=dict(name=dict(text='Robot')))],
            selected=[], busy=False, offset=0, insert=True, loaded=True)
        self.events = []
        from thlib.ui.workspace_models.results import WorkspaceItemModel
        self.native_model = WorkspaceItemModel()
        self.columns = ScopedColumns(self)
        self._focused = ''
        self._anchor = ''
        self._model = self.state
        self._model['selection'] = True
        self.changed.connect(self.sync)
        self.sync()
        from thlib.ui.workspace_models.records import RecordListModel
        from thlib.ui.search_suggestion_data import SEARCH_SUGGESTION_ROLES
        self.suggestions = RecordListModel(SEARCH_SUGGESTION_ROLES)
        self.text = ''
    def sync(self):
        from thlib.ui.workspace_models.results_types import WorkspaceNode
        self._nodes = {row['nodeId']: WorkspaceNode(node_id=row['nodeId'],
            node_type='sobject', search_key=row['key'], code=row['key'],
            title=str(row['record'].get('name') or row['record'].get('code') or row['key']),
            values=row['record']) for row in self.state['rows']}
        signature = repr(self.state['rows'])
        if signature != getattr(self, '_rows_signature', None):
            self._rows_signature = signature
            self.native_model.replace_nodes(list(self._nodes.values()))
        self.columns.stateChanged.emit()
    @Property(QObject, constant=True)
    def tableModel(self): return self.native_model
    @Property(QObject, constant=True)
    def tableColumns(self): return self.columns
    @Property(str, notify=changed)
    def selected_node_id(self): return self._focused
    @Property('QVariantList', notify=changed)
    def selected_result_node_ids(self):
        return [row['nodeId'] for row in self.state['rows'] if row['key'] in self.state['selected']]
    @Property(str, notify=changed)
    def result_group_mode(self): return 'none'
    @Property(str, notify=changed)
    def result_sort_mode(self): return ''
    def node_for(self, identity): return self._nodes.get(identity)
    @Slot(str, str, str, int, bool)
    def select_result_node(self, *args):
        from thlib.ui.table.nested import NestedTableController
        NestedTableController.select_result_node(self, *args)
    @Slot()
    def clear_result_selection(self):
        self.state['selected'] = []
        self.changed.emit()
    @Slot()
    def select_all_result_siblings(self):
        self.state['selected'] = [row['key'] for row in self.state['rows']]
        self.changed.emit()
    @Property(QObject, constant=True)
    def searchSuggestions(self):
        return self.suggestions
    @Property(str, notify=search_text_changed)
    def current_search_text(self):
        return self.text
    @Slot(str)
    def update_search_text(self, value):
        self.text = value
    @Slot(str)
    def request_search_suggestions(self, value):
        self.events.append(('suggest', value))
    @Slot()
    def clear_search_suggestions(self):
        self.suggestions.clear()
    @Slot(str)
    def search(self, value):
        self.events.append(('search', value))
    @Slot(int)
    def accept_search_suggestion(self, row):
        self.events.append(('accept', row))
    @Property('QVariantMap', notify=changed)
    def model(self):
        return self.state
    @Slot('QVariantMap', 'QVariant')
    def activate(self, action, value=None):
        self.events.append((dict(action), value))
        if action['type'] == 'select':
            self.state['selected'] = ['A'] if not self.state['selected'] else []
            self.changed.emit()


class ScopedColumns(_TableColumns):
    def __init__(self, scope):
        super().__init__()
        self.scope = scope
        scope.changed.connect(self.update_cells)
    def update_cells(self):
        self._cell_revision += 1
        self.cellRevisionChanged.emit()
    def shutdown(self):
        pass

    @Property('QVariantList', notify=_TableColumns.stateChanged)
    def visibleColumns(self):
        return [dict(column, row=i, label=column['title'],
                     kind=column.get('cell', {}).get('kind', 'text'))
                for i, column in enumerate(self.scope.model['columns'])]
    @Slot(str, int, result='QVariantMap')
    def row_cells(self, key, _revision):
        return next((row['cells'] for row in self.scope.model['rows'] if row['key'] == key), {})
    @Slot(int, bool)
    def sort_column(self, row, descending):
        self.scope.activate(dict(type='sort', value=self.scope.model['columns'][row]['name'],
                                 direction='desc' if descending else 'asc'), None)
    @Slot(int, str)
    def request_column_focus(self, row, target):
        self.scope.activate(dict(type='columns', column=self.scope.model['columns'][row]['name'] if row >= 0 else ''), None)


def prepare_scope(scope):
    from thlib.ui.workspace_models.results_types import WorkspaceNode
    nodes = [WorkspaceNode(node_id=row['nodeId'], node_type='sobject', search_key=row['key'],
        code=row['key'], title=row['record'].get('code', row['key']), values=row['record'])
        for row in scope._model['rows']]
    scope._nodes = {node.node_id: node for node in nodes}
    scope._table_model.replace_nodes(nodes)
    scope._columns = ScopedColumns(scope)
    scope.changed.connect(scope._columns.stateChanged)


class NestedTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()
    create = frames.FrameTableTests.create
    def close(self, window, view, engine, warnings, owners):
        frames.FrameTableTests.close(self, window, view, engine, warnings, owners)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    click = frames.FrameTableTests.click
    item = frames.FrameTableTests.item

    def test_shared_process_menu_opens_the_same_note_actions(self):
        from PySide6.QtQml import QQmlExpression, qmlContext
        controller = _TableController()
        window, view = self.create('features/objects/ProcessCountMenu.qml', dict(controller=controller),
                                   width=320, height=200)
        expression = QQmlExpression(qmlContext(view), view, 'openProcessCountMenu("asset", "notes", this)')
        expression.evaluate()
        self.assertFalse(expression.hasError(), expression.error().toString())
        frames.frame(window)
        menu = view.findChild(QObject, 'workspaceProcessCountMenu')
        self.assertTrue(menu.property('visible'))
        actions = menu.property('actions').toVariant()
        self.assertTrue(any(action.get('process') == 'publish' for action in actions))
        menu.triggered.emit('publish')
        self.assertEqual(controller.process_details[-1], ('asset', 'notes', 'publish'))
        menu.close()

    def test_nested_table_uses_the_native_suggestion_popup_and_enter(self):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QGuiApplication, QInputMethodEvent
        from PySide6.QtTest import QTest
        scope = Scope()
        window, view = self.create('features/table/NestedTableView.qml', dict(controller=_TableController(),
            columnsController=_TableColumns(), userModel=None, services=None, administration=None, scope=scope),
            width=600, height=320)
        self.click(window, self.item(view, 'tacticSearchInput'))
        event = QInputMethodEvent()
        event.setCommitString('Rob')
        QGuiApplication.sendEvent(window.activeFocusItem(), event)
        QTest.qWait(210)
        self.assertIn(('suggest', 'Rob'), scope.events)
        scope.suggestions.replace([dict(title='Robot', description='Reference', keyword='', code='A', values={}, selected=False)])
        QTest.qWait(50)
        self.assertTrue(self.item(view, 'tacticSearchInput').property('popupOpen'))
        window.requestActivate()
        QTest.qWait(20)
        QTest.keyClick(window, Qt.Key_Down)
        QTest.keyClick(window, Qt.Key_Return)
        frames.frame(window)
        self.assertIn(('accept', 0), scope.events)
        scope.suggestions.clear()
        QTest.qWait(30)
        QTest.keyClick(window, Qt.Key_Return)
        self.assertIn(('search', 'Robot'), scope.events)

    def test_scoped_suggestions_run_off_thread_and_ignore_late_results(self):
        import threading
        import time
        from types import SimpleNamespace
        from unittest.mock import patch
        from PySide6.QtTest import QTest
        from thlib.pool import ThreadsPool
        from thlib.ui.table.nested import NestedTableController
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app = workflows.Application()
        app.columns_editor_controller = SimpleNamespace(_tasks_controller=None)
        services = TableServicesController(app)
        pool = ThreadsPool(max_threads=2)
        self.addCleanup(services.shutdown)
        self.addCleanup(pool.exit)
        scope = NestedTableController(services, 'A', dict(searchType='demo/asset', parentKey=app.node.search_key,
            projectCode='demo', filters=[['status', '=', 'active']]))
        scope.open = True
        release = threading.Event()
        self.addCleanup(release.set)
        calls = []
        def read(_procedure, arguments, **_kwargs):
            calls.append((threading.get_ident(), arguments))
            if arguments['keyword'] == 'Old':
                release.wait(3)
            return dict(searchColumn='name', records=[dict(name=arguments['keyword'], code=arguments['keyword'])])
        with patch('thlib.environment.env_inst.server_pool', pool), \
             patch('thlib.environment.env_inst.get_stype_by_code', side_effect=AssertionError('No client-side type discovery for scoped suggestions')), \
             patch('thlib.tactic_classes.server_start', return_value=object()), \
             patch('thlib.tactic_classes.execute_procedure_serverside', side_effect=read):
            scope.request_search_suggestions('Old')
            deadline = time.monotonic() + 3
            while not calls and time.monotonic() < deadline:
                QTest.qWait(10)
            self.assertTrue(calls)
            scope.request_search_suggestions('New')
            self.assertEqual(scope._pending_suggestion, 'New')
            release.set()
            deadline = time.monotonic() + 3
            while not scope.searchSuggestions._records and time.monotonic() < deadline:
                QTest.qWait(10)
            self.assertEqual([row['title'] for row in scope.searchSuggestions._records], ['New'])
            deadline = time.monotonic() + 3
            while scope._workers and time.monotonic() < deadline:
                QTest.qWait(10)
            self.assertFalse(scope._workers)
            self.assertEqual([row['title'] for row in scope.searchSuggestions._records], ['New'])
        self.assertEqual(len(calls), 2)
        for thread, arguments in calls:
            self.assertNotEqual(thread, threading.get_ident())
            self.assertEqual(arguments['parent_key'], app.node.search_key)
            self.assertEqual(arguments['filters'], [['status', '=', 'active']])
        with patch.object(scope, 'reload'):
            scope.accept_search_suggestion(0)
        self.assertEqual(scope.current_search_text, 'New')
        self.assertEqual(scope._keyword_relation, '=')
        scope.suspend()
        self.assertEqual(scope.searchSuggestions._records, [])

    def test_first_click_selection_and_editor_do_not_change_main_selection(self):
        scope = Scope()
        app = _TableController()
        window, view = self.create('features/table/NestedTableView.qml', dict(controller=app,
            columnsController=_TableColumns(), userModel=None, services=None, administration=None, scope=scope),
            width=600, height=320)
        self.assertEqual(self.item(view,'tableHeaderSurface').property('radius'),0)
        self.assertIsNotNone(self.item(view, 'searchResultTableRowSurface'))
        self.assertFalse(any(item.objectName() == 'nestedDrag' for item in _visual_items(view)))
        self.click(window, self.item(view, 'tableSelection_nested:A'))
        self.assertEqual(scope.state['selected'], ['A'])
        self.assertEqual(app.selections, [])
        self.click(window, self.item(view, 'searchResultTableActions'))
        menu = view.findChild(QObject, 'nestedRowMenu')
        self.assertTrue(menu.property('visible'))
        menu.triggered.emit('open')
        self.assertEqual(app.actions, [('open', 'nested:A')])
        menu.close()

    def test_renderer_fits_a_narrow_surface_and_keeps_its_scrollbars(self):
        scope = Scope()
        scope.state['columns'].append(dict(name='description', title='Description', width=320, cell=dict(kind='text')))
        window, view = self.create('features/table/NestedTableView.qml', dict(controller=_TableController(),
            columnsController=_TableColumns(), userModel=None, services=None, administration=None, scope=scope),
            width=320, height=320)
        from PySide6.QtCore import QPointF
        rows = self.item(view, 'searchResultsTableView')
        footer = self.item(view, 'nestedFooterSurface')
        self.assertGreaterEqual(footer.mapToItem(view, QPointF()).y() - rows.mapToItem(view, QPointF(0, rows.height())).y(), 0)
        self.assertIsNotNone(self.item(view, 'tableHorizontalScrollBar'))

    def test_short_results_fit_the_available_content_and_keep_long_lists_bounded(self):
        scope = Scope()
        window, view = self.create('features/table/NestedTableView.qml', dict(controller=_TableController(),
            columnsController=_TableColumns(), userModel=None, services=None, administration=None, scope=scope),
            width=600, height=177)
        self.assertEqual(view.implicitHeight(), 177)
        scope.state['rows'].append(dict(scope.state['rows'][0], key='B'))
        scope.changed.emit()
        frames.frame(window)
        self.assertEqual(view.implicitHeight(), 235)
        source = scope.state['rows'][0]
        scope.state['rows'] = [dict(source, key=str(index), nodeId='row:'+str(index)) for index in range(40)]
        scope.changed.emit()
        frames.frame(window)
        self.assertEqual(view.implicitHeight(), 320)

    def test_parent_table_uses_free_height_without_reloading_on_resize(self):
        import json
        import os
        from pathlib import Path
        from PySide6.QtCore import QPointF
        from unittest.mock import patch
        from thlib.ui.table.services import TableServicesController
        from thlib.ui.workspace_models.results import WorkspaceItemModel
        from thlib.ui.workspace_models.results_types import WorkspaceNode
        import tests.test_table_service_workflows as workflows
        application = workflows.Application()
        application.columns_editor_controller = SimpleNamespace(_tasks_controller=None)
        owner = TableServicesController(application)
        self.addCleanup(owner.shutdown)
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(node_id='A', node_type='sobject',
            search_key='demo/asset?code=A', code='Parent', title='0 Parent'),
            WorkspaceNode(node_id='NEXT', node_type='sobject', search_key='demo/asset?code=NEXT', code='Next parent', title='1 Next parent')])
        with patch('thlib.ui.table.nested.NestedTableController.reload') as load:
            owner.toggle_nested('A', dict(nestedTable=dict(searchType='demo/asset', view='child',
                parentKey='demo/asset?code=A')))
            scope = owner.nested_row('A')
            columns = [dict(name='code',title='Code',width=160,cell=dict(kind='text')),
                dict(name='expand',title='Details',width=100,cell=dict(kind='text'))]
            scope._model.update(loaded=True, columns=columns,
                rows=[dict(key=str(i),nodeId='child:'+str(i),record=dict(code='Row '+str(i)),
                    cells=dict(code=dict(text='Row '+str(i)),expand=dict(text=''))) for i in range(4)])
            prepare_scope(scope)
            parent_columns = _TableColumns()
            parent_columns._columns = [dict(column,row=i,label=column['title'],kind='text') for i,column in enumerate(columns)]
            parent_columns.cell = lambda key, column: dict(kind='text', text=('Parent' if key.endswith('=A') else 'Next parent') if column == 'code' else '')
            from thlib.ui.icon_font import qml_icon_bindings
            window, view = self.create('SearchResultTable.qml', dict(controller=_TableController(),
                columnsController=parent_columns, resultModel=model, tableServices=owner), width=800, height=650,
                context=qml_icon_bindings(Path(__file__).resolve().parents[1], self.app))
            window.setColor(view.property('theme').property('workspace'))
            parent = next(item for item in _visual_items(view) if item.objectName() == 'searchResultTableRow' and item.property('nodeId') == 'A')
            self.assertEqual(parent.height(), view.property('effectiveRowHeight') + 351)
            load.assert_called_once()
            for height in (350, 650):
                view.setHeight(height)
                window.resize(800, height)
                frames.frame(window)
                viewport = self.item(view, 'searchResultsTableView')
                expected = min(351, viewport.height() - view.property('headerHeight') - view.property('effectiveRowHeight'))
                self.assertEqual(parent.height(), view.property('effectiveRowHeight') + expected)
                load.assert_called_once()
            scope._model['search'] = False
            scope.changed.emit()
            frames.frame(window)
            child = view.property('focusedNestedView')
            self.assertIsNotNone(child)
            self.assertFalse(any(item.objectName() == 'nestedFilter' for item in _visual_items(child)))
            self.assertFalse(any(item.objectName() == 'nestedToolbarSurface' for item in _visual_items(child)))
            body = self.item(child, 'nestedTableBody')
            self.assertEqual(body.y(), 0)
            self.assertFalse(self.item(child, 'nestedReload').property('round'))
            footer = self.item(child, 'nestedFooterSurface')
            self.assertEqual(self.item(child, 'nestedReload').mapToItem(child, QPointF()).y(), footer.mapToItem(child, QPointF()).y() + 4)
            self.assertEqual(self.item(child, 'nestedClose').mapToItem(child, QPointF()).y(), footer.mapToItem(child, QPointF()).y() + 4)
            layer = next(item for item in view.childItems() if item.objectName() == 'nestedFocusLayer')
            self.assertTrue(self.item(layer, 'nestedFocusShadow').isVisible())
            scrim = self.item(layer, 'nestedFocusScrim_0')
            self.assertGreater(scrim.height(), 0)
            self.assertEqual(view.property('nestedFocusBounds').toVariant()['height'], child.height())
            if os.environ.get('TABLE_NESTED_FOCUS_OUTPUT'):
                output = Path(os.environ['TABLE_NESTED_FOCUS_OUTPUT'])
                output.mkdir(parents=True, exist_ok=True)
                window.grabWindow().save(str(output/'native-focus.png'))
                (output/'native-focus.json').write_text(json.dumps(dict(
                    width=window.width(), height=window.height(),
                    bounds=view.property('nestedFocusBounds').toVariant(),
                    bodyY=body.y(), footerY=footer.mapToItem(child, QPointF()).y())), encoding='utf-8')
                captures = []
                theme = view.property('theme')
                for width in (800, 320):
                    view.setWidth(width)
                    window.resize(width, 650)
                    for dark in (True, False):
                        theme.setProperty('dark', dark)
                        frames.frame(window)
                        captures.append(dict(width=width,height=650,dark=dark,
                            bounds=view.property('nestedFocusBounds').toVariant(),
                            bodyY=body.y(),footerY=footer.mapToItem(child,QPointF()).y()))
                        window.grabWindow().save(str(output/f'native-focus-{width}-{dark}.png'))
                (output/'native-focus-matrix.json').write_text(json.dumps(captures),encoding='utf-8')
                view.setWidth(800)
                window.resize(800,650)
                theme.setProperty('dark',True)
                frames.frame(window)
            self.click(window, self.item(layer, 'nestedFocusScrim_0'))
            self.assertIsNone(owner.nested_row('A'))

    def test_expanded_content_fills_the_available_width(self):
        import json
        import os
        from pathlib import Path
        from PySide6.QtCore import QPointF
        from thlib.ui.icon_font import qml_icon_bindings
        captures = []
        for width in (320, 1000):
            scope = Scope()
            scope.state['columns'] = [dict(name='code', title='Code', width=160, cell=dict(kind='text')),
                dict(name='expand', title='Details', width=100, cell=dict(kind='commands'))]
            scope.state['rows'] = [dict(key='demo/asset?code=A', nodeId='A', record=dict(code='A'), cells=dict(
                code=dict(text='A'), expand=dict(actions=[dict(name='nested-table', label='Show related table', icon='chevron-right')])))]
            window, view = self.create('features/table/NestedTableView.qml', dict(controller=_TableController(),
                columnsController=_TableColumns(), userModel=None, services=None, administration=None, scope=scope),
                width=width, height=320, context=qml_icon_bindings(Path(__file__).resolve().parents[1], self.app))
            window.setColor(view.property('theme').property('workspace'))
            view.setHeight(view.implicitHeight())
            window.resize(width, int(view.height()))
            frames.frame(window)
            bounds = {}
            for name in ('nestedFilter', 'nestedReload', 'nestedClose', 'nestedTableBody', 'nestedFooterSurface'):
                item = self.item(view, name)
                position = item.mapToItem(view, QPointF())
                self.assertGreaterEqual(position.x(), 0, name)
                self.assertGreaterEqual(position.y(), 0, name)
                self.assertLessEqual(position.x() + item.width(), width, name)
                self.assertLessEqual(position.y() + item.height(), view.height(), name)
                bounds[name] = dict(x=position.x(), y=position.y(), width=item.width(), height=item.height())
            captures.append(dict(width=width, bounds=bounds))
            if os.environ.get('TABLE_NESTED_OUTPUT'):
                output = Path(os.environ['TABLE_NESTED_OUTPUT'])
                output.mkdir(parents=True, exist_ok=True)
                window.grabWindow().save(str(output/f'native-{width}.png'))
        if os.environ.get('TABLE_NESTED_OUTPUT'):
            (output/'native.json').write_text(json.dumps(captures), encoding='utf-8')

    def test_disclosure_responds_to_first_click_and_uses_its_loading_icon(self):
        from unittest.mock import patch
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        application = workflows.Application()
        owner = TableServicesController(application)
        self.addCleanup(owner.shutdown)
        cell = dict(text='',columnName='tasks',nestedTable=dict(searchType='sthpw/task',view='table',
            parentKey=application.node.search_key),actions=[dict(name='nested-table',label='Show related table',icon='chevron-right')])
        with patch('thlib.ui.table.nested.NestedTableController.reload'):
            window, view = self.create('features/table/ServiceCell.qml',dict(controller=_TableController(),
                nodeId='A',services=owner,administration=None,cell=cell),width=100,height=58)
            import time
            from PySide6.QtTest import QTest
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline and not any(item.objectName() == 'tableServiceAction_0' for item in _visual_items(view)):
                QTest.qWait(5)
            self.click(window,self.item(view,'tableServiceAction_0'))
            scope = owner.nested_row('A',owner.nestedRevision)
            self.assertIsNotNone(scope)
            scope._model['busy'] = True
            scope.changed.emit()
            self.app.processEvents()
            scene = view.property('scene').toVariant()
            self.assertEqual(scene['nodes'][0]['children'][0]['icon'],'loading')
            self.click(window,self.item(view,'tableServiceAction_0'))
            self.assertIsNone(owner.nested_row('A',owner.nestedRevision))
            owner.shutdown()
            self.app.processEvents()

    def test_disclosure_survives_repeated_cell_updates(self):
        import shiboken6
        cell = dict(text='', actions=[dict(name='nested-table', label='History', icon='chevron-right')])
        window, view = self.create('features/table/ServiceCell.qml', dict(controller=_TableController(),
            nodeId='A', services=None, administration=None, cell=cell), width=100, height=58)
        button = self.item(view, 'tableServiceAction_0')
        button.forceActiveFocus()
        for index in range(10):
            view.setProperty('cell', dict(cell, revision=index))
            frames.frame(window)
            self.assertTrue(shiboken6.isValid(button), 'A data refresh recreated the disclosure button')
            self.assertIs(self.item(view, 'tableServiceAction_0'), button)
            self.assertTrue(button.hasActiveFocus())

    def test_disclosure_state_belongs_to_its_row_column_and_scope(self):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFontDatabase
        from PySide6.QtTest import QTest
        import json
        import os
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        from thlib.ui.icon_font import qml_icon_bindings
        for font in ('segoeui.ttf', 'seguisb.ttf'):
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/' + font)
        application = workflows.Application()
        owner = TableServicesController(application)
        self.addCleanup(owner.shutdown)
        history = dict(searchType='sthpw/snapshot', view='history', parentKey=application.node.search_key)
        cells = [dict(text='4 assets', columnName=name, nestedTable=scope,
            displayOptions=dict(icon='FAS_CUBE', label='{@COUNT(demo/asset)} assets'),
            actions=[dict(name='nested-table', label='Show related table', icon='chevron-right')])
            for name, scope in [('history', history), ('tasks', dict(history, view='tasks')), ('history_copy', history)] * 2]
        surfaces = [self.create('features/table/ServiceCell.qml', dict(controller=_TableController(),
            nodeId='B' if index >= 3 else 'A', services=owner, administration=None, cell=cell), width=180, height=58,
            context=qml_icon_bindings(Path(__file__).resolve().parents[1]))
            for index, cell in enumerate(cells)]
        for _, view in surfaces:
            action = view.property('scene').toVariant()['nodes'][0]['children'][0]
            self.assertEqual(action['kind'], 'Action')
            self.assertEqual(action['text'], 'Assets 4')
            self.assertEqual(next(child['icon'] for child in action['children'] if child['id'] == 'tableServiceLeadingIcon'), 'FAS_CUBE')
            self.assertLess(action['width'], view.width())
        captures = []
        def icons():
            self.app.processEvents()
            values = [view.property('scene').toVariant()['nodes'][0]['children'][0]['icon'] for _, view in surfaces]
            captures.append(values)
            return values
        def click(index):
            window, view = surfaces[index]
            self.click(window, self.item(view, 'tableServiceAction_0'))
        with patch('thlib.ui.table.nested.NestedTableController.reload'):
            self.assertEqual(icons(), ['chevron-right'] * 6)
            click(0)
            self.assertEqual(icons(), ['expand-more', 'chevron-right', 'chevron-right', 'chevron-right', 'chevron-right', 'chevron-right'])
            active = owner.nested_row('A')
            active._model['busy'] = True
            active.changed.emit()
            self.assertEqual(icons(), ['loading', 'chevron-right', 'chevron-right', 'chevron-right', 'chevron-right', 'chevron-right'])
            click(1)
            self.assertEqual(icons(), ['chevron-right', 'expand-more', 'chevron-right', 'chevron-right', 'chevron-right', 'chevron-right'])
            click(1)
            self.assertEqual(icons(), ['chevron-right'] * 6)
            click(2)
            self.assertEqual(icons(), ['chevron-right', 'chevron-right', 'expand-more', 'chevron-right', 'chevron-right', 'chevron-right'])
            self.assertFalse(self.item(surfaces[0][1], 'tableServiceAction_0').property('selected'))
            self.assertTrue(self.item(surfaces[2][1], 'tableServiceAction_0').property('selected'))
            click(3)
            self.assertEqual(icons(), ['chevron-right', 'chevron-right', 'expand-more', 'expand-more', 'chevron-right', 'chevron-right'])
            self.assertTrue(self.item(surfaces[3][1], 'tableServiceAction_0').property('selected'))
            parent = owner.nested_row('A')
            parent._nodes['nested:R'] = SimpleNamespace(search_key='sthpw/snapshot?code=R')
            parent._model['rows'] = [dict(key='R', nodeId='nested:R')]
            owner.toggle_nested('nested:R', dict(cells[1], columnName='child', nestedTable=dict(history, view='files')))
            child = owner.nested_row('nested:R')
            self.assertEqual(child.expansionState['column'], 'child')
            self.assertEqual(child.expansionState['scope']['view'], 'files')
            window, view = surfaces[3]
            arrow = self.item(view, 'tableServiceDisclosure')
            from PySide6.QtCore import QPointF
            QTest.mouseClick(window, Qt.LeftButton, pos=arrow.mapToScene(QPointF(8, 8)).toPoint())
            self.assertIsNone(owner.nested_row('B'))
            action = self.item(view, 'tableServiceAction_0')
            window.requestActivate()
            frames.frame(window)
            action.forceActiveFocus()
            frames.frame(window)
            QTest.keyClick(window, Qt.Key_Space)
            frames.frame(window)
            self.assertTrue(owner.nested_row('B').open)
            view.setProperty('editable', False)
            frames.frame(window)
            self.click(window, action)
            self.assertTrue(owner.nested_row('B').open)
        if os.environ.get('TABLE_DISCLOSURE_OUTPUT'):
            output = Path(os.environ['TABLE_DISCLOSURE_OUTPUT'])
            output.mkdir(parents=True, exist_ok=True)
            (output/'native.json').write_text(json.dumps(captures), encoding='utf-8')
            window, view = surfaces[0]
            window.setColor(view.property('theme').property('workspace'))
            window.grabWindow().save(str(output/'native-count-button.png'))

    def test_script_context_uses_the_nested_selection_and_view(self):
        from unittest.mock import patch, Mock
        from types import SimpleNamespace
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app=workflows.Application()
        owner=TableServicesController(app)
        self.addCleanup(owner.shutdown)
        def source(code):
            return SimpleNamespace(get_info=lambda:dict(code=code),get_value=lambda name:code)
        nested=SimpleNamespace(search_key='sthpw/task?code=T',source=source('T'))
        selected=SimpleNamespace(search_key='sthpw/task?code=S',source=source('S'))
        scope=SimpleNamespace(_nodes={'N':nested,'S':selected},model={'selected':[selected.search_key]},descriptor={'view':'nested_tasks'})
        app._node_for_any=lambda identity:{'N':nested,'S':selected}.get(identity)
        app.selected_result_node_ids=['MAIN']
        with patch.object(owner,'scope_for',return_value=scope), patch.object(owner,'_run'), patch('thlib.tactic_classes.server_start',return_value=Mock()), patch('thlib.ui.table.scripts.TableScriptRunner') as runner:
            owner.run_script('N',{'displayOptions':{'cbjs_action':'alert(1)'}})
        context=runner.call_args.args[1]
        self.assertEqual(context['searchKeys'],[selected.search_key])
        self.assertEqual(context['view'],'nested_tasks')
        self.assertEqual(context['records'],{selected.search_key:{'code':'S'}})

    def test_file_table_filters_by_filename_instead_of_internal_code(self):
        from unittest.mock import patch
        from thlib.environment import env_inst
        from thlib.ui.table.nested import NestedTableController
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app = workflows.Application()
        app.columns_editor_controller = SimpleNamespace(_tasks_controller=None)
        owner = TableServicesController(app)
        self.addCleanup(owner.shutdown)
        with patch.object(NestedTableController, 'reload'):
            scope = NestedTableController(owner, 'A', dict(searchType='sthpw/file', view='snapshot_files',
                parentKey='sthpw/snapshot?code=S', projectCode='demo'))
        columns = [dict(name='file_name', className='tactic.ui.table.SnapshotFileElementWdg'),
                   dict(name='code', className='')]
        with patch.object(env_inst, 'projects', {'demo': object()}):
            scope._accept(dict(records=[], hasNext=False, searchType='sthpw/file', layout=dict(columns=columns, rows={})))
        self.assertEqual(scope.model['filterField'], 'file_name')

    def test_time_cell_loads_its_task_and_week_and_rejects_stale_completion(self):
        from unittest.mock import patch, Mock
        from types import SimpleNamespace
        from thlib.ui.work_hours import WorkHoursController
        import tests.test_work_hours as hours
        app = hours._Application()
        app._current_project_code = 'demo'
        with patch.object(WorkHoursController, '_current_login', return_value='artist'):
            owner=WorkHoursController(app)
        self.addCleanup(owner.shutdown)
        record=dict(code='T',__search_key__='sthpw/task?code=T',process='model',project_code='demo')
        server=Mock()
        server.get_by_search_key.return_value=record
        with patch('thlib.tactic_classes.server_start',return_value=server),patch.object(owner,'_run') as run,patch.object(owner,'open_timesheet') as opened,patch('thlib.environment.env_inst.projects',{'demo':SimpleNamespace()}):
            owner.open_table_task('sthpw/task?code=T','2031-04-09')
            operation,accept,_identity = run.call_args.args
            self.assertEqual(operation(),record)
            accept(record)
            self.assertEqual(owner.taskCode,'T')
            self.assertEqual(owner.weekStart,'2031-04-07')
            opened.assert_called_once_with()
        with patch('thlib.tactic_classes.server_start',return_value=server),patch.object(owner,'_run') as run,patch.object(owner,'open_timesheet') as opened:
            owner.open_table_task('sthpw/task?code=T','2031-04-09')
            app._current_project_code='other'
            run.call_args.args[1](record)
            opened.assert_not_called()

    def test_scoped_rows_refresh_from_the_application_event_without_losing_selection(self):
        from thlib.ui.table.nested import NestedTableController
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app = workflows.Application()
        app.columns_editor_controller = SimpleNamespace(_tasks_controller=None)
        owner = TableServicesController(app)
        self.addCleanup(owner.shutdown)
        scope = NestedTableController(owner, 'A', dict(parentKey=app.node.search_key))
        key = 'sthpw/task?code=T'
        scope._model.update(rows=[dict(key=key)], selected=[key])
        app.item_fields_updated.emit('other', [key])
        self.assertFalse(scope._reload_timer.isActive())
        app.item_fields_updated.emit('demo', [key])
        self.assertTrue(scope._reload_timer.isActive())
        self.assertEqual(scope.model['selected'], [key])
        scope.shutdown()

    def test_recursive_scopes_keep_selection_and_cache_and_hide_closed_descendants(self):
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app = workflows.Application()
        app.columns_editor_controller = SimpleNamespace(_tasks_controller=None)
        owner = TableServicesController(app)
        self.addCleanup(owner.shutdown)
        parent = dict(searchType='demo/asset', view='parent', parentKey=app.node.search_key)
        child = dict(parent, view='child')
        columns = [dict(name='code', title='Code', width=160, cell=dict(kind='text')),
            dict(name='expand', title='Details', width=100, cell=dict(kind='commands'))]
        with patch('thlib.ui.table.nested.NestedTableController.reload') as load:
            owner.toggle_nested('A', dict(columnName='parent', nestedTable=parent))
            scope = owner.nested_row('A')
            key = 'demo/asset?code=B'
            identity = 'nested:parent:' + key
            scope._nodes[identity] = SimpleNamespace(search_key=key)
            scope._model.update(loaded=True, columns=columns, rows=[dict(key=key, nodeId=identity,
                record=dict(code='B'),cells=dict(code=dict(text='B'),expand=dict(nestedTable=child,
                    actions=[dict(name='nested-table',label='Show related table',icon='chevron-right')])) )])
            prepare_scope(scope)
            fixture = Path(__file__).parent / 'fixtures/frame_controls/NestedRecursive.qml'
            window, view = self.create(str(fixture.resolve()),dict(controller=_TableController(),
                columnsController=_TableColumns(),services=owner,scope=scope),width=600,height=320)
            import time
            from PySide6.QtTest import QTest
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline and not any(item.objectName() == 'tableServiceAction_0' for item in _visual_items(view)):
                QTest.qWait(5)
            self.click(window,self.item(view,'tableServiceAction_0'))
            branch = owner.nested_row(identity)
            self.assertIsNotNone(branch)
            branch_key = 'demo/asset?code=C'
            branch_id = 'nested:child:' + branch_key
            branch._nodes[branch_id] = SimpleNamespace(search_key=branch_key)
            branch._model.update(loaded=True,columns=columns,rows=[dict(key=branch_key,nodeId=branch_id,
                record=dict(code='C'),cells=dict(code=dict(text='C')))])
            prepare_scope(branch)
            branch.changed.emit()
            self.app.processEvents()
            self.assertIs(owner.scope_for(branch_id),branch)
            branch.activate(dict(type='select',key=branch_key))
            self.assertEqual(scope.model['selected'],[])
            self.assertEqual(branch.model['selected'],[branch_key])
            with patch.object(owner,'report_error') as error:
                owner.toggle_nested(branch_id,dict(columnName='cycle',nestedTable=parent))
                error.assert_called_once_with('This nested table would repeat an ancestor scope')
            owner.close_nested(scope)
            self.assertIsNone(owner.scope_for(branch_id))
            self.assertIsNone(owner.nested_row(identity))
            count=load.call_count
            owner.toggle_nested('A',dict(columnName='parent',nestedTable=parent))
            self.assertEqual(load.call_count,count)
            self.assertIs(owner.nested_row(identity),branch)
            self.assertEqual(branch.model['selected'],[branch_key])
            scope._model['rows'][0]['cells']['expand'] = dict(summary=[dict(label=label,value='2',icon='task',
                nestedTable=dict(parent,searchType=stype)) for stype,label in (('sthpw/task','Tasks'),('sthpw/snapshot','Checkins'))])
            scope.changed.emit()
            self.app.processEvents()
            owner.close_nested(branch)
            frames.frame(window)
            self.click(window,self.item(view,'tableSummary_0'))
            self.assertEqual(owner.nested_row(identity).descriptor['searchType'],'sthpw/task')
            owner.close_nested(owner.nested_row(identity))
            frames.frame(window)
            self.click(window,self.item(view,'tableSummary_1'))
            self.assertEqual(owner.nested_row(identity).descriptor['searchType'],'sthpw/snapshot')
            owner.shutdown()
            self.app.processEvents()

    def test_summary_buttons_switch_between_task_and_snapshot_scopes(self):
        from unittest.mock import patch
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app=workflows.Application()
        owner=TableServicesController(app)
        self.addCleanup(owner.shutdown)
        summary=[dict(label=label,value='2',icon='task',nestedTable=dict(
            searchType=kind,view='table',parentKey=app.node.search_key,projectCode='demo'))
            for kind,label in (('sthpw/task','Tasks'),('sthpw/snapshot','Checkins'))]
        summary.extend([dict(label='Notes',value='3',icon='comment'),dict(label='Work Hours',value='2.5',icon='schedule')])
        with patch('thlib.ui.table.nested.NestedTableController.reload'):
            window,view=self.create('features/table/ServiceCell.qml',dict(controller=_TableController(),
                nodeId='A',services=owner,administration=None,cell=dict(summary=summary)),width=220,height=118)
            label=self.item(view,'tableSummaryText_0')
            self.assertEqual(label.property('text'),'Tasks: 2')
            self.assertGreater(label.property('paintedWidth'),0)
            self.click(window,self.item(view,'tableSummary_0'))
            self.assertEqual(owner.nested_row('A').descriptor['searchType'],'sthpw/task')
            self.click(window,self.item(view,'tableSummary_1'))
            self.assertEqual(owner.nested_row('A').descriptor['searchType'],'sthpw/snapshot')
            owner.shutdown()
            self.app.processEvents()

    def test_nested_headers_use_main_column_sort_menu(self):
        scope=Scope()
        scope.state['columns'][0]['sortable']=True
        window,view=self.create('features/table/NestedTableView.qml',dict(controller=_TableController(),
            columnsController=_TableColumns(),userModel=None,services=None,administration=None,scope=scope),width=600,height=320)
        label=self.item(view,'tableColumnHeaderLabel_name')
        self.assertEqual(label.property('text'),'NAME')
        self.assertGreater(label.property('paintedWidth'),0)
        from PySide6.QtCore import Qt, QPointF
        from PySide6.QtTest import QTest
        header = self.item(view, 'tableColumnContextArea_name')
        QTest.mouseClick(window, Qt.RightButton, Qt.NoModifier,
            header.mapToScene(QPointF(40, 15)).toPoint())
        table = self.item(view, 'nestedMainTable')
        menu = table.findChild(QObject, 'tableColumnContextMenu')
        self.assertTrue(menu.property('visible'))
        menu.triggered.emit('sort:ascending')
        self.assertEqual(scope.events[-1][0],dict(type='sort',value='name',direction='asc'))
        menu.close()

    def test_nested_header_menu_opens_the_selected_column_without_sorting(self):
        from PySide6.QtCore import Qt, QPointF
        from PySide6.QtTest import QTest
        scope = Scope()
        scope.state['gear'] = True
        window, view = self.create('features/table/NestedTableView.qml', dict(controller=_TableController(),
            columnsController=_TableColumns(), userModel=None, services=None, administration=None, scope=scope),
            width=600, height=320)
        header = self.item(view, 'tableColumnContextArea_name')
        QTest.mouseClick(window, Qt.RightButton, Qt.NoModifier,
            header.mapToScene(QPointF(header.width()/2, header.height()/2)).toPoint())
        QTest.qWait(100)
        table = self.item(view, 'nestedMainTable')
        menu = table.findChild(QObject, 'tableColumnContextMenu')
        self.assertTrue(menu.property('visible'))
        actions = menu.property('actions').toVariant()
        self.assertTrue(next(a for a in actions if a.get('command') == 'edit_definition')['enabled'])
        self.assertEqual(scope.events, [])
        menu.triggered.emit('edit_definition')
        self.assertEqual(scope.events[-1][0], dict(type='columns', column='name'))
        menu.close()

    def test_nested_definition_editor_keeps_child_scope_and_admin_guard(self):
        from unittest.mock import Mock
        from thlib.ui.table.services import TableServicesController
        from thlib.ui.table.nested import NestedTableController
        import tests.test_table_service_workflows as workflows
        app = workflows.Application()
        app.columns_editor_controller = SimpleNamespace(_tasks_controller=None)
        app.columns_editor_controller = Mock()
        app.open_columns_editor = Mock()
        owner = TableServicesController(app)
        self.addCleanup(owner.shutdown)
        scope = NestedTableController(owner, 'A', dict(searchType='demo/child', view='child_table', projectCode='other'))
        scope.activate(dict(type='columns', column='name'))
        app.columns_editor_controller.open_scoped_definition.assert_called_once_with('demo/child', 'child_table', 'other', 'name')
        app.open_columns_editor.assert_called_once()
        app.can_manage_tools = False
        scope.activate(dict(type='columns', column='name'))
        app.open_columns_editor.assert_called_once()

    def test_scoped_definition_focus_accepts_a_column_and_preserves_old_callers(self):
        from unittest.mock import patch
        from tests.test_columns_table_view import _Application, _SType
        from thlib.ui.columns_editor import ColumnsEditorController
        controller = ColumnsEditorController(_Application(_SType()))
        with patch.object(controller, 'load_definition_catalog'):
            controller.open_scoped_definition('demo/child', 'child_table', 'other', 'name')
            self.assertEqual(controller.requestedName, 'name')
            self.assertEqual(controller.requestedSearchType, 'demo/child')
            self.assertEqual(controller.requestedView, 'child_table')
            controller.open_scoped_definition('demo/child', 'child_table', 'other')
            self.assertEqual(controller.requestedName, '')

    def test_saved_nested_definition_reloads_its_retained_scope(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from PySide6.QtTest import QTest
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app = workflows.Application()
        app.columns_editor_controller = SimpleNamespace(_tasks_controller=None)
        app._sessions = {'main': SimpleNamespace(tabs=[app.tab])}
        app.columns_editor_controller = Mock()
        app.open_columns_editor = Mock()
        owner = TableServicesController(app)
        self.addCleanup(owner.shutdown)
        with patch('thlib.ui.table.nested.NestedTableController.reload') as load:
            owner.toggle_nested('A', dict(nestedTable=dict(searchType='demo/child',
                view='child_table', parentKey=app.node.search_key)))
            owner.nested_row('A').activate(dict(type='columns', column='name'))
            load.assert_called_once()
            app.results_view_changed.emit()
            QTest.qWait(20)
            self.assertEqual(load.call_count, 2)

    def test_connection_confirmation_captures_the_nested_project(self):
        from unittest.mock import patch,Mock
        from types import SimpleNamespace
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app=workflows.Application()
        owner=TableServicesController(app)
        self.addCleanup(owner.shutdown)
        with patch.object(owner,'scope_for',return_value=SimpleNamespace(descriptor=dict(projectCode='two'))),patch('thlib.tactic_classes.server_start',return_value=Mock()) as server:
            owner.request_connection_removal('nested:row',dict(connectionKey='sthpw/connection?code=C'))
        server.assert_called_once_with(project='two')
        owner.confirm_connection_removal(False)

    def test_filter_sort_page_off_page_selection_and_child_creation(self):
        from types import SimpleNamespace
        from unittest.mock import patch, Mock
        from thlib.ui.table.nested import NestedTableController
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app = workflows.Application()
        app.columns_editor_controller = SimpleNamespace(_tasks_controller=None)
        owner = TableServicesController(app)
        self.addCleanup(owner.shutdown)
        parent = dict(searchType='sthpw/task', view='table', parentKey=app.node.search_key, projectCode='demo', initialLimit=2)
        with patch.object(NestedTableController, 'reload') as load:
            scope = NestedTableController(owner, 'A', parent)
            self.addCleanup(scope.shutdown)
            scope._nodes = {
                'nested:1': SimpleNamespace(search_key='sthpw/task?code=T1', source=SimpleNamespace()),
                'nested:2': SimpleNamespace(search_key='sthpw/task?code=T2', source=SimpleNamespace()),
            }
            scope._model.update(loaded=True, filterField='code', rows=[
                dict(key='sthpw/task?code=T1', nodeId='nested:1', record=dict(code='T1'), cells={}),
                dict(key='sthpw/task?code=T2', nodeId='nested:2', record=dict(code='T2'), cells={}),
            ])
            scope.activate(dict(type='select', key='sthpw/task?code=T1'))
            scope.activate(dict(type='page', value=1))
            self.assertEqual(scope._model['offset'], 2)
            load.assert_called_once_with()
        with patch('thlib.environment.env_inst.projects', {'demo': SimpleNamespace()}), \
             patch('thlib.tactic_classes.SObject', side_effect=lambda record, _project: SimpleNamespace(record=record)):
            scope._accept(dict(searchType='sthpw/task', hasNext=False,
                records=[dict(__search_key__='sthpw/task?code=T3', code='T3')],
                layout=dict(columns=[dict(name='code', title='Code', dataType='string')],
                            rows={'sthpw/task?code=T3': dict(code=dict(text='T3'))})))
        self.assertEqual(scope.model['selected'], ['sthpw/task?code=T1'])
        self.assertIn('nested:1', scope.selected_result_node_ids)
        app.item_fields_updated.emit('demo', ['sthpw/task?code=T1'])
        self.assertTrue(scope._reload_timer.isActive())
        scope._reload_timer.stop()
        with patch.object(NestedTableController, 'reload') as load:
            scope.activate(dict(type='filter', value='rig'))
            scope.activate(dict(type='sort', value='code'))
            self.assertEqual(scope._model['offset'], 0)
            self.assertEqual(scope._model['order'], 'code asc')
            self.assertEqual(scope._model['filter'], 'rig')
            load.assert_called_once_with()
        stype = Mock()
        with patch('thlib.environment.env_inst.get_stype_by_code', return_value=stype) as get_stype, \
             patch('thlib.ui.sobject_editor.open_sobject_editor') as editor:
            scope.activate(dict(type='create'))
            get_stype.assert_called_once_with('sthpw/task', project_code='demo')
            args = editor.call_args.args[1]
            self.assertEqual(args['mode'], 'insert')
            self.assertEqual(args['view'], 'insert')
            self.assertIs(args['parent_sobject'], app.node.source)
            self.assertTrue(callable(editor.call_args.kwargs['refresh']))
            scope.descriptor.update(insertView='schedule_task_edit', editView='schedule_task_edit')
            scope.activate(dict(type='create'))
            self.assertEqual(editor.call_args.args[1]['view'], 'schedule_task_edit')
            scope.activate(dict(type='edit', key='sthpw/task?code=T1'))
            self.assertEqual(editor.call_args.args[1]['mode'], 'edit')
            self.assertEqual(editor.call_args.args[1]['view'], 'schedule_task_edit')
            self.assertIsNone(editor.call_args.args[1]['parent_sobject'])
