import unittest
import json
import tempfile
from types import SimpleNamespace


from thlib.ui.controllers.commands import CommandsMixin
from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.menu_schema import DEFAULT_MENUS, TOOL_WINDOWS
from thlib.ui.workspace_models.windows import FloatingWindowModel


class _WindowModel:
    def __init__(self):
        self.opened = []
        self.visible = set()
        self.raised = []

    def show_window(self, window_id):
        self.opened.append(window_id)
        self.visible.add(window_id)

    def is_window_visible(self, window_id):
        return window_id in self.visible

    def raise_window(self, window_id):
        self.raised.append(window_id)


class _Emitter:
    def __init__(self):
        self.count = 0
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self):
        for callback in list(self.callbacks):
            callback()
        self.count += 1


class _CommandsHarness(CommandsMixin):
    def __init__(self):
        self.debug_log = None
        self.window_model = _WindowModel()
        self._sobject_link_request = {}
        self.sobjectLinkRequested = _Emitter()
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
        self._sobject_editor_request = {}

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
        self.assertNotIn("tool_link_sobjects", TOOL_WINDOWS)
        tool_commands = {
            item.get("command")
            for item in DEFAULT_MENUS["tools"]
            if isinstance(item, dict)
        }
        sobject_commands = {
            item.get("command")
            for item in DEFAULT_MENUS["sobject"]
            if isinstance(item, dict)
        }
        self.assertNotIn("tool_link_sobjects", tool_commands)
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
        self.assertEqual(controller.sobjectLinkRequested.count, 1)

    def test_relation_context_reaches_controller_before_first_window_show(self):
        controller = _CommandsHarness()
        stype = object()
        parent = object()
        relation = {
            "relationship": "instance",
            "instance_type": "demo/asset_in_episode",
        }
        controller._sobject_link_request = {
            "stype": stype,
            "parent_sobject": parent,
            "relation": relation,
            "_prepared": True,
        }
        events = []
        controller.sobjectLinkRequested.connect(lambda: events.append((
            "session",
            controller._sobject_link_request.get("parent_sobject"),
        )))
        original_show = controller.window_model.show_window

        def show_window(window_id):
            events.append(("window", window_id))
            original_show(window_id)

        controller.window_model.show_window = show_window

        controller.open_window("link_sobjects")

        self.assertEqual(events, [
            ("session", parent),
            ("window", "link_sobjects"),
        ])

    def test_visible_window_restarts_with_new_relation_context(self):
        controller = _CommandsHarness()
        controller.window_model.visible.add("link_sobjects")
        controller._sobject_link_request = {
            "stype": object(),
            "parent_sobject": object(),
            "relation": {"relationship": "instance"},
            "_prepared": True,
        }

        controller.open_window("link_sobjects")

        self.assertEqual(controller.sobjectLinkRequested.count, 1)
        self.assertEqual(controller.window_model.opened, [])
        self.assertEqual(
            controller.window_model.raised, ["link_sobjects"]
        )

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

    def test_relation_row_preserves_schema_path_for_related_create(self):
        node = _relation_node()
        node.relation["definition"]["path"] = "child_asset"
        controller = _ItemOperationsHarness(node)

        controller.invoke_item_action("add_related", "relation-node")

        self.assertEqual(controller.opened, ["add_sobject"])
        self.assertEqual(
            controller._sobject_editor_request["relation"],
            node.relation["definition"],
        )

    def test_non_instance_relation_does_not_open_link_editor(self):
        controller = _ItemOperationsHarness(_relation_node("code"))

        controller.invoke_item_action("link_related", "relation-node")

        self.assertEqual(controller.opened, [])
        self.assertEqual(controller._sobject_link_request, {})
        self.assertTrue(controller.messages)

    def test_link_editor_visibility_is_not_restored_without_context(self):
        with tempfile.TemporaryDirectory():
            settings = {
                "workspace/floatingWindows": json.dumps([{
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
            }

            model = FloatingWindowModel(settings)
            link_window = next(
                window for window in model._windows
                if window.window_id == "link_sobjects"
            )

            self.assertFalse(link_window.visible)


if __name__ == "__main__":
    unittest.main()
