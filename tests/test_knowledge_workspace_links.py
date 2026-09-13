from __future__ import annotations

from types import SimpleNamespace
import unittest

from thlib.ui.controller import ApplicationController
from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


def _sobject(
        node_id: str = "asset",
        search_key: str = "skey://demo/asset?code=ASSET0001",
) -> WorkspaceNode:
    return WorkspaceNode(
        node_id=node_id,
        node_type="sobject",
        search_key=search_key,
        code="ASSET0001",
        title="Asset",
    )


def _knowledge_controls(model: WorkspaceItemModel) -> list[dict]:
    controls = model.data(model.index(0, 0), model.ControlsRole)
    return [
        control for control in controls
        if control.get("command") == "knowledge_article"
    ]


class _Knowledge:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.opened: list[str] = []

    def open_for_object(self, search_key: str) -> bool:
        self.opened.append(search_key)
        return self.available


class _ItemActionHarness(ItemOperationsMixin):
    debug_log = None

    def __init__(self, node: WorkspaceNode, knowledge=None) -> None:
        self.node = node
        self.knowledge = knowledge
        self.notifications: list[str] = []

    def _node_for_any(self, _node_id: str):
        return self.node

    @staticmethod
    def _file_object_for_node(_node_id: str):
        return None

    def _notify(self, message: str) -> None:
        self.notifications.append(message)


class KnowledgeWorkspaceLinkTests(unittest.TestCase):
    def test_empty_index_keeps_the_workspace_indicator_absent(self):
        model = WorkspaceItemModel()
        model.replace_nodes([_sobject()])

        model.set_knowledge_index(None)

        self.assertEqual(_knowledge_controls(model), [])

    def test_link_index_adds_one_persistent_success_indicator(self):
        model = WorkspaceItemModel()
        model.replace_nodes([_sobject()])

        model.set_knowledge_index({
            "demo/asset?code=ASSET0001": [
                "DOC0001",
                "DOC0002",
            ],
        })

        controls = _knowledge_controls(model)
        self.assertEqual(len(controls), 1)
        self.assertTrue(controls[0]["active"])
        self.assertTrue(controls[0]["persistent"])
        self.assertTrue(controls[0]["success"])
        all_controls = model.data(model.index(0, 0), model.ControlsRole)
        self.assertEqual(all_controls[-1]["command"], "knowledge_article")

    def test_link_index_normalizes_both_prefixed_and_plain_search_keys(self):
        cases = (
            (
                "demo/asset?code=ASSET0001",
                "skey://demo/asset?code=ASSET0001",
            ),
            (
                "skey://demo/asset?code=ASSET0001",
                "demo/asset?code=ASSET0001",
            ),
        )
        for node_key, index_key in cases:
            with self.subTest(node_key=node_key, index_key=index_key):
                model = WorkspaceItemModel()
                model.replace_nodes([_sobject(search_key=node_key)])

                model.set_knowledge_index({index_key: ["DOC0001"]})

                self.assertEqual(len(_knowledge_controls(model)), 1)

    def test_sobjects_loaded_after_the_index_receive_the_indicator(self):
        model = WorkspaceItemModel()
        model.set_knowledge_index({
            "skey://demo/asset?code=ASSET0001": ["DOC0001"],
        })

        model.replace_nodes([_sobject()])

        self.assertEqual(len(_knowledge_controls(model)), 1)

    def test_clearing_index_removes_the_cached_indicator(self):
        model = WorkspaceItemModel()
        model.replace_nodes([_sobject()])
        model.set_knowledge_index({
            "skey://demo/asset?code=ASSET0001": ["DOC0001"],
        })
        self.assertEqual(len(_knowledge_controls(model)), 1)

        model.set_knowledge_index({})

        self.assertEqual(_knowledge_controls(model), [])

    def test_index_change_repaints_only_affected_visible_sobjects(self):
        model = WorkspaceItemModel()
        model.replace_nodes([
            _sobject("first", "skey://demo/asset?code=ASSET0001"),
            _sobject("second", "skey://demo/asset?code=ASSET0002"),
        ])
        changed_rows = []
        model.dataChanged.connect(
            lambda first, _last, _roles: changed_rows.append(first.row())
        )

        model.set_knowledge_index({
            "skey://demo/asset?code=ASSET0001": ["DOC0001"],
        })

        self.assertEqual(changed_rows, [0])

        changed_rows.clear()
        model.set_knowledge_index({
            "skey://demo/asset?code=ASSET0001": ["DOC0001"],
        })
        self.assertEqual(changed_rows, [])

    def test_application_update_reaches_every_retained_workspace_model(self):
        first = WorkspaceItemModel()
        first.replace_nodes([_sobject("first")])
        second = WorkspaceItemModel()
        second.replace_nodes([_sobject("second")])
        harness = SimpleNamespace(
            _workspace_models=lambda: iter((first, second)),
        )

        ApplicationController.update_workspace_knowledge_index(harness, {
            "skey://demo/asset?code=ASSET0001": ["DOC0001"],
        })

        self.assertEqual(len(_knowledge_controls(first)), 1)
        self.assertEqual(len(_knowledge_controls(second)), 1)
        self.assertEqual(
            harness._knowledge_link_index,
            {"skey://demo/asset?code=ASSET0001": ["DOC0001"]},
        )

    def test_item_action_opens_article_for_the_exact_sobject(self):
        node = _sobject()
        knowledge = _Knowledge()
        controller = _ItemActionHarness(node, knowledge)

        controller.invoke_item_action("knowledge_article", node.node_id)

        self.assertEqual(knowledge.opened, [node.search_key])
        self.assertEqual(controller.notifications, [])

    def test_item_action_is_safe_when_knowledge_base_is_unavailable(self):
        node = _sobject()
        controller = _ItemActionHarness(node, knowledge=None)

        controller.invoke_item_action("knowledge_article", node.node_id)

        self.assertEqual(
            controller.notifications,
            ["The linked Knowledge Base article is unavailable"],
        )


if __name__ == "__main__":
    unittest.main()
