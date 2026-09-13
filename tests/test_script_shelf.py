import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from PySide6.QtCore import QObject, Signal

import thlib.tactic_classes as tc
from thlib.ui.models import NavigationEntry, NavigationModel
from thlib.ui.script_shelf import (
    SCRIPT_SHELF_CATEGORY,
    SCRIPT_SHELF_GLOBAL_VIEW,
    ScriptShelfController,
    shelf_configuration_from_xml,
    shelf_configuration_xml,
    shelf_is_assigned,
)
from thlib.ui.sidebar_editor import SidebarEditorController


class _Registry:
    def register(self, _name, _callback):
        pass


class _Windows(QObject):
    windowVisibilityChanged = Signal(str, bool)

    def show_window(self, _window_id):
        pass


class _Application(QObject):
    project_changed = Signal(str, str)
    search_state_changed = Signal()

    def __init__(self):
        super().__init__()
        self.current_project_code = ""
        self._registry = _Registry()
        self.window_model = _Windows()
        self.navigation_model = NavigationModel()
        self.notifications = []
        self.context = {
            "entryKey": "demo/asset@assets",
            "title": "Assets",
            "shelfPreset": "script_shelf@assets",
        }
        self.shelf_assignments = []
        self.removed_shelf_assignments = []

    def script_shelf_context(self):
        return dict(self.context)

    def _notify(self, message):
        self.notifications.append(str(message))

    def apply_script_shelf_assignment(
            self, project_code, entry_key, shelf_view, record):
        self.context["shelfPreset"] = shelf_view
        self.shelf_assignments.append(
            (project_code, entry_key, shelf_view, record)
        )

    def remove_script_shelf_assignments(
            self, project_code, shelf_view, records):
        if self.context["shelfPreset"] == shelf_view:
            self.context["shelfPreset"] = ""
        self.removed_shelf_assignments.append(
            (project_code, shelf_view, records)
        )


class _Users(QObject):
    stateChanged = Signal()
    login = "artist"
    canManageUsers = True


class _ScriptEditor(QObject):
    stateChanged = Signal()

    def __init__(self):
        super().__init__()
        self.busy = False
        self.error = ""
        self.started = []
        self.shelfScriptOptions = [
            {"value": "tools/save", "label": "tools/save",
             "language": "dcc_python"},
            {"value": "tools/publish", "label": "tools/publish",
             "language": "local_python"},
        ]

    def run_saved_script(self, path):
        self.started.append(path)
        self.busy = True
        self.stateChanged.emit()
        return True


class _DccBridge(QObject):
    stateChanged = Signal()
    commandFinished = Signal(str, bool, "QVariantMap", str)

    def __init__(self):
        super().__init__()
        self.selectedApplicationType = "standalone"
        self.capabilities = set()
        self.commands = []
        self.error = ""

    def has_dcc_capability(self, action):
        return action in self.capabilities

    def send_active_command(self, action, payload, timeout):
        self.commands.append((action, payload, timeout))
        return "maya-shelf-request"


class _Server:
    def __init__(self):
        self.records = []
        self.sidebar_records = []
        self.updates = []
        self.deleted = []

    def insert(self, search_type, data, triggers=True):
        assert search_type == "config/widget_config"
        assert triggers
        saved = {**data, "code": "CONFIG0001"}
        self.records.append(saved)
        return saved

    def query(self, search_type, _filters):
        assert search_type == "config/widget_config"
        return self.sidebar_records

    def build_search_key(self, search_type, code, project_code=""):
        return f"{search_type}?project={project_code}&code={code}"

    def insert_update(self, search_key, data, triggers=True):
        self.updates.append((search_key, data, triggers))

    def delete_sobject(self, search_key):
        self.deleted.append(search_key)


class _FailedWorker(QObject):
    result = Signal(object)
    error = Signal(object)
    settled = Signal(object)

    def start(self):
        self.error.emit(({
            "exception": RuntimeError("Server failed"),
            "stacktrace": "server traceback",
        }, self))
        self.settled.emit(self)


class _FailedPool:
    is_stopped = False

    @staticmethod
    def add_task(_operation):
        return _FailedWorker()


