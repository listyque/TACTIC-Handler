from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tactic_handler_dcc import connectors
from tactic_handler_dcc.runtime import DccEntrypoint
from tactic_handler_dcc import runtime as runtime_module
from thlib.ui.checkin_out import CheckinOutController
from thlib.ui.controllers.item_actions import ItemActionsMixin
from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.controllers.commands import CommandsMixin
from thlib.ui.workspace_models.state import WorkspaceState
from thlib.ui.workspace_models.windows import FloatingWindowModel


class _Connector:
    instances = []
    dispatch = staticmethod(lambda callback: callback())

    def __init__(self, handler_path):
        self.handler_path = Path(handler_path)
        self.exit_callback = None
        self.exit_callback_removed = False
        self.__class__.instances.append(self)

    @classmethod
    def instance(cls, handler_path=None):
        return cls(handler_path)

    @staticmethod
    def register(registry):
        registry.register("open_scene", lambda payload: payload)
        registry.register("prepare_checkin", lambda payload: payload)
        registry.register("execute_custom_script", lambda payload: payload)
        return registry

    def install_exit_callback(self, callback):
        self.exit_callback = callback

        def remove():
            self.exit_callback_removed = True

        return remove


class _Client:
    def __init__(self, application_type, options):
        self.application_type = application_type
        self.client_id = options["client_id"]
        self.registry = options["registry"]
        self.dispatch = options["dispatch"]
        self.on_event = options["on_event"]
        self._connected = threading.Event()
        self.requests = []
        self.events = []
        self.capability_refreshes = 0

    @property
    def connected(self):
        return self._connected.is_set()

    def start(self):
        pass

    def connect(self):
        self._connected.set()
        self.on_event({"type": "capabilities"})

    def wait_connected(self, timeout):
        return self._connected.wait(timeout)

    def request(self, target, action, payload, timeout):
        self.requests.append((target, action, payload, timeout))
        return {"accepted": True}

    def publish_event(self, action, status, payload):
        self.events.append((action, status, payload))

    def refresh_capabilities(self):
        self.capability_refreshes += 1

    def stop(self, wait=True):
        self._connected.clear()


