import unittest

from thlib.ui.search_links import (
    build_saved_search_link,
    parse_saved_search_link,
)


class SavedSearchLinkTests(unittest.TestCase):
    def test_round_trip_preserves_project_search_type_and_view(self):
        value = build_saved_search_link(
            "niki_friends",
            "dolly3d/assets",
            "link_search:мои_ассеты:dolly3d/assets",
        )

        self.assertTrue(value.startswith("tactic-search://open?"))
        self.assertEqual(parse_saved_search_link(value), {
            "project": "niki_friends",
            "search_type": "dolly3d/assets",
            "view": "link_search:мои_ассеты:dolly3d/assets",
        })

    def test_incomplete_or_unrelated_links_are_rejected(self):
        self.assertIsNone(parse_saved_search_link("skey://demo/asset?code=A"))
        self.assertIsNone(parse_saved_search_link(
            "tactic-search://open?project=demo&search_type=demo%2Fasset"
        ))


if __name__ == "__main__":
    unittest.main()
