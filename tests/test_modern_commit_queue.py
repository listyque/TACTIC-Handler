from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QUrl

from modern_ui.commit_queue import CommitQueueController
from modern_ui.checkin_operation import stage_checkin


class MemorySettings:
    def __init__(self, *_args):
        self.values = {}

    def value(self, key, default=None, type=None):
        value = self.values.get(key, default)
        return type(value) if type and value is not None else value

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass


def payload(path, context="publish"):
    return {
        "searchKey": "demo/asset?project=demo&code=ASSET001",
        "context": context,
        "process": context.split("/", 1)[0],
        "repository": "repo",
        "mode": "upload",
        "files": [{"path": str(path), "type": "file"}],
        "filesDict": [("source", {
            "t": ["file"], "s": [""], "e": ["txt"],
            "p": [""], "m": None,
        })],
        "updateVersionless": True,
    }


class CommitQueueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.settings = MemorySettings()
        patcher = patch(
            "modern_ui.commit_queue.QSettings",
            return_value=self.settings,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.queue = CommitQueueController()

    def test_duplicate_requires_an_explicit_decision(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            first_id = self.queue.add_prepared(payload(source.name), "Asset")
            duplicate_id = self.queue.add_prepared(payload(source.name), "Asset")
            self.assertEqual(first_id, duplicate_id)
            self.assertTrue(self.queue.duplicatePending)
            self.assertEqual(self.queue.count, 1)
            self.queue.resolve_duplicate("add")
            self.assertEqual(self.queue.count, 2)

    def test_same_file_in_another_context_is_not_a_duplicate(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            self.queue.add_prepared(payload(source.name), "Asset")
            self.queue.add_prepared(
                payload(source.name, "model/main"), "Asset"
            )
            self.assertEqual(self.queue.count, 2)
            self.assertFalse(self.queue.duplicatePending)

    def test_multiple_duplicates_are_resolved_in_order(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            self.queue.add_prepared(payload(source.name), "Asset")
            self.queue.add_prepared(payload(source.name), "Asset")
            self.queue.add_prepared(payload(source.name), "Asset")
            self.assertTrue(self.queue.duplicatePending)
            self.queue.resolve_duplicate("ignore")
            self.assertTrue(self.queue.duplicatePending)
            self.queue.resolve_duplicate("ignore")
            self.assertFalse(self.queue.duplicatePending)

    def test_checked_operations_can_be_edited_together(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.txt"
            second = Path(directory) / "second.txt"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")
            first_id = self.queue.add_prepared(payload(first), "First")
            second_id = self.queue.add_prepared(payload(second), "Second")
            self.queue.select_row(0)
            self.queue.set_apply_to_checked(True)
            self.queue.update_selected("description", "Shared")
            self.assertEqual(self.queue.operation(first_id)["description"], "Shared")
            self.assertEqual(self.queue.operation(second_id)["description"], "Shared")

    def test_auto_clean_removes_a_completed_operation(self):
        class Executor:
            operationState = "completed"

        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            operation_id = self.queue.add_prepared(payload(source.name), "Asset")
            self.queue._executor = Executor()
            self.queue._active_id = operation_id
            self.queue.set_auto_clean(True)
            self.queue._operation_finished(True, "")

        self.assertEqual(self.queue.count, 0)
        self.assertTrue(self.settings.values["commitQueue/autoClean"])

    def test_removing_a_file_keeps_group_payload_in_sync(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.txt"
            second = Path(directory) / "second.txt"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")
            operation = payload(first)
            operation["files"].append({
                "path": str(second), "type": "file"
            })
            operation["filesDict"].append(("second", {
                "t": ["file"], "s": [""], "e": ["txt"],
                "p": [""], "m": None,
            }))
            operation_id = self.queue.add_prepared(operation, "Asset")

            self.queue.remove_selected_file(0)

            remaining = self.queue.operation(operation_id)
            self.assertEqual(
                [record["path"] for record in remaining["files"]],
                [str(second)],
            )
            self.assertEqual(len(remaining["filesDict"]), 1)

    def test_unfinished_count_excludes_completed_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.txt"
            second = Path(directory) / "second.txt"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")
            first_id = self.queue.add_prepared(payload(first), "First")
            self.queue.add_prepared(payload(second), "Second")
            self.queue._set_record(first_id, status="Completed")

            self.assertEqual(self.queue.count, 2)
            self.assertEqual(self.queue.unfinishedCount, 1)

    def test_restored_validation_waits_for_online_server(self):
        class LocalSignal:
            def __init__(self):
                self.callbacks = []

            def connect(self, callback):
                self.callbacks.append(callback)

            def emit(self):
                for callback in list(self.callbacks):
                    callback()

        class Application:
            def __init__(self):
                self.server_state = "connecting"
                self.server_state_changed = LocalSignal()

        class Executor:
            def __init__(self, application):
                self._application = application
                self.preparationChanged = LocalSignal()
                self.operationFinished = LocalSignal()
                self.preparedValidationFinished = LocalSignal()
                self.validations = []

            def validate_prepared_operation(self, request_id, operation):
                self.validations.append((request_id, operation))

        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            operation_id = self.queue.add_prepared(
                payload(source.name), "Asset"
            )
            application = Application()
            executor = Executor(application)

            self.queue.attach_executor(executor)
            self.assertEqual(executor.validations, [])

            application.server_state = "online"
            application.server_state_changed.emit()

            self.assertEqual(len(executor.validations), 1)
            self.assertTrue(
                executor.validations[0][0].startswith(operation_id + ":")
            )

    def test_operation_previews_are_stored_with_the_selected_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "scene.ma"
            preview = Path(directory) / "preview.png"
            source.write_text("scene", encoding="utf-8")
            preview.write_bytes(b"preview")
            operation_id = self.queue.add_prepared(payload(source), "Asset")

            self.queue.add_selected_previews([
                QUrl.fromLocalFile(str(preview))
            ])

            operation = self.queue.operation(operation_id)
            self.assertEqual(operation["previewFiles"], [str(preview)])
            self.assertEqual(self.queue.selectedRecord["previewCount"], 1)
            self.assertTrue(
                self.queue.selectedRecord["previewUrl"].startswith("file:")
            )
            self.queue.clear_selected_previews()
            self.assertEqual(
                self.queue.operation(operation_id)["previewFiles"], []
            )

    def test_snapshot_preview_uses_ready_name_and_file_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source_scene.ma"
            source.write_text("scene", encoding="utf-8")
            operation = payload(source)
            operation["version"] = 4
            operation["files"][0]["versioned"] = (
                "assets/versions/asset_model_v004.ma"
            )

            self.queue.add_prepared(operation, "Asset model")

            record = self.queue.selectedRecord
            self.assertEqual(record["futureFileName"], "asset_model_v004.ma")
            self.assertEqual(record["previewExtension"], "MA")
            self.assertEqual(record["versionLabel"], "v004")
            self.assertEqual(record["fileSummary"], "1 file")
            self.assertEqual(
                record["snapshotInfoChips"],
                [{"label": "Context", "value": "publish"}],
            )

    def test_image_source_is_used_as_the_snapshot_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "plate.png"
            source.write_bytes(b"image")

            self.queue.add_prepared(payload(source), "Plate")

            record = self.queue.selectedRecord
            self.assertEqual(record["previewExtension"], "PNG")
            self.assertTrue(record["previewUrl"].startswith("file:"))


class FakeFileObject:
    def get_all_new_files_list(
        self, name, directory, new_frame_padding=None
    ):
        return [str(Path(directory) / "".join(name))]


class CheckinStagingTest(unittest.TestCase):
    def test_move_stages_both_versions_before_removing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "scene.ma"
            source.write_text("scene", encoding="utf-8")
            repository_root = root / "repository"
            inputs = {
                "payload": {
                    "mode": "move",
                    "updateVersionless": True,
                    "onlyVersionless": False,
                    "generatePreviews": False,
                    "sequencePadding": 3,
                },
                "filePaths": [[str(source)]],
                "filesObjects": [FakeFileObject()],
                "virtualSnapshot": [("scene", {
                    "versioned": {
                        "paths": ["asset/versions"],
                        "names": [["scene_v001.ma"]],
                    },
                    "versionless": {
                        "paths": ["asset"],
                        "names": [["scene.ma"]],
                    },
                })],
            }
            repository = {
                "value": [str(repository_root), "Repository", "", "repo", True]
            }
            self.assertTrue(stage_checkin(inputs, repository))
            self.assertFalse(source.exists())
            self.assertTrue(
                (repository_root / "asset/versions/scene_v001.ma").is_file()
            )
            self.assertTrue((repository_root / "asset/scene.ma").is_file())


if __name__ == "__main__":
    unittest.main()
