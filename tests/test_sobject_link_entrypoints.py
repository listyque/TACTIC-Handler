import unittest
import json
import tempfile
from types import SimpleNamespace

from PySide6.QtCore import QSettings

from modern_ui.controllers.commands import CommandsMixin
from modern_ui.controllers.item_operations import ItemOperationsMixin
from modern_ui.menu_schema import DEFAULT_MENUS, TEMPORARY_TOOL_WINDOWS
from modern_ui.workspace_models.windows import FloatingWindowModel


class _WindowModel:
    def __init__(self):
        self.opened = []

    def show_window(self, window_id):
        self.opened.append(window_id)


class _CommandsHarness(CommandsMixin):
    def __init__(self):
        self.debug_log = None
        self.window_model = _WindowModel()
        self._sobject_link_request = {}
        self.messages = []

    def _notify(self, message):
        self.messages.append(message)


class _ItemOperationsHarness(ItemOperationsMixin):
    def __init__(self, node):
        self.debug_log = None
        self.node = node
        self.opened = []
        self.messages = []
        self.selected = []
        self._sobject_link_request = {}

    def _node_for_any(self, _node_id):
        return self.node

    def _file_object_for_node(self, _node_id):
        return None

    def select_sobject(self, search_key):
        self.selected.append(search_key)

    def open_window(self, window_id):
        self.opened.append(window_id)

    def _notify(self, message):
        self.messages.append(message)


def _relation_node(relationship="instance"):
    definition = {
        "relationship": relationship,
        "instance_type": "demo/asset_in_episode",
    }
    return SimpleNamespace(
        node_type="relation",
        search_key="demo/episode?code=EPISODE001",
        source=object(),
        relationship=relationship,
        relation={"stype": object(), "definition": definition},
    )


class SObjectLinkEntrypointTests(unittest.TestCase):
    def test_contextless_link_entries_are_not_advertised(self):
        self.assertNotIn("temporary_link_sobjects", TEMPORARY_TOOL_WINDOWS)
        temporary_commands = {
            item.get("command")
            for item in DEFAULT_MENUS["temporary_tools"]
            if isinstance(item, dict)
        }
        sobject_commands = {
            item.get("command")
            for item in DEFAULT_MENUS["sobject"]
            if isinstance(item, dict)
        }
        self.assertNotIn("temporary_link_sobjects", temporary_commands)
        self.assertNotIn("link", sobject_commands)

    def test_window_rejects_missing_relation_context(self):
        controller = _CommandsHarness()

        controller.open_window("link_sobjects")

        self.assertEqual(controller.window_model.opened, [])
        self.assertTrue(controller.messages)

    def test_window_accepts_prepared_instance_relation_context(self):
        controller = _CommandsHarness()
        controller._sobject_link_request = {
            "stype": object(),
            "parent_sobject": object(),
            "relation": {"relationship": "instance"},
            "_prepared": True,
        }

        controller.open_window("link_sobjects")

        self.assertEqual(controller.window_model.opened, ["link_sobjects"])

    def test_relation_row_prepares_link_context(self):
        node = _relation_node()
        controller = _ItemOperationsHarness(node)

        controller.invoke_item_action("link_related", "relation-node")

        self.assertEqual(controller.opened, ["link_sobjects"])
        self.assertIs(controller._sobject_link_request["parent_sobject"], node.source)
        self.assertEqual(
            controller._sobject_link_request["relation"]["relationship"],
            "instance",
        )
        self.assertTrue(controller._sobject_link_request["_prepared"])

    def test_non_instance_relation_does_not_open_link_editor(self):
        controller = _ItemOperationsHarness(_relation_node("code"))

        controller.invoke_item_action("link_related", "relation-node")

        self.assertEqual(controller.opened, [])
        self.assertEqual(controller._sobject_link_request, {})
        self.assertTrue(controller.messages)

    def test_link_editor_visibility_is_not_restored_without_context(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(
                f"{directory}/windows.ini", QSettings.IniFormat
            )
            settings.setValue(
                "workspace/floatingWindowsV1",
                json.dumps([{
                    "window_id": "link_sobjects",
                    "title": "Old Link Editor",
                    "kind": "link_sobjects",
                    "x": 0.1,
                    "y": 0.1,
                    "width": 0.6,
                    "height": 0.7,
                    "visible": True,
                    "z": 10,
                    "blocking": False,
                    "geometry_mode": "relative",
                }]),
            )
            settings.sync()

            model = FloatingWindowModel(settings)
            link_window = next(
                window for window in model._windows
                if window.window_id == "link_sobjects"
            )

            self.assertFalse(link_window.visible)


if __name__ == "__main__":
    unittest.main()
