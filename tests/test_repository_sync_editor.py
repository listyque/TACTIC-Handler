from __future__ import annotations

import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlPropertyMap
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.process_filter_editor import ProcessFilterEditorController
from thlib.ui.repository_sync_editor import RepositorySyncEditorController
from thlib.ui.workspace import RecordListModel


class _Pipeline:
    def __init__(self, code, processes):
        self.info = {"code": code, "name": code.title(), "color": "#456789"}
        self.pipeline = processes

    def get_process_info(self, code):
        return dict(self.pipeline.get(code) or {})

    def get_process_label(self, code):
        return code.title()


class _Schema:
    def __init__(self, children=()):
        self.children = list(children)


class _Project:
    info = {"type": "prod", "code": "demo"}

    def __init__(self):
        self.stypes = {}

    def get_code(self):
        return "demo"


class _SType:
    def __init__(self, code, pipeline, project, children=()):
        self.info = {"code": code, "title": code.split("/")[-1].title()}
        self.pipeline = pipeline
        self.schema = _Schema(children)
        self.project = project

    def get_code(self):
        return self.info["code"]

    def get_pretty_name(self):
        return self.info["title"]

    def get_project(self):
        return self.project

    def get_pipeline(self):
        return self.pipeline


class _SObject:
    def __init__(self, stype):
        self.stype = stype

    def get_stype(self):
        return self.stype

    def get_title(self):
        return "Asset A"


class _RepositorySync:
    def __init__(self):
        self.calls = []
        self.selected_name = ""
        self.stored_selection = None
        self.cached_presets = []

    def cache_presets(self, _source, presets):
        self.cached_presets = list(presets)

    def start_sobject_sync(self, *args, **kwargs):
        self.calls.append((args, kwargs))

    def start_stype_sync(self, *args, **kwargs):
        self.calls.append((args, kwargs))

    @staticmethod
    def configured_scope_mode():
        return "full"

    @staticmethod
    def configured_partial_chunk_size():
        return 10

    @staticmethod
    def selected_preset_index(_source, _tab_name):
        return 0

    def selected_preset_name(self, _source, _tab_name):
        return self.selected_name

    @staticmethod
    def store_selected_preset_index(_source, _tab_name, _index):
        return None

    def store_selected_preset(
        self, _source, _tab_name, index, preset_name
    ):
        self.stored_selection = (index, preset_name)


