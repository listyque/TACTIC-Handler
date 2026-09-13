from __future__ import annotations

import unittest

from thlib.ui.controllers.item_actions import ItemActionsMixin
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


class _Pipeline:
    _colors = {
        "publish": "#78909c",
        "model": "#ef5350",
        "rig": "#5c6bc0",
    }

    def get_all_pipeline_names(self):
        return ["model", "rig", "publish"]

    def get_process_info(self, process):
        return {
            "label": process.capitalize(),
            "color": self._colors.get(process, "#78909c"),
        }

    def get_pipeline_process(self, process):
        return {"color": self._colors.get(process, "#78909c")}

    def get_process_label(self, process):
        return process.capitalize()


class _SearchType:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def get_pipeline(self):
        return {"asset": self.pipeline}


class _Source:
    def __init__(self, notes=None, tasks=None, task_summaries=None):
        self.notes = dict(notes or {})
        self.tasks = dict(tasks or {})
        self.task_summaries = dict(task_summaries or {})
        self.pipeline = _Pipeline()

    def get_notes_count(self, process=None):
        if process is not None:
            return self.notes.get(process, 0)
        return dict(self.notes)

    def set_notes_count(self, process, count):
        self.notes[str(process)] = int(count)

    def get_tasks_count(self, process=None):
        if process is not None:
            return self.tasks.get(process, 0)
        return dict(self.tasks)

    def set_tasks_count(self, process, count):
        self.tasks[str(process)] = int(count)

    def get_task_summaries(self, process=None):
        if process is not None:
            return list(self.task_summaries.get(process, ()))
        return dict(self.task_summaries)

    def get_stype(self):
        return _SearchType(self.pipeline)

    def get_pipeline_code(self):
        return "asset"


class _ActionHarness(ItemActionsMixin):
    def __init__(self, node, model=None):
        self.node = node
        self.workspace_model = model

    def _node_for_any(self, node_id):
        if node_id == self.node.node_id:
            return self.node
        return self.workspace_model.node_for(node_id) if self.workspace_model else None


