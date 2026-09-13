import unittest
import os
import json
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import (
    Q_ARG, QMetaObject, QPoint, QPointF, QObject, Property, Qt, QUrl, Signal,
    Slot,
)
from PySide6.QtGui import QColor, QGuiApplication, QTextFormat
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from thlib.ui.tasks import TasksController
from thlib.ui.task_data import parse_datetime
from thlib.ui.work_hours import WorkHoursController
from thlib.ui.script_editor import ScriptEditorController
from thlib.ui.sobject_delete import SObjectDeleteController
from thlib.ui.configuration import ConfigurationController
from thlib.ui.help import HelpController
from thlib.ui.localization import LocalizationController
from thlib.ui.user import UserController
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.docks import DockPanelModel
from thlib.ui.workspace_models.windows import FloatingWindowModel
from tests.support.async_scenarios import MemorySettings


class FakeRegistry:
    def __init__(self):
        self.actions = {}

    def register(self, name, callback):
        self.actions[name] = callback

    def invoke(self, name):
        callback = self.actions.get(name)
        if callback is None:
            return False
        callback()
        return True


class ScriptEditorDccBridge(QObject):
    stateChanged = Signal()
    commandFinished = Signal(str, bool, "QVariantMap", str)

    def __init__(self):
        super().__init__()
        self.selectedClient = "maya-2026"
        self.selectedClientLabel = "Maya 2026 · scene.mb · PID 42"
        self.error = ""
        self.commands = []

    @staticmethod
    def has_dcc_capability(action):
        return action == "execute_script_file"

    def send_active_command(self, action, payload, timeout):
        self.commands.append((action, dict(payload), timeout))
        return "qml-dcc-run"


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

    def schedule_file_object(
        self, file_object, process="", auto_start=False,
        is_ui_preview=False,
    ):
        self.scheduled.append((file_object, process, auto_start))
        return type("Handle", (), {"task_id": "preview-task"})()


class FakePreviewFile:
    def __init__(self, local_path):
        self.local_path = str(local_path)

    def get_filename_with_ext(self):
        return "task-preview.png"

    def get_full_abs_path(self):
        return self.local_path

    def is_local_current(self):
        return False

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
        self.delete_calls = []

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

    def delete_sobject(
            self, include_dependencies=False, list_dependencies=None,
            confirm=True):
        self.delete_calls.append({
            "include_dependencies": bool(include_dependencies),
            "list_dependencies": list_dependencies,
            "confirm": bool(confirm),
        })
        return {"deleted": self.values["code"]}


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


class FakeSObjectDeleteController(QObject):
    stateChanged = Signal()
    deletionFinished = Signal(str)

    def __init__(self):
        super().__init__()
        self.busy = False
        self.deleting = False
        self.requests = []
        self.parent_requests = []

    def begin(self, sources, context="items", parent_sources=None):
        self.requests.append((list(sources or []), str(context or "items")))
        self.parent_requests.append(dict(parent_sources or {}))
        return bool(sources)

    def finish(self, context="tasks"):
        self.deletionFinished.emit(context)


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
        self.sobject_delete = FakeSObjectDeleteController()
        self._sobject_editor_request = {}
        self._current_project_code = "test"
        self.debug_log = None
        self._settings = MemorySettings()
        self.opened_search_keys = []

    def _write_settings(self):
        pass

    def open_window(self, window_id):
        self.window_model.show_window(window_id)

    def open_search_key(self, search_key):
        self.opened_search_keys.append((search_key, ""))

    def open_search_key_in_process(self, search_key, process):
        self.opened_search_keys.append((search_key, process))


class _TaskInspectorController(QObject):
    stateChanged = Signal()

    def __init__(self):
        super().__init__()
        self.full_create_count = 0
        self._expanded = True
        self._task_choices = []
        self._task = {
            "code": "",
            "processRow": 1,
            "process": "publish",
            "context": "",
            "status": "Ready",
            "statusChoices": [{
                "label": "Ready", "value": "Ready", "color": "#25c2e8",
            }],
            "assigned": "artist",
            "assignedDisplay": "Artist",
            "userChoices": [{
                "label": "Artist", "value": "artist", "avatarUrl": "",
            }],
            "start": "",
            "end": "",
            "progress": 0,
            "progressInput": "0",
            "validationError": "",
            "dirty": False,
        }

    @Property("QVariantMap", notify=stateChanged)
    def currentTask(self):
        return dict(self._task)

    @Property("QVariantMap", notify=stateChanged)
    def selectedObject(self):
        return {
            "title": "Hero asset", "type": "Asset", "searchKey": "",
            "previewUrl": "",
        }

    @Property(bool, notify=stateChanged)
    def hasTarget(self):
        return True

    @Property(bool, notify=stateChanged)
    def busy(self):
        return False

    @Property(bool, notify=stateChanged)
    def taskExpanded(self):
        return self._expanded

    @Property(str, notify=stateChanged)
    def process(self):
        return "publish"

    @Property(str, notify=stateChanged)
    def processLabel(self):
        return "Publish"

    @Property("QVariantList", notify=stateChanged)
    def processChoices(self):
        return [{
            "label": "Publish", "value": "publish", "type": "manual",
            "color": "#25c2e8", "count": 0,
        }]

    @Property("QVariantList", notify=stateChanged)
    def taskChoices(self):
        return list(self._task_choices)

    def set_task_choices(self, choices):
        self._task_choices = list(choices)
        self.stateChanged.emit()

    def set_expanded(self, value):
        self._expanded = bool(value)
        self.stateChanged.emit()

    def set_task(self, **changes):
        self._task.update(changes)
        self.stateChanged.emit()

    @Slot()
    def create_task_for_process(self):
        self.full_create_count += 1

    @Slot()
    def toggle_task_expanded(self):
        self.set_expanded(not self._expanded)

    @Slot()
    def refresh(self):
        pass

    @Slot(str)
    def open_skey_preview(self, _search_key):
        pass

    @Slot(str)
    def set_process(self, _process):
        pass

    @Slot(str)
    def select_task(self, _task_code):
        pass


