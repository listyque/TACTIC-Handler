"""HTTP errors own response streams even when opening raises before a with block."""
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from thlib.repository_download import DownloadOperation, SyncTask
from thlib.ui.repository_sync import WorkerSignals


class File:
    def __init__(self, path):
        self.path = path

    def is_exists(self):
        return False

    def prepare_repo(self):
        return str(self.path)


class DownloadErrorsTests(unittest.TestCase):
    def test_http_error_closes_response_and_retains_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'file.dat'
            response = io.BytesIO(b'missing')
            error = HTTPError('http://example.invalid/file.dat', 404, 'Not Found', {}, response)
            task = SyncTask('id', 'key', File(path), 'File', 'publish', str(path), error.url, 1)
            signals = WorkerSignals()
            failed = []
            signals.failed.connect(lambda task_id, message, trace: failed.append((task_id, message, trace)))
            with patch('thlib.repository_download.UrllibTransport.open', side_effect=error) as request:
                DownloadOperation(task, signals, retries=2).run()
            self.assertTrue(response.closed)
            request.assert_called_once()
            self.assertEqual(failed[0][0], 'id')
            self.assertIn('404', failed[0][1])
            self.assertIn('HTTPError', failed[0][2])
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def task(self, path, policy):
        return SyncTask('test', 'key', SimpleNamespace(is_exists=lambda: False, prepare_repo=lambda: str(path)),
            'File', 'checkout', str(path), 'http://example.invalid/file.dat', 6, overwrite_policy=policy)

    def signals(self):
        return SimpleNamespace(**{name: Mock() for name in ('finished', 'failed', 'progress', 'cancelled')})

    def test_local_file_created_during_transfer_is_not_overwritten(self):
        for policy in ('cancel', 'skip', 'overwrite'):
            with self.subTest(policy=policy), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'file.dat'
                class Response(io.BytesIO):
                    headers = {'Content-Length': '6'}
                    def read(self, *args):
                        if self.tell() == 0:
                            path.write_bytes(b'local changes')
                        return super().read(*args)
                signals = self.signals()
                with patch('thlib.repository_download.UrllibTransport.open', return_value=Response(b'remote')):
                    DownloadOperation(self.task(path, policy), signals, retries=0).run()
                self.assertEqual(path.read_bytes(), b'remote' if policy == 'overwrite' else b'local changes')
                self.assertEqual(list(Path(temporary).iterdir()), [path])
                self.assertFalse(signals.failed.emit.called)
                if policy == 'cancel':
                    signals.cancelled.emit.assert_called_once_with('test')
                    self.assertFalse(signals.finished.emit.called)
                else:
                    self.assertEqual(signals.finished.emit.call_count, 1)
                    self.assertEqual(bool(signals.finished.emit.call_args.args[1].get('skipped')), policy == 'skip')

    def test_cancel_at_end_of_response_does_not_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'file.dat'
            task = self.task(path, 'cancel')
            class Response(io.BytesIO):
                headers = {'Content-Length': '6'}
                def read(self, *args):
                    chunk = super().read(*args)
                    if not chunk:
                        task.cancel.set()
                    return chunk
            signals = self.signals()
            with patch('thlib.repository_download.UrllibTransport.open', return_value=Response(b'remote')):
                DownloadOperation(task, signals, retries=0).run()
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(temporary).iterdir()), [])
            signals.cancelled.emit.assert_called_once_with('test')
            self.assertFalse(signals.finished.emit.called)


if __name__ == '__main__':
    unittest.main()
