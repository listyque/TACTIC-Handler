from __future__ import annotations

import unittest
from unittest.mock import patch

from thlib.ui.controllers.search_runtime import SearchRuntimeMixin
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


class _Source:
    def __init__(self, **info):
        self._info = info

    def get_info(self):
        return dict(self._info)


class _Task(_Source):
    pass


def _node(code, title, **info):
    return WorkspaceNode(
        node_id=f"key-{code}",
        node_type="sobject",
        search_key=f"key-{code}",
        code=code,
        title=title,
        loaded=True,
        source=_Source(code=code, **info),
    )


class ResultOrganizationTests(unittest.TestCase):
    def test_default_order_is_natural_name_order(self):
        model = WorkspaceItemModel()
        model.replace_nodes([
            _node("3", "Asset 10"),
            _node("1", "asset 2"),
            _node("2", "Asset 1"),
        ])

        self.assertEqual(
            [node.title for node in model._roots],
            ["Asset 1", "asset 2", "Asset 10"],
        )

    def test_status_grouping_keeps_each_sobject_once(self):
        model = WorkspaceItemModel()
        model.set_organization(group_mode="status")
        model.replace_nodes([
            _node("1", "Tree", status="Approved"),
            _node("2", "Rock", status="Pending"),
            _node("3", "Bush", status="Approved"),
        ])

        groups = [node for node in model._items if node.node_type == "group"]
        objects = [node for node in model._items if node.node_type == "sobject"]
        self.assertEqual([group.title for group in groups], ["Approved", "Pending"])
        self.assertEqual(len(objects), 3)
        self.assertEqual(len({node.node_id for node in objects}), 3)
        self.assertEqual(groups[0].child_count, 2)

        model.toggle_node(groups[0].node_id)
        self.assertNotIn("Bush", [node.title for node in model._items])
        self.assertNotIn("Tree", [node.title for node in model._items])

    def test_task_grouping_uses_first_workflow_status_without_duplicates(self):
        model = WorkspaceItemModel()
        nodes = [_node("A", "Asset A"), _node("B", "Asset B")]
        tasks = {
            "A": [
                _Task(process="model", status="Approved"),
                _Task(process="model", status="In Progress"),
            ],
            "B": [_Task(process="model", status="Pending")],
        }
        model.set_organization(
            group_mode="task_status",
            task_process="model",
            task_records=tasks,
            loaded_task_codes={"A", "B"},
            task_statuses=[
                {"key": "Pending", "accent": "#111111"},
                {"key": "In Progress", "accent": "#222222"},
                {"key": "Approved", "accent": "#333333"},
            ],
        )
        model.replace_nodes(nodes)

        groups = [node for node in model._items if node.node_type == "group"]
        objects = [node for node in model._items if node.node_type == "sobject"]
        self.assertEqual(
            [group.title for group in groups], ["Pending", "In Progress"]
        )
        self.assertEqual(len(objects), 2)
        self.assertEqual(len({node.node_id for node in objects}), 2)
        self.assertEqual(groups[1].accent, "#222222")

    def test_server_query_defaults_to_legacy_name_order(self):
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        with (
            patch.object(tc, "get_snapshots_updates_list", return_value=[]),
            patch.object(tc, "get_sobjects", return_value=({}, {})) as query,
            patch.object(env_inst, "get_project_by_code", return_value=None),
        ):
            SearchRuntimeMixin._query_sobjects(
                "prod/asset", "project", (), [], 20, 0
            )

        self.assertEqual(query.call_args.kwargs["order_bys"], ["name"])

    def test_table_column_sort_is_shared_by_query_and_result_model(self):
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        model = WorkspaceItemModel()
        model.set_organization(sort_mode="column:priority:desc")
        model.replace_nodes([
            _node("A", "First", priority="2"),
            _node("B", "Second", priority="10"),
        ])
        self.assertEqual([node.code for node in model._roots], ["B", "A"])

        with (
            patch.object(tc, "get_snapshots_updates_list", return_value=[]),
            patch.object(tc, "get_sobjects", return_value=({}, {})) as query,
            patch.object(env_inst, "get_project_by_code", return_value=None),
        ):
            SearchRuntimeMixin._query_sobjects(
                "prod/asset", "project", (), [], 20, 0,
                "column:priority:desc",
            )
        self.assertEqual(query.call_args.kwargs["order_bys"], ["priority desc"])

    def test_config_search_type_loads_without_project_stype(self):
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        widget_config = object()
        with (
            patch.object(
                env_inst, "get_stype_by_code", return_value=None
            ),
            patch.object(env_inst, "get_project_by_code", return_value=None),
            patch.object(
                tc, "get_sobjects",
                return_value=({"WIDGET_CONFIG001": widget_config}, {}),
            ) as query,
        ):
            records, _info, stype = SearchRuntimeMixin._query_sobjects(
                "config/widget_config", "demo", (), [], 20, 0
            )

        self.assertEqual(records, [widget_config])
        self.assertIsNone(stype)
        self.assertEqual(
            query.call_args.kwargs["check_snapshots_updates"], []
        )


if __name__ == "__main__":
    unittest.main()
