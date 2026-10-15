import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.qt_application import gui_test_application
from test_commit_queue import payload
from thlib.checkin_operation import execute_checkin_payload, prepare_checkin
from thlib.server_checkin_queue import operation_manifest
from thlib.ui.commit_queue import CommitQueueController


SPECIAL = [dict(checkinType=kind) for kind in ('multi_file', 'dir', 'sequence')]
SPECIAL.append(dict(checkinType='file', groupCheckin=True))


class CheckinVersionlessPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.source = self.root / 'source.txt'
        self.source.write_bytes(b'content')
        self.payload = dict(payload(self.source), versionlessMode='copy')
        for name in ('env_read_config', 'env_write_config'):
            mock = patch('thlib.ui.commit_queue.' + name, return_value={})
            mock.start()
            self.addCleanup(mock.stop)

    def test_execution_and_server_manifest_enforce_policy_without_mutating_input(self):
        naming = [('source', {
            'versioned': {'paths': ['versions'], 'names': [['source_v001', '', '.txt']]},
            'versionless': {'paths': ['latest'], 'names': [['source', '', '.txt']]},
        })]
        for index, options in enumerate(SPECIAL):
            with self.subTest(options=options):
                operation = dict(self.payload, **options, onlyVersionless=True)
                inputs = prepare_checkin(operation, resolve_naming=False)
                self.assertFalse(inputs['payload']['updateVersionless'])
                self.assertFalse(inputs['payload']['onlyVersionless'])
                manifest, sources = operation_manifest('one', operation)
                self.assertEqual(sources, [str(self.source)])
                self.assertFalse(manifest['options']['update_versionless'])
                self.assertFalse(manifest['options']['only_versionless'])
                repo = self.root / str(index)
                with patch('thlib.tactic_classes.get_virtual_snapshot', return_value=naming), patch(
                    'thlib.tactic_classes.checkin_snapshot',
                    return_value={'__search_key__': 'sthpw/snapshot?code=TEST'},
                ) as commit:
                    execute_checkin_payload(operation, {'value': [str(repo)]})
                self.assertEqual((repo / 'versions/source_v001.txt').read_bytes(), b'content')
                self.assertFalse((repo / 'latest').exists())
                self.assertFalse(commit.call_args.kwargs['update_versionless'])
                self.assertFalse(commit.call_args.kwargs['only_versionless'])
                self.assertTrue(operation['updateVersionless'])
                self.assertTrue(operation['onlyVersionless'])

    def test_regular_file_with_multiple_inputs_retains_versionless_preferences(self):
        operation = dict(self.payload, checkinType='file', onlyVersionless=True)
        operation['files'] = operation['files'] * 2
        operation['filesDict'] = operation['filesDict'] * 2
        inputs = prepare_checkin(operation, resolve_naming=False)
        manifest, _ = operation_manifest('one', operation)
        self.assertTrue(inputs['payload']['updateVersionless'])
        self.assertTrue(inputs['payload']['onlyVersionless'])
        self.assertTrue(manifest['options']['update_versionless'])
        self.assertTrue(manifest['options']['only_versionless'])

    def test_queue_edits_cannot_enable_latest_for_special_operations(self):
        queue = CommitQueueController()
        self.addCleanup(queue.shutdown)
        for index, options in enumerate(SPECIAL):
            operation = dict(self.payload, **options, context=str(index), onlyVersionless=True)
            identity = queue.add_prepared(operation, 'Special')
            queue.select_row(index)
            for field in ('updateVersionless', 'onlyVersionless'):
                queue.update_selected(field, True)
                self.assertFalse(queue.operation(identity)[field])
                self.assertFalse(queue.selectedRecord[field])
            self.assertFalse(queue.selectedRecord['versionlessAllowed'])
        regular = queue.add_prepared(dict(self.payload, context='regular'), 'Regular')
        queue.select_row(4)
        queue.set_apply_to_checked(True)
        queue.update_selected('onlyVersionless', True)
        self.assertTrue(queue.operation(regular)['onlyVersionless'])
        self.assertTrue(queue.selectedRecord['versionlessAllowed'])
        for operation in list(queue._operations.values())[:4]:
            self.assertFalse(operation['updateVersionless'])
            self.assertFalse(operation['onlyVersionless'])

    def test_restore_normalizes_pending_but_preserves_already_submitted_contract(self):
        special = dict(self.payload, checkinType='sequence', onlyVersionless=True)
        entries = [
            dict(id='pending', payload=dict(special)),
            dict(id='submitted', payload=dict(special, _serverQueue=dict(state='complete'))),
        ]
        with patch('thlib.ui.commit_queue.env_read_config', side_effect=lambda **kw:
                   entries if kw.get('filename') == 'pending' else {}):
            queue = CommitQueueController()
        self.addCleanup(queue.shutdown)
        self.assertFalse(queue.operation('pending')['updateVersionless'])
        self.assertFalse(queue.operation('pending')['onlyVersionless'])
        self.assertTrue(queue.operation('submitted')['updateVersionless'])
        self.assertTrue(queue.operation('submitted')['onlyVersionless'])
        manifest, _ = operation_manifest('submitted', queue.operation('submitted'))
        self.assertTrue(manifest['options']['update_versionless'])
        self.assertTrue(manifest['options']['only_versionless'])