class WorkspaceProcessCountMenuTests(unittest.TestCase):
    @staticmethod
    def make_model(notes=None, tasks=None, task_summaries=None):
        source = _Source(
            notes=notes, tasks=tasks, task_summaries=task_summaries,
        )
        node = WorkspaceNode(
            node_id="skey://demo/asset?project=demo&code=ASSET001",
            node_type="sobject",
            search_key="skey://demo/asset?project=demo&code=ASSET001",
            code="ASSET001",
            title="Asset 1",
            accent="#ef5350",
            comments=sum((notes or {}).values()),
            tasks=int((tasks or {}).get("__total__") or 0),
            source=source,
        )
        model = WorkspaceItemModel()
        model.replace_nodes([node])
        return model, node, source

    def test_publish_is_always_first_and_zero_publish_is_visible(self):
        _model, node, _source = self.make_model(
            notes={"model": 2, "rig": 1}
        )

        actions = _ActionHarness(node).process_count_actions(
            node.node_id, "notes"
        )

        self.assertEqual(
            [action["command"] for action in actions],
            ["publish", "model", "rig"],
        )
        self.assertEqual(actions[0]["badgeCount"], 0)
        self.assertTrue(actions[0]["showZeroBadge"])
        self.assertEqual(actions[1]["accent"], "#ef5350")
        self.assertEqual(actions[2]["accent"], "#5c6bc0")

    def test_publish_only_state_produces_one_direct_open_action(self):
        _model, node, _source = self.make_model(
            tasks={"__total__": 4, "publish": 4}
        )

        actions = _ActionHarness(node).process_count_actions(
            node.node_id, "tasks"
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["command"], "publish")
        self.assertEqual(actions[0]["badgeCount"], 4)

    def test_multiple_tasks_add_a_detailed_process_drill_in(self):
        model, node, _source = self.make_model(
            tasks={"__total__": 2, "model": 2},
            task_summaries={"model": [
                {
                    "code": "TASK001", "process": "model",
                    "context": "model", "assigned": "artist",
                    "status": "In Progress", "__notes_count__": 3,
                    "__primary_note_branch__": True,
                },
                {
                    "code": "TASK002", "process": "model",
                    "context": "client-review", "assigned": "lead",
                    "status": "Review", "__notes_count__": 1,
                    "__primary_note_branch__": False,
                },
            ]},
        )
        harness = _ActionHarness(node, model)

        process_actions = harness.process_count_actions(node.node_id, "tasks")
        model_action = next(
            action for action in process_actions
            if action["command"] == "model"
        )
        self.assertEqual(model_action["secondaryCommand"], "tasks:model")
        self.assertEqual(model_action["secondaryIcon"], "chevron-right")
        self.assertTrue(model_action["secondaryKeepOpen"])

        task_actions = harness.process_task_actions(
            node.node_id, "notes", "model"
        )
        self.assertEqual(
            [action["taskCode"] for action in task_actions],
            ["TASK001", "TASK002"],
        )
        self.assertTrue(all(
            action["icon"] == "task" for action in task_actions
        ))
        self.assertEqual(task_actions[1]["title"], "client-review")
        self.assertIn("lead", task_actions[1]["status"])
        self.assertEqual(task_actions[1]["badgeCount"], 1)

    def test_process_node_badge_lists_its_tasks_directly(self):
        model, root, source = self.make_model(
            tasks={"__total__": 2, "model": 2},
            task_summaries={"model": [
                {"code": "TASK001", "process": "model"},
                {"code": "TASK002", "process": "model", "context": "alt"},
            ]},
        )
        process_node = WorkspaceNode(
            node_id="process:model", node_type="process",
            search_key=root.search_key, code="model",
            parent_id=root.node_id, process="model", context="model",
            title="Model", accent="#ef5350", source=source,
        )
        root.children = [process_node]
        root.has_children = True
        root.loaded = True
        root.expanded = True
        model.replace_nodes([root])

        actions = _ActionHarness(process_node, model).process_count_actions(
            process_node.node_id, "tasks"
        )

        self.assertEqual(
            [action["taskCode"] for action in actions],
            ["TASK001", "TASK002"],
        )

    def test_local_freshness_clears_one_opened_process_at_a_time(self):
        model, node, source = self.make_model(notes={"model": 2})
        first_event = {
            "__kind__": "note",
            "code": "NOTE001",
            "search_type": "demo/asset",
            "search_code": "ASSET001",
            "process": "model",
            "__event_timestamp__": "2026-08-26T08:00:00",
        }
        second_event = {
            "__kind__": "note",
            "code": "NOTE002",
            "search_type": "demo/asset",
            "search_code": "ASSET001",
            "process": "rig",
            "__event_timestamp__": "2026-08-26T08:01:00",
        }

        model.apply_server_batch({
            "initialActivity": True,
            "activity": [first_event],
        })
        self.assertFalse(node.comments_updated)

        model.apply_server_batch({
            "initialActivity": False,
            "activity": [first_event, second_event],
        })
        self.assertTrue(node.comments_updated)
        self.assertEqual(
            node.updated_comment_processes,
            {"model", "rig"},
        )
        self.assertEqual(source.get_notes_count("rig"), 1)
        self.assertEqual(node.comments, 3)

        actions = _ActionHarness(node).process_count_actions(
            node.node_id, "notes"
        )
        self.assertTrue(next(
            action for action in actions
            if action["command"] == "model"
        )["badgeUpdated"])
        self.assertTrue(next(
            action for action in actions
            if action["command"] == "rig"
        )["badgeUpdated"])

        model.update_note_count(node.search_key, "model", 2)
        self.assertEqual(
            node.updated_comment_processes,
            {"model", "rig"},
        )

        model.mark_process_seen(node.node_id, "notes", "model")
        self.assertTrue(node.comments_updated)
        self.assertEqual(node.updated_comment_processes, {"rig"})

        model.mark_process_seen(node.node_id, "notes", "rig")
        self.assertFalse(node.comments_updated)
        self.assertEqual(node.updated_comment_processes, set())

    def test_relation_menu_uses_search_type_icon_and_color(self):
        class RelatedSType:
            def __init__(self, title, color, icon):
                self.title = title
                self.color = color
                self.icon = icon

            def get_pretty_name(self):
                return self.title

            def get_stype_color(self, fmt="hex"):
                self.assert_hex_format(fmt)
                return self.color

            @staticmethod
            def assert_hex_format(fmt):
                if fmt != "hex":
                    raise AssertionError(fmt)

            def get_info(self):
                return {"icon": self.icon}

        parent_stype = RelatedSType(
            "Assets Category", "#607d8b", "FAS_FOLDER_OPEN"
        )
        child_stype = RelatedSType(
            "Episode", "#42a5f5", "FAS_FILM"
        )

        class Project:
            stypes = {
                "demo/category": parent_stype,
                "demo/episode": child_stype,
            }

        class RootSType:
            @staticmethod
            def get_schema():
                return type("Schema", (), {
                    "parents": [{"to": "demo/category"}],
                    "children": [{"from": "demo/episode"}],
                })()

            @staticmethod
            def get_project():
                return Project()

        class Source:
            @staticmethod
            def get_stype():
                return RootSType()

        node = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset 1",
            source=Source(),
        )
        model = WorkspaceItemModel()
        model.replace_nodes([node])

        actions = _ActionHarness(node, model).relation_menu_actions(
            node.node_id
        )

        parent, _separator, child = actions
        self.assertEqual(parent["icon"], "folder-open")
        self.assertEqual(parent["accent"], "#607d8b")
        self.assertTrue(parent["accentIcon"])
        self.assertFalse(parent["translate"])
        self.assertEqual(child["icon"], "film")
        self.assertEqual(child["accent"], "#42a5f5")


if __name__ == "__main__":
    unittest.main()
