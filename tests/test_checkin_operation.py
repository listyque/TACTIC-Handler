import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from modern_ui.checkin_operation import CheckinCancelled, _copy_file, stage_checkin
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

    def test_preview_is_generated_once_for_versioned_and_versionless(self):
        class FileObject:
            @staticmethod
            def get_all_new_files_list(name, directory, **_kwargs):
                return [str(Path(directory) / str(name))]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source.write_bytes(b"image")
            inputs = {
                "payload": {
                    "updateVersionless": True,
                    "generatePreviews": True,
                    "sequencePadding": 3,
                    "mode": "copy",
                },
                "filesObjects": [FileObject()],
                "filePaths": [[str(source)]],
                "virtualSnapshot": [["source", {
                    "versioned": {
                        "paths": ["versions", "web/versions", "icon/versions"],
                        "names": ["source_v001.png", "source_v001.jpg", "source_v001.jpg"],
                    },
                    "versionless": {
                        "paths": ["latest", "web/latest", "icon/latest"],
                        "names": ["source.png", "source.jpg", "source.jpg"],
                    },
                }]],
            }

            def generate(_source, web_path, icon_path):
                Path(web_path).write_bytes(b"web")
                Path(icon_path).write_bytes(b"icon")

            with patch(
                "thlib.tactic_classes.generate_web_and_icon",
                side_effect=generate,
            ) as generator:
                self.assertTrue(stage_checkin(
                    inputs,
                    {"value": [str(root / "repository")]},
                ))

            self.assertEqual(generator.call_count, 1)
            self.assertTrue((root / "repository/web/latest/source.jpg").is_file())
            self.assertTrue((root / "repository/icon/latest/source.jpg").is_file())


if __name__ == "__main__":
    unittest.main()
