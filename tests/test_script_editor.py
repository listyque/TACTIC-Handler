from __future__ import annotations

import json
import unittest
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, QEventLoop, QThread, QTimer, Signal
from PySide6.QtGui import QTextDocument

from tests.qt_application import gui_test_application
from thlib.ui.script_editor import ScriptEditorController
from thlib.ui.script_editor_features import (
    PythonSyntaxHighlighter,
    completion_items,
    document_symbols,
    edit_command,
    find_matches,
)
from thlib.ui.debug_logging import DebugLogController
from thlib.pool import ThreadsPool


class _DebugLog:
    def raise_error(self, *_args, **_kwargs):
        return None


class _DccBridge(QObject):
    stateChanged = Signal()
    commandFinished = Signal(str, bool, "QVariantMap", str)

    def __init__(self):
        super().__init__()
        self.selectedClient = "maya-42"
        self.selectedClientLabel = "Maya 2026 · scene.mb · PID 42"
        self.error = ""
        self.commands = []

    @staticmethod
    def has_dcc_capability(action):
        return action in {"execute_custom_script", "execute_script_file"}

    def send_active_command(self, action, payload, timeout):
        self.commands.append((action, dict(payload), timeout))
        return "dcc-script-request"


class _Application(QObject):
    project_changed = Signal(str, str)
    project_state_changed = Signal()

    def __init__(self, project_code=""):
        super().__init__()
        self.current_project_code = project_code


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
        cls.app = gui_test_application()

    def setUp(self):
        read_patcher = patch(
            "thlib.ui.script_editor.env_read_config", return_value={}
        )
        write_patcher = patch("thlib.ui.script_editor.env_write_config")
        read_patcher.start()
        write_patcher.start()
        self.addCleanup(read_patcher.stop)
        self.addCleanup(write_patcher.stop)
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

    def test_tree_filter_finds_nested_scripts_and_restores_folders(self):
        self.controller.set_tree_filter(r"TOOLS\FIR")
        self.assertEqual(
            [row["title"] for row in self.controller.model._records],
            ["pipeline", "tools", "First"],
        )

        self.controller.set_tree_filter("missing")
        self.assertEqual(self.controller.model._records, [])

        self.controller.set_tree_filter("")
        self.assertEqual(
            [row["title"] for row in self.controller.model._records],
            ["pipeline"],
        )

    def test_nested_title_is_loaded_and_saved_as_a_nested_folder(self):
        item = _ScriptObject(
            "NESTED", "batch", "old/scheduler_classes", "local_python", "pass"
        )
        result = self.controller._script_load_result([item], "test")

        self.assertEqual(result["rows"][0]["folder"], "batch/old")
        self.assertEqual(result["rows"][0]["title"], "scheduler_classes")

        self.controller.create_new_script()
        with patch.object(self.controller, "_start", return_value=True) as start:
            self.assertTrue(
                self.controller.save(
                    "", "batch", "old/scheduler_classes", "local_python", "pass"
                )
            )

        payload = start.call_args.args[2]
        self.assertEqual(payload[2:4], ("batch/old", "scheduler_classes"))

    def test_server_refresh_downloads_all_scripts_to_local_mirror(self):
        with patch(
            "thlib.tactic_classes.get_custom_scripts", return_value={}
        ) as get_custom_scripts:
            result = self.controller._load_scripts()

        get_custom_scripts.assert_called_once_with(
            store_locally=True, project=None
        )
        self.assertEqual(result, {
            "kind": "load", "rows": [], "objects": {}, "projectCode": "",
        })

    def test_startup_project_refreshes_the_local_script_mirror(self):
        application = _Application()
        with patch.object(
            ScriptEditorController, "_request_sync"
        ) as request_sync:
            controller = ScriptEditorController(application, _DebugLog())
            request_sync.assert_not_called()

            application.current_project_code = "niki_friends"
            application.project_changed.emit("niki_friends", "Niki Friends")

        request_sync.assert_called_once_with()
        controller.deleteLater()

    def test_reapplying_the_bootstrap_project_does_not_download_scripts_twice(self):
        application = _Application("niki_friends")
        with patch.object(
            ScriptEditorController, "_request_sync"
        ) as request_sync:
            controller = ScriptEditorController(application, _DebugLog())
            request_sync.assert_called_once_with()
            controller._mirrored_project_code = "niki_friends"

            application.project_changed.emit("niki_friends", "Niki Friends")

        request_sync.assert_called_once_with()
        controller.deleteLater()

    def test_server_script_change_refreshes_the_local_mirror(self):
        self.controller._application = _Application("niki_friends")
        with patch.object(self.controller, "_request_sync") as request_sync:
            self.controller.apply_server_batch({
                "cacheChanges": [{
                    "searchType": "config/custom_script",
                    "searchCode": "CUSTOM_SCRIPT00040",
                    "projectCode": "other_project",
                }],
            })
            request_sync.assert_not_called()

            self.controller.apply_server_batch({
                "cacheChanges": [{
                    "searchType": "config/custom_script",
                    "searchCode": "CUSTOM_SCRIPT00040",
                    "projectCode": "niki_friends",
                }],
            })

        request_sync.assert_called_once_with()

    def test_shelf_runs_a_saved_dcc_script_without_a_temporary_file(self):
        item = _ScriptObject(
            "DCC1", "tools", "Saved", "dcc_python", "import maya.cmds"
        )
        self.controller._objects["DCC1"] = item
        self.controller._scripts.append({
            "token": "DCC1", "folder": "tools", "title": "Saved",
            "language": "dcc_python",
        })
        self.controller._scripts.append({
            "token": "XML1", "folder": "tools", "title": "Data",
            "language": "xml",
        })
        bridge = _DccBridge()
        self.controller._application = _Application("niki_friends")
        self.controller.attach_dcc_bridge(bridge)

        self.assertIn(
            {"value": "tools/Saved", "label": "tools/Saved",
             "language": "dcc_python"},
            self.controller.shelfScriptOptions,
        )
        self.assertNotIn(
            "tools/Data",
            [option["value"] for option in self.controller.shelfScriptOptions],
        )
        self.assertTrue(self.controller.run_saved_script("tools/Saved"))
        self.assertEqual(
            bridge.commands[-1],
            (
                "execute_custom_script",
                {"project": "niki_friends", "script": "tools/Saved"},
                300.0,
            ),
        )

    def test_unchanged_startup_mirror_still_loads_script_definitions(self):
        item = _ScriptObject(
            "HOOK1", "dev/tests", "post_save_trigger", "local_python",
            "print('saved')",
        )
        with patch(
            "thlib.tactic_classes.sync_custom_scripts",
            return_value=(None, False),
        ), patch(
            "thlib.tactic_classes.get_custom_scripts",
            return_value=[item],
        ) as get_custom_scripts:
            result = self.controller._sync_scripts("niki_friends")

        get_custom_scripts.assert_called_once_with(
            store_locally=False, project="niki_friends"
        )
        self.assertEqual(result["kind"], "load")
        self.assertEqual(
            result["rows"][0]["title"], "post_save_trigger"
        )

    def test_local_console_keeps_namespace_between_runs(self):
        self.controller._run_local("value = 17")
        result = self.controller._run_local("print(value)")
        self.assertEqual(result["output"].strip(), "17")

    def test_local_console_does_not_inject_api_names(self):
        result = self.controller._run_local("print('th' in globals())")
        self.assertEqual(result["output"].strip(), "False")

    def test_dcc_python_uses_selected_dcc_and_can_run_in_handler(self):
        bridge = _DccBridge()
        self.controller.attach_dcc_bridge(bridge)
        tab_id = self.controller.currentTabId

        options = self.controller.runModeOptions
        self.assertEqual(options[0]["label"], bridge.selectedClientLabel)
        self.assertEqual(
            [item["value"] for item in options],
            ["dcc", "standalone", "server"],
        )

        with TemporaryDirectory() as directory, patch(
            "thlib.ui.script_editor.env_mode.get_current_path",
            return_value=directory,
        ):
            self.controller.request_run(
                "dcc", "dcc_python", "print('inside Maya')"
            )
            action, payload, timeout = bridge.commands[0]
            script_path = Path(payload["path"])
            self.assertEqual(action, "execute_script_file")
            self.assertEqual(timeout, 300.0)
            self.assertEqual(
                script_path.parent,
                Path(directory) / "custom_scripts" / ".temp",
            )
            self.assertEqual(
                script_path.read_text(encoding="utf-8"),
                "print('inside Maya')",
            )

            bridge.commandFinished.emit(
                "dcc-script-request", True, {"output": "inside Maya\n"}, ""
            )
            self.assertTrue(script_path.exists())
            self.assertFalse(self.controller.busy)
            self.assertIn("inside Maya", self.controller.output)

            self.controller.request_run(
                "dcc", "dcc_python", "print('changed in tab')"
            )
            second_path = Path(bridge.commands[1][1]["path"])
            self.assertEqual(second_path, script_path)
            self.assertEqual(
                second_path.read_text(encoding="utf-8"),
                "print('changed in tab')",
            )
            self.controller.close_tab(tab_id)
            self.assertTrue(script_path.exists())
            bridge.commandFinished.emit(
                "dcc-script-request", True, {"output": "changed\n"}, ""
            )
            self.assertFalse(script_path.exists())
            self.assertNotIn(tab_id, self.controller._sessions)
            self.assertFalse(self.controller.busy)

        with patch.object(
            self.controller, "_start_local", return_value=False
        ) as start_local:
            self.controller.request_run(
                "standalone", "dcc_python", "print('inside Handler')"
            )
        start_local.assert_called_once()
        self.assertEqual(len(bridge.commands), 2)
        self.controller.attach_dcc_bridge(None)
        bridge.deleteLater()

    def test_saved_dcc_script_runs_directly_until_edited(self):
        item = _ScriptObject(
            "DCC1", "tools/runners", "textures_checkin_runner",
            "dcc_python", "print('saved')",
        )
        self.controller._objects["DCC1"] = item
        state = self.controller.script("DCC1")
        bridge = _DccBridge()
        self.controller.attach_dcc_bridge(bridge)

        self.controller.request_run(
            "dcc", "dcc_python", state["source"]
        )

        self.assertEqual(bridge.commands[0], (
            "execute_custom_script",
            {
                "project": "default",
                "script": "tools/runners/textures_checkin_runner",
            },
            300.0,
        ))
        bridge.commandFinished.emit(
            "dcc-script-request", True, {"output": "saved\n"}, ""
        )

        with TemporaryDirectory() as directory, patch(
            "thlib.ui.script_editor.env_mode.get_current_path",
            return_value=directory,
        ):
            changed = "print('changed')"
            self.controller.update_editor_state(
                "DCC1", "tools/runners", "textures_checkin_runner",
                "dcc_python", changed, "dcc",
            )
            self.controller.request_run("dcc", "dcc_python", changed)
            action, payload, _timeout = bridge.commands[1]
            self.assertEqual(action, "execute_script_file")
            self.assertEqual(
                Path(payload["path"]).read_text(encoding="utf-8"), changed
            )
            bridge.commandFinished.emit(
                "dcc-script-request", True, {"output": "changed\n"}, ""
            )

        bridge.deleteLater()

    def test_language_selects_its_saved_execution_environment(self):
        self.assertEqual(
            self.controller.handle_scripts_language_combo_box("local_python"),
            {"mode": "standalone", "runnable": True},
        )
        self.assertEqual(
            self.controller.handle_scripts_language_combo_box("dcc_python"),
            {"mode": "dcc", "runnable": True},
        )
        self.assertEqual(
            self.controller.handle_scripts_language_combo_box("xml"),
            {"mode": "server", "runnable": False},
        )

    def test_dcc_python_does_not_fall_back_without_a_dcc(self):
        self.assertEqual(
            self.controller.runModeOptions[0],
            {
                "label": "DCC (not connected)",
                "value": "dcc",
                "icon": "deployed_code",
            },
        )
        with patch.object(self.controller, "_start_local") as start_local:
            self.controller.request_run(
                "dcc", "dcc_python", "print('needs DCC')"
            )

        start_local.assert_not_called()
        self.assertEqual(
            self.controller.error, "No capable DCC client is selected"
        )
        self.assertIn("No capable DCC client is selected", self.controller.output)
        self.assertEqual(self.controller._operation_tab_id, "")

    def test_dcc_language_is_loaded_and_saved_with_the_script(self):
        item = _ScriptObject(
            "DCC1", "tools", "Maya tool", "dcc_python", "import maya.cmds"
        )
        self.controller._objects["DCC1"] = item

        opened = self.controller.script("DCC1")

        self.assertEqual(opened["language"], "dcc_python")
        self.assertEqual(opened["runMode"], "dcc")
        saved_item = Mock()
        self.controller._objects["DCC1"] = saved_item
        self.controller._save_script((
            opened["tabId"], "DCC1", "tools", "Maya tool",
            "dcc_python", "import maya.cmds",
        ))
        saved_item.set_value.assert_any_call("language", "dcc_python")

    def test_server_delete_is_exposed_only_by_the_script_context_menu(self):
        actions = self.controller.scripts_context_menu("SCRIPT1")

        self.assertEqual(
            [action.get("command") for action in actions if not action.get("separator")],
            ["copy_runner", "delete"],
        )
        delete_action = next(
            action for action in actions if action.get("command") == "delete"
        )
        self.assertEqual(delete_action["title"], "Delete from server")
        self.assertTrue(delete_action["enabled"])

    def test_server_delete_uses_the_native_script_sobject_api(self):
        item = Mock()

        result = self.controller._delete_script("SCRIPT1", item)

        item.delete_sobject.assert_called_once_with()
        self.assertEqual(result, {"kind": "deleted", "token": "SCRIPT1"})

    def test_python_highlighter_applies_legacy_semantic_roles(self):
        document = QTextDocument()
        document.setPlainText("def sample():\n    value = 'text' # note")
        highlighter = PythonSyntaxHighlighter(document, {
            "keyword": "#111111",
            "definition": "#222222",
            "string": "#333333",
            "comment": "#444444",
        })
        highlighter.rehighlight()

        first = document.firstBlock().layout().formats()
        second = document.firstBlock().next().layout().formats()
        first_colors = {
            value.start: value.format.foreground().color().name()
            for value in first
        }
        second_colors = {
            value.start: value.format.foreground().color().name()
            for value in second
        }
        self.assertEqual(first_colors[0], "#111111")
        self.assertEqual(first_colors[4], "#222222")
        self.assertIn("#333333", second_colors.values())
        self.assertIn("#444444", second_colors.values())

    def test_python_highlighter_marks_imported_module_aliases(self):
        document = QTextDocument()
        document.setPlainText("import json as codec\ncodec.dumps({})")
        highlighter = PythonSyntaxHighlighter(document, {"module": "#123456"})
        highlighter.rehighlight()

        second = document.firstBlock().next().layout().formats()
        colors = {
            value.start: value.format.foreground().color().name()
            for value in second
        }
        self.assertEqual(colors[0], "#123456")

    def test_completion_indexes_python_locals_and_handler_api(self):
        local = completion_items(
            "custom_value = 1\ncus", len("custom_value = 1\ncus")
        )
        self.assertIn("custom_value", [item["label"] for item in local])

        handler_api = completion_items("th.", 3)
        labels = [item["label"] for item in handler_api]
        self.assertIn("submit", labels)
        self.assertIn("sobject", labels)
        self.assertNotIn("gf", labels)
        stdlib = completion_items("import json as codec\ncodec.", 32)
        self.assertIn("dumps", [item["label"] for item in stdlib])
        self.assertIn("loads", [item["label"] for item in stdlib])

    def test_completion_follows_imports_and_current_class(self):
        source = (
            "import tactic_handler_api\n"
            "tactic_handler_api.get_api().sobj"
        )
        values = completion_items(source, len(source))
        self.assertIn("sobject", [item["label"] for item in values])

        source = (
            "class Worker:\n"
            "    def run_task(self):\n"
            "        self.result = 1\n"
            "        self.__dict__\n"
        )
        values = completion_items(source, source.index("self.") + 5)
        labels = [item["label"] for item in values]
        self.assertIn("run_task", labels)
        self.assertIn("result", labels)

    def test_document_symbols_include_classes_methods_and_functions(self):
        symbols = document_symbols(
            "class Worker:\n"
            "    def run(self):\n"
            "        pass\n\n"
            "def build():\n"
            "    return Worker()\n"
        )

        self.assertEqual(
            [(item["qualifiedName"], item["kind"], item["line"])
             for item in symbols],
            [
                ("Worker", "class", 1),
                ("Worker.run", "method", 2),
                ("build", "function", 5),
            ],
        )


    def test_completion_does_not_import_arbitrary_script_modules(self):
        source = "import definitely_not_a_module as unsafe\nunsafe."
        values = completion_items(source, len(source), True)
        self.assertEqual(values, [])

    def test_find_matches_supports_case_word_and_regex_options(self):
        self.assertEqual(
            find_matches("Alpha alpha alphabet", "alpha", {"wholeWord": True}),
            [{"start": 0, "end": 5}, {"start": 6, "end": 11}],
        )
        self.assertEqual(
            find_matches(
                "item_1 item_x",
                r"item_\d",
                {"regex": True, "caseSensitive": True},
            ),
            [{"start": 0, "end": 6}],
        )

    def test_editor_line_commands_are_selection_aware(self):
        commented = edit_command("toggle_comment", "one\ntwo", 0, 7)
        self.assertEqual(commented["text"], "# one\n# two")
        restored = edit_command(
            "toggle_comment",
            commented["text"],
            commented["start"],
            commented["end"],
        )
        self.assertEqual(restored["text"], "one\ntwo")

        indented = edit_command("indent", "one\ntwo", 0, 7)
        self.assertEqual(indented["text"], "    one\n    two")
        self.assertEqual(
            edit_command(
                "unindent",
                indented["text"],
                indented["start"],
                indented["end"],
            )["text"],
            "one\ntwo",
        )
        duplicated = edit_command("duplicate", "last_line", 4, 4)
        self.assertEqual(duplicated["text"], "last_line\nlast_line")
        deleted = edit_command("delete_line", "one\ntwo\nthree", 5, 5)
        self.assertEqual(deleted, {"text": "one\nthree", "start": 4, "end": 4})


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

    def test_trigger_output_is_written_to_its_open_script_tab(self):
        first = self.controller.script("SCRIPT1")
        second = self.controller.script("SCRIPT2")

        self.controller.append_trigger_output(
            "pipeline/tools/First", "trigger details"
        )

        self.assertEqual(self.controller.currentTabId, second["tabId"])
        self.controller.select_tab(first["tabId"])
        self.assertEqual(self.controller.output, "trigger details")

    def test_server_refresh_updates_only_clean_open_tabs(self):
        dirty_tab = self.controller.script("SCRIPT1")
        self.controller.update_editor_state(
            "SCRIPT1", "pipeline/tools", "First", "local_python",
            "print('local draft')",
        )
        clean_tab = self.controller.script("SCRIPT2")
        changed = []
        self.controller.editorChanged.connect(changed.append)

        first = _ScriptObject(
            "SCRIPT1", "moved", "First server", "python",
            "print('server first')",
        )
        second = _ScriptObject(
            "SCRIPT2", "batch", "Second server", "local_python",
            "print('server second')",
        )
        self.controller._done({
            "kind": "load",
            "objects": {"SCRIPT1": first, "SCRIPT2": second},
            "rows": [
                {"token": "SCRIPT1", "folder": "moved",
                 "title": "First server", "language": "python"},
                {"token": "SCRIPT2", "folder": "batch",
                 "title": "Second server", "language": "local_python"},
            ],
        })

        self.assertEqual(
            self.controller._sessions[dirty_tab["tabId"]]["source"],
            "print('local draft')",
        )
        refreshed = self.controller._sessions[clean_tab["tabId"]]
        self.assertEqual(refreshed["folder"], "batch")
        self.assertEqual(refreshed["title"], "Second server")
        self.assertEqual(refreshed["source"], "print('server second')")
        self.assertFalse(refreshed["dirty"])
        self.assertEqual(changed[-1]["source"], "print('server second')")

    def test_saved_history_is_separate_from_the_local_edit_history(self):
        opened = self.controller.script("SCRIPT1")
        self.controller._done({
            "kind": "saved_history",
            "tabId": opened["tabId"],
            "token": "SCRIPT1",
            "history": [{
                "revisionId": "TX2",
                "timestamp": "2026-09-06 12:00:00",
                "actor": "artist",
                "changedFields": ["script"],
                "action": "update",
                "current": True,
            }],
        })

        self.assertTrue(self.controller.savedHistoryLoaded)
        self.assertEqual(self.controller.savedHistoryCount, 1)
        self.assertEqual(
            self.controller.saved_history.get(0)["summary"],
            "Changed: Source",
        )

        restored = []
        self.controller.savedRevisionReady.connect(restored.append)
        self.controller._done({
            "kind": "saved_revision",
            "tabId": opened["tabId"],
            "token": "SCRIPT1",
            "revision": {"revisionId": "TX1", "script": "print('old')"},
        })
        self.assertEqual(restored, ["print('old')"])

    def test_draft_tabs_are_restored_from_settings(self):
        with TemporaryDirectory():
            settings = {}
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

            restored = ScriptEditorController(None, _DebugLog())
            restored._settings = settings
            restored._session_project_code = "test"
            restored._restore_sessions()
            self.assertEqual(restored.currentTabId, active_tab)
            self.assertEqual(restored.currentEditor["source"], "value = 42")
            self.assertEqual(restored.output, "draft output")

    def test_modified_server_script_is_restored_without_server_save(self):
        settings = {}
        controller = self.controller
        controller._settings = settings
        controller._session_project_code = "test"
        opened = controller.script("SCRIPT1")
        controller.update_editor_state(
            "SCRIPT1", "pipeline/tools", "First", "local_python",
            "print('local unsaved server draft')",
        )
        controller._save_sessions()

        restored = ScriptEditorController(None, _DebugLog())
        restored._settings = settings
        restored._session_project_code = "test"
        restored._restore_sessions()
        state = restored.select_tab(opened["tabId"])

        self.assertEqual(state["token"], "SCRIPT1")
        self.assertTrue(state["dirty"])
        self.assertEqual(
            state["source"], "print('local unsaved server draft')"
        )

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

    def test_new_script_always_creates_a_unique_tab(self):
        self.controller._sessions = {}
        self.controller._current_tab_id = ""
        self.controller.create_new_script()
        first = dict(self.controller.currentEditor)
        self.controller.create_new_script()
        second = dict(self.controller.currentEditor)

        self.assertNotEqual(first["tabId"], second["tabId"])
        self.assertEqual(self.controller.tabs.count(), 2)
        self.assertEqual(first["folder"], "custom")
        self.assertEqual(first["title"], "new_script_1")
        self.assertEqual(second["folder"], "custom")
        self.assertEqual(second["title"], "new_script_2")

    def test_saving_new_script_reuses_its_draft_tab(self):
        self.controller._sessions = {}
        self.controller._current_tab_id = ""
        self.controller.create_new_script()
        tab_id = self.controller.currentTabId
        self.controller.update_editor_state(
            "", "custom", "Saved", "local_python", "print('saved')"
        )
        changed = []
        self.controller.editorChanged.connect(changed.append)

        with patch.object(self.controller, "_request_load"):
            self.controller._done({
                "kind": "saved",
                "tabId": tab_id,
                "folder": "custom",
                "title": "Saved",
            })

        item = _ScriptObject(
            "SCRIPT3", "custom", "Saved", "local_python", "print('saved')"
        )
        self.controller._done({
            "kind": "load",
            "objects": {"SCRIPT3": item},
            "rows": [{
                "token": "SCRIPT3",
                "folder": "custom",
                "title": "Saved",
                "language": "local_python",
            }],
        })

        self.assertEqual(self.controller.tabs.count(), 1)
        self.assertEqual(self.controller.currentTabId, tab_id)
        self.assertEqual(self.controller.currentEditor["token"], "SCRIPT3")
        self.assertEqual(changed[-1]["token"], "SCRIPT3")

    def test_cached_project_state_restores_and_names_its_drafts(self):
        project_tab = "project-draft"
        self.controller._settings = {
            "scriptEditor/sessions/niki_friends": json.dumps([{
                "tabId": project_tab,
                "token": "",
                "folder": "",
                "title": "",
                "language": "dcc_python",
                "source": "print('restored')",
                "runMode": "dcc",
                "output": "",
                "dirty": True,
            }]),
            "scriptEditor/activeSession/niki_friends": project_tab,
        }
        self.controller._application = SimpleNamespace(
            current_project_code="niki_friends"
        )

        with patch.object(self.controller, "_request_load"):
            self.controller._sync_project_sessions()

        self.assertEqual(self.controller.currentTabId, project_tab)
        self.assertEqual(
            self.controller.currentEditor["source"], "print('restored')"
        )
        self.assertEqual(self.controller.currentEditor["folder"], "custom")
        self.assertEqual(
            self.controller.currentEditor["title"], "new_script_1"
        )

    def test_shutdown_flushes_pending_drafts(self):
        self.controller.create_new_script()

        with patch.object(
            self.controller, "writeSettings"
        ) as write_settings:
            self.controller.shutdown()

        self.assertFalse(self.controller._session_save_timer.isActive())
        write_settings.assert_called_once_with()

    def test_editor_layout_settings_round_trip(self):
        self.controller.set_settings_from_dict({
            "treeWidth": 260,
            "outputHeight": 180,
            "treeCollapsed": True,
            "outputCollapsed": True,
            "outputWrap": True,
            "sidePanelMode": "outline",
            "editorFontSize": 13,
        })

        settings = self.controller.get_settings_dict()
        self.assertEqual(settings["treeWidth"], 260)
        self.assertEqual(settings["outputHeight"], 180)
        self.assertTrue(settings["treeCollapsed"])
        self.assertTrue(settings["outputCollapsed"])
        self.assertTrue(settings["outputWrap"])
        self.assertEqual(settings["sidePanelMode"], "outline")
        self.assertEqual(settings["editorFontSize"], 13)

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

    def test_local_python_runs_on_qt_gui_thread(self):
        observed = {}
        event_loop = QEventLoop()

        def run_local(_source, tab_id):
            observed["thread"] = QThread.currentThread()
            return {
                "kind": "run", "tabId": tab_id, "output": "local ok"
            }

        self.controller._run_local = run_local

        def finish_when_local_stops():
            if observed and not self.controller.busy:
                event_loop.quit()

        self.controller.stateChanged.connect(finish_when_local_stops)
        self.controller.request_run(
            "standalone", "local_python", "batch_dispatcher.show()"
        )
        QTimer.singleShot(1000, event_loop.quit)
        event_loop.exec()

        self.assertEqual(observed.get("thread"), self.app.thread())
        self.assertIn("local ok", self.controller.output)

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