class _TaskInspectorTasksController(QObject):
    stateChanged = Signal()

    def __init__(self):
        super().__init__()
        self.saved_rows = []
        self.discarded_rows = []
        self.values = []

    @Property(bool, notify=stateChanged)
    def busy(self):
        return False

    @Property(bool, notify=stateChanged)
    def progressSupported(self):
        return True

    @Slot(int, str, "QVariant")
    def set_process_draft(self, row, field, value):
        self.values.append((row, field, value))

    @Slot(int, result=bool)
    def save_process_changes(self, row):
        self.saved_rows.append(row)
        return True

    @Slot(int)
    def discard_process_changes(self, row):
        self.discarded_rows.append(row)


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
        self.assertEqual(
            self.controller.task_inspector_process_record("publish")[
                "processRow"
            ],
            1,
        )

    def test_task_record_uses_native_parent_search_type_title(self):
        parent = FakeTarget()
        self.controller.task_store.set_parents([parent])

        record = self.controller._task_records([FakeTask()])[0]

        self.assertEqual(record["parentSearchType"], "prod/asset")
        self.assertEqual(record["parentSearchTypeLabel"], "Asset")

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

    def test_field_catalog_uses_resolved_parent_not_scope_key(self):
        import thlib.tactic_classes as tc
        from thlib.ui.task_workspace import TaskWorkspaceStore

        parent_key = "prod/asset?project=test&code=ASSET001"
        parent = tc.SObject({"__search_key__": parent_key})
        cases = (
            ("object", "skey://" + parent_key, parent, parent_key),
            ("search_type", "prod/asset", None, None),
            ("project", "", None, None),
            ("multiple", "", None, None),
            ("user", "", None, None),
            ("team", "", None, None),
        )
        for scope, target_key, target, expected_parent in cases:
            with self.subTest(scope=scope), patch.object(
                TaskWorkspaceStore, "load_scope",
                return_value={"tasks": [], "target": target},
            ), patch(
                "thlib.ui.task_workspace.store._resolve_target_from_search_key",
                return_value=target,
            ), patch.object(
                tc, "execute_procedure_serverside",
                return_value={"InputWidgets": []},
            ) as query:
                result = TasksController._load_advanced_scope(
                    scope, "", "test", None, target_key, [],
                    include_field_catalog=True,
                )

                query.assert_called_once()
                args = query.call_args.args[1]["args"]
                self.assertEqual(args["parent_key"], expected_parent)
                self.assertEqual(args["search_type"], "sthpw/task")
                self.assertEqual(query.call_args.kwargs["project"], "test")
                self.assertEqual(result["fieldCatalog"]["errors"], [])

    def test_field_catalog_retry_does_not_send_search_type_as_parent(self):
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        parent_key = "prod/asset?project=test&code=ASSET001"
        parent = tc.SObject({"__search_key__": parent_key})
        cases = (
            ("object", "skey://" + parent_key, parent, parent_key),
            ("search_type", "prod/asset", None, None),
            ("search_type", "prod/asset", parent, None),
        )
        for scope, target_key, target, expected_parent in cases:
            with self.subTest(scope=scope, target=target):
                controller = TasksController(self.application)
                controller.task_store.set_scope(
                    scope, target=target, target_key=target_key,
                )
                worker = Mock()
                with patch.object(
                    env_inst.server_pool, "add_task", return_value=worker,
                ) as add_task, patch.object(
                    env_inst.server_pool, "start",
                ), patch.object(
                    tc, "execute_procedure_serverside",
                    return_value={"InputWidgets": []},
                ) as query:
                    controller._ensure_task_field_catalog("test")
                    operation, *args = add_task.call_args.args
                    result = operation(*args, **add_task.call_args.kwargs)

                worker.start.assert_called_once()
                self.assertEqual(
                    query.call_args.args[1]["args"]["parent_key"],
                    expected_parent,
                )
                self.assertEqual(result["errors"], [])

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

    def test_task_badge_uses_native_parent_process_count_before_selection(self):
        task = FakeTask()
        task.get_notes_count = Mock(return_value={})
        task.set_notes_count = Mock()
        target = FakeTarget(tasks=[task])
        target.get_info = Mock(return_value={
            "code": "ASSET0001", "project_code": "test",
        })
        target.get_notes_count = Mock(return_value={"model": 7})
        self.application.workspace_state._selected_sobject = target
        self.application.workspace_state._task_sobjects = [task]

        self.controller._rebuild_process_model()
        self.controller.use_current_object()

        self.assertEqual(self.controller.advanced_model.get(0)["notes"], 7)
        self.assertEqual(self.controller.process_model.get(0)["notes"], 7)
        task.set_notes_count.assert_called_with("model", 7)

    def test_non_selected_task_scope_does_not_follow_sobject_selection(self):
        self.controller._advanced_visible = True
        for scope in ("search_type", "project", "user", "team"):
            with self.subTest(scope=scope):
                self.controller._advanced_scope = scope
                with patch.object(
                    self.controller, "use_current_search_type"
                ) as use_search_type, patch.object(
                    self.controller, "use_current_object"
                ) as use_object, patch.object(
                    self.controller, "_rebuild_process_model"
                ) as rebuild_process:
                    self.controller._selection_changed()

                use_search_type.assert_not_called()
                use_object.assert_not_called()
                rebuild_process.assert_called_once_with()

    def test_selected_task_scope_follows_sobject_selection(self):
        self.controller._advanced_visible = True
        self.controller._advanced_scope = "object"

        with patch.object(
            self.controller, "use_current_object"
        ) as use_object:
            self.controller._selection_changed()

        use_object.assert_called_once_with()

    def test_no_object_selection_is_a_normal_empty_state(self):
        workspace = self.application.workspace_state
        workspace._selected_sobject = None
        workspace._task_sobjects = []

        self.controller.set_advanced_visible(True)

        self.assertEqual(self.controller.advanced_model.count(), 0)
        self.assertEqual(self.controller.advancedVisibleCount, 0)
        self.assertEqual(self.controller.advancedError, "")
        self.assertEqual(
            self.controller.advancedEmptyMessage,
            "Select an sObject to view tasks",
        )
        with patch("thlib.environment.env_inst.server_pool.add_task") as add_task:
            self.controller.refresh_advanced()
        add_task.assert_not_called()

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

    def test_result_tasks_action_opens_selected_process_scope(self):
        model_task = FakeTask(
            code="TASK_MODEL", process="model", search_code="ASSET0002",
        )
        publish_task = FakeTask(
            code="TASK_PUBLISH", process="publish", search_code="ASSET0002",
        )
        target = FakeTarget(
            tasks=[model_task, publish_task], code="ASSET0002", title="Chair",
        )
        target_key = target.get_search_key()
        root_node = SimpleNamespace(
            node_id="asset-two", node_type="sobject", parent_id="",
            source=target, search_key=target_key, process="", context="",
        )
        process_node = SimpleNamespace(
            node_id="asset-two-publish", node_type="process",
            parent_id=root_node.node_id, source=None, search_key=target_key,
            process="publish", context="publish",
        )
        nodes = {
            root_node.node_id: root_node,
            process_node.node_id: process_node,
        }
        tab = SimpleNamespace(
            selected_node_id=process_node.node_id,
            selected_node_ids=[process_node.node_id],
        )
        self.application._current_tab = lambda: tab
        self.application.workspace_model = SimpleNamespace(
            node_for=lambda node_id: nodes.get(node_id)
        )

        with patch.object(
            self.controller, "refresh_advanced"
        ) as refresh_advanced:
            self.application._registry.invoke("show_selected_tasks_workspace")
        refresh_advanced.assert_called_once_with()
        self.controller.set_advanced_visible(True)

        self.assertEqual(self.controller.workspaceSurface, "browser")
        self.assertEqual(self.controller.advancedScope, "object")
        self.assertEqual(self.controller._advanced_target_key, target_key)
        self.assertEqual(self.controller._advanced_object_process, "publish")
        self.assertEqual(self.controller._pending_object_scope_key, target_key)
        self.assertEqual(self.application.dock_model.opened, ["tasks"])
        self.assertEqual(self.controller.advanced_model.count(), 0)

        self.application.workspace_state._selected_sobject = target
        self.application.workspace_state._task_sobjects = list(target.tasks)
        self.application.workspace_state.selection_changed.emit()

        self.assertEqual(self.controller._pending_object_scope_key, "")
        self.assertEqual(self.controller.advanced_model.count(), 1)
        self.assertEqual(
            self.controller.advanced_model.get(0)["taskCode"], "TASK_PUBLISH"
        )

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

    def test_task_user_avatar_schedules_web_before_icon_derivative(self):
        repository_sync = FakeRepositorySync(http_enabled=True)
        self.application.repository_sync = repository_sync
        controller = TasksController(self.application)
        web = FakePreviewFile("Z:/missing/user-avatar-web.png")
        icon = FakePreviewFile("Z:/missing/user-avatar-icon.png")
        web.get_web_preview = lambda: web
        web.get_icon_preview = lambda: icon
        icon.get_web_preview = lambda: web
        icon.get_icon_preview = lambda: icon

        class AvatarSnapshot:
            @staticmethod
            def get_files_objects(group_by=None):
                return {"icon": [icon], "web": [web]}

        context = type("Context", (), {
            "versionless": {"SNAPSHOT": AvatarSnapshot()}, "versions": {},
        })()
        process = type("Process", (), {
            "contexts": {"icon": context},
        })()
        login = type("Login", (), {"process": {"icon": process}})()

        self.assertEqual(
            controller._login_avatar_url(login),
            "pending-preview:preview-task",
        )
        self.assertIs(repository_sync.scheduled[0][0], web)

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
        with TemporaryDirectory():
            settings = MemorySettings()
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
                "sortMode": "priority",
                "groupMode": "user",
                "quickViewMode": "compact",
                "workspaceSurface": "browser",
                "columns": columns,
            })
            self.assertEqual(controller.sortMode, "priority")
            self.assertEqual(controller.quickViewMode, "compact")
            self.assertEqual(controller.workspaceSurface, "browser")

            restored_application = FakeApplication()
            restored_application._settings = settings
            restored = TasksController(restored_application)

            self.assertEqual(restored.viewMode, "gantt")
            self.assertEqual(restored.sortMode, "priority")
            self.assertEqual(restored.groupMode, "user")
            self.assertEqual(restored.quickViewMode, "compact")
            self.assertEqual(restored.workspaceSurface, "browser")
            self.assertEqual(
                [item["key"] for item in restored.taskColumns],
                [item["key"] for item in columns],
            )
            self.assertNotIn("day", settings.allKeys())
            self.assertNotIn("checked", settings.allKeys())

    def test_project_task_session_restores_after_application_restart(self):
        settings = MemorySettings()
        application = FakeApplication()
        application._settings = settings
        controller = TasksController(application)
        controller.task_store.set_scope("project")
        controller.set_filter("text", "lighting")
        controller.set_filter("day", "2026-08-25")
        controller.toggle_quick_filter("status", "In Progress")
        controller._sort_descending = True
        controller._collapsed_groups = {"process\x1flight"}
        controller._calendar_year = 2026
        controller._calendar_month = 8
        controller._selected_advanced_code = "TASK0042"
        controller._advanced_checked = {"TASK0042"}
        controller._advanced_drafts = {
            "TASK0042": {"status": "Approved"}
        }

        controller.shutdown()

        restored_application = FakeApplication()
        restored_application._settings = settings
        restored = TasksController(restored_application)

        self.assertEqual(restored.advancedScope, "project")
        self.assertEqual(restored._filters["text"], "lighting")
        self.assertEqual(restored.selectedDay, "2026-08-25")
        self.assertEqual(
            restored._quick_filters["status"], {"In Progress"}
        )
        self.assertTrue(restored.sortDescending)
        self.assertEqual(
            restored._collapsed_groups, {"process\x1flight"}
        )
        self.assertEqual(
            (restored._calendar_year, restored._calendar_month),
            (2026, 8),
        )
        self.assertEqual(
            restored._pending_restored_task_code, "TASK0042"
        )
        self.assertFalse(restored._advanced_checked)
        self.assertFalse(restored._advanced_drafts)

        with patch.object(restored, "refresh_advanced") as refresh, \
                patch.object(restored, "use_current_object") as selected:
            restored.open_workspace()

        refresh.assert_called_once_with()
        selected.assert_not_called()

    def test_task_sessions_are_isolated_by_project(self):
        settings = MemorySettings()
        application = FakeApplication()
        application._settings = settings
        controller = TasksController(application)
        controller.task_store.set_scope("project")
        controller.set_filter("text", "project-a")

        application._current_project_code = "project-b"
        controller._project_changed("project-b")

        self.assertEqual(controller.advancedScope, "object")
        self.assertEqual(controller._filters["text"], "")
        controller.set_filter("text", "project-b")

        application._current_project_code = "test"
        controller._project_changed("test")

        self.assertEqual(controller.advancedScope, "project")
        self.assertEqual(controller._filters["text"], "project-a")

    def test_restored_task_selection_is_applied_after_scope_load(self):
        self.controller.task_store.set_scope("project")
        self.controller._pending_restored_task_code = "TASK0001"
        request_id = self.controller.task_store.begin_load()

        self.controller._advanced_loaded(request_id, {
            "tasks": [FakeTask(code="TASK0001")],
            "parents": [FakeTarget()],
            "page": {"loaded": 1, "hasMore": False, "total": 1},
        })

        self.assertEqual(
            self.controller._selected_advanced_code, "TASK0001"
        )
        self.assertEqual(self.controller._pending_restored_task_code, "")

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
            "viewMode": "gantt", "sortMode": "priority",
            "groupMode": "status", "inspectorExpanded": True,
            "quickViewMode": "compact", "workspaceSurface": "browser",
            "columns": columns,
        }

        configuration.update_page("tasks_preferences", values)
        self.assertTrue(configuration._apply_page("tasks_preferences"))

        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0]["viewMode"], "gantt")
        self.assertEqual(applied[0]["sortMode"], "priority")
        self.assertEqual(applied[0]["groupMode"], "status")
        self.assertEqual(applied[0]["quickViewMode"], "compact")
        self.assertEqual(applied[0]["workspaceSurface"], "browser")
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
        self._receive_filtered_page([])
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
        self.controller.set_view_mode("gantt")
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
        self.controller.set_view_mode("gantt")
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

    def test_unscheduled_gantt_draft_moves_section_only_after_save(self):
        self.controller.set_view_mode("gantt")
        from thlib.environment import env_inst

        task = self.application.workspace_state._task_sobjects[0]
        task.get_info().update({
            "bid_start_date": "",
            "bid_end_date": "",
        })
        self.controller.open_workspace()
        original = self.controller.gantt_model.get(0)
        self.assertEqual(original["ganttSection"], "unscheduled")

        self.assertTrue(self.controller.stage_gantt_schedule(
            "TASK0001", 8, 2
        ))

        draft = self.controller.gantt_model.get(0)
        self.assertTrue(draft["ganttScheduled"])
        self.assertEqual(draft["ganttSection"], "unscheduled")
        self.assertEqual(self.controller.ganttScheduledCount, 0)
        self.assertEqual(self.controller.ganttUnscheduledCount, 1)

        with patch.object(
                env_inst.server_pool, "add_task",
                side_effect=lambda operation: ImmediateWorker(operation)):
            self.assertTrue(self.controller.save_advanced_changes())
            QGuiApplication.processEvents()

        saved = self.controller.gantt_model.get(0)
        self.assertEqual(saved["ganttSection"], "scheduled")
        self.assertEqual(self.controller.ganttScheduledCount, 1)
        self.assertEqual(self.controller.ganttUnscheduledCount, 0)

    def test_gantt_move_shifts_checked_tasks_as_one_edit(self):
        self.controller.set_view_mode("gantt")
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
        self.controller.set_view_mode("gantt")
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
        self.controller.set_view_mode("gantt")
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
        self.controller.set_view_mode("gantt")
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

    def test_task_column_context_commands_share_controller_state(self):
        self.controller.open_workspace()

        self.controller.set_task_column_sort("status", True)
        self.assertEqual(self.controller.sortMode, "status")
        self.assertTrue(self.controller.sortDescending)

        self.controller.group_by_task_column("status")
        self.assertEqual(self.controller.groupMode, "status")

        status = next(
            item for item in self.controller.taskColumns
            if item["key"] == "status"
        )
        self.assertFalse(status["required"])
        self.controller.set_task_column_visible("status", False)
        status = next(
            item for item in self.controller.taskColumns
            if item["key"] == "status"
        )
        self.assertFalse(status["visible"])

    def test_task_sorting_and_grouping_options_have_semantic_icons(self):
        self.assertEqual(
            {
                option["value"]: option["icon"]
                for option in self.controller.sortOptions
            },
            {
                "due": "schedule",
                "recent": "history",
                "process": "process",
                "user": "person",
                "status": "status",
                "object": "sobject",
                "priority": "priority-high",
                "milestone": "milestone",
                "supervisor": "admin-panel-settings",
            },
        )
        self.controller._advanced_raw = [
            {"project": "alpha", "parentSearchType": "asset"},
            {"project": "beta", "parentSearchType": "shot"},
        ]
        self.assertEqual(
            {
                option["value"]: option["icon"]
                for option in self.controller.groupOptions
            },
            {
                "process": "process",
                "status": "status",
                "user": "person",
                "object": "sobject",
                "project": "workspaces",
                "search_type": "schema",
                "none": "ungroup-items",
            },
        )

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

    def test_task_manager_opens_dependency_editor_for_one_native_task(self):
        workspace = self.application.workspace_state
        first = FakeTask(code="TASK0001")
        second = FakeTask(code="TASK0002")
        workspace._task_sobjects = [first, second]
        self.controller.use_current_object()

        self.assertTrue(self.controller.delete_advanced_task("TASK0002"))

        self.assertEqual(first.delete_calls, [])
        self.assertEqual(second.delete_calls, [])
        self.assertEqual(
            self.application.sobject_delete.requests,
            [([second], "tasks")],
        )
        self.assertIs(
            self.application.sobject_delete.parent_requests[0][
                second.get_search_key()],
            workspace._selected_sobject)
        self.assertEqual(
            [task.get_info()["code"] for task in workspace._task_sobjects],
            ["TASK0001", "TASK0002"],
        )

        self.application.sobject_delete.finish()

        self.assertEqual(
            [task.get_info()["code"] for task in workspace._task_sobjects],
            ["TASK0001"],
        )
        self.assertEqual(
            [task.get_info()["code"]
             for task in self.controller.task_store.task_objects()],
            ["TASK0001"],
        )
        self.assertFalse(self.controller.advancedDeleting)

    def test_task_manager_passes_exactly_checked_tasks_to_dependency_editor(self):
        workspace = self.application.workspace_state
        tasks = [
            FakeTask(code="TASK0001"),
            FakeTask(code="TASK0002"),
            FakeTask(code="TASK0003"),
        ]
        workspace._task_sobjects = tasks
        self.controller.use_current_object()
        self.controller.toggle_advanced_checked("TASK0001")
        self.controller.toggle_advanced_checked("TASK0003")

        self.assertTrue(self.controller.delete_checked_advanced_tasks())

        self.assertEqual(tasks[0].delete_calls, [])
        self.assertEqual(tasks[1].delete_calls, [])
        self.assertEqual(tasks[2].delete_calls, [])
        self.assertEqual(
            self.application.sobject_delete.requests,
            [([tasks[0], tasks[2]], "tasks")],
        )

        self.application.sobject_delete.finish()

        self.assertEqual(
            [task.get_info()["code"] for task in workspace._task_sobjects],
            ["TASK0002"],
        )
        self.assertEqual(self.controller.advancedCheckedCount, 0)

    def test_task_manager_delete_is_blocked_by_unsaved_row_changes(self):
        from thlib.environment import env_inst

        self.controller.use_current_object()
        self.controller._advanced_drafts["TASK0001"] = {
            "description": "Pending edit",
        }

        with patch.object(env_inst.server_pool, "add_task") as add_task:
            self.assertFalse(
                self.controller.delete_advanced_task("TASK0001")
            )

        add_task.assert_not_called()
        self.assertEqual(
            self.controller.advancedError,
            "Save or discard task changes before deleting.",
        )

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
        self._receive_filtered_page([workspace._task_sobjects[1]])

        self.assertEqual(self.controller.advanced_model.count(), 1)
        self.assertEqual(self.controller.advancedCheckedCount, 1)
        self.assertEqual(self.controller.bulkPreview["targets"], 1)

    def _receive_filtered_page(self, tasks):
        self.controller._query_timer.stop()
        request = self.controller.task_store.begin_load()
        self.controller._advanced_loaded(request, {
            "tasks": tasks, "parents": list(self.controller.task_store.parents.values()),
            "page": {"loaded": len(tasks), "hasMore": False, "total": len(tasks)},
            "serverFiltered": True,
        })

    def test_replaced_page_keeps_drafts_but_refreshes_checked_native_tasks(self):
        workspace = self.application.workspace_state
        first = FakeTask(code="TASK0001", status="Pending")
        second = FakeTask(code="TASK0002", status="Pending")
        workspace._task_sobjects = [first, second]
        self.controller.use_current_object()
        self.controller._advanced_drafts["TASK0001"] = {"description": "Unsaved edit"}
        self.controller._advanced_checked.add("TASK0002")
        refreshed = FakeTask(code="TASK0002", status="Ready")
        self._receive_filtered_page([refreshed])
        self.assertIs(self.controller._advanced_tasks["TASK0001"], first)
        self.assertIs(self.controller._advanced_tasks["TASK0002"], refreshed)
        records = {row["taskCode"]: row for row in self.controller.advanced_model._records}
        self.assertEqual(records["TASK0001"]["description"], "Unsaved edit")
        self.assertEqual(records["TASK0002"]["status"], "Ready")
        self.assertEqual(self.controller.task_store.page_codes, {"TASK0002"})
        stale_request = self.controller._advanced_request_id
        self.controller.set_filter("text", "no matches")
        self.controller._advanced_loaded(stale_request, {"tasks": []})
        self.assertIn("TASK0002", self.controller._advanced_tasks)

    def test_quick_filters_sorting_and_grouping_replace_server_page(self):
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
        self.assertTrue(self.controller._query_dirty)
        self._receive_filtered_page([workspace._task_sobjects[1]])
        self.assertEqual(self.controller.advanced_model.count(), 1)
        self.assertEqual(
            self.controller.advanced_model.get(0)["taskCode"], "TASK0002"
        )
        self.assertEqual(self.controller.activeQuickFilterCount, 1)
        self.assertEqual(self.controller._selected_advanced_code, "TASK0001")

        self.controller.clear_quick_filters()
        self._receive_filtered_page(workspace._task_sobjects)
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
        table_resets = QSignalSpy(self.controller.table_model.modelReset)
        table_removals = QSignalSpy(self.controller.table_model.rowsRemoved)
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
        self.assertEqual(table_resets.count(), 0)
        self.assertEqual(table_removals.count(), 1)
        self.assertEqual(visible_set_changes, [])
        model_rows = [
            record for record in self.controller.advanced_model._records
            if record["process"] == "model"
        ]
        self.assertEqual(sum(record["groupFirst"] for record in model_rows), 1)
        self.assertTrue(all(record["groupCount"] == 2 for record in model_rows))
        self.assertTrue(all(record["groupCollapsed"] for record in model_rows))

    def test_gantt_applies_deferred_group_state_when_presented(self):
        workspace = self.application.workspace_state
        workspace._task_sobjects = [
            FakeTask(code="TASK0001", process="model", status="Ready"),
            FakeTask(code="TASK0002", process="model", status="Pending"),
            FakeTask(code="TASK0003", process="publish", status="Ready"),
        ]
        self.controller.use_current_object()
        self.controller.set_group_mode("status")

        self.assertTrue(self.controller._gantt_projection_dirty)

        self.controller.set_view_mode("gantt")

        self.assertFalse(self.controller._gantt_projection_dirty)
        self.assertEqual(
            {record["groupKey"] for record in self.controller.gantt_model._records},
            {"Ready", "Pending"},
        )

        self.controller.toggle_group_collapsed("Ready")
        ready = [
            record for record in self.controller.gantt_model._records
            if record["groupKey"] == "Ready"
        ]
        self.assertTrue(ready)
        self.assertTrue(all(record["groupCollapsed"] for record in ready))

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

    def test_pristine_missing_process_task_can_be_saved_from_inspector(self):
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc

        target = self.application.workspace_state._selected_sobject
        target.get_project = lambda: Mock(get_code=lambda: "test")

        with patch.object(
                env_inst.server_pool, "add_task",
                side_effect=lambda operation, *args, **kwargs: ImmediateWorker(
                    lambda: operation(*args, **kwargs)
                )), \
                patch.object(tc, "insert_sobjects", return_value={}) as insert:
            self.assertTrue(self.controller.save_process_changes(1))
            QGuiApplication.processEvents()

        values = insert.call_args.args[2]
        self.assertEqual(values["process"], "publish")
        self.assertEqual(values["pipeline_code"], "publish_pipe")
        self.assertEqual(float(values["bid_duration"]), 8.0)


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

    def test_edit_task_prefers_the_native_task_search_type(self):
        from thlib.environment import env_inst

        task = self.application.workspace_state._task_sobjects[0]
        task_stype = object()
        task.get_stype = Mock(return_value=task_stype)
        with patch.object(
            env_inst, "get_stype_by_code", return_value=None
        ) as fallback:
            self.controller.begin_edit_for_process(0)

        fallback.assert_not_called()
        request = self.application._sobject_editor_request
        self.assertEqual(request["mode"], "edit")
        self.assertIs(request["stype"], task_stype)
        self.assertIs(request["sobject"], task)
        self.assertEqual(self.application.window_model.opened, ["task_editor"])

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

        self.controller._selected_advanced_code = "TASK0001"
        self.controller._advanced_selection_anchor = "TASK0001"
        self.controller.history_model.replace([{
            "timestamp": "2026-08-23 10:00:00",
            "fromStatus": "Pending",
            "toStatus": "Ready",
            "login": "artist",
            "color": "#607d8b",
        }])
        previous_history_request = self.controller._history_request_id

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
        self.assertEqual(self.controller.history_model.count(), 0)
        self.assertNotEqual(
            self.controller._history_request_id, previous_history_request
        )

        self.controller._advanced_selection_anchor = code
        self.controller._gantt_undo.append({code: {"progress": 35}})
        self.controller._gantt_redo.append({code: {"progress": 20}})

        self.controller.discard_advanced_changes(code)
        self.assertFalse(any(
            item["taskCode"] == code
            for item in self.controller.table_model._records
        ))
        self.assertEqual(self.controller.advancedDirtyCount, 0)
        self.assertEqual(self.controller._selected_advanced_code, "")
        self.assertEqual(self.controller._advanced_selection_anchor, "")
        self.assertEqual(self.controller.history_model.count(), 0)
        self.assertEqual(self.controller._gantt_undo, [])
        self.assertEqual(self.controller._gantt_redo, [])

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
        selection_changes = QSignalSpy(
            self.application.workspace_state.selection_changed
        )
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
        self.assertEqual(selection_changes.count(), 0)

    def test_process_notes_without_a_task_refresh_the_selected_context(self):
        selection_changes = QSignalSpy(
            self.application.workspace_state.selection_changed
        )

        self.controller.open_notes(
            self.controller.targetSearchKey, "model"
        )

        self.assertEqual(selection_changes.count(), 1)
        self.assertEqual(self.application.dock_model.opened, ["notes"])

    def test_notes_open_unselected_parent_with_attachment_process(self):
        parent_key = "skey://test/asset?project=test&code=ASSET002"
        self.controller.open_notes(parent_key, "model", "TASK0002")
        self.assertEqual(
            self.application.opened_search_keys,
            [(parent_key, "model")],
        )
        self.assertEqual(self.application._selected_detail_process, "model")
        self.assertEqual(self.application.dock_model.opened, ["notes"])

    def test_object_scope_uses_one_batched_workspace_query_with_note_counts(self):
        import thlib.tactic_classes as tc

        target = FakeTarget(tasks=[FakeTask()])
        task = target.tasks[0]
        result_page = {
            "tasks": [task], "parents": [target], "total": 1,
        }

        with patch.object(
                tc, "get_task_workspace_page", return_value=result_page
        ) as query, patch.object(
                target, "get_tasks_sobjects",
                wraps=target.get_tasks_sobjects
        ) as old_query:
            result = TasksController._load_advanced_scope(
                "object", "", "test", target, target.get_search_key(), []
            )

        self.assertEqual(query.call_count, 1)
        old_query.assert_not_called()
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
                return_value=grouped) as old_query, patch.object(
                    tc, "get_task_workspace_page",
                    return_value={"tasks": grouped["model"], "parents": targets, "total": 2}) as query:
            result = TasksController._load_advanced_scope(
                "multiple", "", "test", None, "", targets
            )

        self.assertEqual(query.call_count, 1)
        old_query.assert_not_called()
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
                ) as query, patch.object(
                    tc, "execute_procedure_serverside",
                    return_value={"InputWidgets": [{
                        "name": "priority", "values": ["2"],
                        "labels": ["High"],
                    }]},
                ) as field_query:
            result = self.controller._load_advanced_scope(
                "search_type", "", "test", None, "prod/asset", [],
                include_field_catalog=True,
            )

        query.assert_called_once_with([
            ("project_code", "test"),
            ("search_type", "prod/asset?project=test"),
        ], ["bid_end_date", "timestamp desc"], "test", limit=500, offset=0)
        server.build_search_type.assert_called_once_with(
            "prod/asset", "test"
        )
        self.assertEqual(result["tasks"], [])
        field_query.assert_called_once()
        self.assertIsNone(field_query.call_args.args[1]["args"]["parent_key"])
        self.assertEqual(result["fieldCatalog"]["errors"], [])
        self.assertEqual(
            result["fieldCatalog"]["priorityChoices"][-1]["value"], "2",
        )

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
        self._receive_filtered_page([workspace._task_sobjects[0]])
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

    def test_hidden_projections_wait_for_their_actual_dock_presentation(self):
        from thlib.ui import tasks as module

        self.controller.use_current_object()
        self.controller.set_view_mode("list")
        self.controller.set_calendar_visible(False)
        with patch.object(module, "gantt_layout", wraps=module.gantt_layout) as gantt, \
                patch.object(module, "calendar_cells", wraps=module.calendar_cells) as calendar:
            self.controller._rebuild_advanced_models()
            gantt.assert_not_called()
            calendar.assert_not_called()
            self.controller.set_view_mode("gantt")
            gantt.assert_called_once()
            calendar.assert_not_called()
            self.controller.set_view_mode("list")
            self.application.dock_model.is_panel_presented = lambda name: name == "task_calendar"
            self.controller.sync_presentation()
            calendar.assert_called_once()
            self.application.dock_model.is_panel_presented = lambda name: False
            self.controller.sync_presentation()
            calendar.reset_mock()
            self.controller._rebuild_advanced_models()
            calendar.assert_not_called()
            gantt.assert_called_once()

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
        self.controller.set_calendar_visible(True)
        from thlib.environment import env_inst

        self.controller.use_current_object()
        initial_count = self.controller.calendar_model.count()

        with patch.object(env_inst.server_pool, "add_task") as add_task:
            self.controller.change_calendar_month(1)
            self.controller.change_calendar_month(-1)

        add_task.assert_not_called()
        self.assertFalse(self.controller._query_dirty)
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

    def test_open_calendar_builds_grid_while_task_query_is_running(self):
        self.controller.calendar_model.clear()
        self.controller._advanced_raw = []
        self.controller._advanced_busy = True

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

    def test_task_note_counts_do_not_copy_process_count_to_context_task(self):
        parent_key = self.controller.targetSearchKey
        records = [
            {
                "taskCode": "TASK0001", "parentKey": parent_key,
                "process": "model", "context": "model", "notes": 4,
            },
            {
                "taskCode": "TASK0002", "parentKey": parent_key,
                "process": "model", "context": "review", "notes": 4,
            },
        ]
        self.controller._advanced_raw = [dict(record) for record in records]
        self.controller.advanced_model.replace(records)

        self.controller.update_task_note_counts(
            parent_key, "model", {"TASK0001": 4, "TASK0002": 1},
            ["NOTE0002"],
        )

        self.assertEqual(self.controller._advanced_raw[0]["notes"], 4)
        self.assertEqual(self.controller._advanced_raw[1]["notes"], 1)
        self.assertEqual(self.controller.advanced_model.get(1)["notes"], 1)

    def test_live_notes_increment_only_their_own_task_branch(self):
        self.controller.set_advanced_visible(True)
        parent_key = self.controller.targetSearchKey
        records = [
            {
                "taskCode": "TASK0001", "parentKey": parent_key,
                "parentCode": "ASSET0001", "parentSearchType": "prod/asset",
                "process": "model", "context": "model", "notes": 4,
            },
            {
                "taskCode": "TASK0002", "parentKey": parent_key,
                "parentCode": "ASSET0001", "parentSearchType": "prod/asset",
                "process": "model", "context": "review", "notes": 1,
            },
        ]
        self.controller._advanced_raw = [dict(record) for record in records]
        self.controller.advanced_model.replace(records)

        self.controller.apply_server_batch({
            "initialActivity": False,
            "activity": [{
                "__kind__": "note", "code": "NOTE_ROOT",
                "search_type": "prod/asset", "search_code": "ASSET0001",
                "process": "model",
            }],
        })
        self.assertEqual(
            [record["notes"] for record in self.controller._advanced_raw],
            [5, 1],
        )

        self.controller.apply_server_batch({
            "initialActivity": False,
            "activity": [{
                "__kind__": "note", "code": "NOTE_TASK",
                "search_type": "sthpw/task?project=test",
                "search_code": "TASK0002", "process": "model",
            }],
        })
        self.assertEqual(
            [record["notes"] for record in self.controller._advanced_raw],
            [5, 2],
        )

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

    def test_section_layout_hide_retains_running_and_loaded_task_scope(self):
        live_worker = Mock()
        load_worker = Mock()
        visibility = []
        presented = {
            "tasks": True,
            "task_calendar": False,
            "notes": False,
        }
        self.application.dock_model.is_panel_presented = (
            lambda panel_id: presented.get(panel_id, False)
        )
        self.controller._workspace_surface = "browser"
        self.controller._advanced_visible = True
        self.controller.task_store.set_scope("project")
        request_id = self.controller.task_store.begin_load()
        model = self.controller.advanced_model
        self.controller._advanced_worker = load_worker
        self.controller._live_worker = live_worker
        self.controller._live_task_codes = {"TASK0042"}
        self.controller._live_inflight_codes = {"TASK0001"}
        live_request_id = self.controller._live_request_id
        self.controller._live_timer.start()
        self.controller.advancedVisibilityChanged.connect(visibility.append)

        with patch.object(
                self.controller, "_start_advanced_load") as start_load:
            # Section A hides Tasks while the already-presented Section B
            # still has a request in flight.
            presented["tasks"] = False
            self.controller.sync_presentation()

            self.assertTrue(self.controller.advancedBusy)
            self.assertIs(self.controller._advanced_worker, load_worker)
            self.assertEqual(self.controller._advanced_request_id, request_id)
            load_worker.cancel.assert_not_called()
            live_worker.cancel.assert_called_once_with()
            self.assertIsNone(self.controller._live_worker)
            self.assertFalse(self.controller._live_timer.isActive())
            self.assertFalse(self.controller._live_task_codes)
            self.assertFalse(self.controller._live_inflight_codes)
            self.assertNotEqual(
                self.controller._live_request_id, live_request_id
            )

            # Completion while A is active populates the retained B model.
            self.controller._advanced_loaded(request_id, {
                "tasks": [FakeTask(code="TASK0042")],
                "parents": [FakeTarget()],
                "page": {"loaded": 1, "hasMore": False, "total": 1},
            })
            self.assertIs(self.controller.advanced_model, model)
            self.assertEqual(model.get(0)["taskCode"], "TASK0042")

            # Warm A -> B -> A -> B exchanges only presentation.  The same
            # rows return synchronously and no task load is reconstructed.
            for tasks_presented in (True, False, True):
                presented["tasks"] = tasks_presented
                self.controller.sync_presentation()

        start_load.assert_not_called()
        self.assertIs(self.controller.advanced_model, model)
        self.assertEqual(model.get(0)["taskCode"], "TASK0042")
        self.assertEqual(visibility, [False, True, False, True])

    def test_project_change_and_shutdown_still_cancel_task_scope_loads(self):
        project_worker = Mock()
        project_request = self.controller.task_store.begin_load()
        self.controller._advanced_worker = project_worker

        self.application._current_project_code = "other"
        self.controller._project_changed("other")

        project_worker.cancel.assert_called_once_with()
        self.assertFalse(self.controller.advancedBusy)
        self.assertIsNone(self.controller._advanced_worker)
        self.assertNotEqual(
            self.controller._advanced_request_id, project_request
        )

        shutdown_controller = TasksController(FakeApplication())
        shutdown_worker = Mock()
        shutdown_controller.task_store.begin_load()
        shutdown_controller._advanced_worker = shutdown_worker

        shutdown_controller.shutdown()

        shutdown_worker.cancel.assert_called_once_with()
        self.assertIsNone(shutdown_controller._advanced_worker)

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
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        for name in (
            "controls/ComboBox.qml", "controls/SegmentedButton.qml",
            "controls/FilledActionButton.qml",
            "controls/DockWorkspaceFooter.qml",
            "controls/ItemCountActionButton.qml", "controls/StatusChip.qml",
            "controls/PreviewNavigationButton.qml", "QuickFilterChip.qml",
            "controls/InitialBatchPresentation.qml",
            "controls/DateField.qml",
            "UserComboBox.qml",
            "ContentLoadingOverlay.qml", "RefreshIconButton.qml",
            "TaskWorkspaceSurfaceSwitcher.qml",
            "TaskWorkspaceModeSwitcher.qml",
            "TaskProcessPanel.qml",
            "TaskEditorReleaseCoordinator.qml",
            "TaskHiddenDetails.qml",
            "TaskBrowserTable.qml", "TaskGanttProgressHandle.qml",
            "TaskGanttView.qml",
            "TaskCalendarView.qml",
            "TaskInspector.qml", "TaskBulkBar.qml",
            "TasksWorkspaceView.qml", "TaskDockView.qml",
            "ActivityFeedView.qml",
            "ColumnsEditorView.qml", "NamingEditorView.qml",
            "MessagesView.qml", "ScriptEditorView.qml", "HelpView.qml",
            "DeleteSObjectView.qml",
            "UpdateView.qml", "UserProfileView.qml",
            "TimesheetView.qml", "WorkReportsView.qml",
            "SnapshotBrowser.qml", "DockHost.qml",
            "AdvancedSearchView.qml", "DebugLogView.qml",
            "CommunicationView.qml", "DropPlateView.qml",
            "RepositorySyncView.qml", "CommitQueueView.qml",
            "CostReportsView.qml", "DatabaseEditorView.qml",
            "DescriptionEditor.qml", "SObjectInfoView.qml", "WatchFoldersView.qml",
            "TacticSearchField.qml",
            "WorkspaceCard.qml", "WorkspaceResultItem.qml",
            "DccOptionsView.qml",
            "ProcessFilterEditorView.qml", "SObjectFieldEditor.qml",
            "ConfigurationPage.qml",
            "controls/ProjectCard.qml", "controls/ProjectFilterToggles.qml",
            "ProjectChooser.qml", "ProjectEditorView.qml",
            "MilestoneManagerView.qml",
        ):
            component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(qml_dir / name))
            )
            self.assertNotEqual(
                component.status(), QQmlComponent.Status.Error,
                "\n".join(error.toString() for error in component.errors()),
            )

    def test_gantt_edge_handles_win_over_zero_and_full_progress(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        application = FakeApplication()
        task = application.workspace_state._task_sobjects[0]
        task.get_info().update({
            "bid_start_date": "2026-08-03 09:00:00",
            "bid_end_date": "2026-08-05 18:00:00",
            "progress": 0,
        })
        controller = TasksController(application)
        controller._progress_column = lambda: "progress"
        controller.open_workspace()
        controller.set_view_mode("gantt")
        self.assertEqual(controller.gantt_model.count(), 1)
        self.assertTrue(
            controller.gantt_model.get(0)["ganttScheduled"],
            controller.gantt_model.get(0),
        )
        engine.rootContext().setContextProperty("tasksController", controller)
        engine.rootContext().setContextProperty(
            "taskGanttModel", controller.gantt_model
        )

        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "TaskGanttView.qml"))
        )
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(1000, 520)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        QGuiApplication.processEvents()

        gantt_list = view.findChild(QQuickItem, "ganttTaskList")
        self.assertIsNotNone(gantt_list)
        QMetaObject.invokeMethod(gantt_list, "forceLayout")
        QTest.qWait(40)
        visual_items = [gantt_list]
        for visual_item in visual_items:
            visual_items.extend(visual_item.childItems())
        progress_handle = next((
            item for item in visual_items
            if item.objectName() == "ganttProgressHandle"
        ), None)
        self.assertIsNotNone(progress_handle)
        schedule_bar = progress_handle.parentItem()

        day_width = float(view.property("dayWidth"))
        initial = controller.gantt_model.get(0)
        start_point = schedule_bar.mapToScene(QPointF(
            10, schedule_bar.height() / 2
        )).toPoint()
        QTest.mouseMove(window, start_point)
        QGuiApplication.processEvents()
        self.assertTrue(progress_handle.isVisible())
        self.assertTrue(progress_handle.contains(
            progress_handle.mapFromScene(QPointF(start_point))
        ))
        QTest.mousePress(window, Qt.LeftButton, pos=start_point)
        QTest.mouseMove(window, start_point + QPoint(round(day_width), 0))
        QTest.mouseRelease(
            window, Qt.LeftButton,
            pos=start_point + QPoint(round(day_width), 0),
        )
        QGuiApplication.processEvents()
        resized_start = controller.gantt_model.get(0)
        self.assertGreater(
            resized_start["ganttStartDay"], initial["ganttStartDay"]
        )
        self.assertEqual(resized_start["end"], initial["end"])

        controller.stage_gantt_progress("TASK0001", 100)
        QMetaObject.invokeMethod(gantt_list, "forceLayout")
        QGuiApplication.processEvents()
        visual_items = [gantt_list]
        for visual_item in visual_items:
            visual_items.extend(visual_item.childItems())
        progress_handle = next(
            item for item in visual_items
            if item.objectName() == "ganttProgressHandle"
        )
        schedule_bar = progress_handle.parentItem()
        end_point = schedule_bar.mapToScene(QPointF(
            schedule_bar.width() - 10, schedule_bar.height() / 2
        )).toPoint()
        before_end_resize = controller.gantt_model.get(0)
        QTest.mouseMove(window, end_point)
        QGuiApplication.processEvents()
        self.assertTrue(progress_handle.isVisible())
        self.assertTrue(progress_handle.contains(
            progress_handle.mapFromScene(QPointF(end_point))
        ))
        QTest.mousePress(window, Qt.LeftButton, pos=end_point)
        QTest.mouseMove(window, end_point + QPoint(round(day_width), 0))
        QTest.mouseRelease(
            window, Qt.LeftButton,
            pos=end_point + QPoint(round(day_width), 0),
        )
        QGuiApplication.processEvents()
        resized_end = controller.gantt_model.get(0)
        self.assertEqual(resized_end["start"], before_end_resize["start"])
        self.assertGreater(
            resized_end["ganttDurationDays"],
            before_end_resize["ganttDurationDays"],
        )

        window.close()
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()

    def test_task_inspector_edits_and_saves_an_empty_process_task(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        application = FakeApplication()
        inspector_controller = _TaskInspectorController()
        tasks_controller = _TaskInspectorTasksController()
        work_hours = WorkHoursController(application)
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ))
        engine.rootContext().setContextProperty(
            "tasksController", tasks_controller
        )
        engine.rootContext().setContextProperty("userListModel", users)
        engine.rootContext().setContextProperty(
            "workHoursController", work_hours
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "TaskInspector.qml"))
        )
        inspector = component.createWithInitialProperties({
            "theme": theme,
            "controller": inspector_controller,
            "width": 620,
            "height": 310,
        })
        self.assertIsNotNone(
            inspector,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(620, 310)
        inspector.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(50)

        def item(name):
            result = inspector.findChild(QQuickItem, name)
            self.assertIsNotNone(result, name)
            return result

        def click(target):
            center = target.mapToItem(
                window.contentItem(),
                QPointF(target.width() / 2, target.height() / 2),
            )
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(center.x()), round(center.y())),
            )
            QGuiApplication.processEvents()

        surface = item("taskInspectorTaskSurface")
        title = item("taskInspectorTaskTitle")
        status = item("taskInspectorStatusField")
        assignee = item("taskInspectorAssigneeField")
        save = item("taskInspectorSaveButton")
        full_create = item("taskInspectorFullCreateButton")
        edit = item("taskInspectorEditButton")
        task_switch = item("taskInspectorTaskSwitchButton")

        self.assertTrue(surface.property("visible"))
        self.assertEqual(title.property("text"), "Publish task")
        self.assertTrue(status.property("visible"))
        self.assertTrue(assignee.property("visible"))
        self.assertTrue(save.property("visible"))
        self.assertTrue(full_create.property("visible"))
        self.assertFalse(edit.property("visible"))
        self.assertFalse(task_switch.property("visible"))

        click(save)
        self.assertEqual(tasks_controller.saved_rows, [1])
        click(full_create)
        self.assertEqual(inspector_controller.full_create_count, 1)

        inspector_controller.set_task(code="TASK001", dirty=False)
        inspector_controller.set_task_choices([
            {
                "value": "TASK001", "label": "publish",
                "status": "Artist · Ready", "selected": True,
                "primaryBranch": True, "noteCount": 2,
            },
            {
                "value": "TASK002", "label": "review",
                "status": "Lead · Review", "selected": False,
                "primaryBranch": False, "noteCount": 1,
            },
        ])
        QTest.qWait(30)
        self.assertTrue(edit.property("visible"))
        self.assertTrue(full_create.property("visible"))
        self.assertTrue(task_switch.property("visible"))
        self.assertEqual(task_switch.property("iconName"), "swap_horiz")
        self.assertFalse(save.property("visible"))
        edit_right = edit.mapToScene(QPointF(edit.width(), 0)).x()
        create_left = full_create.mapToScene(QPointF()).x()
        self.assertGreaterEqual(create_left, edit_right)
        self.assertLessEqual(create_left - edit_right, 10)

        for width in (360, 620):
            window.resize(width, 310)
            inspector.setProperty("width", width)
            QTest.qWait(30)
            surface_right = surface.mapToScene(
                QPointF(surface.width(), 0)
            ).x()
            surface_bottom = surface.mapToScene(
                QPointF(0, surface.height())
            ).y()
            for control in (status, assignee, edit, full_create):
                control_right = control.mapToScene(
                    QPointF(control.width(), 0)
                ).x()
                control_bottom = control.mapToScene(
                    QPointF(0, control.height())
                ).y()
                self.assertLessEqual(control_right, surface_right + 0.5)
                self.assertLessEqual(control_bottom, surface_bottom + 0.5)

        inspector_controller.set_expanded(False)
        QTest.qWait(20)
        self.assertFalse(surface.property("visible"))
        self.assertTrue(task_switch.property("visible"))

        window.close()
        window.deleteLater()
        inspector.deleteLater()
        theme.deleteLater()

    def test_empty_task_workspace_keeps_heavy_surfaces_unloaded(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        application = FakeApplication()
        application.workspace_state._selected_sobject = None
        application.workspace_state._task_sobjects = []
        controller = TasksController(application)
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ))
        engine.rootContext().setContextProperty("tasksController", controller)
        engine.rootContext().setContextProperty(
            "advancedTaskModel", controller.advanced_model
        )
        engine.rootContext().setContextProperty(
            "advancedTaskTableModel", controller.table_model
        )
        engine.rootContext().setContextProperty(
            "taskGanttModel", controller.gantt_model
        )
        engine.rootContext().setContextProperty("userListModel", users)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
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
        window = QQuickWindow()
        window.resize(900, 560)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        QTest.qWait(40)

        menu_expression = QQmlExpression(
            QQmlEngine.contextForObject(view), view,
            "JSON.stringify(workspaceMenuActions())",
        )
        encoded_actions, _undefined = menu_expression.evaluate()
        self.assertFalse(menu_expression.hasError())
        actions = json.loads(encoded_actions)

        def commands(records):
            self.assertLessEqual(sum(not record.get("separator") for record in records), 8)
            result = set()
            for record in records:
                if record.get("command"):
                    result.add(record["command"])
                if "children" in record:
                    result.update(commands(record["children"]))
            return result

        available = commands(actions)
        self.assertTrue({"view:list", "view:gantt", "calendar", "columns", "clear", "filters"} <= available)
        self.assertTrue({"sort:" + option["value"] for option in controller.sortOptions} <= available)
        self.assertTrue({"group:" + option["value"] for option in controller.groupOptions} <= available)

        surface_slot = view.findChild(
            QQuickItem, "taskWorkspaceSurfaceSlot"
        )
        surface_loader = view.findChild(
            QObject, "taskWorkspaceSurfaceLoader"
        )
        empty_state = view.findChild(QQuickItem, "taskWorkspaceEmptyState")
        persistent_footer = view.findChild(
            QQuickItem, "taskWorkspacePersistentFooter"
        )
        empty_title = view.findChild(
            QObject, "taskWorkspaceEmptyTitle"
        )
        empty_hint = view.findChild(
            QObject, "taskWorkspaceEmptyHint"
        )
        empty_arrow = view.findChild(
            QQuickItem, "taskWorkspaceEmptyArrow"
        )
        empty_message = view.findChild(
            QQuickItem, "taskWorkspaceEmptyMessageBlock"
        )
        create_button = view.findChild(
            QQuickItem, "taskWorkspaceCreateButton"
        )
        self.assertIsNotNone(surface_slot)
        self.assertIsNotNone(surface_loader)
        self.assertFalse(surface_loader.property("active"))
        self.assertIsNotNone(empty_state)
        self.assertIsNotNone(persistent_footer)
        self.assertIsNotNone(empty_title)
        self.assertIsNotNone(empty_hint)
        self.assertIsNotNone(empty_arrow)
        self.assertIsNotNone(empty_message)
        self.assertIsNotNone(create_button)
        self.assertTrue(empty_state.property("visible"))
        self.assertTrue(persistent_footer.property("visible"))
        self.assertEqual(empty_title.property("text"), "Create a task")
        self.assertEqual(
            empty_hint.property("text"), "Use the + button above"
        )
        self.assertAlmostEqual(
            empty_state.mapToScene(QPointF(0, 0)).x(),
            surface_slot.mapToScene(QPointF(0, 0)).x(),
            delta=0.5,
        )
        self.assertAlmostEqual(
            float(empty_state.property("height")),
            float(surface_slot.property("height"))
                - float(persistent_footer.property("height")),
            delta=0.5,
        )
        self.assertAlmostEqual(
            persistent_footer.mapToScene(QPointF(
                0, float(persistent_footer.property("height"))
            )).y(),
            float(view.property("height")),
            delta=0.5,
        )
        self.assertAlmostEqual(
            float(empty_state.property("width")),
            float(surface_slot.property("width")),
            delta=0.5,
        )
        for arrow_width in (1180, 720, 500, 380):
            view.setProperty("width", arrow_width)
            QTest.qWait(20)
            arrow_target = empty_arrow.mapToScene(QPointF(
                float(empty_arrow.property("targetX")),
                float(empty_arrow.property("targetY")),
            ))
            button_bottom = create_button.mapToScene(QPointF(
                create_button.width() / 2,
                create_button.height(),
            ))
            arrow_source = empty_arrow.mapToScene(QPointF(
                float(empty_arrow.property("sourceX")),
                float(empty_arrow.property("sourceY")),
            ))
            message_left = empty_message.mapToScene(QPointF(
                0, empty_message.height() / 2 + 8,
            ))
            self.assertAlmostEqual(
                arrow_target.x(), button_bottom.x(), delta=0.5
            )
            self.assertAlmostEqual(
                arrow_target.y(), button_bottom.y() + 4.0, delta=0.5
            )
            self.assertAlmostEqual(
                arrow_source.x(), message_left.x() - 18.0, delta=0.5
            )
            self.assertAlmostEqual(
                arrow_source.y(), message_left.y(), delta=0.5
            )
        self.assertIsNone(view.findChild(QObject, "taskBrowserTable"))
        self.assertIsNone(view.findChild(QObject, "ganttTaskList"))
        self.assertIsNone(
            view.findChild(QObject, "taskPendingChangesOverlaySlot")
        )
        self.assertIsNone(view.findChild(QObject, "taskColumnContextMenu"))

        window.close()
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()

    def test_quick_task_view_switcher_uses_shared_segmented_control(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        controller = TasksController(FakeApplication())
        controller.use_current_object()
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ))
        engine.rootContext().setContextProperty("tasksController", controller)
        engine.rootContext().setContextProperty(
            "taskProcessModel", controller.process_model
        )
        engine.rootContext().setContextProperty("userListModel", users)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "TaskProcessPanel.qml"))
        )
        panel = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            panel,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.setColor(QColor("#ff00ff"))
        window.resize(640, 480)
        panel.setParentItem(window.contentItem())
        panel.setSize(window.size())
        window.show()
        QTest.qWait(40)

        switcher = panel.findChild(QQuickItem, "quickTaskViewSwitcher")
        refresh = panel.findChild(QQuickItem, "quickTaskRefreshButton")
        background_surface = panel.findChild(
            QQuickItem, "quickTaskBackgroundSurface"
        )
        footer = panel.findChild(QQuickItem, "quickTaskFooter")
        self.assertIsNotNone(switcher)
        self.assertIsNotNone(refresh)
        self.assertIsNotNone(background_surface)
        self.assertIsNotNone(footer)
        self.assertEqual(
            footer.height(), theme.property("dockWorkspaceFooterHeight")
        )
        self.assertEqual(
            footer.property("bottomLeftRadius"),
            background_surface.property("bottomLeftRadius"),
        )
        self.assertEqual(
            footer.property("bottomRightRadius"),
            background_surface.property("bottomRightRadius"),
        )
        image = window.grabWindow()
        self.assertFalse(image.isNull())
        bottom_corner = image.pixelColor(0, image.height() - 1)
        bottom_center = image.pixelColor(
            image.width() // 2, image.height() - 1
        )
        self.assertGreater(bottom_corner.red(), 200)
        self.assertGreater(bottom_corner.blue(), 200)
        self.assertNotEqual(bottom_center.name(), bottom_corner.name())
        segments = [switcher]
        for item in segments:
            segments.extend(item.childItems())
        cards = next((
            item for item in segments
            if item.objectName() == "segmentedButtonSegment_cards"
        ), None)
        compact = next((
            item for item in segments
            if item.objectName() == "segmentedButtonSegment_compact"
        ), None)
        workspace = next((
            item for item in segments
            if item.objectName() == "segmentedButtonSegment_workspace"
        ), None)
        self.assertIsNotNone(cards)
        self.assertIsNotNone(compact)
        self.assertIsNotNone(workspace)
        self.assertLess(cards.property("x"), compact.property("x"))
        self.assertLess(compact.property("x"), workspace.property("x"))
        switcher_width = switcher.width()
        segment_positions = [
            item.mapToScene(QPointF(0, 0)).x()
            for item in (cards, compact, workspace)
        ]
        switcher_right = switcher.mapToScene(QPointF(
            switcher.width(), 0
        )).x()
        refresh_left = refresh.mapToScene(QPointF(0, 0)).x()
        refresh_right = refresh.mapToScene(QPointF(
            refresh.width(), 0
        )).x()
        self.assertLess(switcher_right, refresh_left)
        self.assertLess(refresh_left - switcher_right, 12)
        self.assertLess(panel.width() - refresh_right, 12)
        self.assertAlmostEqual(
            panel.width() - switcher_right, 49.0, delta=1.0
        )
        self.assertTrue(cards.property("selected"))
        compact_center = compact.mapToScene(QPointF(
            compact.width() / 2, compact.height() / 2
        ))
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(compact_center.x()), round(compact_center.y())),
        )
        QGuiApplication.processEvents()
        self.assertEqual(controller.quickViewMode, "compact")
        self.assertTrue(compact.property("selected"))
        self.assertEqual(switcher.width(), switcher_width)
        self.assertEqual([
            item.mapToScene(QPointF(0, 0)).x()
            for item in (cards, compact, workspace)
        ], segment_positions)

        workspace_center = workspace.mapToScene(QPointF(
            workspace.width() / 2, workspace.height() / 2
        ))
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(workspace_center.x()), round(workspace_center.y())),
        )
        QGuiApplication.processEvents()
        self.assertEqual(controller.workspaceSurface, "browser")
        self.assertTrue(workspace.property("selected"))
        self.assertEqual(switcher.width(), switcher_width)
        self.assertEqual([
            item.mapToScene(QPointF(0, 0)).x()
            for item in (cards, compact, workspace)
        ], segment_positions)

        window.close()
        window.deleteLater()
        panel.deleteLater()
        theme.deleteLater()

    def test_help_view_keeps_navigation_and_article_usable_at_minimum_size(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(
                error.toString() for error in errors
            )
        )
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        window_model = FloatingWindowModel(MemorySettings())
        window_model.open_help("dock.tasks")
        engine.rootContext().setContextProperty("windowModel", window_model)
        settings_owner = SimpleNamespace(
            _settings={"appearance/language": "en"},
            _write_settings=lambda: None,
        )
        localization = LocalizationController(self.app, settings_owner)
        help_controller = HelpController(qml_dir.parent / "help_articles", localization)
        engine.rootContext().setContextProperty("helpController", help_controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "HelpView.qml"))
        )
        help_view = component.createWithInitialProperties({
            "theme": theme,
            "width": 760,
            "height": 520,
        })
        self.assertIsNotNone(
            help_view,
            "\n".join(error.toString() for error in component.errors()),
        )

        window = QQuickWindow()
        window.resize(760, 520)
        help_view.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(50)

        topic_list = help_view.findChild(QObject, "helpTopicList")
        topic_search = help_view.findChild(QObject, "helpTopicSearch")
        article = help_view.findChild(QObject, "helpArticleScroll")
        self.assertIsNotNone(topic_list)
        self.assertIsNotNone(topic_search)
        self.assertIsNotNone(article)
        topics = help_controller.topics
        self.assertGreater(len(topics), 0)
        self.assertEqual(topic_list.property("count"), len(topics))
        self.assertEqual(help_controller.selected_topic_id, "dock.tasks")
        self.assertGreater(
            float(topic_list.property("contentY")), 0,
            {
                "currentIndex": topic_list.property("currentIndex"),
                "height": topic_list.property("height"),
                "contentHeight": topic_list.property("contentHeight"),
            },
        )
        window_model.open_help("overview")
        QTest.qWait(20)
        self.assertLessEqual(float(topic_list.property("contentY")), 1)
        topic_search.setProperty("text", "overview")
        window_model.open_help("script_triggers")
        QTest.qWait(60)
        self.assertEqual(
            topic_search.property("text"), "",
            {
                "selected": help_controller.selected_topic_id,
                "currentIndex": topic_list.property("currentIndex"),
                "warnings": warnings,
            },
        )
        self.assertGreater(float(topic_list.property("contentY")), 0)
        self.assertIn("```python", help_controller.article["body"])
        self.assertIn("TACTIC_SCRIPT_KWARGS", help_controller.article["body"])
        self.assertGreater(float(topic_list.property("width")), 210)
        self.assertGreater(float(topic_list.property("height")), 360)
        self.assertGreater(float(article.property("width")), 420)
        self.assertGreater(float(article.property("height")), 420)
        article_body = help_view.findChild(QObject, "helpArticleBody")
        article_summary = help_view.findChild(QObject, "helpArticleSummary")
        summary_text = help_view.findChild(QObject, "helpArticleSummaryText")
        self.assertIsNotNone(article_body)
        self.assertIsNotNone(article_summary)
        self.assertIsNotNone(summary_text)
        self.assertTrue(article_summary.property("visible"))
        self.assertEqual(
            summary_text.property("text").split(),
            help_controller.article["summary"].split(),
        )
        self.assertIn("```python", article_body.property("text"))
        text_document = article_body.property("textDocument")
        document = text_document.textDocument()
        block = document.begin()
        spaced_blocks = 0
        code_margins = []
        while block.isValid():
            if block.blockFormat().bottomMargin() >= 8:
                spaced_blocks += 1
            if block.blockFormat().hasProperty(
                QTextFormat.Property.BlockCodeFence
            ):
                code_margins.append(block.blockFormat().bottomMargin())
            block = block.next()
        self.assertGreater(spaced_blocks, 8)
        self.assertIn(0, code_margins)
        self.assertIn(8, code_margins)
        del block, document, text_document
        rendered = window.grabWindow()
        self.assertFalse(rendered.isNull())
        self.assertEqual((rendered.width(), rendered.height()), (760, 520))
        help_warnings = [
            warning for warning in warnings if "/HelpView.qml:" in warning
        ]
        self.assertFalse(help_warnings, "\n".join(help_warnings))

        window.close()
        window.deleteLater()
        help_view.deleteLater()
        theme.deleteLater()

    def test_script_editor_is_compact_and_output_collapses_at_minimum_size(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(
                error.toString() for error in errors
            )
        )
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        settings = MemorySettings()
        settings.sync = lambda: None
        with (
            patch("thlib.ui.script_editor.env_read_config", return_value={}),
            patch("thlib.ui.script_editor.env_write_config"),
        ):
            controller = ScriptEditorController(None, Mock())
        controller._write_settings = Mock()
        dcc_bridge = ScriptEditorDccBridge()
        controller.attach_dcc_bridge(dcc_bridge)
        script_item = Mock()
        script_values = {
            "folder": "tools",
            "title": "History test",
            "language": "dcc_python",
            "script": "print('current')",
        }
        script_item.get_value.side_effect = script_values.get
        controller._done({
            "kind": "load",
            "objects": {"SCRIPT1": script_item},
            "rows": [{
                "token": "SCRIPT1",
                "folder": "tools",
                "title": "History test",
                "language": "dcc_python",
            }],
        })
        opened_script = controller.script("SCRIPT1")
        controller._done({
            "kind": "saved_history",
            "tabId": opened_script["tabId"],
            "token": "SCRIPT1",
            "history": [{
                "revisionId": "TX2",
                "timestamp": "2026-09-06 12:00:00",
                "actor": "artist",
                "changedFields": ["script"],
                "action": "update",
                "current": True,
            }, {
                "revisionId": "TX1",
                "timestamp": "2026-09-05 12:00:00",
                "actor": "artist",
                "changedFields": ["script"],
                "action": "create",
                "current": False,
            }],
        })
        controller._settings = settings
        window_model = FloatingWindowModel(MemorySettings())
        engine.rootContext().setContextProperty(
            "scriptEditorController", controller
        )
        engine.rootContext().setContextProperty(
            "scriptEditorTabModel", controller.tabs
        )
        engine.rootContext().setContextProperty(
            "scriptEditorModel", controller.model
        )
        engine.rootContext().setContextProperty("windowModel", window_model)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "ScriptEditorView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "width": 720,
            "height": 500,
        })
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(720, 500)
        view.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(50)

        toolbar = view.findChild(QObject, "scriptEditorToolbar")
        toolbar_scrollbar = view.findChild(
            QObject, "scriptEditorToolbarScrollBar"
        )
        tabs = view.findChild(QObject, "scriptEditorTabs")
        output_panel = view.findChild(QObject, "scriptEditorOutputPanel")
        source_panel = view.findChild(QObject, "scriptEditorSourcePanel")
        source_toolbar = view.findChild(QObject, "scriptEditorSourceToolbar")
        source_toolbar_scrollbar = view.findChild(
            QObject, "scriptEditorSourceToolbarScrollBar"
        )
        scripts_panel = view.findChild(QObject, "scriptEditorScriptsPanel")
        tree_search = view.findChild(QObject, "scriptEditorTreeSearch")
        tree_list = view.findChild(QObject, "scriptEditorTreeList")
        code_editor = view.findChild(QObject, "scriptEditorCodeEditor")
        line_numbers = view.findChild(QObject, "scriptEditorLineNumberGutter")
        line_number_text = view.findChild(
            QObject, "scriptEditorLineNumberText"
        )
        source_scroll = view.findChild(
            QObject, "scriptEditorSourceScrollView"
        )
        source_vertical = view.findChild(
            QObject, "scriptEditorSourceVerticalScrollBar"
        )
        source_horizontal = view.findChild(
            QObject, "scriptEditorSourceHorizontalScrollBar"
        )
        output_horizontal = view.findChild(
            QObject, "scriptEditorOutputHorizontalScrollBar"
        )
        output_vertical = view.findChild(
            QObject, "scriptEditorOutputVerticalScrollBar"
        )
        output_wrap_button = view.findChild(
            QObject, "scriptEditorOutputWrapButton"
        )
        tree_toggle_button = view.findChild(
            QObject, "scriptEditorTreeToggleButton"
        )
        close_all_button = view.findChild(
            QObject, "scriptEditorCloseAllButton"
        )
        find_button = view.findChild(QObject, "scriptEditorFindButton")
        edit_history_button = view.findChild(
            QObject, "scriptEditorHistoryButton"
        )
        saved_history_button = view.findChild(
            QObject, "scriptEditorSavedHistoryButton"
        )
        saved_history_popup = view.findChild(
            QObject, "scriptSavedRevisionHistoryPopup"
        )
        search_panel = view.findChild(QObject, "scriptEditorSearchPanel")
        source_text_item = view.findChild(QObject, "scriptEditorSourceText")
        output_text_item = view.findChild(QObject, "scriptEditorOutputText")
        output_title = view.findChild(QObject, "scriptEditorOutputTitle")
        outline = view.findChild(QObject, "scriptEditorOutline")
        outline_filter = view.findChild(QObject, "scriptEditorOutlineFilter")
        outline_list = view.findChild(QObject, "scriptEditorOutlineList")
        completion_popup = view.findChild(
            QObject, "scriptEditorCompletionPopup"
        )
        execution_target = view.findChild(
            QObject, "scriptEditorExecutionTarget"
        )
        for name, item in {
            "toolbar": toolbar, "toolbar scrollbar": toolbar_scrollbar,
            "tabs": tabs, "output": output_panel,
            "source": source_panel, "tree": scripts_panel,
            "source toolbar": source_toolbar,
            "source toolbar scrollbar": source_toolbar_scrollbar,
            "tree search": tree_search, "tree list": tree_list,
            "code editor": code_editor, "line numbers": line_numbers,
            "line number text": line_number_text,
            "source scroll view": source_scroll,
            "source vertical scrollbar": source_vertical,
            "source horizontal scrollbar": source_horizontal,
            "output horizontal scrollbar": output_horizontal,
            "output vertical scrollbar": output_vertical,
            "output wrap button": output_wrap_button,
            "tree toggle button": tree_toggle_button,
            "close all button": close_all_button,
            "find button": find_button,
            "local edit history": edit_history_button,
            "saved history": saved_history_button,
            "saved history popup": saved_history_popup,
            "search panel": search_panel,
            "source text": source_text_item,
            "output text": output_text_item,
            "output title": output_title,
            "outline": outline,
            "outline filter": outline_filter,
            "outline list": outline_list,
            "completion popup": completion_popup,
            "execution target": execution_target,
        }.items():
            self.assertIsNotNone(item, name)
        self.assertEqual(source_text_item.property("text"), "print('current')")
        self.assertEqual(execution_target.property("currentValue"), "dcc")
        self.assertEqual(
            execution_target.property("currentText"),
            dcc_bridge.selectedClientLabel,
        )
        self.assertLessEqual(float(toolbar.property("height")), 36)
        self.assertLessEqual(float(tabs.property("height")), 40)
        self.assertLessEqual(float(close_all_button.property("y")), 42)
        self.assertLessEqual(float(scripts_panel.property("width")), 205)
        self.assertGreater(float(source_panel.property("height")), 150)
        expanded_source_height = float(source_panel.property("height"))
        expanded_output_title_y = float(output_title.property("y"))

        view.setWidth(600)
        window.resize(600, 500)
        QTest.qWait(30)
        for name, viewport, scrollbar in (
            ("script", toolbar, toolbar_scrollbar),
            ("source", source_toolbar, source_toolbar_scrollbar),
        ):
            with self.subTest(toolbar=name):
                self.assertTrue(viewport.property("clip"))
                self.assertTrue(scrollbar.property("visible"), (
                    view.width(), source_panel.width(),
                    scripts_panel.x(), scripts_panel.width(),
                    viewport.width(), viewport.property("contentWidth")
                ))
                self.assertGreater(
                    float(viewport.property("contentWidth")), viewport.width()
                )
        if os.environ.get("SCRIPT_EDITOR_SCREENSHOT"):
            window.grabWindow().save(os.environ["SCRIPT_EDITOR_SCREENSHOT"])
        view.setWidth(720)
        window.resize(720, 500)
        QTest.qWait(30)

        self.assertTrue(QMetaObject.invokeMethod(
            tree_search, "forceActiveFocus"
        ))
        for key in (
            Qt.Key_H, Qt.Key_I, Qt.Key_S, Qt.Key_T,
            Qt.Key_O, Qt.Key_R, Qt.Key_Y,
        ):
            QTest.keyClick(window, key)
        QTest.qWait(20)
        self.assertEqual(controller.model.rowCount(), 2)
        self.assertEqual(tree_list.property("count"), 2)
        QTest.keyClick(window, Qt.Key_Escape)
        QTest.qWait(20)
        self.assertEqual(tree_search.property("text"), "")
        self.assertEqual(controller.model.rowCount(), 1)

        splitter = scripts_panel.mapToItem(
            window.contentItem(),
            QPointF(0, float(scripts_panel.property("height")) / 2),
        ).toPoint()
        splitter.setX(splitter.x() - 3)
        wider = QPoint(splitter.x() - 80, splitter.y())
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, splitter)
        QTest.mouseMove(window, wider, 20)
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, wider)
        QTest.qWait(20)
        resized_tree_width = float(scripts_panel.property("width"))
        self.assertGreater(resized_tree_width, 250)

        controller.close_tab(opened_script["tabId"])
        controller.script("SCRIPT1")
        QTest.qWait(30)
        self.assertAlmostEqual(
            float(scripts_panel.property("width")),
            resized_tree_width,
            delta=1.0,
        )

        code_editor.setProperty("text", "x")
        QGuiApplication.processEvents()
        self.assertEqual(controller.currentEditor["source"], "x")
        code_editor.setProperty("cursorPosition", 1)
        self.assertTrue(QMetaObject.invokeMethod(code_editor, "forceActiveFocus"))
        QTest.keyClick(window, Qt.Key_Tab)
        QTest.qWait(20)
        self.assertEqual(source_text_item.property("text"), "x   ")
        QTest.keyClick(window, Qt.Key_Z, Qt.ControlModifier)
        QTest.qWait(20)
        self.assertEqual(source_text_item.property("text"), "x")
        QTest.keyClick(window, Qt.Key_Y, Qt.ControlModifier)
        QTest.qWait(20)
        self.assertEqual(source_text_item.property("text"), "x   ")
        QTest.keyClick(
            window, Qt.Key_K, Qt.ControlModifier | Qt.ShiftModifier
        )
        QTest.qWait(20)
        self.assertEqual(source_text_item.property("text"), "")

        code_editor.setProperty("text", "pri")
        code_editor.setProperty("cursorPosition", 3)
        self.assertTrue(QMetaObject.invokeMethod(code_editor, "forceActiveFocus"))
        QTest.qWait(180)
        self.assertTrue(bool(completion_popup.property("visible")))
        QTest.keyClick(window, Qt.Key_Return)
        QTest.qWait(20)
        self.assertEqual(source_text_item.property("text"), "pri\n")
        QTest.qWait(220)
        self.assertFalse(bool(completion_popup.property("visible")))

        code_editor.setProperty("text", "pri")
        code_editor.setProperty("cursorPosition", 3)
        QTest.keyClick(window, Qt.Key_Space, Qt.ControlModifier)
        QTest.qWait(20)
        self.assertTrue(bool(completion_popup.property("visible")))
        QTest.keyClick(window, Qt.Key_Space)
        QTest.qWait(20)
        self.assertEqual(source_text_item.property("text"), "print( )")

        symbol_source = (
            "class Worker:\n"
            "    def run(self):\n"
            "        pass\n\n"
            "def build():\n"
            "    return Worker()\n"
        )
        code_editor.setProperty("text", symbol_source)
        QTest.qWait(220)
        self.assertEqual(len(view.property("codeSymbols")), 3)
        self.assertTrue(QMetaObject.invokeMethod(code_editor, "forceActiveFocus"))
        QTest.keyClick(
            window, Qt.Key_O, Qt.ControlModifier | Qt.ShiftModifier
        )
        QTest.qWait(30)
        self.assertEqual(view.property("sidePanelMode"), "outline")
        self.assertTrue(bool(outline.property("visible")))
        self.assertTrue(bool(outline_filter.property("activeFocus")))

        code_editor.setProperty("cursorPosition", 0)
        self.assertTrue(QMetaObject.invokeMethod(code_editor, "forceActiveFocus"))
        QTest.keyClick(window, Qt.Key_Down, Qt.AltModifier)
        QTest.qWait(20)
        self.assertGreater(int(code_editor.property("cursorPosition")), 0)

        with TemporaryDirectory() as directory, patch(
            "thlib.ui.script_editor.env_mode.get_current_path",
            return_value=directory,
        ):
            view.setProperty("outputCollapsed", True)
            QTest.qWait(20)
            self.assertTrue(bool(view.property("outputCollapsed")))
            run_spy = QSignalSpy(code_editor.runRequested)
            QTest.keyClick(
                window, Qt.Key_Enter,
                Qt.ControlModifier | Qt.KeypadModifier,
            )
            QTest.qWait(20)
            self.assertEqual(run_spy.count(), 1)
            action, payload, _timeout = dcc_bridge.commands[0]
            self.assertEqual(action, "execute_script_file")
            staged_script = Path(payload["path"])
            self.assertEqual(
                staged_script.parent,
                Path(directory) / "custom_scripts" / ".temp",
            )
            self.assertEqual(
                staged_script.read_text(encoding="utf-8"), symbol_source
            )
            dcc_bridge.commandFinished.emit(
                "qml-dcc-run", True, {"output": "QML Maya output\n"}, ""
            )
            QTest.qWait(20)
            self.assertTrue(staged_script.exists())
            self.assertIn("QML Maya output", controller.output)
            self.assertFalse(bool(view.property("outputCollapsed")))
            self.assertGreater(float(output_panel.property("height")), 42)

        source_text = "\n".join(
            [f"line_{index} = {index}" for index in range(90)]
            + ["x" * 600]
        )
        code_editor.setProperty("text", source_text)
        controller._append_output("\n".join(
            [f"output {index}" for index in range(60)] + ["y" * 600]
        ))
        QTest.qWait(60)

        line_pitch = float(line_number_text.property("implicitHeight")) / 91
        editor_pitch = float(source_text_item.property("contentHeight")) / 91
        self.assertAlmostEqual(line_pitch, editor_pitch, delta=0.5)
        self.assertTrue(QMetaObject.invokeMethod(
            code_editor, "goToLine", Q_ARG("QVariant", 60)
        ))
        QTest.qWait(20)
        cursor_rectangle = source_text_item.property("cursorRectangle")
        source_flickable = source_scroll.property("contentItem")
        self.assertLessEqual(
            cursor_rectangle.y() - float(source_flickable.property("contentY")),
            float(source_text_item.property("topPadding")) + 1,
        )

        self.assertGreaterEqual(int(code_editor.property("historyLimit")), 100)
        self.assertTrue(bool(output_text_item.property("readOnly")))
        self.assertTrue(bool(output_text_item.property("activeFocusOnPress")))

        find_center = find_button.mapToItem(
            window.contentItem(),
            QPointF(
                float(find_button.property("width")) / 2,
                float(find_button.property("height")) / 2,
            ),
        ).toPoint()
        self.assertFalse(bool(search_panel.property("visible")))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, find_center)
        QTest.qWait(20)
        self.assertTrue(bool(search_panel.property("visible")))
        find_center = find_button.mapToItem(
            window.contentItem(),
            QPointF(
                float(find_button.property("width")) / 2,
                float(find_button.property("height")) / 2,
            ),
        ).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, find_center)
        QTest.qWait(20)
        self.assertFalse(bool(search_panel.property("visible")))

        self.assertTrue(QMetaObject.invokeMethod(code_editor, "undoEdit"))
        QTest.qWait(20)
        self.assertNotEqual(source_text_item.property("text"), source_text)
        self.assertTrue(QMetaObject.invokeMethod(code_editor, "redoEdit"))
        QTest.qWait(20)
        self.assertEqual(source_text_item.property("text"), source_text)

        self.assertEqual(view.property("token"), "SCRIPT1")
        self.assertFalse(controller.busy)
        self.assertFalse(controller.savedHistoryLoading)
        self.assertTrue(bool(saved_history_button.property("visible")))
        self.assertTrue(bool(saved_history_button.property("enabled")))
        self.assertGreater(float(saved_history_button.property("width")), 0)
        self.assertGreater(float(saved_history_button.property("height")), 0)
        saved_history_center = saved_history_button.mapToItem(
            window.contentItem(),
            QPointF(
                float(saved_history_button.property("width")) / 2,
                float(saved_history_button.property("height")) / 2,
            ),
        ).toPoint()
        QTest.mouseClick(
            window, Qt.LeftButton, Qt.NoModifier, saved_history_center
        )
        QTest.qWait(30)
        self.assertTrue(bool(saved_history_popup.property("visible")))
        self.assertEqual(controller.savedHistoryCount, 2)
        self.assertTrue(QMetaObject.invokeMethod(saved_history_popup, "close"))
        controller.savedRevisionReady.emit("print('saved revision')")
        QTest.qWait(20)
        self.assertEqual(
            source_text_item.property("text"), "print('saved revision')"
        )
        self.assertTrue(controller.currentEditor["dirty"])
        self.assertTrue(QMetaObject.invokeMethod(code_editor, "undoEdit"))
        QTest.qWait(20)
        self.assertEqual(source_text_item.property("text"), source_text)

        self.assertEqual(int(code_editor.property("lineNumberCount")), 91)
        self.assertGreaterEqual(float(line_numbers.property("width")), 36)
        self.assertTrue(bool(source_vertical.property("visible")))
        self.assertTrue(bool(source_horizontal.property("visible")))
        self.assertTrue(bool(output_horizontal.property("visible")))
        self.assertTrue(bool(output_vertical.property("visible")))

        source_width_with_tree = float(source_panel.property("width"))
        view.setProperty("treeCollapsed", True)
        QTest.qWait(40)
        self.assertFalse(bool(scripts_panel.property("visible")))
        self.assertGreater(
            float(source_panel.property("width")), source_width_with_tree + 100
        )

        view.setProperty("outputWrap", True)
        QTest.qWait(40)
        self.assertFalse(bool(output_horizontal.property("visible")))

        view.setProperty("outputCollapsed", True)
        QTest.qWait(340)

        saved_layout = controller.get_settings_dict()
        self.assertTrue(saved_layout["treeCollapsed"])
        self.assertTrue(saved_layout["outputCollapsed"])
        self.assertTrue(saved_layout["outputWrap"])
        self.assertEqual(saved_layout["sidePanelMode"], "outline")
        view.setProperty("treeCollapsed", False)
        view.setProperty("outputCollapsed", False)
        view.setProperty("outputWrap", False)
        view.setProperty("sidePanelMode", "scripts")
        self.assertTrue(QMetaObject.invokeMethod(view, "restoreLayout"))
        QTest.qWait(20)
        self.assertTrue(bool(view.property("treeCollapsed")))
        self.assertTrue(bool(view.property("outputCollapsed")))
        self.assertTrue(bool(view.property("outputWrap")))
        self.assertEqual(view.property("sidePanelMode"), "outline")
        self.assertAlmostEqual(
            float(view.property("expandedOutputHeight")),
            float(saved_layout["outputHeight"]),
            delta=0.5,
        )

        self.assertLessEqual(float(output_panel.property("height")), 42)
        self.assertAlmostEqual(
            float(output_title.property("y")), expanded_output_title_y,
            delta=0.01,
        )
        self.assertGreater(
            float(source_panel.property("height")),
            expanded_source_height + 50,
        )
        rendered = window.grabWindow()
        self.assertFalse(rendered.isNull())
        self.assertEqual((rendered.width(), rendered.height()), (720, 500))

        controller.create_new_script()
        QTest.qWait(30)
        draft = dict(controller.currentEditor)
        self.assertTrue(draft["title"].startswith("new_script_"))
        self.assertLessEqual(
            abs(float(source_flickable.property("contentX"))), 1.0
        )
        self.assertLessEqual(
            abs(float(source_flickable.property("contentY"))), 1.0
        )
        draft_source = "\n".join(
            [f"draft_{index} = {index}" for index in range(120)]
            + ["print('restored draft')"]
        )
        code_editor.setProperty("text", draft_source)
        QGuiApplication.processEvents()
        self.assertTrue(QMetaObject.invokeMethod(
            view, "activateTab", Q_ARG("QVariant", opened_script["tabId"])
        ))
        self.assertTrue(QMetaObject.invokeMethod(
            view, "activateTab", Q_ARG("QVariant", draft["tabId"])
        ))
        QTest.qWait(30)
        self.assertEqual(source_text_item.property("text"), draft_source)
        controller.shutdown()

        with (
            patch("thlib.ui.script_editor.env_read_config", return_value={}),
            patch("thlib.ui.script_editor.env_write_config"),
        ):
            restored = ScriptEditorController(None, Mock())
        restored._settings = settings
        restored._session_project_code = "default"
        restored._restore_sessions()
        self.assertEqual(
            restored.select_tab(draft["tabId"])["source"],
            draft_source,
        )
        self.assertEqual([
            warning for warning in warnings
            if ("ScriptEditorView.qml" in warning
                or "ScriptCodeEditor.qml" in warning)
        ], [])

        window.close()
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()
        controller.attach_dcc_bridge(None)
        dcc_bridge.deleteLater()
        restored.deleteLater()
        controller.deleteLater()

    def test_delete_sobject_view_renders_legacy_dependency_groups_lazily(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        application = Mock()
        controller = SObjectDeleteController(application)
        source = Mock()
        source.get_search_key.return_value = "prod/asset?code=ASSET001"
        source.get_title.return_value = "Asset 001"
        controller._sources = [source]
        controller._ready = True
        controller.model.reset_records([{
            "searchType": "sthpw/file",
            "searchTypeTitle": "Files",
            "iconName": "file",
            "count": 2,
            "checked": True,
            "defaultChecked": True,
            "expanded": False,
            "items": [
                {"title": "preview.jpg", "details": "publish",
                 "searchKey": "sthpw/file?code=FILE001"},
                {"title": "scene.ma", "details": "model",
                 "searchKey": "sthpw/file?code=FILE002"},
            ],
        }])
        window_model = FloatingWindowModel(MemorySettings())
        engine.rootContext().setContextProperty(
            "sobjectDeleteController", controller
        )
        engine.rootContext().setContextProperty(
            "sobjectDependencyModel", controller.model
        )
        engine.rootContext().setContextProperty("windowModel", window_model)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "DeleteSObjectView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "width": 720,
            "height": 520,
        })
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(720, 520)
        view.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(40)

        targets = view.findChild(QObject, "deleteSObjectTargets")
        dependencies = view.findChild(QObject, "deleteSObjectDependencies")
        header = view.findChild(QObject, "deleteSObjectHeader")
        target_card = view.findChild(QObject, "deleteSObjectTargetCard")
        footer = view.findChild(QObject, "deleteSObjectFooter")
        dependency_repeater = view.findChild(
            QObject, "deleteDependencyRepeater"
        )
        dependency_group, expression_undefined = QQmlExpression(
            QQmlEngine.contextForObject(dependency_repeater),
            dependency_repeater,
            "itemAt(0)",
        ).evaluate()
        self.assertIsNotNone(targets)
        self.assertIsNotNone(dependencies)
        self.assertIsNotNone(header)
        self.assertIsNotNone(target_card)
        self.assertIsNotNone(footer)
        self.assertIsNotNone(dependency_repeater)
        self.assertGreaterEqual(float(header.property("height")), 70.0)
        self.assertGreater(float(target_card.property("radius")), 0.0)
        self.assertEqual(float(dependencies.property("leftPadding")), 6.0)
        self.assertEqual(float(footer.property("height")), 64.0)
        self.assertEqual(dependency_repeater.property("count"), 1)
        self.assertFalse(expression_undefined)
        self.assertIsNotNone(dependency_group)
        self.assertGreater(float(dependency_group.property("radius")), 0.0)
        self.assertEqual(targets.property("count"), 1)
        self.assertTrue(dependencies.property("visible"))
        self.assertTrue(dependency_group.property("checked"))
        dependency_header = dependency_group.findChild(
            QQuickItem, "deleteDependencyHeader_0"
        )
        dependency_check = dependency_group.findChild(
            QQuickItem, "deleteDependencyCheck_0"
        )
        dependency_expand = dependency_group.findChild(
            QQuickItem, "deleteDependencyExpand_0"
        )
        self.assertIsNotNone(dependency_header)
        self.assertIsNotNone(dependency_check)
        self.assertIsNotNone(dependency_expand)
        header_center = dependency_header.mapToItem(
            dependency_group, QPointF(0, dependency_header.height() / 2)
        ).y()
        for item in (dependency_check, dependency_expand):
            item_center = item.mapToItem(
                dependency_group, QPointF(0, item.height() / 2)
            ).y()
            self.assertAlmostEqual(item_center, header_center, delta=0.5)
        self.assertIsNone(
            dependency_group.findChild(QObject, "deleteDependencyItems_0")
        )

        controller.toggle_group(0)
        QTest.qWait(30)

        dependency_items = dependency_group.findChild(
            QObject, "deleteDependencyItems_0"
        )
        QTest.qWait(80)
        dependency_row, row_undefined = QQmlExpression(
            QQmlEngine.contextForObject(dependency_items),
            dependency_items,
            "itemAtIndex(0)",
        ).evaluate()
        dependency_title = dependency_row.findChild(
            QObject, "deleteDependencyItemTitle"
        )
        dependency_details = dependency_row.findChild(
            QObject, "deleteDependencyItemDetails"
        )
        self.assertIsNotNone(dependency_items)
        self.assertFalse(row_undefined)
        self.assertIsNotNone(dependency_row)
        self.assertIsNotNone(dependency_title)
        self.assertIsNotNone(dependency_details)
        self.assertEqual(dependency_items.property("count"), 2)
        self.assertEqual(dependency_title.property("text"), "preview.jpg")
        self.assertEqual(dependency_details.property("text"), "publish")
        last_row, last_row_undefined = QQmlExpression(
            QQmlEngine.contextForObject(dependency_items),
            dependency_items,
            "itemAtIndex(count - 1)",
        ).evaluate()
        self.assertFalse(last_row_undefined)
        self.assertIsNotNone(last_row)
        self.assertGreater(float(last_row.property("bottomLeftRadius")), 0.0)
        self.assertEqual(
            float(last_row.property("bottomLeftRadius")),
            float(last_row.property("bottomRightRadius")),
        )
        list_position = dependency_items.mapToItem(
            dependency_group, QPointF(0, 0)
        )
        self.assertGreaterEqual(list_position.x(), 4.0)
        rendered = window.grabWindow()
        self.assertFalse(rendered.isNull())
        self.assertEqual((rendered.width(), rendered.height()), (720, 520))

        window.close()
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()
        controller.deleteLater()

    def test_shared_date_field_creates(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "controls" / "DateField.qml")),
        )
        raw_value = "2026-08-23 14:35:00"
        field = component.createWithInitialProperties({
            "theme": theme,
            "includeTime": True,
            "text": raw_value,
            "width": 150,
        })
        self.assertIsNotNone(
            field,
            "\n".join(error.toString() for error in component.errors()),
        )
        self.assertEqual(field.property("implicitHeight"), 36.0)
        QGuiApplication.processEvents()
        narrow_text = field.property("presentationText")
        self.assertNotIn("14:35", narrow_text)
        self.assertRegex(narrow_text, r"[^\W\d_]")
        text_input = field.findChild(QObject, "dateFieldTextInput")
        presentation = field.findChild(
            QObject, "dateFieldPresentationLabel"
        )
        self.assertIsNotNone(text_input)
        self.assertIsNotNone(presentation)
        self.assertEqual(text_input.property("text"), raw_value)
        self.assertEqual(presentation.property("text"), narrow_text)

        field.setProperty("width", 360)
        QGuiApplication.processEvents()
        self.assertIn("14:35", field.property("presentationText"))

        window = QQuickWindow()
        window.resize(440, 520)
        field.setParentItem(window.contentItem())
        field.setPosition(QPointF(24, 24))
        window.show()
        QTest.qWait(30)
        calendar_button = field.findChild(
            QQuickItem, "dateFieldCalendarButton"
        )
        calendar_popup = field.findChild(
            QObject, "dateFieldCalendarPopup"
        )
        month_label = field.findChild(QObject, "calendarMonthLabel")
        self.assertIsNotNone(calendar_button)
        self.assertIsNotNone(calendar_popup)
        self.assertIsNotNone(month_label)
        button_center = calendar_button.mapToScene(QPointF(
            calendar_button.width() / 2, calendar_button.height() / 2
        ))
        opened = QSignalSpy(calendar_popup.opened)
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(button_center.x()), round(button_center.y())),
        )
        if not calendar_popup.property("opened"):
            self.assertTrue(opened.wait(1000))
        self.assertTrue(calendar_popup.property("opened"))
        self.assertRegex(month_label.property("text"), r"[^\W\d_]")
        self.assertFalse(window.grabWindow().isNull())

        closed = QSignalSpy(calendar_popup.closed)
        calendar_popup.close()
        if calendar_popup.property("visible"):
            self.assertTrue(closed.wait(1000))
        field_center = field.mapToScene(QPointF(40, field.height() / 2))
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(field_center.x()), round(field_center.y())),
        )
        QGuiApplication.processEvents()
        self.assertTrue(text_input.property("activeFocus"))
        self.assertFalse(presentation.property("visible"))
        self.assertEqual(text_input.property("text"), raw_value)

        window.close()
        window.deleteLater()
        field.deleteLater()
        theme.deleteLater()

    def test_filled_action_button_clips_localized_text_to_its_width(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                qml_dir / "controls" / "FilledActionButton.qml"
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
        content = button.findChild(QObject, "filledActionContent")
        label = button.findChild(QObject, "filledActionLabel")
        self.assertIsNotNone(content)
        self.assertIsNotNone(label)
        self.assertLessEqual(content.property("width"), 78.0)
        self.assertTrue(label.property("truncated"))
        button.setProperty("text", "")
        QTest.qWait(20)
        icon = button.findChild(QObject, "filledActionIcon")
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
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                qml_dir / "controls" / "FilledActionButton.qml"
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
        label = button.findChild(QObject, "filledActionLabel")
        self.assertIsNotNone(label)
        self.assertFalse(label.property("truncated"))
        window.close()
        window.deleteLater()
        button.deleteLater()
        theme.deleteLater()

    def test_shared_editable_controls_use_text_input_cursor(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        cases = (
            ("TextField.qml", "textFieldCursorArea", {}),
            ("TextArea.qml", "textAreaCursorArea", {}),
            ("SpinBox.qml", "spinBoxCursorHandler", {}),
            ("ComboBox.qml", "comboBoxCursorHandler", {
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
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        cases = (
            ("Button.qml", "buttonCursorHandler"),
            ("CheckBox.qml", "checkBoxCursorHandler"),
            ("Switch.qml", "switchCursorHandler"),
            ("TabButton.qml", "tabButtonCursorHandler"),
            ("Slider.qml", "sliderCursorHandler"),
            ("ComboBox.qml", "comboBoxCursorHandler"),
            ("CompactIconButton.qml", "compactIconButtonHoverHandler"),
            ("ItemCountActionButton.qml", "compactIconButtonHoverHandler"),
            ("PreviewNavigationButton.qml", "previewNavigationCursorArea"),
            ("FilledActionButton.qml", "filledActionCursorArea"),
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
            cursor_shape = cursor_target.property("cursorShape")
            cursor_value = (
                cursor_shape.value
                if hasattr(cursor_shape, "value") else int(cursor_shape)
            )
            self.assertEqual(
                cursor_value, Qt.PointingHandCursor.value, file_name,
            )
            control.setProperty("enabled", False)
            QGuiApplication.processEvents()
            disabled_cursor = cursor_target.property("cursorShape")
            disabled_cursor_value = (
                disabled_cursor.value
                if hasattr(disabled_cursor, "value")
                else int(disabled_cursor)
            )
            self.assertEqual(
                disabled_cursor_value,
                Qt.PointingHandCursor.value,
                f"{file_name} disabled",
            )
            self.assertTrue(
                cursor_target.property("enabled"),
                f"{file_name} cursor handler disabled with the button",
            )
            control.deleteLater()
        theme.deleteLater()

    def test_highlighted_destructive_button_uses_error_contrast(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "controls" / "Button.qml")),
        )
        control = component.createWithInitialProperties({
            "theme": theme,
            "text": "Delete",
            "destructive": True,
            "highlighted": True,
        })
        self.assertIsNotNone(
            control,
            "\n".join(error.toString() for error in component.errors()),
        )
        background = control.property("background")
        self.assertEqual(
            background.property("color").toRgb().rgba(),
            theme.property("error").toRgb().rgba(),
        )
        self.assertEqual(
            control.property("contentColor").toRgb().rgba(),
            theme.property("onError").toRgb().rgba(),
        )
        control.deleteLater()
        theme.deleteLater()

    def test_item_count_action_reuses_compact_badge_button(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                qml_dir / "controls" / "ItemCountActionButton.qml"
            )),
        )
        control = component.createWithInitialProperties({
            "theme": theme,
            "iconName": "comment",
            "count": 4,
            "toolTip": "Open notes",
        })
        self.assertIsNotNone(
            control,
            "\n".join(error.toString() for error in component.errors()),
        )
        compact = control.findChild(QObject, "itemCountCompactButton")
        self.assertIsNotNone(compact)
        self.assertTrue(compact.property("round"))
        self.assertEqual(compact.property("badgeCount"), 4)
        self.assertEqual(compact.property("iconName"), "comment")
        self.assertEqual(compact.property("toolTip"), "Open notes")
        control.setProperty("toolTipsAllowed", False)
        QGuiApplication.processEvents()
        self.assertEqual(compact.property("toolTip"), "")
        control.deleteLater()
        theme.deleteLater()

    def test_dock_workspace_footer_keeps_rounded_bottom_corners(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                qml_dir / "controls" / "DockWorkspaceFooter.qml"
            )),
        )
        footer = component.createWithInitialProperties({
            "theme": theme,
            "width": 320,
        })
        self.assertIsNotNone(
            footer,
            "\n".join(error.toString() for error in component.errors()),
        )
        expected_radius = max(
            0.0, float(theme.property("surfaceRadius")) - 1.0
        )
        self.assertEqual(
            float(footer.property("height")),
            float(theme.property("dockWorkspaceFooterHeight")),
        )
        divider = footer.findChild(
            QObject, "dockWorkspaceFooterDivider"
        )
        self.assertIsNotNone(divider)
        self.assertTrue(divider.property("visible"))
        self.assertEqual(float(divider.property("height")), 1.0)
        self.assertAlmostEqual(float(footer.property("radius")), expected_radius)
        self.assertEqual(float(footer.property("topLeftRadius")), 0.0)
        self.assertEqual(float(footer.property("topRightRadius")), 0.0)
        self.assertAlmostEqual(
            float(footer.property("bottomLeftRadius")), expected_radius
        )
        self.assertAlmostEqual(
            float(footer.property("bottomRightRadius")), expected_radius
        )

        window = QQuickWindow()
        window.setColor(QColor("#ff00ff"))
        window.resize(320, 58)
        footer.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(30)
        image = window.grabWindow()
        self.assertFalse(image.isNull())
        bottom_corner = image.pixelColor(0, image.height() - 1)
        bottom_center = image.pixelColor(image.width() // 2, image.height() - 1)
        top_corner = image.pixelColor(0, 0)
        self.assertGreater(bottom_corner.red(), 200)
        self.assertGreater(bottom_corner.blue(), 200)
        self.assertNotEqual(bottom_center.name(), bottom_corner.name())
        self.assertNotEqual(top_corner.name(), bottom_corner.name())
        window.close()
        window.deleteLater()
        footer.deleteLater()
        theme.deleteLater()

    def test_dock_panel_retains_content_between_all_activations(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        engine.rootContext().setContextProperty(
            "dockModel", DockPanelModel({})
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine)
        component.setData(b"""
            import QtQuick
            Item {
                id: probe
                required property var theme
                property bool panelIsOpen: true
                property int panelStackSize: 1
                property int creationCount: 0
                width: 640
                height: 480

                Item {
                    id: fakeHost
                    anchors.fill: parent
                    property bool windowResizeActive: false
                    property bool dockResizeActive: false
                    function beginDockDrag(panelId) {}
                    function updateDockDrag(
                        panelId, pointerX, pointerY) {}
                    function finishDockDrag(
                        panelId, x, y, width, height) {}
                    function beginDockResize() {}
                    function endDockResize() {}
                }

                DockPanel {
                    anchors.fill: parent
                    host: fakeHost
                    theme: probe.theme
                    panelId: "lifecycle_probe"
                    title: "Lifecycle probe"
                    kind: "description"
                    panelX: 0
                    panelY: 0
                    panelWidth: 1
                    panelHeight: 1
                    modelVisible: probe.panelIsOpen
                    panelOpen: probe.panelIsOpen
                    stackActive: probe.panelIsOpen
                    closable: true
                    stackOrder: 1
                    dockArea: "right"
                    canResizeLeft: false
                    canResizeRight: false
                    canResizeTop: false
                    canResizeBottom: false
                    stackPanels: []
                    stackSize: probe.panelStackSize
                    contentComponent: Component {
                        Item {
                            objectName: "retainedDockContentProbe"
                            Component.onCompleted:
                                probe.creationCount += 1
                        }
                    }
                }
            }
        """, QUrl.fromLocalFile(str(qml_dir / "DockLifecycleProbe.qml")))
        probe = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            probe,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(640, 480)
        probe.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(120)

        loader = probe.findChild(
            QObject, "dockPanelContentLoader_lifecycle_probe"
        )
        release_timer = probe.findChild(
            QObject, "dockPanelContentRelease_lifecycle_probe"
        )
        first_content = probe.findChild(
            QObject, "retainedDockContentProbe"
        )
        self.assertIsNotNone(loader)
        self.assertIsNone(release_timer)
        self.assertTrue(loader.property("asynchronous"))
        self.assertIsNotNone(first_content)
        self.assertEqual(probe.property("creationCount"), 1)

        probe.setProperty("panelIsOpen", False)
        QTest.qWait(30)
        self.assertTrue(loader.property("active"))
        self.assertEqual(
            probe.findChild(QObject, "retainedDockContentProbe"),
            first_content,
        )

        probe.setProperty("panelIsOpen", True)
        QTest.qWait(30)
        self.assertEqual(probe.property("creationCount"), 1)
        self.assertEqual(
            probe.findChild(QObject, "retainedDockContentProbe"),
            first_content,
        )

        probe.setProperty("panelStackSize", 2)
        probe.setProperty("panelIsOpen", False)
        QTest.qWait(30)
        self.assertTrue(loader.property("active"))
        self.assertEqual(
            probe.findChild(QObject, "retainedDockContentProbe"),
            first_content,
        )

        window.close()
        window.deleteLater()
        probe.deleteLater()
        theme.deleteLater()

    def test_all_dock_views_reuse_the_shared_bottom_surface(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        dock_views = (
            "SearchWorkspaceView.qml",
            "SnapshotBrowser.qml",
            "TasksWorkspaceView.qml",
            "TaskProcessPanel.qml",
            "TaskBrowserTable.qml",
            "TaskGanttView.qml",
            "TaskCalendarView.qml",
            "TimesheetView.qml",
            "WorkReportsView.qml",
            "CostReportsView.qml",
            "DescriptionEditor.qml",
            "CommunicationView.qml",
            "DropPlateView.qml",
            "AdvancedSearchView.qml",
            "RepositorySyncView.qml",
            "CommitQueueView.qml",
            "DatabaseEditorView.qml",
            "WatchFoldersView.qml",
        )
        for file_name in dock_views:
            with self.subTest(file_name=file_name):
                source = (qml_dir / file_name).read_text(encoding="utf-8")
                self.assertIn("Controls.DockWorkspaceFooter", source)

    def test_expanded_task_editor_exposes_optional_task_fields(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
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
            QObject, "spinBoxTextInput"
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
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
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
            import "controls" as Controls
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
                    delegate: Controls.ComboBox {
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

    def test_task_table_virtualizes_two_hundred_lightweight_rows(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        application = FakeApplication()
        controller = TasksController(application)
        controller.open_workspace()
        base = dict(controller.table_model._records[0])
        records = []
        for index in range(240):
            record = dict(base)
            record.update({
                "taskCode": f"TASK{index:05d}",
                "parentTitle": f"Asset {index:05d}",
                "selected": False,
                "checked": False,
                "group": "",
                "groupKey": "",
                "groupCount": 0,
                "groupFirst": False,
                "groupCollapsed": False,
            })
            records.append(record)
        controller.table_model.reset_records(records)

        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ))
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
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "TaskBrowserTable.qml")),
        )
        table = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            table,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(1400, 640)
        table.setParentItem(window.contentItem())
        table.setProperty("width", 1400)
        table.setProperty("height", 640)
        window.show()
        QTest.qWait(80)

        task_list = table.findChild(QObject, "taskBrowserList")
        self.assertIsNotNone(task_list)
        self.assertEqual(task_list.property("count"), 240)
        self.assertGreater(float(task_list.property("height")), 0)
        self.assertGreater(float(task_list.property("contentHeight")), 0)
        self.assertGreater(task_list.property("liveDelegateCount"), 0)
        self.assertLess(task_list.property("liveDelegateCount"), 40)
        presentation = table.findChild(
            QObject, "initialTaskTablePresentation"
        )
        self.assertIsNotNone(presentation)
        self.assertTrue(presentation.property("ready"))
        controller._advanced_busy = True
        controller.advancedChanged.emit()
        QGuiApplication.processEvents()
        self.assertFalse(presentation.property("ready"))
        self.assertEqual(task_list.property("opacity"), 0)
        controller._advanced_busy = False
        controller.advancedChanged.emit()
        QTest.qWait(30)
        self.assertTrue(presentation.property("ready"))
        self.assertEqual(task_list.property("opacity"), 1)
        timer_count = sum(
            child.metaObject().className().startswith("QQmlTimer")
            for child in table.findChildren(QObject)
        )
        self.assertLessEqual(timer_count, 20)
        self.assertEqual(
            len(table.findChildren(QObject, "taskEditorReleaseCoordinator")),
            1,
        )

        window.resize(1000, 640)
        table.setProperty("width", 1000)
        QTest.qWait(20)
        status_header = table.findChild(QObject, "taskStatusHeader")
        assignee_header = table.findChild(QObject, "taskAssigneeHeader")
        progress_header = table.findChild(QObject, "taskProgressHeader")
        self.assertIsNotNone(status_header)
        self.assertIsNotNone(assignee_header)
        self.assertIsNotNone(progress_header)
        context_spy = QSignalSpy(table.columnContextRequested)
        status_center = status_header.mapToScene(QPointF(
            float(status_header.property("width")) / 2.0,
            float(status_header.property("height")) / 2.0,
        ))
        QTest.mouseClick(
            window,
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(status_center.x()), round(status_center.y())),
        )
        QGuiApplication.processEvents()
        self.assertEqual(context_spy.count(), 1)
        self.assertEqual(context_spy.at(0)[1], "status")
        self.assertGreater(
            float(status_header.property("width")),
            float(table.property("statusColumnWidth")),
        )
        self.assertGreater(
            float(assignee_header.property("width")),
            float(table.property("assigneeColumnWidth")),
        )
        self.assertLessEqual(
            float(progress_header.property("width")),
            float(table.property("progressColumnWidth")) + 0.5,
        )

        maximum_y = max(
            0.0,
            float(task_list.property("contentHeight"))
            - float(task_list.property("height")),
        )
        task_list.setProperty("contentY", maximum_y)
        QGuiApplication.processEvents()
        self.assertFalse(task_list.property("hoverEditorsEnabled"))
        QTest.qWait(80)
        self.assertLess(task_list.property("liveDelegateCount"), 40)
        self.assertFalse(task_list.property("hoverEditorsEnabled"))
        QTest.qWait(140)
        self.assertTrue(task_list.property("hoverEditorsEnabled"))

        window.close()
        window.deleteLater()
        table.deleteLater()
        theme.deleteLater()

    def test_task_table_notes_button_keeps_presented_inspector_stable(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        application = FakeApplication()
        application.dock_model = DockPanelModel({})
        controller = TasksController(application)
        controller.open_workspace()
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ))
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
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "TaskBrowserTable.qml")),
        )
        table = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            table,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(1400, 640)
        table.setParentItem(window.contentItem())
        table.setProperty("width", 1400)
        table.setProperty("height", 640)
        window.show()
        QTest.qWait(80)
        task_list = table.findChild(QQuickItem, "taskBrowserList")
        self.assertIsNotNone(task_list)
        QMetaObject.invokeMethod(task_list, "forceLayout")
        QTest.qWait(40)

        visual_items = [table]
        for item in visual_items:
            visual_items.extend(item.childItems())
        note_buttons = [
            item for item in visual_items
            if item.objectName() == "itemCountCompactButton"
        ]
        note_button = next((
            button for button in note_buttons
            if button.property("visible")
            and button.property("enabled")
            and button.property("toolTip") == "Open notes"
        ), None)
        self.assertIsNotNone(note_button, {
            "list": {
                "count": task_list.property("count"),
                "width": task_list.width(),
                "height": task_list.height(),
                "contentHeight": task_list.property("contentHeight"),
            },
            "buttons": [{
                "class": button.metaObject().className(),
                "visible": button.property("visible"),
                "enabled": button.property("enabled"),
                "toolTip": button.property("toolTip"),
            }
            for button in note_buttons
        ]})
        before = application.dock_model.capture_layout()
        layout_changes = QSignalSpy(
            application.dock_model.minimumHostSizeChanged
        )
        selection_changes = QSignalSpy(
            application.workspace_state.selection_changed
        )
        center = note_button.mapToScene(QPointF(
            note_button.width() / 2.0, note_button.height() / 2.0,
        ))

        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        QGuiApplication.processEvents()

        self.assertEqual(selection_changes.count(), 0)
        self.assertEqual(layout_changes.count(), 0)
        self.assertEqual(application.dock_model.capture_layout(), before)
        window.close()
        window.deleteLater()
        table.deleteLater()
        theme.deleteLater()

    def test_task_table_editor_control_is_created_only_on_demand(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine)
        component.setData(b"""
            import QtQuick
            import "controls" as Controls
            Item {
                id: root
                required property var theme
                property bool editorActive: false
                width: 180
                height: 32
                function clearEditorSource() {
                    editorCell.editorComponent = null
                }
                function restoreEditorSource() {
                    editorCell.editorComponent = editorDefinition
                }
                TaskEditorReleaseCoordinator {
                    id: releaseCoordinator
                    theme: root.theme
                }
                TaskTableEditorCell {
                    id: editorCell
                    anchors.fill: parent
                    theme: root.theme
                    releaseCoordinator: releaseCoordinator
                    editorActive: root.editorActive
                    actionField: true
                    showAccent: true
                    accentColor: "#33a1fd"
                    displayText: "Ready"
                    editorComponent: Component {
                        id: editorDefinition
                        Controls.ComboBox {
                            objectName: "lazyTaskEditorProbe"
                            theme: root.theme
                            actionField: true
                            model: [
                                {"label": "Ready", "color": "#33a1fd"},
                                {"label": "Done", "color": "#3ca66b"}
                            ]
                            textRole: "label"
                            colorRole: "color"
                            currentIndex: 0
                            Component.onCompleted: {
                                popup.usePopupWindow = false
                                popup.objectName = "lazyTaskEditorPopupProbe"
                            }
                        }
                    }
                }
            }
        """, QUrl.fromLocalFile(str(qml_dir / "LazyTaskEditorProbe.qml")))
        probe = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            probe,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(240, 100)
        probe.setParentItem(window.contentItem())
        probe.setPosition(QPointF(20, 20))
        window.show()
        QTest.qWait(20)
        self.assertIsNone(probe.findChild(QObject, "lazyTaskEditorProbe"))
        cell = probe.findChild(QObject, "taskTableEditorCell")
        self.assertIsNotNone(cell)
        display_label = probe.findChild(
            QQuickItem, "taskTableCellDisplayLabel"
        )
        self.assertIsNotNone(display_label)
        display_position = display_label.mapToScene(QPointF(0, 0))
        probe.setProperty("editorActive", True)
        QGuiApplication.processEvents()
        self.assertIsNotNone(
            probe.findChild(QObject, "lazyTaskEditorProbe")
        )
        editor_label = probe.findChild(
            QQuickItem, "comboBoxDisplayLabel"
        )
        self.assertIsNotNone(editor_label)
        editor_position = editor_label.mapToScene(QPointF(0, 0))
        self.assertAlmostEqual(
            editor_position.x(), display_position.x()
        )
        self.assertAlmostEqual(
            editor_position.y(), display_position.y()
        )
        probe.setProperty("editorActive", False)
        QGuiApplication.processEvents()
        self.assertTrue(QMetaObject.invokeMethod(probe, "clearEditorSource"))
        QGuiApplication.processEvents()
        self.assertTrue(QMetaObject.invokeMethod(probe, "restoreEditorSource"))
        QGuiApplication.processEvents()
        QGuiApplication.processEvents()
        editor_popup = probe.findChild(
            QObject, "lazyTaskEditorPopupProbe"
        )
        self.assertIsNotNone(editor_popup)
        self.assertFalse(editor_popup.property("visible"))
        probe.setProperty("editorActive", True)
        QTest.qWait(20)
        editor = probe.findChild(QQuickItem, "lazyTaskEditorProbe")
        editor_position = editor.mapToScene(QPointF(
            editor.width() / 2, editor.height() / 2
        ))
        QTest.mousePress(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(editor_position.x()), round(editor_position.y())),
        )
        probe.setProperty("editorActive", False)
        QGuiApplication.processEvents()
        self.assertTrue(cell.property("editorLoaded"))
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(editor_position.x()), round(editor_position.y())),
        )
        QTest.qWait(100)
        self.assertTrue(cell.property("editorPopupOpen"))
        self.assertTrue(cell.property("editorLoaded"))
        cell.setProperty("scrolling", True)
        QGuiApplication.processEvents()
        self.assertFalse(cell.property("editorPopupOpen"))
        self.assertFalse(cell.property("editorLoaded"))
        window.close()
        window.deleteLater()
        probe.deleteLater()
        theme.deleteLater()

    def test_task_workspace_creates_with_a_real_record(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        application = FakeApplication()
        application.workspace_state._task_sobjects[0].get_info().update({
            "bid_start_date": "",
            "bid_end_date": "",
        })
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
        engine.rootContext().setContextProperty(
            "taskGanttModel", controller.gantt_model
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
        window = QQuickWindow()
        window.resize(1400, 720)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        QTest.qWait(40)
        self.assertFalse(view.property("compactScopeControls"))
        background_surface = view.findChild(
            QObject, "taskWorkspaceBackgroundSurface"
        )
        self.assertIsNotNone(background_surface)
        expected_corner = theme.property("surfaceRadius") - 1
        self.assertEqual(
            background_surface.property("bottomLeftRadius"), expected_corner
        )
        self.assertEqual(
            background_surface.property("bottomRightRadius"), expected_corner
        )
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
        workspace_surface_switcher = view.findChild(
            QQuickItem, "taskWorkspaceSurfaceSwitcher"
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
        self.assertIsNotNone(workspace_surface_switcher)
        self.assertIsNotNone(sort_combo)
        self.assertIsNotNone(group_combo)
        self.assertEqual(sort_combo.property("iconRole"), "icon")
        self.assertEqual(group_combo.property("iconRole"), "icon")
        self.assertIsNone(view_switcher)
        self.assertIsNotNone(clear_filters_button)
        self.assertIsNotNone(refresh_button)
        self.assertIsNotNone(overflow_button)
        self.assertTrue(workspace_surface_switcher.property("visible"))
        self.assertTrue(sort_combo.property("visible"))
        self.assertTrue(group_combo.property("visible"))
        self.assertTrue(clear_filters_button.property("visible"))
        self.assertTrue(refresh_button.property("visible"))
        self.assertFalse(overflow_button.property("visible"))
        surface_items = [workspace_surface_switcher]
        for item in surface_items:
            surface_items.extend(item.childItems())
        compact_surface = next((
            item for item in surface_items
            if item.objectName() == "segmentedButtonSegment_compact"
        ), None)
        self.assertIsNotNone(compact_surface)
        compact_surface_center = compact_surface.mapToScene(QPointF(
            compact_surface.width() / 2,
            compact_surface.height() / 2,
        ))
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(
                round(compact_surface_center.x()),
                round(compact_surface_center.y()),
            ),
        )
        QGuiApplication.processEvents()
        self.assertEqual(controller.quickViewMode, "compact")
        self.assertEqual(controller.workspaceSurface, "quick")
        controller.open_workspace()
        QGuiApplication.processEvents()
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
        self.assertGreater(
            clear_filters_button.property("x"), quick_filter.property("x")
        )
        self.assertLess(
            clear_filters_button.property("x")
                - quick_filter.property("x")
                - quick_filter.property("width"),
            12,
        )
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
        QTest.qWait(40)
        browser = view.findChild(QQuickItem, "taskBrowserTable")
        self.assertIsNotNone(browser)
        surface_slot = view.findChild(
            QQuickItem, "taskWorkspaceSurfaceSlot"
        )
        surface_loader = view.findChild(
            QQuickItem, "taskWorkspaceSurfaceLoader"
        )
        table_header = browser.findChild(QQuickItem, "taskTableHeader")
        persistent_footer = view.findChild(
            QQuickItem, "taskWorkspacePersistentFooter"
        )
        self.assertIsNotNone(surface_slot)
        self.assertIsNotNone(surface_loader)
        self.assertIsNotNone(table_header)
        self.assertIsNotNone(persistent_footer)
        toolbar_top = toolbar.mapToScene(QPointF(0, 0)).y()
        toolbar_bottom = toolbar.mapToScene(QPointF(
            0, float(toolbar.property("height"))
        )).y()
        slot_top = surface_slot.mapToScene(QPointF(0, 0)).y()
        browser_top = browser.mapToScene(QPointF(0, 0)).y()
        self.assertAlmostEqual(toolbar_top, 0.0, delta=0.5)
        self.assertAlmostEqual(slot_top, toolbar_bottom + 5.0, delta=0.5)
        self.assertAlmostEqual(browser_top, slot_top, delta=0.5)
        self.assertAlmostEqual(
            float(browser.property("width")),
            float(surface_slot.property("width")),
            delta=0.5,
        )
        self.assertAlmostEqual(
            float(browser.property("height")),
            float(surface_slot.property("height")),
            delta=0.5,
        )
        self.assertTrue(table_header.property("visible"))
        self.assertEqual(float(table_header.property("height")), 34.0)
        stable_slot_geometry = (
            slot_top,
            float(surface_slot.property("width")),
            float(surface_slot.property("height")),
        )
        stable_footer_top = persistent_footer.mapToScene(
            QPointF(0, 0)
        ).y()
        self.assertIsNone(
            view.findChild(QObject, "taskDeleteConfirmationDialog")
        )
        self.assertIsNotNone(
            browser.findChild(QObject, "taskBulkDeleteButton")
        )
        self.assertIsNone(
            view.findChild(QObject, "ganttDeleteSelectedTasksButton")
        )
        status_context_area = browser.findChild(
            QObject, "taskColumnContextArea_status"
        )
        self.assertIsNotNone(status_context_area)
        status_header = browser.findChild(QObject, "taskStatusHeader")
        self.assertIsNotNone(status_header)
        status_center = status_header.mapToScene(QPointF(
            float(status_header.property("width")) / 2.0,
            float(status_header.property("height")) / 2.0,
        ))
        QTest.mouseClick(
            window,
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(status_center.x()), round(status_center.y())),
        )
        column_menu = view.findChild(QObject, "taskColumnContextMenu")
        self.assertIsNotNone(column_menu)
        opened = QSignalSpy(column_menu.opened)
        if not column_menu.property("opened"):
            self.assertTrue(opened.wait(1000))
        self.assertEqual(view.property("taskColumnContextKey"), "status")
        self.assertTrue(column_menu.property("opened"))
        column_actions = column_menu.property("actions").toVariant()
        commands = {
            item.get("command") for item in column_actions
            if isinstance(item, dict) and item.get("command")
        }
        self.assertTrue({
            "sort:ascending", "sort:descending", "group",
            "ungroup", "hide", "columns", "configure",
        }.issubset(commands))
        column_menu.close()
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
        QTest.qWait(60)
        workspace_mode_switcher = view.findChild(
            QQuickItem, "taskWorkspaceModeSwitcher"
        )
        self.assertIsNotNone(workspace_mode_switcher)
        self.assertTrue(workspace_mode_switcher.property("visible"))
        calendar_button = view.findChild(QQuickItem, "taskCalendarButton")
        self.assertIsNotNone(calendar_button)
        surface_right = workspace_surface_switcher.mapToScene(QPointF(
            workspace_surface_switcher.width(), 0
        )).x()
        refresh_left = refresh_button.mapToScene(QPointF(0, 0)).x()
        refresh_right = refresh_button.mapToScene(QPointF(
            refresh_button.property("width"), 0
        )).x()
        self.assertLess(surface_right, refresh_left)
        self.assertLess(refresh_left - surface_right, 12)
        self.assertAlmostEqual(
            view.property("width") - surface_right, 49.0, delta=1.0
        )
        overflow_right = overflow_button.mapToScene(QPointF(
            overflow_button.property("width"), 0
        )).x()
        surface_left = workspace_surface_switcher.mapToScene(
            QPointF(0, 0)
        ).x()
        self.assertLess(overflow_right, surface_left)
        mode_top = workspace_mode_switcher.mapToScene(QPointF(0, 0)).y()
        self.assertGreater(
            mode_top,
            float(view.property("height"))
                - float(theme.property("dockWorkspaceFooterHeight")) - 12,
        )
        mode_segments = [workspace_mode_switcher]
        for item in mode_segments:
            mode_segments.extend(item.childItems())
        gantt_segment = next((
            item for item in mode_segments
            if item.objectName() == "segmentedButtonSegment_gantt"
        ), None)
        self.assertIsNotNone(gantt_segment)
        gantt_center = gantt_segment.mapToScene(QPointF(
            gantt_segment.width() / 2, gantt_segment.height() / 2
        ))
        gantt_surface_loader = view.findChild(
            QQuickItem, "taskWorkspaceGanttSurfaceLoader"
        )
        self.assertIsNotNone(gantt_surface_loader)
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(gantt_center.x()), round(gantt_center.y())),
        )
        QGuiApplication.processEvents()
        self.assertGreaterEqual(
            float(surface_loader.property("opacity"))
                + float(gantt_surface_loader.property("opacity")),
            0.95,
        )
        self.assertAlmostEqual(
            persistent_footer.mapToScene(QPointF(0, 0)).y(),
            stable_footer_top,
            delta=0.5,
        )
        QTest.qWait(140)
        calendar_center = calendar_button.mapToScene(QPointF(
            calendar_button.width() / 2, calendar_button.height() / 2
        ))
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(calendar_center.x()), round(calendar_center.y())),
        )
        self.assertEqual(
            application.dock_model.opened[-1], "task_calendar"
        )
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
        gantt_list = view.findChild(QQuickItem, "ganttTaskList")
        self.assertIsNotNone(gantt_list)
        self.assertIs(view.findChild(QQuickItem, "taskBrowserTable"), browser)
        self.assertTrue(gantt_surface_loader.property("active"))
        self.assertAlmostEqual(
            float(gantt_surface_loader.property("opacity")), 1.0, delta=0.01
        )
        self.assertAlmostEqual(
            float(surface_loader.property("opacity")), 0.0, delta=0.01
        )
        self.assertAlmostEqual(
            persistent_footer.mapToScene(QPointF(0, 0)).y(),
            stable_footer_top,
            delta=0.5,
        )
        self.assertAlmostEqual(
            toolbar.mapToScene(QPointF(0, 0)).y(), 0.0, delta=0.5
        )
        self.assertAlmostEqual(
            surface_slot.mapToScene(QPointF(0, 0)).y(),
            stable_slot_geometry[0],
            delta=0.5,
        )
        self.assertGreater(float(gantt_list.property("width")), 0.0)
        self.assertGreater(float(gantt_list.property("height")), 0.0)
        QMetaObject.invokeMethod(gantt_list, "forceLayout")
        QTest.qWait(40)
        visual_items = [gantt_list]
        for visual_item in visual_items:
            visual_items.extend(visual_item.childItems())
        unscheduled_chip = next((
            item for item in visual_items
            if item.objectName() == "ganttUnscheduledIssueChip"
        ), None)
        unscheduled_label = next((
            item for item in visual_items
            if item.objectName() == "ganttUnscheduledIssueLabel"
        ), None)
        self.assertIsNotNone(unscheduled_chip, {
            "count": gantt_list.property("count"),
            "visible": gantt_list.property("visible"),
            "width": gantt_list.property("width"),
            "height": gantt_list.property("height"),
            "contentHeight": gantt_list.property("contentHeight"),
            "records": list(controller.gantt_model._records),
        })
        self.assertIsNotNone(unscheduled_label)
        self.assertTrue(unscheduled_chip.property("visible"))
        self.assertEqual(
            unscheduled_label.property("text"),
            "Start and deadline are not set",
        )
        self.assertEqual(unscheduled_chip.property("height"), 30.0)
        self.assertGreaterEqual(
            float(unscheduled_label.property("width")) + 0.5,
            float(unscheduled_label.property("implicitWidth")),
        )
        view.setProperty("width", 900)
        QGuiApplication.processEvents()
        self.assertTrue(workspace_surface_switcher.property("visible"))
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
        self.assertFalse(workspace_mode_switcher.property("visible"))
        self.assertTrue(workspace_surface_switcher.property("visible"))
        self.assertFalse(clear_filters_button.property("visible"))
        self.assertTrue(search_field.property("visible"))
        self.assertFalse(quick_filter.property("visible"))
        self.assertTrue(refresh_button.property("visible"))
        trailing_actions = view.findChild(
            QQuickItem, "taskWorkspaceTrailingActions"
        )
        primary_actions = view.findChild(
            QQuickItem, "taskWorkspacePrimaryActions"
        )
        compact_scope_button = view.findChild(
            QQuickItem, "compactScopeButton"
        )
        self.assertIsNotNone(trailing_actions)
        self.assertIsNotNone(primary_actions)
        self.assertIsNotNone(compact_scope_button)
        for toolbar_width in (
                320, 380, 440, 500, 520, 720, 840, 1279, 1360, 1400):
            view.setProperty("width", toolbar_width)
            QTest.qWait(20)
            refresh_right = refresh_button.mapToScene(QPointF(
                refresh_button.width(), 0
            )).x()
            trailing_left = trailing_actions.mapToScene(QPointF(0, 0)).x()
            primary_right = primary_actions.mapToScene(QPointF(
                primary_actions.width(), 0
            )).x()
            self.assertLessEqual(
                refresh_right,
                float(toolbar_width),
                f"refresh escaped at {toolbar_width}px",
            )
            self.assertGreaterEqual(
                trailing_left, 0.0,
                f"trailing actions escaped at {toolbar_width}px",
            )
            self.assertLessEqual(primary_right, trailing_left + 0.5)
            self.assertTrue(search_field.property("visible"))
            search_left = search_field.mapToScene(QPointF(0, 0)).x()
            search_right = search_field.mapToScene(QPointF(
                search_field.width(), 0
            )).x()
            create_right = create_task_button.mapToScene(QPointF(
                create_task_button.width(), 0
            )).x()
            self.assertGreaterEqual(search_left, create_right)
            self.assertLessEqual(
                search_right, trailing_left + 0.5,
                f"search overlapped trailing actions at {toolbar_width}px",
            )
            self.assertGreater(float(search_field.property("width")), 0.0)
            if toolbar_width < 520:
                self.assertEqual(
                    compact_scope_button.property("visible"),
                    toolbar_width >= 380,
                )
                if compact_scope_button.property("visible"):
                    compact_left = compact_scope_button.mapToScene(
                        QPointF(0, 0)
                    ).x()
                    compact_right = compact_scope_button.mapToScene(QPointF(
                        compact_scope_button.width(), 0
                    )).x()
                    self.assertLessEqual(
                        compact_left - create_right, 8.0
                    )
                    self.assertLessEqual(
                        search_left - compact_right, 8.0
                    )
        view.setProperty("embedded", False)
        for toolbar_width in (760, 900, 1180):
            view.setProperty("width", toolbar_width)
            QTest.qWait(20)
            refresh_right = refresh_button.mapToScene(QPointF(
                refresh_button.width(), 0
            )).x()
            trailing_left = trailing_actions.mapToScene(QPointF(0, 0)).x()
            self.assertLessEqual(
                refresh_right,
                float(toolbar_width),
                {
                    "requestedWidth": toolbar_width,
                    "viewWidth": view.property("width"),
                    "trailingX": trailing_left,
                    "trailingWidth": trailing_actions.width(),
                    "refreshX": refresh_button.mapToScene(
                        QPointF(0, 0)
                    ).x(),
                },
            )
            self.assertGreaterEqual(trailing_left, 0.0)
        view.setProperty("embedded", True)
        controller.set_view_mode("list")
        view.setProperty("width", 1400)
        QTest.qWait(80)
        browser = view.findChild(QObject, "taskBrowserTable")
        self.assertIsNotNone(browser)
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
        QGuiApplication.processEvents()
        expanded = browser.property("expandedTaskDetails").toVariant()
        self.assertNotIn(draft_code, expanded)
        window.close()
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()

    def test_task_calendar_creates_at_minimum_dock_size(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        controller = TasksController(FakeApplication())
        controller.use_current_object()
        controller.set_calendar_visible(True)
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
