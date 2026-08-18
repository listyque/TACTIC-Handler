from __future__ import annotations

import unittest
from unittest.mock import patch

from modern_ui.process_filter_editor import ProcessFilterEditorController


class _Pipeline:
    def __init__(self, code, processes):
        self.info = {"code": code, "name": code.title()}
        self.pipeline = processes

    def get_process_info(self, code):
        return self.pipeline.get(code) or {}

    def get_process_label(self, code):
        return code.title()


class _Schema:
    children = [{"from": "demo/shot"}]


class _SType:
    def __init__(self, code, pipelines, project=None):
        self.info = {"code": code, "title": code.split("/")[-1].title()}
        self.pipeline = pipelines
        self.schema = _Schema()
        self._project = project

    def get_project(self):
        return self._project


class _Project:
    def __init__(self):
        self.stypes = {}


class ProcessFilterEditorControllerTests(unittest.TestCase):
    def make_controller(self):
        project = _Project()
        child = _SType(
            "demo/shot",
            {"shot": _Pipeline("shot", {"animation": {"type": "manual"}})},
            project,
        )
        stype = _SType(
            "demo/asset",
            {"asset": _Pipeline("asset", {"model": {"type": "manual"}})},
            project,
        )
        project.stypes = {"demo/shot": child, "demo/asset": stype}
        context = {
            "project": project,
            "project_code": "demo",
            "project_type": "prod",
            "search_type": "demo/asset",
            "tab_name": "demo/asset@assets",
            "stype": stype,
        }
        applied = []
        controller = ProcessFilterEditorController(
            lambda: context, applied.append, lambda _message: None
        )
        return controller, applied

    @patch("thlib.environment.env_read_config", return_value={})
    def test_legacy_tree_contains_children_pipelines_processes_and_builtins(
        self, _read
    ):
        controller, _applied = self.make_controller()

        controller.begin_session()

        kinds = [record["kind"] for record in controller.model._records]
        self.assertIn("child", kinds)
        self.assertIn("pipeline", kinds)
        self.assertIn("process", kinds)
        self.assertEqual(kinds.count("builtin"), 3)

    @patch("thlib.environment.env_write_config")
    @patch("thlib.environment.env_read_config", return_value={})
    def test_save_writes_legacy_process_ignore_contract(
        self, _read, write
    ):
        controller, applied = self.make_controller()
        controller.begin_session()
        model_row = next(
            index for index, record in enumerate(controller.model._records)
            if record["kind"] == "process" and record["key"] == "model"
        )
        controller.set_checked(model_row, False)

        self.assertTrue(controller.save())

        ignore = write.call_args.args[0]
        self.assertEqual(ignore["processes"]["asset"], ["model"])
        self.assertEqual(applied[-1], ignore)
        self.assertIn(
            "ui_search/checkin_out/prod/demo/demo/asset@assets",
            write.call_args.kwargs["unique_id"],
        )


if __name__ == "__main__":
    unittest.main()
