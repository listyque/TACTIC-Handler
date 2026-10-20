"""Real input and lifecycle checks for the expanded table renderer."""
import unittest
from PySide6.QtCore import QObject, Property, Signal, Slot, QCoreApplication, QEvent
import tests.test_frame_table as frames
from tests.test_columns_table_view import _TableController, _TableColumns


class Scope(QObject):
    changed = Signal()
    def __init__(self):
        super().__init__()
        self.state = dict(columns=[dict(name='name', title='Name', width=180, cell=dict(kind='text'))],
            rows=[dict(key='A', nodeId='nested:A', record=dict(name='Robot'), cells=dict(name=dict(text='Robot')))],
            selected=[], busy=False, offset=0, insert=True)
        self.events = []
    @Property('QVariantMap', notify=changed)
    def model(self):
        return self.state
    @Slot('QVariantMap', 'QVariant')
    def activate(self, action, value):
        self.events.append((dict(action), value))
        if action['type'] == 'select':
            self.state['selected'] = ['A'] if not self.state['selected'] else []
            self.changed.emit()


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

    def test_first_click_selection_and_editor_do_not_change_main_selection(self):
        scope = Scope()
        app = _TableController()
        window, view = self.create('features/table/NestedTableView.qml', dict(controller=app,
            columnsController=_TableColumns(), userModel=None, services=None, administration=None, scope=scope),
            width=600, height=320)
        self.click(window, self.item(view, 'nestedSelect'))
        self.assertEqual(scope.state['selected'], ['A'])
        self.assertEqual(app.selections, [])
        self.click(window, self.item(view, 'nestedEdit'))
        self.assertEqual(scope.events[-1][0], dict(type='edit', key='A'))

    def test_renderer_fits_a_narrow_surface_and_keeps_its_scrollbars(self):
        scope = Scope()
        scope.state['columns'].append(dict(name='description', title='Description', width=320, cell=dict(kind='text')))
        window, view = self.create('features/table/NestedTableView.qml', dict(controller=_TableController(),
            columnsController=_TableColumns(), userModel=None, services=None, administration=None, scope=scope),
            width=320, height=320)
        self.assertEqual(self.item(view, 'nestedRows').height(), 197)
        self.assertIsNotNone(self.item(view, 'nestedHorizontalBar'))

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
