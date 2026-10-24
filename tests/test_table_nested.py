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

    def test_file_table_filters_by_filename_instead_of_internal_code(self):
        from unittest.mock import patch
        from thlib.environment import env_inst
        from thlib.ui.table.nested import NestedTableController
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows
        app = workflows.Application()
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
            fixture = Path(__file__).parent / 'fixtures/frame_controls/NestedRecursive.qml'
            window, view = self.create(str(fixture.resolve()),dict(controller=_TableController(),
                columnsController=_TableColumns(),services=owner,scope=scope),width=600,height=320)
            self.click(window,self.item(view,'tableServiceAction_0'))
            branch = owner.nested_row(identity)
            self.assertIsNotNone(branch)
            branch_key = 'demo/asset?code=C'
            branch_id = 'nested:child:' + branch_key
            branch._nodes[branch_id] = SimpleNamespace(search_key=branch_key)
            branch._model.update(loaded=True,columns=columns,rows=[dict(key=branch_key,nodeId=branch_id,
                record=dict(code='C'),cells=dict(code=dict(text='C')))])
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
            self.click(window,self.item(view,'tableSummary_0'))
            self.assertEqual(owner.nested_row(identity).descriptor['searchType'],'sthpw/task')
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

    def test_sortable_nested_headers_have_a_visible_label_and_first_click_sort(self):
        scope=Scope()
        scope.state['columns'][0]['sortable']=True
        window,view=self.create('features/table/NestedTableView.qml',dict(controller=_TableController(),
            columnsController=_TableColumns(),userModel=None,services=None,administration=None,scope=scope),width=600,height=320)
        label=self.item(view,'nestedHeaderText_name')
        self.assertEqual(label.property('text'),'Name')
        self.assertGreater(label.property('paintedWidth'),0)
        self.click(window,self.item(view,'nestedHeader_name'))
        self.assertEqual(scope.events[-1][0],dict(type='sort',value='name'))

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
            self.assertIs(args['parent_sobject'], app.node.source)
            self.assertTrue(callable(editor.call_args.kwargs['refresh']))
