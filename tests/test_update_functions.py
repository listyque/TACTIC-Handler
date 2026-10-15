"""Portable release validation and rollback regression checks."""

import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from thlib import update_functions as updates
from thlib import update_installer


def make_app(root: Path, version=(1, 2, 3, 4)) -> Path:
    app = root / "app"
    (app / "thlib" / "ui" / "qml").mkdir(parents=True)
    (app / "side_tools" / "batch_scheduler").mkdir(parents=True)
    (app / "server_plugin" / "tactic_handler_queries").mkdir(parents=True)
    (app / "settings").mkdir()
    (app / "settings" / "user.json").write_text('{"safe": true}')
    (app / "temp_custom_scripts").mkdir()
    (app / "temp_custom_scripts" / "private.py").write_text("SECRET")
    (app / "launch.py").write_text("print('ready')")
    (app / "CHANGELOG.md").write_text(
        "# Changelog\n\n## 1.2.3.5 - 2026-10-04\n\n"
        "- Fixed UI.\n\n## 1.2.3.4 - 2026-10-03\n\n- Earlier change.\n",
        encoding="utf-8",
    )
    (app / "thlib" / "version.json").write_text(json.dumps(
        dict(zip(updates.VERSION_FIELDS, version))))
    (app / "thlib" / "ui" / "qml" / "Main.qml").write_text("Item {}")
    (app / "side_tools" / "batch_scheduler" / "scheduler_classes.py").write_text(
        "def show(): pass\n"
    )
    (app / "server_plugin" / "tactic_handler_queries" / "command.py").write_text(
        "class QueryCommand: pass\n"
    )
    return app


class UpdateArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_version_uses_final_four_numbers_in_zip_name(self):
        self.assertEqual(
            updates.version_from_filename("snapshot_003_0_5_1_0.zip"),
            (0, 5, 1, 0),
        )
        self.assertIsNone(updates.version_from_filename("snapshot_003.zip"))

    def test_bundled_changelog_matches_current_version(self):
        changelog = updates.read_changelog()
        headings = re.findall(
            r"^## (\d+\.\d+\.\d+\.\d+) - \d{4}-\d{2}-\d{2}$",
            changelog, re.MULTILINE,
        )
        versions = [tuple(map(int, heading.split("."))) for heading in headings]
        self.assertTrue(versions)
        self.assertEqual(versions[0], updates.current_version())
        self.assertEqual(versions, sorted(set(versions), reverse=True))
        for version in versions:
            self.assertTrue(updates.release_notes(changelog, version))

    def test_archive_bundles_history_and_defaults_to_exact_version_notes(self):
        app = make_app(self.root)
        changelog = updates.read_changelog(app)
        self.assertEqual(
            updates.release_notes(changelog, (1, 2, 3, 5)), '- Fixed UI.',
        )
        self.assertEqual(
            updates.release_notes(changelog, (1, 2, 3, 4)), '- Earlier change.',
        )
        self.assertEqual(updates.release_notes(changelog, (1, 2, 3, 50)), '')
        archive = self.root / '1_2_3_5.zip'
        updates.create_update_archive(app, archive, (1, 2, 3, 5))
        with zipfile.ZipFile(archive) as stream:
            self.assertEqual(stream.read('CHANGELOG.md'), (app / 'CHANGELOG.md').read_bytes())
            self.assertEqual(
                json.loads(stream.read('release.json'))['changes'], '- Fixed UI.',
            )
        staged = self.root / 'staged'
        updates.stage_archive(archive, staged, (1, 2, 3, 5))
        self.assertEqual(updates.read_changelog(staged), changelog)

    def test_update_ships_frame_modules_and_native_renderer_without_checkout_paths(self):
        app = make_app(self.root)
        source = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'
        files = [source / 'qmldir']
        for directory in ('tactic_frame', 'features/administration', 'shell'):
            files.extend(path for path in (source / directory).rglob('*') if path.is_file())
        for path in files:
            name = path.relative_to(source).as_posix()
            data = path.read_bytes()
            if path.suffix in ('.qml', '.mjs'):
                self.assertNotIn(b'D:/code/', data)
            target = app / 'thlib/ui/qml' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        archive = self.root / 'frame-1_2_3_5.zip'
        updates.create_update_archive(app, archive, (1, 2, 3, 5))
        with zipfile.ZipFile(archive) as packaged:
            for path in files:
                name = path.relative_to(source).as_posix()
                self.assertEqual(packaged.read('thlib/ui/qml/' + name), path.read_bytes())

    def test_archive_requires_a_changelog_entry_for_its_version(self):
        app = make_app(self.root)
        archive = self.root / '1_2_3_6.zip'
        with self.assertRaisesRegex(ValueError, '1.2.3.6.*CHANGELOG.md'):
            updates.create_update_archive(app, archive, (1, 2, 3, 6), 'Manual notes')
        self.assertFalse(archive.exists())

    def test_archive_contains_qml_and_preserves_settings(self):
        app = make_app(self.root)
        archive = self.root / "1_2_3_5.zip"
        updates.create_update_archive(app, archive, (1, 2, 3, 5), "Fixed UI")
        with zipfile.ZipFile(archive) as stream:
            names = stream.namelist()
            self.assertIn("thlib/ui/qml/Main.qml", names)
            self.assertIn("side_tools/batch_scheduler/scheduler_classes.py", names)
            self.assertIn("server_plugin/tactic_handler_queries/command.py", names)
            self.assertNotIn("settings/user.json", names)
            self.assertNotIn("temp_custom_scripts/private.py", names)
        staged = self.root / "staged"
        updates.stage_archive(archive, staged, (1, 2, 3, 5))
        self.assertEqual(updates.current_version(staged), (1, 2, 3, 5))
        self.assertTrue((staged / "side_tools" / "batch_scheduler" / "scheduler_classes.py").is_file())
        self.assertFalse((staged / "settings").exists())
        self.assertTrue((app / "settings" / "user.json").exists())

    def test_rejects_unsafe_archive_entries(self):
        for entry in ("../escape", "/absolute",
                      "settings/private.json", "CON", "thlib//bad.py"):
            with self.subTest(entry=entry):
                archive = self.root / "bad.zip"
                with zipfile.ZipFile(archive, "w") as stream:
                    stream.writestr("launch.py", "")
                    stream.writestr("thlib/version.json", json.dumps(dict(zip(
                        updates.VERSION_FIELDS, (1, 0, 0, 0)))))
                    stream.writestr(entry, "bad")
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    updates.stage_archive(archive, self.root / "stage", (1, 0, 0, 0))
                self.assertFalse((self.root / "stage").exists())

    def test_rejects_mismatched_version(self):
        app = make_app(self.root)
        archive = self.root / "release.zip"
        updates.create_update_archive(app, archive, (1, 2, 3, 5))
        with self.assertRaisesRegex(ValueError, "version"):
            updates.stage_archive(archive, self.root / "stage", (1, 2, 3, 6))

    def test_installer_swaps_app_and_preserves_user_data(self):
        root = self.root / "portable"
        root.mkdir()
        make_app(root)
        staged = root / "_updates" / "stage-test"
        staged.parent.mkdir()
        staged.mkdir()
        (staged / "thlib").mkdir()
        (staged / "launch.py").write_text("new")
        (staged / "thlib" / "version.json").write_text(json.dumps(dict(zip(
            updates.VERSION_FIELDS, (1, 2, 3, 5)))))

        class Child:
            def poll(self):
                return None

        def launch(*_args, **_kwargs):
            (root / "_updates" / "ready-123").write_text("ready")
            return Child()

        with patch.object(update_installer, "wait_for_parent"), patch.object(
            update_installer.subprocess, "Popen", side_effect=launch
        ):
            update_installer.install(root, staged, 123)
        self.assertEqual((root / "app" / "launch.py").read_text(), "new")
        self.assertTrue((root / "app" / "settings" / "user.json").exists())
        self.assertEqual(
            (root / "app" / "temp_custom_scripts" / "private.py").read_text(),
            "SECRET",
        )
        self.assertTrue(any((root / "_updates" / "backups").iterdir()))

    def test_installer_restores_previous_version_if_new_app_fails(self):
        root = self.root / "portable"
        root.mkdir()
        make_app(root)
        staged = root / "_updates" / "stage-test"
        staged.parent.mkdir()
        staged.mkdir()
        (staged / "launch.py").write_text("broken")

        class FailedChild:
            def poll(self):
                return 1

            def terminate(self):
                pass

            def wait(self, timeout):
                return 1

        with patch.object(update_installer, "wait_for_parent"), patch.object(
            update_installer.subprocess, "Popen", return_value=FailedChild()
        ) as launch:
            with self.assertRaisesRegex(RuntimeError, "first frame"):
                update_installer.install(root, staged, 123)
        self.assertEqual(launch.call_count, 2)
        self.assertEqual((root / "app" / "launch.py").read_text(), "print('ready')")
        self.assertTrue((root / "app" / "settings" / "user.json").exists())


if __name__ == "__main__":
    unittest.main()