class _QueryServer:
    def __init__(self, records):
        self.records = records
        self.queries = []

    def query(self, search_type, filters):
        self.queries.append((search_type, filters))
        return self.records


def _record(view, title, buttons, *, login="", scope="preset",
            entry_key="", code="CONFIG0001"):
    return {
        "code": code,
        "search_type": "SideBarWdg",
        "category": SCRIPT_SHELF_CATEGORY,
        "view": view,
        "title": title,
        "login": login,
        "config": shelf_configuration_xml(
            buttons, view, scope=scope, entry_key=entry_key,
        ),
    }


def _button(identity, script):
    return {
        "buttonId": identity,
        "title": identity,
        "description": "",
        "iconName": "play-arrow",
        "script": script,
    }


class ScriptShelfTests(unittest.TestCase):
    def setUp(self):
        self.read_config = patch(
            "thlib.ui.script_shelf.env_read_config", return_value={}
        ).start()
        self.write_config = patch(
            "thlib.ui.script_shelf.env_write_config"
        ).start()
        self.addCleanup(patch.stopall)
        self.application = _Application()
        self.editor = _ScriptEditor()
        self.users = _Users()
        self.controller = ScriptShelfController(
            self.application, self.users, self.editor,
        )

    def test_active_shelf_mode_is_restored_after_restart(self):
        self.controller.set_active_mode("personal")

        saved = self.write_config.call_args.args[0]
        self.assertEqual(saved["scriptShelf/activeMode"], "personal")
        self.assertEqual(
            self.write_config.call_args.kwargs,
            {
                "filename": "ui_script_shelf",
                "unique_id": "ui_main",
                "long_abs_path": True,
            },
        )
        self.read_config.return_value = saved
        restored = ScriptShelfController(
            self.application, self.users, self.editor,
        )

        self.assertEqual(restored.activeMode, "personal")
        restored._project_changed("", "")
        self.assertEqual(restored.activeMode, "personal")

    def test_xml_round_trip_keeps_button_order_and_scope(self):
        view = "script_shelf@review"
        save_button = _button("save", "tools/save")
        save_button["description"] = "Save the current scene"
        payload = shelf_configuration_from_xml(
            shelf_configuration_xml(
                [save_button, _button("publish", "tools/publish")],
                view,
                scope="tab",
                entry_key="demo/asset@assets",
            ),
            view,
        )

        self.assertEqual(payload["scope"], "tab")
        self.assertEqual(payload["entryKey"], "demo/asset@assets")
        self.assertEqual(
            [button["script"] for button in payload["buttons"]],
            ["tools/save", "tools/publish"],
        )
        self.assertEqual(
            payload["buttons"][0]["description"],
            "Save the current scene",
        )

    def test_shared_shelf_assignment_is_found_in_sidebar_xml(self):
        self.assertTrue(shelf_is_assigned([{
            "config": (
                "<config><element><display><script_shelf>"
                "script_shelf@review</script_shelf></display>"
                "</element></config>"
            )
        }], "script_shelf@review"))
        self.assertFalse(shelf_is_assigned(
            [{"config": "<broken"}], "script_shelf@review"
        ))

    def test_active_shelf_can_be_copied_to_the_connected_dcc_client(self):
        save = _button("save", "tools/save")
        save.update({
            "title": "Save",
            "description": "Save the current scene",
            "iconName": "save",
        })
        self.controller._project_code = "demo"
        self.controller._sync_records([_record(
            "script_shelf@assets", "Assets", [save],
        )])
        bridge = _DccBridge()
        self.controller.attach_dcc_bridge(bridge)

        self.assertFalse(self.controller.canExportDccShelf)
        bridge.selectedApplicationType = "maya"
        bridge.capabilities.add("create_script_shelf")
        bridge.stateChanged.emit()
        self.assertTrue(self.controller.canExportDccShelf)
        self.assertEqual(self.controller.dccShelfName, "TACTIC Assets")

        self.controller.export_dcc_shelf("Animation Tools")

        self.assertTrue(self.controller.dccShelfBusy)
        self.assertEqual(bridge.commands, [(
            "create_script_shelf",
            {
                "project": "demo",
                "name": "Animation Tools",
                "buttons": [{
                    "title": "Save",
                    "description": "Save the current scene",
                    "icon": "save",
                    "script": "tools/save",
                }],
            },
            30.0,
        )])
        bridge.commandFinished.emit(
            "maya-shelf-request", True,
            {"buttons": 2, "updated": True}, "",
        )
        self.assertFalse(self.controller.dccShelfBusy)
        self.assertEqual(
            self.application.notifications[-1], "DCC shelf updated"
        )

    def test_active_shelf_switches_between_personal_and_shared(self):
        global_record = _record(
            SCRIPT_SHELF_GLOBAL_VIEW, "Global",
            [_button("global", "tools/save")], scope="global",
        )
        assigned = _record(
            "script_shelf@assets", "Assets",
            [_button("assigned", "tools/publish")], code="CONFIG0002",
        )
        personal_global = _record(
            "script_shelf@mine", "Mine",
            [_button("mine", "tools/save")], login="artist",
            scope="global", code="CONFIG0003",
        )
        personal_tab = _record(
            "script_shelf@my_assets", "Mine for Assets",
            [_button("tab", "tools/publish")], login="artist",
            scope="tab", entry_key="demo/asset@assets", code="CONFIG0004",
        )

        self.controller._sync_records([
            global_record, assigned, personal_global, personal_tab,
        ])
        self.assertEqual(self.controller.buttons.get(0)["buttonId"], "tab")

        self.controller.set_active_mode("shared")
        self.assertEqual(
            self.controller.buttons.get(0)["buttonId"], "assigned"
        )
        self.controller.set_active_mode("personal")
        self.assertEqual(self.controller.buttons.get(0)["buttonId"], "tab")

        self.controller._sync_records([
            global_record, assigned, personal_global,
        ])
        self.assertEqual(self.controller.buttons.get(0)["buttonId"], "mine")

        self.controller._sync_records([global_record, assigned])
        self.assertEqual(self.controller.buttons.records(), [])

        self.controller.set_active_mode("shared")
        self.assertEqual(
            self.controller.buttons.get(0)["buttonId"], "assigned"
        )

        self.application.context["shelfPreset"] = ""
        self.controller._context_changed()
        self.assertEqual(
            self.controller.buttons.get(0)["buttonId"], "global"
        )

    def test_personal_tab_saves_to_server_under_current_login(self):
        server = _Server()
        self.controller._project_code = "demo"
        self.controller._personal_scope = "tab"
        self.controller.editor_buttons.replace([
            _button("save", "tools/save")
        ])
        self.controller._run = lambda operation, handler: handler(operation())

        with patch.object(tc, "server_start", return_value=server):
            self.controller.save()

        self.assertEqual(len(server.records), 1)
        saved = server.records[0]
        self.assertEqual(saved["login"], "artist")
        payload = shelf_configuration_from_xml(
            saved["config"], saved["view"]
        )
        self.assertEqual(payload["scope"], "tab")
        self.assertEqual(payload["entryKey"], "demo/asset@assets")

    def test_shared_tab_saves_shelf_and_sidebar_assignment_together(self):
        server = _Server()
        server.sidebar_records = [{
            "code": "CONFIG0099",
            "search_type": "SideBarWdg",
            "view": "definition",
            "title": "Definition",
            "login": "",
            "config": (
                "<config><element name='assets'>"
                "<display class='LinkWdg'/><search_type>demo/asset"
                "</search_type></element></config>"
            ),
        }]
        self.application.context["shelfPreset"] = ""
        self.controller._project_code = "demo"
        self.controller._editor_mode = "shared"
        self.controller._shared_scope = "tab"
        self.controller._editor_view = "script_shelf@assets"
        self.controller._editor_title = "Assets"
        self.controller.editor_buttons.replace([
            _button("save", "tools/save")
        ])
        self.controller._run = lambda operation, handler: handler(operation())

        with patch.object(tc, "server_start", return_value=server):
            self.controller.save()

        self.assertEqual(
            self.application.context["shelfPreset"],
            "script_shelf@assets",
        )
        self.assertEqual(len(self.application.shelf_assignments), 1)
        self.assertEqual(len(server.updates), 1)
        assigned = ElementTree.fromstring(server.updates[0][1]["config"])
        self.assertEqual(
            assigned.findtext(".//display/script_shelf"),
            "script_shelf@assets",
        )

    def test_saved_shared_shelf_can_be_applied_to_the_current_tab(self):
        server = _Server()
        server.sidebar_records = [{
            "code": "CONFIG0099",
            "search_type": "SideBarWdg",
            "view": "definition",
            "title": "Definition",
            "login": "",
            "config": (
                "<config><element name='assets'>"
                "<display class='LinkWdg'/><search_type>demo/asset"
                "</search_type></element></config>"
            ),
        }]
        view = "script_shelf@review"
        self.application.context["shelfPreset"] = ""
        self.controller._project_code = "demo"
        self.controller._sync_records([
            _record(view, "Review", [_button("review", "tools/save")])
        ])
        self.controller._editor_mode = "shared"
        self.controller._shared_scope = "tab"
        self.controller._editor_view = view
        self.controller._load_editor()
        self.controller._run = lambda operation, handler: handler(operation())

        self.assertTrue(self.controller.assignmentPending)
        with patch.object(tc, "server_start", return_value=server):
            self.controller.apply_to_current_tab()

        self.assertEqual(server.records, [])
        self.assertEqual(len(server.updates), 1)
        self.assertEqual(self.application.context["shelfPreset"], view)
        self.assertFalse(self.controller.assignmentPending)
        self.assertEqual(self.controller.activeMode, "shared")
        self.assertIn(
            "Shelf applied to current tab", self.application.notifications
        )

    def test_global_shared_shelf_has_a_fixed_display_title(self):
        self.controller._sync_records([_record(
            SCRIPT_SHELF_GLOBAL_VIEW, "Assets Shelf",
            [_button("save", "tools/save")], scope="global",
        )])
        self.controller._editor_mode = "shared"
        self.controller._shared_scope = "global"
        self.controller._editor_view = SCRIPT_SHELF_GLOBAL_VIEW
        self.controller._load_editor()

        self.assertEqual(self.controller.editorTitle, "Shared shelf")
        self.assertEqual(
            self.controller.sharedOptions[0]["label"], "Shared shelf"
        )
        self.assertFalse(self.controller.canRename)
        self.controller.set_editor_title("Renamed")
        self.assertEqual(self.controller.editorTitle, "Shared shelf")

    def test_named_shared_shelf_can_be_reopened_without_locking_editor(self):
        server = _Server()
        self.application.context = {
            "entryKey": "",
            "title": "",
            "shelfPreset": "",
        }
        self.controller._project_code = "demo"
        self.controller._editor_mode = "shared"
        self.controller._run = lambda operation, handler: handler(operation())
        self.controller._shared_scope = "global"
        self.controller._editor_view = SCRIPT_SHELF_GLOBAL_VIEW
        self.controller._load_editor()

        self.controller.create_shared()
        view = self.controller.editorView
        self.controller.set_editor_title("Новый шелф для Assets")
        self.controller.add_button()
        with patch.object(tc, "server_start", return_value=server):
            self.controller.save()

        self.assertEqual(server.records[0]["title"], "Новый шелф для Assets")
        self.assertEqual(self.controller.editorTitle, "Новый шелф для Assets")
        self.assertFalse(self.controller.editorDirty)

        code = server.records[0]["code"]
        self.controller.set_editor_title("Assets shelf")
        with patch.object(tc, "server_start", return_value=server):
            self.controller.save()

        self.assertEqual(self.controller.editorView, view)
        self.assertEqual(self.controller.editorTitle, "Assets shelf")
        self.assertEqual(self.controller._editor_record()["code"], code)
        self.assertEqual(server.updates[-1][1]["title"], "Assets shelf")
        self.assertFalse(self.controller.editorDirty)

        self.application.context = {
            "entryKey": "demo/asset@assets",
            "title": "Assets",
            "shelfPreset": "",
        }
        self.controller._shared_scope = "tab"
        self.controller.select_shared(view)
        self.assertEqual(self.controller.editorTitle, "Assets shelf")
        self.assertFalse(self.controller.editorDirty)
        self.assertTrue(self.controller.assignmentPending)
        self.controller.set_shared_scope("global")
        self.assertEqual(self.controller.editorView, SCRIPT_SHELF_GLOBAL_VIEW)
        self.assertNotIn("Save or discard", self.controller.error)

    def test_personal_scope_offers_the_current_sidebar_tab(self):
        options = self.controller.personalScopeOptions

        self.assertEqual(
            [option["value"] for option in options], ["global", "tab"]
        )
        self.assertIn("Assets", options[1]["label"])

    def test_editor_opens_the_shelf_selected_in_the_toolbar(self):
        assigned = _record(
            "script_shelf@assets", "Assets",
            [_button("shared", "tools/save")],
        )
        personal = _record(
            "script_shelf@my_assets", "Mine",
            [_button("personal", "tools/publish")], login="artist",
            scope="tab", entry_key="demo/asset@assets", code="CONFIG0002",
        )
        self.controller._sync_records([assigned, personal])

        self.controller._select_active_editor()
        self.controller._load_editor()
        self.assertEqual(self.controller.editorMode, "personal")
        self.assertEqual(self.controller.personalScope, "tab")
        self.assertEqual(
            self.controller.editor_buttons.get(0)["buttonId"], "personal"
        )

        self.controller.set_active_mode("shared")
        self.controller._select_active_editor()
        self.controller._load_editor()
        self.assertEqual(self.controller.editorMode, "shared")
        self.assertEqual(self.controller.sharedScope, "tab")
        self.assertEqual(self.controller.editorView, "script_shelf@assets")
        self.assertEqual(
            self.controller.editor_buttons.get(0)["buttonId"], "shared"
        )
        self.controller.set_shared_scope("global")
        self.assertEqual(
            self.controller.editorView, SCRIPT_SHELF_GLOBAL_VIEW
        )
        self.controller.set_shared_scope("tab")
        self.assertEqual(self.controller.editorView, "script_shelf@assets")

    def test_editor_loads_the_global_shelf_before_showing_its_window(self):
        self.application.context["shelfPreset"] = ""
        self.controller._sync_records([_record(
            SCRIPT_SHELF_GLOBAL_VIEW, "Global",
            [_button("global", "tools/save")], scope="global",
        )])

        self.controller.open_editor()

        self.assertEqual(self.controller.editorMode, "shared")
        self.assertEqual(self.controller.sharedScope, "global")
        self.assertEqual(self.controller.editorView, SCRIPT_SHELF_GLOBAL_VIEW)
        self.assertEqual(
            self.controller.editor_buttons.get(0)["buttonId"], "global"
        )
        self.assertFalse(self.controller.editorDirty)

    def test_button_runs_through_script_editor(self):
        self.controller._sync_records([_record(
            SCRIPT_SHELF_GLOBAL_VIEW, "Global",
            [_button("save", "tools/save")], scope="global",
        )])

        self.controller.run("save")

        self.assertEqual(self.editor.started, ["tools/save"])
        self.assertTrue(self.controller.executionBusy)
        self.editor.busy = False
        self.editor.stateChanged.emit()
        self.assertFalse(self.controller.executionBusy)

    def test_login_change_reloads_personal_server_records(self):
        self.controller._project_code = "demo"
        self.controller._loaded_login = "artist"
        self.users.login = "other_artist"

        with patch.object(self.controller, "refresh") as refresh:
            self.users.stateChanged.emit()

        refresh.assert_called_once_with()

    def test_refresh_loads_null_shared_and_only_current_personal_shelves(self):
        records = [
            _record(
                SCRIPT_SHELF_GLOBAL_VIEW, "Global",
                [_button("global", "tools/save")], scope="global",
            ),
            _record(
                "script_shelf@mine", "Mine",
                [_button("mine", "tools/save")], login="artist",
                scope="global", code="CONFIG0002",
            ),
            _record(
                "script_shelf@other", "Other",
                [_button("other", "tools/save")], login="other_artist",
                scope="global", code="CONFIG0003",
            ),
        ]
        records[0]["login"] = None
        server = _QueryServer(records)
        self.controller._project_code = "demo"
        self.controller._run = lambda operation, handler: handler(operation())

        with patch.object(tc, "server_start", return_value=server):
            self.controller.refresh()

        self.assertEqual(len(server.queries), 1)
        self.assertEqual(
            {record["view"] for record in self.controller._records},
            {SCRIPT_SHELF_GLOBAL_VIEW, "script_shelf@mine"},
        )

    def test_editor_does_not_discard_unsaved_buttons_when_scope_changes(self):
        self.controller.editor_buttons.replace([
            _button("save", "tools/save")
        ])

        self.controller.set_personal_scope("tab")

        self.assertEqual(self.controller.personalScope, "global")
        self.assertEqual(self.controller.error, "")

    def test_failed_server_operation_releases_the_editor(self):
        self.controller._server_pool = _FailedPool()

        self.controller._run(lambda: None, lambda _payload: None)

        self.assertFalse(self.controller.busy)
        self.assertEqual(self.controller.error, "Server failed")
        self.controller.create_shared()
        self.assertTrue(
            self.controller.editorView.startswith("script_shelf@")
        )
        self.assertEqual(self.controller.error, "")

    def test_deleting_assigned_shared_shelf_clears_tabs_and_uses_global(self):
        shelf = _record(
            "script_shelf@new", "New shelf",
            [_button("save", "tools/save")],
        )
        server = _Server()
        server.sidebar_records = [{
            "code": "CONFIG0099",
            "search_type": "SideBarWdg",
            "view": "definition",
            "title": "Definition",
            "login": "",
            "config": (
                "<config><element name='assets'><display>"
                "<script_shelf>script_shelf@new</script_shelf>"
                "</display></element><element name='shots'><display>"
                "<script_shelf>script_shelf@new</script_shelf>"
                "</display></element></config>"
            ),
        }]
        self.application.context["shelfPreset"] = shelf["view"]
        self.controller._project_code = "demo"
        self.controller._sync_records([shelf])
        self.controller._editor_mode = "shared"
        self.controller._shared_scope = "tab"
        self.controller._editor_view = shelf["view"]
        self.controller._load_editor()
        self.controller.set_editor_title("Unsaved renamed shelf")
        self.assertEqual(self.controller.removeTargetTitle, "New shelf")
        self.controller._run = lambda operation, handler: handler(operation())

        with patch.object(tc, "server_start", return_value=server):
            self.controller.remove()

        self.assertEqual(len(server.deleted), 1)
        self.assertEqual(len(server.updates), 1)
        updated = ElementTree.fromstring(server.updates[0][1]["config"])
        self.assertEqual(updated.findall(".//script_shelf"), [])
        self.assertEqual(self.application.context["shelfPreset"], "")
        self.assertEqual(len(self.application.removed_shelf_assignments), 1)
        self.assertEqual(self.controller.sharedScope, "global")
        self.assertEqual(self.controller.editorView, SCRIPT_SHELF_GLOBAL_VIEW)
        self.assertFalse(self.controller.editorDirty)

    def test_navigation_clears_deleted_shelf_from_every_tab(self):
        model = NavigationModel([
            NavigationEntry(
                "demo/asset@assets", "Assets", "", "", "",
                script_shelf="script_shelf@new",
            ),
            NavigationEntry(
                "demo/shot@shots", "Shots", "", "", "",
                script_shelf="script_shelf@new",
            ),
        ])

        self.assertTrue(model.clear_script_shelf("script_shelf@new"))
        self.assertEqual(model.entry("demo/asset@assets").script_shelf, "")
        self.assertEqual(model.entry("demo/shot@shots").script_shelf, "")

    def test_sidebar_shelf_assignment_is_native_and_shelf_records_are_hidden(self):
        controller = SidebarEditorController(
            self.application, _Users(),
        )
        controller._loaded(("demo", "Demo", object(), [{
            "search_type": "SideBarWdg",
            "view": "definition",
            "config": (
                "<config><element name='assets' title='Assets'>"
                "<display class='LinkWdg'/><search_type>demo/asset"
                "</search_type></element></config>"
            ),
        }, _record(
            "script_shelf@assets", "Assets", [_button("save", "tools/save")]
        )]))
        controller.select_entry(0)

        controller.update_selected("scriptShelf", "script_shelf@assets")

        self.assertEqual(set(controller._documents), {"definition"})
        self.assertEqual(
            controller.selectedEntry["scriptShelf"], "script_shelf@assets"
        )
        self.assertIn(
            "<script_shelf>script_shelf@assets</script_shelf>",
            controller.xmlText,
        )


if __name__ == "__main__":
    unittest.main()
