import os
import hashlib
import io
import time
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QSignalSpy, QTest

from thlib.ui.repository_sync import (
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
    def __init__(
        self, directory, filename="preview.jpg", expected_size=0,
        server_timestamp=None,
    ):
        self.directory = str(directory)
        self.filename = filename
        self.expected_size = expected_size
        self.server_timestamp = server_timestamp

    def get_abs_path(self):
        return self.directory

    def get_full_abs_path(self):
        return os.path.join(self.directory, self.filename)

    def get_file_size(self):
        return self.expected_size

    def get_timestamp(self, obj=False):
        return self.server_timestamp if obj else ""


class RepositorySyncTests(unittest.TestCase):
    def test_discovery_time_is_included_in_batch_elapsed_time(self):
        controller = RepositorySyncController()

        with patch("thlib.ui.repository_sync.time.perf_counter", return_value=10):
            controller._begin_discovery("default", False, "full")
        with patch("thlib.ui.repository_sync.time.perf_counter", return_value=16):
            summary = controller._compute_aggregate_summary()

        self.assertTrue(controller._batch_running)
        self.assertEqual(controller._batch_started_at, 10)
        self.assertEqual(summary["elapsed"], 6)
        controller._elapsed_timer.stop()

    def test_presets_are_ui_safe_cached_copies(self):
        project = Mock()
        project.get_code.return_value = "demo"
        stype = Mock()
        stype.get_code.return_value = "demo/asset"
        stype.get_project.return_value = project
        source = Mock()
        source.get_stype.return_value = stype
        controller = RepositorySyncController()

        with patch("thlib.tactic_classes.server_start") as server_start:
            initial = controller.presets(source)

        server_start.assert_not_called()
        self.assertEqual(initial[0]["preset_name"], "default")
        controller.cache_presets(source, [{
            "preset_name": "review", "pretty_preset_name": "Review",
        }])
        cached = controller.presets(source)
        cached[0]["preset_name"] = "mutated"
        self.assertEqual(
            controller.presets(source)[0]["preset_name"], "review"
        )

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
        ):
            result = get_snapshots_updates_list("demo/episode", "demo")

        self.assertEqual(result, [
            ("EPISODE0001", "2026.08.13 10:00:00"),
            ("EPISODE0002", "2026.08.13 11:00:00"),
        ])

    def test_update_check_skips_non_project_config_search_types(self):
        with (
            patch(
                "thlib.tactic_classes.env_inst.get_stype_by_code",
                return_value=None,
            ),
            patch("thlib.tactic_classes.env_read_config") as read_config,
        ):
            result = get_snapshots_updates_list(
                "config/widget_config", "demo"
            )

        self.assertEqual(result, [])
        read_config.assert_not_called()

    def test_sync_state_reads_only_aggregate_requested_codes(self):
        with patch(
            "thlib.environment.env_read_config",
            return_value={
                "ASSET001": "2026.08.13 10:00:00",
                "ASSET002": "2026.08.13 11:00:00",
            },
        ) as read_config:
            result = RepositorySyncController._read_sync_state(
                "ui_search/demo/assets", ["ASSET002"]
            )

        self.assertEqual(result, {"ASSET002": "2026.08.13 11:00:00"})
        read_config.assert_called_once_with(
            filename="repository_sync_state",
            unique_id="ui_search/demo/assets",
            long_abs_path=True,
        )

    def test_partial_stype_discovery_streams_bounded_root_pages(self):
        project = Mock()
        project.info = {"type": "project", "code": "demo"}
        project.get_code.return_value = "demo"
        project.stypes = {}
        stype = Mock()
        stype.get_project.return_value = project
        stype.get_code.return_value = "demo/episode"

        roots = []
        for index in range(9):
            root = Mock()
            root.get_code.return_value = f"EPISODE{index:04d}"
            root.get_stype.return_value = stype
            root.get_all_processes.return_value = {}
            roots.append(root)

        first_wave = __import__("threading").Barrier(4, timeout=2)

        def get_sobjects(_search_type, filters, **kwargs):
            if not kwargs.get("get_all_snapshots"):
                return {root.get_code(): root for root in roots}
            page_filter = filters[0]
            codes = (
                [page_filter[1]] if len(page_filter) == 2
                else page_filter[2].split("|")
            )
            if codes[0] != "EPISODE0008":
                first_wave.wait()
            return {
                root.get_code(): root
                for root in roots if root.get_code() in codes
            }

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
                stype, "default", False, {}, 2, 4, 7,
                __import__("threading").Event(), progress,
            )

        self.assertEqual(result["processedRoots"], 9)
        self.assertEqual(result["totalRoots"], 9)
        self.assertEqual(result["checkpoint"]["codes"], [
            f"EPISODE{index:04d}" for index in range(9)
        ])
        self.assertEqual(
            [
                value["processedRoots"] for value in progress.values
                if value["stage"] == "streaming"
            ],
            [2, 4, 6, 8, 9],
        )
        self.assertEqual(query.call_count, 6)
        page_calls = [
            call for call in query.call_args_list
            if call.kwargs.get("get_all_snapshots")
        ]
        self.assertEqual(
            sorted(
                tuple(
                    [call.args[1][0][1]]
                    if len(call.args[1][0]) == 2
                    else call.args[1][0][2].split("|")
                )
                for call in page_calls
            ),
            [
                ("EPISODE0000", "EPISODE0001"),
                ("EPISODE0002", "EPISODE0003"),
                ("EPISODE0004", "EPISODE0005"),
                ("EPISODE0006", "EPISODE0007"),
                ("EPISODE0008",),
            ],
        )
        self.assertTrue(all(
            call.kwargs["get_all_snapshots"]
            for call in page_calls
        ))

    def test_partial_batch_does_not_finish_between_discovery_chunks(self):
        controller = RepositorySyncController()
        controller._discovery_active = True
        controller._discovery_mode = "partial"
        controller._batch_started_at = time.perf_counter()

        with patch.object(controller, "_commit_completed_checkpoints") as commit:
            self.assertFalse(controller._finish_batch_if_idle())

        commit.assert_not_called()

    def test_partial_discovery_rejects_an_incomplete_server_page(self):
        project = Mock()
        project.info = {"type": "project", "code": "demo"}
        project.get_code.return_value = "demo"
        project.stypes = {}
        stype = Mock()
        stype.get_project.return_value = project
        stype.get_code.return_value = "demo/episode"
        roots = {}
        for code in ("EPISODE0001", "EPISODE0002"):
            root = Mock()
            root.get_code.return_value = code
            root.get_stype.return_value = stype
            root.get_all_processes.return_value = {}
            roots[code] = root

        with patch(
            "thlib.tactic_classes.get_sobjects",
            side_effect=[roots, {"EPISODE0001": roots["EPISODE0001"]}],
        ):
            with self.assertRaisesRegex(
                RuntimeError, "omitted 1 Repository Sync objects",
            ):
                RepositorySyncController._discover_stype_files_partial(
                    stype, "default", False, {}, 2, 1, 7,
                    __import__("threading").Event(),
                )

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

    def test_file_schedule_uses_native_server_timestamp(self):
        file_object = Mock()
        file_object.get_full_abs_path.return_value = (
            "C:/repository/__preview/icon/asset.jpg"
        )
        file_object.get_full_web_path.return_value = (
            "https://example.invalid/asset.jpg"
        )
        file_object.get_filename_with_ext.return_value = "asset.jpg"
        file_object.get_file_size.return_value = 10
        file_object.get_md5.return_value = ""
        file_object.get_unique_id.return_value = "FILE0001"
        server_timestamp = __import__("datetime").datetime(
            2026, 8, 20, 12, 30, 0
        )
        file_object.get_timestamp.return_value = server_timestamp
        controller = RepositorySyncController()

        with patch.object(
            controller, "verify_repository_md5_enabled", return_value=True
        ):
            handle = controller.schedule_file_object(
                file_object, process="preview", auto_start=False,
                is_ui_preview=True,
            )
            batch_entry = controller._prepare_file_object(
                file_object, "preview"
            )

        expected = server_timestamp.timestamp()
        self.assertEqual(
            controller._tasks[handle.task_id].expected_mtime, expected
        )
        self.assertEqual(batch_entry.expected_mtime, expected)
        self.assertTrue(controller._tasks[handle.task_id].is_ui_preview)
        self.assertFalse(controller._tasks[handle.task_id].verify_md5)
        self.assertFalse(batch_entry.is_ui_preview)
        self.assertEqual(controller.model.rowCount(), 0)
        self.assertEqual(controller.queue_count, 0)
        self.assertEqual(controller.queue_dict, {})

        with patch.object(
            controller, "verify_repository_md5_enabled", return_value=True
        ):
            full_sync_handle = controller._schedule_prepared_entry(
                batch_entry, auto_start=False
            )

        self.assertNotEqual(full_sync_handle.task_id, handle.task_id)
        self.assertTrue(controller._tasks[handle.task_id].is_ui_preview)
        self.assertFalse(controller._tasks[handle.task_id].verify_md5)
        self.assertFalse(
            controller._tasks[full_sync_handle.task_id].is_ui_preview
        )
        self.assertTrue(
            controller._tasks[full_sync_handle.task_id].verify_md5
        )
        self.assertEqual(controller.model.rowCount(), 1)
        self.assertEqual(controller.queue_count, 1)
        self.assertEqual(
            controller.queue_dict["FILE0001"].task_id,
            full_sync_handle.task_id,
        )
        file_object.get_timestamp.assert_called_with(obj=True)

    def test_fresh_ui_preview_finishes_without_queue_logs_or_batch_notice(self):
        application = QGuiApplication.instance() or QGuiApplication([])
        self.assertIsNotNone(application)
        with TemporaryDirectory() as directory:
            destination = os.path.join(directory, "preview.jpg")
            with open(destination, "wb") as stream:
                stream.write(b"local-preview")
            local_mtime = os.path.getmtime(destination)
            debug_log = Mock()
            file_object = Mock()
            file_object.get_full_abs_path.return_value = destination
            file_object.get_full_web_path.return_value = (
                "https://example.invalid/preview.jpg"
            )
            file_object.get_filename_with_ext.return_value = "preview.jpg"
            file_object.get_file_size.return_value = len(b"local-preview")
            file_object.get_md5.return_value = ""
            file_object.get_timestamp.return_value = (
                __import__("datetime").datetime.fromtimestamp(local_mtime)
            )
            file_object.get_unique_id.return_value = "FILE_PREVIEW"
            file_object.is_exists.return_value = True
            controller = RepositorySyncController(debug_log=debug_log)
            finished = QSignalSpy(controller.task_finished)
            downloaded = []
            batch_notices = []
            controller.file_download_done.connect(downloaded.append)
            controller.downloads_finished.connect(
                lambda: batch_notices.append(True)
            )

            with patch(
                "thlib.ui.repository_sync.urllib.request.urlopen"
            ) as urlopen:
                handle = controller.schedule_file_object(
                    file_object, process="preview", auto_start=True,
                    is_ui_preview=True,
                )
                deadline = time.monotonic() + 2.0
                while finished.count() == 0 and time.monotonic() < deadline:
                    QTest.qWait(10)
                self.assertEqual(finished.count(), 1)

            self.assertEqual(controller.model.rowCount(), 0)
            self.assertEqual(controller.queue_count, 0)
            self.assertEqual(controller.queue_dict, {})
            self.assertEqual(batch_notices, [])
            self.assertEqual(downloaded, [file_object])
            self.assertTrue(handle.is_download_finished())
            self.assertNotIn(handle.task_id, controller._tasks)
            file_object.prepare_repo.assert_not_called()
            urlopen.assert_not_called()
            debug_log.log.assert_not_called()
            controller.shutdown()

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

    def test_stype_full_discovery_balances_four_parallel_pages(self):
        project = Mock()
        project.info = {"type": "project", "code": "demo"}
        project.get_code.return_value = "demo"
        project.stypes = {}
        stype = Mock()
        stype.get_project.return_value = project
        stype.get_code.return_value = "demo/asset"
        sobjects = {}
        for index in range(8):
            sobject = Mock()
            code = f"ASSET{index:04d}"
            sobject.get_code.return_value = code
            sobject.get_stype.return_value = stype
            sobject.get_all_processes.return_value = {}
            sobjects[code] = sobject
        progress = []

        class Progress:
            @staticmethod
            def emit(payload):
                progress.append(dict(payload))

        first_wave = __import__("threading").Barrier(4, timeout=2)

        def get_sobjects(_search_type, filters, **kwargs):
            if not kwargs.get("get_all_snapshots"):
                return sobjects
            first_wave.wait()
            page_filter = filters[0]
            codes = (
                [page_filter[1]] if len(page_filter) == 2
                else page_filter[2].split("|")
            )
            return {code: sobjects[code] for code in codes}

        with (
            patch(
                "thlib.tactic_classes.get_sobjects",
                side_effect=get_sobjects,
            ) as get_sobjects,
            patch.object(
                RepositorySyncController, "_load_stype_preset"
            ) as load_preset,
        ):
            files, checkpoint = RepositorySyncController._discover_stype_files(
                stype, "default", False, preset_data={}, max_workers=4,
                generation=7,
                progress_signal=Progress(),
            )

        self.assertEqual(files, [])
        self.assertEqual(checkpoint["codes"], list(sobjects))
        self.assertEqual(get_sobjects.call_count, 5)
        page_calls = [
            call for call in get_sobjects.call_args_list
            if call.kwargs.get("get_all_snapshots")
        ]
        self.assertEqual(
            sorted(tuple(call.args[1][0][2].split("|")) for call in page_calls),
            [
                ("ASSET0000", "ASSET0001"),
                ("ASSET0002", "ASSET0003"),
                ("ASSET0004", "ASSET0005"),
                ("ASSET0006", "ASSET0007"),
            ],
        )
        self.assertEqual(progress[0]["stage"], "objects")
        self.assertEqual(progress[1]["stage"], "scope")
        self.assertEqual(progress[-1]["processedRoots"], 8)
        self.assertEqual(progress[-1]["totalRoots"], 8)
        self.assertTrue(all(item["generation"] == 7 for item in progress))
        load_preset.assert_not_called()
        for sobject in sobjects.values():
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
        from thlib.tactic_classes import Schema

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
        instance_schema = Schema([
            {"search_type": {"name": "demo/asset_in_episode"}},
            {
                "children": [],
                "parents": [
                    {
                        "from": "demo/asset_in_episode",
                        "to": "demo/asset",
                        "relationship": "code",
                        "from_col": "asset_code",
                        "to_col": "code",
                    },
                    {
                        "from": "demo/asset_in_episode",
                        "to": "demo/episode",
                        "relationship": "code",
                        "from_col": "episode_code",
                        "to_col": "code",
                    },
                ],
            },
        ])
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
        self.assertEqual(instance_call.args[1][0][0], "episode_code")
        self.assertFalse(instance_call.kwargs["include_snapshots"])
        self.assertEqual(child_call.args[0], "demo/asset")
        self.assertTrue(child_call.kwargs["get_all_snapshots"])
        for parent in parents:
            parent.get_related_sobjects.assert_not_called()

    def test_self_instance_children_use_path_columns_in_two_batches(self):
        from thlib.tactic_classes import Schema

        project = Mock()
        project.get_code.return_value = "demo"
        asset_stype = Mock()
        asset_stype.get_code.return_value = "demo/asset"
        asset_stype.get_project.return_value = project
        relation_schema = Mock()
        relation_schema.get_child.return_value = {
            "from": "demo/asset", "to": "demo/asset",
            "relationship": "instance",
            "instance_type": "demo/asset_in_asset",
        }
        asset_stype.get_schema.return_value = relation_schema
        instance_schema = Schema([
            {"search_type": {"name": "demo/asset_in_asset"}},
            {
                "children": [{
                    "from": "demo/asset_in_asset", "to": "demo/asset",
                    "relationship": "code",
                    "from_col": "parent_asset_code", "to_col": "code",
                    "path": "child",
                }],
                "parents": [{
                    "from": "demo/asset_in_asset", "to": "demo/asset",
                    "relationship": "code",
                    "from_col": "child_asset_code", "to_col": "code",
                    "path": "parent",
                }],
            },
        ])
        parents = []
        for code in ("ASSET0001", "ASSET0002"):
            parent = Mock()
            parent.get_code.return_value = code
            parent.get_schema.return_value = instance_schema
            parents.append(parent)
        instance = Mock()
        instance.get_value.side_effect = {
            "child_asset_code": "ASSET0003",
        }.get
        child = Mock()
        child.get_search_key.return_value = "demo/asset?code=ASSET0003"
        child.get_code.return_value = "ASSET0003"

        with patch(
            "thlib.tactic_classes.get_sobjects",
            side_effect=[
                ({"INSTANCE0001": instance}, {}),
                ({"ASSET0003": child}, {}),
            ],
        ) as get_sobjects:
            related = RepositorySyncController._query_related_sobjects_batch(
                parents, asset_stype, asset_stype,
            )

        self.assertEqual(related, [child])
        instance_call, child_call = get_sobjects.call_args_list
        self.assertEqual(
            instance_call.args[1][0][:2],
            ("parent_asset_code", "in"),
        )
        self.assertEqual(child_call.args[1][0], ("code", "ASSET0003"))
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
                    {"ASSET0001": sobject},
                    {"ASSET0001": sobject},
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
        scope, snapshots = get_sobjects.call_args_list
        self.assertFalse(scope.kwargs["include_snapshots"])
        self.assertEqual(
            snapshots.kwargs["snapshot_timestamps"],
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
        controller._visible_active = 1
        controller._batch_running = True
        controller._pending_start_ids.append("next")
        task = SyncTask(
            task_id="complete", key="complete", file_object=Mock(),
            title="complete", process="publish", local_path="complete",
            web_path="https://example.invalid/complete",
            expected_size=0,
        )
        controller._tasks["next"] = SyncTask(
            task_id="next", key="next", file_object=Mock(),
            title="next", process="publish", local_path="next",
            web_path="https://example.invalid/next", expected_size=0,
        )

        with (
            patch.object(controller, "_pump_downloads"),
            patch.object(controller, "_refresh_aggregate") as refresh,
            patch.object(controller, "_request_aggregate_refresh") as request,
        ):
            controller._complete_active(task)

        refresh.assert_not_called()
        request.assert_called_once_with()

    def test_preset_shortcut_closes_queue_after_successful_run(self):
        controller = RepositorySyncController()
        visibility = []
        controller.visibility_requested.connect(visibility.append)
        controller._auto_close_on_success = True
        controller._auto_close_task_ids = {"complete"}
        controller._batch_task_ids = {"complete"}
        controller._batch_running = True
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
        controller._batch_running = True
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

    def test_finished_worker_does_not_require_a_published_model_row(self):
        debug_log = Mock()
        controller = RepositorySyncController(debug_log=debug_log)
        file_object = Mock()
        task = SyncTask(
            task_id="unpublished", key="repository/file.jpg",
            file_object=file_object, title="file.jpg", process="publish",
            local_path="D:/repository/file.jpg",
            web_path="https://example.invalid/file.jpg", expected_size=4,
        )
        handle = SyncHandle(controller, task.task_id, file_object)
        task.handle = handle
        controller._tasks[task.task_id] = task
        controller._handles[task.task_id] = handle
        controller._key_to_task[task.key] = task.task_id

        controller._finished(task.task_id, {
            "bytes": 4, "elapsed": 0.25,
            "path": task.local_path, "exists": True,
        })

        self.assertEqual(task.state, "exists")
        self.assertTrue(handle.is_download_finished())
        self.assertEqual(controller.model.rowCount(), 0)
        self.assertIn(
            "file.jpg: Already in repository",
            debug_log.log.call_args.args,
        )

    def test_native_prepare_repo_is_idempotent(self):
        with TemporaryDirectory() as directory:
            target = os.path.join(directory, "__preview", "icon")
            file_object = _FilePaths(target)

            first = File.prepare_repo(file_object)
            second = File.prepare_repo(file_object)

            self.assertEqual(first, second)
            self.assertTrue(os.path.isdir(target))

    def test_native_file_freshness_uses_size_and_server_timestamp(self):
        with TemporaryDirectory() as directory:
            path = os.path.join(directory, "preview.jpg")
            with open(path, "wb") as stream:
                stream.write(b"same")
            local_mtime = os.path.getmtime(path)
            fresh = _FilePaths(
                directory, expected_size=4,
                server_timestamp=__import__("datetime").datetime.fromtimestamp(
                    local_mtime
                ),
            )
            stale_size = _FilePaths(
                directory, expected_size=5,
                server_timestamp=fresh.server_timestamp,
            )
            stale_time = _FilePaths(
                directory, expected_size=4,
                server_timestamp=__import__("datetime").datetime.fromtimestamp(
                    local_mtime + 60
                ),
            )
            locally_changed = _FilePaths(
                directory, expected_size=4,
                server_timestamp=__import__("datetime").datetime.fromtimestamp(
                    local_mtime - 60
                ),
            )

            self.assertTrue(File.is_local_current(fresh))
            self.assertFalse(File.is_local_current(stale_size))
            self.assertFalse(File.is_local_current(stale_time))
            self.assertFalse(File.is_local_current(locally_changed))

    def test_prepare_repo_failure_is_reported_by_worker(self):
        file_object = Mock()
        file_object.is_exists.return_value = False
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

    def test_fresh_existing_preview_skips_http_and_prepare(self):
        with TemporaryDirectory() as directory:
            destination = os.path.join(directory, "preview.jpg")
            with open(destination, "wb") as stream:
                stream.write(b"local-preview")
            local_mtime = os.path.getmtime(destination)
            file_object = Mock()
            file_object.is_exists.return_value = True
            task = SyncTask(
                task_id="preview-local", key="preview-local",
                file_object=file_object, title="Preview", process="preview",
                local_path=destination,
                web_path="https://example.invalid/preview.jpg",
                expected_size=len(b"local-preview"),
                expected_mtime=local_mtime,
            )
            signals = WorkerSignals()
            finished = []
            signals.finished.connect(
                lambda _task_id, result: finished.append(result)
            )

            with patch(
                "thlib.ui.repository_sync.urllib.request.urlopen"
            ) as urlopen:
                DownloadRunnable(task, signals).run()

        file_object.is_exists.assert_called_once_with()
        file_object.prepare_repo.assert_not_called()
        urlopen.assert_not_called()
        self.assertEqual(len(finished), 1)
        self.assertTrue(finished[0]["exists"])
        self.assertEqual(finished[0]["path"], destination)

    def test_same_size_preview_with_newer_server_timestamp_is_downloaded(self):
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
                stream.write(b"old!")
            local_mtime = os.path.getmtime(destination)
            server_mtime = local_mtime + 60
            file_object = Mock()
            file_object.is_exists.return_value = True
            file_object.prepare_repo.return_value = destination
            task = SyncTask(
                task_id="preview-stale", key="preview-stale",
                file_object=file_object, title="Preview", process="preview",
                local_path=destination,
                web_path="https://example.invalid/preview.jpg",
                expected_size=4,
                expected_mtime=server_mtime,
            )
            signals = WorkerSignals()
            finished = []
            signals.finished.connect(
                lambda _task_id, result: finished.append(result)
            )

            with patch(
                "thlib.ui.repository_sync.urllib.request.urlopen",
                return_value=Response(b"new!"),
            ) as urlopen:
                DownloadRunnable(task, signals).run()

            with open(destination, "rb") as stream:
                self.assertEqual(stream.read(), b"new!")
            downloaded_mtime = os.path.getmtime(destination)

        urlopen.assert_called_once()
        self.assertEqual(len(finished), 1)
        self.assertFalse(finished[0]["exists"])
        self.assertAlmostEqual(
            downloaded_mtime, server_mtime, delta=2.0
        )

    def test_full_sync_still_redownloads_wrong_sized_local_file(self):
        class Response(io.BytesIO):
            def __init__(self, value):
                super().__init__(value)
                self.headers = {"Content-Length": str(len(value))}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                self.close()

        with TemporaryDirectory() as directory:
            destination = os.path.join(directory, "asset.bin")
            with open(destination, "wb") as stream:
                stream.write(b"old")
            file_object = Mock()
            file_object.is_exists.return_value = True
            file_object.prepare_repo.return_value = destination
            task = SyncTask(
                task_id="sync-local", key="sync-local",
                file_object=file_object, title="Asset", process="preview",
                local_path=destination,
                web_path="https://example.invalid/asset.bin",
                expected_size=4,
            )
            signals = WorkerSignals()
            finished = []
            signals.finished.connect(
                lambda _task_id, result: finished.append(result)
            )

            with patch(
                "thlib.ui.repository_sync.urllib.request.urlopen",
                return_value=Response(b"new!"),
            ) as urlopen:
                DownloadRunnable(task, signals).run()

            with open(destination, "rb") as stream:
                self.assertEqual(stream.read(), b"new!")

        urlopen.assert_called_once()
        self.assertEqual(len(finished), 1)
        self.assertFalse(finished[0]["exists"])

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
                    "thlib.ui.repository_sync.urllib.request.urlopen",
                    return_value=Response(b"tiny"),
                ),
                patch(
                    "thlib.ui.repository_sync.time.perf_counter",
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
                "thlib.ui.repository_sync.urllib.request.urlopen",
                return_value=Response(expected),
            ):
                DownloadRunnable(task, signals).run()

            with open(destination, "rb") as stream:
                self.assertEqual(stream.read(), expected)
            self.assertEqual(len(finished), 1)
            self.assertFalse(finished[0]["exists"])


if __name__ == "__main__":
    unittest.main()
