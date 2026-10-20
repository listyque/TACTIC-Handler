"""Snapshot attachment uses one captured draft and the real shared form."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Signal, Qt
from PySide6.QtGui import QGuiApplication, QInputMethodEvent, QImage
from thlib.ui.table.file_append import SnapshotAppendController
from thlib.ui.workspace_models.windows import FloatingWindowModel
import tests.test_frame_table as frames


class TableAppendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()
    create = frames.FrameTableTests.create
    click = frames.FrameTableTests.click
    item = frames.FrameTableTests.item
    def close(self, window, view, engine, warnings, owners):
        frames.FrameTableTests.close(self, window, view, engine, warnings, owners)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def owner(self):
        app = SimpleNamespace(window_model=Mock(), _notify=Mock(), debug_log=None, refresh_snapshot_browser=Mock())
        owner = SnapshotAppendController(app)
        self.addCleanup(owner.shutdown)
        owner._open = True
        owner._model.update(ready=True, title='Hero Robot', version=7, process='publish', context='publish')
        owner._scope = dict(searchKey='sthpw/snapshot?code=S7', expectedRevision='revision-seven', existingNames=[], uploadDirectory='append_'+'a'*32)
        return owner

    def test_real_form_first_click_keep_name_remove_and_discard(self):
        owner = self.owner()
        owner._add_records([dict(path='D:/fixture/reference.txt', title='reference.txt', size=10)])
        window, view = self.create('features/table/SnapshotAppendView.qml', dict(owner=owner), width=760, height=750)
        self.assertFalse(owner.model['keepFileName'])
        self.click(window, self.item(view, 'objectCheckinKeepNameText'))
        self.assertTrue(owner.model['keepFileName'])
        self.click(window, self.item(view, 'objectCheckinField_fileType'))
        from PySide6.QtTest import QTest
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        event = QInputMethodEvent()
        event.setCommitString('reference')
        QGuiApplication.sendEvent(window.activeFocusItem(), event)
        self.click(window, self.item(view, 'objectCheckinKeepNameText'))
        self.assertEqual(owner.model['fileType'], 'reference')
        self.click(window, self.item(view, 'objectCheckinFileRemove_0'))
        self.assertEqual(owner.files.rowCount(), 0)
        owner._add_records([dict(path='D:/fixture/reference.txt', title='reference.txt', size=10)])
        owner.changed.emit()
        owner.request_close()
        self.assertTrue(owner.model['discard'])
        owner.activate(dict(type='continue'))
        self.assertTrue(owner.isOpen)
        owner.activate(dict(type='discard'))
        self.assertFalse(owner.isOpen)

    def test_submit_captures_snapshot_revision_files_and_options(self):
        owner = self.owner()
        server = Mock()
        server.get_project.return_value = 'cg'
        owner._server = server
        owner._source_key = 'sthpw/snapshot?code=CURRENT'
        completed = []
        owner.completed.connect(completed.append)
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'reference.txt'
            path.write_text('retain original', encoding='utf-8')
            owner._add_records(owner._file_records([str(path),str(path)]))
            self.assertEqual(owner.files.rowCount(), 1)
            owner.activate(dict(type='field', field='fileType',value='reference'))
            owner.activate(dict(type='field', field='keepFileName',value=True))
            with patch.object(owner, '_run') as run, patch('thlib.tactic_classes.execute_procedure_serverside', return_value=dict(state='saved',searchKey='sthpw/snapshot?code=S7')) as execute:
                owner.activate(dict(type='submit'))
                operation, accept = run.call_args.args
                self.assertFalse(run.call_args.kwargs['write_started'].is_set())
                result = operation()
                self.assertTrue(run.call_args.kwargs['write_started'].is_set())
                server.upload_file.assert_called_once_with(str(path), upload_subdir='append_'+'a'*32)
                self.assertEqual(execute.call_args.args[1], dict(search_key='sthpw/snapshot?code=S7', action='save',expected_revision='revision-seven',filenames=['reference.txt'],file_type='reference',keep_file_name=True, upload_directory='append_'+'a'*32))
                accept(result)
            self.assertEqual(path.read_text(encoding='utf-8'), 'retain original')
            self.assertFalse(owner.isOpen)
            self.assertEqual(completed, ['sthpw/snapshot?code=S7','sthpw/snapshot?code=CURRENT'])
            owner._application.refresh_snapshot_browser.assert_called_once_with()

    def test_cancellation_before_write_never_mutates_the_snapshot(self):
        owner=self.owner(); owner._server=Mock()
        owner._add_records([dict(path='D:/fixture/reference.txt', title='reference.txt', size=10)])
        with patch.object(owner,'_run') as run, patch('thlib.tactic_classes.execute_procedure_serverside') as execute:
            owner.activate(dict(type='submit'))
            owner._cancel.set()
            with self.assertRaises(InterruptedError): run.call_args.args[0]()
            self.assertFalse(run.call_args.kwargs['write_started'].is_set())
            execute.assert_not_called()

    def test_window_is_native_modal_and_not_restored_without_context(self):
        windows=FloatingWindowModel({})
        window=next(row for row in windows._windows if row.window_id=='snapshot_append')
        self.assertTrue(window.blocking)
        self.assertEqual((window.width, window.height), (760, 820))
        self.assertIn('snapshot_append', windows._context_required_windows)
        self.assertTrue((Path(frames.QML)/windows._content_sources['snapshot_append']).is_file())

    def test_worker_failure_marks_only_started_writes_as_uncertain(self):
        import threading
        from thlib.environment import env_inst
        class Worker(QObject):
            result=Signal(object);error=Signal(object);settled=Signal(object)
            def start(self):pass
            def cancel(self):pass
        for started in (False,True):
            owner=self.owner(); worker=Worker(); marker=threading.Event()
            if started:marker.set()
            pool=Mock(is_stopped=False);pool.add_task.return_value=worker
            with patch.object(env_inst,'server_pool',pool):
                owner._run(lambda:None,lambda result:None,write_started=marker)
                worker.error.emit((dict(exception=OSError('connection lost')),worker))
                worker.settled.emit(worker)
                self.app.processEvents()
            self.assertEqual(owner.model['appendUncertain'],started)
            self.assertFalse(owner.busy)
            self.assertFalse(owner._workers)

    def test_cancelled_clipboard_result_is_cleaned_even_when_worker_suppresses_result(self):
        from thlib.environment import env_inst
        class Worker(QObject):
            result=Signal(object);error=Signal(object);settled=Signal(object)
            def start(self):pass
            def cancel(self):pass
        owner=self.owner(); worker=Worker();operations=[]
        pool=Mock(is_stopped=False)
        def task(operation):operations.append(operation);return worker
        pool.add_task.side_effect=task
        cleanup=Mock()
        with patch.object(env_inst,'local_pool',pool):
            owner._run(lambda:['generated image'],lambda result:None,local=True,stale=cleanup)
            operations[0]()
            owner.shutdown()
            worker.settled.emit(worker)
            self.app.processEvents()
            operations[1]()
        cleanup.assert_called_once_with(['generated image'])

    def test_invalid_file_type_never_starts_upload(self):
        owner=self.owner()
        owner._add_records([dict(path='D:/fixture/reference.txt',title='reference.txt',size=10)])
        for value in ('', 'a'*129, 'bad\ntype'):
            owner.activate(dict(type='field',field='fileType',value=value))
            with patch.object(owner,'_run') as run:
                owner.activate(dict(type='submit'))
                run.assert_not_called()
            self.assertEqual(owner.model['error'],'Choose a valid file type')
            self.assertEqual(owner.files.rowCount(),1)

    def test_failed_clipboard_encoding_removes_the_partial_generated_file(self):
        owner=self.owner();image=Mock();image.isNull.return_value=False;image.copy.return_value=image
        paths=[]
        def failed_save(filename,format):
            path=Path(filename);path.write_bytes(b'partial image');paths.append(path);return False
        image.save.side_effect=failed_save
        with patch('PySide6.QtGui.QGuiApplication.clipboard',return_value=SimpleNamespace(image=lambda:image)),patch.object(owner,'_run') as run:
            owner._paste_image()
            with self.assertRaisesRegex(OSError,'clipboard image'):
                run.call_args.args[0]()
        self.assertTrue(paths)
        self.assertFalse(paths[0].exists())

    def test_ctrl_v_pastes_text_normally_and_an_image_through_the_existing_owner(self):
        from PySide6.QtTest import QTest
        owner=self.owner();clipboard=QGuiApplication.clipboard()
        self.addCleanup(clipboard.clear)
        clipboard.setText('reference-from-clipboard')
        window,view=self.create('features/table/SnapshotAppendView.qml',dict(owner=owner),width=760,height=750)
        self.click(window,self.item(view,'objectCheckinField_fileType'))
        QTest.keyClick(window,Qt.Key_A,Qt.ControlModifier)
        QTest.keyClick(window,Qt.Key_V,Qt.ControlModifier)
        frames.frame(window)
        self.assertEqual(owner.model['fileType'],'reference-from-clipboard')
        image=QImage(8,8,QImage.Format_ARGB32);image.fill(Qt.red)
        clipboard.setImage(image)
        window.requestActivate()
        frames.frame(window)
        self.assertTrue(window.isActive())
        with patch.object(owner,'_paste_image') as paste:
            QTest.keyClick(window,Qt.Key_V,Qt.ControlModifier)
            frames.frame(window)
            paste.assert_called_once_with()
        self.assertEqual(owner.model['fileType'],'reference-from-clipboard')

    def test_directories_and_more_than_50_files_leave_the_selection_unchanged(self):
        owner=self.owner()
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'not directories'):
                owner._file_records([directory])
        owner._add_records([dict(path='D:/fixture/a.txt',title='a.txt',size=1)])
        with self.assertRaisesRegex(ValueError,'50 files'):
            owner._add_records([dict(path='D:/fixture/'+str(index)+'.txt',title=str(index)+'.txt',size=1) for index in range(50)])
        self.assertEqual(owner.files.rowCount(),1)

    def test_sdk_upload_subdirectory_reuses_the_existing_upload_transport(self):
        from thlib.side.client.tactic_client_lib import TacticServerStub
        server=TacticServerStub.__new__(TacticServerStub)
        server.transaction_ticket='fixture-ticket';server.site=None;server.server_name='http://example.test'
        with TemporaryDirectory() as directory:
            path=Path(directory)/'source.txt';path.write_bytes(b'original source')
            with patch('thlib.side.client.tactic_client_lib.common.UploadMultipart') as transport:
                server.upload_file(str(path),upload_subdir='append_'+'a'*32)
                transport.return_value.set_subdir.assert_called_once_with('append_'+'a'*32)
                transport.return_value.execute.assert_called_once_with(str(path),None)
            self.assertEqual(path.read_bytes(), b'original source')
