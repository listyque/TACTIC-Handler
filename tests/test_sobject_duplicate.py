from __future__ import annotations

import os
from pathlib import Path
import json
import sys
import textwrap
from types import ModuleType
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

import thlib.tactic_classes as tc
import thlib.tactic_query as tq
from thlib.environment import env_inst
from thlib.ui.sobject_duplicate import (
    SObjectDuplicateController,
    apply_duplicate_profile,
)
from thlib.ui.controllers.item_actions import ItemActionsMixin
from thlib.ui.workspace_models.windows import FloatingWindowModel
from tests.qt_application import gui_test_application
from tests.support.async_scenarios import DeferredWorker, MemorySettings


class _Project:
    def get_code(self):
        return "demo"


class _SType:
    def get_project(self):
        return _Project()

    def get_column_data_type(self, _name):
        return "text"


class _Source:
    def get_search_key(self):
        return "prod/asset?project=demo&code=ASSET001"

    def get_plain_search_type(self):
        return "prod/asset"

    def get_stype(self):
        return _SType()

    def get_info(self):
        return {"name": "Asset 001", "description": "Original"}

    def get_value(self, name):
        return self.get_info().get(name)


class _WindowModel:
    def __init__(self):
        self.shown = []
        self.closed = []

    def show_window(self, window_id):
        self.shown.append(window_id)

    def close_window(self, window_id):
        self.closed.append(window_id)


class _Application:
    def __init__(self):
        self.window_model = _WindowModel()
        self.notifications = []
        self.refreshes = 0

    def _notify(self, message):
        self.notifications.append(str(message))

    def refresh_current(self):
        self.refreshes += 1


class _Pool:
    is_stopped = False

    def __init__(self):
        self.calls = []
        self.workers = []

    def start(self):
        self.is_stopped = False

    def add_task(self, operation, *args):
        self.calls.append((operation, args))
        worker = DeferredWorker(operation)
        self.workers.append(worker)
        return worker


def _analysis_payload():
    return {
        "searchKey": "prod/asset?project=demo&code=ASSET001",
        "searchType": "prod/asset",
        "projectCode": "demo",
        "title": "Asset 001",
        "fields": [
            {
                "name": "name", "label": "Name", "value": "Asset 001",
                "originalValue": "Asset 001", "dataType": "str",
                "multiline": False,
            },
            {
                "name": "description", "label": "Description",
                "value": "Original", "originalValue": "Original",
                "dataType": "str", "multiline": True,
            },
        ],
        "relations": [{
            "key": "instance|prod/tag|prod/asset_in_tag|",
            "direction": "children", "kind": "instance",
            "relationship": "instance", "searchType": "prod/tag",
            "title": "Tags", "count": 2, "mode": "link",
            "defaultMode": "link", "localColumn": "", "path": "",
            "instanceType": "prod/asset_in_tag",
            "options": [
                {"value": "none", "label": "Do not copy"},
                {"value": "link", "label": "Keep links"},
            ],
            "items": [{"title": "Hero"}, {"title": "Featured"}],
        }],
        "processes": [{
            "name": "model", "snapshotCount": 2, "fileCount": 3,
            "taskCount": 1, "processMessageCount": 4,
            "taskMessageCount": 2, "processAttachmentCount": 1,
            "taskAttachmentCount": 2, "copySnapshots": False,
            "copyTasks": False, "copyProcessMessages": False,
            "copyTaskMessages": False,
            "copyProcessAttachments": False,
            "copyTaskAttachments": False,
        }],
    }


