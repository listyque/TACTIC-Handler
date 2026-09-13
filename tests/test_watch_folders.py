from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal

from thlib.ui.watch_folders import WatchFoldersController, _FIELDS
from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.controllers.lifecycle import LifecycleMixin
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


ROOT = Path(__file__).resolve().parents[1]


class _DockModel:
    def __init__(self):
        self.shown = []

    def show_panel(self, panel_id):
        self.shown.append(panel_id)


class _WatchFolderActions:
    def __init__(self):
        self.added = []
        self.edited = []
        self.removed = []

    def begin_add_for_source(self, source, origin="item"):
        self.added.append((source, origin))

    def begin_edit_search_key(self, search_key, origin="item"):
        self.edited.append((search_key, origin))

    def request_remove_search_key(self, search_key, origin="item"):
        self.removed.append((search_key, origin))


class _ItemActionHarness(ItemOperationsMixin):
    def __init__(self, node):
        self.debug_log = None
        self.node = node
        self.watch_folders = _WatchFolderActions()
        self.dock_model = _DockModel()
        self.selected = []
        self.messages = []

    def _node_for_any(self, _node_id):
        return self.node
    def _file_object_for_node(self, _node_id):
        return None

    def select_sobject(self, search_key):
        self.selected.append(search_key)

    def _notify(self, message):
        self.messages.append(message)


class _Checkin:
    updateVersionless = True
    generatePreviews = True

    @staticmethod
    def _checkin_mode():
        return "copy"


class _PayloadHarness:
    _checkin = _Checkin()
    _file_type = staticmethod(lambda _path: "file")

    @staticmethod
    def _watch_checkin_target(_record, context):
        return context, "file"


class _Workspace(QObject):
    selection_changed = Signal()
    _project = None
    _selected_sobject = None


class _Application(QObject):
    project_state_changed = Signal()

    def __init__(self):
        super().__init__()
        self.workspace_state = _Workspace()
        self.workspace_model = None
        self.window_model = SimpleNamespace(
            closed=[],
            close_window=lambda window_id: self.window_model.closed.append(
                window_id
            ),
        )


def _watch_controller():
    return WatchFoldersController(
        _Application(), _Checkin(), SimpleNamespace()
    )


def _watch_record(repositories=None):
    return {
        "title": "Asset",
        "code": "ASSET0001",
        "searchKey": "skey://demo/asset?code=ASSET0001",
        "stype": "Asset",
        "path": "assets/ASSET0001",
        "watchEnabled": True,
        "repository": "Client",
        "repositories": list(repositories or []),
        "pipeline": "asset",
        "watcherStatus": "Stopped",
        "selected": False,
    }


