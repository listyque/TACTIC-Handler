"""Queue results stay live while expensive presentation refresh waits for idle."""
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Signal

from thlib.ui.checkin_out import CheckinOutController
from thlib.ui.server_updates import ServerUpdateService
from test_server_checkin_queue import ServerCheckinQueue
from test_server_updates import _Application, _PoolStub


class _Executor(QObject):
    preparationChanged = Signal()
    operationFinished = Signal(bool, str)
    operationResult = Signal(object)
    preparedValidationFinished = Signal(str, bool, 'QVariantMap', str)

    def __init__(self):
        super().__init__()
        self._application = Mock(server_state='offline')
        self._script_triggers = Mock()
        self.operationState = 'completed'
        self.started = []
        self.accept_start = True

    def start_prepared_operation(self, value):
        self.started.append(value)
        return self.accept_start

    def cancel_checkin(self):
        self.operationState = 'cancelled'

    def _trigger_context(self, payload):
        return payload


class DeferredQueueRefresh(unittest.TestCase):
    setUpClass = classmethod(ServerCheckinQueue.setUpClass.__func__)
    setUp = ServerCheckinQueue.setUp
    add = ServerCheckinQueue.add

    def executor(self):
        executor = _Executor()
        self.queue.attach_executor(executor)
        return executor

    def legacy(self, count=3):
        ids = []
        for index in range(count):
            source = self.source.with_name('source%d.txt' % index)
            source.write_bytes(b'content')
            value = dict(self.payload, files=[{'path': str(source), 'type': 'file'}])
            ids.append(self.queue.add_prepared(value, str(index)))
        return ids, self.executor()

    def event(self, operation_id, batch='batch', state='complete'):
        return dict(batch_id=batch, operation_id=operation_id, state=state,
                    snapshot={'code': 'SNAP-' + operation_id}, error='failed' if state == 'error' else '')

    def test_legacy_refreshes_once_after_all_results_even_with_auto_clean(self):
        ids, executor = self.legacy()
        completed, presentation = [], []
        self.queue.operationCompleted.connect(completed.append)
        self.queue.presentationRefreshRequested.connect(presentation.append)
        with patch('thlib.server_cache.invalidate_domains') as invalidate:
            self.queue.commit_all()
            for index, operation_id in enumerate(ids):
                self.assertTrue(self.queue.busy)
                executor.operationResult.emit({'code': 'SNAP%d' % index})
                executor.operationFinished.emit(True, '')
                self.assertEqual(len(completed), index + 1)
                if index < len(ids) - 1:
                    invalidate.assert_not_called()
                    executor._application.refresh_checkin_result.assert_not_called()
                    self.assertFalse(presentation)
            invalidate.assert_called_once_with(('snapshots', 'relations', 'search', 'activity'), 'demo')
        self.assertFalse(self.queue.busy)
        self.assertEqual(self.queue.count, 0)
        self.assertEqual(len(presentation), 1)
        self.assertEqual(executor._application.refresh_checkin_result.call_args.args[1]['code'], 'SNAP2')
        self.assertTrue(all(p['_refreshTreeOnComplete'] is False for p in executor.started))

    def test_legacy_failure_and_cancel_flush_previous_success(self):
        for state in ('failed', 'cancelled'):
            with self.subTest(state=state):
                self.queue.clear()
                self.queue._executor = None
                ids, executor = self.legacy(2)
                with patch('thlib.server_cache.invalidate_domains') as invalidate:
                    self.queue.commit_all()
                    executor.operationResult.emit({'code': 'SAVED'})
                    executor.operationFinished.emit(True, '')
                    executor._application.refresh_checkin_result.assert_not_called()
                    executor.operationState = state
                    if state == 'cancelled':
                        self.queue.cancel()
                        invalidate.assert_not_called()
                    executor.operationFinished.emit(False, state)
                    invalidate.assert_called_once()
                executor._application.refresh_checkin_result.assert_called_once()
                self.assertEqual(executor._application.refresh_checkin_result.call_args.args[1]['code'], 'SAVED')
                self.assertFalse(self.queue.busy)

    def test_worker_refusal_flushes_previous_success(self):
        ids, executor = self.legacy(2)
        with patch('thlib.server_cache.invalidate_domains') as invalidate:
            self.queue.commit_all()
            executor.operationResult.emit({'code': 'SAVED'})
            executor.accept_start = False
            executor.operationFinished.emit(True, '')
            invalidate.assert_called_once()
        self.assertFalse(self.queue.busy)
        executor._application.refresh_checkin_result.assert_called_once()

    def test_server_waits_for_all_batches_preserving_hooks_progress_and_results(self):
        ids = [self.add(str(i)) for i in range(3)]
        for operation_id in ids:
            self.queue._operations[operation_id]['context'] = 'publish'
        self.queue._operations[ids[2]]['_serverQueue']['batch_id'] = 'last'
        self.queue._server_batches = {
            'batch': dict(submitted=True, operations=[dict(operation_id=op) for op in ids[:2]]),
            'last': dict(submitted=True, operations=[dict(operation_id=ids[2])]),
        }
        executor = self.executor()
        completed, presentation = [], []
        self.queue.operationCompleted.connect(completed.append)
        self.queue.presentationRefreshRequested.connect(presentation.append)
        with patch('thlib.server_cache.invalidate_domains') as invalidate:
            for index, operation_id in enumerate(ids):
                batch = 'last' if index == 2 else 'batch'
                value = dict(checkins=[self.event(operation_id, batch)], checkinCursors={batch: index + 1})
                self.queue._server_updates(value)
                self.assertEqual(len(completed), index + 1)
                self.assertEqual(executor._script_triggers.run_after.call_count, index + 1)
                self.assertEqual(self.queue.count, 2 - index)
                if index < 2:
                    self.assertTrue(self.queue.busy)
                    invalidate.assert_not_called()
                    executor._application.refresh_checkin_result.assert_not_called()
                else:
                    invalidate.assert_called_once()
            self.queue._server_updates(value)
            invalidate.assert_called_once()
        self.assertFalse(self.queue.busy)
        self.assertEqual(len(presentation), 1)
        executor._application.refresh_checkin_result.assert_called_once()
        self.assertEqual(executor._application.refresh_checkin_result.call_args.args[1]['code'], 'SNAP-' + ids[-1])

    def test_status_failure_flushes_known_success_without_resubmitting_or_completing_pending(self):
        ids = [self.add('first'), self.add('second')]
        self.queue._server_batches['batch'] = dict(submitted=True, operations=[dict(operation_id=op) for op in ids])
        executor = self.executor()
        executor._worker_error_text = str
        self.queue._set_record(ids[1], status='Queued')
        with patch('thlib.server_cache.invalidate_domains') as invalidate:
            self.queue._server_updates(dict(checkins=[self.event(ids[0])]))
            invalidate.assert_not_called()
            self.queue._server_updates_failed('connection lost')
            invalidate.assert_called_once()
            self.queue._server_updates_failed('still lost')
            invalidate.assert_called_once()
        executor._application.refresh_checkin_result.assert_called_once()
        self.assertTrue(self.queue.busy)
        self.assertIn('batch', self.queue._server_batches)
        self.assertEqual(self.queue.selectedRecord['stage'], 'waiting for server')

    def test_restored_result_invalidates_cache_without_revealing_old_selection(self):
        operation_id = self.add()
        self.queue._current_session_ids.clear()
        self.queue._server_batches['batch'] = dict(submitted=True, operations=[dict(operation_id=operation_id)])
        executor = self.executor()
        with patch('thlib.server_cache.invalidate_domains') as invalidate:
            self.queue._server_updates(dict(checkins=[self.event(operation_id)]))
            invalidate.assert_called_once()
        executor._application.refresh_checkin_result.assert_not_called()

    def test_completion_does_not_clear_the_next_operations_queue_flag(self):
        controller = CheckinOutController.__new__(CheckinOutController)
        QObject.__init__(controller)
        controller._application = Mock()
        controller._operation_id = 7
        controller._operation_payload = dict(self.payload, _refreshTreeOnComplete=False)
        controller._operation_worker = None
        controller._worker_stages = {}
        controller._operation_inputs = {}
        controller._operation_repository = {}
        controller._script_triggers = None
        controller._queue_operation = True
        controller.operationFinished.connect(
            lambda *_args: setattr(controller, '_queue_operation', True)
        )
        controller._checkin_finished(7, {'code': 'SNAP'})
        self.assertTrue(controller._queue_operation)

    def test_mixed_current_and_restored_results_keep_live_reveal(self):
        ids = [self.add('first'), self.add('second')]
        for operation_id in ids:
            self.queue._operations[operation_id]['context'] = 'publish'
        self.queue._current_session_ids.discard(ids[1])
        self.queue._server_batches['batch'] = dict(submitted=True, operations=[dict(operation_id=op) for op in ids])
        executor = self.executor()
        with patch('thlib.server_cache.invalidate_domains'):
            self.queue._server_updates(dict(checkins=[self.event(op) for op in ids]))
        executor._application.refresh_checkin_result.assert_called_once()
        self.assertEqual(executor._application.refresh_checkin_result.call_args.args[1]['code'], 'SNAP-' + ids[1])

    def test_standalone_checkin_keeps_immediate_cache_invalidation(self):
        for deferred in (False, True):
            with self.subTest(deferred=deferred), patch('thlib.tactic_classes.checkin_snapshot', return_value={'code': 'SNAP'}) as checkin, patch('thlib.server_cache.invalidate_domains') as invalidate:
                result = CheckinOutController._create_snapshot(defer_refresh=deferred, search_key=self.payload['searchKey'])
                self.assertEqual(result, {'code': 'SNAP'})
                checkin.assert_called_once_with(search_key=self.payload['searchKey'])
                self.assertEqual(invalidate.call_count, 0 if deferred else 1)

    def test_background_updates_wait_for_queue_and_keep_inflight_result(self):
        service = ServerUpdateService(_Application())
        self.addCleanup(service.shutdown)
        batches = []
        service.batchReady.connect(batches.append)
        from thlib.environment import env_server
        service._session = (str(env_server.get_server() or ''), str(env_server.get_user() or ''), 'ticket')
        service._running = True
        service._busy = True
        service.set_checkin_active(True)
        result = dict(activity=[{'__event_timestamp__': '2026-10-11 01:00:00'}], cacheChanges=[{'code': 'change'}], cacheCursor='cursor')
        service._ready(result)
        self.assertFalse(batches)
        self.assertEqual(service._cache_cursor, '')
        pool = _PoolStub()
        with patch('thlib.environment.env_inst.server_pool', pool), patch('thlib.environment.env_inst.logins', {'artist': object()}), patch('thlib.environment.env_server.get_ticket', return_value='ticket'), patch('thlib.server_cache.write_cursor') as write_cursor:
            service.poll()
            self.assertIsNone(pool.operation)
            service.set_checkin_active(False)
            self.assertIsNotNone(pool.operation)
            write_cursor.assert_called_once_with('server_changes', 'cursor', 'demo')
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0]['cacheChanges'], result['cacheChanges'])
        self.assertEqual(service._cache_cursor, 'cursor')
        self.assertIsNone(service._deferred_result)

    def test_signout_discards_deferred_background_result(self):
        service = ServerUpdateService(_Application())
        self.addCleanup(service.shutdown)
        batches = []
        service.batchReady.connect(batches.append)
        service._running = True
        service.set_checkin_active(True)
        service._ready({'messages': [{'code': 'private'}]})
        service.stop()
        service.set_checkin_active(False)
        self.assertFalse(batches)


if __name__ == '__main__':
    unittest.main()