class SObjectDuplicateControllerTests(unittest.TestCase):
    def test_first_page_uses_the_edit_view_field_catalog(self):
        application = _Application()
        pool = _Pool()
        edit_view = {
            "InputWidgets": [{
                "name": "name",
                "title": "Display name",
                "class_name": "pyasm.widget.input_wdg.TextWdg",
                "kwargs": {},
                "action_options": {"column": "name"},
            }],
        }
        with patch(
            "thlib.ui.sobject_duplicate.env_read_config",
            return_value={},
        ), patch.object(env_inst, "server_pool", pool), patch.object(
            tc, "analyze_sobject_duplicate", return_value=_analysis_payload()
        ), patch.object(
            tc, "execute_procedure_serverside", return_value=edit_view
        ) as edit_query:
            controller = SObjectDuplicateController(application)
            self.assertTrue(controller.begin(_Source()))
            operation, args = pool.calls[0]
            self.assertEqual(args, ())
            pool.workers[0].resolve(operation())

        field = controller.fields.get(0)
        self.assertEqual(field["fieldName"], "name")
        self.assertEqual(field["title"], "Display name")
        self.assertEqual(field["fieldType"], "string")
        self.assertEqual(
            field["widgetClass"], "pyasm.widget.input_wdg.TextWdg"
        )
        edit_query.assert_called_once()

    def test_profile_applies_only_valid_relation_and_process_choices(self):
        payload = _analysis_payload()
        relations, processes = apply_duplicate_profile(
            payload["relations"], payload["processes"], {
                "relations": {
                    "instance|prod/tag|prod/asset_in_tag|": "none",
                },
                "processes": {
                    "model": {
                        "copySnapshots": True,
                        "copyTaskMessages": True,
                        "copyTaskAttachments": True,
                    },
                },
                "fields": {"name": "Stale name must be ignored"},
            },
        )

        self.assertEqual(relations[0]["mode"], "none")
        self.assertTrue(processes[0]["copySnapshots"])
        self.assertTrue(processes[0]["copyTaskMessages"])
        self.assertTrue(processes[0]["copyTaskAttachments"])
        self.assertTrue(processes[0]["copyTasks"])
        self.assertEqual(payload["fields"][0]["value"], "Asset 001")

    def test_analysis_failure_releases_busy_state_and_can_retry(self):
        application = _Application()
        pool = _Pool()
        with patch(
            "thlib.ui.sobject_duplicate.env_read_config",
            return_value={},
        ), patch.object(env_inst, "server_pool", pool):
            controller = SObjectDuplicateController(application)
            self.assertTrue(controller.begin(_Source()))
            pool.workers[0].reject(RuntimeError("Analysis failed"))

            self.assertFalse(controller.busy)
            self.assertFalse(controller.ready)
            self.assertEqual(controller.error, "Analysis failed")
            self.assertEqual(application.window_model.closed, [])

            controller.retry()

        self.assertEqual(len(pool.workers), 2)
        self.assertTrue(pool.workers[1].started)
        self.assertTrue(controller.busy)

    def test_controller_analyzes_async_and_builds_explicit_copy_payload(self):
        profile = {
            "demo|prod/asset": {
                "relations": {
                    "instance|prod/tag|prod/asset_in_tag|": "none",
                },
                "processes": {
                    "model": {"copySnapshots": True},
                },
            },
        }
        application = _Application()
        pool = _Pool()
        writes = []
        with patch(
            "thlib.ui.sobject_duplicate.env_read_config",
            return_value=profile,
        ), patch.object(env_inst, "server_pool", pool), patch(
            "thlib.ui.sobject_duplicate.env_write_config",
            side_effect=lambda value, **kwargs: writes.append(
                (value, kwargs)
            ),
        ):
            controller = SObjectDuplicateController(application)
            self.assertTrue(controller.begin(_Source()))
            self.assertEqual(
                application.window_model.shown, ["duplicate_sobject"]
            )
            self.assertTrue(pool.workers[0].started)
            pool.workers[0].resolve(_analysis_payload())

            self.assertTrue(controller.ready)
            self.assertEqual(controller.relations.get(0)["mode"], "none")
            self.assertTrue(
                controller.processes.get(0)["copySnapshots"]
            )
            controller.set_field_value(0, "Asset 001 copy")
            controller.set_relation_mode(0, "link")
            controller.set_process_choice(
                0, "copyTaskAttachments", True
            )

            duplicate = Mock(return_value={
                "searchKey": "prod/asset?project=demo&code=ASSET002"
            })
            with patch.object(
                tc, "duplicate_sobject_advanced", duplicate
            ), patch("thlib.server_cache.invalidate_domains"):
                controller.duplicate()
                self.assertEqual(
                    writes, [],
                    "Duplicate must not write configuration on the UI thread",
                )
                operation, args = pool.calls[1]
                self.assertEqual(args, ())
                result = operation()
                pool.workers[1].resolve(result)

        duplicate.assert_called_once()
        search_key, options = duplicate.call_args.args
        self.assertEqual(search_key, _Source().get_search_key())
        self.assertEqual(options["fields"]["name"], "Asset 001 copy")
        self.assertEqual(
            options["relations"][
                "instance|prod/tag|prod/asset_in_tag|"
            ],
            "link",
        )
        self.assertTrue(options["processes"]["model"]["copyTasks"])
        self.assertTrue(
            options["processes"]["model"]["copyTaskMessages"]
        )
        self.assertTrue(
            options["processes"]["model"]["copyTaskAttachments"]
        )
        self.assertEqual(len(writes), 1)
        saved_profile = writes[0][0]["demo|prod/asset"]
        self.assertNotIn("fields", saved_profile)
        self.assertEqual(application.window_model.closed, [
            "duplicate_sobject"
        ])
        self.assertEqual(application.refreshes, 1)

    def test_quick_duplicate_is_unavailable_until_profile_exists(self):
        application = _Application()
        with patch(
            "thlib.ui.sobject_duplicate.env_read_config",
            return_value={},
        ):
            controller = SObjectDuplicateController(application)

        self.assertFalse(controller.quick_duplicate(_Source()))
        self.assertIn("Open Duplicate", application.notifications[0])

    def test_quick_action_is_published_only_from_cached_profile_state(self):
        class MenuController(ItemActionsMixin):
            def __init__(self, has_profile):
                self.node = SimpleNamespace(
                    node_type="sobject", source=_Source(), preview_url="",
                    children=[], watch_state="none", relationship="",
                )
                self.sobject_duplicate = Mock()
                self.sobject_duplicate.has_profile_for_source.return_value = (
                    has_profile
                )

            def _node_for_any(self, _node_id):
                return self.node

            def _current_tab(self):
                return None

            def _dcc_available(self, _action):
                return False

        without_profile = MenuController(False).item_menu_actions("asset")
        with_profile = MenuController(True).item_menu_actions("asset")

        self.assertNotIn(
            "duplicate_quick",
            {row.get("command") for row in without_profile},
        )
        self.assertIn(
            "duplicate_quick",
            {row.get("command") for row in with_profile},
        )


