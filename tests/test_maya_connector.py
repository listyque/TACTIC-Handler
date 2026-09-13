from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import queue
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

from handler_server.client import ThinClient
from handler_server.registry import CommandRegistry
from handler_server.server import HandlerServer
from tactic_handler_dcc.connectors.maya import MayaConnector
from thlib.ui.checkin_out import CheckinOutController
from thlib.ui.controllers.item_actions import ItemActionsMixin
from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.dcc_options import DccOptionsController


class _Mel:
    def __init__(self, commands):
        self.commands = commands
        self.result = True
        self.calls = []

    def eval(self, source):
        self.calls.append(source)
        if source == "$tmp = $gShelfTopLevel":
            return "ShelfLayout"
        if source.startswith("addNewShelfTab "):
            title = json.loads(source[len("addNewShelfTab "):-1])
            self.commands.shelves[title] = {}
            self.commands.shelf_labels[title] = title
            return title
        return self.result


class _Cmds:
    def __init__(self, scene_path, shelf_dir=None):
        self.scene_path = str(scene_path)
        self.scene_type = "mayaAscii"
        self.modified = False
        self.selection = ["|root|mesh"]
        self.attributes = {}
        self.file_calls = []
        self.workspace_calls = []
        self.shown_windows = []
        self.focused_controls = []
        self.open_error = None
        self.shelf_dir = str(shelf_dir or Path.cwd())
        self.shelves = {}
        self.shelf_buttons = []
        self.shelf_tabs = []
        self.shelf_labels = {}
        self.deleted_ui = []

    @staticmethod
    def about(**options):
        if options.get("version"):
            return "2026"
        key = next(iter(options), "")
        return f"maya-{key}"

    def file(self, *args, **options):
        if options.get("query"):
            if options.get("type"):
                return [self.scene_type]
            if options.get("sceneName"):
                return self.scene_path
            if options.get("modified"):
                return self.modified
        if "rename" in options:
            self.scene_path = str(options["rename"])
        if options.get("open") and args:
            self.scene_path = str(args[0])
            if self.open_error is not None:
                raise self.open_error
        if options.get("save"):
            self.modified = False
        self.file_calls.append((args, dict(options)))
        return self.scene_path

    def workspace(self, *args, **options):
        if options.get("rootDirectory") or options.get("fullName"):
            return "D:/maya-project"
        self.workspace_calls.append((args, dict(options)))
        return ""

    def showWindow(self, name):
        self.shown_windows.append(str(name))

    def setFocus(self, name):
        self.focused_controls.append(str(name))

    def ls(self, **_options):
        return list(self.selection)

    def attributeQuery(self, name, **_options):
        return name in self.attributes

    def addAttr(self, _node, longName, **_options):
        self.attributes[longName] = ""

    def setAttr(self, name, value, **_options):
        self.attributes[name.rpartition(".")[2]] = value

    def getAttr(self, name):
        return self.attributes.get(name.rpartition(".")[2])

    @staticmethod
    def currentTime(**_options):
        return 1

    @staticmethod
    def playblast(**options):
        target = options.get("completeFilename") or options.get("filename")
        if target:
            path = Path(target)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"playblast")
        return target

    def internalVar(self, **options):
        if options.get("userShelfDir"):
            return self.shelf_dir
        return ""

    def shelfLayout(self, name, **options):
        if options.get("exists"):
            return name in self.shelves
        self.shelves[name] = dict(options)
        return name

    def deleteUI(self, name):
        self.deleted_ui.append(name)
        self.shelves.pop(name, None)
        self.shelf_labels.pop(name, None)
        self.shelf_buttons = [
            button for button in self.shelf_buttons
            if button.get("parent") != name
        ]

    def shelfButton(self, **options):
        self.shelf_buttons.append(dict(options))
        return "shelfButton{}".format(len(self.shelf_buttons))

    def shelfTabLayout(self, name, **options):
        self.shelf_tabs.append((name, dict(options)))
        if options.get("query"):
            children = list(self.shelves)
            if options.get("childArray"):
                return children
            if options.get("tabLabel"):
                return [
                    self.shelf_labels.get(child, child)
                    for child in children
                ]
        if options.get("edit") and options.get("tabLabel"):
            shelf, label = options["tabLabel"]
            self.shelf_labels[shelf] = label
        return name


class _FileObject:
    def __init__(self, path):
        self.path = str(path)

    def get_full_abs_path(self):
        return self.path


class MayaConnectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def make_connector(
        self, scene_path, handler_path=None, shelf_dir=None,
    ):
        calls = []
        commands = _Cmds(scene_path, shelf_dir)
        connector = MayaConnector(
            commands, _Mel(commands), lambda callback: (
                calls.append(callback), callback()
            )[1],
            handler_path=handler_path,
        )
        return connector, calls

    def test_registry_exposes_fixed_maya_capabilities_without_eval(self):
        with TemporaryDirectory() as directory:
            scene = Path(directory) / "scene.ma"
            scene.write_text("// maya", encoding="utf-8")
            connector, dispatch_calls = self.make_connector(scene)
            registry = connector.register(CommandRegistry())

            capabilities = registry.capabilities()
            self.assertIn("prepare_checkin", capabilities)
            self.assertIn("get_temp_playblast", capabilities)
            self.assertIn("focus_application", capabilities)
            self.assertIn("open_scene", capabilities)
            self.assertIn("execute_custom_script", capabilities)
            self.assertIn("execute_script_file", capabilities)
            self.assertIn("create_script_shelf", capabilities)
            self.assertNotIn("exec", capabilities)
            self.assertNotIn("eval", capabilities)
            self.assertEqual(
                registry.execute("get_current_scene", {})["path"],
                str(scene),
            )
            queue_preview = registry.execute("get_temp_playblast", {})
            self.assertEqual(queue_preview["scene_type"], "mayaAscii")
            self.assertEqual(
                Path(queue_preview["preview_path"]).name, "playblast.jpg"
            )
            self.assertEqual(
                Path(queue_preview["preview_path"]).read_bytes(),
                b"playblast",
            )
            self.assertEqual(dispatch_calls, [])

    def test_script_shelf_is_recreated_with_launcher_and_saved_buttons(self):
        project_root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as shelf_dir:
            connector, _calls = self.make_connector(
                "scene.ma", handler_path=project_root,
                shelf_dir=shelf_dir,
            )
            payload = {
                "project": "demo",
                "name": "Animation Tools",
                "buttons": [{
                    "title": "Save",
                    "description": "Save the current scene",
                    "icon": "save",
                    "script": "tools/save",
                }, {
                    "title": "Textures",
                    "description": "Check textures",
                    "icon": "missing-shelf-icon",
                    "script": "tools/textures",
                }],
            }

            result = connector.create_script_shelf(payload)
            updated = connector.create_script_shelf(payload)

            self.assertEqual(result["title"], "Animation Tools")
            self.assertEqual(result["buttons"], 3)
            self.assertFalse(result["updated"])
            self.assertTrue(updated["updated"])
            self.assertEqual(result["shelf"], "Animation Tools")
            self.assertIn(
                'addNewShelfTab "Animation Tools";', connector.mel.calls
            )
            self.assertEqual(
                [button["label"] for button in connector.cmds.shelf_buttons],
                ["TACTIC Handler", "Save", "Textures"],
            )
            self.assertEqual(
                connector.cmds.shelf_buttons[1]["annotation"],
                "Save the current scene",
            )
            self.assertIn(
                "tactic_handler_maya.startup",
                connector.cmds.shelf_buttons[0]["command"],
            )
            self.assertIn(
                "execute_custom_script('tools/save', project='demo')",
                connector.cmds.shelf_buttons[1]["command"],
            )
            for button in connector.cmds.shelf_buttons:
                compile(button["command"], "<maya-shelf>", "exec")
            self.assertTrue(Path(
                connector.cmds.shelf_buttons[1]["image1"]
            ).is_file())
            self.assertEqual(
                connector.cmds.shelf_buttons[2]["image1"],
                "pythonFamily.png",
            )
            self.assertEqual(
                [
                    button["imageOverlayLabel"]
                    for button in connector.cmds.shelf_buttons
                ],
                ["TH", "Save", "Textur"],
            )
            self.assertTrue(all(
                button["overlayLabelBackColor"]
                == (0.08, 0.08, 0.08, 0.85)
                for button in connector.cmds.shelf_buttons
            ))
            self.assertTrue(all(
                button["overlayLabelColor"] == (0.9, 0.9, 0.9)
                for button in connector.cmds.shelf_buttons
            ))
            self.assertEqual(
                connector.cmds.deleted_ui, [result["shelf"]]
            )
            self.assertEqual(
                connector.cmds.shelf_tabs[-1][1]["tabLabel"],
                (result["shelf"], "Animation Tools"),
            )
            self.assertEqual(
                connector.mel.calls.count(
                    "saveAllShelves $gShelfTopLevel;"
                ),
                2,
            )

    def test_script_shelf_updates_an_existing_maya_tab_with_the_same_label(self):
        project_root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as shelf_dir:
            connector, _calls = self.make_connector(
                "scene.ma", handler_path=project_root,
                shelf_dir=shelf_dir,
            )
            connector.cmds.shelves["ManualShelf"] = {}
            connector.cmds.shelf_labels["ManualShelf"] = "Animation Tools"

            result = connector.create_script_shelf({
                "project": "demo",
                "name": "animation tools",
                "buttons": [],
            })

            self.assertTrue(result["updated"])
            self.assertEqual(connector.cmds.deleted_ui, ["ManualShelf"])

    def test_script_shelf_replaces_the_old_hashed_shelf_preference(self):
        project_root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as shelf_dir:
            legacy_name = "TACTIC_e32325d7dafc"
            legacy_file = Path(shelf_dir, "shelf_" + legacy_name + ".mel")
            legacy_file.write_text("// old generated shelf", encoding="utf-8")
            connector, _calls = self.make_connector(
                "scene.ma", handler_path=project_root,
                shelf_dir=shelf_dir,
            )
            connector.cmds.shelves[legacy_name] = {}

            result = connector.create_script_shelf({
                "project": "demo",
                "name": "Animation Tools",
                "buttons": [],
            })

            self.assertTrue(result["updated"])
            self.assertEqual(connector.cmds.deleted_ui, [legacy_name])
            self.assertFalse(legacy_file.exists())
            self.assertEqual(result["shelf"], "Animation Tools")

    def test_script_shelf_rejects_unsafe_script_paths_before_replacing_it(self):
        project_root = Path(__file__).resolve().parents[1]
        connector, _calls = self.make_connector(
            "scene.ma", handler_path=project_root,
        )
        connector.cmds.shelves["TACTIC_Handler"] = {}

        with self.assertRaisesRegex(ValueError, "safe custom script"):
            connector.create_script_shelf({
                "project": "demo",
                "name": "Unsafe",
                "buttons": [{"script": "../outside"}],
            })

        self.assertIn("TACTIC_Handler", connector.cmds.shelves)
        self.assertEqual(connector.cmds.deleted_ui, [])

    def test_script_editor_file_runs_inside_the_persistent_maya_console(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "custom_scripts" / ".temp"
            root.mkdir(parents=True)
            first = root / "first.py"
            second = root / "second.py"
            published = (
                Path(directory)
                / "custom_scripts/demo/tools/published.py"
            )
            published.parent.mkdir(parents=True)
            first.write_text(
                "from tactic_handler_api.operations import check_blocking_call\n"
                "check_blocking_call()\n"
                "maya_value = 41\n"
                "print('maya')\n",
                encoding="utf-8",
            )
            second.write_text("print(maya_value + 1)\n", encoding="utf-8")
            published.write_text(
                "print(maya_value + 2)\n", encoding="utf-8"
            )
            connector, _dispatch_calls = self.make_connector(
                "scene.ma", handler_path=directory
            )
            registry = connector.register(CommandRegistry())

            maya_output = io.StringIO()
            with contextlib.redirect_stdout(maya_output):
                first_result = registry.execute(
                    "execute_script_file", {"path": str(first)}
                )
            self.assertEqual(first_result["output"].strip(), "maya")
            self.assertEqual(maya_output.getvalue().strip(), "maya")
            self.assertEqual(
                registry.execute("execute_script_file", {"path": str(second)})[
                    "output"
                ].strip(),
                "42",
            )
            self.assertEqual(
                registry.execute(
                    "execute_custom_script",
                    {"project": "demo", "script": "tools/published"},
                )["output"].strip(),
                "43",
            )
            with self.assertRaisesRegex(ValueError, "staging file"):
                registry.execute(
                    "execute_script_file",
                    {"path": str(Path(directory) / "outside.py")},
                )
            with self.assertRaisesRegex(ValueError, "safe project"):
                registry.execute(
                    "execute_custom_script",
                    {"project": "../demo", "script": "tools/published"},
                )

    def test_maya_item_menu_exposes_manifest_option_actions(self):
        node = SimpleNamespace(
            node_id="snapshot-1",
            node_type="snapshot",
            source=object(),
            is_multiple=False,
            is_versionless=False,
        )

        class Actions(ItemActionsMixin):
            _dcc_bridge = SimpleNamespace(selectedApplicationType="maya")

            @staticmethod
            def _node_for_any(_node_id):
                return node

            @staticmethod
            def _current_tab():
                return SimpleNamespace(selected_node_ids=[])

            @staticmethod
            def _dcc_available(_capability):
                return True

        actions = {
            action.get("command"): action
            for action in Actions().item_menu_actions(node.node_id)
            if action.get("command")
        }

        self.assertEqual(actions["dcc:open"]["secondaryCommand"], "dcc_options:open")
        self.assertEqual(actions["dcc:open"]["icon"], "folder_open")
        self.assertEqual(actions["dcc:save"]["secondaryCommand"], "dcc_options:save")
        self.assertEqual(actions["dcc:import"]["secondaryCommand"], "dcc_options:import")
        self.assertEqual(actions["dcc:reference"]["secondaryCommand"], "dcc_options:reference")

    def test_maya_save_options_forward_selected_scene_format(self):
        application = SimpleNamespace(
            window_model=SimpleNamespace(close_window=lambda _window: None)
        )
        requests = []
        with patch("thlib.ui.dcc_options.env_read_config", return_value={}), \
                patch("thlib.ui.dcc_options.env_write_config"), \
                patch(
                    "thlib.ui.dcc_options.read_dcc_preferences",
                    return_value={"scene_type": "mayaBinary"},
                ):
            options = DccOptionsController(
                application,
                lambda action_id, node_id, payload: requests.append(
                    (action_id, node_id, payload)
                ) or True,
            )
            options.attach_dcc_bridge(SimpleNamespace(
                selectedApplicationType="maya",
                has_dcc_capability=lambda _capability: True,
                stateChanged=SimpleNamespace(connect=lambda _callback: None),
            ))
            options.prepare_target("save", "asset-1", "Asset 1")
            options.set_value("scene_type", "mayaAscii")
            options.confirm()

        self.assertEqual(
            requests,
            [("save", "asset-1", {"scene_type": "mayaAscii"})],
        )

    def test_maya_save_options_qml_exposes_scene_format_control(self):
        qml = Path(__file__).resolve().parents[1] / "thlib" / "ui" / "qml"
        application = SimpleNamespace(
            window_model=SimpleNamespace(close_window=lambda _window: None)
        )
        with patch("thlib.ui.dcc_options.env_read_config", return_value={}), \
                patch(
                    "thlib.ui.dcc_options.read_dcc_preferences",
                    return_value={"scene_type": "mayaBinary"},
                ):
            options = DccOptionsController(
                application, lambda _action, _node_id, _payload: True
            )
        options.attach_dcc_bridge(SimpleNamespace(
            selectedApplicationType="maya",
            has_dcc_capability=lambda _capability: True,
            stateChanged=SimpleNamespace(connect=lambda _callback: None),
        ))
        options.prepare_target("save", "asset-1", "Asset 1")

        engine = QQmlEngine()
        engine.addImportPath(str(qml))
        engine.rootContext().setContextProperty(
            "dccOptionsController", options
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml / "DccOptionsView.qml"))
        )
        view = component.createWithInitialProperties({
            "theme": theme,
        })

        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        visual_items = [view]
        for item in visual_items:
            visual_items.extend(item.childItems())
        scene_type = next(
            item for item in visual_items
            if item.objectName() == "dccSettingControl_scene_type"
        )
        self.assertIsNotNone(scene_type)
        self.assertEqual(scene_type.property("currentIndex"), 0)
        view.deleteLater()
        theme.deleteLater()

    def test_file_objects_and_payloads_use_one_maya_connector(self):
        with TemporaryDirectory() as directory:
            scene = Path(directory) / "scene.ma"
            asset = Path(directory) / "asset.ma"
            scene.write_text("// scene", encoding="utf-8")
            asset.write_text("// asset", encoding="utf-8")
            connector, _dispatch_calls = self.make_connector(scene)

            imported = connector.import_scene(_FileObject(asset))
            referenced = connector.reference_file({
                "path": str(asset),
                "namespace": "asset_main",
            })
            connector.set_info_to_scene(
                "demo/asset?project=demo&code=ASSET001", "model"
            )

            self.assertEqual(imported["opened_path"], str(asset.resolve()))
            self.assertEqual(referenced["opened_path"], str(asset.resolve()))
            self.assertEqual(
                connector.get_skey_from_scene(),
                "skey://demo/asset?project=demo&code=ASSET001&context=model",
            )
            modes = [
                options for _args, options in connector.cmds.file_calls
                if options.get("i") or options.get("reference")
            ]
            self.assertTrue(any(options.get("i") for options in modes))
            self.assertTrue(any(options.get("reference") for options in modes))

    def test_scene_load_runtime_errors_remain_local_to_maya(self):
        with TemporaryDirectory() as directory:
            scene = Path(directory) / "scene.ma"
            scene.write_text("// scene", encoding="utf-8")
            connector, _dispatch_calls = self.make_connector(scene)
            connector.cmds.open_error = RuntimeError(
                "Maya scene plug-in reported an error"
            )

            result = connector.open_scene({"path": str(scene)})

            self.assertTrue(result["success"])
            self.assertFalse(result["cancelled"])
            self.assertEqual(result["opened_path"], str(scene.resolve()))

    def test_open_scene_focuses_maya_before_the_save_prompt(self):
        with TemporaryDirectory() as directory:
            scene = Path(directory) / "scene.ma"
            scene.write_text("// scene", encoding="utf-8")
            connector, _dispatch_calls = self.make_connector(scene)
            connector.cmds.modified = True
            events = []

            with patch.object(
                connector, "_activate_main_window",
                side_effect=lambda: events.append("focus"),
            ), patch.object(
                connector.mel, "eval",
                side_effect=lambda _source: events.append("prompt") or False,
            ):
                result = connector.open_scene({"path": str(scene)})

            self.assertEqual(events, ["focus", "prompt"])
            self.assertTrue(result["cancelled"])

    def test_open_options_apply_the_selected_scene_workspace(self):
        with TemporaryDirectory() as directory:
            scene = Path(directory) / "asset" / "scene.ma"
            scene.parent.mkdir()
            scene.write_text("// scene", encoding="utf-8")
            connector, _dispatch_calls = self.make_connector(scene)

            connector.open_scene({
                "path": str(scene),
                "setup_workdir": True,
                "force": True,
            })

            self.assertEqual(
                connector.cmds.workspace_calls,
                [((str(scene.parent.resolve()),), {"openWorkspace": True})],
            )

    def test_scene_path_errors_are_still_handler_command_errors(self):
        connector, _dispatch_calls = self.make_connector("missing.ma")

        with self.assertRaises(FileNotFoundError):
            connector.open_scene({"path": "missing.ma"})

    def test_prepare_checkin_returns_local_preparation_only(self):
        with TemporaryDirectory() as directory:
            scene = Path(directory) / "scene.ma"
            scene.write_text("// scene", encoding="utf-8")
            connector, _dispatch_calls = self.make_connector(scene)

            result = connector.prepare_checkin({
                "search_key": "demo/asset?code=A1",
                "context": "model",
                "generate_previews": False,
            })

            self.assertEqual(result["files"][0]["path"], str(scene))
            self.assertEqual(result["files"][0]["role"], "main")
            self.assertEqual(result["previews"], [])
            self.assertEqual(result["application_info"]["p"], "maya-p")
            self.assertNotIn("snapshot", result)
            self.assertNotIn("checkin", result)

    def test_file_actions_return_focus_to_maya_unless_disabled(self):
        with TemporaryDirectory() as directory:
            scene = Path(directory) / "scene.ma"
            asset = Path(directory) / "asset.ma"
            scene.write_text("// scene", encoding="utf-8")
            asset.write_text("// asset", encoding="utf-8")
            connector, _dispatch_calls = self.make_connector(scene)

            connector.prepare_checkin({"generate_previews": False})
            connector.open_scene({"path": str(scene), "force": True})
            connector.import_file({"path": str(asset)})
            connector.reference_file({"path": str(asset)})

            self.assertEqual(
                connector.cmds.shown_windows, ["MayaWindow"] * 4
            )
            self.assertEqual(
                connector.cmds.focused_controls, ["MayaWindow"] * 4
            )

            connector.import_file({
                "path": str(asset),
                "focus_application": False,
            })
            self.assertEqual(len(connector.cmds.shown_windows), 4)
            self.assertEqual(len(connector.cmds.focused_controls), 4)

    def test_focus_activates_the_native_maya_window(self):
        connector, _dispatch_calls = self.make_connector("scene.ma")
        window = Mock()
        window.isMinimized.return_value = True
        window.winId.return_value = 451

        with patch.object(
            connector, "get_maya_window", return_value=window
        ), patch.object(
            connector, "_activate_windows_window"
        ) as activate_native, patch(
            "tactic_handler_dcc.connectors.maya.os.name", "nt"
        ):
            connector._activate_main_window()

        window.showNormal.assert_called_once_with()
        window.raise_.assert_called_once_with()
        window.activateWindow.assert_called_once_with()
        activate_native.assert_called_once_with(451)

    def test_unnamed_scene_is_renamed_to_prepared_paths_before_save(self):
        with TemporaryDirectory() as directory:
            scene = Path(directory) / "asset_model_v001.ma"
            preview = Path(directory) / "asset_model_v001.jpg"
            preview.write_bytes(b"preview")
            connector, _dispatch_calls = self.make_connector("")

            result = connector.prepare_checkin({
                "path": str(scene),
                "preview_path": str(preview),
                "scene_type": "mayaAscii",
            })

            rename_call = next(
                options for _args, options in connector.cmds.file_calls
                if "rename" in options
            )
            save_call = next(
                options for _args, options in connector.cmds.file_calls
                if options.get("save")
            )
            self.assertEqual(rename_call["rename"], str(scene))
            self.assertEqual(save_call["type"], "mayaAscii")
            self.assertEqual(result["files"][0]["path"], str(scene))
            self.assertEqual(result["previews"][0]["path"], str(preview))

    def test_unnamed_scene_without_prepared_path_fails_before_maya_save(self):
        connector, _dispatch_calls = self.make_connector("")

        with self.assertRaisesRegex(RuntimeError, "prepared save path"):
            connector.save_current_scene()

        self.assertFalse(any(
            options.get("save")
            for _args, options in connector.cmds.file_calls
        ))

    def test_maya_checkin_starts_legacy_queue_preparation(self):
        class Bridge:
            selectedApplicationType = "maya"

            def __init__(self):
                self.commands = []

            @staticmethod
            def has_dcc_capability(action):
                return action in {
                    "get_current_scene", "prepare_checkin",
                    "save_current_scene",
                }

            def send_active_command(self, action, payload, timeout):
                self.commands.append((action, payload, timeout))
                return "inspect-request"

        class Checkin:
            generatePreviews = True

            def __init__(self):
                self.calls = []

            def start_dcc_scene_checkin(
                self, target, payload, capability
            ):
                self.calls.append((target, payload, capability))
                return True

        class Operations(ItemOperationsMixin):
            debug_log = None

            def __init__(self):
                self._dcc_bridge = Bridge()
                self._checkin_controller = Checkin()
                self.messages = []

            @staticmethod
            def _node_for_any(_node_id):
                return SimpleNamespace(source=object())

            @staticmethod
            def _checkin_target_for_node(_node):
                return {
                    "searchKey": "demo/asset?code=A1",
                    "source": object(),
                    "projectCode": "demo",
                    "title": "Asset",
                    "code": "A1",
                    "process": "model",
                    "context": "model",
                    "description": "",
                    "version": 0,
                }

            @staticmethod
            def _dcc_item_payload(_node, _file_object=None):
                return {"search_key": "demo/asset?code=A1"}

            def _notify(self, message):
                self.messages.append(message)

        operations = Operations()

        operations.invoke_item_action("dcc:save", "asset")

        target, payload, capability = (
            operations._checkin_controller.calls[0]
        )
        self.assertEqual(target["searchKey"], "demo/asset?code=A1")
        self.assertTrue(payload["generate_previews"])
        self.assertEqual(capability, "prepare_checkin")

    def test_checkin_controller_queues_real_playblast_before_maya_save(self):
        class Bridge:
            selectedApplicationType = "maya"

            def __init__(self):
                self.commands = []

            @staticmethod
            def has_dcc_capability(action):
                return action in {
                    "get_current_scene", "get_temp_playblast",
                    "prepare_checkin",
                }

            def send_active_command(self, action, payload, timeout):
                self.commands.append((action, payload, timeout))
                return "preview-request"

            def send_client_command(self, client_id, action, payload, timeout):
                self.commands.append((client_id, action, payload, timeout))
                return "preview-request"

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
            "process": "model",
            "context": "model",
            "description": "",
            "version": 0,
        }

        started = CheckinOutController.start_dcc_scene_checkin(
            controller,
            target,
            {
                "generate_previews": True,
                "scene_type": "mayaBinary",
                "update_versionless": True,
                "client_id": "maya-42",
                "application_type": "maya",
            },
            "prepare_checkin",
        )

        self.assertTrue(started)
        self.assertEqual(
            controller._dcc_bridge.commands[0],
            ("maya-42", "get_temp_playblast", {}, 60.0),
        )
        with TemporaryDirectory() as directory:
            preview = Path(directory) / "maya_preview.jpg"
            preview.write_bytes(b"real playblast")
            request = controller._dcc_checkin_requests["preview-request"]
            CheckinOutController._queue_dcc_scene_checkin(
                controller,
                request,
                {
                    "scene_type": "mayaAscii",
                    "extension": "ma",
                    "preview_path": str(preview),
                    "preview_type": "playblast",
                },
            )

            queued = controller.prepare_external_checkin.call_args.kwargs
            self.assertEqual(Path(queued["paths"][1]), preview)
            self.assertEqual(
                Path(queued["paths"][1]).read_bytes(), b"real playblast"
            )
            self.assertEqual(
                queued["file_types"], ["main", "playblast"]
            )
            self.assertTrue(queued["update_versionless"])

    def test_scene_save_reports_the_handler_start_error(self):
        class Checkin:
            generatePreviews = False

            @staticmethod
            def start_dcc_scene_checkin(_target, _payload, _capability):
                return False

        class Operations(ItemOperationsMixin):
            debug_log = None

            def __init__(self):
                self._dcc_bridge = SimpleNamespace(
                    error="Maya client disconnected",
                    has_dcc_capability=lambda _action: True,
                )
                self._checkin_controller = Checkin()
                self.messages = []

            @staticmethod
            def _node_for_any(_node_id):
                return SimpleNamespace(source=object())

            @staticmethod
            def _checkin_target_for_node(_node):
                return {"searchKey": "demo/asset?code=A1"}

            @staticmethod
            def _dcc_item_payload(_node, _file_object=None):
                return {}

            def _notify(self, message):
                self.messages.append(message)

        operations = Operations()

        self.assertFalse(operations.request_dcc_scene_checkin("asset"))
        self.assertEqual(operations.messages[-1], "Maya client disconnected")

    def test_failed_queue_playblast_stops_scene_preparation(self):
        messages = []
        request = {
            "stage": "deferred_scene",
            "payload": {"generate_previews": True},
        }
        controller = SimpleNamespace(
            _dcc_bridge=SimpleNamespace(),
            _dcc_checkin_requests={"preview-request": request},
            _application=SimpleNamespace(notify=messages.append),
        )

        CheckinOutController._remote_dcc_finished(
            controller,
            "preview-request",
            False,
            {},
            "Viewport is unavailable",
        )

        self.assertEqual(controller._dcc_checkin_requests, {})
        self.assertEqual(messages[-1], "Viewport is unavailable")

    def test_commit_saves_final_maya_name_then_continues_checkin(self):
        class Bridge:
            def __init__(self):
                self.commands = []

            def send_client_command(
                self, client_id, action, payload, timeout
            ):
                self.commands.append((client_id, action, payload, timeout))
                return "save-request"

        continued = []
        controller = SimpleNamespace(
            _dcc_bridge=Bridge(),
            _dcc_checkin_requests={},
            _operation_id=0,
            _operation_state="idle",
            _operation_stage="",
            _operation_message="",
            _operation_file="",
            _operation_progress=0.0,
            _operation_error="",
            _operation_payload=None,
            _operation_repository={},
            _operation_cancel_requested=False,
            _operation_cancel_event=SimpleNamespace(clear=lambda: None),
            _queue_operation=False,
            preparationChanged=SimpleNamespace(emit=lambda: None),
            operationFinished=SimpleNamespace(emit=lambda *_args: None),
            _start_operation=lambda payload, repository, queued: continued.append(
                (payload, repository, queued)
            ),
        )
        naming = [["scene", {
            "versioned": {
                "paths": ["assets/versions"],
                "names": [["asset_model_v001", ".ma"]],
            },
        }]]
        operation = {
            "searchKey": "demo/asset?code=A1",
            "context": "model",
            "process": "model",
            "files": [{"path": "D:/temp/scene.ma", "type": "main"}],
            "virtualSnapshot": naming,
            "dccScene": {
                "clientId": "maya-42",
                "capability": "prepare_checkin",
                "sceneType": "mayaAscii",
            },
        }
        repository_root = TemporaryDirectory()
        self.addCleanup(repository_root.cleanup)
        repository = {
            "value": [repository_root.name, "", "", "base"]
        }

        self.assertTrue(CheckinOutController._start_prepared_dcc_scene(
            controller, operation, repository
        ))

        client_id, action, dcc_payload, timeout = (
            controller._dcc_bridge.commands[0]
        )
        self.assertEqual(client_id, "maya-42")
        self.assertEqual(action, "prepare_checkin")
        self.assertEqual(
            Path(dcc_payload["path"]),
            Path(repository_root.name)
            / "assets/versions/asset_model_v001.ma",
        )
        self.assertEqual(timeout, 120.0)

        request = controller._dcc_checkin_requests["save-request"]
        CheckinOutController._finish_prepared_dcc_scene(
            controller,
            request,
            True,
            {
                "success": True,
                "application_info": {"p": "Autodesk Maya 2026"},
                "files": [{"path": dcc_payload["path"]}],
            },
            "",
        )

        self.assertEqual(len(continued), 1)
        self.assertEqual(
            continued[0][0]["files"][0]["path"], dcc_payload["path"]
        )
        self.assertEqual(
            continued[0][0]["applicationInfo"]["p"],
            "Autodesk Maya 2026",
        )
        self.assertTrue(continued[0][2])

    def test_handler_server_dispatches_maya_command_once(self):
        with TemporaryDirectory() as directory:
            scene = Path(directory) / "scene.ma"
            scene.write_text("// scene", encoding="utf-8")
            connector, dispatch_calls = self.make_connector(
                scene, handler_path=directory
            )
            registry = connector.register(CommandRegistry())
            server = HandlerServer(token="maya-connector-test")
            port = server.start()
            maya = ThinClient(
                "127.0.0.1",
                port,
                "maya-connector-test",
                "maya",
                registry=registry,
                client_id="maya-connector",
                dispatch=connector.dispatch,
            )
            operator = ThinClient(
                "127.0.0.1",
                port,
                "maya-connector-test",
                "operator",
                client_id="maya-operator",
                on_event=queue.Queue().put,
            )
            try:
                maya.start()
                operator.start()
                self.assertTrue(maya.wait_connected(3.0))
                self.assertTrue(operator.wait_connected(3.0))

                result = operator.request(
                    "maya-connector", "get_current_scene", {}, timeout=2
                )

                connector.cmds.open_error = RuntimeError(
                    "Maya scene plug-in reported an error"
                )
                opened = operator.request(
                    "maya-connector", "open_scene",
                    {"path": str(scene)}, timeout=2,
                )
                script_root = Path(directory) / "custom_scripts" / ".temp"
                script_root.mkdir(parents=True)
                script = script_root / "remote.py"
                script.write_text(
                    "print('remote Maya output')\n", encoding="utf-8"
                )
                published = (
                    Path(directory)
                    / "custom_scripts/demo/tools/published.py"
                )
                published.parent.mkdir(parents=True)
                published.write_text(
                    "print(TACTIC_SCRIPT_KWARGS['event'])\n"
                    "RESULT = TACTIC_PROJECT_CODE\n",
                    encoding="utf-8",
                )
                script_result = operator.request(
                    "maya-connector", "execute_script_file",
                    {"path": str(script)}, timeout=2,
                )
                published_result = operator.request(
                    "maya-connector", "execute_custom_script",
                    {
                        "project": "demo",
                        "script": "tools/published",
                        "kwargs": {"event": "scene.open"},
                    },
                    timeout=2,
                )

                self.assertEqual(result["path"], str(scene))
                self.assertTrue(opened["success"])
                self.assertEqual(opened["opened_path"], str(scene.resolve()))
                self.assertEqual(
                    script_result["output"].strip(), "remote Maya output"
                )
                self.assertEqual(
                    published_result["output"].strip(),
                    "scene.open",
                )
                self.assertEqual(published_result["result"], "'demo'")
                self.assertEqual(len(dispatch_calls), 4)
            finally:
                operator.stop()
                maya.stop()
                server.stop()


if __name__ == "__main__":
    unittest.main()