class RepositorySyncEditorTests(unittest.TestCase):
    def test_partial_scope_is_forwarded_without_changing_preset_payload(self):
        controller, repository_sync = self.make_controller()
        controller.presets.replace([{
            "name": "default", "title": "Default", "data": {},
        }])
        controller.select_preset(0)
        controller.set_scope_mode("partial")

        controller.start_sync()

        _args, kwargs = repository_sync.calls[-1]
        self.assertEqual(kwargs["scope_mode"], "partial")
        self.assertEqual(kwargs["partial_chunk_size"], 10)
        self.assertNotIn("scope_mode", kwargs["preset_data"])

    def test_runtime_chunk_size_is_forwarded_directly(self):
        controller, repository_sync = self.make_controller()
        controller.presets.replace([{
            "name": "default", "title": "Default", "data": {},
        }])
        controller.select_preset(0)
        controller.set_scope_mode("partial")

        controller.start_sync_with_chunk_size(1)

        _args, kwargs = repository_sync.calls[-1]
        self.assertEqual(controller.partialChunkSize, 1)
        self.assertEqual(kwargs["partial_chunk_size"], 1)

    def make_controller(self):
        project = _Project()
        child = _SType(
            "demo/shot",
            {"shot": _Pipeline("shot", {"animation": {"color": "#aabbcc"}})},
            project,
        )
        root = _SType(
            "demo/asset",
            {"asset": _Pipeline("asset", {"model": {"color": "#112233"}})},
            project,
            ({"from": "demo/shot", "type": "one_to_many"},),
        )
        project.stypes = {"demo/asset": root, "demo/shot": child}
        sobject = _SObject(root)
        sync = _RepositorySync()
        controller = RepositorySyncEditorController(
            lambda: {
                "sobject": sobject,
                "stype": root,
                "tab_name": "Assets",
                "project_code": "demo",
            },
            sync,
            lambda _message: None,
        )
        controller._context = controller._context_provider()
        controller.model.replace(controller._build_tree(root))
        return controller, sync

    def test_tree_repeats_legacy_kinds_and_nested_children(self):
        controller, _sync = self.make_controller()

        kinds = [record["kind"] for record in controller.model._records]

        self.assertEqual(kinds.count("child"), 1)
        self.assertEqual(kinds.count("pipeline"), 2)
        self.assertEqual(kinds.count("process"), 2)
        self.assertEqual(kinds.count("builtin"), 6)
        self.assertEqual(kinds, [
            "builtin", "builtin", "builtin",
            "pipeline", "process", "child",
            "builtin", "builtin", "builtin",
            "pipeline", "process",
        ])
        self.assertTrue(all(
            record["dataKey"].endswith((":{b}", ":{pp}", ":{pr}", ":{s}"))
            for record in controller.model._records
        ))

    def test_process_filter_and_repository_sync_share_the_same_tree(self):
        controller, _sync = self.make_controller()
        stype = controller._context["stype"]
        project = stype.get_project()
        filter_controller = ProcessFilterEditorController(
            lambda: {}, lambda _settings: None, lambda _message: None
        )

        filter_records = filter_controller._build_records(stype, project)
        sync_records = controller._build_tree(stype)
        structural_roles = (
            "nodeId", "parentId", "dataKey", "key", "title", "kind",
            "group", "depth", "checkable", "accent", "hasChildren",
        )

        self.assertEqual(
            [tuple(record[role] for role in structural_roles)
             for record in filter_records],
            [tuple(record[role] for role in structural_roles)
             for record in sync_records],
        )

    def test_duplicate_empty_window_event_keeps_the_active_process_tree(self):
        controller, _sync = self.make_controller()
        valid_context = dict(controller._context)
        contexts = iter((valid_context, {}))
        controller._context_provider = lambda: next(contexts)

        with patch.object(controller, "reload_presets"):
            controller.begin_session()
            records = [dict(record) for record in controller.model._records]
            generation = controller._session_generation
            controller.begin_session()

        self.assertTrue(controller.validContext)
        self.assertEqual(controller.error, "")
        self.assertEqual(controller.model._records, records)
        self.assertEqual(controller._session_generation, generation)

        controller.cancel()
        self.assertGreater(controller._session_generation, generation)
        controller._context_provider = lambda: {}
        controller.begin_session()
        self.assertFalse(controller.validContext)
        self.assertEqual(
            controller.error, "Select an sObject or Search Type first"
        )

    def test_loaded_project_resolves_stype_during_window_bootstrap(self):
        controller, _sync = self.make_controller()
        root = controller._context["stype"]
        controller._context_provider = lambda: {
            "stype": None,
            "project": root.get_project(),
            "project_code": "demo",
            "search_type": root.get_code(),
            "tab_name": "Assets",
        }

        with patch.object(controller, "reload_presets"):
            controller.begin_session()

        self.assertTrue(controller.validContext)
        self.assertIs(controller._context["stype"], root)
        self.assertTrue(controller.model._records)

    def test_shift_expansion_applies_to_the_entire_descendant_branch(self):
        controller, _sync = self.make_controller()
        child_row = next(
            index for index, record in enumerate(controller.model._records)
            if record["kind"] == "child"
        )

        controller.toggle_expanded(child_row, True)

        child_id = controller.model._records[child_row]["nodeId"]
        descendants = [
            record for record in controller.model._records
            if record["parentId"] == child_id
        ]
        self.assertFalse(controller.model._records[child_row]["expanded"])
        self.assertTrue(descendants)
        self.assertTrue(all(not record["rowVisible"] for record in descendants))

    def test_native_get_pipeline_fallback_builds_legacy_pipeline_rows(self):
        controller, _sync = self.make_controller()
        stype = controller._context["stype"]
        pipelines = stype.pipeline
        stype.pipeline = None
        stype.get_pipeline = lambda: pipelines

        records = controller._build_tree(stype)

        self.assertTrue(any(
            record["dataKey"] == "asset:{pp}" for record in records
        ))

    def test_deep_child_tree_matches_legacy_recursion_and_breaks_cycles(self):
        project = _Project()
        grandchild = _SType(
            "demo/task",
            {"task": _Pipeline("task", {"work": {}})},
            project,
            ({"from": "demo/asset", "type": "one_to_many"},),
        )
        child = _SType(
            "demo/shot",
            {"shot": _Pipeline("shot", {"animation": {}})},
            project,
            ({"from": "demo/task", "type": "one_to_many"},),
        )
        root = _SType(
            "demo/asset",
            {"asset": _Pipeline("asset", {"model": {}})},
            project,
            ({"from": "demo/shot", "type": "one_to_many"},),
        )
        project.stypes = {
            "demo/asset": root,
            "demo/shot": child,
            "demo/task": grandchild,
        }
        child.project = None
        grandchild.project = None
        sync = _RepositorySync()
        controller = RepositorySyncEditorController(
            lambda: {"stype": root, "project_code": "demo"},
            sync,
            lambda _message: None,
        )

        records = controller._build_tree(root)

        child_keys = [
            record["dataKey"] for record in records
            if record["kind"] == "child"
        ]
        self.assertEqual(child_keys, [
            "demo/shot:{s}", "demo/task:{s}", "demo/asset:{s}",
        ])
        task = next(
            record for record in records
            if record["dataKey"] == "demo/task:{s}"
        )
        self.assertEqual(task["depth"], 1)
        self.assertTrue(any(
            record["parentId"] == task["nodeId"]
            and record["dataKey"] == "task:{pp}"
            for record in records
        ))

    def test_preset_query_uses_the_broad_legacy_search_type_key(self):
        controller, _sync = self.make_controller()
        server = Mock()
        server.query.return_value = []

        with patch("thlib.tactic_classes.server_start", return_value=server):
            controller._query_presets(controller._context["stype"])

        filters = server.query.call_args.args[1]
        self.assertIn(
            ("key", "like", "search_type:demo/asset%"), filters
        )

    @patch("thlib.environment.env_write_config")
    def test_legacy_nested_preset_round_trips(self, _write):
        controller, _sync = self.make_controller()
        preset = {
            "preset_name": "review",
            "pretty_preset_name": "Review",
            "get_versions": True,
            "publish:{b}": {"state": True},
            "asset:{pp}": {
                "state": False,
                "sub": {"model:{pr}": {"state": True}},
            },
            "demo/shot:{s}": {
                "state": True,
                "sub": {
                    "icon:{b}": {"state": True},
                    "shot:{pp}": {
                        "state": False,
                        "sub": {"animation:{pr}": {"state": True}},
                    },
                },
            },
        }
        controller.presets.replace([{
            "name": "review", "title": "Review", "data": preset,
            "getVersions": True, "onlyUpdates": False, "code": "",
        }])

        controller.select_preset(0)
        payload = controller._preset_payload("review", "Review")

        self.assertTrue(payload["get_versions"])
        self.assertTrue(payload["asset:{pp}"]["sub"]["model:{pr}"]["state"])
        child = payload["demo/shot:{s}"]
        self.assertTrue(child["state"])
        self.assertTrue(
            child["sub"]["shot:{pp}"]["sub"]["animation:{pr}"]["state"]
        )

    @patch("thlib.environment.env_write_config")
    def test_start_uses_unsaved_tree_state_without_server_round_trip(self, _write):
        controller, sync = self.make_controller()
        controller.presets.replace([{
            "name": "default", "title": "Default",
            "data": {"preset_name": "default"},
            "getVersions": False, "onlyUpdates": False, "code": "",
        }])
        controller.select_preset(0)
        process_row = next(
            index for index, record in enumerate(controller.model._records)
            if record["dataKey"] == "model:{pr}"
        )
        controller.set_checked(process_row, True)

        controller.start_sync()

        _args, kwargs = sync.calls[-1]
        self.assertTrue(
            kwargs["preset_data"]["asset:{pp}"]["sub"]["model:{pr}"]["state"]
        )

    @patch("thlib.environment.env_write_config")
    def test_saved_preset_name_survives_server_row_reordering(self, _write):
        controller, sync = self.make_controller()
        sync.selected_name = "full"
        controller.presets.replace([{
            "name": "default", "title": "Default",
            "data": {"preset_name": "default"},
            "getVersions": False, "onlyUpdates": False, "code": "",
        }])

        controller._presets_loaded((
            controller._session_generation,
            "demo/asset",
            [{
                "name": "review", "title": "Review",
                "data": {"preset_name": "review"},
                "getVersions": False, "onlyUpdates": False, "code": "",
            }, {
                "name": "full", "title": "Full",
                "data": {"preset_name": "full", "get_versions": True},
                "getVersions": True, "onlyUpdates": False, "code": "",
            }],
        ))

        self.assertEqual(controller.selectedPreset, 1)
        self.assertEqual(sync.stored_selection, (1, "full"))

    @patch("thlib.environment.env_write_config")
    def test_presets_from_previous_search_type_are_ignored(self, _write):
        controller, _sync = self.make_controller()
        controller._session_generation = 2

        controller._presets_loaded((1, "demo/episode", [{
            "name": "episodes", "title": "Episodes",
            "data": {"preset_name": "episodes"},
            "getVersions": False, "onlyUpdates": False, "code": "",
        }]))

        self.assertEqual(controller.presets._records, [])


class RepositorySyncEditorQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    @staticmethod
    def _property_map(values):
        result = QQmlPropertyMap()
        for key, value in values.items():
            result.insert(key, value)
        return result

    def test_legacy_left_and_queue_right_layout_instantiates(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        editor = self._property_map({
            "contextTitle": "Asset A", "busy": False,
            "selectedPreset": 0, "validContext": True,
            "fullSync": False, "onlyUpdates": False,
            "scopeMode": "full", "partialChunkSize": 10,
            "error": "", "dirty": False,
        })
        sync = self._property_map({
            "discovery_active": False, "discovery_state": "idle",
            "discovery_mode": "full", "active_count": 0,
            "queue_count": 0, "auto_clean": False,
            "batch_file_count": 0, "failed_file_count": 0,
            "processed_file_count": 0, "completed_file_count": 0,
            "overall_progress": 0.0, "discovery_total_roots": 0,
            "discovery_processed_roots": 0, "active_row": -1,
            "total_size_text": "0 B", "transferred_size_text": "0 B",
            "remaining_size_text": "0 B", "aggregate_speed_text": "0 B/s",
            "elapsed_text": "00:00", "eta_text": "--",
            "discovery_error": "",
        })
        presets = RecordListModel((
            "name", "title", "getVersions", "onlyUpdates", "data", "code",
        ))
        presets.reset_records([{
            "name": "default", "title": "Default",
            "getVersions": False, "onlyUpdates": False,
            "data": {}, "code": "",
        }])
        tree = RecordListModel((
            "nodeId", "parentId", "dataKey", "title", "subtitle", "kind",
            "depth", "checkable", "checked", "expanded", "rowVisible",
            "selected", "accent", "hasChildren",
        ))
        tree.reset_records([{
            "nodeId": "builtin:publish", "parentId": "",
            "dataKey": "publish:{b}", "title": "Publish",
            "subtitle": "Built-in process", "kind": "builtin",
            "depth": 0, "checkable": True, "checked": True,
            "expanded": True, "rowVisible": True, "selected": False,
            "accent": "", "hasChildren": False,
        }])
        queue = RecordListModel((
            "taskId", "title", "process", "progress", "progressValue",
            "status", "checked", "bytesDone", "bytesTotal", "speed",
            "localPath", "webPath", "attempt", "error", "active",
            "phase", "alreadyExists",
        ))
        context = engine.rootContext()
        context.setContextProperty("repositorySyncEditorController", editor)
        context.setContextProperty("repositorySync", sync)
        context.setContextProperty("repositorySyncPresetModel", presets)
        context.setContextProperty("repositorySyncTreeModel", tree)
        context.setContextProperty("repoSyncModel", queue)
        context.setContextProperty("windowModel", self._property_map({}))

        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "RepositorySyncEditorView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme, "windowId": "repository_sync_editor",
        })
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(960, 620)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        QTest.qWait(40)

        process_panel = view.findChild(QObject, "repositorySyncProcessPanel")
        queue_panel = view.findChild(QObject, "repositorySyncQueuePanel")
        delete_button = view.findChild(
            QObject, "repositorySyncPresetDeleteButton"
        )
        process_tree = view.findChild(
            QObject, "repositorySyncProcessTree"
        )
        status_label = view.findChild(QObject, "repositorySyncStatusLabel")
        self.assertIsNotNone(process_panel)
        self.assertIsNotNone(queue_panel)
        self.assertIsNotNone(process_tree)
        self.assertIsNotNone(status_label)
        self.assertEqual(process_tree.property("count"), 1)
        self.assertLess(
            process_panel.mapToScene(QPointF()).x(),
            queue_panel.mapToScene(QPointF()).x(),
        )
        self.assertFalse(delete_button.property("visible"))
        process_panel.setProperty("togglersExpanded", True)
        QTest.qWait(20)
        self.assertTrue(delete_button.property("visible"))
        sync.insert("discovery_active", True)
        sync.insert("discovery_state", "processing")
        sync.insert("discovery_total_roots", 300)
        QTest.qWait(20)
        self.assertEqual(
            status_label.property("text"),
            "Processing server response: 300 objects",
        )

        window.close()
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()


if __name__ == "__main__":
    unittest.main()
