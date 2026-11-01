"""Native table ports use existing owners and preserve row/draft context."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import QObject, Signal, Slot, Property, Qt
from PySide6.QtTest import QTest
import tests.test_frame_table as frames
import tests.test_sobject_link as links
from thlib.ui.table.services import TableServicesController
from thlib.ui.workspace_models.windows import FloatingWindowModel


class Application(QObject):
    is_stream_server = True
    signing_out=Signal()
    project_changed=Signal()
    results_view_changed=Signal()
    selected_node_changed=Signal()
    item_fields_updated=Signal(str, object)
    def __init__(self):
        super().__init__()
        self.tab=SimpleNamespace(table_view='table')
        self._current_project_code='demo'
        self.selected_result_node_ids=[]
        self.can_manage_tools=True
        self.repository_sync=Mock()
        self.window_model=Mock()
        self.window_model.is_window_visible.return_value=False
        self.open_window=Mock()
        self._notify=Mock()
        self._current_tab=lambda:self.tab
        self._node_for_any=lambda identity:self.node
        self.node=SimpleNamespace(search_key='demo/asset?project=demo&code=A',source=SimpleNamespace(get_value=lambda name:'GROUP0002' if name=='code' else 'crew'))


class Ports(QObject):
    def __init__(self):
        super().__init__(); self.calls=[]
    @Slot(str,'QVariantMap')
    def run_script(self,node,cell):self.calls.append(('script',node,dict(cell)))
    @Property(bool,constant=True)
    def busy(self):return False
    @Slot(str)
    @Slot(str, str)
    def insert_record(self,view,operation=''):
        self.calls.append(('insert',view,operation) if operation else ('insert',view))
    @Slot(str)
    def open_link(self,href):self.calls.append(('url',href))
    @Slot(str,str,'QVariantMap')
    def open_task_action(self,action,node,cell):self.calls.append((action,node,dict(cell)))
    @Slot(str,'QVariantMap','QVariantList')
    def open_links(self,node,cell,keys):self.calls.append(('links',node,dict(cell),list(keys)))
    @Slot(str,'QVariantMap','QVariantList')
    def open_ingest(self,node,cell,files):self.calls.append(('ingest',node,dict(cell),list(files)))


class TableServiceWorkflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=frames.gui_test_application()
    create=frames.FrameTableTests.create
    close=frames.FrameTableTests.close
    item=frames.FrameTableTests.item
    click=frames.FrameTableTests.click

    def test_insert_keeps_the_open_object_or_task_editor_context(self):
        for window_id in ('add_sobject', 'task_editor'):
            application = Application()
            application.window_model = FloatingWindowModel({})
            application._active_stype = lambda: object()
            original = dict(mode='edit', sobject=object(), draft='Unsaved current record')
            application._sobject_editor_request = original
            application.window_model.show_window(window_id)
            raised = self.enterContext(patch.object(application.window_model, 'raise_window', wraps=application.window_model.raise_window))
            owner = TableServicesController(application)
            self.addCleanup(owner.shutdown)
            owner.insert_record('multi_publish')
            self.assertIs(application._sobject_editor_request, original)
            application.open_window.assert_not_called()
            raised.assert_called_once_with(window_id)

    def test_native_custom_layout_click_keeps_its_script_and_external_link(self):
        ports=Ports()
        window,view=self.create('features/table/ServiceCell.qml',dict(controller=frames._TableController(),nodeId='A',services=ports,administration=None,
            cell=dict(text='',targetSearchKey='demo/asset?code=A',layoutNodes=[
                dict(kind='action',text='Edit Script Link',javascript='alert(bvr.kwargs.search_key)'),
                dict(kind='link',text='Open document',href='https://example.com/document')])),height=110)
        self.click(window,self.item(view,'customLayout_0'))
        self.assertEqual(ports.calls[0][0:2],('script','A'))
        self.assertEqual(ports.calls[0][2]['displayOptions']['cbjs_action'],'alert(bvr.kwargs.search_key)')
        self.click(window,self.item(view,'customLayout_1'))
        self.assertEqual(ports.calls[1],('url','https://example.com/document'))

    def test_native_parallel_bar_and_accessible_label_open_existing_task_owner(self):
        ports=Ports()
        cell=dict(text='',targetSearchKey='demo/asset?code=A',steps=3,barHeight=3,groups=[dict(process='PIPE/model',label='MODEL',bars=[
            dict(search_key='sthpw/task?code=T',taskCode='T',process='model',percent=66,color='#aabbcc')],children=[])])
        window,view=self.create('features/table/ServiceCell.qml',dict(controller=frames._TableController(),nodeId='A',services=ports,administration=None,cell=cell),height=90)
        self.click(window,self.item(view,'parallelTask_0_0'))
        self.assertEqual(ports.calls[0][0:2],('task-details','A'))
        self.assertEqual(ports.calls[0][2]['actionTaskCode'],'T')
        self.assertEqual(ports.calls[0][2]['actionProcess'],'model')
        self.click(window,self.item(view,'parallelProcess_0'))
        self.assertEqual(ports.calls[1][2]['actionProcess'],'model')

    def test_parallel_process_children_toggle_without_opening_tasks(self):
        ports = Ports()
        cell = dict(steps=1, barHeight=3, groups=[dict(process='__nested', label='ROOT', bars=[],
            children=[dict(process='child', label='CHILD', bars=[], children=[])])])
        window, view = self.create('features/table/ServiceCell.qml', dict(controller=frames._TableController(),
            nodeId='A', services=ports, administration=None, cell=cell), width=600, height=100)
        self.assertFalse(any(item.property('text') == 'CHILD' for item in frames._visual_items(view)))
        self.click(window, self.item(view, 'parallelExpand_0'))
        self.assertTrue(any(item.property('text') == 'CHILD' for item in frames._visual_items(view)))
        self.click(window, self.item(view, 'parallelExpand_0'))
        self.assertFalse(any(item.property('text') == 'CHILD' for item in frames._visual_items(view)))
        self.assertEqual(ports.calls, [])

    def test_configured_group_uses_code_and_loaded_focus_owner(self):
        app=Application();admin=Mock(projectLocked=False)
        owner=TableServicesController(app,administration=admin)
        owner._script_session=dict(tab=app.tab,node_id='A')
        owner._open_port(dict(type='groups',options=dict(search_key=app.node.search_key)))
        admin.focus_group.assert_called_once_with('GROUP0002')
        admin.select_section.assert_called_once_with('groups')

    def test_drop_opens_prepared_existing_link_window_without_writing(self):
        app=Application();link_owner=SimpleNamespace(_busy=False,_dirty=False,_uncertain=False)
        owner=TableServicesController(app,links=link_owner)
        cell=dict(targetSearchKey=app.node.search_key,acceptedType='demo/asset',tableView='table',columnName='assets',expectedRevision='old',links=[],relation=dict(relationship='instance',instance_type='demo/asset_in_asset'))
        with patch('thlib.environment.env_inst.get_stype_by_code',return_value=object()):owner.open_links('A',cell,[])
        app.open_window.assert_called_once_with('link_sobjects')
        self.assertTrue(app._sobject_link_request['_prepared'])
        self.assertEqual(app._sobject_link_request['table_drop']['expected_revision'],'old')
        self.assertEqual(app._sobject_link_request['table_drop']['links'],[])

    def test_document_window_is_native_modeless_and_never_restored_with_stale_context(self):
        model=FloatingWindowModel({})
        record=next(row for row in model._windows if row.window_id=='table_document')
        self.assertFalse(record.blocking)
        self.assertIn('table_document',model._context_required_windows)
        self.assertTrue((Path(frames.QML)/model._content_sources['table_document']).is_file())

    def test_header_insert_uses_first_click_and_custom_view(self):
        from thlib.ui.workspace_models.results import WorkspaceItemModel
        ports=Ports();columns=frames._TableColumns()
        columns._columns=[dict(row=0,name='update',label='Update',width=70,kind='commands',resolvedClass='pyasm.widget.table_element_wdg.UpdateWdg',displayOptions=dict(insert_view='insert_review'))]
        window,view=self.create('SearchResultTable.qml',dict(controller=frames._TableController(),columnsController=columns,resultModel=WorkspaceItemModel()),
            height=120,context={'tableServicesController':ports})
        self.click(window,self.item(view,'tableColumnInsert_update'))
        self.assertEqual(ports.calls,[('insert','insert_review')])

    def test_publish_file_control_clears_on_first_click_and_respects_busy(self):
        model = frames.QObject()
        window, view = self.create('SObjectValueEditor.qml', dict(fieldType='file', fieldValue='D:/publish/reference.txt',
            fieldOptions=[], fieldModel=None), width=320, height=44)
        values = []
        view.valueEdited.connect(values.append)
        self.click(window, self.item(view, 'fileInputClear'))
        self.assertEqual(values, [''])
        view.setProperty('editorBusy', True)
        frames.frame(window)
        self.click(window, self.item(view, 'fileInputClear'))
        self.assertEqual(values, [''])

    def test_publish_uses_first_click_custom_view_and_explicit_header_operation(self):
        from thlib.ui.workspace_models.results import WorkspaceItemModel
        controller = frames._TableController()
        cell = dict(publish=True, available=True, publishView='review_publish', targetSearchKey='demo/asset?code=A', preview=dict(image=''))
        window, view = self.create('features/table/ServiceCell.qml', dict(controller=controller,
            services=None, administration=None, nodeId='A', cell=cell), width=120, height=98)
        self.click(window, self.item(view, 'tablePublish'))
        self.assertEqual(controller.table_widget_actions, [('publish', 'A', dict(cell, actionView='review_publish'))])
        view.setProperty('editable', False)
        frames.frame(window)
        self.click(window, self.item(view, 'tablePublish'))
        self.assertEqual(len(controller.table_widget_actions), 1)
        ports = Ports()
        columns = frames._TableColumns()
        columns._columns = [dict(row=0, name='publish', label='Publish', width=90, kind='commands',
            resolvedClass='pyasm.widget.PublishTableElement', displayOptions=dict(multi_publish='true'))]
        window, view = self.create('SearchResultTable.qml', dict(controller=controller, columnsController=columns,
            resultModel=WorkspaceItemModel()), height=120, context={'tableServicesController':ports})
        self.click(window, self.item(view, 'tableColumnInsert_publish'))
        self.assertEqual(ports.calls, [('insert', 'multi_publish', 'publish')])

    def test_real_summary_uses_one_readonly_code_editor_and_switches_groups(self):
        app=Application();owner=TableServicesController(app)
        owner._document=dict(identity='admin',sections=[
            dict(title='first',text='<rules id="first"/>',syntax='xml'),
            dict(title='second',text='<rules id="second"/>',syntax='xml')])
        window,view=self.create('features/table/DocumentView.qml',{},width=700,height=500,
            context={'tableServicesController':owner})
        self.assertEqual(sum(item.objectName()=='tableDocumentSource' for item in frames._visual_items(view)),1)
        self.assertTrue(any(item.property('text')=='<rules id="first"/>' and item.property('readOnly') is True for item in frames._visual_items(view)))
        self.click(window,self.item(view,'tableDocumentGroup'))
        QTest.keyClick(window,Qt.Key_Down);QTest.keyClick(window,Qt.Key_Return)
        frames.frame(window)
        self.assertEqual(view.property('selected'),1)
        self.assertTrue(any(item.property('text')=='<rules id="second"/>' for item in frames._visual_items(view)))
        owner.documentChanged.emit();frames.frame(window)
        self.assertEqual(view.property('selected'),0)

    def test_session_teardown_closes_native_table_confirmations(self):
        app=Application();owner=TableServicesController(app)
        window,view=self.create('features/table/ServiceDialogs.qml',dict(controller=owner),width=700,height=500)
        for signal,name,args in ((owner.templateOpened,'templateConfirm',('demo',)),
                                 (owner.objectActionOpened,'statusConfirm',('retire',{})),
                                 (owner.scriptConfirmation,'scriptConfirm',('Run fixture?',))):
            signal.emit(*args);frames.frame(window)
            popup=view.findChild(QObject,'tableConfirmation_'+name)
            self.assertIsNotNone(popup)
            self.assertTrue(popup.property('opened'))
            owner.shutdown();frames.frame(window)
            self.assertFalse(popup.property('visible'))

    def test_native_file_ingest_cell_routes_to_open_ingest(self):
        ports=Ports()
        cell=dict(drop=True,ingest=True,available=True,targetSearchKey='demo/asset?code=A',context='ingest',checkinMode='default',subcontextMode='{leaf}')
        window,view=self.create('features/table/ServiceCell.qml',dict(controller=frames._TableController(),nodeId='A',services=ports,administration=None,cell=cell),height=90)
        self.click(window,self.item(view,'dropIngest'))
        self.assertEqual(ports.calls,[('ingest','A',cell,[])])

    def test_native_table_schedule_routes_user_project_and_cascade_scopes(self):
        app=Application()
        tasks=Mock()
        owner=TableServicesController(app,tasks=tasks)
        owner.open_task_action('table-schedule','A',dict(targetSearchKey='sthpw/login?code=admin',actionLogin='admin'))
        tasks.open_for_user.assert_called_once_with('admin')
        tasks.set_view_mode.assert_called_with('gantt')
        owner.open_task_action('table-schedule','A',dict(targetSearchKey='sthpw/project?code=demo',actionScope='project'))
        tasks.use_project.assert_called_once_with()
        owner.open_task_action('table-schedule','A',dict(targetSearchKey='demo/seq?code=SQ1',actionParentKeys=['demo/shot?code=SH1','demo/shot?code=SH2']))
        tasks.use_related_objects.assert_called_once_with(['demo/shot?code=SH1','demo/shot?code=SH2'])