class SObjectDuplicateServerProcedureTests(unittest.TestCase):
    def test_server_procedures_compile_as_self_contained_scripts(self):
        analysis = tq.prepare_serverside_script(
            tq.analyze_sobject_duplicate,
            {"search_key": "prod/asset?project=demo&code=ASSET001"},
            shrink=False,
            catch_traceback=False,
        )["code"]
        duplicate = tq.prepare_serverside_script(
            tq.duplicate_sobject_advanced,
            {
                "search_key": "prod/asset?project=demo&code=ASSET001",
                "options": {},
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        compile(
            "def execute():\n" + textwrap.indent(analysis, "    "),
            "<analyze_sobject_duplicate>", "exec",
        )
        compile(
            "def execute():\n" + textwrap.indent(duplicate, "    "),
            "<duplicate_sobject_advanced>", "exec",
        )

    def test_analysis_and_copy_use_native_relation_and_checkin_paths(self):
        instance_target = Mock()
        instance_target.get_data.return_value = {
            "code": "TAG001", "name": "Featured"
        }
        instance_target.get_code.return_value = "TAG001"
        child = Mock()
        child.get_data.return_value = {"code": "SHOT001", "name": "Shot"}
        child.get_code.return_value = "SHOT001"
        parent = Mock()
        parent.get_data.return_value = {
            "code": "CATEGORY001", "name": "Characters"
        }
        parent.get_code.return_value = "CATEGORY001"

        class Source:
            def get_base_search_type(self):
                return "prod/asset"

            def get_search_type(self):
                return "prod/asset?project=demo"

            def get_project_code(self):
                return "demo"

            def get_code(self):
                return "ASSET001"

            def get_id(self):
                return 1

            def get_data(self):
                return {
                    "id": 1, "code": "ASSET001", "name": "Hero",
                    "description": None, "category_code": "CATEGORY001",
                }

            def get_related_sobjects(self, related_type, path=None):
                return {
                    "prod/category": [parent],
                    "prod/tag": [instance_target],
                    "prod/shot": [child],
                }.get(related_type, [])

            def get_parent(self, related_type):
                return parent if related_type == "prod/category" else None

        source = Source()

        class NewSObject:
            def __init__(self):
                self.values = {}

            def set_value(self, name, value):
                if value is None:
                    raise ValueError("TACTIC fields do not accept None")
                self.values[name] = value

            def set_json_value(self, name, value):
                self.values[name] = value

            def commit(self):
                self.values["code"] = "ASSET002"

            def get_search_type(self):
                return "prod/asset?project=demo"

            def get_code(self):
                return "ASSET002"

            def get_id(self):
                return 2

        created = NewSObject()

        class InstanceConnection:
            def __init__(self):
                self.related = None
                self.path = None
                self.committed = False

            def add_related_connection(self, source, target, src_path=None):
                self.related = (source, target)
                self.path = src_path

            def commit(self):
                self.committed = True

            def get_code(self):
                return "ASSETINTAG002" if self.committed else ""

            def get_id(self):
                return 102 if self.committed else None

        instance_connection = InstanceConnection()

        task_clone = Mock()
        task_clone.get_code.return_value = "TASK002"
        task_clone.get_id.return_value = 22
        task_clone.get_value.side_effect = lambda name: {
            "process": "model",
        }.get(name)
        task = Mock()
        task.get_code.return_value = "TASK001"
        task.get_id.return_value = 21
        task.get_base_search_type.return_value = "sthpw/task"
        task.get_value.side_effect = lambda name: {
            "process": "model",
        }.get(name)
        task.clone.return_value = task_clone

        process_note = Mock()
        process_note.get_value.side_effect = lambda name: {
            "process": "model", "search_type": "prod/asset",
            "search_code": "ASSET001",
        }.get(name)
        process_note_clone = Mock()
        process_note_clone.get_code.return_value = "NOTE102"
        process_note.copy_note.return_value = process_note_clone
        process_note.get_child_notes.return_value = []
        task_note = Mock()
        task_note.get_value.side_effect = lambda name: {
            "process": "model", "search_type": "sthpw/task",
            "search_code": "TASK001",
        }.get(name)
        task_note_clone = Mock()
        task_note_clone.get_code.return_value = "NOTE202"
        task_note.copy_note.return_value = task_note_clone
        task_note.get_child_notes.return_value = []

        class Schema:
            @staticmethod
            def get(project_code=None):
                return Schema()

            def get_related_search_types(self, search_type, direction=None):
                if direction == "parent":
                    return ["prod/category"]
                return ["prod/tag", "prod/shot"]

            def get_relationship_attrs(self, first, second):
                return {
                    "prod/category": {
                        "relationship": "code", "from": "prod/asset",
                        "to": "prod/category", "from_col": "category_code",
                        "to_col": "code",
                    },
                    "prod/tag": {
                        "relationship": "instance", "from": "prod/asset",
                        "to": "prod/tag", "instance_type": "prod/asset_in_tag",
                    },
                    "prod/shot": {
                        "relationship": "code", "from": "prod/shot",
                        "to": "prod/asset", "from_col": "asset_code",
                        "to_col": "code",
                    },
                }[second]

        class SearchKey:
            @staticmethod
            def get_by_search_key(_search_key):
                return source

            @staticmethod
            def get_by_sobject(item, use_id=False):
                if item is source:
                    return "prod/asset?project=demo&code=ASSET001"
                if item is created:
                    return "prod/asset?project=demo&code=ASSET002"
                return "related?code={}".format(item.get_code())

        class SearchType:
            @staticmethod
            def get_columns(_search_type):
                return [
                    "id", "code", "name", "description", "category_code",
                ]

            @staticmethod
            def create(target_search_type):
                if target_search_type == "prod/asset_in_tag":
                    return instance_connection
                return created

            @staticmethod
            def column_exists(_search_type, _column):
                return False

            @staticmethod
            def get(search_type):
                value = Mock()
                value.get_title.return_value = search_type.rsplit("/", 1)[-1].title()
                return value

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []

            def add_filter(self, name, value, *_args, **_kwargs):
                self.filters.append((name, value))

            def add_filters(self, name, values, *_args, **_kwargs):
                self.filters.append((name, list(values)))

            def add_relationship_filters(
                self, values, *_args, **_kwargs
            ):
                self.filters.append(("relationship", list(values)))

            def get_sobjects(self):
                if self.search_type == "sthpw/snapshot":
                    return [snapshot]
                if self.search_type == "sthpw/task":
                    return [task]
                if self.search_type == "sthpw/note":
                    search_code = next(
                        (value for name, value in self.filters
                         if name == "search_code"),
                        None,
                    )
                    if search_code == "TASK001":
                        return [task_note]
                    return [process_note]
                return []

        class SnapshotObject:
            def __init__(self, code, context, process="model"):
                self.code = code
                self.context = context
                self.process = process

            def get_code(self):
                return self.code

            def get_version(self):
                return 1

            def is_latest(self):
                return True

            def get_value(self, name):
                return {
                    "context": self.context, "process": self.process,
                    "snapshot_type": "file",
                }.get(name)

            def get_all_paths_dict(self):
                return {
                    "SNAPSHOT001": {
                        "main": ["/repo/hero.ma"],
                        "web": ["/repo/hero.jpg"],
                    },
                    "SNAPSHOT101": {"file": ["/repo/brief.pdf"]},
                    "SNAPSHOT201": {"preview": ["/repo/review.png"]},
                    "SNAPSHOT301": {"file": ["/repo/task.txt"]},
                }.get(self.code, {})

        snapshot = SnapshotObject("SNAPSHOT001", "model/main")
        process_attachment = SnapshotObject(
            "SNAPSHOT101", "attachment/model/brief"
        )
        task_attachment = SnapshotObject(
            "SNAPSHOT201", "attachment/model/review"
        )
        task_direct_attachment = SnapshotObject(
            "SNAPSHOT301", "attachment/model/task"
        )
        process_note.get_connections.return_value = [process_attachment]
        task_note.get_connections.return_value = [task_attachment]

        class FileObject:
            def __init__(self, path, file_type):
                self.path = path
                self.file_type = file_type

            def get_full_abs_path(self):
                return self.path

            def get_value(self, name):
                return self.file_type if name == "type" else None

        snapshot_files = [
            FileObject("/repo/hero.ma", "main"),
            FileObject("/repo/hero.jpg", "web"),
        ]
        process_attachment_files = [
            FileObject("/repo/brief.pdf", "file"),
        ]
        task_attachment_files = [
            FileObject("/repo/review.png", "preview"),
        ]

        class Snapshot:
            @staticmethod
            def get_all_current_by_sobject(target):
                return [snapshot] if target is source else []

            @staticmethod
            def get_files_dict_by_snapshots(values):
                files = {
                    "SNAPSHOT001": snapshot_files,
                    "SNAPSHOT101": process_attachment_files,
                    "SNAPSHOT201": task_attachment_files,
                }
                return {
                    value.get_code(): files.get(value.get_code(), [])
                    for value in values
                }

            @staticmethod
            def get_by_sobjects(values):
                target = values[0]
                if target is source:
                    return [snapshot]
                if target is task:
                    return [task_direct_attachment]
                return []

        class Task:
            @staticmethod
            def get_by_sobject(target):
                return [task] if target is source else []

        checkins = []

        class FileCheckin:
            def __init__(self, sobject, **kwargs):
                self.sobject = sobject
                self.kwargs = kwargs
                checkins.append(self)

            def execute(self):
                return SnapshotObject(
                    "SNAPSHOTCOPY{:03d}".format(len(checkins)),
                    self.kwargs.get("context") or "publish",
                )

        pyasm = ModuleType("pyasm")
        biz = ModuleType("pyasm.biz")
        search = ModuleType("pyasm.search")
        checkin = ModuleType("pyasm.checkin")
        biz.Schema = Schema
        biz.Snapshot = Snapshot
        biz.Task = Task
        search.Search = Search
        search.SearchKey = SearchKey
        search.SearchType = SearchType
        checkin.FileCheckin = FileCheckin
        fake_server = Mock()

        modules = {
            "pyasm": pyasm, "pyasm.biz": biz, "pyasm.search": search,
            "pyasm.checkin": checkin,
        }
        with patch.dict(sys.modules, modules), patch.object(
            tq, "server", fake_server, create=True
        ):
            analysis = json.loads(tq.analyze_sobject_duplicate(
                "prod/asset?project=demo&code=ASSET001"
            ))
            result = json.loads(tq.duplicate_sobject_advanced(
                "prod/asset?project=demo&code=ASSET001",
                {
                    "fields": {
                        "name": "Hero copy", "description": "",
                    },
                    "relations": {
                        "code|parent|prod/category||": "none",
                        "instance|prod/tag|prod/asset_in_tag|": "link",
                        "code|children|prod/shot||": "copy",
                    },
                    "processes": {
                        "model": {
                            "copySnapshots": True,
                            "copyTasks": True,
                            "copyProcessMessages": True,
                            "copyTaskMessages": True,
                            "copyProcessAttachments": True,
                            "copyTaskAttachments": True,
                        },
                    },
                },
            ))

        fields = {field["name"]: field for field in analysis["fields"]}
        self.assertIn("name", fields)
        self.assertIn("description", fields)
        self.assertNotIn("category_code", fields)
        kinds = {record["kind"] for record in analysis["relations"]}
        self.assertEqual(kinds, {"parent", "instance", "children"})
        self.assertEqual(analysis["processes"][0]["snapshotCount"], 1)
        self.assertEqual(analysis["processes"][0]["fileCount"], 2)
        self.assertEqual(analysis["processes"][0]["taskCount"], 1)
        self.assertEqual(
            analysis["processes"][0]["processMessageCount"], 1
        )
        self.assertEqual(
            analysis["processes"][0]["taskMessageCount"], 1
        )
        self.assertEqual(
            analysis["processes"][0]["processAttachmentCount"], 1
        )
        self.assertEqual(
            analysis["processes"][0]["taskAttachmentCount"], 2
        )

        self.assertEqual(created.values["name"], "Hero copy")
        self.assertEqual(created.values["description"], "")
        self.assertNotIn("category_code", created.values)
        self.assertEqual(
            instance_connection.related, (created, instance_target)
        )
        self.assertTrue(instance_connection.committed)
        child.clone.assert_called_once_with(recursive=False, parent=created)
        self.assertEqual(len(checkins), 4)
        self.assertEqual(checkins[0].kwargs["mode"], "inplace")
        self.assertEqual(
            checkins[0].kwargs["file_paths"],
            ["/repo/hero.ma", "/repo/hero.jpg"],
        )
        task.clone.assert_called_once_with(
            recursive=False, parent=created
        )
        process_note.copy_note.assert_called_once_with(
            created, parent=None
        )
        task_note.copy_note.assert_called_once_with(
            task_clone, parent=None
        )
        self.assertEqual(result["relationsLinked"], 1)
        self.assertEqual(result["childrenCopied"], 1)
        self.assertEqual(result["snapshotsCopied"], 1)
        self.assertEqual(result["tasksCopied"], 1)
        self.assertEqual(result["processMessagesCopied"], 1)
        self.assertEqual(result["taskMessagesCopied"], 1)
        self.assertEqual(result["attachmentFilesCopied"], 3)
        self.assertEqual(checkins[1].sobject, process_note_clone)
        self.assertEqual(checkins[2].sobject, task_clone)
        self.assertEqual(checkins[3].sobject, task_note_clone)


class SObjectDuplicateQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def _create(self, width):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        warnings = []
        engine.warnings.connect(
            lambda values: warnings.extend(
                value.toString() for value in values
            )
        )
        application = _Application()
        with patch(
            "thlib.ui.sobject_duplicate.env_read_config",
            return_value={},
        ):
            controller = SObjectDuplicateController(application)
        payload = _analysis_payload()
        controller._source = _Source()
        controller._profile_key_value = "demo|prod/asset"
        controller._title = payload["title"]
        controller._search_type = payload["searchType"]
        controller._ready = True
        controller.fields.replace(
            controller._fallback_fields(payload["fields"])
        )
        controller.relations.reset_records(payload["relations"])
        controller.processes.reset_records(payload["processes"])
        window_model = FloatingWindowModel(MemorySettings())
        context = engine.rootContext()
        for name, value in {
            "sobjectDuplicateController": controller,
            "sobjectDuplicateFieldModel": controller.fields,
            "sobjectDuplicateRelationModel": controller.relations,
            "sobjectDuplicateProcessModel": controller.processes,
            "windowModel": window_model,
        }.items():
            context.setContextProperty(name, value)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "DuplicateSObjectView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme, "width": width, "height": 620,
        })
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(width, 620)
        view.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(40)
        return (
            engine, theme_component, component, theme, controller,
            window_model, view, window, warnings,
        )

    def test_wizard_renders_narrow_and_wide_and_switches_pages(self):
        for width in (560, 900):
            with self.subTest(width=width):
                (
                    engine, theme_component, component, theme, controller,
                    window_model, view, window, warnings,
                ) = (
                    self._create(width)
                )
                self.assertIsNotNone(
                    view.findChild(QObject, "duplicateSObjectHeader")
                )
                self.assertIsNotNone(
                    view.findChild(QObject, "duplicateFieldsPage")
                )
                confirm = view.findChild(
                    QObject, "duplicateConfirmButton"
                )
                self.assertIsNotNone(confirm)
                self.assertTrue(confirm.property("visible"))
                self.assertTrue(confirm.property("enabled"))
                footer = view.findChild(
                    QObject, "duplicateSObjectFooter"
                )
                self.assertIsNotNone(footer)
                footer_divider = view.findChild(
                    QObject, "dockWorkspaceFooterDivider"
                )
                self.assertIsNotNone(footer_divider)
                self.assertFalse(footer_divider.property("visible"))
                field_repeater = view.findChild(
                    QObject, "duplicateFieldRepeater"
                )
                field_card, undefined = QQmlExpression(
                    QQmlEngine.contextForObject(field_repeater),
                    field_repeater,
                    "itemAt(0)",
                ).evaluate()
                self.assertFalse(undefined)
                self.assertIsNotNone(field_card)
                self.assertEqual(
                    field_card.property("objectName"),
                    "duplicateFieldItem_name",
                )
                description_card, undefined = QQmlExpression(
                    QQmlEngine.contextForObject(field_repeater),
                    field_repeater,
                    "itemAt(1)",
                ).evaluate()
                self.assertFalse(undefined)
                self.assertIsNotNone(description_card.findChild(
                    QObject,
                    "sobjectMultilineVerticalScrollBar_description",
                ))
                if width >= 700:
                    self.assertAlmostEqual(
                        field_card.property("width"),
                        description_card.property("width"),
                        delta=2,
                    )
                controller.set_step(1)
                QTest.qWait(20)
                self.assertLessEqual(
                    confirm.property("x") + confirm.property("width"),
                    confirm.parent().property("width") + 1,
                )
                relations_page = view.findChild(
                    QObject, "duplicateRelationsPage"
                )
                self.assertIsNotNone(relations_page)
                relation_repeater = view.findChild(
                    QObject, "duplicateRelationRepeater"
                )
                relation_card, undefined = QQmlExpression(
                    QQmlEngine.contextForObject(relation_repeater),
                    relation_repeater,
                    "itemAt(0)",
                ).evaluate()
                self.assertFalse(undefined)
                self.assertIsNotNone(relation_card)
                relation_mode = relation_card.findChild(
                    QObject, "duplicateRelationMode_0"
                )
                self.assertIsNotNone(relation_mode)
                self.assertGreater(
                    relation_mode.property("width"),
                    relation_card.property("width") * 0.9,
                )
                controller.set_step(2)
                QTest.qWait(20)
                self.assertIsNotNone(
                    view.findChild(QObject, "duplicateSnapshotsPage")
                )
                process_repeater = view.findChild(
                    QObject, "duplicateProcessRepeater"
                )
                process_card, undefined = QQmlExpression(
                    QQmlEngine.contextForObject(process_repeater),
                    process_repeater,
                    "itemAt(0)",
                ).evaluate()
                self.assertFalse(undefined)
                self.assertIsNotNone(process_card)
                snapshot_choice = process_card.findChild(
                    QObject, "duplicateSnapshots_0"
                )
                self.assertIsNotNone(snapshot_choice)
                self.assertTrue(snapshot_choice.property("visible"))
                controller.set_step(3)
                QTest.qWait(20)
                self.assertIsNotNone(
                    view.findChild(QObject, "duplicateTasksMessagesPage")
                )
                task_choice = process_card.findChild(
                    QObject, "duplicateTasks_0"
                )
                self.assertIsNotNone(task_choice)
                self.assertTrue(task_choice.property("visible"))
                controller.set_step(4)
                QTest.qWait(20)
                self.assertIsNotNone(
                    view.findChild(QObject, "duplicateReviewPage")
                )
                self.assertTrue(confirm.property("visible"))
                loading_overlay = view.findChild(
                    QObject, "duplicateLoadingOverlay"
                )
                self.assertIsNotNone(loading_overlay)
                controller._duplicating = True
                controller.stateChanged.emit()
                QTest.qWait(20)
                self.assertTrue(loading_overlay.property("visible"))
                self.assertFalse(loading_overlay.property("cancellable"))
                loading_message = str(
                    loading_overlay.property("message") or ""
                )
                self.assertTrue(
                    "server" in loading_message.casefold()
                    or "сервер" in loading_message.casefold()
                )
                controller._duplicating = False
                controller.stateChanged.emit()
                self.assertEqual(warnings, [])
                window.close()
                window.deleteLater()
                view.deleteLater()
                theme.deleteLater()
                controller.deleteLater()
                engine.deleteLater()


if __name__ == "__main__":
    unittest.main()
