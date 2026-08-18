import unittest

from modern_ui.controllers.search_suggestions import SearchSuggestionsMixin
from modern_ui.controllers.types import SearchTabSession, SectionSession
from modern_ui.models import NavigationEntry, NavigationModel
from modern_ui.search_contract import records_from_filters


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


if __name__ == "__main__":
    unittest.main()
