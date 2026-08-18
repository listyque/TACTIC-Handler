from __future__ import annotations

import unittest
from unittest.mock import patch

from modern_ui.repository_sync_editor import RepositorySyncEditorController


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
        self.assertTrue(all(
            record["dataKey"].endswith((":{b}", ":{pp}", ":{pr}", ":{s}"))
            for record in controller.model._records
        ))

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

        controller._presets_loaded([{
            "name": "review", "title": "Review",
            "data": {"preset_name": "review"},
            "getVersions": False, "onlyUpdates": False, "code": "",
        }, {
            "name": "full", "title": "Full",
            "data": {"preset_name": "full", "get_versions": True},
            "getVersions": True, "onlyUpdates": False, "code": "",
        }])

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


if __name__ == "__main__":
    unittest.main()
