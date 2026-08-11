from __future__ import annotations

import unittest
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEventLoop, QSettings, QTimer

from modern_ui.script_editor import ScriptEditorController
from modern_ui.debug_logging import DebugLogController
from thlib.pool import ThreadsPool


class _DebugLog:
    def raise_error(self, *_args, **_kwargs):
        return None


class _ScriptObject:
    def __init__(self, code, folder, title, language, source):
        self.values = {
            "folder": folder, "title": title,
            "language": language, "script": source,
        }
        self.code = code

    def get_value(self, name):
        return self.values.get(name)


class ScriptEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.controller = ScriptEditorController(None, _DebugLog())
        self.controller._expanded = set()
        first = _ScriptObject(
            "SCRIPT1", "pipeline/tools", "First", "local_python",
            "print('first')",
        )
        second = _ScriptObject(
            "SCRIPT2", "pipeline", "Second", "python", "return 2",
        )
        self.controller._done({
            "kind": "load",
            "objects": {"SCRIPT1": first, "SCRIPT2": second},
            "rows": [
                {"token": "SCRIPT1", "folder": "pipeline/tools",
                 "title": "First", "language": "local_python"},
                {"token": "SCRIPT2", "folder": "pipeline",
                 "title": "Second", "language": "python"},
            ],
        })

    def test_tree_preserves_folder_hierarchy(self):
        self.assertEqual(
            [row["title"] for row in self.controller.model._records],
            ["pipeline"],
        )
        self.controller._expanded.add("pipeline")
        self.controller._rebuild_tree()
        self.assertEqual(
            [row["title"] for row in self.controller.model._records],
            ["pipeline", "tools", "Second"],
        )
        self.controller._expanded.add("pipeline/tools")
        self.controller._rebuild_tree()
        self.assertEqual(
            [row["title"] for row in self.controller.model._records],
            ["pipeline", "tools", "First", "Second"],
        )

    def test_local_console_keeps_namespace_between_runs(self):
        self.controller._run_local("value = 17")
        result = self.controller._run_local("print(value)")
        self.assertEqual(result["output"].strip(), "17")

    def test_original_language_execution_rules_are_retained(self):
        self.assertEqual(
            self.controller.handle_scripts_language_combo_box("local_python"),
            {"mode": "local", "runnable": True},
        )
        self.assertEqual(
            self.controller.handle_scripts_language_combo_box("xml"),
            {"mode": "server", "runnable": False},
        )

    def test_each_script_tab_keeps_its_draft_and_output(self):
        first = self.controller.script("SCRIPT1")
        self.controller.update_editor_state(
            "SCRIPT1", "pipeline/tools", "First", "local_python",
            "print('draft one')",
        )
        self.controller._append_output("first output", first["tabId"])
        second = self.controller.script("SCRIPT2")
        self.controller.update_editor_state(
            "SCRIPT2", "pipeline", "Second", "python",
            "print('draft two')",
        )
        self.controller._append_output("second output", second["tabId"])

        restored_first = self.controller.select_tab(first["tabId"])
        self.assertEqual(restored_first["source"], "print('draft one')")
        self.assertEqual(self.controller.output, "first output")
        restored_second = self.controller.select_tab(second["tabId"])
        self.assertEqual(restored_second["source"], "print('draft two')")
        self.assertEqual(self.controller.output, "second output")

    def test_draft_tabs_are_restored_from_settings(self):
        with TemporaryDirectory() as directory:
            settings_path = str(Path(directory) / "script-editor.ini")
            settings = QSettings(settings_path, QSettings.IniFormat)
            controller = ScriptEditorController(None, _DebugLog())
            controller._settings = settings
            controller._session_project_code = "test"
            controller._sessions = {}
            controller._current_tab_id = ""
            controller.create_new_script()
            controller.update_editor_state(
                "", "drafts", "Unsaved", "local_python", "value = 42"
            )
            controller._append_output("draft output")
            active_tab = controller.currentTabId
            controller._save_sessions()
            settings.sync()

            restored = ScriptEditorController(None, _DebugLog())
            restored._settings = QSettings(settings_path, QSettings.IniFormat)
            restored._session_project_code = "test"
            restored._restore_sessions()
            self.assertEqual(restored.currentTabId, active_tab)
            self.assertEqual(restored.currentEditor["source"], "value = 42")
            self.assertEqual(restored.output, "draft output")

    def test_closing_last_tab_creates_new_draft(self):
        self.controller._sessions = {}
        self.controller._current_tab_id = ""
        self.controller.create_new_script()
        only_tab = self.controller.currentTabId
        self.controller.close_tab(only_tab)
        self.assertTrue(self.controller.currentTabId)
        self.assertNotEqual(self.controller.currentTabId, only_tab)
        self.assertEqual(self.controller.tabs.count(), 1)
        self.assertEqual(self.controller.currentEditor["source"], "")

    def test_new_scripts_have_useful_unique_defaults(self):
        self.controller._sessions = {}
        self.controller._current_tab_id = ""
        self.controller.create_new_script()
        first = dict(self.controller.currentEditor)
        self.controller.create_new_script()
        second = dict(self.controller.currentEditor)

        self.assertEqual(first["folder"], "custom")
        self.assertEqual(first["title"], "new_script_1")
        self.assertEqual(second["folder"], "custom")
        self.assertEqual(second["title"], "new_script_2")

    def test_close_all_requests_one_confirmation_and_discards_all(self):
        self.controller._sessions = {}
        self.controller._current_tab_id = ""
        self.controller.create_new_script()
        self.controller.update_editor_state(
            "", "custom", "first", "local_python", "print(1)"
        )
        self.controller.create_new_script()
        self.controller.update_editor_state(
            "", "custom", "second", "local_python", "print(2)"
        )
        requested = []
        self.controller.closeAllConfirmationRequested.connect(requested.append)

        self.controller.request_close_all()
        self.assertEqual(requested, [2])
        self.assertEqual(self.controller.tabs.count(), 2)

        self.controller.confirm_close_all_discard()
        self.assertEqual(self.controller.tabs.count(), 1)
        self.assertFalse(self.controller.currentEditor["dirty"])

    def test_worker_error_is_written_to_editor_output(self):
        self.controller._failed(({
            "exception": RuntimeError("broken script"),
            "stacktrace": "Traceback\nbroken script",
        }, object()))
        self.assertIn("Traceback\nbroken script", self.controller.output)
        self.assertEqual(self.controller.error, "")

    def test_server_script_error_does_not_open_global_dialog(self):
        with TemporaryDirectory() as directory:
            debug_log = DebugLogController(Path(directory))
            controller = ScriptEditorController(None, debug_log)

            def fail_inside_tactic_wrapper(*_args, **_kwargs):
                error = RuntimeError("script boom")
                debug_log.raise_error(error, stacktrace="server traceback")
                raise error

            with patch(
                "thlib.tactic_classes.execute_procedure_serverside",
                side_effect=fail_inside_tactic_wrapper,
            ):
                with self.assertRaisesRegex(RuntimeError, "script boom"):
                    controller._run_server("raise RuntimeError('script boom')")
            self.assertFalse(debug_log.error_visible)
            debug_log.shutdown()

    def test_script_run_suppresses_dialog_from_worker_and_gui_paths(self):
        with TemporaryDirectory() as directory:
            debug_log = DebugLogController(Path(directory))
            debug_log.begin_inline_error_output("script-editor-run")
            worker = threading.Thread(
                target=lambda: debug_log.raise_error(
                    RuntimeError("worker script error")
                )
            )
            worker.start()
            worker.join()
            debug_log.raise_error(RuntimeError("queued script error"))
            self.assertFalse(debug_log.error_visible)
            debug_log.end_inline_error_output("script-editor-run")
            debug_log.raise_error(RuntimeError("ordinary application error"))
            self.assertTrue(debug_log.error_visible)
            debug_log.shutdown()

    def test_run_button_worker_error_stays_in_output(self):
        from thlib.environment import env_inst

        with TemporaryDirectory() as directory:
            debug_log = DebugLogController(Path(directory))
            controller = ScriptEditorController(None, debug_log)
            pool = ThreadsPool(max_threads=1)
            pool.start()

            def failing_server_script(_source, _tab_id):
                error = RuntimeError("run button script error")
                debug_log.raise_error(error, stacktrace="worker traceback")
                raise error

            controller._run_server = failing_server_script
            event_loop = QEventLoop()

            def finish_when_worker_stops():
                if not controller.busy and controller.output:
                    event_loop.quit()

            controller.stateChanged.connect(finish_when_worker_stops)
            with patch.object(env_inst, "server_pool", pool):
                controller.request_run(
                    "server", "python", "raise RuntimeError('broken')"
                )
                QTimer.singleShot(3000, event_loop.quit)
                event_loop.exec()
            pool.exit()
            self.assertFalse(controller.busy)
            self.assertIn("run button script error", controller.output)
            self.assertFalse(debug_log.error_visible)
            self.assertFalse(debug_log._inline_error_owners)
            debug_log.shutdown()


if __name__ == "__main__":
    unittest.main()
