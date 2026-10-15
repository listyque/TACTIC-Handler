import unittest
from copy import deepcopy
from types import SimpleNamespace

from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.controllers.navigation import NavigationMixin
from thlib.ui.controllers.search_suggestions import SearchSuggestionsMixin
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.models import NavigationEntry, NavigationModel
from thlib.ui.search_contract import records_from_filters


class _SObject:
    def __init__(self, code):
        self._code = code

    def get_code(self):
        return self._code


class _NavigationHarness(SearchSuggestionsMixin):
    def __init__(self, entries=()):
        self._sessions = {}
        self._current_section_key = ""
        self._page_size = 25
        self._default_view_mode = "continious"
        self.navigation_model = NavigationModel(entries)

    def _current_section(self):
        return self._sessions.get(self._current_section_key)

    def _current_tab(self):
        section = self._current_section()
        if section is None:
            return None
        return next(
            (tab for tab in section.tabs if tab.tab_id == section.current_tab_id),
            None,
        )

    def _capture_current_workspace_layout(self):
        tab = self._current_tab()
        dock_model = getattr(self, "dock_model", None)
        if tab is not None and dock_model is not None:
            tab.workspace_layout = deepcopy(dock_model.capture_layout())

    @staticmethod
    def _visible_sobjects(tab, _section=None):
        hidden = set(tab.quick_filters.get("hidden_codes", ()))
        return [
            sobject for sobject in tab.sobjects
            if sobject.get_code() not in hidden
        ]

    def _create_section(self, key, title, accent=""):
        existing = self._sessions.get(key)
        if existing:
            return existing
        entry = self.navigation_model.entry(key)
        tab = SearchTabSession(
            tab_id=f"{key}:base",
            title=title,
            tab_kind="base",
        )
        section = SectionSession(
            entry_key=key,
            title=title,
            accent=accent,
            search_type=(
                entry.search_type if entry else key.partition("@")[0]
            ),
            base_filters=(),
            tabs=[tab],
            current_tab_id=tab.tab_id,
        )
        self._sessions[key] = section
        return section


def _section(key, filters=(), objects=()):
    tab = SearchTabSession(
        tab_id=f"{key}:tab",
        title=key,
        tab_kind="base",
        loaded=True,
        sobjects=list(objects),
    )
    return SectionSession(
        entry_key=key,
        title=key,
        accent="",
        search_type="demo/asset",
        base_filters=filters,
        tabs=[tab],
        current_tab_id=tab.tab_id,
    )


