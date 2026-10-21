"""Real dependency tree input and captured request lifetime."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtTest import QTest
import tests.test_frame_table as frames
import tests.test_table_service_workflows as fixtures
from thlib.ui.table.services import TableServicesController


class DependencyResponses(QObject):
    received = Signal(str, 'QVariantMap', str)
    fileFailed = Signal(str)

    def __init__(self, fixture, mode='tree'):
        super().__init__()
        self.fixture, self.mode = fixture, mode
        self.calls = []

    @Slot()
    def restart_reads(self):
        self.calls.append(('restart',))

    @Slot('QVariantMap')
    def request(self, request):
        self.calls.append(('read', dict(request)))
        if self.mode == 'loading':
            return
        if self.mode == 'error':
            self.received.emit(request['path'], {}, 'File Offline')
        elif self.mode == 'empty':
            self.received.emit(request['path'], dict(rows=[], hasNext=False, message='No snapshot found'), '')
        else:
            result = self.fixture['range' if 'file_index' in request else 'root' if request['path'] == 'root' else 'child']
            self.received.emit(request['path'], result, '')

    @Slot('QVariantMap')
    def open_file(self, action):
        self.calls.append(('file', dict(action)))


class TableDependencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    def setUp(self):
        from tempfile import TemporaryDirectory
        from thlib.environment import env_mode
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.enterContext(patch.object(env_mode, 'current_path', temporary.name))

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item
    click = frames.FrameTableTests.click

    def data(self):
        return dict(seed=dict(searchKey='S1', projectCode='demo'),
            root=dict(identity='S1',snapshotKey='S1',revision='r1',rows=[
                dict(key='0',kind='reference',group='Upstream',snapshotKey='S2',projectCode='other',revision='r2',parentCode='Arm'),
                dict(key='1',kind='file',group='Files',snapshotKey='S1',projectCode='demo',fileCode='F1',filename='scene.ma')],hasNext=False),
            child=dict(snapshotKey='S2',rows=[dict(key='0',kind='reference',group='Inputs',snapshotKey='S1',parentCode='Cycle')],hasNext=False))

    def test_first_pointer_expands_cached_branch_and_exposes_cycle_without_request(self):
        data = self.data()
        ports = DependencyResponses(data)
        window, view = self.create('features/table/DependenciesView.qml', dict(owner=ports, model=data['seed']), width=700, height=400)
        self.assertEqual(len([call for call in ports.calls if call[0]=='read']), 1)
        self.click(window, self.item(view, 'dependencyExpand_root_0'))
        self.assertEqual(ports.calls[-1][1]['projectCode'], 'other')
        self.assertEqual(ports.calls[-1][1]['expected_revision'], 'r2')
        labels = [item.property('text') for item in frames._visual_items(view)]
        self.assertTrue(any('Cyclic dependency' in str(text) for text in labels))
        self.click(window, self.item(view, 'dependencyExpand_root_0'))
        self.click(window, self.item(view, 'dependencyExpand_root_0'))
        self.assertEqual(len([call for call in ports.calls if call[0]=='read']), 2)
        self.assertTrue(self.item(view, 'dependencyTitle_root_0').property('paintedWidth') > 0)

    def test_file_pointer_and_keyboard_capture_concrete_snapshot_revision(self):
        data = self.data()
        ports = DependencyResponses(data)
        window, view = self.create('features/table/DependenciesView.qml',dict(owner=ports,model=data['seed']),width=700,height=400)
        action = self.item(view, 'dependencyFileOpen_root_1')
        self.click(window, action)
        payload = ports.calls[-1][1]
        self.assertEqual((payload['snapshotKey'],payload['fileCode'],payload['revision']),('S1','F1','r1'))
        action.forceActiveFocus()
        QTest.keyClick(window,Qt.Key_Space)
        frames.frame(window)
        self.assertEqual(len([call for call in ports.calls if call[0]=='file']),2)

    def test_error_retries_once_and_long_lists_keep_shared_scrollbar(self):
        data = self.data()
        ports = DependencyResponses(data,'error')
        window, view = self.create('features/table/DependenciesView.qml',dict(owner=ports,model=data['seed']),width=320,height=240)
        ports.mode='tree'
        data['root']['rows'] *= 50
        data['root']['rows'] = [dict(row,key=str(index)) for index,row in enumerate(data['root']['rows'])]
        self.click(window,self.item(view,'dependencyRetry_root_status'))
        self.assertEqual(len([call for call in ports.calls if call[0]=='read']),2)
        scrollbar=self.item(view,'dependencyScrollBar')
        self.assertTrue(scrollbar.isVisible())
        self.assertGreater(scrollbar.width(),0)
        self.assertLess(len([item for item in frames._visual_items(view) if item.objectName().startswith('dependencyTitle_')]),20)

    def test_document_host_and_native_port_preserve_source_project(self):
        application=fixtures.Application()
        application.debug_log=None
        owner=TableServicesController(application)
        self.addCleanup(owner.shutdown)
        owner.dependencyViewer.open('A',dict(targetSearchKey='sthpw/snapshot?code=S7',projectCode='other'))
        self.assertTrue(owner.document['translateTitle'])
        for descriptor, expected in (({}, 'demo'), ({'projectCode': 'other'}, 'other')):
            with patch.object(owner, '_owner_scope', return_value=SimpleNamespace(descriptor=descriptor)):
                owner.dependencyViewer.open('A', {})
                self.assertEqual(owner.document['projectCode'], expected)
        owner.dependencyViewer.open('A', dict(targetSearchKey='sthpw/snapshot?code=S7', projectCode='other'))
        self.assertEqual(owner.document['projectCode'],'other')
        self.assertEqual(owner.document['searchKey'],'sthpw/snapshot?code=S7')
        with patch.object(owner.dependencyViewer,'request'):
            self.create('features/table/DocumentView.qml',{},width=700,height=500,context={'tableServicesController':owner})
        from thlib import tactic_classes as tc
        server=SimpleNamespace(get_project=lambda:'other')
        request=dict(path='root',search_key='sthpw/snapshot?code=S7',projectCode='other',offset=0,limit=50)
        with patch.object(tc,'server_start',return_value=server),patch.object(tc,'execute_procedure_serverside',return_value={}) as execute,patch.object(owner.dependencyViewer,'_run') as run:
            owner.dependencyViewer.request(request)
            run.call_args.args[0]()
            self.assertEqual(execute.call_args.kwargs['project'],'other')
            self.assertEqual(execute.call_args.args[1]['search_key'],'sthpw/snapshot?code=S7')

    def test_real_worker_is_off_gui_and_late_results_are_discarded_on_close_or_project_change(self):
        import threading
        import time
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst
        from thlib.pool import ThreadsPool
        from thlib.ui.workspace_models.windows import FloatingWindowModel

        application=fixtures.Application()
        application.debug_log=None
        application.window_model=FloatingWindowModel({})
        application.open_window=application.window_model.show_window
        owner=TableServicesController(application)
        pool=ThreadsPool()
        self.enterContext(patch.object(env_inst,'server_pool',pool))
        self.addCleanup(pool.exit)
        self.addCleanup(owner.shutdown)
        received=[]
        owner.dependencyViewer.received.connect(lambda *args:received.append(args))
        gui_thread=threading.get_ident()
        def wait(condition):
            deadline=time.monotonic()+3
            while not condition() and time.monotonic()<deadline:
                self.app.processEvents()
                QTest.qWait(5)
            self.assertTrue(condition())
        with patch.object(tc,'server_start',return_value=SimpleNamespace()):
            for close in (lambda:application.window_model.close_window('table_document'),application.project_changed.emit):
                started,release=threading.Event(),threading.Event()
                def execute(*args,**kwargs):
                    self.assertNotEqual(threading.get_ident(),gui_thread)
                    started.set()
                    if not release.wait(3):
                        raise TimeoutError('test release timed out')
                    return dict(rows=[],hasNext=False)
                with patch.object(tc,'execute_procedure_serverside',side_effect=execute):
                    owner.dependencyViewer.open('A',{})
                    owner.dependencyViewer.request(dict(path='root',projectCode='demo',search_key='S1'))
                    try:
                        wait(started.is_set)
                        close()
                    finally:
                        release.set()
                    wait(lambda:not owner.dependencyViewer._workers)
        self.assertEqual(received,[])
        from xmlrpc.client import Fault
        message='Dependencies changed. Reload this snapshot.'
        with patch.object(tc,'server_start',return_value=SimpleNamespace()),patch.object(tc,'execute_procedure_serverside',side_effect=Fault(501,message)):
            owner.dependencyViewer.open('A',{})
            owner.dependencyViewer.request(dict(path='root',projectCode='demo',search_key='S1'))
            wait(lambda:bool(received))
        self.assertEqual(received[-1][2],message)


    def test_pending_generic_document_cannot_replace_dependencies_or_reopen_closed_window(self):
        from thlib import tactic_classes as tc
        from thlib.ui.workspace_models.windows import FloatingWindowModel
        application=fixtures.Application()
        application.debug_log=None
        application.window_model=FloatingWindowModel({})
        application.open_window=Mock(wraps=application.window_model.show_window)
        owner=TableServicesController(application)
        self.addCleanup(owner.shutdown)
        owner._script_session=dict(tab=application.tab,node_id='A',runner=SimpleNamespace(context=dict(project='demo',searchKey=application.node.search_key),cancel=Mock()))
        command=dict(type='security-summary',options=dict(search_key='sthpw/login?code=admin'))
        with patch.object(tc,'server_start',return_value=SimpleNamespace(get_project=lambda:'demo')),patch.object(owner,'_run') as run:
            owner.open_port(command)
            earlier=run.call_args.args[1]
            owner.dependencyViewer.open('A',{})
            earlier(dict(title='Earlier',sections=[]))
            self.assertEqual(owner.document['kind'],'dependencies')
            owner.open_port(command)
            earlier=run.call_args.args[1]
            application.window_model.close_window('table_document')
            opened=application.open_window.call_count
            earlier(dict(title='Earlier',sections=[]))
            self.assertEqual(application.open_window.call_count,opened)
            self.assertFalse(application.window_model.is_window_visible('table_document'))


if __name__=='__main__':
    unittest.main()
