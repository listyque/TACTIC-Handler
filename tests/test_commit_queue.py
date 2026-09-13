import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication

from thlib.ui.commit_queue import CommitQueueController
from thlib.checkin_operation import stage_checkin
from thlib.ui.workspace_models.windows import FloatingWindowModel


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
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        read_patcher = patch(
            "thlib.ui.commit_queue.env_read_config",
            side_effect=lambda **kwargs: (
                [] if kwargs.get("filename") == "pending" else {}
            ),
        )
        write_patcher = patch("thlib.ui.commit_queue.env_write_config")
        read_patcher.start()
        write_patcher.start()
        self.addCleanup(read_patcher.stop)
        self.addCleanup(write_patcher.stop)
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

    def test_only_current_session_operations_request_tree_reveal(self):
        class Executor:
            def __init__(self):
                self.payloads = []

            def start_prepared_operation(self, operation):
                self.payloads.append(dict(operation))
                return True

        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            restored_id = "restored-operation"
            restored_payload = payload(source.name)
            self.queue._operations[restored_id] = restored_payload
            self.queue.model.append(self.queue._record(
                restored_id, restored_payload, "Restored"
            ))
            self.queue._set_record(
                restored_id, canCommit=True, status="Prepared"
            )
            restored_executor = Executor()
            self.queue._executor = restored_executor
            self.queue._batch_ids = [restored_id]

            self.queue._start_next()

            self.assertFalse(restored_executor.payloads[0][
                "_refreshTreeOnComplete"
            ])

        current_queue = CommitQueueController()
        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            current_id = current_queue.add_prepared(
                payload(source.name), "Current"
            )
            current_queue._set_record(
                current_id, canCommit=True, status="Prepared"
            )
            current_executor = Executor()
            current_queue._executor = current_executor
            current_queue._batch_ids = [current_id]

            current_queue._start_next()

            self.assertTrue(current_executor.payloads[0][
                "_refreshTreeOnComplete"
            ])

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

    def test_context_editor_uses_only_the_branch_after_the_process(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            operation_id = self.queue.add_prepared(
                payload(source.name), "Asset"
            )

            self.assertEqual(self.queue.selectedRecord["context"], "publish")
            self.assertEqual(self.queue.selectedRecord["contextBranch"], "")

            self.queue.update_selected_context_branch("review pass")

            self.assertEqual(
                self.queue.operation(operation_id)["context"],
                "publish/review_pass",
            )
            self.assertEqual(
                self.queue.selectedRecord["contextBranch"],
                "review_pass",
            )

            self.queue.update_selected_context_branch("")

            self.assertEqual(
                self.queue.operation(operation_id)["context"], "publish"
            )
            self.assertEqual(self.queue.selectedRecord["contextBranch"], "")

    def test_naming_edit_drops_the_path_reserved_for_a_dcc_scene(self):
        with tempfile.NamedTemporaryFile(suffix=".ma") as source:
            operation = payload(source.name)
            operation["virtualSnapshot"] = [["scene", {
                "versioned": {
                    "paths": ["assets/versions"],
                    "names": [["asset_v001.ma"]],
                },
                "versionless": {
                    "paths": ["assets"],
                    "names": [["asset.ma"]],
                },
            }]]
            operation_id = self.queue.add_prepared(operation, "Asset")

            self.queue.update_selected_context_branch("review")

            self.assertNotIn(
                "virtualSnapshot", self.queue.operation(operation_id)
            )

    def test_existing_context_branch_is_projected_without_the_process(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            self.queue.add_prepared(
                payload(source.name, "publish/client_review"),
                "Asset",
            )

            self.assertEqual(
                self.queue.selectedRecord["contextBranch"],
                "client_review",
            )

    def test_context_as_filename_keeps_base_context_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            operation_id = self.queue.add_prepared(
                payload(source.name), "Asset"
            )

            self.queue.update_selected("contextAsFilename", True)

            operation = self.queue.operation(operation_id)
            self.assertEqual(operation["context"], "publish")
            self.assertEqual(operation["explicitFilename"], "")

    def test_context_as_filename_links_existing_filename_and_context(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            operation = payload(source.name)
            operation["explicitFilename"] = "client_review"
            operation_id = self.queue.add_prepared(operation, "Asset")

            self.queue.update_selected("contextAsFilename", True)

            self.assertEqual(
                self.queue.operation(operation_id)["context"],
                "publish/client_review",
            )
            self.queue.update_selected("explicitFilename", "director_cut")
            self.assertEqual(
                self.queue.operation(operation_id)["context"],
                "publish/director_cut",
            )

    def test_repositories_expose_titles_without_losing_native_codes(self):
        repositories = [
            ("base", {
                "value": ["D:/repo", "General", "", "base", True],
            }),
            ("local", {
                "value": ["D:/local", "Local", "", "local", True],
            }),
            ("client", {
                "value": ["D:/client", "Client", "", "client", False],
            }),
        ]
        with patch(
            "thlib.environment.env_tactic.get_all_base_dirs",
            return_value=repositories,
        ):
            self.assertEqual(self.queue.repositories, [
                {"title": "General", "code": "base"},
                {"title": "Local", "code": "local"},
            ])

    def test_sole_repository_is_assigned_to_prepared_operation(self):
        repositories = [("base", {
            "value": ["D:/repo", "General", "", "base", True],
        })]
        with tempfile.NamedTemporaryFile(suffix=".txt") as source, patch(
            "thlib.environment.env_tactic.get_all_base_dirs",
            return_value=repositories,
        ):
            operation = payload(source.name)
            operation["repository"] = ""

            operation_id = self.queue.add_prepared(operation, "Asset")

        self.assertEqual(
            self.queue.operation(operation_id)["repository"], "base"
        )
        self.assertEqual(self.queue.selectedRecord["repository"], "base")

    def test_repository_reload_repairs_queued_operation_when_one_is_left(self):
        multiple = [
            ("base", {
                "value": ["D:/repo", "General", "", "base", True],
            }),
            ("local", {
                "value": ["D:/local", "Local", "", "local", True],
            }),
        ]
        only_base = [multiple[0]]
        with tempfile.NamedTemporaryFile(suffix=".txt") as source, patch(
            "thlib.environment.env_tactic.get_all_base_dirs",
            return_value=multiple,
        ):
            operation = payload(source.name)
            operation["repository"] = ""
            operation_id = self.queue.add_prepared(operation, "Asset")
        self.assertEqual(
            self.queue.operation(operation_id)["repository"], ""
        )

        with patch(
            "thlib.environment.env_tactic.get_all_base_dirs",
            return_value=only_base,
        ):
            self.queue.reload_repository_configuration()

        self.assertEqual(
            self.queue.operation(operation_id)["repository"], "base"
        )

    def test_context_branch_batch_edit_keeps_each_operation_process(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.txt"
            second = Path(directory) / "second.txt"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")
            publish_id = self.queue.add_prepared(
                payload(first, "publish"), "Publish"
            )
            model_operation = payload(second, "model")
            model_id = self.queue.add_prepared(model_operation, "Model")
            self.queue.select_row(0)
            self.queue.set_apply_to_checked(True)

            self.queue.update_selected_context_branch("client_review")

            self.assertEqual(
                self.queue.operation(publish_id)["context"],
                "publish/client_review",
            )
            self.assertEqual(
                self.queue.operation(model_id)["context"],
                "model/client_review",
            )

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
        self.assertTrue(self.queue._settings["commitQueue/autoClean"])

    def test_auto_clean_closes_window_only_after_whole_batch_succeeds(self):
        class Executor:
            operationState = "completed"

            def __init__(self):
                self.started = []

            def start_prepared_operation(self, operation):
                self.started.append(dict(operation))
                return True

        windows = FloatingWindowModel({})
        windows.show_window("commit_queue")
        queue = CommitQueueController(window_model=windows)
        executor = Executor()
        queue.set_auto_clean(True)

        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.txt"
            second = Path(directory) / "second.txt"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")
            queue.add_prepared(payload(first), "First")
            queue.add_prepared(payload(second), "Second")
            queue._executor = executor

            queue.commit_all()
            queue._operation_finished(True, "")

            self.assertTrue(windows.is_window_visible("commit_queue"))
            self.assertEqual(queue.count, 1)
            self.assertTrue(queue.busy)

            queue._operation_finished(True, "")

        self.assertEqual(queue.count, 0)
        self.assertFalse(windows.is_window_visible("commit_queue"))
        self.assertEqual(len(executor.started), 2)

    def test_auto_clean_keeps_window_open_after_batch_error(self):
        class Executor:
            operationState = "failed"

            @staticmethod
            def start_prepared_operation(_operation):
                return True

        windows = FloatingWindowModel({})
        windows.show_window("commit_queue")
        queue = CommitQueueController(window_model=windows)
        queue.set_auto_clean(True)

        with tempfile.NamedTemporaryFile(suffix=".txt") as source:
            queue.add_prepared(payload(source.name), "Asset")
            queue._executor = Executor()
            queue.commit_all()
            queue._operation_finished(False, "Upload failed")

        self.assertTrue(windows.is_window_visible("commit_queue"))
        self.assertEqual(queue.count, 1)
        self.assertEqual(queue.model._records[0]["status"], "Failed")

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
                [{"label": "Process", "value": "publish"}],
            )

    def test_image_source_is_used_as_the_snapshot_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "plate.png"
            source.write_bytes(b"image")

            self.queue.add_prepared(payload(source), "Plate")

            record = self.queue.selectedRecord
            self.assertEqual(record["previewExtension"], "PNG")
            self.assertTrue(record["previewUrl"].startswith("file:"))

    def test_maya_queue_renders_the_captured_playblast_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            scene = Path(directory) / "scene.ma"
            playblast = Path(directory) / "playblast.jpg"
            scene.touch()
            playblast.write_bytes(b"real playblast")
            operation = payload(scene)
            operation["files"].append({
                "path": str(playblast), "type": "playblast"
            })
            operation["dccScene"] = {
                "clientId": "maya-1",
            }
            operation["ignoreKeepFileName"] = True

            self.queue.add_prepared(operation, "Asset")

            self.assertTrue(
                self.queue.selectedRecord["previewUrl"].startswith("file:")
            )
            self.queue.remove_selected_file(0)
            self.assertEqual(len(self.queue.operation(
                self.queue.selectedId
            )["files"]), 2)
            self.queue.update_selected("explicitFilename", "hero")
            self.assertFalse(self.queue.operation(
                self.queue.selectedId
            )["ignoreKeepFileName"])


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
