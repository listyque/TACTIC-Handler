import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


SCRIPT = (
    Path(__file__).parents[1]
    / "custom_scripts/niki_friends/tools/modules/checkin_textures_module.py"
)
RUNNER = (
    Path(__file__).parents[1]
    / "custom_scripts/niki_friends/tools/runners/textures_checkin_runner.py"
)


class TextureCheckinScriptTests(unittest.TestCase):
    def test_scene_lookup_and_checkin_use_the_public_api(self):
        scene_key = "dolly3d/assets?project=niki_friends&code=ASSET1&context=publish"
        commands = ModuleType("maya.cmds")
        commands.workspace = Mock(return_value="D:/project")
        commands.progressWindow = Mock(return_value=False)
        maya = ModuleType("maya")
        maya.__path__ = []
        maya.cmds = commands

        texture = SimpleNamespace(
            get_search_key=lambda: "dolly3d/texture?project=niki_friends&code=T1",
            get_project=lambda: SimpleNamespace(get_code=lambda: "niki_friends")
        )
        parent = SimpleNamespace(
            related=Mock(return_value=[texture]),
        )
        operation = SimpleNamespace(wait=Mock(return_value="queued"))
        ui = SimpleNamespace(checkin_files=Mock(return_value=operation))
        api = SimpleNamespace(
            sobject=Mock(return_value=parent),
            ui=ui,
        )

        with (
            patch.dict(sys.modules, {"maya": maya, "maya.cmds": commands}),
            patch("tactic_handler_api.get_api", return_value=api),
            patch(
                "tactic_handler_dcc.maya.get_skey_from_scene",
                return_value=scene_key,
            ) as get_skey_from_scene,
        ):
            spec = importlib.util.spec_from_file_location(
                "test_checkin_textures_module", SCRIPT
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(
                module.check_attached_textures(), ([texture], parent)
            )
            get_skey_from_scene.assert_called_once_with()

        api.sobject.assert_called_once_with(scene_key)
        parent.related.assert_called_once_with(search_type="dolly3d/texture")

        path = Path("D:/project/sourceimages/texture.png")
        self.assertEqual(
            module.checkin_texture_file(texture, str(path)), "queued"
        )
        ui.checkin_files.assert_called_once_with(
            texture.get_search_key(), "publish", "", [str(path)]
        )
        operation.wait.assert_called_once_with()

        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("maya_call", source)
        self.assertNotIn("executeInMainThreadWithResult", source)

        runner = RUNNER.read_text(encoding="utf-8")
        self.assertNotIn(".submit(", runner)


if __name__ == "__main__":
    unittest.main()
