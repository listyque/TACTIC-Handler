import tempfile
import threading
import unittest
from pathlib import Path

from modern_ui.checkin_operation import CheckinCancelled, _copy_file
from modern_ui.checkin_out import _naming_path, _naming_snapshots


class CheckinOperationTest(unittest.TestCase):

    def test_virtual_naming_result_keeps_one_snapshot_per_input_file(self):
        result = [
            ["scene", {
                "versioned": {
                    "paths": ["assets/versions"],
                    "names": [["scene", "_v001", ".ma"]],
                },
                "versionless": {
                    "paths": ["assets"],
                    "names": [["scene", "", ".ma"]],
                },
            }],
            ["preview", {
                "versioned": {
                    "paths": ["assets/versions"],
                    "names": [["preview", "_v001", ".jpg"]],
                },
            }],
        ]

        snapshots = _naming_snapshots(result)

        self.assertEqual(len(snapshots), 2)
        self.assertEqual(
            _naming_path(snapshots[0], "versioned"),
            "assets/versions/scene_v001.ma",
        )
        self.assertEqual(
            _naming_path(snapshots[0], "versionless"),
            "assets/scene.ma",
        )
        self.assertEqual(
            _naming_path(snapshots[1], "versioned"),
            "assets/versions/preview_v001.jpg",
        )

    def test_cancelled_copy_does_not_leave_completed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.bin"
            destination = Path(directory) / "destination.part"
            source.write_bytes(b"content")
            cancel = threading.Event()
            cancel.set()

            with self.assertRaises(CheckinCancelled):
                _copy_file(source, destination, cancel)
            self.assertNotEqual(source.read_bytes(), destination.read_bytes())


if __name__ == "__main__":
    unittest.main()
