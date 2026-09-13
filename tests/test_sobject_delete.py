from __future__ import annotations

import unittest
from collections import OrderedDict
from unittest.mock import Mock, patch

import thlib.tactic_classes as tc
from thlib.environment import env_inst

from thlib.ui.sobject_delete import (
    SObjectDeleteController,
    dependency_records,
)
from tests.support.async_scenarios import DeferredWorker


class _Schema:
    def __init__(self, relations=None):
        self.relations = dict(relations or {})

    def get_child(self, child_code, parent_code):
        return self.relations.get((child_code, parent_code))


class _Project:
    def __init__(self, code="demo"):
        self.code = code

    def get_code(self):
        return self.code


class _SType:
    def __init__(self, code, schema=None, project=None):
        self.code = code
        self.schema = schema
        self.project = project or _Project()

    def get_code(self):
        return self.code

    def get_pretty_name(self):
        return self.code.rsplit("/", 1)[-1].replace("_", " ").title()

    def get_schema(self):
        return self.schema

    def get_project(self):
        return self.project


class _SObject:
    def __init__(self, search_key, title, stype=None, info=None):
        self.search_key = search_key
        self.title = title
        self.stype = stype
        self.info = dict(info or {})

    def get_search_key(self):
        return self.search_key

    def get_title(self, pretty=False):
        if pretty:
            return self.title.replace("_", " ").capitalize()
        return self.title

    def get_info(self):
        return self.info

    def get_stype(self):
        return self.stype

    def get_plain_search_type(self):
        return self.search_key.split("?", 1)[0]