class WatchFoldersTests(unittest.TestCase):
    def test_hidden_editor_defers_workspace_selection_publication(self):
        controller = _watch_controller()
        publications = []
        controller.editorChanged.connect(lambda: publications.append(True))

        controller._workspace.selection_changed.emit()

        self.assertEqual(publications, [])
        self.assertTrue(controller._selection_presentation_dirty)

        controller.set_presentation_visible(True)

        self.assertEqual(publications, [True])

    def test_persistence_contract_matches_legacy_exactly(self):
        self.assertEqual(
            _FIELDS,
            (
                "assets_codes", "assets_names", "assets_stypes",
                "assets_skeys", "assets_pipelines", "paths", "repos",
                "statuses",
            ),
        )

    def test_repository_paths_wait_until_bootstrap_configuration_is_ready(self):
        from thlib.environment import env_tactic

        controller = WatchFoldersController.__new__(WatchFoldersController)
        record = {
            "repositories": ["client"],
            "path": "project/assets/ASSET0001",
        }
        with patch.object(env_tactic, "base_dirs", None):
            paths, repositories, pending = controller._absolute_paths(record)

        self.assertEqual(paths, [])
        self.assertEqual(repositories, [])
        self.assertTrue(pending)

    def test_invalid_repository_does_not_look_like_bootstrap_pending(self):
        from thlib.environment import env_tactic

        controller = WatchFoldersController.__new__(WatchFoldersController)
        record = {
            "repositories": ["removed_repository"],
            "path": "project/assets/ASSET0001",
        }
        with (
            patch.object(env_tactic, "base_dirs", {}),
            patch.object(
                env_tactic, "get_base_dir", side_effect=KeyError("missing")
            ),
        ):
            paths, repositories, pending = controller._absolute_paths(record)

        self.assertEqual(paths, [])
        self.assertEqual(repositories, [])
        self.assertFalse(pending)

    def test_process_directories_are_created_below_watch_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "watch"
            WatchFoldersController._mkdirs(
                [str(root)], ["model", "publish", "animation"]
            )
            self.assertTrue(root.is_dir())
            self.assertTrue((root / "model").is_dir())
            self.assertTrue((root / "publish").is_dir())
            self.assertTrue((root / "animation").is_dir())

    def test_watch_event_payload_targets_the_watched_sobject(self):
        payload = WatchFoldersController._watch_payload(
            _PayloadHarness(),
            {
                "searchKey": "skey://demo/asset?code=ASSET0001",
                "pipeline": "asset",
            },
            Path("D:/repo/watch/model/mesh.ma"),
            "client_repo",
            "model",
        )
        self.assertEqual(
            payload["searchKey"], "skey://demo/asset?code=ASSET0001"
        )
        self.assertEqual(payload["context"], "model")
        self.assertEqual(payload["description"], "From watch folder")
        self.assertEqual(payload["repository"], "client_repo")
        self.assertEqual(payload["files"][0]["template"], "$FILENAME.$EXT")
        self.assertEqual(payload["mode"], "copy")

    def test_last_repository_can_remove_an_existing_watch_folder(self):
        controller = _watch_controller()
        record = _watch_record(["client"])
        controller.model.replace([record])
        controller._editing_row = 0
        controller._editor = dict(record, repositories=[])

        self.assertTrue(controller.canSaveEditor)
        with patch.object(controller, "_persist") as persist:
            self.assertTrue(controller.save_edit())

        self.assertEqual(controller.model.count(), 0)
        persist.assert_called_once_with()
        self.assertEqual(
            controller._application.window_model.closed,
            ["watch_folder_editor"],
        )

    def test_new_watch_folder_still_requires_a_repository(self):
        controller = _watch_controller()
        controller._editing_row = -1
        controller._editor = _watch_record([])

        self.assertFalse(controller.canSaveEditor)

    def test_save_availability_tracks_busy_state(self):
        controller = _watch_controller()
        controller._editing_row = 0
        controller.model.replace([_watch_record(["client"])])
        controller._editor = _watch_record([])
        changes = []
        controller.canSaveEditorChanged.connect(
            lambda: changes.append(controller.canSaveEditor)
        )

        controller._busy = True
        controller.stateChanged.emit()
        controller._busy = False
        controller.stateChanged.emit()

        self.assertEqual(changes, [False, True])

    def test_manager_keeps_the_complete_watch_folder_interface(self):
        source = (
            ROOT / "thlib" / "ui" / "qml" / "WatchFoldersView.qml"
        ).read_text(encoding="utf-8")
        self.assertIn('text: qsTr("Active Watch Folders  ·  ")', source)
        self.assertIn("required property string path", source)
        self.assertIn("required property string repository", source)
        self.assertIn("required property string stype", source)
        self.assertIn("required property string pipeline", source)
        self.assertIn("required property string watcherStatus", source)
        self.assertNotIn('iconName: "add"', source)
        self.assertNotIn("watchFoldersController.begin_add()", source)
        self.assertIn("required property string searchKey", source)
        self.assertIn("watchFoldersController.begin_edit_search_key(", source)
        self.assertNotIn("watchFoldersController.begin_edit(watchRow.index)", source)
        self.assertIn("watchFoldersController.set_enabled(", source)
        self.assertIn("WatchFolderDeleteDialog", source)

    def test_primary_menu_opens_complete_manager_after_reload(self):
        events = []
        harness = SimpleNamespace(
            watch_folders=SimpleNamespace(
                reload=lambda: events.append("reload")
            ),
            window_model=SimpleNamespace(
                show_window=lambda window_id: events.append(window_id)
            ),
        )

        LifecycleMixin._show_watch_folders(harness)

        self.assertEqual(events, ["reload", "watch_folders"])
        menu = (ROOT / "thlib" / "ui" / "menu_schema.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("show_watch_folders", menu)

    def test_manager_and_item_editor_are_separate_modal_windows(self):
        source = (
            ROOT / "thlib" / "ui" / "workspace_models" / "windows.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'FloatingWindow("watch_folders", "Watch Folders", '
            '"watch_folders", .16, .13, .68, .70, blocking=True)',
            source,
        )
        self.assertIn(
            'FloatingWindow("watch_folder_editor", "Watch Folder", '
            '"watch_folder_editor", .25, .20, .50, .50, blocking=True)',
            source,
        )

    def test_item_create_opens_context_editor_without_manager_dock(self):
        source = object()
        node = SimpleNamespace(
            source=source,
            search_key="skey://demo/asset?code=ASSET0001",
            watch_state="none",
        )
        controller = _ItemActionHarness(node)

        controller.invoke_item_action("create_watch", "asset-node")

        self.assertEqual(controller.watch_folders.added, [(source, "item")])
        self.assertEqual(controller.dock_model.shown, [])

    def test_item_watch_button_reuses_context_editor(self):
        source = object()
        node = SimpleNamespace(
            source=source,
            search_key="skey://demo/asset?code=ASSET0001",
            watch_state="enabled",
        )
        controller = _ItemActionHarness(node)

        controller.invoke_item_action("watch_folder", "asset-node")

        self.assertEqual(
            controller.watch_folders.edited,
            [(node.search_key, "item")],
        )
        self.assertEqual(controller.watch_folders.added, [])
        self.assertEqual(controller.dock_model.shown, [])

    def test_item_edit_reuses_context_editor_for_exact_sobject(self):
        source = object()
        node = SimpleNamespace(
            source=source,
            search_key="skey://demo/asset?code=ASSET0001",
            watch_state="enabled",
        )
        controller = _ItemActionHarness(node)

        controller.invoke_item_action("edit_watch", "asset-node")

        self.assertEqual(
            controller.watch_folders.edited,
            [(node.search_key, "item")],
        )
        self.assertEqual(controller.watch_folders.added, [])
        self.assertEqual(controller.dock_model.shown, [])
    def test_item_delete_uses_context_dialog_without_manager_dock(self):
        node = SimpleNamespace(
            source=object(),
            search_key="skey://demo/asset?code=ASSET0001",
            watch_state="enabled",
        )
        controller = _ItemActionHarness(node)

        controller.invoke_item_action("delete_watch", "asset-node")

        self.assertEqual(
            controller.watch_folders.removed,
            [(node.search_key, "item")],
        )
        self.assertEqual(controller.dock_model.shown, [])
    def test_editor_dialog_is_shared_by_item_and_manager_hosts(self):
        dialog = (
            ROOT / "thlib" / "ui" / "qml" / "WatchFolderEditorView.qml"
        ).read_text(encoding="utf-8")
        manager = (
            ROOT / "thlib" / "ui" / "qml" / "WatchFoldersView.qml"
        ).read_text(encoding="utf-8")
        main = (
            ROOT / "thlib" / "ui" / "qml" / "Main.qml"
        ).read_text(encoding="utf-8")
        self.assertNotIn("WatchFolderEditorDialog", manager)
        self.assertNotIn("WatchFolderEditorDialog", main)
        self.assertIn("WatchFolderDeleteDialog", manager)
        self.assertNotIn("id: repositoryDialog", manager)
        self.assertIn('text: qsTr("Relative Watch Path:")', dialog)
    def test_application_wires_watch_events_to_commit_queue(self):
        source = (ROOT / "thlib/ui/application.py").read_text(encoding="utf-8")
        block_start = source.index(
            "watch_folders_controller = WatchFoldersController("
        )
        block = source[block_start:block_start + 260]
        self.assertIn("checkin_out_controller", block)
        self.assertIn("commit_queue_controller", block)
        self.assertNotIn("matching_templates_controller", block)
        self.assertNotIn("drop_plate_controller", block)


    def test_watch_control_is_persistent_and_green_when_enabled(self):
        missing = WorkspaceNode(
            node_id="missing", node_type="sobject",
            search_key="skey://demo/asset?code=ASSET0000",
            code="ASSET0000", title="Missing", watch_state="none",
        )
        missing_control = next(
            item for item in WorkspaceItemModel._controls_for(missing)
            if item["command"] == "watch_folder"
        )
        self.assertEqual(missing_control["icon"], "visibility_off")
        self.assertFalse(missing_control["persistent"])
        self.assertFalse(missing_control["success"])

        enabled = WorkspaceNode(
            node_id="asset", node_type="sobject",
            search_key="skey://demo/asset?code=ASSET0001",
            code="ASSET0001", title="Asset", watch_state="enabled",
        )
        control = next(
            item for item in WorkspaceItemModel._controls_for(enabled)
            if item["command"] == "watch_folder"
        )
        self.assertEqual(control["icon"], "visibility")
        self.assertTrue(control["persistent"])
        self.assertTrue(control["success"])

        disabled = WorkspaceNode(
            node_id="disabled", node_type="sobject",
            search_key="skey://demo/asset?code=ASSET0002",
            code="ASSET0002", title="Disabled", watch_state="disabled",
        )
        disabled_control = next(
            item for item in WorkspaceItemModel._controls_for(disabled)
            if item["command"] == "watch_folder"
        )
        self.assertEqual(disabled_control["icon"], "visibility")
        self.assertTrue(disabled_control["persistent"])
        self.assertTrue(disabled_control["active"])
        self.assertTrue(disabled_control["success"])

    def test_workspace_watch_state_updates_without_search_reload(self):
        model = WorkspaceItemModel()
        node = WorkspaceNode(
            node_id="asset", node_type="sobject",
            search_key="skey://demo/asset?code=ASSET0001",
            code="ASSET0001", title="Asset",
        )
        model._nodes = {node.node_id: node}
        model._items = [node]
        model._rebuild_row_map()

        model.update_watch_state(node.search_key, "enabled")

        self.assertEqual(node.watch_state, "enabled")
        control = next(
            item for item in model._controls_for(node)
            if item["command"] == "watch_folder"
        )
        self.assertTrue(control["persistent"])
        self.assertTrue(control["success"])

    def test_watch_dialogs_are_modal_and_rows_use_shared_surface(self):
        editor = (
            ROOT / "thlib" / "ui" / "qml" / "WatchFolderEditorView.qml"
        ).read_text(encoding="utf-8")
        delete = (
            ROOT / "thlib" / "ui" / "qml" / "WatchFolderDeleteDialog.qml"
        ).read_text(encoding="utf-8")
        result_item = (
            ROOT / "thlib" / "ui" / "qml" / "WorkspaceResultItem.qml"
        ).read_text(encoding="utf-8")
        card = (
            ROOT / "thlib" / "ui" / "qml" / "WorkspaceCard.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("Item {", editor)
        self.assertNotIn("Controls.Dialog {", editor)
        self.assertIn("modal: true", delete)
        self.assertIn("dim: true", delete)
        self.assertIn("focus: true", delete)
        self.assertIn("ItemSurface {", editor)
        self.assertIn("normalColor: root.theme.row", editor)
        self.assertNotIn('name: "folder_special"', editor)
        self.assertIn('icon.name: "delete"', editor)
        self.assertIn("destructive: true", editor)
        self.assertIn('icon.name: "delete"', delete)
        self.assertIn('text: qsTr("Delete")', delete)
        self.assertNotIn('text: qsTr("Keep")', delete)
        self.assertIn(
            "watchFoldersController.confirm_remove(false)", delete
        )
        self.assertNotIn("confirm_remove(true)", delete)
        self.assertIn("hasPersistentItemControls", result_item)
        self.assertIn("modelData.success ? root.theme.green", result_item)
        self.assertIn("hasPersistentItemControls", card)
        self.assertIn("modelData.success ? root.theme.green", card)

if __name__ == "__main__":
    unittest.main()
