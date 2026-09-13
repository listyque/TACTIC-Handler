from __future__ import annotations

import errno
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

from thlib import environment


class AtomicJsonWriteTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "tasks.json"
        environment._write_json_atomic(str(self.path), {"previous": True})

    def test_transient_windows_lock_retries_only_replace(self):
        replace = environment.os.replace
        for winerror in (5, 32, 33):
            with self.subTest(winerror=winerror):
                error = PermissionError(errno.EACCES, "File is in use")
                error.winerror = winerror
                attempts = 0

                def replace_after_lock(source, destination):
                    nonlocal attempts
                    attempts += 1
                    if attempts <= 2:
                        raise error
                    return replace(source, destination)

                with patch.object(
                    environment.os, "replace",
                    side_effect=replace_after_lock,
                ) as replace_mock, patch.object(
                    environment.time, "sleep",
                ) as sleep, patch.object(
                    environment.json, "dump", wraps=json.dump,
                ) as dump, patch.object(
                    environment.os, "fsync", wraps=environment.os.fsync,
                ) as fsync:
                    environment._write_json_atomic(
                        str(self.path), {"winerror": winerror},
                    )

                self.assertEqual(replace_mock.call_count, 3)
                self.assertEqual(sleep.call_count, 2)
                dump.assert_called_once()
                fsync.assert_called_once()
                self.assertEqual(
                    json.loads(self.path.read_text(encoding="utf-8")),
                    {"winerror": winerror},
                )
                self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_persistent_windows_lock_keeps_previous_file_and_error(self):
        error = PermissionError(errno.EACCES, "File is in use", str(self.path))
        error.winerror = 5
        with patch.object(
            environment.os, "replace", side_effect=error,
        ) as replace, patch.object(environment.time, "sleep") as sleep:
            with self.assertRaises(PermissionError) as raised:
                environment._write_json_atomic(str(self.path), {"new": True})

        self.assertIs(raised.exception, error)
        self.assertEqual(replace.call_count, 6)
        self.assertEqual(sleep.call_count, 5)
        self.assertLess(sum(call.args[0] for call in sleep.call_args_list), 0.5)
        self.assertEqual(
            json.loads(self.path.read_text(encoding="utf-8")), {"previous": True},
        )
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_other_io_errors_are_not_retried(self):
        for error in (
            PermissionError(errno.EACCES, "Permission denied"),
            OSError(errno.ENOSPC, "Disk is full"),
        ):
            with self.subTest(error=error), patch.object(
                environment.os, "replace", side_effect=error,
            ) as replace, patch.object(environment.time, "sleep") as sleep:
                with self.assertRaises(OSError) as raised:
                    environment._write_json_atomic(
                        str(self.path), {"new": True},
                    )

                self.assertIs(raised.exception, error)
                replace.assert_called_once()
                sleep.assert_not_called()
                self.assertEqual(
                    json.loads(self.path.read_text(encoding="utf-8")),
                    {"previous": True},
                )
                self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    @unittest.skipUnless(sys.platform == "win32", "Windows file sharing")
    def test_open_windows_reader_releases_before_replace_retry(self):
        previous_documents = []
        # A reader outside env_read_config simulates a scanner/SMB client whose
        # handle does not share delete access. Use real Windows rename semantics.
        with self.path.open(encoding="utf-8") as reader:
            def release_reader(_delay):
                previous_documents.append(json.load(reader))
                reader.close()

            with patch.object(
                environment.time, "sleep", side_effect=release_reader,
            ) as sleep:
                environment._write_json_atomic(str(self.path), {"new": True})

        sleep.assert_called_once()
        self.assertEqual(previous_documents, [{"previous": True}])
        self.assertEqual(
            json.loads(self.path.read_text(encoding="utf-8")), {"new": True},
        )
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_uncontended_replace_does_not_wait(self):
        with patch.object(environment.time, "sleep") as sleep:
            environment._write_json_atomic(str(self.path), {"new": True})

        sleep.assert_not_called()


