from __future__ import annotations

from types import SimpleNamespace
import unittest

from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.workspace_models.windows import FloatingWindowModel


class _SObject:
    def __init__(self, name, stype):
        self.name = name
        self.stype = stype

    def get_stype(self):
        return self.stype


class _WindowModel:
    def __init__(self):
        self.opened = []

    def show_window(self, window_id):
        self.opened.append(window_id)


class _Signal:
    def __init__(self):
        self.emissions = 0

    def emit(self):
        self.emissions += 1


class _VisibleWindowModel(_WindowModel):
    def __init__(self):
        super().__init__()
        self.raised = []

    @staticmethod
    def is_window_visible(_window_id):
        return True

    def raise_window(self, window_id):
        self.raised.append(window_id)


class _Operations(ItemOperationsMixin):
    _current_project_code = "demo"
    debug_log = None

    def __init__(self):
        self.old_stype = object()
        self.clicked_stype = object()
        self.old_source = _SObject("old", self.old_stype)
        self.clicked_source = _SObject("clicked", self.clicked_stype)
        self.nodes = {
            "old": SimpleNamespace(
                node_id="old", node_type="sobject", parent_id="",
                source=self.old_source, search_key="demo/asset?code=OLD",
            ),
            "clicked": SimpleNamespace(
                node_id="clicked", node_type="sobject", parent_id="",
                source=self.clicked_source,
                search_key="demo/asset?code=CLICKED",
            ),
        }
        self.tab = SimpleNamespace(
            selected_node_id="old", title="Assets", stype=self.old_stype,
        )
        self.window_model = _WindowModel()
        self.notifications = []

    def _current_tab(self):
        return self.tab

    def _node_for_any(self, node_id):
        return self.nodes.get(node_id)

    def _active_stype(self):
        return self.tab.stype

    @staticmethod
    def _file_object_for_node(_node_id):
        return None

    def _notify(self, message):
        self.notifications.append(message)

    @staticmethod
    def select_sobject(_search_key):
        raise AssertionError("Repo Sync must not depend on async selection")


class RepositorySyncScopeTests(unittest.TestCase):
    def test_context_process_windows_are_not_restored_before_search_bootstrap(self):
        self.assertIn(
            "repository_sync_editor",
            FloatingWindowModel._context_required_windows,
        )
        self.assertIn(
            "process_filter_editor",
            FloatingWindowModel._context_required_windows,
        )

    def test_item_repo_sync_uses_clicked_item_instead_of_old_selection(self):
        operations = _Operations()

        operations.invoke_item_action("repo_sync", "clicked")
        context = operations.repository_sync_editor_context()

        self.assertEqual(
            operations.window_model.opened, ["repository_sync_editor"]
        )
        self.assertIs(context["sobject"], operations.clicked_source)
        self.assertIs(context["stype"], operations.clicked_stype)

    def test_item_repo_sync_keeps_child_stype_and_repeatable_context(self):
        operations = _Operations()
        operations._current_section = lambda: SimpleNamespace(
            search_type="demo/asset"
        )

        operations.invoke_item_action("repo_sync", "clicked")
        first = operations.repository_sync_editor_context()
        second = operations.repository_sync_editor_context()

        self.assertIs(first["sobject"], operations.clicked_source)
        self.assertIs(first["stype"], operations.clicked_stype)
        self.assertIs(second["sobject"], operations.clicked_source)
        self.assertIs(second["stype"], operations.clicked_stype)

    def test_search_type_repo_sync_has_no_single_sobject_scope(self):
        operations = _Operations()

        operations.open_search_type_repository_sync()
        context = operations.repository_sync_editor_context()

        self.assertEqual(
            operations.window_model.opened, ["repository_sync_editor"]
        )
        self.assertIsNone(context["sobject"])
        self.assertIs(context["stype"], operations.old_stype)
        self.assertEqual(context["tab_name"], "Assets")

    def test_open_editor_refreshes_scope_when_window_is_already_visible(self):
        operations = _Operations()
        operations.window_model = _VisibleWindowModel()
        operations.repositorySyncEditorRequested = _Signal()

        operations.open_search_type_repository_sync()

        self.assertEqual(
            operations.repositorySyncEditorRequested.emissions, 1
        )
        self.assertEqual(
            operations.window_model.raised, ["repository_sync_editor"]
        )
        self.assertEqual(operations.window_model.opened, [])


if __name__ == "__main__":
    unittest.main()
