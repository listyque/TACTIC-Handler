import unittest
from types import SimpleNamespace
from unittest.mock import patch

from thlib.ui.controllers.item_actions import ItemActionsMixin
from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.menu_schema import DEFAULT_MENUS


class _ItemActionsHarness(ItemActionsMixin):
    def __init__(self, node, selected_ids=None):
        self.node = node
        self.tab = SimpleNamespace(selected_node_ids=list(selected_ids or []))

    def _node_for_any(self, _node_id):
        return self.node

    def _current_tab(self):
        return self.tab

    @staticmethod
    def _dcc_available(_capability):
        return False


class _ItemOperationsHarness(ItemOperationsMixin):
    def __init__(self, node):
        self.node = node
        self.tab = SimpleNamespace(selected_node_id="other-node")
        self.selected = []
        self.opened = []
        self.loaded = []
        self.messages = []
        self.debug_log = None

    def _node_for_any(self, _node_id):
        return self.node

    def _current_tab(self):
        return self.tab

    def select_result_node(self, *args):
        self.selected.append(args)

    def open_window(self, window_id):
        self.opened.append(window_id)

    def select_sobject(self, search_key):
        self.loaded.append(search_key)

    def _notify(self, message):
        self.messages.append(message)


def _sobject_node():
    return SimpleNamespace(
        node_id="child-sobject",
        node_type="sobject",
        search_key="demo/asset?code=ASSET001",
        source=SimpleNamespace(get_all_processes=lambda: {}),
        preview_url="",
        children=[],
        watch_state="none",
        relationship="",
    )


def _process_node():
    return SimpleNamespace(
        node_id="process-model",
        node_type="process",
        watch_state="none",
    )