class _ParentSObject(_SObject):
    def __init__(self, *args, notes=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.notes = dict(notes or {})
        self.note_processes = []

    def get_notes_sobjects(self, process=None):
        self.note_processes.append(process)
        return self.notes


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
        self.result_refreshes = 0
        self.snapshot_refreshes = 0

    def _notify(self, message):
        self.notifications.append(message)

    def refresh_current(self):
        self.result_refreshes += 1

    def refresh_snapshot_browser(self):
        self.snapshot_refreshes += 1


class _CapturingPool:
    def __init__(self):
        self.is_stopped = False
        self.calls = []
        self.workers = []

    def start(self):
        self.is_stopped = False

    def add_task(self, operation, *args):
        self.calls.append((operation, args))
        worker = DeferredWorker(operation)
        self.workers.append(worker)
        return worker


class SObjectDeleteTests(unittest.TestCase):
    def test_legacy_defaults_include_builtin_and_instance_dependencies(self):
        schema = _Schema({
            ("prod/asset_in_asset", "prod/asset"): {
                "relationship": "instance",
                "instance_type": "prod/asset_in_asset",
            },
        })
        parent_stype = _SType("prod/asset", schema=schema)
        root = _SObject(
            "prod/asset?project=demo&code=ASSET001",
            "Asset 001",
            parent_stype,
        )
        task = _SObject(
            "sthpw/task?code=TASK001", "TASK001",
            info={"process": "Model", "status": "In Progress"},
        )
        instance = _SObject(
            "prod/asset_in_asset?project=demo&code=REL001",
            "Linked asset",
        )
        render = _SObject(
            "prod/render?project=demo&code=RENDER001", "Render"
        )
        file_object = _SObject(
            "sthpw/file?code=FILE001", "FILE001",
            info={"file_name": "preview.jpg", "context": "publish"},
        )
        dependencies = OrderedDict({
            "sthpw/task": OrderedDict({task.get_search_key(): task}),
            "prod/asset_in_asset": OrderedDict({
                instance.get_search_key(): instance,
            }),
            "prod/render": OrderedDict({render.get_search_key(): render}),
            "sthpw/file": OrderedDict({
                root.get_search_key(): root,
                file_object.get_search_key(): file_object,
            }),
        })
        stypes = {
            "sthpw/task": _SType("sthpw/task"),
            "prod/asset_in_asset": _SType("prod/asset_in_asset"),
            "prod/render": _SType("prod/render"),
            "sthpw/file": _SType("sthpw/file"),
        }

        records = dependency_records(
            [root], dependencies, stypes.get
        )

        by_type = {record["searchType"]: record for record in records}
        self.assertTrue(by_type["sthpw/task"]["checked"])
        self.assertTrue(by_type["prod/asset_in_asset"]["checked"])
        self.assertTrue(by_type["sthpw/file"]["checked"])
        self.assertFalse(by_type["prod/render"]["checked"])
        self.assertEqual(by_type["sthpw/file"]["count"], 1)
        self.assertEqual(
            by_type["sthpw/file"]["items"][0]["searchKey"],
            file_object.get_search_key(),
        )
        self.assertEqual(by_type["sthpw/file"]["searchTypeTitle"], "File")
        self.assertEqual(by_type["sthpw/file"]["iconName"], "file")
        self.assertEqual(
            by_type["sthpw/task"]["items"][0]["title"], "Model",
        )
        self.assertEqual(
            by_type["sthpw/task"]["items"][0]["details"],
            "In Progress",
        )
        self.assertEqual(
            by_type["sthpw/file"]["items"][0]["title"],
            "preview.jpg",
        )
        self.assertEqual(
            by_type["sthpw/file"]["items"][0]["details"],
            "publish",
        )
        self.assertTrue(all(not record["expanded"] for record in records))

    def test_status_log_dependency_uses_readable_transition_metadata(self):
        root = _SObject("prod/asset?code=ASSET001", "Asset")
        status_log = _SObject(
            "sthpw/status_log?code=LOG001",
            "LOG001",
            info={
                "code": "LOG001",
                "from_status": "In Progress",
                "to_status": "Complete",
                "process": "publish",
                "login": "artist",
                "timestamp": "2026-08-21 12:30:00",
            },
        )

        records = dependency_records(
            [root],
            {"sthpw/status_log": {
                status_log.get_search_key(): status_log,
            }},
            lambda search_type: _SType(search_type),
        )

        item = records[0]["items"][0]
        self.assertEqual(item["title"], "In Progress → Complete")
        self.assertEqual(
            item["details"], "publish · artist · 2026-08-21 12:30:00"
        )
        self.assertNotIn("LOG001", item["title"])

    def test_no_checked_dependency_falls_back_to_root_search_type(self):
        root = _SObject("prod/asset?code=ASSET001", "Asset")
        controller = SObjectDeleteController(_Application())
        controller._sources = [root]
        controller.model.reset_records([{
            "searchType": "prod/render",
            "count": 2,
            "checked": False,
            "defaultChecked": False,
            "expanded": False,
            "items": [],
        }])

        self.assertEqual(
            controller._selected_search_types(), ["prod/asset"]
        )

    def test_task_discovery_adds_parent_process_notes_as_explicit_dependencies(self):
        project = _Project("demo")
        task = _SObject(
            "sthpw/task?project=demo&code=TASK001",
            "TASK001",
            _SType("sthpw/task", project=project),
            info={
                "code": "TASK001",
                "search_type": "prod/asset",
                "search_code": "ASSET001",
                "project_code": "demo",
                "process": "model",
            },
        )
        note = _SObject(
            "sthpw/note?project=demo&code=NOTE001",
            "NOTE001",
            info={
                "code": "NOTE001",
                "note": "Model review",
                "process": "model",
            },
        )
        parent = _ParentSObject(
            "prod/asset?project=demo&code=ASSET001",
            "Asset 001",
            _SType("prod/asset", project=project),
            notes={note.get_search_key(): note},
        )

        with patch.object(
                tc, "get_all_dependency",
                return_value={"sthpw/note": {
                    note.get_search_key(): note,
                }}), patch.object(
                    env_inst, "get_stype_by_code",
                    return_value=_SType("sthpw/note", project=project)):
            records = SObjectDeleteController._discover_dependencies(
                [task], {task.get_search_key(): parent}
            )

        self.assertEqual(parent.note_processes, ["model"])
        notes = next(
            record for record in records
            if record["searchType"] == "sthpw/note"
        )
        self.assertTrue(notes["checked"])
        self.assertEqual(notes["count"], 1)
        self.assertEqual(
            notes["explicitSearchKeys"], [note.get_search_key()]
        )
        self.assertEqual(notes["items"][0]["title"], "Model review")

    def test_checked_task_notes_are_explicit_roots_in_delete_batch(self):
        application = _Application()
        controller = SObjectDeleteController(application)
        task = _SObject(
            "sthpw/task?project=demo&code=TASK001", "TASK001"
        )
        note_key = "sthpw/note?project=demo&code=NOTE001"
        controller._sources = [task]
        controller._ready = True
        controller.model.reset_records([{
            "searchType": "sthpw/note",
            "count": 1,
            "checked": True,
            "defaultChecked": True,
            "expanded": False,
            "items": [{"searchKey": note_key}],
            "explicitSearchKeys": [note_key],
        }])
        self.assertEqual(
            controller._selected_explicit_search_keys(), [note_key]
        )

        pool = _CapturingPool()
        delete = Mock(return_value={})
        with patch.object(env_inst, "server_pool", pool), patch.object(
                tc, "delete_sobjects", delete), patch(
                    "thlib.server_cache.invalidate_domains"
                ):
            controller.confirm_delete()
            operation, args = pool.calls[0]
            self.assertEqual(args, ())
            operation()
            delete.assert_called_once_with(
                [task.get_search_key(), note_key],
                {"search_types": ["sthpw/note"]},
            )

        controller.model.update_record(0, {"checked": False})
        self.assertEqual(controller._selected_explicit_search_keys(), [])


    def test_controller_uses_legacy_batch_payload_off_the_ui_thread(self):
        application = _Application()
        controller = SObjectDeleteController(application)
        root = _SObject("prod/asset?code=ASSET001", "Asset")
        pool = _CapturingPool()

        with patch.object(env_inst, "server_pool", pool):
            self.assertTrue(controller.begin([root], "snapshot_file"))
            self.assertEqual(application.window_model.shown, ["delete_sobject"])
            self.assertTrue(pool.workers[0].started)
            pool.workers[0].resolve([{
                "searchType": "sthpw/file",
                "count": 3,
                "checked": True,
                "defaultChecked": True,
                "expanded": False,
                "items": [],
            }])
            self.assertTrue(controller.ready)

            delete = Mock(return_value={})
            with patch.object(tc, "delete_sobjects", delete), patch(
                    "thlib.server_cache.invalidate_domains"):
                controller.confirm_delete()
                operation, args = pool.calls[1]
                self.assertEqual(args, ())
                operation()
                delete.assert_called_once_with(
                    [root.get_search_key()],
                    {"search_types": ["sthpw/file"]},
                )
            self.assertTrue(pool.workers[1].started)
            pool.workers[1].resolve({"deleted": True})

        self.assertEqual(application.window_model.closed, ["delete_sobject"])
        self.assertEqual(application.snapshot_refreshes, 1)
        self.assertEqual(application.result_refreshes, 0)
        self.assertEqual(application.notifications, ["Item deleted"])

    def test_search_key_target_uses_same_dependency_window_and_delete_batch(self):
        application = _Application()
        controller = SObjectDeleteController(application)
        pool = _CapturingPool()
        search_key = (
            "skey://demo/th_knowledge_article?project=demo&id=17"
        )

        with patch.object(env_inst, "server_pool", pool):
            self.assertTrue(controller.begin_search_keys([{
                "searchKey": search_key,
                "title": "Pipeline guide",
                "projectCode": "demo",
            }], "knowledge"))
            self.assertEqual(application.window_model.shown, [
                "delete_sobject"
            ])
            self.assertEqual(controller.targets, [{
                "title": "Pipeline guide",
                "searchKey": (
                    "demo/th_knowledge_article?project=demo&id=17"
                ),
            }])
            snapshot = _SObject(
                "sthpw/snapshot?code=SNAPSHOT001",
                "Article attachment",
            )
            file_object = _SObject(
                "sthpw/file?code=FILE001",
                "guide.png",
            )
            related = _SObject(
                "demo/article_link?project=demo&code=LINK001",
                "Linked record",
            )
            discovery, discovery_args = pool.calls[0]
            with patch.object(tc, "get_all_dependency", return_value={
                    "sthpw/snapshot": {snapshot.get_search_key(): snapshot},
                    "sthpw/file": {file_object.get_search_key(): file_object},
                    "demo/article_link": {related.get_search_key(): related},
            }), patch.object(
                    env_inst, "get_stype_by_code",
                    side_effect=lambda code, project_code=None: _SType(
                        code, project=_Project(project_code or "demo")
                    )):
                records = discovery(*discovery_args)
            pool.workers[0].resolve(records)
            discovered = {
                record["searchType"]: record
                for record in controller.model.records()
            }
            self.assertEqual(set(discovered), {
                "sthpw/snapshot", "sthpw/file", "demo/article_link",
            })
            self.assertTrue(discovered["sthpw/snapshot"]["checked"])
            self.assertTrue(discovered["sthpw/file"]["checked"])
            self.assertFalse(discovered["demo/article_link"]["checked"])

            delete = Mock(return_value={})
            with patch.object(tc, "delete_sobjects", delete), patch(
                    "thlib.server_cache.invalidate_domains"):
                controller.confirm_delete()
                operation, _args = pool.calls[1]
                operation()
                delete.assert_called_once_with(
                    ["demo/th_knowledge_article?project=demo&id=17"],
                    {"search_types": ["sthpw/snapshot", "sthpw/file"]},
                )
            pool.workers[1].resolve({"deleted": True})

        self.assertEqual(application.result_refreshes, 0)
        self.assertEqual(application.notifications, ["Item deleted"])


if __name__ == "__main__":
    unittest.main()
