import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from modern_ui.repository_sync import (
    DownloadRunnable,
    SyncTask,
    WorkerSignals,
)
from thlib.tactic_classes import File


class _FilePaths:
    def __init__(self, directory, filename="preview.jpg"):
        self.directory = str(directory)
        self.filename = filename

    def get_abs_path(self):
        return self.directory

    def get_full_abs_path(self):
        return os.path.join(self.directory, self.filename)


class RepositorySyncTests(unittest.TestCase):
    def test_native_prepare_repo_is_idempotent(self):
        with TemporaryDirectory() as directory:
            target = os.path.join(directory, "__preview", "icon")
            file_object = _FilePaths(target)

            first = File.prepare_repo(file_object)
            second = File.prepare_repo(file_object)

            self.assertEqual(first, second)
            self.assertTrue(os.path.isdir(target))

    def test_prepare_repo_failure_is_reported_by_worker(self):
        file_object = Mock()
        file_object.prepare_repo.side_effect = OSError("Repository unavailable")
        task = SyncTask(
            task_id="sync-1",
            key="file-1",
            file_object=file_object,
            title="Preview",
            process="publish",
            local_path="",
            web_path="https://example.invalid/preview.jpg",
            expected_size=0,
        )
        signals = WorkerSignals()
        failures = []
        signals.failed.connect(
            lambda task_id, message, traceback_text:
                failures.append((task_id, message, traceback_text))
        )

        DownloadRunnable(task, signals).run()

        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0][0], "sync-1")
        self.assertIn("Repository unavailable", failures[0][1])
        self.assertIn("OSError", failures[0][2])


if __name__ == "__main__":
    unittest.main()
