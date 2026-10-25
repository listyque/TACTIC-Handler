"""Native program hooks and captured client context, on owned files only."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')

from tactic_handler_api.automation import run_checkin_program
from thlib.ui.checkin_out import CheckinOutController


class AutomationTests(unittest.TestCase):
    def test_cancel_during_before_hook_never_starts_checkin(self):
        callbacks = []
        controller = SimpleNamespace(operationBusy=False, _operation_cancel_event=threading.Event(),
            _operation_id=3, preparationChanged=SimpleNamespace(emit=lambda: None),
            _script_triggers=SimpleNamespace(run_before=lambda action, context, ready: callbacks.append(ready)),
            _trigger_context=lambda payload: {}, _operation_cancelled=Mock())
        with patch.object(CheckinOutController, '_start_operation_now') as start:
            CheckinOutController._start_operation(controller, {}, {}, True)
            controller._operation_cancel_requested = True
            callbacks[0](True, '')
            start.assert_not_called()
        controller._operation_cancelled.assert_called_once_with(3)

    def test_real_program_success_failure_timeout_missing_and_multiple_files(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input file.bin'
            source.write_bytes(b'original')
            payload = dict(files=[dict(path=str(source))], operation_id='owned-test')
            result = run_checkin_program([sys.executable, '-c', 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_text())', '{file}'], payload)
            self.assertIn('original', result[0]['stdout'])
            with self.assertRaisesRegex(RuntimeError, 'code 7'):
                run_checkin_program([sys.executable, '-c', 'raise SystemExit(7)'], payload)
            with self.assertRaises(subprocess.TimeoutExpired):
                run_checkin_program([sys.executable, '-c', 'import time; time.sleep(5)'], payload, timeout=.05)
            with self.assertRaises(ValueError):
                run_checkin_program([str(Path(directory) / 'absent.exe')], payload)
            payload['files'].append(dict(path=str(source)))
            with self.assertRaises(ValueError):
                run_checkin_program([sys.executable, '{file}'], payload)
            self.assertEqual(source.read_bytes(), b'original')

    def test_checkin_context_contains_captured_paths_identity_and_completed_snapshot(self):
        data = dict(projectCode='one', searchKey='cg/shot?project=one&code=SH001', context='publish',
                    operation_id='operation-one', files=[dict(path='D:/owned/input.bin')],
                    _serverSnapshot=dict(__search_key__='sthpw/snapshot?project=one&code=SNAP001'))
        context = CheckinOutController._trigger_context(SimpleNamespace(), data)
        self.assertEqual(context['operation_id'], 'operation-one')
        self.assertEqual(context['files'], data['files'])
        self.assertEqual(context['result_search_key'], data['_serverSnapshot']['__search_key__'])
        data['files'][0]['path'] = 'changed'
        self.assertEqual(context['files'][0]['path'], 'D:/owned/input.bin')


if __name__ == '__main__':
    unittest.main()
