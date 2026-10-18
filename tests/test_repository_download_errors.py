"""HTTP errors own response streams even when opening raises before a with block."""
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
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


if __name__ == '__main__':
    unittest.main()