class DccRuntimeTests(unittest.TestCase):
    def test_one_manifest_builds_nuke_actions_tools_and_configuration(self):
        module = ModuleType("tactic_handler_dcc.connectors.nuke")
        module.DCC_MANIFEST = {
            "application": "nuke",
            "title": "Nuke",
            "ui": {
                "item_actions": ({
                    "id": "open_script",
                    "capability": "open_scene",
                    "title": "Open in Nuke",
                    "icon": "folder_open",
                    "target": "file",
                    "scopes": ("snapshot",),
                    "requires_snapshot": True,
                },),
                "tool_actions": ({
                    "id": "show_viewer",
                    "capability": "show_viewer",
                    "title": "Show Viewer",
                    "icon": "visibility",
                },),
                "configuration": {
                    "title": "Nuke",
                    "description": "Nuke integration settings",
                    "sections": ({
                        "title": "Scripts",
                        "fields": ({
                            "key": "script_format",
                            "type": "choice",
                            "default": "nk",
                            "choices": ({"label": "Nuke", "value": "nk"},),
                        },),
                    },),
                },
                "focus_preferences": {"open_scene": "focus_after_open"},
            },
        }

        with patch.object(
            connectors,
            "iter_modules",
            return_value=[SimpleNamespace(name="_template"), SimpleNamespace(name="nuke")],
        ), patch.object(connectors, "import_module", return_value=module):
            self.assertEqual(
                [item["id"] for item in connectors.dcc_item_actions("nuke")],
                ["open_script"],
            )
            self.assertEqual(
                [item["id"] for item in connectors.dcc_tool_actions("nuke")],
                ["show_viewer"],
            )
            bridge = SimpleNamespace(
                selectedApplicationType="nuke",
                has_dcc_capability=lambda capability: capability == "show_viewer",
            )
            owner = SimpleNamespace(
                _menus=SimpleNamespace(actions=lambda _menu_id: []),
                _dcc_bridge=bridge,
                can_administer=False,
            )
            self.assertIn(
                "dcc_tool:show_viewer",
                [
                    action.get("command")
                    for action in CommandsMixin.menu_actions(owner, "tools")
                ],
            )
            self.assertEqual(
                connectors.dcc_focus_preference("nuke", "open_scene"),
                "focus_after_open",
            )
            page = connectors.dcc_configuration("dcc.nuke")
            self.assertEqual(page["title"], "Nuke")
            self.assertEqual(page["sections"][0]["fields"][0]["key"], "script_format")
            with patch(
                "thlib.environment.env_server.get_server_presets",
                return_value={"presets_list": []},
            ):
                pages = WorkspaceState().configuration_page_model.records()
            self.assertIn("dcc.nuke", [item["target"] for item in pages])
            window = next(
                item for item in FloatingWindowModel._defaults()
                if item.window_id == "dcc.nuke"
            )
            self.assertEqual(
                FloatingWindowModel._content_source(window),
                "ConfigurationPage.qml",
            )

    def test_copyable_template_is_hidden_until_it_is_renamed(self):
        root = Path(__file__).resolve().parents[1] / "tactic_handler_dcc"
        self.assertTrue((root / "_template.py").is_file())
        self.assertTrue((root / "connectors" / "_template.py").is_file())
        template = __import__("tactic_handler_dcc._template", fromlist=[""])
        self.assertEqual(
            template._entrypoint.connector_module,
            "tactic_handler_dcc.connectors._template",
        )
        self.assertEqual(template.status()["state"], "stopped")
        self.assertNotIn(
            "template",
            [manifest["application"] for manifest in connectors.dcc_manifests()],
        )

    def test_copied_root_template_finds_same_named_connector(self):
        root = Path(__file__).resolve().parents[1] / "tactic_handler_dcc"
        module_name = "tactic_handler_dcc.nuke_boilerplate"
        connector_name = "tactic_handler_dcc.connectors.nuke_boilerplate"
        connector_module = ModuleType(connector_name)
        connector_module.DCC_MANIFEST = {
            "application": "nuke_boilerplate",
            "title": "Nuke Boilerplate",
        }
        connector_module.Connector = _Connector
        spec = importlib.util.spec_from_file_location(
            module_name, root / "_template.py"
        )
        copied_module = importlib.util.module_from_spec(spec)
        clients = []

        def client_factory(application_type, **options):
            client = _Client(application_type, options)
            clients.append(client)
            return client

        with patch.dict(sys.modules, {
            module_name: copied_module,
            connector_name: connector_module,
        }), patch.object(
            runtime_module.importlib,
            "reload",
            side_effect=lambda module: module,
        ):
            spec.loader.exec_module(copied_module)
            self.assertEqual(
                copied_module._entrypoint.connector_module,
                connector_name,
            )
            self.assertEqual(
                copied_module._entrypoint.application_type,
                "nuke_boilerplate",
            )
            runtime = copied_module.startup(
                root.parent,
                client_factory=client_factory,
                session_finder=lambda: {"available": True},
                notifier=lambda *_args: None,
                register_exit=False,
            )
            clients[0].connect()
            self.assertTrue(runtime.wait_until_connected(1.0))
            self.assertEqual(clients[0].application_type, "nuke_boilerplate")
            copied_module.stop()

    def test_connector_manifest_adds_trigger_actions_without_a_central_list(self):
        module = ModuleType("tactic_handler_dcc.connectors.nuke")
        module.DCC_MANIFEST = {
            "application": "nuke",
            "title": "Nuke",
            "script_triggers": (
                ("scene.open", "Open script", "folder_open"),
                ("scene.save", "Save script", "save"),
            ),
        }
        with patch.object(
            connectors,
            "iter_modules",
            return_value=[SimpleNamespace(name="nuke")],
        ), patch.object(connectors, "import_module", return_value=module):
            self.assertEqual(connectors.dcc_trigger_actions(), (
                ("dcc.nuke.scene.open", "Nuke · Open script", "folder_open", True),
                ("dcc.nuke.scene.save", "Nuke · Save script", "save", True),
            ))

    def test_manifest_and_connector_are_enough_for_another_dcc(self):
        connector_module = ModuleType("tests.fake_nuke_connector")
        connector_module.DCC_MANIFEST = {
            "application": "nuke",
            "title": "Nuke",
            "script_triggers": (
                ("scene.open", "Open script", "folder_open"),
            ),
        }
        connector_module.NukeConnector = _Connector
        clients = []

        def client_factory(application_type, **options):
            client = _Client(application_type, options)
            clients.append(client)
            return client

        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "launch.pyw").write_text("# launcher\n", encoding="utf-8")
            with patch.dict(sys.modules, {connector_module.__name__: connector_module}), \
                    patch.object(
                        runtime_module.importlib,
                        "reload",
                        side_effect=lambda module: module,
                    ):
                entrypoint = DccEntrypoint(
                    connector_module.__name__, "NukeConnector"
                )
                runtime = entrypoint.startup(
                    root,
                    client_factory=client_factory,
                    session_finder=lambda: {"available": True},
                    notifier=lambda *_args: None,
                    register_exit=True,
                )
                clients[0].connect()
                self.assertTrue(runtime.wait_until_connected(1.0))

                self.assertEqual(clients[0].application_type, "nuke")
                self.assertTrue(clients[0].client_id.startswith("nuke-"))
                self.assertEqual(
                    clients[0].registry.capabilities(),
                    ["execute_custom_script", "open_scene", "prepare_checkin"],
                )
                self.assertEqual(runtime.status["message"], (
                    "Nuke is connected to TACTIC Handler"
                ))
                self.assertEqual(clients[0].events[0][0], "nuke_connector")
                self.assertIsNotNone(runtime.connector.exit_callback)
                exit_owner = runtime.connector

                same_runtime = entrypoint.startup(root)
                self.assertIs(same_runtime, runtime)
                self.assertEqual(len(clients), 1)
                self.assertEqual(clients[0].capability_refreshes, 1)
                entrypoint.stop()
                self.assertTrue(exit_owner.exit_callback_removed)

    def test_non_maya_scene_options_reach_the_selected_connector(self):
        calls = []

        class Operations(ItemOperationsMixin):
            debug_log = None
            _dcc_bridge = SimpleNamespace(
                selectedApplicationType="nuke",
                selectedClient="nuke-1",
                has_dcc_capability=lambda _action: True,
                error="",
            )
            _checkin_controller = SimpleNamespace(
                generatePreviews=False,
                start_dcc_scene_checkin=lambda target, payload, capability: (
                    calls.append((target, payload, capability)) or True
                ),
            )

            @staticmethod
            def _node_for_any(_node_id):
                return SimpleNamespace(source=object())

            @staticmethod
            def _checkin_target_for_node(_node):
                return {"searchKey": "demo/asset?code=A1"}

            @staticmethod
            def _dcc_item_payload(_node, _file_object=None):
                return {"search_key": "demo/asset?code=A1"}

            @staticmethod
            def _notify(_message):
                pass

        self.assertTrue(Operations().request_dcc_scene_checkin(
            "asset", {"scene_type": "nukeScript"}
        ))
        self.assertEqual(calls[0][1]["scene_type"], "nukeScript")
        self.assertEqual(calls[0][1]["application_type"], "nuke")
        self.assertEqual(calls[0][2], "prepare_checkin")

    def test_non_maya_capabilities_drive_the_existing_file_menu(self):
        node = SimpleNamespace(
            node_id="snapshot-1",
            node_type="snapshot",
            source=object(),
            is_multiple=False,
            is_versionless=False,
        )

        class Actions(ItemActionsMixin):
            _dcc_bridge = SimpleNamespace(selectedApplicationType="nuke")

            @staticmethod
            def _node_for_any(_node_id):
                return node

            @staticmethod
            def _current_tab():
                return SimpleNamespace(selected_node_ids=[])

            @staticmethod
            def _dcc_available(capability):
                return capability in {
                    "open_scene", "import_file", "prepare_checkin",
                }

        module = ModuleType("tactic_handler_dcc.connectors.nuke")
        module.DCC_MANIFEST = {"application": "nuke", "title": "Nuke"}
        with patch.object(
            connectors,
            "dcc_manifests",
            return_value=(connectors.dcc_manifest(module),),
        ):
            actions = {
                action.get("command"): action
                for action in Actions().item_menu_actions(node.node_id)
                if action.get("command")
            }
        self.assertIn("dcc:open", actions)
        self.assertIn("dcc:import", actions)
        self.assertIn("dcc:save", actions)
        self.assertNotIn("dcc:reference", actions)
        self.assertNotIn("secondaryCommand", actions["dcc:open"])

    def test_non_maya_scene_uses_the_deferred_commit_queue_flow(self):
        class Bridge:
            selectedApplicationType = "nuke"
            selectedClient = "nuke-1"

            def __init__(self):
                self.commands = []

            @staticmethod
            def has_dcc_capability(action):
                return action in {"get_current_scene", "prepare_checkin"}

            def send_client_command(self, client_id, action, payload, timeout):
                self.commands.append((client_id, action, payload, timeout))
                return "inspect-request"

        controller = SimpleNamespace(
            _dcc_bridge=Bridge(),
            _dcc_checkin_requests={},
            _application=SimpleNamespace(notify=Mock()),
            prepare_external_checkin=Mock(),
        )
        target = {
            "searchKey": "demo/asset?code=A1",
            "source": object(),
            "projectCode": "demo",
            "title": "Asset",
            "code": "A1",
            "process": "comp",
            "context": "comp",
            "description": "",
            "version": 0,
        }

        self.assertTrue(CheckinOutController.start_dcc_scene_checkin(
            controller,
            target,
            {
                "application_type": "nuke",
                "client_id": "nuke-1",
                "generate_previews": False,
            },
            "prepare_checkin",
        ))
        self.assertEqual(controller._dcc_bridge.commands[0], (
            "nuke-1", "get_current_scene", {}, 15.0,
        ))
        request = controller._dcc_checkin_requests["inspect-request"]
        self.assertEqual(request["stage"], "deferred_scene")

        CheckinOutController._queue_dcc_scene_checkin(
            controller,
            request,
            {
                "path": "D:/shots/example.nk",
                "scene_type": "nukeScript",
                "extension": "nk",
            },
        )
        queued = controller.prepare_external_checkin.call_args.kwargs
        self.assertEqual(queued["file_types"], ["main"])
        self.assertEqual(queued["dcc_scene"]["applicationType"], "nuke")
        self.assertEqual(queued["dcc_scene"]["sceneType"], "nukeScript")


if __name__ == "__main__":
    unittest.main()
