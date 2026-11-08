"""Optional queue transport and client recovery use the real controller and files."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE','Material')
os.environ.setdefault('QT_QUICK_BACKEND','software')
os.environ.setdefault('QSG_RENDER_LOOP','basic')
from PySide6.QtGui import QGuiApplication
from thlib.server_checkin_queue import operation_manifest, submit_batch, remove_committed_sources
from thlib.ui.commit_queue import CommitQueueController
from tests.test_commit_queue import payload


class ServerCheckinQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        # Offscreen Windows Qt does not always discover system fonts.
        font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/segoeui.ttf"
        if font_path.is_file():
            from PySide6.QtGui import QFontDatabase
            QFontDatabase.addApplicationFont(str(font_path))

    def setUp(self):
        self.enterContext(patch('thlib.environment.get_server_api', return_value='stream'))
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source = Path(self.temporary.name) / 'source.txt'
        self.source.write_bytes(b'abcdefgh')
        self.payload = payload(self.source)
        for name in ('env_read_config','env_write_config'):
            p = patch('thlib.ui.commit_queue.' + name,return_value={})
            p.start(); self.addCleanup(p.stop)
        self.queue = CommitQueueController()
        self.addCleanup(self.queue.shutdown)

    def add(self, name='first'):
        self.queue.set_server_queue(True)
        operation_id = self.queue.add_prepared(dict(self.payload,context=name),name)
        self.queue._operations[operation_id]['_serverQueue'] = dict(batch_id='batch',project='demo')
        return operation_id

    def test_legacy_is_default_and_bulk_manifest_does_not_resolve_naming(self):
        self.assertFalse(self.queue.serverQueue)
        with patch('thlib.tactic_classes.get_virtual_snapshot',side_effect=AssertionError('naming RPC')):
            manifest,paths = operation_manifest('one',self.payload)
        self.assertEqual(paths,[str(self.source)])
        self.assertEqual(manifest['options']['source_files'][0]['sha256'],hashlib.sha256(b'abcdefgh').hexdigest())
        self.assertNotIn('source_path',manifest['options']['source_files'][0])
        with self.assertRaises(ValueError):
            operation_manifest('one',dict(self.payload,dccScene={'clientId':'maya'}))

    def test_parts_are_bounded_and_resume_preserves_chunk_identities(self):
        calls = []
        def accept(_server,_ticket,_project,action,value,uploads=None,opener=None):
            calls.append((value,uploads,opener))
            return dict(accepted=True)
        operations = [dict(operation_id='one',payload=self.payload)]
        with patch('thlib.server_checkin_queue.request',side_effect=accept), patch('thlib.server_checkin_queue.PART_SIZE',3), patch('thlib.server_checkin_queue.CHUNK_FILES',2):
            submit_batch('server','ticket','demo','batch',operations)
            first = calls[:]; calls.clear()
            submit_batch('server','ticket','demo','batch',operations)
        self.assertEqual([value for value,_,_ in first],[value for value,_,_ in calls])
        self.assertEqual(b''.join(content for _,contents,_ in first for content in contents),b'abcdefgh')
        self.assertTrue(all(len(content)<=3 for _,contents,_ in first for content in contents))
        self.assertEqual(len({id(opener) for _,_,opener in first}),1)
        self.assertEqual([len(value['operations']) for value,_,_ in first],[1,0])

    def test_interrupted_upload_keeps_entire_batch_and_cannot_start_legacy_or_remove(self):
        ids = [self.add('first'),self.add('second')]
        batch = dict(batch_id='batch',project='demo',submitted=False,uploadError='',
                     operations=[dict(operation_id=op,payload=self.queue.operation(op)) for op in ids])
        self.queue._server_batches['batch'] = batch
        self.queue._server_submission_failed('connection lost')
        self.assertTrue(self.queue.serverResumeAvailable)
        self.queue.remove_row(0)
        self.assertEqual(self.queue.count,2)
        with patch.object(self.queue,'_send_server_batches') as retry:
            self.queue.retry_current()
        self.assertEqual(retry.call_args.args[0],[batch])
        self.assertEqual(len(batch['operations']),2)

    def test_cancel_uses_server_lock_state_and_does_not_offer_a_second_commit(self):
        operation_id = self.add()
        batch = dict(batch_id='batch',submitted=False,uploadError='',operations=[dict(operation_id=operation_id)])
        self.queue._server_batches['batch'] = batch
        self.queue._set_record(operation_id,status='Queued',canCommit=False)
        self.queue._server_cancelled(batch,dict(states={operation_id:'locked'}))
        self.assertEqual(self.queue.selectedRecord['status'],'Running')
        self.assertFalse(self.queue.selectedRecord['canCommit'])
        self.assertTrue(self.queue.busy)

    def test_updates_are_idempotent_and_refresh_is_combined(self):
        ids = [self.add('first'),self.add('second')]
        for operation_id in ids:
            self.queue._operations[operation_id]['context'] = 'publish'
        application = Mock()
        executor = Mock(_application=application,_script_triggers=None)
        self.queue._executor = executor
        self.queue._auto_clean = False
        self.queue._server_batches['batch'] = dict(submitted=True,operations=[dict(operation_id=op) for op in ids])
        completed = []
        self.queue.operationCompleted.connect(completed.append)
        result = dict(checkins=[dict(batch_id='batch',operation_id=op,state='complete',revision=index,
                                    snapshot=dict(code='SNAP'+str(index),version=index)) for index,op in enumerate(ids,1)],
                      checkinCursors={'batch':2},checkinsHasMore=False)
        self.queue._server_updates(result)
        self.queue._server_updates(result)
        self.assertEqual(len(completed),2)
        self.assertEqual(application.refresh_checkin_result.call_count,1)
        self.assertFalse(self.queue._server_batches)
        self.assertFalse(self.queue.busy)

    def test_restored_accepted_work_does_not_require_sources_and_close_stops_poll(self):
        operation_id = self.add()
        operation = self.queue.operation(operation_id)
        self.source.unlink()
        with patch('thlib.ui.commit_queue.env_read_config',return_value=[dict(id=operation_id,payload=operation)]):
            self.queue.model._records.clear()
            self.queue._operations.clear()
            self.queue._restore()
        self.assertEqual(self.queue.selectedRecord['status'],'Queued')
        self.queue.shutdown()
        self.queue._server_updates_failed('late reply')
        self.assertFalse(self.queue._server_timer.isActive())

    def test_uncertain_server_result_cannot_be_retried(self):
        operation_id = self.add()
        self.queue._server_batches['batch'] = dict(submitted=True, operations=[dict(operation_id=operation_id)])
        self.queue._server_updates(dict(checkins=[dict(batch_id='batch', operation_id=operation_id,
            state='error', uncertain=True, error='Worker stopped')], checkinCursors={'batch': 1}))
        self.assertEqual(self.queue.selectedRecord['status'], 'Result unknown')
        self.queue.commit_all()
        self.assertFalse(self.queue.selectedRecord['canCommit'])
        self.assertTrue(self.queue.operation(operation_id)['_serverQueue']['uncertain'])

    def test_explicit_clear_resets_finished_progress_even_after_auto_clean(self):
        self.queue._server_progress['finished'] = dict(totalOperations=2, completed=2)
        self.queue._server_progress_error = 'old error'
        self.queue._server_progress_timer.start()
        signals = []
        self.queue.progressChanged.connect(lambda: signals.append(self.queue.serverProgress))
        self.queue.clear()
        self.assertEqual(self.queue.serverProgress, {})
        self.assertEqual(self.queue._server_progress_error, '')
        self.assertFalse(self.queue._server_progress_timer.isActive())
        self.assertEqual(signals, [{}])

    def test_clear_preserves_pending_server_work_and_its_progress(self):
        operation_id = self.add()
        self.queue._set_record(operation_id, status='Queued')
        batch = dict(submitted=True, operations=[dict(operation_id=operation_id)])
        self.queue._server_batches['batch'] = batch
        self.queue._server_progress['batch'] = dict(totalOperations=1)
        self.queue._server_progress_timer.start()
        before = self.queue.serverProgress
        self.queue.clear()
        self.assertEqual(self.queue.count, 1)
        self.assertEqual(self.queue.serverProgress, before)
        self.assertIs(self.queue._server_batches['batch'], batch)
        self.assertTrue(self.queue._server_progress_timer.isActive())

    def test_manual_clear_completed_resets_progress_when_queue_becomes_empty(self):
        operation_id = self.queue.add_prepared(self.payload, 'completed')
        self.queue._set_record(operation_id, status='Completed')
        self.queue._server_progress['finished'] = dict(totalOperations=1, completed=1)
        self.queue.remove_completed()
        self.assertEqual(self.queue.count, 0)
        self.assertEqual(self.queue.serverProgress, {})

    def test_move_removes_only_confirmed_unchanged_bytes(self):
        operation = dict(self.payload,mode='move',_serverSourceHashes={self.source.as_posix():hashlib.sha256(b'abcdefgh').hexdigest()})
        self.source.write_bytes(b'changed')
        with self.assertRaises(OSError):
            remove_committed_sources(operation)
        self.assertTrue(self.source.exists())
        self.source.write_bytes(b'abcdefgh')
        remove_committed_sources(operation)
        self.assertFalse(self.source.exists())

    def test_cancel_failure_retains_active_poll_and_network_error_clears_on_recovery(self):
        operation_id = self.add()
        self.queue._set_record(operation_id,status='Queued',canCommit=False)
        worker = object()
        self.queue._server_poll_worker = worker
        self.queue._server_updates_failed('network unavailable',from_cancel=True)
        self.assertIs(self.queue._server_poll_worker,worker)
        self.assertEqual(self.queue.selectedRecord['error'],'network unavailable')
        self.queue._server_updates(dict(checkins=[],checkinCursors={'batch':0}))
        self.assertEqual(self.queue.selectedRecord['error'],'')
        self.assertFalse(self.queue.selectedRecord['canCommit'])

    def test_before_hook_veto_stops_submission_and_retry_skips_completed_hooks(self):
        from types import SimpleNamespace
        ids = [self.add('first'),self.add('second')]
        calls, veto = [], [True]
        class Hooks:
            def run_before(self,action,context,finished):
                calls.append(context['context'])
                finished(not (veto[0] and context['context']=='second'),'veto')
        self.queue._executor = SimpleNamespace(_script_triggers=Hooks(),_trigger_context=lambda p:p,_worker_error_text=str)
        batch = dict(batch_id='batch',project='demo',server='server',user='user',submitted=False,uploadError='',
                     operations=[dict(operation_id=op,payload=self.queue.operation(op)) for op in ids])
        self.queue._server_batches['batch'] = batch
        pool = Mock()
        with patch('thlib.environment.env_server.get_server',return_value='server'), patch('thlib.environment.env_server.get_user',return_value='user'), patch('thlib.environment.env_server.get_ticket',return_value='ticket'), patch('thlib.environment.env_inst.commit_pool',pool):
            self.queue._send_server_batches([batch])
            self.app.processEvents()
            pool.add_task.assert_not_called()
            self.assertTrue(self.queue.serverResumeAvailable)
            self.assertTrue(batch['operations'][0]['before_hook_done'])
            veto[0] = False
            self.queue.retry_current()
            self.app.processEvents()
            pool.add_task.assert_called_once()
        self.assertEqual(calls,['first','second','second'])

    def test_large_batch_before_hooks_do_not_recurse_on_the_gui_thread(self):
        from types import SimpleNamespace
        completed = []
        class Hooks:
            def run_before(self,action,context,finished):
                completed.append(context['index'])
                finished(True,'')
        self.queue._executor = SimpleNamespace(_script_triggers=Hooks(),_trigger_context=lambda p:p,_worker_error_text=str)
        batch = dict(batch_id='batch',project='demo',server='server',user='user',submitted=False,uploadError='',
                     operations=[dict(operation_id=str(index),payload=dict(index=index)) for index in range(1100)])
        self.queue._server_batches['batch'] = batch
        pool = Mock()
        with patch('thlib.environment.env_server.get_server',return_value='server'), patch('thlib.environment.env_server.get_user',return_value='user'), patch('thlib.environment.env_server.get_ticket',return_value='ticket'), patch('thlib.environment.env_inst.commit_pool',pool):
            self.queue._send_server_batches([batch])
            for _ in range(1200):
                if pool.add_task.called:
                    break
                self.app.processEvents()
            pool.add_task.assert_called_once()
        self.assertEqual(completed,list(range(1100)))

    def test_restart_during_upload_offers_resume_even_without_a_recorded_exception(self):
        operation_id = self.add()
        operation = self.queue.operation(operation_id)
        batch = dict(batch_id='batch',project='demo',server='server',user='user',submitted=False,uploadError='',
                     operations=[dict(operation_id=operation_id,payload=operation,before_hook_done=True)])
        def read(**kwargs):
            if kwargs['filename']=='server_batches':
                return {'batch':batch}
            if kwargs['filename']=='pending':
                return [dict(id=operation_id,payload=operation)]
            return {}
        with patch('thlib.ui.commit_queue.env_read_config',side_effect=read):
            restored = CommitQueueController()
        try:
            self.assertTrue(restored.serverResumeAvailable)
            self.assertFalse(restored.selectedRecord['canCommit'])
        finally:
            restored.shutdown()

    def test_lost_submit_response_is_recovered_from_server_even_without_local_rows(self):
        self.queue._server_batches['batch'] = dict(submitted=False,uploadError='lost reply',operations=[dict(operation_id='gone')])
        self.queue._server_updates(dict(checkins=[dict(batch_id='batch',operation_id='gone',state='complete',revision=1)],
                                        checkinCursors={'batch':1},checkinsHasMore=False))
        self.assertFalse(self.queue._server_batches)
        self.assertFalse(self.queue._server_timer.isActive())

    def test_complete_result_does_not_clean_move_while_upload_worker_is_active(self):
        operation_id = self.add()
        operation = self.queue._operations[operation_id]
        operation['mode'] = 'move'
        self.queue._server_uploading = True
        self.queue._auto_clean = False
        self.queue._server_batches['batch'] = dict(submitted=False,operations=[dict(operation_id=operation_id)])
        result = dict(checkins=[dict(batch_id='batch',operation_id=operation_id,state='complete',revision=1,snapshot=dict(code='SNAP1'))],checkinCursors={'batch':1})
        with patch.object(self.queue,'_finish_server_move') as cleanup:
            self.queue._server_updates(result)
            cleanup.assert_not_called()
            self.queue._server_uploading = False
            self.queue._server_updates(dict(checkins=[],checkinCursors={'batch':1}))
            cleanup.assert_called_once_with(operation_id)

    def test_move_cleanup_keeps_queue_busy_and_closes_auto_clean_after_finishing(self):
        operation_id = self.add()
        operation = self.queue._operations[operation_id]
        operation['mode'] = 'move'
        operation['_serverQueue']['state'] = 'complete'
        self.queue._set_record(operation_id,status='Completed')
        self.queue._server_cleanup_ids.add(operation_id)
        self.queue._window_model = Mock()
        self.queue._auto_clean = True
        self.assertTrue(self.queue.busy)
        self.queue._server_move_finished(operation_id)
        self.assertFalse(self.queue.busy)
        self.assertEqual(self.queue.count,0)
        self.queue._window_model.close_window.assert_called_once_with('commit_queue')

    def test_switch_is_visible_in_empty_queue_and_accepts_mouse_and_keyboard(self):
        from PySide6.QtCore import QObject,QPoint,QPointF,QUrl,Qt,Slot,Property
        from PySide6.QtQml import QQmlComponent,QQmlEngine
        from PySide6.QtQuick import QQuickWindow
        from PySide6.QtTest import QTest
        from thlib.ui.localization import CatalogTranslator
        class Host(QObject):
            @Property(bool,constant=True)
            def clipboardHasImage(self):
                return False
            @Slot(str)
            def open_help(self,_topic):
                pass
            @Slot(str)
            def show_window(self,_window):
                pass
            @Slot(str)
            def prepare_operation(self,_operation):
                pass
        root = Path(__file__).resolve().parents[1]/'thlib/ui'
        translator = CatalogTranslator(root/'translations/ru.json')
        self.app.installTranslator(translator)
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda messages:warnings.extend(message.toString() for message in messages))
        context = engine.rootContext()
        context.setContextProperty('commitQueueController',self.queue)
        context.setContextProperty('commitQueueModel',self.queue.model)
        host = Host()
        for name in ('screenshotController','namingEditorController','windowModel'):
            context.setContextProperty(name,host)
        theme_component = QQmlComponent(engine,QUrl.fromLocalFile(str(root/'qml/Theme.qml')))
        theme = theme_component.createWithInitialProperties(dict(dark=True))
        component = QQmlComponent(engine,QUrl.fromLocalFile(str(root/'qml/CommitQueueView.qml')))
        view = component.createWithInitialProperties(dict(theme=theme))
        self.assertIsNotNone(view,[e.toString() for e in component.errors()])
        window = QQuickWindow()
        view.setParentItem(window.contentItem())
        switch = view.findChild(QObject,'commitQueueServerSwitch')
        self.assertIsNotNone(switch)
        try:
            for width in (720,1280):
                window.resize(width,760);view.setWidth(width);view.setHeight(760)
                window.show();QTest.qWait(30)
                self.assertTrue(switch.property('visible'))
                position = switch.mapToScene(QPointF(20,switch.height()/2))
                right = switch.mapToScene(QPointF(switch.width(),switch.height()))
                dock = view.findChild(QObject,'commitQueueFilesDock')
                boundary = dock.mapToScene(QPointF(dock.width(),dock.height()))
                self.assertLessEqual(right.x(),boundary.x())
                QTest.mouseClick(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,QPoint(round(position.x()),round(position.y())))
                self.assertTrue(self.queue.serverQueue)
                switch.forceActiveFocus()
                QTest.keyClick(window,Qt.Key.Key_Space)
                self.assertFalse(self.queue.serverQueue)
            self.queue._server_uploading = True
            self.queue.stateChanged.emit()
            self.app.processEvents()
            self.assertFalse(switch.property('enabled'))
            self.queue._server_chunk_progress((8,dict(batch_id='display',phase='uploading',
                filename='D:/input/Очень длинное имя файла ' + 'x' * 100 + '.abc',
                bytesDone=8,totalBytes=32,filesDone=1,totalFiles=1200,
                completed=284,totalOperations=1201,failed=1,cancelled=0,running=1)))
            from time import monotonic
            self.queue._server_last_activity=monotonic()-25
            self.queue.progressChanged.emit()
            for width in (720,1280):
                window.resize(width,760);view.setWidth(width);view.setHeight(760)
                QTest.qWait(30)
                indicator=view.findChild(QObject,'commitQueueProgress')
                self.assertTrue(indicator.property('visible'))
                self.assertEqual(view.findChild(QObject,'commitQueueProgressStage').property('text'),'Загружаем файлы')
                self.assertAlmostEqual(view.findChild(QObject,'commitQueueUploadProgress').property('value'),0.25)
                self.assertEqual(view.findChild(QObject,'commitQueueServerProgress').property('value'),285)
                self.assertIn('284 / 1201',view.findChild(QObject,'commitQueueServerSummary').property('text'))
                self.assertIn('Нет нового прогресса 25 с',view.findChild(QObject,'commitQueueProgressElapsed').property('text'))
                edge=indicator.mapToScene(QPointF(indicator.width(),indicator.height()))
                self.assertLessEqual(edge.x(),width)
                self.assertLessEqual(edge.y(),760)
                self.assertGreater(view.findChild(QObject,'commitQueuePrimarySendButton').height(),0)
            self.queue._server_updates_failed('private network failure')
            self.app.processEvents()
            self.assertIn('Нет связи с сервером',view.findChild(QObject,'commitQueueProgressStage').property('text'))
            self.queue._server_uploading = False
            self.queue.stateChanged.emit()

            def click(item):
                from PySide6.QtTest import QSignalSpy
                clicked = QSignalSpy(item.clicked)
                # Respect the shared icon button's duplicate-click window.
                QTest.qWait(int(item.property('duplicateWindow') or 0) + 1)
                position = item.mapToScene(QPointF(item.width()/2, item.height()/2))
                point = QPoint(round(position.x()), round(position.y()))
                QTest.mouseMove(window, point)
                self.app.processEvents()
                QTest.mouseClick(window, Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier, point)
                QTest.qWait(30)
                self.assertEqual(clicked.count(), 1, (item.objectName(), position, item.size()))

            for width in (720, 1280):
                window.resize(width,760);view.setWidth(width);view.setHeight(760)
                self.queue._server_progress['display'] = dict(totalOperations=2, completed=2)
                self.queue.progressChanged.emit()
                QTest.qWait(30)
                clear = view.findChild(QObject, 'commitQueueClearButton')
                dialog = view.findChild(QObject, 'commitQueueClearConfirmation')
                self.assertEqual(self.queue.count, 0)
                self.assertTrue(clear.property('visible'))
                self.assertTrue(clear.property('enabled'))
                click(clear)
                self.assertTrue(dialog.property('visible'))
                from PySide6.QtTest import QSignalSpy
                closed = QSignalSpy(dialog.closed)
                click(view.findChild(QObject, 'commitQueueClearCancelButton'))
                if not closed.count():
                    self.assertTrue(closed.wait(1000))
                self.assertFalse(dialog.property('visible'))
                self.assertTrue(indicator.property('visible'))
                click(clear)
                click(view.findChild(QObject, 'commitQueueClearAcceptButton'))
                self.assertFalse(dialog.property('visible'))
                self.assertEqual(self.queue.serverProgress, {})
                self.assertFalse(indicator.property('visible'))
                self.assertFalse(clear.property('visible'))
            self.assertFalse(warnings,warnings)
        finally:
            window.close();view.deleteLater();window.deleteLater()
            self.app.processEvents()
            self.app.removeTranslator(translator)


    def test_bulk_auto_clean_persists_once_per_response(self):
        self.queue.set_server_queue(True)
        ids = self.queue.add_prepared_many([(dict(self.payload,context=str(i)),str(i)) for i in range(1200)])
        for op in ids:
            self.queue._operations[op]['_serverQueue'] = dict(batch_id='batch',project='demo')
        self.queue._server_batches['batch'] = dict(submitted=True,operations=[dict(operation_id=op) for op in ids])
        result = dict(checkins=[dict(batch_id='batch',operation_id=op,state='complete',snapshot={'code':op}) for op in ids],checkinCursors={'batch':1200})
        with patch.object(self.queue,'_save',wraps=self.queue._save) as save, patch('thlib.server_cache.invalidate_domains'):
            self.queue._server_updates(result)
        self.assertEqual(self.queue.count,0)
        self.assertEqual(save.call_count,1)

    def test_before_hooks_coalesce_persistence(self):
        from types import SimpleNamespace
        hooks = SimpleNamespace(run_before=lambda _action,_context,done:done(True,''))
        self.queue._executor = SimpleNamespace(_script_triggers=hooks,_trigger_context=lambda p:p,_worker_error_text=str)
        batch = dict(batch_id='batch',project='demo',server='server',user='user',submitted=False,uploadError='',operations=[dict(operation_id=str(i),payload={}) for i in range(1200)])
        self.queue._server_batches['batch'] = batch
        pool = Mock()
        with patch('thlib.environment.env_server.get_server',return_value='server'), patch('thlib.environment.env_server.get_user',return_value='user'), patch('thlib.environment.env_server.get_ticket',return_value='ticket'), patch('thlib.environment.env_inst.commit_pool',pool), patch.object(self.queue,'_save') as save:
            self.queue._send_server_batches([batch])
            for _ in range(1300):
                if pool.add_task.called:
                    break
                self.app.processEvents()
            pool.add_task.assert_called_once()
        self.assertLess(save.call_count,30)
        self.assertTrue(all(op['before_hook_done'] for op in batch['operations']))

    def test_progress_counts_only_accepted_bytes_and_preserves_completed_totals(self):
        ids = [self.add('first'), self.add('second')]
        batch = dict(submitted=True,operations=[dict(operation_id=op) for op in ids])
        self.queue._server_batches['batch'] = batch
        self.queue._server_progress['batch'] = dict(totalOperations=2)
        signals=[]
        progress=Mock()
        progress.emit.side_effect=lambda value:(signals.append(value),self.queue._server_chunk_progress(value))
        def accepted(*_args,**_kwargs):
            self.assertLess(self.queue.serverProgress['bytesDone'],8)
            return dict(accepted=True)
        with patch('thlib.server_checkin_queue.request',side_effect=accepted), patch('thlib.server_checkin_queue.PART_SIZE',3), patch('thlib.server_checkin_queue.CHUNK_FILES',2):
            submit_batch('server','ticket','demo','batch',[dict(operation_id=ids[0],payload=self.payload)],progress)
        current=self.queue.serverProgress
        self.assertEqual((current['filesDone'],current['totalFiles'],current['bytesDone'],current['totalBytes']),(1,1,8,8))
        self.assertEqual([info['phase'] for _,info in signals][0],'preparing')
        self.assertEqual(signals[-1][1]['phase'],'uploaded')
        self.assertTrue(any(info['filename']==str(self.source) for _,info in signals))
        with patch('thlib.server_cache.invalidate_domains') as invalidate:
            self.queue._server_updates(dict(checkins=[dict(batch_id='batch',operation_id=op,state='complete',snapshot={'code':op}) for op in ids],checkinCursors={'batch':2}))
        invalidate.assert_called_once()
        self.assertEqual(self.queue.serverProgress['completed'],2)
        self.assertEqual(self.queue.serverProgress['totalOperations'],2)
        self.assertEqual(self.queue.serverProgress['phase'],'finished')
        self.assertFalse(self.queue._server_progress_timer.isActive())

    def test_transport_error_does_not_report_unaccepted_chunk_as_uploaded(self):
        signals=[]
        progress=Mock();progress.emit.side_effect=signals.append
        with patch('thlib.server_checkin_queue.request',side_effect=OSError('connection lost')):
            with self.assertRaises(OSError):
                submit_batch('server','ticket','demo','batch',[dict(operation_id='one',payload=self.payload)],progress)
        self.assertTrue(signals)
        self.assertTrue(all(info['bytesDone']==0 and info['filesDone']==0 for _,info in signals))
        self.assertNotEqual(signals[-1][1]['phase'],'uploaded')

    def test_1200_completed_rows_use_native_config_without_blocking_ui(self):
        import time
        from PySide6.QtCore import QTimer
        from thlib.environment import env_mode, env_write_config
        ids=self.queue.add_prepared_many([(dict(self.payload,context=str(i)),str(i)) for i in range(1200)])
        for op in ids:
            self.queue._operations[op]['_serverQueue']=dict(batch_id='batch',project='demo')
        self.queue._server_batches['batch']=dict(submitted=True,operations=[dict(operation_id=op) for op in ids])
        result=dict(checkins=[dict(batch_id='batch',operation_id=op,state='complete',snapshot={'code':op}) for op in ids],checkinCursors={'batch':1200})
        beats=[time.monotonic()]
        timer=QTimer();timer.setInterval(10);timer.timeout.connect(lambda:beats.append(time.monotonic()));timer.start()
        with patch.object(env_mode,'current_path',self.temporary.name), patch('thlib.ui.commit_queue.env_write_config',wraps=env_write_config) as writes, patch('thlib.server_cache.invalidate_domains'):
            self.queue._server_updates(result)
            self.app.processEvents()
            beats.append(time.monotonic())
        timer.stop()
        self.assertEqual(writes.call_count,2)  # One batch-state file and one pending-state file.
        self.assertEqual(self.queue.count,0)
        self.assertLess(max(b-a for a,b in zip(beats,beats[1:])),1.0)
        self.assertTrue(list(Path(self.temporary.name).rglob('pending.json')))

if __name__ == '__main__':
    unittest.main()
