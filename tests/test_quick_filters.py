from collections import OrderedDict
import unittest

from modern_ui.quick_filters import QuickFilterCatalog


class _TaskPipeline:
    def __init__(self):
        self.pipeline = OrderedDict((
            ("Assigned", {"color": "#8a6d3b"}),
            ("In Progress", {"color": "#3f7fc4"}),
        ))


class _Workflow:
    def get_by_pipeline_code(self, search_type, code):
        if search_type == "sthpw/task" and code == "demo/story_task":
            return _TaskPipeline()
        return None

    def get_by_process_node_type(self, search_type, node_type):
        return None


class _Pipeline:
    pipeline = OrderedDict((
        ("storyboard", {"name": "storyboard"}),
        ("publish", {"name": "publish"}),
    ))

    def get_all_pipeline_names(self):
        return list(self.pipeline)

    def get_all_pipeline_process(self):
        return [
            {"process": "storyboard"},
            {"process": "publish"},
        ]

    def get_info(self):
        return {
            "code": "demo/episode",
            "name": "Asset production",
            "color": "#5267a8",
        }

    def get_process_info(self, process):
        return {
            "label": process.title(),
            "type": "manual",
        }

    def get_pipeline_process(self, process):
        if process == "storyboard":
            return {
                "color": "#b54f3e",
                "workflow": {
                    "properties": {
                        "task_pipeline": "demo/story_task",
                    },
                },
            }
        return {"color": "#28a96b"}


class _Stype:
    def __init__(self, code="complex/scenes"):
        self.code = code

    def get_code(self):
        return self.code

    def get_pipeline(self):
        return {"demo/episode": _Pipeline()}

    def get_workflow(self):
        return _Workflow()

    def get_columns_info(self):
        return {}


class _Record:
    def __init__(self, code, **values):
        self.info = {"code": code, **values}

    def get_code(self):
        return self.info["code"]

    def get_info(self):
        return dict(self.info)

    def get_pipeline_code(self):
        return self.info.get("pipeline_code", "demo/episode")


class QuickFilterCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = QuickFilterCatalog()
        self.episode_a = _Record("EPISODE0001", duration=40)
        self.episode_b = _Record("EPISODE0002", duration=80)
        self.tasks = {
            "EPISODE0001": [
                _Record(
                    "TASK0001", process="storyboard", status="Assigned"
                )
            ],
            "EPISODE0002": [
                _Record(
                    "TASK0002", process="publish", status="In Progress"
                )
            ],
        }

    def test_workflow_process_and_task_status_facets_keep_colors(self):
        groups = self.catalog.groups(
            "complex/scenes",
            _Stype(),
            [self.episode_a, self.episode_b],
            {},
            self.tasks,
        )
        by_key = {group["key"]: group for group in groups}
        processes = {
            option["key"]: option
            for option in by_key["process"]["options"]
        }
        statuses = {
            option["key"]: option
            for option in by_key["status"]["options"]
        }
        self.assertEqual(processes["storyboard"]["accent"], "#b54f3e")
        self.assertTrue(processes["storyboard"]["showAccentMarker"])
        self.assertEqual(statuses["Assigned"]["accent"], "#8a6d3b")
        self.assertEqual(statuses["In Progress"]["accent"], "#3f7fc4")

    def test_task_filters_filter_parent_sobjects_from_batched_cache(self):
        episodes = [self.episode_a, self.episode_b]
        loaded = set(self.tasks)
        self.assertEqual(
            self.catalog.filter(
                "complex/scenes", episodes,
                {"process": {"storyboard"}}, self.tasks, loaded,
            ),
            [self.episode_a],
        )
        self.assertEqual(
            self.catalog.filter(
                "complex/scenes", episodes,
                {"status": {"In Progress"}}, self.tasks, loaded,
            ),
            [self.episode_b],
        )

    def test_task_filter_does_not_flash_empty_before_batch_finishes(self):
        episodes = [self.episode_a, self.episode_b]
        self.assertEqual(
            self.catalog.filter(
                "complex/scenes", episodes,
                {"status": {"Assigned"}}, {}, set(),
            ),
            episodes,
        )

    def test_generic_task_facets_are_not_hardcoded_to_episodes(self):
        groups = self.catalog.groups(
            "demo/assets", _Stype("demo/assets"),
            [self.episode_a], {}, self.tasks
        )
        self.assertEqual(
            [group["key"] for group in groups],
            ["pipeline", "process", "status"],
        )

    def test_asset_facets_use_native_category_and_pipeline_code(self):
        asset_a = _Record(
            "ASSET0001", category="characters",
            pipeline_code="demo/episode",
        )
        asset_b = _Record(
            "ASSET0002", category="props",
            pipeline_code="demo/other",
        )
        groups = self.catalog.groups(
            "demo/assets", _Stype("demo/assets"),
            [asset_a, asset_b], {}, {},
        )
        by_key = {group["key"]: group for group in groups}
        self.assertEqual(by_key["pipeline"]["title"], "ASSET PIPELINES")
        self.assertEqual(
            {option["key"] for option in by_key["category"]["options"]},
            {"characters", "props"},
        )
        self.assertEqual(
            self.catalog.filter(
                "demo/assets", [asset_a, asset_b],
                {"pipeline": {"demo/episode"}}, {}, set(),
            ),
            [asset_a],
        )

    def test_shared_configuration_reorders_hides_and_limits_facets(self):
        self.catalog.set_configuration("complex/scenes", {
            "version": 1,
            "groups": [
                {"key": "status", "enabled": True,
                 "options": ["Assigned"]},
                {"key": "duration", "enabled": False},
                {"key": "process", "enabled": True,
                 "options": ["storyboard"]},
            ],
        })
        groups = self.catalog.groups(
            "complex/scenes", _Stype(),
            [self.episode_a, self.episode_b], {}, self.tasks,
        )
        self.assertEqual(
            [group["key"] for group in groups], ["status", "process"]
        )
        self.assertEqual(
            [option["key"] for option in groups[0]["options"]],
            ["Assigned"],
        )
        editor_groups = self.catalog.editor_groups(
            "complex/scenes", _Stype(),
            [self.episode_a, self.episode_b], self.tasks,
        )
        editor_by_key = {group["key"]: group for group in editor_groups}
        self.assertFalse(editor_by_key["duration"]["enabled"])
        self.assertFalse(next(
            option["enabled"]
            for option in editor_by_key["status"]["options"]
            if option["key"] == "In Progress"
        ))


if __name__ == "__main__":
    unittest.main()