class EnvironmentConfigTests(unittest.TestCase):
    def test_reloaded_server_presets_are_returned(self):
        server_environment = object.__new__(environment.Env)
        presets = {
            "presets_list": ["default", "studio"],
            "current": "studio",
        }
        server_environment.server_presets = None
        server_environment.server_presets_defaults = {
            "server_presets": presets,
        }

        self.assertIs(server_environment.get_server_presets(), presets)

    def config_scope(self, directory):
        return (
            patch.object(
                environment.env_mode, "get_current_path",
                return_value=directory,
            ),
            patch.object(
                environment.env_server, "get_cur_srv_preset",
                return_value="test-preset",
            ),
            patch.object(
                environment.env_mode, "get_mode",
                return_value="standalone",
            ),
        )

    def test_long_path_round_trip_uses_project_config_tree(self):
        with TemporaryDirectory() as directory:
            scopes = self.config_scope(directory)
            with scopes[0], scopes[1], scopes[2]:
                value = {"language": "Русский", "enabled": True, "size": 12}
                environment.env_write_config(
                    value,
                    filename="ui_settings",
                    unique_id="ui_main",
                    long_abs_path=True,
                )
                restored = environment.env_read_config(
                    filename="ui_settings",
                    unique_id="ui_main",
                    long_abs_path=True,
                )

            path = (
                Path(directory) / "settings" / "full" / "test-preset"
                / "standalone" / "ui_main" / "ui_settings.json"
            )
            self.assertTrue(path.is_file())
            self.assertEqual(restored, value)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")), value
            )

    def test_failed_serialization_keeps_previous_file_intact(self):
        with TemporaryDirectory() as directory:
            scopes = self.config_scope(directory)
            with scopes[0], scopes[1], scopes[2]:
                environment.env_write_config(
                    {"safe": True}, filename="atomic", unique_id="cache",
                    long_abs_path=True,
                )
                with self.assertRaises(TypeError):
                    environment.env_write_config(
                        {"unsafe": object()}, filename="atomic",
                        unique_id="cache", long_abs_path=True,
                    )
                restored = environment.env_read_config(
                    filename="atomic", unique_id="cache",
                    long_abs_path=True,
                )
            self.assertEqual(restored, {"safe": True})

    def test_concurrent_sub_id_updates_do_not_lose_values(self):
        with TemporaryDirectory() as directory:
            scopes = self.config_scope(directory)
            with scopes[0], scopes[1], scopes[2]:
                threads = [
                    threading.Thread(
                        target=environment.env_write_config,
                        kwargs={
                            "obj": index,
                            "filename": "shared",
                            "unique_id": "cache",
                            "sub_id": f"item-{index}",
                            "update_file": True,
                            "long_abs_path": True,
                        },
                    )
                    for index in range(20)
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                restored = environment.env_read_config(
                    filename="shared", unique_id="cache",
                    long_abs_path=True,
                )
            self.assertEqual(
                restored,
                {f"item-{index}": index for index in range(20)},
            )

    def test_sub_id_update_does_not_replace_non_mapping_document(self):
        with TemporaryDirectory() as directory:
            scopes = self.config_scope(directory)
            with scopes[0], scopes[1], scopes[2]:
                environment.env_write_config(
                    ["keep", "this"], filename="shared",
                    unique_id="cache", long_abs_path=True,
                )
                with self.assertRaises(TypeError):
                    environment.env_write_config(
                        "new", filename="shared", unique_id="cache",
                        sub_id="item", update_file=True,
                        long_abs_path=True,
                    )
                restored = environment.env_read_config(
                    filename="shared", unique_id="cache",
                    long_abs_path=True,
                )
            self.assertEqual(restored, ["keep", "this"])

    def test_application_production_code_does_not_use_qsettings(self):
        root = Path(__file__).parents[1]
        sources = [root / "thlib/ui/application.py"]
        sources.extend((root / "thlib" / "ui").rglob("*.py"))
        for source in sources:
            text = source.read_text(encoding="utf-8")
            self.assertNotIn("QSettings", text, source)

    def test_unique_id_cannot_escape_settings_directory(self):
        with TemporaryDirectory() as directory:
            scopes = self.config_scope(directory)
            with scopes[0], scopes[1], scopes[2]:
                with self.assertRaises(ValueError):
                    environment.env_write_config(
                        {"unsafe": True},
                        filename="escape",
                        unique_id="../../outside",
                        long_abs_path=True,
                    )
            self.assertFalse((Path(directory) / "outside").exists())

    def test_remove_group_deletes_only_owned_json_documents(self):
        with TemporaryDirectory() as directory:
            scopes = self.config_scope(directory)
            with scopes[0], scopes[1], scopes[2]:
                environment.env_write_config(
                    {"entries": [1]}, filename="search",
                    unique_id="cache/server_data/scope",
                    long_abs_path=True,
                )
                environment.env_write_config(
                    {"entries": [2]}, filename="tasks",
                    unique_id="cache/server_data/scope",
                    long_abs_path=True,
                )
                group = (
                    Path(directory) / "settings" / "full" / "test-preset"
                    / "standalone" / "cache" / "server_data" / "scope"
                )
                keep = group / "keep.txt"
                keep.write_text("not a config", encoding="utf-8")
                nested = group / "old_scope"
                nested.mkdir()
                (nested / "reference_07.json").write_text(
                    "{}", encoding="utf-8"
                )

                environment.env_write_config(
                    filename="", unique_id="cache/server_data/scope",
                    long_abs_path=True, remove=True,
                )

            self.assertFalse((group / "search.json").exists())
            self.assertFalse((group / "tasks.json").exists())
            self.assertFalse((nested / "reference_07.json").exists())
            self.assertEqual(keep.read_text(encoding="utf-8"), "not a config")


if __name__ == "__main__":
    unittest.main()
