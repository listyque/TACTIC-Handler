import os
import hashlib
import io
import time
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from modern_ui.repository_sync import (
    DownloadRunnable,
    PreparedSyncEntry,
    RepositorySyncController,
    SyncHandle,
    SyncTask,
    WorkerSignals,
)
from thlib.tactic_classes import File
from thlib.tactic_classes import get_snapshots_updates_list


class _FilePaths:
    def __init__(self, directory, filename="preview.jpg"):
        self.directory = str(directory)
        self.filename = filename

    def get_abs_path(self):
        return self.directory

    def get_full_abs_path(self):
        return os.path.join(self.directory, self.filename)


class RepositorySyncTests(unittest.TestCase):
    def test_update_check_reads_aggregate_repository_sync_state(self):
        stype = Mock()
        stype.project.info = {"type": "project", "code": "demo"}
        stype.get_code.return_value = "demo/episode"
        with (
            patch(
                "thlib.tactic_classes.env_inst.get_stype_by_code",
                return_value=stype,
            ),
            patch(
                "thlib.tactic_classes.env_read_config",
                return_value={
                    "EPISODE0001": "2026.08.13 10:00:00",
                    "EPISODE0002": "2026.08.13 11:00:00",
                },
            ),
            patch("thlib.tactic_classes.glob.glob1", return_value=[]),
        ):
            result = get_snapshots_updates_list("demo/episode", "demo")

        self.assertEqual(result, [
            ("EPISODE0001", "2026.08.13 10:00:00"),
            ("EPISODE0002", "2026.08.13 11:00:00"),
        ])

    def test_partial_stype_discovery_streams_bounded_root_pages(self):
        project = Mock()
        project.info = {"type": "project", "code": "demo"}
        project.get_code.return_value = "demo"
        project.stypes = {}
        stype = Mock()
        stype.get_project.return_value = project
        stype.get_code.return_value = "demo/episode"

        roots = []
        for index in range(5):
            root = Mock()
            root.get_code.return_value = f"EPISODE{index:04d}"
            root.get_stype.return_value = stype
            root.get_all_processes.return_value = {}
            roots.append(root)

        def get_sobjects(_search_type, _filters, **kwargs):
            offset = int(kwargs.get("offset") or 0)
            limit = int(kwargs.get("limit") or 2)
            page = roots[offset:offset + limit]
            result = {
                root.get_code(): root for root in page
            }
            if kwargs.get("include_info"):
                return result, {"total_sobjects_query_count": len(roots)}
            return result

        class Progress:
            def __init__(self):
                self.values = []

            def emit(self, value):
                self.values.append(value)

        progress = Progress()
        with patch(
            "thlib.tactic_classes.get_sobjects", side_effect=get_sobjects,
        ) as query:
            result = RepositorySyncController._discover_stype_files_partial(
                stype, "default", False, {}, 2, 7,
                __import__("threading").Event(), progress,
            )

        self.assertEqual(result["processedRoots"], 5)
        self.assertEqual(result["totalRoots"], 5)
        self.assertEqual(result["checkpoint"]["codes"], [
            f"EPISODE{index:04d}" for index in range(5)
        ])
        self.assertEqual(
            [value["processedRoots"] for value in progress.values],
            [2, 4, 5],
        )
        self.assertEqual(query.call_count, 3)
        self.assertEqual(
            [call.kwargs["offset"] for call in query.call_args_list],
            [0, 2, 4],
        )
        self.assertTrue(all(
            call.kwargs["get_all_snapshots"]
            for call in query.call_args_list
        ))

    def test_partial_batch_does_not_finish_between_discovery_chunks(self):
        controller = RepositorySyncController()
        controller._discovery_active = True
        controller._discovery_mode = "partial"
        controller._batch_started_at = time.perf_counter()

        with patch.object(controller, "_commit_completed_checkpoints") as commit:
            self.assertFalse(controller._finish_batch_if_idle())

        commit.assert_not_called()

    def test_repeated_sync_requeues_terminal_original_and_preview_files(self):
        controller = RepositorySyncController()
        entries = [
            PreparedSyncEntry(
                file_object=Mock(), process="publish",
                local_path="C:/repository/asset.ma",
                web_path="https://example.invalid/asset.ma",
                title="asset.ma", expected_size=100, expected_md5="",
            ),
            PreparedSyncEntry(
                file_object=Mock(), process="publish",
                local_path="C:/repository/__preview/web/asset_web.jpg",
                web_path="https://example.invalid/asset_web.jpg",
                title="asset_web.jpg", expected_size=20, expected_md5="",
            ),
        ]
        old_handles = [
            controller._schedule_prepared_entry(entry) for entry in entries
        ]
        controller.model.update_many(
            [handle.task_id for handle in old_handles], status="exists"
        )

        new_handles = [
            controller._schedule_prepared_entry(entry) for entry in entries
        ]

        self.assertEqual(controller.model.rowCount(), 2)
        self.assertTrue(all(
            old.task_id != new.task_id
            for old, new in zip(old_handles, new_handles)
        ))
        self.assertEqual(
            {controller.model.get(row)["title"] for row in range(2)},
            {"asset.ma", "asset_web.jpg"},
        )
        self.assertTrue(all(
            controller.model.get(row)["status"] == "waiting"
            for row in range(2)
        ))

    def test_child_collection_inherits_full_sync_versions(self):
        project = Mock()
        root_stype = Mock()
        child_stype = Mock()
        root_stype.get_project.return_value = project
        project.stypes = {"demo/child": child_stype}

        root = Mock()
        root.get_stype.return_value = root_stype
        root.get_all_processes.return_value = {}
        child = Mock()
        child.get_stype.return_value = child_stype
        child.get_all_processes.return_value = {
            "publish": Mock(get_contexts=Mock(return_value={
                "publish": Mock(
                    get_versionless=Mock(return_value={}),
                    get_versions=Mock(return_value={
                        "SNAP1": Mock(get_files_objects=Mock(return_value=[]))
                    }),
                )
            }))
        }
        root.get_related_sobjects.return_value = ({"CHILD1": child}, {})
        preset = {
            "get_versions": True,
            "demo/child:{s}": {
                "state": True,
                "sub": {"publish:{b}": {"state": True}},
            },
        }

        RepositorySyncController._collect_sobject(root, preset, {})

        context = child.get_all_processes.return_value[
            "publish"
        ].get_contexts.return_value["publish"]
        context.get_versions.assert_called_once_with()

    def test_collection_uses_preset_as_strict_process_allow_list(self):
        stype = Mock()
        stype.get_project.return_value = Mock(stypes={})
        publish_context = Mock(
            get_versionless=Mock(return_value={}),
            get_versions=Mock(return_value={}),
        )
        cache_context = Mock(
            get_versionless=Mock(return_value={}),
            get_versions=Mock(return_value={}),
        )
        sobject = Mock()
        sobject.get_stype.return_value = stype
        sobject.get_all_processes.return_value = {
            "publish": Mock(get_contexts=Mock(return_value={
                "publish": publish_context,
            })),
            "cache": Mock(get_contexts=Mock(return_value={
                "cache": cache_context,
            })),
        }
        preset = {
            "asset:{pp}": {
                "state": False,
                "sub": {
                    "publish:{pr}": {"state": True},
                    # Legacy presets may contain textual check states.
                    "cache:{pr}": {"state": "false"},
                },
            },
        }

        RepositorySyncController._collect_sobject(sobject, preset, {})

        publish_context.get_versionless.assert_called_once_with()
        cache_context.get_versionless.assert_not_called()

    def test_unselected_builtin_process_is_not_collected(self):
        stype = Mock()
        stype.get_project.return_value = Mock(stypes={})
        cache_context = Mock(
            get_versionless=Mock(return_value={}),
            get_versions=Mock(return_value={}),
        )
        sobject = Mock()
        sobject.get_stype.return_value = stype
        sobject.get_all_processes.return_value = {
            "cache": Mock(get_contexts=Mock(return_value={
                "cache": cache_context,
            })),
        }

        RepositorySyncController._collect_sobject(
            sobject, {"cache:{b}": {"state": "off"}}, {}
        )

        cache_context.get_versionless.assert_not_called()

    def test_start_checked_dispatches_only_pool_capacity(self):
        class Pool:
            def __init__(self):
                self.started = []

            @staticmethod
            def maxThreadCount():
                return 4

            def start(self, runnable):
                self.started.append(runnable)

        controller = RepositorySyncController()
        controller.pool = Pool()
        for index in range(9):
            controller._schedule_prepared_entry(PreparedSyncEntry(
                file_object=Mock(),
                process="publish",
                local_path=f"C:/repository/file_{index}.dat",
                web_path=f"https://example.invalid/file_{index}.dat",
                title=f"file_{index}.dat",
                expected_size=100,
                expected_md5="",
            ))

        controller.start_checked()

        self.assertEqual(len(controller.pool.started), 4)
        self.assertEqual(controller._active, 4)
        self.assertEqual(len(controller._pending_start_ids), 5)

    def test_stype_full_discovery_uses_one_snapshot_batch(self):
        project = Mock()
        project.info = {"type": "project", "code": "demo"}
        project.get_code.return_value = "demo"
        project.stypes = {}
        stype = Mock()
        stype.get_project.return_value = project
        stype.get_code.return_value = "demo/asset"
        sobject = Mock()
        sobject.get_code.return_value = "ASSET0001"
        sobject.get_stype.return_value = stype
        sobject.get_all_processes.return_value = {}

        with (
            patch(
                "thlib.tactic_classes.get_sobjects",
                return_value=({"ASSET0001": sobject}, {}),
            ) as get_sobjects,
            patch.object(
                RepositorySyncController, "_load_stype_preset"
            ) as load_preset,
        ):
            files, checkpoint = RepositorySyncController._discover_stype_files(
                stype, "default", False, preset_data={}
            )

        self.assertEqual(files, [])
        self.assertEqual(checkpoint["codes"], ["ASSET0001"])
        get_sobjects.assert_called_once()
        self.assertTrue(get_sobjects.call_args.kwargs["get_all_snapshots"])
        self.assertFalse(get_sobjects.call_args.kwargs["include_info"])
        load_preset.assert_not_called()
        sobject.update_snapshots.assert_not_called()

    def test_many_direct_children_are_loaded_in_one_relation_batch(self):
        project = Mock()
        project.get_code.return_value = "demo"
        parent_stype = Mock()
        parent_stype.get_code.return_value = "demo/episode"
        parent_stype.get_project.return_value = project
        child_stype = Mock()
        child_stype.get_code.return_value = "demo/asset"
        child_stype.get_project.return_value = project
        project.stypes = {"demo/asset": child_stype}
        schema = Mock()
        schema.get_child.return_value = {
            "from": "demo/asset",
            "to": "demo/episode",
            "relationship": "code",
            "from_col": "episode_code",
            "to_col": "code",
        }
        parent_stype.get_schema.return_value = schema

        parents = []
        for index in range(219):
            parent = Mock()
            parent.get_search_key.return_value = (
                f"demo/episode?code=EPISODE{index:04d}"
            )
            parent.get_code.return_value = f"EPISODE{index:04d}"
            parent.get_stype.return_value = parent_stype
            parent.get_all_processes.return_value = {}
            parents.append(parent)
        child = Mock()
        child.get_search_key.return_value = "demo/asset?code=ASSET0001"
        child.get_code.return_value = "ASSET0001"
        child.get_stype.return_value = child_stype
        child.get_all_processes.return_value = {}
        preset = {
            "demo/asset:{s}": {"state": True, "sub": {}},
        }

        with patch(
            "thlib.tactic_classes.get_sobjects",
            return_value=({"ASSET0001": child}, {}),
        ) as get_sobjects:
            RepositorySyncController._collect_sobjects(parents, preset, {})

        get_sobjects.assert_called_once()
        relation_filter = get_sobjects.call_args.args[1][0]
        self.assertEqual(relation_filter[:2], ("episode_code", "in"))
        self.assertEqual(len(relation_filter[2].split("|")), 219)
        for parent in parents:
            parent.get_related_sobjects.assert_not_called()

    def test_many_instance_children_use_two_level_batches(self):
        project = Mock()
        project.get_code.return_value = "demo"
        parent_stype = Mock()
        parent_stype.get_code.return_value = "demo/episode"
        child_stype = Mock()
        child_stype.get_code.return_value = "demo/asset"
        child_stype.get_project.return_value = project
        relation_schema = Mock()
        relation_schema.get_child.return_value = {
            "from": "demo/asset", "to": "demo/episode",
            "relationship": "instance",
            "instance_type": "demo/asset_in_episode",
        }
        parent_stype.get_schema.return_value = relation_schema
        instance_schema = Mock()
        instance_schema.get_child_instance.return_value = {
            "from": "demo/asset_in_episode", "to": "demo/asset",
            "from_col": "asset_code", "to_col": "episode_code",
        }
        parents = []
        for index in range(219):
            parent = Mock()
            parent.get_code.return_value = f"EPISODE{index:04d}"
            parent.get_schema.return_value = instance_schema
            parents.append(parent)
        instance = Mock()
        instance.get_value.return_value = "ASSET0001"
        child = Mock()
        child.get_search_key.return_value = "demo/asset?code=ASSET0001"
        child.get_code.return_value = "ASSET0001"

        with patch(
            "thlib.tactic_classes.get_sobjects",
            side_effect=[
                ({"INSTANCE0001": instance}, {}),
                ({"ASSET0001": child}, {}),
            ],
        ) as get_sobjects:
            related = RepositorySyncController._query_related_sobjects_batch(
                parents, child_stype, parent_stype,
            )

        self.assertEqual(related, [child])
        self.assertEqual(get_sobjects.call_count, 2)
        instance_call, child_call = get_sobjects.call_args_list
        self.assertEqual(instance_call.args[0], "demo/asset_in_episode")
        self.assertFalse(instance_call.kwargs["include_snapshots"])
        self.assertEqual(child_call.args[0], "demo/asset")
        self.assertTrue(child_call.kwargs["get_all_snapshots"])
        for parent in parents:
            parent.get_related_sobjects.assert_not_called()

    def test_updates_discovery_uses_light_scope_then_snapshot_batch(self):
        project = Mock()
        project.info = {"type": "project", "code": "demo"}
        project.get_code.return_value = "demo"
        project.stypes = {}
        stype = Mock()
        stype.get_project.return_value = project
        stype.get_code.return_value = "demo/asset"
        sobject = Mock()
        sobject.get_code.return_value = "ASSET0001"
        sobject.get_stype.return_value = stype
        sobject.get_all_processes.return_value = {}

        with (
            patch(
                "thlib.tactic_classes.get_sobjects",
                side_effect=[
                    ({"ASSET0001": sobject}, {}),
                    ({"ASSET0001": sobject}, {}),
                ],
            ) as get_sobjects,
            patch.object(
                RepositorySyncController, "_read_sync_state",
                return_value={"ASSET0001": "2026.08.13 10:00:00"},
            ),
        ):
            RepositorySyncController._discover_stype_files(
                stype, "default", True, preset_data={}
            )

        self.assertEqual(get_sobjects.call_count, 2)
        first, second = get_sobjects.call_args_list
        self.assertFalse(first.kwargs["include_snapshots"])
        self.assertEqual(
            second.kwargs["snapshot_timestamps"],
            [("ASSET0001", "2026.08.13 10:00:00")],
        )
        sobject.update_snapshots.assert_not_called()

    def test_sync_checkpoint_is_written_only_after_all_downloads_succeed(self):
        controller = RepositorySyncController()
        checkpoint = {
            "groupPath": "ui_search/project/demo/asset/sobjects_conf",
            "codes": ["ASSET0001"],
            "timestamp": "2026.08.13 10:00:00",
            "taskIds": ["one", "two"],
        }
        controller._sync_checkpoints.append(checkpoint)
        controller.model.extend([
            {"taskId": "one", "status": "finished"},
            {"taskId": "two", "status": "failed"},
        ])

        with patch.object(
            controller, "_write_sync_checkpoint"
        ) as write_checkpoint:
            controller._commit_completed_checkpoints()
            write_checkpoint.assert_not_called()
            controller.model.update("two", status="exists")
            controller._commit_completed_checkpoints()
            write_checkpoint.assert_called_once_with(checkpoint)

        self.assertEqual(controller._sync_checkpoints, [])

    def test_aggregate_distinguishes_processed_and_transferred_bytes(self):
        controller = RepositorySyncController()
        controller.model.append({
            "taskId": "active",
            "status": "downloading",
            "active": True,
            "bytesDone": 50,
            "bytesTotal": 100,
            "transferredBytes": 50,
            "speedValue": 25.0,
        })
        controller.model.append({
            "taskId": "local",
            "status": "exists",
            "active": False,
            "bytesDone": 200,
            "bytesTotal": 200,
            "transferredBytes": 0,
            "speedValue": 0.0,
        })

        self.assertAlmostEqual(controller.overall_progress, 250 / 300)
        self.assertEqual(controller.batch_file_count, 2)
        self.assertEqual(controller.processed_file_count, 1)
        self.assertEqual(controller.completed_file_count, 1)
        self.assertEqual(controller.failed_file_count, 0)
        self.assertEqual(controller.transferred_size_text, "50 B")
        self.assertEqual(controller.aggregate_speed_text, "25 B/s")
        self.assertEqual(controller.total_size_text, "300 B")
        self.assertEqual(controller.remaining_size_text, "50 B")

    def test_discovery_scope_is_visible_before_all_rows_are_published(self):
        controller = RepositorySyncController()
        controller._last_batch_summary = {
            "totalFiles": 7, "bytesTotal": 700,
        }
        controller._discovery_active = True
        controller._discovery_scope_files = 2000
        controller._discovery_scope_bytes = 2_000_000
        controller.model.append({
            "taskId": "first-chunk", "status": "waiting",
            "bytesDone": 0, "bytesTotal": 1000,
        })

        self.assertEqual(controller.batch_file_count, 2000)
        self.assertEqual(controller.total_size_text, "1.9 MB")
        self.assertEqual(controller.remaining_size_text, "1.9 MB")

    def test_aggregate_reports_success_errors_and_cancelled_separately(self):
        controller = RepositorySyncController()
        controller.model.extend([
            {"taskId": "ok", "status": "finished"},
            {"taskId": "local", "status": "exists"},
            {"taskId": "failed", "status": "failed"},
            {"taskId": "cancelled", "status": "cancelled"},
        ])

        self.assertEqual(controller.batch_file_count, 4)
        self.assertEqual(controller.processed_file_count, 4)
        self.assertEqual(controller.completed_file_count, 2)
        self.assertEqual(controller.failed_file_count, 1)
        self.assertEqual(controller.cancelled_file_count, 1)

    def test_starting_download_exposes_row_for_queue_following(self):
        controller = RepositorySyncController()
        file_object = Mock()
        handle = SyncHandle(controller, "active", file_object)
        task = SyncTask(
            task_id="active", key="repository/file.ma",
            file_object=file_object,
            local_path="C:/repository/file.ma",
            web_path="https://example.invalid/file.ma",
            title="file.ma", process="publish", expected_size=10,
            expected_md5="", handle=handle,
        )
        controller._tasks[task.task_id] = task
        controller.model.append({
            "taskId": task.task_id, "status": "waiting", "active": False,
        })

        with patch.object(controller.pool, "start"):
            controller._start_task_now(task)

        self.assertEqual(controller.active_row, 0)

    def test_completion_coalesces_aggregate_scan_while_batch_continues(self):
        controller = RepositorySyncController()
        controller._active = 1
        controller._pending_start_ids.append("next")

        with (
            patch.object(controller, "_pump_downloads"),
            patch.object(controller, "_refresh_aggregate") as refresh,
            patch.object(controller, "_request_aggregate_refresh") as request,
        ):
            controller._complete_active()

        refresh.assert_not_called()
        request.assert_called_once_with()

    def test_preset_shortcut_closes_queue_after_successful_run(self):
        controller = RepositorySyncController()
        visibility = []
        controller.visibility_requested.connect(visibility.append)
        controller._auto_close_on_success = True
        controller._auto_close_task_ids = {"complete"}
        controller._batch_task_ids = {"complete"}
        controller._batch_started_at = time.perf_counter() - 1.0
        controller.model.append({
            "taskId": "complete", "status": "finished",
            "bytesDone": 1, "bytesTotal": 1,
            "transferredBytes": 1, "speedValue": 0.0,
        })

        self.assertTrue(controller._finish_batch_if_idle())

        self.assertEqual(visibility, [False])
        self.assertFalse(controller._auto_close_on_success)

    def test_preset_shortcut_keeps_queue_open_after_failure(self):
        controller = RepositorySyncController()
        visibility = []
        controller.visibility_requested.connect(visibility.append)
        controller._auto_close_on_success = True
        controller._auto_close_task_ids = {"failed"}
        controller._batch_task_ids = {"failed"}
        controller._batch_started_at = time.perf_counter() - 1.0
        controller.model.append({
            "taskId": "failed", "status": "failed",
            "bytesDone": 0, "bytesTotal": 1,
            "transferredBytes": 0, "speedValue": 0.0,
        })

        self.assertTrue(controller._finish_batch_if_idle())

        self.assertEqual(visibility, [])
        self.assertFalse(controller._auto_close_on_success)

    def test_clear_finished_keeps_failed_rows_for_diagnostics(self):
        controller = RepositorySyncController()
        controller._batch_started_at = time.perf_counter() - 1
        controller._batch_finished_at = time.perf_counter()
        controller._batch_task_ids.update({"complete", "failed"})
        controller.model.append({
            "taskId": "complete", "status": "finished"
        })
        controller.model.append({
            "taskId": "failed", "status": "failed"
        })

        controller.clear_finished()

        self.assertEqual(controller.model.rowCount(), 1)
        self.assertEqual(controller.model.get(0)["taskId"], "failed")
        self.assertEqual(controller.batch_file_count, 2)
        self.assertEqual(controller.processed_file_count, 2)
        self.assertEqual(controller.failed_file_count, 1)

    def test_completed_batch_summary_survives_auto_clean(self):
        controller = RepositorySyncController()
        now = time.perf_counter()
        controller._batch_started_at = now - 2.0
        controller._batch_finished_at = now
        controller._batch_task_ids.add("complete")
        controller.model.append({
            "taskId": "complete",
            "status": "finished",
            "active": False,
            "bytesDone": 1024,
            "bytesTotal": 1024,
            "transferredBytes": 1024,
            "speedValue": 0.0,
        })

        controller.clear_finished()

        self.assertEqual(controller.model.rowCount(), 0)
        self.assertEqual(controller.batch_file_count, 1)
        self.assertEqual(controller.processed_file_count, 1)
        self.assertEqual(controller.transferred_size_text, "1.0 KB")
        self.assertEqual(controller.aggregate_speed_text, "512 B/s")
        self.assertEqual(controller.elapsed_text, "00:02")

    def test_auto_cleaned_handle_keeps_terminal_state(self):
        controller = RepositorySyncController()
        file_object = Mock()
        handle = SyncHandle(controller, "complete", file_object)
        controller._handles["complete"] = handle
        controller.model.append({
            "taskId": "complete",
            "status": "finished",
            "active": False,
            "bytesDone": 1,
            "bytesTotal": 1,
            "transferredBytes": 1,
            "speedValue": 0.0,
        })

        controller.clear_finished()

        self.assertTrue(handle.is_download_finished())
        self.assertFalse(handle.is_download_in_progress())

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

    def test_tiny_download_skips_redundant_terminal_progress_event(self):
        class Response(io.BytesIO):
            def __init__(self, value):
                super().__init__(value)
                self.headers = {"Content-Length": str(len(value))}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                self.close()

        with TemporaryDirectory() as directory:
            destination = os.path.join(directory, "tiny.bin")
            file_object = Mock()
            file_object.prepare_repo.return_value = destination
            task = SyncTask(
                task_id="sync-tiny", key="file-tiny",
                file_object=file_object, title="Tiny", process="publish",
                local_path=destination,
                web_path="https://example.invalid/tiny.bin",
                expected_size=4,
            )
            signals = WorkerSignals()
            progress = []
            finished = []
            signals.progress.connect(
                lambda *values: progress.append(values)
            )
            signals.finished.connect(
                lambda _task_id, result: finished.append(result)
            )

            with (
                patch(
                    "modern_ui.repository_sync.urllib.request.urlopen",
                    return_value=Response(b"tiny"),
                ),
                patch(
                    "modern_ui.repository_sync.time.perf_counter",
                    side_effect=[10.0, 10.01, 10.02],
                ),
            ):
                DownloadRunnable(task, signals).run()

        self.assertEqual(progress, [])
        self.assertEqual(len(finished), 1)

    def test_md5_mismatch_redownloads_same_size_file(self):
        class Response(io.BytesIO):
            def __init__(self, value):
                super().__init__(value)
                self.headers = {"Content-Length": str(len(value))}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                self.close()

        with TemporaryDirectory() as directory:
            destination = os.path.join(directory, "preview.jpg")
            with open(destination, "wb") as stream:
                stream.write(b"wrong")
            file_object = Mock()
            file_object.prepare_repo.return_value = destination
            expected = b"right"
            task = SyncTask(
                task_id="sync-md5",
                key="file-md5",
                file_object=file_object,
                title="Preview",
                process="publish",
                local_path=destination,
                web_path="https://example.invalid/preview.jpg",
                expected_size=len(expected),
                expected_md5=hashlib.md5(expected).hexdigest(),
                verify_md5=True,
            )
            signals = WorkerSignals()
            finished = []
            signals.finished.connect(lambda _task_id, result: finished.append(result))

            with patch(
                "modern_ui.repository_sync.urllib.request.urlopen",
                return_value=Response(expected),
            ):
                DownloadRunnable(task, signals).run()

            with open(destination, "rb") as stream:
                self.assertEqual(stream.read(), expected)
            self.assertEqual(len(finished), 1)
            self.assertFalse(finished[0]["exists"])


if __name__ == "__main__":
    unittest.main()
