from __future__ import annotations

from types import SimpleNamespace
import unittest

from thlib.tactic_classes import BeautifulSoup

from modern_ui.controllers.advanced_search import AdvancedSearchMixin
from modern_ui.controllers.navigation import NavigationMixin
from modern_ui.controllers.types import SearchTabSession
from modern_ui.models import NavigationEntry
from modern_ui.models import NavigationModel
from modern_ui.search_presets import presets_from_rows, records_from_config


def test_sidebar_icon_comes_from_project_definition_without_search_type_guess():
    assert NavigationModel._icon_name("box", "demo/assets") == "box"
    assert NavigationModel._icon_name("custom-star", "demo/tasks") == "custom-star"
    assert NavigationModel._icon_name(
        "FAS_PROJECT_DIAGRAM", "demo/tasks"
    ) == "project-diagram"
    assert NavigationModel._icon_name("", "demo/scenes") == "sidebar-link"


SEARCH_CONFIG = """<config>
  <filter>
    <values type="json">[{"prefix":"filter_mode","filter_mode":"and"},{"prefix":"main_body","main_body_enabled":"on","filter_type":"_column","main_body_column":"name","main_body_relation":"contains","main_body_value":""},{"prefix":"main_body","main_body_enabled":"on","filter_type":"_column","main_body_column":"_expression","main_body_relation":"expression","main_body_op":"in","main_body_value":"@SOBJECT(sthpw/task['assigned', '$LOGIN'])"},{"prefix":"search_ops","levels":[0],"ops":["and"],"modes":["child"]}]</values>
  </filter>
</config>"""


class _NavigationModel:
    def __init__(self, entry):
        self._entry = entry

    def entry(self, key):
        return self._entry if self._entry.key == key else None


class _SidebarHarness(NavigationMixin, AdvancedSearchMixin):
    def __init__(self, entry):
        self.navigation_model = _NavigationModel(entry)
        self._sessions = {}
        self._page_size = 25
        self._default_view_mode = "continious"
        self._pending_search_loads = {}
        self._search_workers = {}
        self._quick_filter_workers = {}
        self._current_section_key = ""
        self.section_state_changed = SimpleNamespace(emit=lambda: None)
        self.sync_count = 0
        self.preset_requests = 0
        self.requested_tab_name = ""

    def _sync_section_model(self):
        pass

    def _save_opened_sections(self):
        pass

    def _save_search_cache(self):
        pass

    def _sync_search_tabs(self, clear_suggestions=True):
        self.sync_count += 1

    def _request_sidebar_presets(self, section):
        self.preset_requests += 1