class SObjectInfoEntrypointTests(unittest.TestCase):
    def test_snapshot_actions_require_a_real_cached_snapshot(self):
        node = _sobject_node()
        node.preview_url = "image://preview/asset"
        node.children = [SimpleNamespace(node_type="process")]

        class MayaActions(_ItemActionsHarness):
            _dcc_bridge = SimpleNamespace(selectedApplicationType="maya")

            @staticmethod
            def _dcc_available(_capability):
                return True

        controller = MayaActions(node)
        commands = {
            action.get("command")
            for action in controller.item_menu_actions(node.node_id)
        }
        self.assertTrue({"dcc_save_scene", "save"} <= commands)
        self.assertTrue(
            {"dcc_open", "dcc_import", "dcc_reference"}.isdisjoint(commands)
        )
        self.assertEqual(
            [
                action["command"]
                for action in controller.item_quick_actions(node.node_id)
            ],
            ["dcc_save_scene"],
        )

        node.source = SimpleNamespace(
            get_all_processes=lambda: {"publish": object()},
        )
        commands = {
            action.get("command")
            for action in controller.item_menu_actions(node.node_id)
        }
        self.assertTrue(
            {"dcc_open", "dcc_import", "dcc_reference"} <= commands
        )
        self.assertEqual(
            [
                action["command"]
                for action in controller.item_quick_actions(node.node_id)
            ],
            [
                "dcc_save_scene",
                "dcc_open",
                "dcc_import",
                "dcc_reference",
            ],
        )

    def test_process_menu_does_not_offer_database_editing(self):
        node = _process_node()
        actions = _ItemActionsHarness(node).item_menu_actions(node.node_id)

        commands = {item.get("command") for item in actions}
        self.assertNotIn("db", commands)
        self.assertIn("save", commands)
        self.assertIn("folder_versions", commands)
        self.assertFalse(actions[-1].get("separator", False))

    def test_regular_sobject_menu_exposes_info(self):
        node = _sobject_node()
        actions = _ItemActionsHarness(node).item_menu_actions(node.node_id)

        self.assertIn("sobject_info", {item.get("command") for item in actions})

    def test_sobject_menu_keeps_clipboard_primary_and_preview_advanced(self):
        node = _sobject_node()
        actions = _ItemActionsHarness(node).item_menu_actions(node.node_id)
        by_command = {item['command']: item for item in actions if 'command' in item}
        self.assertFalse(by_command['paste']['advanced'])
        self.assertTrue(by_command['preview']['advanced'])
        self.assertTrue(by_command['copy_skey']['advanced'])
        self.assertTrue(by_command['sobject_info']['advanced'])
        self.assertLessEqual(sum(not action['advanced'] for action in by_command.values()) + 1, 8)

    def test_multi_selection_menu_still_exposes_clicked_sobject_info(self):
        node = _sobject_node()
        actions = _ItemActionsHarness(
            node, [node.node_id, "another-sobject"]
        ).item_menu_actions(node.node_id)

        self.assertEqual(actions[0].get("command"), "sobject_info")
        by_command = {
            action.get("command"): action
            for action in actions if action.get("command")
        }
        self.assertEqual(
            by_command["db_selected"]["titleArgs"], [2]
        )
        self.assertEqual(
            by_command["delete_selected"]["titleArgs"], [2]
        )

    def test_info_action_selects_clicked_object_before_opening_report(self):
        node = _sobject_node()
        controller = _ItemOperationsHarness(node)

        controller.invoke_item_action("sobject_info", node.node_id)

        self.assertEqual(controller.selected[0][0:3], (
            node.node_id, node.search_key, node.node_type,
        ))
        self.assertEqual(controller.opened, ["sobject_info"])

    def test_table_detail_uses_native_parent_target(self):
        node = _sobject_node()
        controller = _ItemOperationsHarness(node)

        controller.invoke_table_widget_action(
            "sobject_detail",
            node.node_id,
            {"targetSearchKey": "demo/shot?code=SHOT001"},
        )

        self.assertEqual(
            controller.loaded, ["demo/shot?code=SHOT001"]
        )
        self.assertEqual(controller.opened, ["sobject_info"])

    def test_table_checkin_prepares_configured_process(self):
        node = _sobject_node()
        controller = _ItemOperationsHarness(node)
        configured = []
        prepared = []
        shown = []
        controller._checkin_controller = SimpleNamespace(
            set_process_and_context=lambda *args: configured.append(args)
        )
        controller._checkin_target_for_node = lambda selected: {
            "searchKey": selected.search_key,
        }
        controller._prepare_checkin_target = lambda target: (
            prepared.append(dict(target)) or True
        )
        controller.dock_model = SimpleNamespace(
            show_panel=lambda panel: shown.append(panel)
        )

        controller.invoke_table_widget_action(
            "checkin",
            node.node_id,
            {
                "targetSearchKey": node.search_key,
                "process": "model",
                "context": "model/review",
                "checkinMode": "sequence",
                "transferMode": "move",
            },
        )

        self.assertEqual(configured, [("model", "model/review")])
        self.assertEqual(prepared[0]["checkinType"], "sequence")
        self.assertEqual(prepared[0]["transferMode"], "move")
        self.assertEqual(prepared[0]["process"], "model")
        self.assertEqual(shown, ["drop_plate"])

    def test_table_file_and_metadata_widgets_reuse_sobject_report(self):
        node = _sobject_node()
        for kind in ("file_list", "metadata"):
            controller = _ItemOperationsHarness(node)
            controller.invoke_table_widget_action(kind, node.node_id, {})
            self.assertEqual(controller.opened, ["sobject_info"])

    def test_table_delete_widget_reuses_dependency_editor(self):
        node = _sobject_node()
        controller = _ItemOperationsHarness(node)
        calls = []
        controller.workspace_model = SimpleNamespace(
            node_for=lambda _node_id: node
        )
        controller.sobject_delete = SimpleNamespace(
            begin=lambda sources, mode: calls.append((sources, mode))
        )

        controller.invoke_table_widget_action(
            "delete", node.node_id, {"available": True}
        )

        self.assertEqual(calls, [([node.source], "items")])

    def test_table_explorer_widget_opens_native_resolved_path(self):
        node = _sobject_node()
        controller = _ItemOperationsHarness(node)
        with patch("thlib.global_functions.open_folder") as open_folder:
            controller.invoke_table_widget_action(
                "explorer", node.node_id, {"path": "D:/projects/demo"}
            )

        open_folder.assert_called_once_with("D:/projects/demo", False)

    def test_table_checkin_waits_for_native_parent_target(self):
        node = _sobject_node()
        controller = _ItemOperationsHarness(node)
        configured = []
        prepared = []
        shown = []
        controller._current_project_code = "demo"
        controller._checkin_controller = SimpleNamespace(
            set_process_and_context=lambda *args: configured.append(args)
        )
        controller._prepare_checkin_target = lambda target: (
            prepared.append(dict(target)) or True
        )
        controller.dock_model = SimpleNamespace(
            show_panel=lambda panel: shown.append(panel)
        )

        parent_key = "demo/shot?code=SHOT001"
        controller.invoke_table_widget_action(
            "checkin",
            node.node_id,
            {
                "targetSearchKey": parent_key,
                "process": "animation",
                "context": "animation/review",
            },
        )
        parent = SimpleNamespace(
            get_search_key=lambda: parent_key,
            get_code=lambda: "SHOT001",
            get_title=lambda: "Shot 001",
        )
        controller._finish_table_checkin(parent)

        self.assertEqual(controller.loaded, [parent_key])
        self.assertEqual(shown, ["drop_plate"])
        self.assertIs(prepared[0]["source"], parent)
        self.assertEqual(prepared[0]["process"], "animation")
        self.assertEqual(configured, [("animation", "animation/review")])
        self.assertEqual(controller._pending_table_checkin, {})

    def test_tools_menu_does_not_duplicate_sobject_info(self):
        commands = {
            item.get("command") for item in DEFAULT_MENUS["tools"]
        }

        self.assertNotIn("tool_sobject_info", commands)


if __name__ == "__main__":
    unittest.main()