class SearchKeyNavigationTests(unittest.TestCase):
    def test_item_new_tab_action_appends_a_filtered_tab(self):
        controller = _NavigationHarness()
        source = _SObject("ASSET001")
        source.get_title = lambda: "Asset One"
        source.get_stype = lambda: SimpleNamespace(
            get_code=lambda: "demo/asset",
            get_pretty_name=lambda: "Assets",
            get_stype_color=lambda fmt="hex": "#123456",
        )
        source.get_search_key = (
            lambda: "demo/asset?project=demo&code=ASSET001"
        )
        section = _section("demo/asset@assets", objects=(source,))
        controller._sessions[section.entry_key] = section
        controller._current_section_key = section.entry_key
        controller._current_project_code = "demo"
        controller.debug_log = None
        controller._node_for_any = lambda _node_id: SimpleNamespace(
            node_type="sobject", source=source
        )
        controller._file_object_for_node = lambda _node_id: None
        controller._current_tab = lambda: next(
            tab for tab in section.tabs
            if tab.tab_id == section.current_tab_id
        )
        controller._capture_current_tree_state = lambda: None
        controller._capture_current_workspace_layout = lambda: None
        controller._sync_search_tabs = lambda: None
        controller.section_state_changed = SimpleNamespace(emit=lambda: None)
        loaded = []
        controller._load_tab = loaded.append
        controller.activate_section = lambda key: setattr(
            controller, "_current_section_key", key
        )
        controller._open_sobject_on_new_tab = lambda item: (
            ItemOperationsMixin._open_sobject_on_new_tab(controller, item)
        )

        ItemOperationsMixin.invoke_item_action(
            controller, "new_tab", "asset-node"
        )

        self.assertEqual(len(section.tabs), 2)
        self.assertEqual(section.current_tab_id, section.tabs[-1].tab_id)
        self.assertEqual(section.tabs[-1].title, "Asset One")
        self.assertEqual(
            section.tabs[-1].extra_filters,
            [("code", "=", "ASSET001")],
        )
        self.assertEqual(loaded, [section.tabs[-1]])

    def test_new_tab_action_ignores_non_sobject_nodes(self):
        controller = _NavigationHarness()
        source = _SObject("ASSET001")
        opened = []
        controller.debug_log = None
        controller._node_for_any = lambda _node_id: SimpleNamespace(
            node_type="snapshot", source=source
        )
        controller._file_object_for_node = lambda _node_id: None
        controller._open_sobject_on_new_tab = opened.append

        ItemOperationsMixin.invoke_item_action(
            controller, "new_tab", "snapshot-node"
        )

        self.assertEqual(opened, [])

    def test_local_identity_uses_code_without_server_resolution(self):
        parsed = _NavigationHarness._local_search_key_identity(
            "skey://demo/asset?project=sample&code=ASSET001"
        )

        self.assertEqual(parsed, {
            "namespace": "demo",
            "pipeline_code": "asset",
            "project": "sample",
            "code": "ASSET001",
            "type": "sobject",
        })

    def test_snapshot_identity_still_requires_snapshot_resolution(self):
        self.assertIsNone(_NavigationHarness._local_search_key_identity(
            "skey://sthpw/snapshot?project=sample&code=SNAPSHOT001"
        ))

    def test_loaded_object_can_be_reused_in_filtered_preset(self):
        controller = _NavigationHarness()
        preset = _section(
            "demo/asset@my_assets",
            filters=(("assigned", "=", "me"),),
            objects=(_SObject("ASSET001"),),
        )
        controller._sessions[preset.entry_key] = preset
        controller._current_section_key = preset.entry_key

        result = controller._loaded_search_key_target(
            "demo/asset", "ASSET001"
        )

        self.assertEqual(result[:2], (preset, preset.tabs[0]))

    def test_object_hidden_by_local_filter_is_not_reused(self):
        controller = _NavigationHarness()
        preset = _section(
            "demo/asset@my_assets",
            filters=(("assigned", "=", "me"),),
            objects=(_SObject("ASSET001"),),
        )
        preset.tabs[0].quick_filters = {
            "hidden_codes": {"ASSET001"},
        }
        controller._sessions[preset.entry_key] = preset

        self.assertIsNone(controller._loaded_search_key_target(
            "demo/asset", "ASSET001"
        ))

    def test_new_target_prefers_unfiltered_section_over_preset(self):
        entries = (
            NavigationEntry(
                key="demo/asset@my_assets",
                title="My Assets",
                glyph="sobject",
                group="Project",
                command="open",
                search_type="demo/asset",
                filter_records=tuple(records_from_filters(
                    [("assigned", "=", "me")]
                )),
            ),
            NavigationEntry(
                key="demo/asset@assets",
                title="Assets",
                glyph="sobject",
                group="Project",
                command="open",
                search_type="demo/asset",
            ),
        )
        controller = _NavigationHarness(entries)
        preset = controller._create_section(
            "demo/asset@my_assets", "My Assets"
        )
        controller._current_section_key = preset.entry_key

        section = controller._unfiltered_search_key_section(
            "demo/asset", "Assets", "#123456"
        )

        self.assertEqual(section.entry_key, "demo/asset@assets")
        self.assertEqual(section.base_filters, ())

    def test_relation_navigation_uses_unfiltered_search_type_section(self):
        entries = (
            NavigationEntry(
                key="demo/asset@in_progress",
                title="In Progress Assets",
                glyph="progress-clock",
                group="Project",
                command="open",
                search_type="demo/asset",
                filter_records=tuple(records_from_filters(
                    [("status", "=", "In Progress")]
                )),
            ),
            NavigationEntry(
                key="demo/asset@assets",
                title="Assets",
                glyph="asset",
                group="Project",
                command="open",
                search_type="demo/asset",
            ),
        )
        controller = _NavigationHarness(entries)
        controller.activate_section = lambda key: setattr(
            controller, "_current_section_key", key
        )
        controller._sync_search_tabs = lambda: None
        controller._load_tab = lambda tab: setattr(
            controller, "loaded_tab", tab
        )

        class SearchType:
            def __init__(self, code, title, project=None):
                self.code = code
                self.title = title
                self.project = project

            def get_project(self):
                return self.project

            def get_pretty_name(self):
                return self.title

            @staticmethod
            def get_stype_color(fmt="hex"):
                return "#ef5350" if fmt == "hex" else ""

        asset_stype = SearchType("demo/asset", "Assets")
        project = SimpleNamespace(stypes={"demo/asset": asset_stype})
        parent_stype = SearchType("demo/episode", "Episodes", project)
        source = SimpleNamespace(
            get_stype=lambda: parent_stype,
            get_title=lambda: "Episode 01",
            get_related_sobjects_tel_string=lambda **_kwargs: "@SOBJECT(...)"
        )
        controller.workspace_model = SimpleNamespace(
            node_for=lambda _node_id: SimpleNamespace(source=source)
        )

        ItemOperationsMixin._open_related_search(
            controller, "episode-node", "child", "demo/asset"
        )

        section = controller._current_section()
        self.assertEqual(section.entry_key, "demo/asset@assets")
        self.assertEqual(controller.navigation_model.entry(
            section.entry_key
        ).glyph, "asset")
        self.assertEqual(controller.loaded_tab.tab_kind, "related")
        self.assertEqual(
            controller.loaded_tab.extra_filters,
            [("_expression", "in", "@SOBJECT(...)")],
        )

    def test_completion_opens_the_existing_related_search_workflow(self):
        calls = []
        controller = SimpleNamespace(
            _open_related_search=lambda *args: calls.append(args),
            _notify=lambda _message: None,
        )

        ItemOperationsMixin.open_completion(
            controller, "episode-node", "demo/shot"
        )

        self.assertEqual(calls, [("episode-node", "child", "demo/shot")])

    def test_direct_section_reuses_blank_tab_for_navigation(self):
        controller = _NavigationHarness()
        section = controller._unfiltered_search_key_section(
            "demo/asset", "Assets", "#123456"
        )

        tab = controller._prepare_search_key_tab(
            section,
            "Asset One",
            "ASSET001",
            {"type": "sobject"},
        )

        self.assertEqual(len(section.tabs), 1)
        self.assertEqual(tab.tab_kind, "navigation")
        self.assertEqual(tab.navigation_target, "ASSET001")
        self.assertEqual(tab.extra_filters, [("code", "=", "ASSET001")])
        self.assertEqual(section.base_filters, ())

    def test_created_object_navigation_keeps_current_dock_layout(self):
        controller = _NavigationHarness()
        section = _section("demo/asset@assets")
        controller._sessions[section.entry_key] = section
        controller._current_section_key = section.entry_key
        live_layout = {"panels": [{"id": "results", "size": 410}]}
        applied = []
        controller.dock_model = SimpleNamespace(
            capture_layout=lambda: deepcopy(live_layout),
            apply_layout=lambda layout: applied.append(layout) or True,
        )
        section.layout_preset = "task_layout"
        controller._workspace_layout_presets = SimpleNamespace(
            apply_assigned=lambda _preset: self.fail(
                "Object navigation must not apply the section layout preset"
            )
        )
        original_tab = section.tabs[0]

        new_tab = controller._prepare_search_key_tab(
            section, "New Asset", "ASSET002", {"type": "sobject"}
        )

        self.assertEqual(original_tab.workspace_layout, live_layout)
        self.assertEqual(new_tab.workspace_layout, live_layout)
        self.assertIsNot(new_tab.workspace_layout, original_tab.workspace_layout)
        NavigationMixin._apply_tab_workspace_layout(
            controller, section, new_tab
        )
        self.assertEqual(applied, [live_layout])

    def test_navigation_tab_preserves_requested_notes_process(self):
        controller = _NavigationHarness()
        section = controller._unfiltered_search_key_section(
            "demo/asset", "Assets", "#123456"
        )

        tab = controller._prepare_search_key_tab(
            section,
            "Asset One",
            "ASSET001",
            {"type": "sobject"},
            "model",
        )

        self.assertEqual(tab.pending_detail_process, "model")

    def test_saved_search_link_reuses_one_addressed_preset_tab(self):
        controller = _NavigationHarness()
        controller.activate_section = lambda key: setattr(
            controller, "_current_section_key", key
        )
        controller._save_search_cache = lambda: None
        spec = {
            "project": "demo",
            "search_type": "demo/asset",
            "view": "link_search:published:demo/asset",
        }
        preset = {
            "title": "Published",
            "records": records_from_filters([
                ("status", "=", "Published")
            ]),
        }

        first = controller._activate_saved_search_preset(spec, preset)
        second = controller._activate_saved_search_preset(spec, preset)
        section = controller._current_section()

        self.assertEqual(first.tab_id, second.tab_id)
        self.assertEqual(len([
            tab for tab in section.tabs
            if tab.tab_kind == "preset-link"
        ]), 1)
        self.assertIn(
            ("status", "=", "Published"), second.extra_filters
        )


if __name__ == "__main__":
    unittest.main()