class SidebarSearchContractTests(unittest.TestCase):
    def test_sidebar_visibility_and_default_result_view_are_runtime_data(self):
        definitions = BeautifulSoup(
            "<config>"
            "<element name='hidden' title='Hidden' is_visible='off'>"
            "<display class='LinkWdg'><widget_key>view_panel</widget_key>"
            "</display></element>"
            "<element name='cards' title='Cards' is_visible='on'>"
            "<display class='LinkWdg'><widget_key>view_panel</widget_key>"
            "<view_mode>tiles</view_mode></display>"
            "<search_type>demo/assets</search_type></element>"
            "</config>",
            "html.parser",
        ).find_all("element")
        requested = BeautifulSoup(
            "<config><element name='hidden'/><element name='cards'/></config>",
            "html.parser",
        ).find_all("element")

        class Views:
            @staticmethod
            def has_definition():
                return True

            @staticmethod
            def get_view(search_type, view=None, bs=False):
                if search_type != "SideBarWdg":
                    return None
                return requested if view == "tactic_handler" else definitions

        project = SimpleNamespace(
            get_config_views=lambda: Views(),
            get_code=lambda: "demo",
            get_stypes=lambda: {},
        )
        login = SimpleNamespace(check_security=lambda **_kwargs: "allow")

        entries = NavigationModel.build_project_entries(project, login)

        self.assertEqual([entry.title for entry in entries], ["Cards"])
        self.assertEqual(entries[0].view_mode, "tiles")

    def test_search_view_parser_keeps_name_and_expression_cards(self):
        records = records_from_config(SEARCH_CONFIG)

        self.assertEqual([record["column"] for record in records], [
            "name", "_expression",
        ])
        self.assertEqual(records[0]["relation"], "EQI")
        self.assertEqual(records[0]["value"], "")
        self.assertEqual(records[1]["relation"], "in")
        self.assertEqual(records[1]["operator"], "and")

    def test_sidebar_definition_uses_the_same_card_parser(self):
        item = BeautifulSoup(
            "<element><search_view>my_assets</search_view></element>",
            "html.parser",
        ).element
        definition = BeautifulSoup(SEARCH_CONFIG, "html.parser")
        views = SimpleNamespace(
            get_view=lambda search_type, view, bs=False: definition,
        )
        project = SimpleNamespace(get_config_views=lambda: views)

        records = NavigationMixinRecords.item_records(
            project, item, "demo/assets",
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["column"], "name")
        self.assertEqual(records[1]["column"], "_expression")

    def test_repeated_sidebar_click_rebuilds_runtime_tabs(self):
        records = records_from_config(SEARCH_CONFIG)
        entry = NavigationEntry(
            key="demo/assets@my_assets",
            title="My Assets",
            glyph="sobject",
            group="",
            command="open_sidebar_item",
            search_type="demo/assets",
            search_view="my_assets",
            view_mode="tiles",
            filter_records=tuple(records),
        )
        controller = _SidebarHarness(entry)
        section = controller._reset_sidebar_section(entry.key, entry.title)
        section.tabs.append(SearchTabSession("user-tab", "Temporary"))

        reset = controller._reset_sidebar_section(entry.key, entry.title)

        self.assertEqual(controller.preset_requests, 2)
        self.assertEqual(len(reset.tabs), 1)
        self.assertEqual(reset.tabs[0].tab_kind, "base")
        self.assertEqual(reset.tabs[0].filter_records, records)
        self.assertEqual(reset.tabs[0].view_mode, "tiles")
        self.assertEqual(
            reset.tabs[0].extra_filters,
            [("_expression", "in", "@SOBJECT(sthpw/task['assigned', '$LOGIN'])")],
        )
        self.assertEqual(reset.base_filters, ())

    def test_sidebar_preset_namespace_is_the_complete_customized_key(self):
        records = records_from_config(SEARCH_CONFIG)
        entry = NavigationEntry(
            key="demo/assets@archive_assets",
            title="Archive",
            glyph="sobject",
            group="",
            command="open_sidebar_item",
            search_type="demo/assets",
            search_view="archive_assets",
            filter_records=tuple(records),
        )
        controller = _SidebarHarness(entry)
        section = controller._create_section(entry.key, entry.title)

        self.assertEqual(
            controller._sidebar_preset_tab_name(section),
            "demo/assets@archive_assets",
        )

    def test_sibling_sidebar_presets_are_not_mixed(self):
        rows = [
            {
                "code": "ARCHIVE",
                "view": "link_search:archive:demo/assets@archive_assets",
                "title": "Archive",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "PROGRESS",
                "view": "link_search:progress:demo/assets@in_progress",
                "title": "In progress",
                "config": SEARCH_CONFIG,
            },
        ]

        presets = presets_from_rows(rows, "demo/assets@archive_assets")

        self.assertEqual([preset["code"] for preset in presets], ["ARCHIVE"])

    def test_saved_search_picker_rejects_a_different_namespace(self):
        rows = [
            {
                "code": "CURRENT",
                "view": "link_search:current:demo/assets@archive_assets",
                "title": "Current",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "EARLIER_MODERN",
                "view": "link_search:earlier:assets",
                "title": "Earlier modern",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "SIBLING",
                "view": "link_search:sibling:demo/assets@in_progress",
                "title": "Sibling",
                "config": SEARCH_CONFIG,
            },
        ]

        presets = presets_from_rows(rows, "demo/assets@archive_assets")

        self.assertEqual(
            [preset["code"] for preset in presets],
            ["CURRENT"],
        )

    def test_saved_search_picker_is_not_a_search_type_library(self):
        rows = [
            {
                "code": "ARCHIVE",
                "view": "link_search:archive:demo/assets@archive_assets",
                "title": "Archive",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "PROGRESS",
                "view": "link_search:progress:demo/assets@in_progress",
                "title": "In progress",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "NOT_SEARCH",
                "view": "edit_definition:demo/assets",
                "title": "Not a saved search",
                "config": SEARCH_CONFIG,
            },
        ]

        presets = presets_from_rows(rows, "demo/assets@archive_assets")

        self.assertEqual(
            [preset["code"] for preset in presets],
            ["ARCHIVE"],
        )

    def test_plain_search_type_picker_sees_every_saved_search(self):
        rows = [
            {
                "code": "PLAIN",
                "view": "link_search:plain:demo/assets",
                "title": "Plain",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "ARCHIVE",
                "view": "link_search:archive:demo/assets@archive_assets",
                "title": "Archive",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "PROGRESS",
                "view": "link_search:progress:demo/assets@in_progress",
                "title": "In progress",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "SERVICE",
                "view": "edit_definition:demo/assets",
                "title": "Service view",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "TACTIC_NATIVE",
                "view": "link_search:native:planner_view",
                "title": "TACTIC native search",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "TACTIC_SHORT",
                "view": "link_search:native_without_namespace",
                "title": "TACTIC native short search",
                "config": SEARCH_CONFIG,
            },
        ]

        presets = presets_from_rows(rows, search_type="demo/assets")

        self.assertEqual(
            [preset["code"] for preset in presets],
            ["PLAIN", "ARCHIVE", "PROGRESS"],
        )

    def test_scoped_picker_does_not_include_plain_presets(self):
        rows = [
            {
                "code": "PLAIN",
                "view": "link_search:plain:demo/assets",
                "title": "Plain",
                "config": SEARCH_CONFIG,
            },
            {
                "code": "ARCHIVE",
                "view": "link_search:archive:demo/assets@archive_assets",
                "title": "Archive",
                "config": SEARCH_CONFIG,
            },
        ]

        presets = presets_from_rows(
            rows,
            "demo/assets@archive_assets",
            "demo/assets",
        )

        self.assertEqual(
            [preset["code"] for preset in presets],
            ["ARCHIVE"],
        )

    def test_saved_search_query_matches_the_original_filters(self):
        import thlib.tactic_classes as tc
        from modern_ui.search_presets import query_search_presets

        class Server:
            def __init__(self):
                self.filters = None

            def query(self, _search_type, filters, _columns):
                self.filters = filters
                return []

        server = Server()
        original_server_start = tc.server_start
        tc.server_start = lambda **_kwargs: server
        try:
            query_search_presets(
                "demo",
                "demo/assets?project=demo",
                "demo/assets@archive_assets",
            )
        finally:
            tc.server_start = original_server_start

        self.assertIn(("search_type", "demo/assets"), server.filters)
        self.assertIn(
            ("view", "like", "%demo/assets@archive_assets"),
            server.filters,
        )
        self.assertNotIn(("category", "search_filter"), server.filters)

    def test_plain_search_query_does_not_restrict_the_view_namespace(self):
        import thlib.tactic_classes as tc
        from modern_ui.search_presets import query_search_presets

        class Server:
            def __init__(self):
                self.filters = None

            def query(self, _search_type, filters, _columns):
                self.filters = filters
                return []

        server = Server()
        original_server_start = tc.server_start
        tc.server_start = lambda **_kwargs: server
        try:
            query_search_presets("demo", "demo/assets")
        finally:
            tc.server_start = original_server_start

        self.assertEqual(server.filters, [("search_type", "demo/assets")])

    def test_saved_searches_are_added_as_real_result_tabs(self):
        entry = NavigationEntry(
            key="demo/assets@my_assets",
            title="My Assets",
            glyph="sobject",
            group="",
            command="open_sidebar_item",
            search_type="demo/assets",
        )
        controller = _SidebarHarness(entry)
        section = controller._create_section(entry.key, entry.title)
        controller._current_section_key = entry.key
        controller._sidebar_preset_requests = {entry.key: "request"}

        controller._sidebar_presets_ready((
            entry.key,
            "request",
            [{
                "code": "WIDGET_CONFIG0001",
                "title": "Archived Assets",
                "records": records_from_config(SEARCH_CONFIG),
            }],
        ))

        self.assertEqual(len(section.tabs), 2)
        self.assertEqual(section.tabs[1].tab_kind, "preset")
        self.assertEqual(section.tabs[1].title, "Archived Assets")
        self.assertGreater(controller.sync_count, 0)


class NavigationMixinRecords:
    """Expose the model parser without constructing a Qt model."""

    from modern_ui.models import NavigationModel

    item_records = staticmethod(NavigationModel._item_filter_records)


if __name__ == "__main__":
    unittest.main()
