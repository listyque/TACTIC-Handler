import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


TOOLS = (
    Path(__file__).parents[1]
    / "custom_scripts/niki_friends/tools"
)


def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CustomToolsScriptTests(unittest.TestCase):
    def test_tools_compile_without_the_removed_legacy_api(self):
        for path in TOOLS.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
            self.assertNotIn("tactic_handler_dcc.environment", source, path)
            self.assertNotIn("thenv.", source, path)

        for path in (TOOLS / "runners").glob("*_runner.py"):
            source = path.read_text(encoding="utf-8")
            self.assertIn("from importlib import import_module, reload", source)
            self.assertIn("RESULT =", source)

    def test_asset_lookup_resolves_a_shot_to_its_episode(self):
        scene_key = (
            "complex/shot?project=niki_friends&code=SHOT1&context=publish"
        )
        commands = ModuleType("maya.cmds")
        commands.progressWindow = Mock()
        maya = ModuleType("maya")
        maya.__path__ = []
        maya.cmds = commands

        shot = SimpleNamespace(
            get_stype=lambda: SimpleNamespace(get_code=lambda: "complex/shot"),
            get_value=lambda column: "EP1" if column == "scenes_code" else None,
        )
        assets = [object()]
        episode = SimpleNamespace(related=Mock(return_value=assets))
        episode_type = SimpleNamespace(get=Mock(return_value=episode))
        project = SimpleNamespace(stype=Mock(return_value=episode_type))
        api = SimpleNamespace(
            sobject=Mock(return_value=shot),
            project=Mock(return_value=project),
        )

        with (
            patch.dict(sys.modules, {"maya": maya, "maya.cmds": commands}),
            patch("tactic_handler_api.get_api", return_value=api),
            patch(
                "tactic_handler_dcc.maya.get_skey_from_scene",
                return_value=scene_key,
            ),
        ):
            module = load_script(
                "test_connect_assets_to_scene_module",
                TOOLS / "modules/connect_assets_to_scene_module.py",
            )
            self.assertEqual(module.check_attached_assets(), (assets, episode))

        api.sobject.assert_called_once_with(scene_key)
        episode_type.get.assert_called_once_with(code="EP1")
        episode.related.assert_called_once_with(search_type="dolly3d/assets")

    def test_cache_checkins_use_the_public_ui_api(self):
        scene_key = (
            "complex/shot?project=niki_friends&code=SHOT1&context=publish"
        )
        commands = ModuleType("maya.cmds")
        commands.workspace = Mock(return_value="D:/project")
        mel = ModuleType("maya.mel")
        maya = ModuleType("maya")
        maya.__path__ = []
        maya.cmds = commands
        maya.mel = mel

        operation = SimpleNamespace(wait=Mock(return_value="queued"))
        ui = SimpleNamespace(
            checkin_files=Mock(return_value=operation),
            checkin_from_maya=Mock(return_value=operation),
        )
        api = SimpleNamespace(ui=ui)
        sobject = SimpleNamespace(get_search_key=lambda: scene_key)
        runtime = SimpleNamespace(connected=True, client_id="maya-1")

        with (
            patch.dict(
                sys.modules,
                {"maya": maya, "maya.cmds": commands, "maya.mel": mel},
            ),
            patch("tactic_handler_api.get_api", return_value=api),
            patch("tactic_handler_dcc.maya.runtime", return_value=runtime),
            patch(
                "tactic_handler_dcc.maya.get_skey_from_scene",
                return_value=scene_key,
            ),
        ):
            module = load_script(
                "test_checkin_cache_module",
                TOOLS / "modules/checkin_cache_module.py",
            )
            self.assertEqual(
                module.checkin_cache_file(sobject, "D:/cache.zip"), "queued"
            )
            self.assertEqual(module.checkin_current_scene(sobject), "queued")

        ui.checkin_files.assert_called_once_with(
            scene_key, "cache", "", ["D:/cache.zip"]
        )
        ui.checkin_from_maya.assert_called_once_with(
            scene_key, "publish", "Added Cache", "maya-1"
        )


if __name__ == "__main__":
    unittest.main()
