import importlib.util
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = ROOT / "installer" / "shelf_install.py"
SPEC = importlib.util.spec_from_file_location("maya_shelf_installer", INSTALLER_PATH)
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class MayaInstallerTests(unittest.TestCase):
    def _archive(self, path, files):
        with zipfile.ZipFile(path, "w") as archive:
            for name, contents in files.items():
                archive.writestr(name, contents)

    def test_archive_replaces_install_and_strips_repository_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            target = directory / INSTALLER.INSTALL_DIR_NAME
            target.mkdir()
            (target / "obsolete.txt").write_text("old", encoding="utf-8")
            archive_path = directory / "handler.zip"
            self._archive(
                archive_path,
                {
                    "TACTIC-Handler-stable/launch.pyw": "from launch import main",
                    "TACTIC-Handler-stable/tactic_handler_dcc/maya.py": "def startup(): pass",
                    "TACTIC-Handler-stable/version.txt": "new",
                },
            )

            installed = Path(INSTALLER.install_archive(archive_path, directory))

            self.assertEqual(installed, target)
            self.assertEqual((installed / "version.txt").read_text(), "new")
            self.assertFalse((installed / "obsolete.txt").exists())

    def test_archive_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            archive_path = directory / "handler.zip"
            self._archive(
                archive_path,
                {
                    "../escaped.txt": "bad",
                    "root/launch.pyw": "",
                    "root/tactic_handler_dcc/maya.py": "",
                },
            )

            with self.assertRaisesRegex(ValueError, "Unsafe package entry"):
                INSTALLER.install_archive(archive_path, directory / "install")
            self.assertFalse((directory / "escaped.txt").exists())

    def test_shelf_bootstrap_reloads_without_stopping_live_client(self):
        command = INSTALLER.shelf_command(r"D:\apps\TACTIC-handler")

        self.assertIn("importlib.reload(tactic_handler_maya)", command)
        self.assertIn("tactic_handler_maya.startup(CURRENT_PATH)", command)
        self.assertNotIn(".stop(", command)

        save_command = INSTALLER.custom_script_command(
            r"D:\apps\TACTIC-handler",
            INSTALLER.BUTTONS["save"][-1],
        )
        self.assertIn("tools/runners/save_similar_runner", save_command)
        self.assertIn("project='niki_friends'", save_command)

    def test_download_rejects_non_http_package_url(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "HTTP or HTTPS"):
                INSTALLER.download_and_install("file:///tmp/handler.zip", directory)

    def test_install_creates_shelf_before_starting_download(self):
        events = []

        class Thread:
            def __init__(self, *args, **kwargs):
                events.append("thread-created")

            def start(self):
                events.append("download-started")

        application = INSTALLER.QtWidgets.QApplication.instance()
        if application is None:
            application = INSTALLER.QtWidgets.QApplication([])

        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(
                    INSTALLER,
                    "create_shelf",
                    side_effect=lambda *_args: events.append("shelf-created"),
                ) as create_shelf,
                patch.object(INSTALLER.threading, "Thread", Thread),
            ):
                dialog = INSTALLER.InstallerDialog()
                dialog.path_edit.setText(directory)
                dialog.preset_combo.setCurrentText("Animation")
                dialog._install()

                create_shelf.assert_called_once_with(
                    str(Path(directory) / INSTALLER.INSTALL_DIR_NAME),
                    "Animation",
                )
                self.assertEqual(
                    events,
                    ["shelf-created", "thread-created", "download-started"],
                )
                dialog._set_busy(False)
                dialog.close()

    def test_legacy_presets_create_their_exact_button_sets(self):
        class Commands:
            def __init__(self):
                self.deleted = []
                self.buttons = []

            def shelfLayout(self, name, exists=False, parent=None):
                if exists:
                    return True
                self.parent = parent
                return name

            def deleteUI(self, name):
                self.deleted.append(name)

            def shelfButton(self, **kwargs):
                self.buttons.append(kwargs)

        class Mel:
            def __init__(self):
                self.calls = []

            def eval(self, command):
                self.calls.append(command)
                return "ShelfTop"

        expected = {
            "Animation": [
                "Tactic Handler",
                "Append Save Current Scene",
                "Create nCache",
                "Save nCache and Current Scene",
                "Render Setup for Episodes",
            ],
            "Modelling/Rig": [
                "Tactic Handler",
                "Append Save Current Scene",
                "Checkin / Check Textures",
                "Attach References",
            ],
            "Full": [
                "Tactic Handler",
                "Append Save Current Scene",
                "Create nCache",
                "Save nCache and Current Scene",
                "Checkin / Check Textures",
                "Attach References",
                "Unpack All Caches",
                "Apply All Caches",
                "Render Setup for Episodes",
            ],
        }

        self.assertEqual(list(INSTALLER.INSTALL_PRESETS), list(expected))
        self.assertEqual(
            {code: values[-1] for code, values in INSTALLER.BUTTONS.items()},
            {
                "save": "tools/runners/save_similar_runner",
                "create_cache": "tools/runners/cache_create_runner",
                "save_cache": "tools/runners/cache_checkin_runner",
                "textures": "tools/runners/textures_checkin_runner",
                "references": "tools/runners/connect_assets_to_scene_runner",
                "unpack_cache": "tools/runners/cache_fetcher_runner",
                "apply_cache": "tools/runners/cache_apply_runner",
                "render_setup": "tools/runners/render_setup_runner",
            },
        )
        for preset, labels in expected.items():
            with self.subTest(preset=preset):
                commands = Commands()
                mel = Mel()
                shelf = INSTALLER.create_shelf(
                    str(ROOT), preset, commands, mel
                )

                self.assertEqual(shelf, INSTALLER.SHELF_NAME)
                self.assertEqual(commands.deleted, [INSTALLER.SHELF_NAME])
                self.assertEqual(commands.parent, "ShelfTop")
                self.assertEqual(
                    [button["label"] for button in commands.buttons], labels
                )
                self.assertTrue(
                    all(
                        Path(button["image1"]).is_file()
                        for button in commands.buttons
                    )
                )
                self.assertTrue(
                    all(
                        button["sourceType"] == "python"
                        for button in commands.buttons
                    )
                )
                self.assertIn(
                    "tactic_handler_maya.startup",
                    commands.buttons[0]["command"],
                )
                self.assertEqual(
                    mel.calls[-1], "saveAllShelves $gShelfTopLevel;"
                )

    def test_distributable_zip_contains_current_installer(self):
        bundle = ROOT / "installer" / "th_silent_install.zip"
        with zipfile.ZipFile(bundle) as archive:
            self.assertEqual(
                archive.read("drop_install.mel"),
                (ROOT / "installer" / "drop_install.mel").read_bytes(),
            )
            self.assertEqual(
                archive.read("shelf_install.py"),
                INSTALLER_PATH.read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
