import unittest
import os
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QSettings, Qt, QUrl, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from modern_ui.tasks import TasksController
from modern_ui.task_data import parse_datetime
from modern_ui.configuration import ConfigurationController
from modern_ui.user import UserController
from modern_ui.workspace_models.records import RecordListModel


class FakeRegistry:
    def __init__(self):
        self.actions = {}

    def register(self, name, callback):
        self.actions[name] = callback


class FakeWindowModel:
    def __init__(self):
        self.opened = []

    def show_window(self, window_id):
        self.opened.append(window_id)


class FakeDockModel:
    def __init__(self):
        self.opened = []
        self.snapshot_visible = True

    def show_panel(self, panel_id):
        self.opened.append(panel_id)

    def is_panel_visible(self, panel_id):
        return panel_id != "snapshot" or self.snapshot_visible


class FakeRepositorySync(QObject):
    task_finished = Signal(str, str)
    task_failed = Signal(str)

    def __init__(self, http_enabled):
        super().__init__()
        self.http_enabled = bool(http_enabled)
        self.scheduled = []

    def previews_through_http_enabled(self):
        return self.http_enabled

    def schedule_file_object(self, file_object, process="", auto_start=False):
        self.scheduled.append((file_object, process, auto_start))
        return type("Handle", (), {"task_id": "preview-task"})()


class FakePreviewFile:
    def __init__(self, local_path):
        self.local_path = str(local_path)

    def get_filename_with_ext(self):
        return "task-preview.png"

    def get_full_abs_path(self):
        return self.local_path

    def get_icon_preview(self):
        return self

    def get_web_preview(self):
        return self


class FakePreviewSnapshot:
    def __init__(self, file_object):
        self.file_object = file_object

    def get_files_objects(self, group_by=None):
        return {"icon": [self.file_object]}


class FakePreviewLogin:
    def __init__(self, file_object):
        snapshot = FakePreviewSnapshot(file_object)
        context = type("Context", (), {
            "versionless": {"SNAPSHOT": snapshot}, "versions": {},
        })()
        process = type("Process", (), {
            "contexts": {"icon": context},
        })()
        self.process = {"icon": process}


class FakeStatusPipeline:
    pipeline = {
        "Pending": {"color": "#f0b429"},
        "In Progress": {"color": "#33a1fd"},
    }


class FakePublishStatusPipeline:
    pipeline = {
        "Ready": {"color": "#a67cdb"},
        "Approved": {"color": "#3ca66b"},
    }


class FakeWorkflow:
    def get_by_pipeline_code(self, _search_type, pipeline_code):
        if pipeline_code == "publish_pipe":
            return FakePublishStatusPipeline()
        return FakeStatusPipeline()

    def get_by_process_node_type(self, _search_type, _node_type):
        return FakeStatusPipeline()


class FakePipeline:
    pipeline = {"model": {}, "publish": {}}

    def get_process_info(self, process):
        return {
            "model": {
                "label": "Model", "color": "#ff5353",
                "task_pipeline": "task_pipe",
            },
            "publish": {
                "label": "Publish", "color": "#25c2e8",
                "task_pipeline": "publish_pipe",
            },
        }.get(process, {})

    def get_pipeline_process(self, process):
        defaults = {
            "model": {
                "assigned_group": "scriptwriter",
                "bid_duration": "24",
                "completion": "10",
                "duration": "3",
                "supervisor_group": "supervisor",
                "task_pipeline": "task_pipe",
            },
            "publish": {
                "bid_duration": "8",
                "completion": "0",
                "duration": "1",
                "task_pipeline": "publish_pipe",
            },
        }
        return {
            "color": self.get_process_info(process).get("color"),
            "workflow": {
                # TACTIC adds these runtime values beside the configured
                # properties.  They describe the process editor/trigger state
                # and must not preselect a user for a newly created task.
                "assigned": "workflow_editor",
                "supervisor": "workflow_supervisor",
                "node_type": "manual",
                "properties": defaults.get(process, {}),
                "version": 2,
            },
        }


class FakeStype:
    def get_code(self):
        return "prod/asset"

    def get_pretty_name(self):
        return "Asset"

    def get_pipeline(self):
        return {"asset": FakePipeline()}

    def get_workflow(self):
        return FakeWorkflow()


class FakeTarget:
    def __init__(self, tasks=None, code="ASSET0001", title="Robot"):
        self.tasks = list(tasks or [])
        self.code = code
        self.title = title
        self.snapshot_updates = 0

    def get_stype(self):
        return FakeStype()

    def get_pipeline_code(self):
        return "asset"

    def get_title(self):
        return self.title

    def get_code(self):
        return self.code

    def get_search_key(self):
        return "skey://prod/asset?project=test&code={}".format(self.code)

    def get_info(self):
        return {"code": self.code}

    def get_tasks_sobjects(self, include_status_log=False):
        return {task.get_info()["code"]: task for task in self.tasks}

    def update_snapshots(self, order_bys=None):
        self.snapshot_updates += 1


class FakeTask:
    def __init__(self, **values):
        self.values = {
            "code": "TASK0001", "process": "model",
            "status": "In Progress", "assigned": "artist",
            "context": "model/main", "progress": 40,
            "search_type": "prod/asset", "search_code": "ASSET0001",
            "project_code": "test",
            "bid_end_date": "2026-08-04 18:00:00",
        }
        self.values.update(values)
        self.update_dict = {}

    def get_info(self):
        return self.values

    def get_search_key(self):
        return "skey://sthpw/task?project=test&code={}".format(
            self.values["code"]
        )

    def get_notes_count(self):
        return {"model": 3}

    def set_value(self, key, value):
        self.update_dict[key] = value

    def commit(self, triggers=True):
        self.values.update(self.update_dict)
        return dict(self.values)


class FakeLogin:
    def __init__(self, login):
        self.login = login

    def get_login(self):
        return self.login


class FakeLoginGroup:
    def __init__(self, code, label, logins):
        self.code = code
        self.label = label
        self.logins = [FakeLogin(login) for login in logins]

    def get_code(self):
        return self.code

    def get_login_group(self):
        return self.code

    def get_pretty_name(self):
        return self.label

    def get_logins(self):
        return list(self.logins)


class FakeCurrentLogin:
    def __init__(self, groups, all_groups=None):
        self.groups = list(groups)
        self.all_groups = list(
            groups if all_groups is None else all_groups
        )

    def get_login_groups(self):
        return list(self.groups)

    def get_all_login_groups(self):
        return list(self.all_groups)


class ImmediateWorker(QObject):
    result = Signal(object)
    error = Signal(object)

    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    def start(self):
        try:
            self.result.emit(self.operation())
        except Exception as exc:
            self.error.emit(exc)


class FakeBatchServer:
    def __init__(self):
        self.updates = []

    def update_multiple(self, data, triggers=True):
        self.updates.append((dict(data), bool(triggers)))
        return {"updated": len(data)}


class FailingBatchServer(FakeBatchServer):
    def update_multiple(self, data, triggers=True):
        raise RuntimeError("Batch update failed")


class FakeWorkspace(QObject):
    selection_changed = Signal()

    def __init__(self):
        super().__init__()
        self._selected_sobject = FakeTarget()
        self._task_sobjects = [FakeTask()]

    def replace_tasks(self, tasks):
        self._task_sobjects = list(tasks or [])


class FakeApplication(QObject):
    project_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.workspace_state = FakeWorkspace()
        self._registry = FakeRegistry()
        self.window_model = FakeWindowModel()
        self.dock_model = FakeDockModel()
        self._sobject_editor_request = {}
        self._current_project_code = "test"
        self.debug_log = None

    def open_window(self, window_id):
        self.window_model.show_window(window_id)


class TasksControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.application = FakeApplication()
        self.controller = TasksController(self.application)

    def test_compact_model_contains_empty_pipeline_process(self):
        records = self.controller.process_model._records
        self.assertEqual([item["process"] for item in records], ["model", "publish"])
        self.assertTrue(records[0]["hasTask"])
        self.assertEqual(records[0]["taskCount"], 1)
        self.assertEqual(records[0]["notes"], 3)
        self.assertEqual(records[0]["statusColor"], "#33a1fd")
        self.assertFalse(records[1]["hasTask"])
        self.assertEqual(records[1]["color"], "#25c2e8")

    def test_incomplete_priority_catalog_is_not_cached_as_ready(self):
        self.controller._task_field_catalogs["test"] = {
            "priorityChoices": [{
                "value": "", "label": "No priority", "color": "",
            }],
        }
        self.assertFalse(
            self.controller._task_field_catalog_ready("test")
        )

        self.controller._task_field_catalogs["test"][
            "priorityChoices"
        ].append({
            "value": "3", "label": "Important", "color": "",
        })
        self.assertTrue(
            self.controller._task_field_catalog_ready("test")
        )
        self.assertEqual(len(self.controller.taskPriorityChoices), 2)

    def test_object_scope_requests_task_field_catalog(self):
        with patch.object(
                self.controller, "_ensure_task_field_catalog") as ensure:
            self.controller._advanced_visible = True
            self.controller.use_current_object()

        ensure.assert_called_once_with("test")

    def test_processes_keep_their_own_task_status_pipeline(self):
        model_statuses = self.controller._status_choices_for(
            self.application.workspace_state._selected_sobject, "model"
        )
        publish_statuses = self.controller._status_choices_for(
            self.application.workspace_state._selected_sobject, "publish"
        )

        self.assertEqual(
            [item["value"] for item in model_statuses],
            ["Pending", "In Progress"],
        )
        self.assertEqual(
            [item["value"] for item in publish_statuses],
            ["Ready", "Approved"],
        )

    def test_multiple_tasks_on_process_are_distinct_and_selectable(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", context="model/main"),
            FakeTask(
                code="TASK0002", context="model/review",
                assigned="reviewer", status="Pending",
            ),
        ]
        self.controller._rebuild_process_model()

        model = self.controller.process_model.get(0)
        self.assertEqual(model["taskCount"], 2)
        self.assertEqual(
            [item["value"] for item in model["taskChoices"]],
            ["TASK0001", "TASK0002"],
        )

        self.controller.select_process_task(0, "TASK0002")
        selected = self.controller.process_model.get(0)
        self.assertEqual(selected["currentTaskCode"], "TASK0002")
        self.assertEqual(selected["context"], "model/review")

    def test_quick_task_activation_uses_common_notes_context(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", context="model/main"),
            FakeTask(code="TASK0002", context="model/review"),
        ]
        self.controller._rebuild_process_model()
        activated = []
        self.controller.taskActivated.connect(
            lambda code, parent, process: activated.append(
                (code, parent, process)
            )
        )

        self.controller.activate_process_task(0, "TASK0002")

        self.assertEqual(
            activated,
            [("TASK0002", self.controller.targetSearchKey, "model")],
        )
        self.assertEqual(
            self.controller.process_model.get(0)["currentTaskCode"],
            "TASK0002",
        )

    def test_task_inspector_reuses_process_draft_and_selection(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", context="model/main"),
            FakeTask(
                code="TASK0002", context="model/review",
                assigned="reviewer", status="Pending",
            ),
        ]
        self.controller._rebuild_process_model()

        self.controller.select_process_task_code("model", "TASK0002")
        record = self.controller.task_inspector_record("TASK0002")
        self.assertEqual(record["currentTaskCode"], "TASK0002")
        self.assertEqual(record["assigned"], "reviewer")

        self.controller.set_inspector_task_value(
            "TASK0002", "status", "In Progress"
        )
        self.controller.set_inspector_task_value(
            "TASK0002", "start", "2026-08-10"
        )
        self.controller.set_inspector_task_value(
            "TASK0002", "end", "2026-08-12"
        )
        with patch.object(self.controller, "_progress_column", return_value="progress"):
            self.controller.set_inspector_task_value(
                "TASK0002", "progress", "75"
            )
        staged = self.controller.task_inspector_record("TASK0002")
        self.assertEqual(staged["status"], "In Progress")
        self.assertEqual(staged["start"], "2026-08-10")
        self.assertEqual(staged["end"], "2026-08-12")
        self.assertEqual(staged["progress"], 75)
        self.assertEqual(staged["validationError"], "")
        self.assertTrue(staged["dirty"])

        self.controller.discard_inspector_task("TASK0002")
        discarded = self.controller.task_inspector_record("TASK0002")
        self.assertEqual(discarded["status"], "Pending")
        self.assertEqual(discarded["progress"], 40)
        self.assertFalse(discarded["dirty"])

    def test_task_inspector_validates_and_maps_deadline_and_progress(self):
        from thlib.environment import env_inst

        task = self.application.workspace_state._task_sobjects[0]
        self.controller.set_inspector_task_value(
            "TASK0001", "end", "not a date"
        )
        invalid = self.controller.task_inspector_record("TASK0001")
        self.assertIn("Deadline", invalid["validationError"])
        self.assertFalse(self.controller.save_inspector_task("TASK0001"))

        self.controller.set_inspector_task_value(
            "TASK0001", "end", "2026-08-12 18:00:00"
        )
        with patch.object(self.controller, "_progress_column", return_value="progress"):
            self.controller.set_inspector_task_value(
                "TASK0001", "progress", "75"
            )
            def add_task(operation, *args, **kwargs):
                return ImmediateWorker(
                    lambda: operation(*args, **kwargs)
                )

            with patch.object(
                env_inst.server_pool, "add_task",
                side_effect=add_task,
            ):
                self.assertTrue(self.controller.save_inspector_task("TASK0001"))
                QGuiApplication.processEvents()

        self.assertEqual(task.get_info()["bid_end_date"], "2026-08-12 18:00:00")
        self.assertEqual(task.get_info()["progress"], 75)

    def test_no_task_state_keeps_pipeline_processes_available(self):
        self.application.workspace_state._task_sobjects = []
        self.controller._rebuild_process_model()

        records = self.controller.process_model._records
        self.assertEqual([item["process"] for item in records], ["model", "publish"])
        self.assertTrue(all(not item["hasTask"] for item in records))
        self.assertTrue(all(item["taskCount"] == 0 for item in records))

    def test_no_object_selection_is_a_normal_empty_state(self):
        workspace = self.application.workspace_state
        workspace._selected_sobject = None
        workspace._task_sobjects = []

        self.controller.set_advanced_visible(True)

        self.assertEqual(self.controller.advanced_model.count(), 0)
        self.assertEqual(self.controller.advancedError, "")
        self.assertEqual(
            self.controller.advancedEmptyMessage,
            "Select an sObject to view tasks",
        )

    def test_removed_status_remains_visible_but_cannot_be_bulk_applied(self):
        task = FakeTask(status="Retired Status")
        workspace = self.application.workspace_state
        workspace._selected_sobject = FakeTarget(tasks=[task])
        workspace._task_sobjects = [task]

        self.controller._rebuild_process_model()
        process_record = self.controller.process_model.get(0)
        retired = next(
            item for item in process_record["statusChoices"]
            if item["value"] == "Retired Status"
        )
        self.assertEqual(retired["label"], "Retired Status (unavailable)")
        self.assertFalse(retired["available"])

        self.controller.open_workspace()
        self.controller.toggle_advanced_checked("TASK0001")
        self.assertNotIn(
            "Retired Status",
            [item["value"] for item in self.controller.bulkStatusOptions],
        )

    def test_missing_assignee_is_retained_without_an_avatar(self):
        task = FakeTask(assigned="former_artist")
        workspace = self.application.workspace_state
        workspace._selected_sobject = FakeTarget(tasks=[task])
        workspace._task_sobjects = [task]

        self.controller.open_workspace()

        record = self.controller.advanced_model.get(0)
        former = next(
            item for item in record["userChoices"]
            if item["value"] == "former_artist"
        )
        self.assertEqual(former["label"], "former_artist")
        self.assertEqual(former["avatarUrl"], "")
        self.assertEqual(record["assignedLabel"], "former_artist")

    def test_each_task_keeps_its_assignee_choice_for_the_same_process(self):
        tasks = [
            FakeTask(code="TASK_ARTIST", assigned="artist"),
            FakeTask(code="TASK_REVIEWER", assigned="reviewer"),
        ]
        target = FakeTarget(tasks=tasks)
        self.controller.task_store.set_scope("object", target=target)
        self.controller.task_store.apply_source(tasks, [target])

        records = self.controller._task_records(tasks)

        self.assertEqual(
            [record["assigned"] for record in records],
            ["artist", "reviewer"],
        )
        self.assertTrue(all(
            record["assignedChoiceIndex"] >= 0 for record in records
        ))

    def test_user_scope_uses_filtered_login_when_task_payload_is_incomplete(self):
        task = FakeTask(assigned="")
        target = FakeTarget(tasks=[task])
        self.controller.task_store.set_scope("user", user="artist")
        self.controller.task_store.apply_source([task], [target])

        record = self.controller._task_records([task])[0]

        self.assertEqual(record["assigned"], "artist")
        self.assertEqual(record["assignedLabel"], "artist")
        self.assertGreaterEqual(record["assignedChoiceIndex"], 0)

    def test_open_workspace_uses_current_loaded_tasks(self):
        self.controller.open_workspace()
        self.assertEqual(self.application.dock_model.opened, ["tasks"])
        self.assertEqual(self.controller.workspaceSurface, "browser")
        self.assertEqual(self.controller.advanced_model.count(), 1)
        self.assertEqual(
            self.controller.advanced_model.get(0)["parentTitle"], "Robot"
        )

        self.controller.open_quick_workspace()
        self.assertEqual(self.controller.workspaceSurface, "quick")
        self.assertEqual(self.application.dock_model.opened, ["tasks", "tasks"])

    def test_visible_object_scope_follows_selected_sobject_tasks(self):
        self.controller.set_advanced_visible(True)
        self.controller.task_store.total_count = 3670
        self.application.workspace_state._task_sobjects = [
            FakeTask(code="TASK0001", process="model"),
            FakeTask(code="TASK0002", process="publish"),
        ]

        self.application.workspace_state.selection_changed.emit()

        self.assertEqual(self.controller.advanced_model.count(), 2)
        self.assertEqual(self.controller.advancedLoadedCount, 2)
        self.assertEqual(self.controller.advancedTotalCount, 2)

    def test_visible_object_scope_filters_a_selected_process(self):
        self.controller.set_advanced_visible(True)
        self.application.workspace_state._task_sobjects = [
            FakeTask(code="TASK0001", process="model"),
            FakeTask(code="TASK0002", process="publish"),
        ]

        with patch.object(
                self.controller, "_selected_object_process",
                return_value="publish"):
            self.application.workspace_state.selection_changed.emit()

        self.assertEqual(self.controller.advanced_model.count(), 1)
        self.assertEqual(
            self.controller.advanced_model.get(0)["taskCode"], "TASK0002"
        )
        self.assertEqual(self.controller.advancedTotalCount, 1)

    def test_object_scope_uses_all_distinct_selected_sobjects(self):
        first = FakeTarget(code="ASSET0001", title="First")
        second = FakeTarget(code="ASSET0002", title="Second")

        class Node:
            node_type = "sobject"
            parent_id = ""

            def __init__(self, source):
                self.source = source

        nodes = {"first": Node(first), "second": Node(second)}
        tab = type("Tab", (), {
            "selected_node_ids": ["first", "second"],
        })()
        self.application._current_tab = lambda: tab
        self.application.workspace_model = type("Model", (), {
            "node_for": staticmethod(nodes.get),
        })()

        with patch.object(
                self.controller, "_use_multiple_targets") as use_multiple:
            self.controller.use_current_object()

        use_multiple.assert_called_once()
        self.assertEqual(use_multiple.call_args.args[0], [first, second])

    def test_snapshot_summary_is_built_once_per_parent_process(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", context="model/main"),
            FakeTask(code="TASK0002", context="model/review"),
        ]
        self.controller.use_current_object()

        with patch.object(
            self.controller, "_snapshot_summary_for",
            return_value={
                "parentPreviewUrl": "", "snapshotCount": 2,
                "snapshotFileCount": 3, "latestVersion": "v002",
            },
        ) as summary:
            records = self.controller._task_records(
                workspace._task_sobjects
            )

        self.assertEqual(summary.call_count, 1)
        self.assertTrue(all(
            record["latestVersion"] == "v002"
            and record["snapshotFileCount"] == 3
            for record in records
        ))

    def test_task_preview_does_not_bypass_disabled_http_setting(self):
        repository_sync = FakeRepositorySync(http_enabled=False)
        self.application.repository_sync = repository_sync
        controller = TasksController(self.application)
        snapshot = FakePreviewSnapshot(
            FakePreviewFile("Z:/missing/task-preview.png")
        )

        self.assertEqual(controller._snapshot_preview_url(snapshot), "")
        self.assertEqual(repository_sync.scheduled, [])

    def test_task_preview_uses_repository_sync_when_http_is_enabled(self):
        repository_sync = FakeRepositorySync(http_enabled=True)
        self.application.repository_sync = repository_sync
        controller = TasksController(self.application)
        snapshot = FakePreviewSnapshot(
            FakePreviewFile("Z:/missing/task-preview.png")
        )

        preview_url = controller._snapshot_preview_url(snapshot)

        self.assertEqual(preview_url, "pending-preview:preview-task")
        self.assertEqual(len(repository_sync.scheduled), 1)
        self.assertEqual(repository_sync.scheduled[0][1:], ("preview", True))

    def test_task_user_avatar_uses_same_repository_preview_policy(self):
        repository_sync = FakeRepositorySync(http_enabled=False)
        self.application.repository_sync = repository_sync
        controller = TasksController(self.application)
        login = FakePreviewLogin(
            FakePreviewFile("Z:/missing/user-avatar.png")
        )

        self.assertEqual(controller._login_avatar_url(login), "")
        self.assertEqual(repository_sync.scheduled, [])

        repository_sync.http_enabled = True
        self.assertEqual(
            controller._login_avatar_url(login),
            "pending-preview:preview-task",
        )
        self.assertEqual(len(repository_sync.scheduled), 1)

    def test_completed_task_preview_replaces_pending_model_urls(self):
        repository_sync = FakeRepositorySync(http_enabled=True)
        self.application.repository_sync = repository_sync
        controller = TasksController(self.application)
        token = "pending-preview:preview-task"
        controller._pending_preview_paths[token] = (
            "Z:/missing/task-preview.png"
        )
        controller._advanced_raw = [{
            "taskCode": "TASK0001", "parentPreviewUrl": token,
            "assignedAvatar": token,
            "userChoices": [{"value": "artist", "avatarUrl": token}],
        }]
        controller.advanced_model.replace([{
            "taskCode": "TASK0001", "parentPreviewUrl": token,
            "assignedAvatar": token,
            "userChoices": [{"value": "artist", "avatarUrl": token}],
        }])

        controller._repository_preview_ready(
            "preview-task", "C:/repo/task-preview.png"
        )

        ready_url = QUrl.fromLocalFile(
            str(Path("C:/repo/task-preview.png").resolve())
        ).toString()
        self.assertEqual(
            controller._advanced_raw[0]["parentPreviewUrl"], ready_url
        )
        self.assertEqual(
            controller.advanced_model.get(0)["parentPreviewUrl"], ready_url
        )
        self.assertEqual(
            controller.advanced_model.get(0)["assignedAvatar"], ready_url
        )
        self.assertEqual(
            controller.advanced_model.get(0)["userChoices"][0]["avatarUrl"],
            ready_url,
        )

    def test_activating_task_reuses_shared_snapshot_browser_loader(self):
        loader = Mock()
        self.application.load_task_snapshot_context = loader
        self.controller.open_workspace()

        self.controller.activate_advanced_task("TASK0001")

        loader.assert_called_once_with(
            self.application.workspace_state._selected_sobject,
            self.application.workspace_state._selected_sobject.get_search_key(),
            "model", "model/main",
        )

    def test_hidden_snapshot_browser_refreshes_summary_after_checkin(self):
        from thlib.environment import env_inst

        self.controller.open_workspace()
        parent = self.application.workspace_state._selected_sobject
        parent_key = parent.get_search_key()
        self.application._selected_detail_key = parent_key
        self.application._task_snapshot_source = parent
        self.application.dock_model.snapshot_visible = False
        self.application.invalidate_task_snapshot_context = Mock()
        self.application.mark_task_snapshot_source_current = Mock()
        workers = []

        def add_task(operation, **_kwargs):
            worker = ImmediateWorker(operation)
            workers.append(worker)
            return worker

        with patch.object(
            env_inst.server_pool, "add_task",
            side_effect=add_task,
        ):
            self.controller._checkin_completed({
                "searchKey": parent_key, "process": "model",
            })
            QGuiApplication.processEvents()

        self.assertEqual(parent.snapshot_updates, 1)
        self.application.invalidate_task_snapshot_context.assert_called_once_with(
            parent_key, "model"
        )
        self.application.mark_task_snapshot_source_current.assert_called_once_with(
            parent_key
        )

    def test_workspace_preferences_restore_without_saving_transient_state(self):
        with TemporaryDirectory() as directory:
            settings = QSettings(
                str(Path(directory) / "tasks.ini"),
                QSettings.Format.IniFormat,
            )
            application = FakeApplication()
            application._settings = settings
            controller = TasksController(application)
            columns = controller.configuration_values()["columns"]
            columns.reverse()
            for order, column in enumerate(columns):
                column["order"] = order
            columns[0]["visible"] = False
            columns[1]["width"] = 120
            controller.apply_configuration({
                "viewMode": "gantt",
                "sortMode": "recent",
                "groupMode": "user",
                "columns": columns,
            })
            controller.set_quick_view_mode("compact")
            controller._show_workspace_surface("browser")

            restored_application = FakeApplication()
            restored_application._settings = settings
            restored = TasksController(restored_application)

            self.assertEqual(restored.viewMode, "gantt")
            self.assertEqual(restored.sortMode, "recent")
            self.assertEqual(restored.groupMode, "user")
            self.assertEqual(restored.quickViewMode, "compact")
            self.assertEqual(restored.workspaceSurface, "browser")
            self.assertEqual(
                [item["key"] for item in restored.taskColumns],
                [item["key"] for item in columns],
            )
            self.assertNotIn("day", settings.allKeys())
            self.assertNotIn("checked", settings.allKeys())

    def test_configuration_tasks_page_applies_its_normalized_contract(self):
        applied = []
        columns = self.controller.configuration_values()["columns"]
        original = {
            **self.controller.configuration_values(),
            "inspectorExpanded": False,
        }
        configuration = ConfigurationController(
            lambda *_args: None,
            lambda _message: None,
            task_values=lambda: original,
            apply_task_configuration=lambda values: applied.append(values),
        )
        configuration._original_values["tasks_preferences"] = original
        values = {
            "viewMode": "gantt", "sortMode": "recent",
            "groupMode": "status", "inspectorExpanded": True,
            "columns": columns,
        }

        configuration.update_page("tasks_preferences", values)
        self.assertTrue(configuration._apply_page("tasks_preferences"))

        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0]["viewMode"], "gantt")
        self.assertEqual(applied[0]["groupMode"], "status")
        self.assertTrue(applied[0]["inspectorExpanded"])

    def test_advanced_status_edit_is_staged_until_saved_or_discarded(self):
        self.controller.open_workspace()
        self.controller.stage_advanced_value(
            "TASK0001", "status", "Pending"
        )

        record = self.controller.advanced_model.get(0)
        self.assertEqual(record["status"], "Pending")
        self.assertTrue(record["dirty"])
        self.assertEqual(self.controller.advancedDirtyCount, 1)
        self.assertEqual(
            self.application.workspace_state._task_sobjects[0]
                .get_info()["status"],
            "In Progress",
        )

        self.controller.discard_advanced_changes()
        self.assertEqual(
            self.controller.advanced_model.get(0)["status"], "In Progress"
        )
        self.assertEqual(self.controller.advancedDirtyCount, 0)

    def test_selection_does_not_refresh_visible_task_server_data(self):
        self.controller.open_workspace()
        visible_set_changes = []
        self.controller.visibleTaskSetChanged.connect(
            lambda: visible_set_changes.append(True)
        )

        self.controller.activate_advanced_task("TASK0001", 0)

        self.assertEqual(visible_set_changes, [])
        self.controller.set_filter("text", "no matching task")
        self.assertEqual(visible_set_changes, [True])

    def test_advanced_staged_edit_saves_through_one_worker(self):
        from thlib.environment import env_inst

        self.controller.open_workspace()
        self.controller.stage_advanced_value(
            "TASK0001", "status", "Pending"
        )
        workers = []

        def add_task(operation):
            worker = ImmediateWorker(operation)
            workers.append(worker)
            return worker

        with patch.object(env_inst.server_pool, "add_task", side_effect=add_task):
            self.assertTrue(self.controller.save_advanced_changes())
            QGuiApplication.processEvents()

        self.assertEqual(len(workers), 1)
        self.assertEqual(
            self.application.workspace_state._task_sobjects[0]
                .get_info()["status"],
            "Pending",
        )
        self.assertEqual(self.controller.advancedDirtyCount, 0)
        self.assertFalse(self.controller.advancedSaving)

    def test_expected_work_hours_save_to_native_bid_duration(self):
        from thlib.environment import env_inst

        task = self.application.workspace_state._task_sobjects[0]
        self.controller.open_workspace()
        self.controller.stage_advanced_value(
            "TASK0001", "plannedHours", 32
        )

        with patch.object(
                env_inst.server_pool, "add_task",
                side_effect=lambda operation: ImmediateWorker(operation)):
            self.assertTrue(self.controller.save_advanced_changes())
            QGuiApplication.processEvents()

        self.assertEqual(task.get_info()["bid_duration"], "32")
        self.assertNotIn("plannedHours", task.get_info())

    def test_gantt_drag_stages_dates_and_preserves_time(self):
        task = self.application.workspace_state._task_sobjects[0]
        task.get_info().update({
            "bid_start_date": "2026-08-03 09:30:00",
            "bid_end_date": "2026-08-05 18:15:00",
        })
        self.controller.open_workspace()
        record = self.controller.gantt_model.get(0)

        self.assertTrue(self.controller.stage_gantt_schedule(
            "TASK0001", record["ganttStartDay"] + 2,
            record["ganttDurationDays"],
        ))

        staged = self.controller.gantt_model.get(0)
        self.assertEqual(staged["start"], "2026-08-05 09:30:00")
        self.assertEqual(staged["end"], "2026-08-07 18:15:00")
        self.assertTrue(staged["dirty"])
        self.assertEqual(
            task.get_info()["bid_start_date"], "2026-08-03 09:30:00"
        )

    def test_gantt_dates_save_to_task_schedule_columns(self):
        from thlib.environment import env_inst

        task = self.application.workspace_state._task_sobjects[0]
        task.get_info().update({
            "bid_start_date": "2026-08-03 09:30:00",
            "bid_end_date": "2026-08-05 18:15:00",
        })
        self.controller.open_workspace()
        record = self.controller.gantt_model.get(0)
        self.controller.stage_gantt_schedule(
            "TASK0001", record["ganttStartDay"], 5
        )

        with patch.object(
                env_inst.server_pool, "add_task",
                side_effect=lambda operation: ImmediateWorker(operation)):
            self.assertTrue(self.controller.save_advanced_changes())
            QGuiApplication.processEvents()

        self.assertEqual(
            task.get_info()["bid_start_date"], "2026-08-03 09:30:00"
        )
        self.assertEqual(
            task.get_info()["bid_end_date"], "2026-08-07 18:15:00"
        )
        self.assertNotIn("start", task.get_info())
        self.assertNotIn("end", task.get_info())

    def test_gantt_move_shifts_checked_tasks_as_one_edit(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(
                code="TASK0001", bid_start_date="2026-08-03 09:00:00",
                bid_end_date="2026-08-05 18:00:00",
            ),
            FakeTask(
                code="TASK0002", process="publish",
                bid_start_date="2026-08-10 10:00:00",
                bid_end_date="2026-08-11 19:00:00",
            ),
        ]
        self.controller.use_current_object()
        self.controller.toggle_advanced_checked("TASK0001")
        self.controller.toggle_advanced_checked("TASK0002")
        records = {
            item["taskCode"]: item
            for item in self.controller.gantt_model._records
        }

        self.assertTrue(self.controller.stage_gantt_schedule(
            "TASK0001", records["TASK0001"]["ganttStartDay"] + 2,
            records["TASK0001"]["ganttDurationDays"], "move",
        ))

        staged = {
            item["taskCode"]: item
            for item in self.controller.gantt_model._records
        }
        self.assertEqual(staged["TASK0001"]["start"], "2026-08-05 09:00:00")
        self.assertEqual(staged["TASK0002"]["start"], "2026-08-12 10:00:00")
        self.assertTrue(self.controller.ganttCanUndo)

    def test_gantt_undo_preserves_other_task_drafts(self):
        task = self.application.workspace_state._task_sobjects[0]
        task.get_info().update({
            "bid_start_date": "2026-08-03 09:00:00",
            "bid_end_date": "2026-08-05 18:00:00",
        })
        self.controller.open_workspace()
        self.controller.stage_advanced_value("TASK0001", "status", "Pending")
        record = self.controller.gantt_model.get(0)
        self.controller.stage_gantt_schedule(
            "TASK0001", record["ganttStartDay"] + 1,
            record["ganttDurationDays"], "move",
        )

        self.controller.undo_gantt_change()

        restored = self.controller.gantt_model.get(0)
        self.assertEqual(restored["start"], "2026-08-03 09:00:00")
        self.assertEqual(restored["status"], "Pending")
        self.assertTrue(self.controller.ganttCanRedo)
        self.controller.redo_gantt_change()
        self.assertEqual(
            self.controller.gantt_model.get(0)["start"],
            "2026-08-04 09:00:00",
        )

    def test_gantt_workday_batch_shift_skips_weekend(self):
        task = self.application.workspace_state._task_sobjects[0]
        task.get_info().update({
            "bid_start_date": "2026-08-07 09:00:00",
            "bid_end_date": "2026-08-10 18:00:00",
        })
        self.controller.open_workspace()
        self.controller.toggle_advanced_checked("TASK0001")
        self.controller.set_gantt_working_days(True)

        self.assertTrue(self.controller.apply_gantt_batch("shift", 1))

        staged = self.controller.gantt_model.get(0)
        self.assertEqual(staged["start"], "2026-08-10 09:00:00")
        self.assertEqual(staged["end"], "2026-08-11 18:00:00")

    def test_gantt_progress_uses_schema_column_and_undo(self):
        self.controller.open_workspace()

        with patch.object(
                TasksController, "_progress_column",
                return_value="completion"):
            self.assertTrue(
                self.controller.stage_gantt_progress("TASK0001", 75)
            )
            self.assertEqual(self.controller.gantt_model.get(0)["progress"], 75)
            self.controller.undo_gantt_change()
            self.assertEqual(self.controller.gantt_model.get(0)["progress"], 40)
            self.controller.redo_gantt_change()
            self.assertEqual(self.controller.gantt_model.get(0)["progress"], 75)

    def test_gantt_progress_saves_through_detected_schema_column(self):
        from thlib.environment import env_inst

        task = self.application.workspace_state._task_sobjects[0]
        self.controller.open_workspace()
        with patch.object(
                TasksController, "_progress_column",
                return_value="completion"):
            self.assertTrue(
                self.controller.stage_gantt_progress("TASK0001", 75)
            )
            with patch.object(
                    env_inst.server_pool, "add_task",
                    side_effect=lambda operation: ImmediateWorker(operation)):
                self.assertTrue(self.controller.save_advanced_changes())
                QGuiApplication.processEvents()

        self.assertEqual(task.get_info()["completion"], 75)

    def test_gantt_resource_mode_restores_previous_grouping(self):
        self.controller.open_workspace()
        self.controller.set_sort_mode("due")
        self.controller.set_group_mode("process")

        self.controller.set_gantt_resource_mode(True)

        self.assertTrue(self.controller.ganttResourceMode)
        self.assertEqual(self.controller.sortMode, "user")
        self.assertEqual(self.controller.groupMode, "user")
        self.controller.set_gantt_resource_mode(False)
        self.assertFalse(self.controller.ganttResourceMode)
        self.assertEqual(self.controller.sortMode, "due")
        self.assertEqual(self.controller.groupMode, "process")

    def test_active_and_checked_task_selection_are_independent(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001"),
            FakeTask(code="TASK0002", process="publish"),
            FakeTask(code="TASK0003"),
        ]
        self.controller.use_current_object()

        self.controller.activate_advanced_task("TASK0001", 0)
        records = {
            item["taskCode"]: item
            for item in self.controller.advanced_model._records
        }
        self.assertTrue(records["TASK0001"]["selected"])
        self.assertFalse(records["TASK0001"]["checked"])

        self.controller.toggle_advanced_checked("TASK0001")
        self.assertEqual(self.controller.advancedCheckedCount, 1)
        self.controller.activate_advanced_task(
            "TASK0002", Qt.KeyboardModifier.ControlModifier.value
        )
        self.assertEqual(self.controller.advancedCheckedCount, 2)

        self.controller.activate_advanced_task(
            "TASK0003", Qt.KeyboardModifier.ShiftModifier.value
        )
        self.assertEqual(self.controller.advancedCheckedCount, 3)

    def test_bulk_edit_uses_exact_checked_task_keys_in_one_request(self):
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc

        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", status="In Progress"),
            FakeTask(code="TASK0002", status="Pending"),
        ]
        self.controller.use_current_object()
        self.controller.toggle_advanced_checked("TASK0001")
        self.controller.toggle_advanced_checked("TASK0002")
        self.assertTrue(self.controller.bulkEditor["statusMixed"])
        self.assertEqual(
            [item["value"] for item in self.controller.bulkStatusOptions],
            ["Pending", "In Progress"],
        )
        self.controller.set_bulk_value("status", "Pending")
        self.controller.set_bulk_enabled("status", True)
        self.assertEqual(self.controller.bulkPreview["eligible"], 1)
        self.assertEqual(self.controller.bulkPreview["unchanged"], 1)

        server = FakeBatchServer()
        workers = []

        def add_task(operation):
            worker = ImmediateWorker(operation)
            workers.append(worker)
            return worker

        with patch.object(env_inst.server_pool, "add_task", side_effect=add_task), \
                patch.object(tc, "server_start", return_value=server):
            self.assertTrue(self.controller.apply_bulk())
            QGuiApplication.processEvents()

        self.assertEqual(len(workers), 1)
        payload, triggers = server.updates[0]
        self.assertTrue(triggers)
        self.assertEqual(
            list(payload),
            ["skey://sthpw/task?project=test&code=TASK0001"],
        )
        self.assertEqual(payload[list(payload)[0]], {"status": "Pending"})
        self.assertEqual(workspace._task_sobjects[0].get_info()["status"], "Pending")
        self.assertEqual(self.controller.advancedCheckedCount, 0)

    def test_bulk_status_must_be_valid_for_every_checked_pipeline(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", process="model"),
            FakeTask(code="TASK0002", process="publish", status="Ready"),
        ]
        self.controller.use_current_object()
        self.controller.toggle_advanced_checked("TASK0001")
        self.controller.toggle_advanced_checked("TASK0002")

        self.assertEqual(self.controller.bulkStatusOptions, [])
        self.controller.set_bulk_value("status", "Pending")
        self.controller.set_bulk_enabled("status", True)
        self.assertEqual(self.controller.bulkPreview["invalid"], 1)
        self.assertFalse(self.controller.bulkCanApply)
        self.assertFalse(self.controller.apply_bulk())
        self.assertEqual(self.controller.advancedCheckedCount, 2)

    def test_filtering_does_not_expand_bulk_selection(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", status="In Progress"),
            FakeTask(code="TASK0002", status="Pending"),
        ]
        self.controller.use_current_object()
        self.controller.toggle_advanced_checked("TASK0001")
        self.controller.set_filter("status", "Pending")

        self.assertEqual(self.controller.advanced_model.count(), 1)
        self.assertEqual(self.controller.advancedCheckedCount, 1)
        self.assertEqual(self.controller.bulkPreview["targets"], 1)

    def test_quick_filters_sorting_and_grouping_are_local(self):
        from thlib.environment import env_inst

        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(
                code="TASK0001", process="model",
                status="In Progress", assigned="artist",
            ),
            FakeTask(
                code="TASK0002", process="model",
                status="Pending", assigned="",
            ),
            FakeTask(
                code="TASK0003", process="publish",
                status="Ready", assigned="artist",
            ),
        ]
        self.controller.use_current_object()
        self.controller.activate_advanced_task("TASK0001", 0)

        with patch.object(env_inst.server_pool, "add_task") as add_task:
            self.controller.toggle_quick_filter("status", "Pending")
            self.controller.set_sort_mode("status")
            self.controller.set_group_mode("process")

        add_task.assert_not_called()
        self.assertEqual(self.controller.advanced_model.count(), 1)
        self.assertEqual(
            self.controller.advanced_model.get(0)["taskCode"], "TASK0002"
        )
        self.assertEqual(self.controller.activeQuickFilterCount, 1)
        self.assertEqual(self.controller._selected_advanced_code, "TASK0001")

        status_group = next(
            group for group in self.controller.quickFilterGroups
            if group["key"] == "status"
        )
        self.assertEqual(
            {item["key"] for item in status_group["options"]},
            {"In Progress", "Pending", "Ready"},
        )

        self.controller.clear_quick_filters()
        records = {
            item["taskCode"]: item
            for item in self.controller.advanced_model._records
        }
        self.assertTrue(records["TASK0001"]["selected"])

    def test_group_collapse_keeps_task_rows_in_the_model(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", process="model"),
            FakeTask(code="TASK0002", process="model"),
            FakeTask(code="TASK0003", process="publish", status="Ready"),
        ]
        self.controller.use_current_object()
        self.controller.set_group_mode("process")
        metrics_before = self.controller.performanceMetrics
        visible_set_changes = []
        self.controller.visibleTaskSetChanged.connect(
            lambda: visible_set_changes.append(True)
        )
        self.controller.toggle_group_collapsed("model")

        self.assertEqual(self.controller.advanced_model.count(), 3)
        self.assertEqual(self.controller.table_model.count(), 2)
        self.assertEqual(
            self.controller.performanceMetrics["projectionRebuilds"],
            metrics_before["projectionRebuilds"],
        )
        self.assertEqual(
            self.controller.performanceMetrics["advancedSignals"],
            metrics_before["advancedSignals"],
        )
        self.assertEqual(visible_set_changes, [])
        model_rows = [
            record for record in self.controller.advanced_model._records
            if record["process"] == "model"
        ]
        self.assertEqual(sum(record["groupFirst"] for record in model_rows), 1)
        self.assertTrue(all(record["groupCount"] == 2 for record in model_rows))
        self.assertTrue(all(record["groupCollapsed"] for record in model_rows))

    def test_quick_filter_catalog_adds_assignees_only_for_supervisor_scope(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", assigned="artist"),
            FakeTask(code="TASK0002", process="review", assigned="reviewer"),
        ]
        self.controller.use_current_object()
        object_groups = {
            group["key"] for group in self.controller.quickFilterGroups
        }
        self.assertNotIn("assigned", object_groups)
        review = next(
            group for group in self.controller.quickFilterGroups
            if group["key"] == "preset"
        )
        self.assertIn("review", {
            option["key"] for option in review["options"]
        })

        self.controller._advanced_scope = "team"
        team_groups = {
            group["key"] for group in self.controller.quickFilterGroups
        }
        self.assertIn("assigned", team_groups)

    def test_failed_bulk_rows_remain_checked_for_retry(self):
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc

        self.controller.use_current_object()
        self.controller.toggle_advanced_checked("TASK0001")
        self.controller.set_bulk_value("status", "Pending")
        self.controller.set_bulk_enabled("status", True)

        with patch.object(
                env_inst.server_pool, "add_task",
                side_effect=lambda operation: ImmediateWorker(operation)), \
                patch.object(
                    tc, "server_start", return_value=FailingBatchServer()
                ):
            self.assertTrue(self.controller.apply_bulk())
            QGuiApplication.processEvents()

        self.assertEqual(self.controller.advancedCheckedCount, 1)
        self.assertFalse(self.controller.bulkBusy)
        record = self.controller.advanced_model.get(0)
        self.assertTrue(record["checked"])
        self.assertEqual(record["error"], "Batch update failed")

    def test_quick_view_supports_cards_and_compact_rows(self):
        self.assertEqual(self.controller.quickViewMode, "cards")
        self.controller.set_quick_view_mode("compact")
        self.assertEqual(self.controller.quickViewMode, "compact")
        self.controller.set_quick_view_mode("unknown")
        self.assertEqual(self.controller.quickViewMode, "compact")

    def test_missing_task_can_hold_status_and_user_before_creation(self):
        self.controller.set_process_draft(1, "status", "Ready")
        self.controller.set_process_draft(1, "assigned", "artist")
        record = self.controller.process_model.get(1)
        self.assertEqual(self.controller.dirtyProcessCount, 1)
        self.assertTrue(record["dirty"])
        self.assertEqual(record["status"], "Ready")
        self.assertEqual(record["statusColor"], "#a67cdb")
        self.assertEqual(record["assigned"], "artist")
        self.controller.discard_all_process_changes()
        self.assertEqual(self.controller.dirtyProcessCount, 0)
        self.assertFalse(self.controller.process_model.get(1)["dirty"])

    def test_quick_task_creation_saves_process_workflow_defaults(self):
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc

        target = self.application.workspace_state._selected_sobject
        target.get_project = lambda: Mock(get_code=lambda: "test")
        self.controller.set_process_draft(1, "status", "Ready")

        def add_task(operation, *args, **kwargs):
            return ImmediateWorker(lambda: operation(*args, **kwargs))

        with patch.object(
                env_inst.server_pool, "add_task",
                side_effect=add_task), \
                patch.object(tc, "insert_sobjects", return_value={}) as insert:
            self.assertTrue(self.controller.save_process_changes(1))
            QGuiApplication.processEvents()

        values = insert.call_args.args[2]
        self.assertEqual(values["process"], "publish")
        self.assertEqual(values["pipeline_code"], "publish_pipe")
        self.assertEqual(float(values["bid_duration"]), 8.0)
        self.assertEqual(
            parse_datetime(values["bid_end_date"])
            - parse_datetime(values["bid_start_date"]),
            timedelta(days=1),
        )

    def test_quick_process_prefers_task_assigned_to_current_user(self):
        self.application.workspace_state._task_sobjects = [
            FakeTask(code="TASK_ARTIST", assigned="artist"),
            FakeTask(code="TASK_REVIEWER", assigned="reviewer"),
        ]

        with patch.object(
                TasksController, "_current_login", return_value="reviewer"):
            self.controller._rebuild_process_model()

        record = self.controller.process_model.get(0)
        self.assertEqual(record["currentTaskCode"], "TASK_REVIEWER")
        self.assertEqual(record["assigned"], "reviewer")

    def test_add_and_edit_use_schema_driven_task_editor(self):
        from thlib.environment import env_inst
        task_stype = object()
        with patch.object(
            env_inst, "get_stype_by_code", return_value=task_stype
        ):
            self.controller.begin_create_for_process(1)
            request = self.application._sobject_editor_request
            self.assertEqual(request["mode"], "insert")
            self.assertEqual(request["stype"], task_stype)
            self.assertEqual(request["info_dict"]["process"], "publish")
            self.assertEqual(request["info_dict"]["context"], "publish")
            self.assertEqual(request["info_dict"]["bid_duration"], 8.0)
            self.assertEqual(
                request["info_dict"]["pipeline_code"], "publish_pipe"
            )
            self.assertIs(request["parent_sobject"], self.application.workspace_state._selected_sobject)

            self.controller.begin_edit_for_process(0)
            request = self.application._sobject_editor_request
            self.assertEqual(request["mode"], "edit")
            self.assertIs(request["sobject"], self.application.workspace_state._task_sobjects[0])

            self.controller.begin_edit(0)
            request = self.application._sobject_editor_request
            self.assertEqual(request["mode"], "edit")
            self.assertEqual(request["info_dict"], {"process": "model"})
            self.assertIs(
                request["sobject"],
                self.application.workspace_state._task_sobjects[0],
            )

    def test_full_editor_create_uses_schema_driven_sobject_editor(self):
        from thlib.environment import env_inst
        task_stype = object()
        with patch.object(
            env_inst, "get_stype_by_code", return_value=task_stype
        ):
            self.controller.begin_create()

        request = self.application._sobject_editor_request
        self.assertEqual(request["mode"], "insert")
        self.assertEqual(request["stype"], task_stype)
        self.assertEqual(request["info_dict"]["process"], "model")
        self.assertEqual(request["info_dict"]["context"], "model")
        self.assertEqual(request["info_dict"]["bid_duration"], 24.0)
        self.assertEqual(request["info_dict"]["pipeline_code"], "task_pipe")
        self.assertIs(
            request["parent_sobject"],
            self.application.workspace_state._selected_sobject,
        )
        self.assertEqual(self.application.window_model.opened, ["task_editor"])
        self.assertFalse(self.controller.editorVisible)

    def test_task_manager_adds_an_expanded_virtual_draft_without_a_window(self):
        created = []
        self.controller.taskDraftCreated.connect(created.append)

        self.assertTrue(self.controller.create_advanced_task_draft())

        self.assertEqual(self.application.window_model.opened, [])
        self.assertEqual(len(created), 1)
        code = created[0]
        record = next(
            item for item in self.controller.table_model._records
            if item["taskCode"] == code
        )
        self.assertTrue(record["isNew"])
        self.assertTrue(record["dirty"])
        self.assertEqual(record["process"], "model")
        self.assertEqual(record["taskPipeline"], "task_pipe")
        self.assertEqual(record["progress"], 10)
        self.assertEqual(record["plannedHours"], 24.0)
        self.assertEqual(record["hoursLabel"], "0.0 / 24.0 h")
        self.assertNotIn(
            "plannedHours", self.controller._advanced_drafts[code]
        )
        self.assertEqual(record["assigned"], "")
        self.assertEqual(record["assignedLabel"], "Not assigned")
        self.assertEqual(record["supervisor"], "")
        self.assertEqual(record["supervisorLabel"], "No supervisor")
        start = parse_datetime(record["start"])
        end = parse_datetime(record["end"])
        self.assertIsNotNone(start)
        self.assertEqual(end - start, timedelta(days=3))
        self.assertEqual(self.controller.advancedDirtyCount, 1)

        self.controller.discard_advanced_changes(code)
        self.assertFalse(any(
            item["taskCode"] == code
            for item in self.controller.table_model._records
        ))
        self.assertEqual(self.controller.advancedDirtyCount, 0)

    def test_changing_virtual_task_process_reapplies_process_defaults(self):
        self.assertTrue(self.controller.create_advanced_task_draft())
        code = next(iter(self.controller._advanced_inserts))

        self.controller.stage_advanced_process(code, "publish")

        record = next(
            item for item in self.controller.table_model._records
            if item["taskCode"] == code
        )
        self.assertEqual(record["process"], "publish")
        self.assertEqual(record["taskPipeline"], "publish_pipe")
        self.assertEqual(record["plannedHours"], 8.0)
        self.assertEqual(record["hoursLabel"], "0.0 / 8.0 h")
        self.assertEqual(
            parse_datetime(record["end"])
            - parse_datetime(record["start"]),
            timedelta(days=1),
        )

    def test_virtual_task_stays_first_when_edited_or_grouping_changes(self):
        self.assertTrue(self.controller.create_advanced_task_draft())
        code = next(iter(self.controller._advanced_inserts))

        for group_mode in ("process", "status", "user", "object", "none"):
            self.controller.set_group_mode(group_mode)
            self.assertEqual(
                self.controller.table_model._records[0]["taskCode"], code
            )

        self.controller.stage_advanced_value(code, "process", "publish")
        self.controller.stage_advanced_value(code, "status", "Ready")
        self.controller.stage_advanced_value(code, "assigned", "artist")

        self.assertEqual(
            self.controller.table_model._records[0]["taskCode"], code
        )
        self.assertFalse(
            self.controller.table_model._records[0]["groupCollapsed"]
        )

    def test_milestone_refresh_keeps_virtual_task_creation_open(self):
        self.controller.set_advanced_visible(True)
        self.controller.use_current_object()
        self.assertTrue(self.controller.create_advanced_task_draft())
        code = next(iter(self.controller._advanced_inserts))
        milestone_controller = Mock()
        milestone_controller.projectCode = "test"
        milestone_controller.ganttMarkers = [{
            "code": "MILESTONE0001",
            "label": "Delivery",
            "dueDate": "2026-08-31",
        }]
        self.controller._milestone_controller = milestone_controller

        self.controller._milestones_changed()

        record = next(
            item for item in self.controller.table_model._records
            if item["taskCode"] == code
        )
        self.assertTrue(record["isNew"])
        self.assertTrue(record["dirty"])
        self.assertIn(code, self.controller._advanced_inserts)
        self.assertEqual(
            record["milestoneChoices"][-1]["value"], "MILESTONE0001"
        )

    def test_virtual_task_is_inserted_only_when_workspace_changes_are_saved(self):
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc

        self.assertTrue(self.controller.create_advanced_task_draft())
        code = next(iter(self.controller._advanced_inserts))
        self.controller.stage_advanced_value(code, "description", "New task")
        inserted = FakeTask(code="TASK_NEW", description="New task")

        with patch.object(
                env_inst.server_pool, "add_task",
                side_effect=lambda operation: ImmediateWorker(operation)), \
                patch.object(
                    tc, "insert_sobjects", return_value=inserted.get_info()
                ) as insert:
            self.assertTrue(self.controller.save_advanced_changes())
            QGuiApplication.processEvents()

        self.assertEqual(insert.call_count, 1)
        self.assertEqual(insert.call_args.kwargs["parent_key"],
                         self.controller.targetSearchKey)
        inserted_values = insert.call_args.args[2]
        self.assertEqual(inserted_values["pipeline_code"], "task_pipe")
        self.assertEqual(float(inserted_values["bid_duration"]), 24.0)
        self.assertEqual(self.controller.advancedDirtyCount, 0)
        self.assertNotIn(code, self.controller._advanced_inserts)
        self.assertIn("TASK_NEW", self.controller._advanced_tasks)

    def test_notes_open_for_the_selected_process(self):
        activated = []
        self.controller.taskActivated.connect(
            lambda code, parent, process: activated.append(
                (code, parent, process)
            )
        )
        self.controller.open_notes(
            self.controller.targetSearchKey, "model", "TASK0001"
        )
        self.assertEqual(self.application._selected_detail_process, "model")
        self.assertEqual(self.application.dock_model.opened, ["notes"])
        self.assertEqual(activated, [(
            "TASK0001", self.controller.targetSearchKey, "model",
        )])

    def test_object_scope_uses_one_native_task_query(self):
        target = FakeTarget(tasks=[FakeTask()])

        with patch.object(
                target, "get_tasks_sobjects",
                wraps=target.get_tasks_sobjects) as query:
            result = TasksController._load_advanced_scope(
                "object", "", "test", target, target.get_search_key(), []
            )

        self.assertEqual(query.call_count, 1)
        self.assertEqual(len(result["tasks"]), 1)

    def test_multiple_scope_uses_one_batched_task_query(self):
        import thlib.tactic_classes as tc

        targets = [FakeTarget(code="ASSET0001"), FakeTarget(code="ASSET0002")]
        grouped = {
            "model": [
                FakeTask(code="TASK0001", search_code="ASSET0001"),
                FakeTask(code="TASK0002", search_code="ASSET0002"),
            ]
        }
        with patch.object(
                tc.SObject, "get_multiple_tasks_sobjects",
                return_value=grouped) as query:
            result = TasksController._load_advanced_scope(
                "multiple", "", "test", None, "", targets
            )

        self.assertEqual(query.call_count, 1)
        self.assertEqual(len(result["tasks"]), 2)

    def test_project_scope_uses_single_workspace_page_request(self):
        import thlib.tactic_classes as tc

        tasks = [
            FakeTask(
                code="TASK0001", search_type="prod/asset",
                search_code="ASSET0001",
            ),
            FakeTask(
                code="TASK0002", search_type="prod/asset",
                search_code="ASSET0002",
            ),
            FakeTask(
                code="TASK0003", search_type="prod/shot",
                search_code="SHOT0001",
            ),
        ]
        parents = {
            "prod/asset": [
                FakeTarget(code="ASSET0001"), FakeTarget(code="ASSET0002")
            ],
            "prod/shot": [FakeTarget(code="SHOT0001")],
        }
        flattened_parents = [
            item for values in parents.values() for item in values
        ]
        with patch.object(
                tc, "get_task_workspace_page",
                return_value={
                    "tasks": tasks, "parents": flattened_parents,
                    "total": len(tasks),
                }) as query:
            result = TasksController._load_advanced_scope(
                "project", "", "test", None, "", []
            )

        query.assert_called_once_with(
            [("project_code", "test")],
            ["bid_end_date", "timestamp desc"], "test",
            limit=500, offset=0,
        )
        self.assertEqual(len(result["tasks"]), 3)

    def test_user_scope_adds_assignee_filter_without_extra_task_query(self):
        import thlib.tactic_classes as tc

        with patch.object(
                tc, "get_task_workspace_page",
                return_value={"tasks": [], "parents": [], "total": 0},
        ) as query:
            result = TasksController._load_advanced_scope(
                "user", "artist", "test", None, "", []
            )

        query.assert_called_once_with(
            [("project_code", "test"), ("assigned", "artist")],
            ["bid_end_date", "timestamp desc"], "test",
            limit=500, offset=0,
        )
        self.assertEqual(result["tasks"], [])

    def test_search_type_scope_filters_tasks_in_current_project(self):
        import thlib.tactic_classes as tc

        server = Mock()
        server.build_search_type.return_value = "prod/asset?project=test"

        with patch.object(tc, "server_start", return_value=server), \
                patch.object(
                    tc, "get_task_workspace_page",
                    return_value={"tasks": [], "parents": [], "total": 0},
                ) as query:
            result = self.controller._load_advanced_scope(
                "search_type", "", "test", None, "prod/asset", []
            )

        query.assert_called_once_with([
            ("project_code", "test"),
            ("search_type", "prod/asset?project=test"),
        ], ["bid_end_date", "timestamp desc"], "test", limit=500, offset=0)
        server.build_search_type.assert_called_once_with(
            "prod/asset", "test"
        )
        self.assertEqual(result["tasks"], [])

    def test_search_type_scope_uses_selected_sobject_type_and_label(self):
        with patch.object(self.controller, "refresh_advanced") as refresh:
            self.controller.use_current_search_type()

        self.assertEqual(self.controller.advancedScope, "search_type")
        self.assertEqual(self.controller.searchTypeScopeName, "Asset")
        self.assertEqual(self.controller.searchTypeScopeLabel, "All Asset")
        self.assertEqual(self.controller._advanced_target_key, "prod/asset")
        refresh.assert_called_once_with()

    def test_team_scope_uses_all_available_login_groups(self):
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc

        team = FakeLoginGroup("TEAM_A", "Team A", ["artist", "lead"])
        other_team = FakeLoginGroup(
            "TEAM_B", "Team B", ["supervisor", "reviewer"]
        )
        current = FakeCurrentLogin([team], [team, other_team])
        with patch.object(
                env_inst, "get_current_login_object", return_value=current), \
                patch.object(
                    tc, "get_task_workspace_page",
                    return_value={"tasks": [], "parents": [], "total": 0},
                ) as query:
            self.assertEqual(self.controller.teamOptions, [
                {"label": "Team A", "value": "TEAM_A", "members": 2},
                {"label": "Team B", "value": "TEAM_B", "members": 2},
            ])
            result = self.controller._load_advanced_scope(
                "team", "TEAM_B", "test", None, "", []
            )

        query.assert_called_once_with([
            ("project_code", "test"),
            ("assigned", "in", "reviewer|supervisor"),
        ], ["bid_end_date", "timestamp desc"], "test", limit=500, offset=0)
        self.assertEqual(result["tasks"], [])

    def test_unavailable_team_scope_is_rejected_before_query(self):
        from thlib.environment import env_inst

        with patch.object(
                env_inst, "get_current_login_object",
                return_value=FakeCurrentLogin([])), patch.object(
                    self.controller, "refresh_advanced") as refresh:
            self.controller.open_for_team("UNKNOWN")

        refresh.assert_not_called()
        self.assertIn("not available", self.controller.advancedError)
        self.assertNotIn("tasks_workspace", self.application.window_model.opened)

    def test_workspace_summary_and_presets_use_loaded_records_only(self):
        today = date.today()
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(
                code="TASK0001", assigned="", status="Waiting for Review",
                bid_end_date=(today - timedelta(days=1)).isoformat(),
                timestamp=today.isoformat(),
            ),
            FakeTask(
                code="TASK0002", assigned="artist", status="In Progress",
                bid_end_date=today.isoformat(),
                timestamp=(today - timedelta(days=30)).isoformat(),
            ),
        ]
        self.controller.use_current_object()
        self.controller.task_store.has_more = True
        self.controller.task_store.total_count = 5

        summary = self.controller.workspaceSummary
        self.assertEqual(summary["loaded"], 2)
        self.assertEqual(summary["total"], 5)
        self.assertFalse(summary["complete"])
        self.assertEqual(summary["unassigned"], 1)
        self.assertEqual(summary["overdue"], 1)
        self.assertEqual(summary["today"], 1)
        self.assertEqual(summary["review"], 1)
        self.assertEqual(summary["recent"], 1)

        self.controller.apply_workspace_preset("review")
        self.assertEqual(self.controller.advanced_model.count(), 1)
        self.assertEqual(
            self.controller.advanced_model.get(0)["taskCode"], "TASK0001"
        )

    def test_gantt_view_reuses_filtered_store_without_server_request(self):
        from thlib.environment import env_inst

        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(
                code="TASK0001", bid_start_date="2026-08-04",
                bid_end_date="2026-08-06", progress=50,
            ),
            FakeTask(
                code="TASK0002", bid_start_date="",
                bid_end_date="2026-08-07",
            ),
        ]
        self.controller.use_current_object()

        with patch.object(env_inst.server_pool, "add_task") as add_task:
            self.controller.set_view_mode("gantt")

        add_task.assert_not_called()
        self.assertEqual(self.controller.viewMode, "gantt")
        self.assertEqual(self.controller.gantt_model.count(), 2)
        self.assertEqual(self.controller.ganttScheduledCount, 1)
        self.assertEqual(self.controller.ganttUnscheduledCount, 1)
        self.assertEqual(
            self.controller.gantt_model.get(0)["ganttDurationDays"], 3
        )
        self.assertEqual(
            self.controller.gantt_model.get(1)["ganttIssue"],
            "Start is not set",
        )

    def test_gantt_activation_uses_common_task_selection_signal(self):
        self.controller.use_current_object()
        activated = []
        self.controller.taskActivated.connect(
            lambda code, parent, process: activated.append(
                (code, parent, process)
            )
        )

        self.controller.activate_advanced_task("TASK0001", 0)

        self.assertEqual(self.controller._selected_advanced_code, "TASK0001")
        self.assertEqual(activated, [(
            "TASK0001", self.controller.targetSearchKey, "model",
        )])

    def test_calendar_navigation_reuses_loaded_tasks(self):
        from thlib.environment import env_inst

        self.controller.use_current_object()
        initial_count = self.controller.calendar_model.count()

        with patch.object(env_inst.server_pool, "add_task") as add_task:
            self.controller.change_calendar_month(1)
            self.controller.change_calendar_month(-1)

        add_task.assert_not_called()
        self.assertEqual(initial_count, 42)
        self.assertEqual(self.controller.calendar_model.count(), 42)

    def test_calendar_task_uses_common_selection_and_opens_notes(self):
        self.controller.use_current_object()
        activated = []
        self.controller.taskActivated.connect(
            lambda code, parent, process: activated.append(
                (code, parent, process)
            )
        )

        self.controller.activate_calendar_task(
            "TASK0001", self.controller.targetSearchKey, "model"
        )

        self.assertEqual(self.controller._selected_advanced_code, "TASK0001")
        self.assertEqual(activated[0][0], "TASK0001")
        self.assertEqual(self.application.dock_model.opened, ["notes"])

    def test_open_calendar_uses_current_scope_and_shows_dock(self):
        self.controller.open_calendar()

        self.assertEqual(self.controller.calendar_model.count(), 42)
        self.assertEqual(
            self.application.dock_model.opened, ["task_calendar"]
        )

    def test_opening_loaded_user_scope_does_not_query_again(self):
        self.controller.task_store.set_scope("user", user="artist")
        self.controller._advanced_raw = [{
            "taskCode": "TASK0001", "searchKey": "task-key",
            "assigned": "artist",
        }]

        with patch.object(self.controller, "refresh_advanced") as refresh:
            self.controller.open_for_user("artist")

        refresh.assert_not_called()
        self.assertEqual(
            self.application.dock_model.opened, ["tasks"]
        )

    def test_user_profile_task_projection_uses_workspace_records(self):
        class WorkspaceTasks:
            advancedScope = "user"
            advancedUser = "artist"
            advancedBusy = False
            advancedTotalCount = 1
            advancedLoadedCount = 1

            @staticmethod
            def _quick_filter_source():
                return [{
                    "searchKey": "task-key", "parentTitle": "Robot",
                    "processLabel": "Model", "status": "In Progress",
                    "statusColor": "#3f8dd8", "processColor": "#b05fd3",
                    "description": "Blocking pass", "start": "2026-08-01",
                    "end": "2026-08-10", "progress": 40,
                    "dueState": "overdue", "plannedHours": 24,
                    "loggedHours": 12, "approvedHours": 8,
                    "pendingHours": 4,
                    "project": "test",
                }]

        user = UserController.__new__(UserController)
        QObject.__init__(user)
        user._selected_login = "artist"
        user._tasks_controller = WorkspaceTasks()
        user.tasks = RecordListModel((
            "searchKey", "title", "process", "status", "description",
            "start", "end", "progress", "project",
        ))

        user._task_workspace_changed()

        self.assertEqual(user.tasks.count(), 1)
        self.assertEqual(user.tasks.get(0)["title"], "Robot")
        self.assertEqual(user.tasks.get(0)["process"], "Model")
        self.assertEqual(user.taskSummary["active"], 1)
        self.assertEqual(user.taskSummary["overdue"], 1)
        self.assertEqual(user.taskSummary["plannedHours"], 24.0)
        self.assertEqual(user.taskSummary["loggedHours"], 12.0)
        self.assertEqual(user.taskSummary["workloadPercent"], 50)
        self.assertEqual(user.taskStatusSummary, [{
            "label": "In Progress", "color": "#3f8dd8", "count": 1,
        }])
        self.assertEqual(user.taskProcessSummary, [{
            "label": "Model", "color": "#b05fd3", "count": 1,
        }])

    def test_one_live_task_update_does_not_reset_the_model(self):
        self.controller.open_workspace()
        before = self.controller.performanceMetrics
        changed = FakeTask(
            code="TASK0001", status="Pending",
            timestamp="2026-08-09 10:00:00",
        )

        self.controller._live_request_id = "request"
        self.controller._live_tasks_ready("request", [changed])

        record = self.controller.advanced_model.get(0)
        metrics = self.controller.performanceMetrics
        self.assertEqual(record["status"], "Pending")
        self.assertEqual(metrics["modelResets"], before["modelResets"])
        self.assertGreater(metrics["modelDataChanges"], before["modelDataChanges"])

    def test_live_note_event_updates_only_the_matching_process_count(self):
        self.controller.open_workspace()
        self.controller.set_advanced_visible(True)

        self.controller.apply_server_batch({
            "initialActivity": False,
            "activity": [{
                "__kind__": "note", "code": "NOTE0001",
                "search_type": "prod/asset", "search_code": "ASSET0001",
                "process": "model",
            }],
        })

        self.assertEqual(self.controller.advanced_model.get(0)["notes"], 4)
        self.controller.update_note_count(
            self.controller.targetSearchKey, "model", 3, ["NOTE0001"]
        )
        self.assertEqual(self.controller.advanced_model.get(0)["notes"], 3)

    def test_dirty_live_task_update_requires_explicit_resolution(self):
        self.controller.open_workspace()
        self.controller.stage_advanced_value("TASK0001", "status", "Pending")
        changed = FakeTask(
            code="TASK0001", status="Ready",
            timestamp="2026-08-09 10:00:00",
        )

        self.controller._live_request_id = "request"
        self.controller._live_tasks_ready("request", [changed])

        record = self.controller.advanced_model.get(0)
        self.assertTrue(record["conflict"])
        self.assertFalse(self.controller.save_advanced_changes())
        self.controller.resolve_advanced_conflict("TASK0001", "server")
        record = self.controller.advanced_model.get(0)
        self.assertFalse(record["conflict"])
        self.assertFalse(record["dirty"])
        self.assertEqual(record["status"], "Ready")

    def test_hiding_workspace_stops_task_owned_live_work(self):
        live_worker = Mock()
        load_worker = Mock()
        visibility = []
        self.controller.advancedVisibilityChanged.connect(visibility.append)
        self.controller.set_advanced_visible(True)
        self.controller._live_worker = live_worker
        self.controller._advanced_worker = load_worker
        self.controller._live_timer.start()

        self.controller.set_advanced_visible(False)

        live_worker.cancel.assert_called_once_with()
        load_worker.cancel.assert_called_once_with()
        self.assertFalse(self.controller._live_timer.isActive())
        self.assertFalse(self.controller.advancedBusy)
        self.assertEqual(visibility, [True, False])

    def test_failed_refresh_keeps_previously_loaded_rows(self):
        self.controller.open_workspace()
        request_id = self.controller.task_store.begin_load()

        self.controller._advanced_failed(
            request_id, RuntimeError("Server is unavailable")
        )

        self.assertEqual(self.controller.advanced_model.count(), 1)
        self.assertEqual(self.controller.advancedLoadedCount, 1)
        self.assertFalse(self.controller.advancedBusy)
        self.assertIn("Server is unavailable", self.controller.advancedError)

    def test_cancel_advanced_load_invalidates_worker_result(self):
        request_id = self.controller.task_store.begin_load()
        worker = Mock()
        self.controller._advanced_worker = worker

        self.controller.cancel_advanced_load()

        worker.cancel.assert_called_once_with()
        self.assertFalse(self.controller.advancedBusy)
        self.assertNotEqual(self.controller._advanced_request_id, request_id)
        self.assertIsNone(self.controller._advanced_worker)


class TasksQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_quick_task_components_compile(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        for name in (
            "controls/Md3ComboBox.qml", "Md3SegmentedButton.qml",
            "Md3FilledActionButton.qml",
            "ItemCountActionButton.qml", "StatusChip.qml",
            "PreviewNavigationButton.qml", "QuickFilterChip.qml",
            "Md3DateField.qml",
            "Md3UserComboBox.qml",
            "ContentLoadingOverlay.qml", "RefreshIconButton.qml",
            "TaskProcessPanel.qml",
            "TaskHiddenDetails.qml",
            "TaskBrowserTable.qml", "TaskGanttView.qml",
            "TaskCalendarView.qml", "TaskWorkspaceModeSwitcher.qml",
            "TaskInspector.qml", "TaskBulkBar.qml",
            "TasksWorkspaceView.qml", "TaskDockView.qml",
            "AssetsBrowserView.qml", "ActivityFeedView.qml",
            "ColumnsEditorView.qml", "NamingEditorView.qml",
            "MessagesView.qml", "ScriptEditorView.qml",
            "UpdateView.qml", "UserProfileView.qml",
            "TimesheetView.qml", "WorkReportsView.qml",
            "SnapshotBrowser.qml", "DockHost.qml",
            "AdvancedSearchView.qml", "DebugLogView.qml",
            "CommitQueueView.qml", "TacticSearchField.qml",
            "WorkspaceCard.qml", "WorkspaceResultItem.qml",
            "FilePreparationEditor.qml", "MayaOptionsView.qml",
            "ProcessFilterEditorView.qml", "SObjectFieldEditor.qml",
            "ConfigurationPage.qml",
            "MilestoneManagerView.qml",
        ):
            component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(qml_dir / name))
            )
            self.assertNotEqual(
                component.status(), QQmlComponent.Status.Error,
                "\n".join(error.toString() for error in component.errors()),
            )

    def test_shared_date_field_creates(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Md3DateField.qml"))
        )
        field = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            field,
            "\n".join(error.toString() for error in component.errors()),
        )
        self.assertEqual(field.property("implicitHeight"), 36.0)

    def test_filled_action_button_clips_localized_text_to_its_width(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                qml_dir / "controls" / "Md3FilledActionButton.qml"
            )),
        )
        button = component.createWithInitialProperties({
            "theme": theme,
            "iconName": "add",
            "text": "A deliberately long localized action",
        })
        self.assertIsNotNone(
            button,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.setWidth(180)
        window.setHeight(80)
        button.setParentItem(window.contentItem())
        button.setProperty("width", 108)
        button.setProperty("height", 40)
        window.show()
        QTest.qWait(20)
        content = button.findChild(QObject, "md3FilledActionContent")
        label = button.findChild(QObject, "md3FilledActionLabel")
        self.assertIsNotNone(content)
        self.assertIsNotNone(label)
        self.assertLessEqual(content.property("width"), 78.0)
        self.assertTrue(label.property("truncated"))
        button.setProperty("text", "")
        QTest.qWait(20)
        icon = button.findChild(QObject, "md3FilledActionIcon")
        self.assertIsNotNone(icon)
        self.assertEqual(content.property("width"), 18.0)
        self.assertAlmostEqual(
            icon.property("x"),
            (content.property("width") - icon.property("width")) / 2,
        )
        window.close()
        window.deleteLater()
        button.deleteLater()
        theme.deleteLater()

    def test_filled_action_button_natural_width_does_not_clip_label(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                qml_dir / "controls" / "Md3FilledActionButton.qml"
            )),
        )
        button = component.createWithInitialProperties({
            "theme": theme,
            "iconName": "add",
            "text": "Create",
        })
        self.assertIsNotNone(
            button,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.setWidth(180)
        window.setHeight(80)
        button.setParentItem(window.contentItem())
        button.setProperty("width", button.property("implicitWidth"))
        button.setProperty("height", 40)
        window.show()
        QTest.qWait(20)
        label = button.findChild(QObject, "md3FilledActionLabel")
        self.assertIsNotNone(label)
        self.assertFalse(label.property("truncated"))
        window.close()
        window.deleteLater()
        button.deleteLater()
        theme.deleteLater()

    def test_shared_editable_controls_use_text_input_cursor(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        cases = (
            ("Md3TextField.qml", "md3TextFieldCursorArea", {}),
            ("Md3TextArea.qml", "md3TextAreaCursorArea", {}),
            ("Md3SpinBox.qml", "md3SpinBoxCursorHandler", {}),
            ("Md3ComboBox.qml", "md3ComboBoxCursorHandler", {
                "editable": True,
            }),
        )
        for file_name, cursor_name, properties in cases:
            component = QQmlComponent(
                engine,
                QUrl.fromLocalFile(str(
                    qml_dir / "controls" / file_name
                )),
            )
            initial = {"theme": theme}
            initial.update(properties)
            control = component.createWithInitialProperties(initial)
            self.assertIsNotNone(
                control,
                "\n".join(error.toString() for error in component.errors()),
            )
            cursor_target = control.findChild(QObject, cursor_name)
            self.assertIsNotNone(cursor_target, file_name)
            self.assertEqual(
                cursor_target.property("cursorShape"), Qt.IBeamCursor,
                file_name,
            )
            control.deleteLater()
        theme.deleteLater()

    def test_shared_clickable_controls_use_pointing_hand_cursor(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        cases = (
            ("Md3Button.qml", "md3ButtonCursorHandler"),
            ("Md3CheckBox.qml", "md3CheckBoxCursorHandler"),
            ("Md3Switch.qml", "md3SwitchCursorHandler"),
            ("Md3TabButton.qml", "md3TabButtonCursorHandler"),
            ("Md3Slider.qml", "md3SliderCursorHandler"),
            ("Md3ComboBox.qml", "md3ComboBoxCursorHandler"),
            ("CompactIconButton.qml", "compactIconButtonCursorArea"),
            ("ItemCountActionButton.qml", "itemCountActionCursorArea"),
            ("PreviewNavigationButton.qml", "previewNavigationCursorArea"),
            ("Md3FilledActionButton.qml", "md3FilledActionCursorArea"),
        )
        for file_name, cursor_name in cases:
            component = QQmlComponent(
                engine,
                QUrl.fromLocalFile(str(
                    qml_dir / "controls" / file_name
                )),
            )
            control = component.createWithInitialProperties({"theme": theme})
            self.assertIsNotNone(
                control,
                "\n".join(error.toString() for error in component.errors()),
            )
            cursor_target = control.findChild(QObject, cursor_name)
            self.assertIsNotNone(cursor_target, file_name)
            self.assertEqual(
                cursor_target.property("cursorShape"),
                Qt.PointingHandCursor,
                file_name,
            )
            control.deleteLater()
        theme.deleteLater()

    def test_expanded_task_editor_exposes_optional_task_fields(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ))
        engine.rootContext().setContextProperty("userListModel", users)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        controller = TasksController(FakeApplication())
        controller._advanced_raw = [{
            "taskCode": "TASK00001", "plannedHours": 12.5,
        }]
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "TaskHiddenDetails.qml")),
        )
        editor = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "taskCode": "TASK00001",
            "parentKey": "skey://demo/asset?code=ASSET00001",
            "process": "publish",
            "processChoices": [],
            "isNew": False,
            "status": "",
            "statusChoices": [],
            "assigned": "",
            "assignedLabel": "Not assigned",
            "assignedAvatar": "",
            "userChoices": [],
            "supervisor": "",
            "supervisorLabel": "No supervisor",
            "supervisorChoices": [],
            "priority": "3",
            "priorityLabel": "Important",
            "priorityChoices": [
                {"value": "", "label": "No priority"},
                {"value": "3", "label": "Important"},
            ],
            "milestoneCode": "",
            "milestoneLabel": "No milestone",
            "milestoneChoices": [],
            "start": "",
            "end": "",
            "progress": 0,
            "description": "",
            "plannedHours": 12.5,
            "processColor": "#42a5f5",
            "notes": 0,
            "showPriority": True,
            "showMilestone": True,
            "showSupervisor": True,
        })
        self.assertIsNotNone(
            editor,
            "\n".join(error.toString() for error in component.errors()),
        )
        priority_editor = editor.findChild(QObject, "taskPriorityEditor")
        milestone_editor = editor.findChild(QObject, "taskMilestoneEditor")
        supervisor_editor = editor.findChild(QObject, "taskSupervisorEditor")
        expected_hours_editor = editor.findChild(
            QObject, "taskExpectedHoursEditor"
        )
        details_background = editor.findChild(
            QObject, "taskDetailsBackground"
        )
        self.assertIsNotNone(priority_editor)
        self.assertIsNotNone(milestone_editor)
        self.assertIsNotNone(supervisor_editor)
        self.assertIsNotNone(expected_hours_editor)
        expected_hours_input = expected_hours_editor.findChild(
            QObject, "md3SpinBoxTextInput"
        )
        self.assertIsNotNone(expected_hours_input)
        self.assertIsNotNone(details_background)
        self.assertEqual(
            details_background.property("color"),
            theme.property("panelDeep"),
        )
        self.assertEqual(expected_hours_editor.property("realValue"), 12.5)
        self.assertIn(
            expected_hours_editor.property("displayText"), {"12.5", "12,5"}
        )
        self.assertIn(expected_hours_input.property("text"), {"12.5", "12,5"})
        self.assertNotIn("TASK00001", controller._advanced_drafts)
        editor.setProperty("plannedHours", 24.0)
        QGuiApplication.processEvents()
        self.assertEqual(expected_hours_editor.property("realValue"), 24.0)
        self.assertEqual(expected_hours_input.property("text"), "24")
        self.assertNotIn("TASK00001", controller._advanced_drafts)
        self.assertEqual(priority_editor.property("count"), 2)
        self.assertEqual(priority_editor.property("displayText"), "Important")
        self.assertFalse(priority_editor.property("actionField"))
        self.assertTrue(priority_editor.property("showIndicator"))
        window = QQuickWindow()
        window.setWidth(1400)
        window.setHeight(600)
        editor.setParentItem(window.contentItem())
        editor.setProperty("height", 500)
        editor.setProperty("width", 1400)
        window.show()
        QGuiApplication.processEvents()
        self.assertEqual(editor.property("detailColumnCount"), 5)
        self.assertGreater(editor.property("detailCellWidth"), 250)
        self.assertGreater(priority_editor.property("width"), 250)
        editor.setProperty("width", 900)
        QTest.qWait(20)
        self.assertEqual(editor.property("detailColumnCount"), 3)
        self.assertGreater(priority_editor.property("width"), 270)
        editor.setProperty("width", 600)
        QTest.qWait(20)
        self.assertEqual(editor.property("detailColumnCount"), 2)
        self.assertGreater(priority_editor.property("width"), 270)
        description_editor = editor.findChild(
            QObject, "taskDescriptionEditor"
        )
        description_button = editor.findChild(
            QObject, "taskDescriptionEditButton"
        )
        details_background = editor.findChild(
            QObject, "taskDetailsBackground"
        )
        self.assertIsNotNone(details_background)
        self.assertTrue(description_editor.property("readOnly"))
        self.assertTrue(description_button.property("visible"))
        editor.setProperty("isNew", True)
        QGuiApplication.processEvents()
        self.assertEqual(
            details_background.property("color"),
            theme.property("panelDeep"),
        )
        self.assertFalse(description_editor.property("readOnly"))
        self.assertFalse(description_button.property("visible"))
        window.close()
        window.deleteLater()
        editor.deleteLater()
        theme.deleteLater()

    def test_table_delegate_receives_priority_choices_from_record_model(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        application = FakeApplication()
        controller = TasksController(application)
        controller._task_field_catalogs["test"] = {
            "priorityChoices": [
                {"value": "", "label": "No priority", "color": ""},
                {"value": "3", "label": "Important", "color": ""},
            ],
        }
        controller._advanced_raw = controller._task_records(
            application.workspace_state._task_sobjects
        )
        controller._rebuild_advanced_models()
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ))
        engine.rootContext().setContextProperty(
            "tasksController", controller
        )
        engine.rootContext().setContextProperty(
            "advancedTaskTableModel", controller.table_model
        )
        engine.rootContext().setContextProperty("userListModel", users)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine)
        component.setData(b"""
            import QtQuick
            Item {
                id: root
                required property var theme
                property var firstDelegate: null
                width: 400
                height: 200
                Repeater {
                    objectName: "priorityProbeList"
                    model: advancedTaskTableModel
                    onItemAdded: (index, item) => root.firstDelegate = item
                    delegate: Md3ComboBox {
                        objectName: "taskPriorityEditor"
                        required property string priority
                        required property string priorityLabel
                        required property var priorityChoices
                        width: 180
                        height: 36
                        theme: root.theme
                        model: priorityChoices
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: {
                            const source = priorityChoices || []
                            for (let index = 0; index < source.length; ++index) {
                                if (String(source[index].value || "")
                                        === String(priority || ""))
                                    return index
                            }
                            return -1
                        }
                        displayText: currentIndex >= 0
                            ? currentText : priorityLabel
                    }
                }
            }
        """, QUrl.fromLocalFile(str(qml_dir / "PriorityModelProbe.qml")))
        table = component.createWithInitialProperties({
            "theme": theme,
        })
        self.assertIsNotNone(
            table,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(1400, 720)
        table.setParentItem(window.contentItem())
        window.show()
        QGuiApplication.processEvents()
        QTest.qWait(50)
        probe_list = table.findChild(QObject, "priorityProbeList")
        self.assertIsNotNone(probe_list)
        self.assertEqual(probe_list.property("count"), 1)
        priority_editor = table.property("firstDelegate")
        self.assertIsNotNone(
            priority_editor,
            repr([
                (child.metaObject().className(), child.objectName())
                for child in table.findChildren(QObject)
                if child.objectName()
            ]),
        )
        self.assertEqual(priority_editor.property("count"), 2)
        self.assertEqual(priority_editor.property("displayText"), "No priority")
        window.close()
        window.deleteLater()
        table.deleteLater()
        theme.deleteLater()

    def test_task_workspace_creates_with_a_real_record(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        application = FakeApplication()
        controller = TasksController(application)
        controller.open_workspace()
        self.assertEqual(controller.advancedDockTitle, "Tasks for: Robot")
        self.assertEqual(controller.advancedDockSubject, "Robot")
        self.assertEqual(controller.advancedProcessCount, 1)
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ))
        users.replace([{
            "login": "artist", "displayName": "Artist",
            "initials": "AR", "avatarUrl": "",
        }])
        engine.rootContext().setContextProperty(
            "tasksController", controller
        )
        engine.rootContext().setContextProperty(
            "advancedTaskModel", controller.advanced_model
        )
        engine.rootContext().setContextProperty(
            "advancedTaskTableModel", controller.table_model
        )
        engine.rootContext().setContextProperty("userListModel", users)

        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        self.assertIsNotNone(theme)
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "TasksWorkspaceView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme, "embedded": True,
        })
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        view.setProperty("width", 1400)
        view.setProperty("height", 720)
        QGuiApplication.processEvents()
        self.assertFalse(view.property("compactScopeControls"))
        toolbar = view.findChild(QObject, "taskWorkspaceToolbar")
        self.assertIsNotNone(toolbar)
        self.assertEqual(toolbar.property("radius"), 0.0)
        self.assertIsNone(view.findChild(QObject, "taskWorkspaceTargetLabel"))
        scope_switcher = view.findChild(QObject, "embeddedScopeSwitcher")
        self.assertIsNotNone(scope_switcher)
        self.assertTrue(scope_switcher.property("visible"))
        self.assertEqual(scope_switcher.property("currentValue"), "object")
        scope_model = scope_switcher.property("model").toVariant()
        self.assertEqual(
            [item["label"] for item in scope_model],
            ["Selected", "All Asset", "Project", "Teams", "My Tasks"],
        )
        quick_workspace_button = view.findChild(
            QObject, "taskQuickWorkspaceButton"
        )
        sort_combo = view.findChild(QObject, "taskSortModeCombo")
        group_combo = view.findChild(QObject, "taskGroupModeCombo")
        view_switcher = view.findChild(
            QObject, "taskWorkspaceTopViewSwitcher"
        )
        clear_filters_button = view.findChild(
            QObject, "taskWorkspaceClearFiltersButton"
        )
        refresh_button = view.findChild(
            QObject, "taskWorkspaceRefreshButton"
        )
        overflow_button = view.findChild(
            QObject, "taskWorkspaceOverflowButton"
        )
        self.assertIsNotNone(quick_workspace_button)
        self.assertIsNotNone(sort_combo)
        self.assertIsNotNone(group_combo)
        self.assertIsNone(view_switcher)
        self.assertIsNotNone(clear_filters_button)
        self.assertIsNotNone(refresh_button)
        self.assertIsNotNone(overflow_button)
        self.assertTrue(quick_workspace_button.property("visible"))
        self.assertTrue(sort_combo.property("visible"))
        self.assertTrue(group_combo.property("visible"))
        self.assertTrue(clear_filters_button.property("visible"))
        self.assertTrue(refresh_button.property("visible"))
        self.assertFalse(overflow_button.property("visible"))
        search_field = view.findChild(QObject, "taskWorkspaceSearchField")
        quick_filter = view.findChild(
            QObject, "taskWorkspaceQuickFilterButton"
        )
        create_task_button = view.findChild(
            QObject, "taskWorkspaceCreateButton"
        )
        self.assertIsNotNone(search_field)
        self.assertIsNotNone(quick_filter)
        self.assertIsNotNone(create_task_button)
        self.assertTrue(create_task_button.property("visible"))
        self.assertTrue(create_task_button.property("enabled"))
        self.assertEqual(
            create_task_button.property("cornerRadius"),
            theme.property("itemRadius"),
        )
        view.setProperty("width", 1250)
        QGuiApplication.processEvents()
        self.assertTrue(sort_combo.property("visible"))
        self.assertTrue(group_combo.property("visible"))
        self.assertTrue(clear_filters_button.property("visible"))
        self.assertFalse(overflow_button.property("visible"))
        view.setProperty("width", 1180)
        QGuiApplication.processEvents()
        browser = view.findChild(QObject, "taskBrowserTable")
        self.assertIsNotNone(browser)
        self.assertIsNone(browser.property("useSideBySideTaskDetails"))
        self.assertTrue(browser.property("showDateColumn"))
        self.assertTrue(browser.property("showProgressColumn"))
        view.setProperty("width", 840)
        QGuiApplication.processEvents()
        self.assertTrue(view.property("compactScopeControls"))
        compact_scope = view.findChild(QObject, "embeddedScopeButton")
        self.assertIsNotNone(compact_scope)
        self.assertTrue(compact_scope.property("visible"))
        self.assertFalse(sort_combo.property("visible"))
        self.assertTrue(group_combo.property("visible"))
        self.assertTrue(clear_filters_button.property("visible"))
        self.assertTrue(refresh_button.property("visible"))
        self.assertTrue(overflow_button.property("visible"))
        self.assertTrue(browser.property("showDateColumn"))
        self.assertTrue(browser.property("showProgressColumn"))
        view.setProperty("width", 900)
        QGuiApplication.processEvents()
        workspace_mode_switcher = view.findChild(
            QObject, "taskWorkspaceModeSwitcher"
        )
        self.assertIsNotNone(workspace_mode_switcher)
        mode_switcher_x = workspace_mode_switcher.property("x")
        controller.set_view_mode("gantt")
        view.setProperty("width", 720)
        QGuiApplication.processEvents()
        self.assertEqual(controller.viewMode, "gantt")
        self.assertEqual(controller.gantt_model.count(), 1)
        gantt_wheel_area = view.findChild(
            QObject, "ganttTimelineWheelArea"
        )
        gantt_daily_grid = view.findChild(QObject, "ganttDailyGrid")
        self.assertIsNotNone(gantt_wheel_area)
        self.assertIsNotNone(gantt_daily_grid)
        view.setProperty("width", 900)
        QGuiApplication.processEvents()
        self.assertEqual(
            workspace_mode_switcher.property("x"), mode_switcher_x
        )
        view.setProperty("width", 720)
        QGuiApplication.processEvents()
        self.assertTrue(gantt_wheel_area.property("visible"))
        self.assertTrue(view.property("compactScopeControls"))
        self.assertFalse(scope_switcher.property("visible"))
        self.assertFalse(sort_combo.property("visible"))
        self.assertTrue(group_combo.property("visible"))
        self.assertTrue(clear_filters_button.property("visible"))
        self.assertTrue(refresh_button.property("visible"))
        self.assertTrue(overflow_button.property("visible"))
        self.assertFalse(view.property("minimalToolbar"))
        view.setProperty("width", 320)
        QGuiApplication.processEvents()
        self.assertTrue(view.property("minimalToolbar"))
        self.assertFalse(group_combo.property("visible"))
        self.assertTrue(clear_filters_button.property("visible"))
        self.assertTrue(refresh_button.property("visible"))
        controller.set_view_mode("list")
        view.setProperty("width", 1400)
        QGuiApplication.processEvents()
        self.assertTrue(controller.create_advanced_task_draft())
        QGuiApplication.processEvents()
        draft_code = next(iter(controller._advanced_inserts))
        expanded = browser.property("expandedTaskDetails").toVariant()
        self.assertTrue(expanded[draft_code])
        expanded_object_x = browser.property("expandedObjectLeft")
        view.setProperty("width", 900)
        QGuiApplication.processEvents()
        self.assertEqual(
            browser.property("expandedObjectLeft"), expanded_object_x
        )
        view.setProperty("width", 1400)
        QGuiApplication.processEvents()
        self.assertEqual(
            browser.property("expandedObjectLeft"), expanded_object_x
        )
        controller.discard_advanced_changes(draft_code)
        view.deleteLater()
        theme.deleteLater()

    def test_task_calendar_creates_at_minimum_dock_size(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        engine.addImportPath(str(qml_dir))
        controller = TasksController(FakeApplication())
        controller.use_current_object()
        engine.rootContext().setContextProperty(
            "tasksController", controller
        )
        engine.rootContext().setContextProperty(
            "taskCalendarModel", controller.calendar_model
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "TaskCalendarView.qml")),
        )
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        view.setProperty("width", 380)
        view.setProperty("height", 360)
        QGuiApplication.processEvents()
        self.assertEqual(controller.calendar_model.count(), 42)
        view.deleteLater()
        theme.deleteLater()


if __name__ == "__main__":
    unittest.main()
