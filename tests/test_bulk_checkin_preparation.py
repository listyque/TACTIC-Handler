"""Bulk queue persistence, bounded naming and independent results."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal
from tests import test_commit_queue as fixtures
payload = fixtures.payload
from thlib import tactic_query as tq


class Executor(QObject):
    preparationChanged = Signal()
    operationFinished = Signal(bool, str)
    preparedValidationFinished = Signal(str, bool, 'QVariantMap', str)
    serverStateChanged = Signal()

    def __init__(self):
        super().__init__()
        self._application = SimpleNamespace(server_state='online', server_state_changed=self.serverStateChanged)
        self.chunks = []

    def validate_prepared_operation(self, request_id, operation):
        self.chunks.append([(request_id, operation)])

    def validate_prepared_operations(self, operations):
        self.chunks.append(operations)

    def complete(self, chunk, fail_at=-1):
        for index, (request_id, operation) in enumerate(chunk):
            self.preparedValidationFinished.emit(request_id, index != fail_at,
                                                 {'virtualSnapshot': []}, 'bad naming' if index == fail_at else '')


class BulkPreparationTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.CommitQueueTest.setUpClass.__func__)
    setUp = fixtures.CommitQueueTest.setUp

    def test_bulk_save_and_model_insert_happen_once_and_duplicates_stay_pending(self):
        with patch.object(self.queue, '_save') as save:
            ids = self.queue.add_prepared_many([(payload(f'/input/{index}.txt'), 'Asset') for index in range(1200)])
            save.assert_called_once()
        self.assertEqual(self.queue.count, 1200)
        self.assertEqual(len(set(ids)), 1200)
        duplicate = self.queue.add_prepared_many([(payload('/input/0.txt'), 'Duplicate')])
        self.assertEqual(duplicate, [ids[0]])
        self.assertEqual(self.queue.count, 1200)
        self.assertTrue(self.queue.duplicatePending)

    def test_only_one_fifty_item_chunk_runs_and_failure_does_not_stop_the_rest(self):
        executor = Executor()
        self.queue.attach_executor(executor)
        self.queue.add_prepared_many([(payload(f'/input/{index}.txt'), 'Asset') for index in range(1200)])
        self.assertEqual(len(executor.chunks), 1)
        completed = 0
        while self.queue._validation_inflight:
            chunk = executor.chunks[completed]
            self.assertLessEqual(len(chunk), 50)
            executor.complete(chunk, fail_at=3 if completed == 0 else -1)
            completed += 1
        self.assertEqual(completed, 24)
        self.assertEqual(sum(row['status'] == 'Prepared' for row in self.queue.model._records), 1199)
        self.assertEqual(sum(row['status'] == 'Invalid' for row in self.queue.model._records), 1)
        self.assertEqual(self.queue._pending_validations, {})

    def test_new_generation_ignores_stale_result_and_uses_latest_payload(self):
        executor = Executor()
        self.queue.attach_executor(executor)
        ids = self.queue.add_prepared_many([(payload(f'/input/{index}.txt'), 'Asset') for index in range(51)])
        first = list(executor.chunks[0])
        self.queue._operations[ids[0]]['description'] = 'edited'
        self.queue._request_validation(ids[0])
        executor.complete(first)
        self.assertEqual(self.queue.model._records[0]['status'], 'Validating')
        next_chunk = executor.chunks[1]
        edited = next(value for request_id, value in next_chunk if request_id.startswith(ids[0] + ':'))
        self.assertEqual(edited['description'], 'edited')
        executor.complete(next_chunk)
        self.assertEqual(self.queue.model._records[0]['status'], 'Prepared')

    def test_server_mode_never_requests_virtual_snapshots(self):
        executor = Executor()
        self.queue.attach_executor(executor)
        self.queue.set_server_queue(True)
        self.queue.add_prepared_many([(payload(f'/input/{index}.txt'), 'Asset') for index in range(1200)])
        self.assertEqual(executor.chunks, [])
        self.assertTrue(all(row['canCommit'] for row in self.queue.model._records))

    def test_batch_reexecutes_each_naming_and_does_not_swallow_callback_failure(self):
        arguments = [{'version': index} for index in range(5)]
        with patch.object(tq, 'get_virtual_snapshot_extended', side_effect=lambda version:json.dumps({'unique':version})) as call:
            results = json.loads(tq.get_virtual_snapshots_extended(arguments))
        self.assertEqual(call.call_count,5)
        self.assertEqual([item['result'] for item in results],[{'unique':index} for index in range(5)])
        def naming(version):
            if version == 2:
                raise ValueError('per-file failure')
            return json.dumps({'unique':version})
        with patch.object(tq,'get_virtual_snapshot_extended',side_effect=naming) as call:
            with self.assertRaisesRegex(ValueError,'per-file failure'):
                tq.get_virtual_snapshots_extended(arguments)
        self.assertEqual(call.call_count,3)
        with self.assertRaises(ValueError):
            tq.get_virtual_snapshots_extended(arguments * 11)
