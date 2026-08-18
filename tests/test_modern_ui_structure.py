from pathlib import Path
import re
import unittest

from modern_ui.workspace_models.windows import FloatingWindowModel


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "modern_ui" / "qml"


class ModernUiStructureTests(unittest.TestCase):
    def test_preview_presenters_do_not_load_remote_file_paths_directly(self):
        presenters = (
            ROOT / "modern_ui" / "models.py",
            ROOT / "modern_ui" / "tasks.py",
            ROOT / "modern_ui" / "user.py",
            ROOT / "modern_ui" / "skey_previews.py",
            ROOT / "modern_ui" / "workspace_models"
            / "results_presentation.py",
            ROOT / "modern_ui" / "workspace_models"
            / "state_snapshot_state.py",
        )
        offenders = [
            str(path.relative_to(ROOT))
            for path in presenters
            if "get_full_web_path(" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])

    def test_window_model_is_the_only_standalone_content_registry(self):
        for window in FloatingWindowModel._defaults():
            source = FloatingWindowModel._content_source(window)
            self.assertTrue(source.endswith(".qml"))
            self.assertTrue(
                (QML / source).is_file(), (window.window_id, source)
            )

        host = (QML / "WindowContent.qml").read_text(encoding="utf-8")
        self.assertNotIn("Component {", host)
        self.assertNotIn("ConfigurationView", host)
        self.assertNotIn("MessagesView", host)

    def test_sidebar_search_editor_reuses_advanced_search_view(self):
        windows = {
            window.window_id: window
            for window in FloatingWindowModel._defaults()
        }
        sidebar_search = windows["sidebar_advanced_search"]
        self.assertEqual(sidebar_search.kind, "advanced_search")
        self.assertTrue(sidebar_search.blocking)
        self.assertEqual(
            FloatingWindowModel._content_source(sidebar_search),
            "AdvancedSearchView.qml",
        )

        navigation = (
            ROOT / "modern_ui" / "controllers" / "navigation.py"
        ).read_text(encoding="utf-8")
        method = navigation.split(
            "def edit_sidebar_search_presets", 1
        )[1].split("def _show_tab_if_current", 1)[0]
        self.assertIn('show_window("sidebar_advanced_search")', method)
        self.assertNotIn('show_window("filter_editor")', method)

    def test_saved_searches_and_process_visibility_are_separate_tools(self):
        windows = {
            window.window_id: window
            for window in FloatingWindowModel._defaults()
        }
        self.assertNotIn("filter_editor", windows)
        self.assertEqual(
            FloatingWindowModel._content_source(
                windows["process_filter_editor"]
            ),
            "ProcessFilterEditorView.qml",
        )
        self.assertFalse((QML / "FilterEditorView.qml").exists())
        advanced_search = (QML / "AdvancedSearchView.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("filterPresetModel", advanced_search)
        self.assertIn("save_current_search_as", advanced_search)

    def test_sidebar_editor_and_drawer_share_the_same_tree_row(self):
        drawer_source = (QML / "NavigationDrawer.qml").read_text(
            encoding="utf-8"
        )
        for name in ("NavigationDrawer.qml", "SidebarEditorView.qml"):
            source = (QML / name).read_text(encoding="utf-8")
            self.assertIn("SidebarTreeRow {", source)

        shared_row = (QML / "SidebarTreeRow.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("ItemPreview {", shared_row)
        self.assertIn("MaterialRipple {", shared_row)
        self.assertIn("SmoothListView {", drawer_source)
        self.assertIn("onWheel: wheel => wheel.accepted = true", drawer_source)

    def test_dock_host_only_owns_layout_and_routes_content(self):
        host = (QML / "DockHost.qml").read_text(encoding="utf-8")
        self.assertLess(len(host.splitlines()), 600)
        self.assertIn("DockContentRegistry", host)
        self.assertNotIn("TaskDockView", host)
        self.assertNotIn("CommunicationView", host)

    def test_main_top_bar_is_fixed_and_compact(self):
        source = (QML / "Main.qml").read_text(encoding="utf-8")
        top_bar = source.split("id: topAppBar", 1)[1].split(
            "id: workspaceLayer", 1
        )[0]
        self.assertIn("height: 44", top_bar)
        self.assertIn("controlExtent: 36", top_bar)
        self.assertIn("controlSurfaceExtent: 32", top_bar)
        self.assertIn("height: topAppBar.height", top_bar)
        self.assertNotIn("expansionProgress", top_bar)
        self.assertNotIn("topAppBarHover", top_bar)
        self.assertNotIn("topAppBarCollapseTimer", top_bar)
        self.assertIn("z: 100", top_bar)
    def test_search_chrome_keeps_search_above_tabs(self):
        source = (QML / "DockContentRegistry.qml").read_text(
            encoding="utf-8"
        )
        header_index = source.index("id: searchHeader")
        tabs_index = source.index("id: searchTabs", header_index)
        results_index = source.index("id: resultsArea", tabs_index)
        self.assertLess(header_index, tabs_index)
        self.assertLess(tabs_index, results_index)

        header = source[header_index:tabs_index]
        tabs = source[tabs_index:results_index]
        self.assertIn("anchors.top: parent.top", header)
        self.assertIn(
            "height: root.theme.dockWorkspaceHeaderHeight / 2",
            header,
        )
        self.assertIn("anchors.top: searchHeader.bottom", tabs)
        self.assertIn(
            "height: root.theme.dockWorkspaceHeaderHeight / 2",
            tabs,
        )
        self.assertIn("id: searchTabsView", tabs)
        self.assertIn("id: addSearchTabButton", tabs)
        self.assertLess(
            tabs.index("id: addSearchTabButton"),
            tabs.index("id: searchTabsView"),
        )
    def test_project_qml_uses_shared_controls_for_common_primitives(self):
        forbidden = re.compile(
            r"^\s*(?:Button|TextField|TextArea|Dialog|Popup|BusyIndicator)\s*\{",
            re.MULTILINE,
        )
        offenders = []
        for path in QML.glob("*.qml"):
            if forbidden.search(path.read_text(encoding="utf-8")):
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_inline_busy_indicators_receive_the_active_theme(self):
        pattern = re.compile(
            r"Md3BusyIndicator\s*\{([^{}]|\{[^{}]*\})*\}", re.DOTALL
        )
        offenders = []
        for path in QML.glob("*.qml"):
            if path.name == "Md3BusyIndicator.qml":
                continue
            for block in pattern.finditer(path.read_text(encoding="utf-8")):
                if "uiTheme:" not in block.group(0):
                    offenders.append(path.name)
                    break
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
