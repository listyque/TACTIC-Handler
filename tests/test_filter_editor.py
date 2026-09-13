from __future__ import annotations

import unittest
from unittest.mock import patch

from thlib.ui.filter_editor import FilterEditorController


class FilterEditorControllerTests(unittest.TestCase):
    def make_controller(
        self,
        source,
        applied,
        notifications,
        staged=None,
        context_updates=None,
    ):
        context = {
            "project_code": "demo",
            "search_type": "demo/asset",
            "tab_id": "assets-tab",
            "tab_name": "demo/asset@assets",
            "preset_scope": "demo/asset@assets",
            "preset_namespace": "demo/asset@assets",
            "tab_title": "Assets",
        }
        context.update(context_updates or {})
        controller = FilterEditorController(
            lambda: source,
            lambda: [
                {"label": "Name", "value": "name", "dataType": "text"},
                {"label": "Code", "value": "code", "dataType": "text"},
            ],
            lambda _column: [{"label": "Contains", "value": "EQI"}],
            notifications.append,
            lambda: True,
            lambda: context,
            (
                lambda records, title: staged.append((records, title))
                if staged is not None else None
            ),
        )
        controller._context_key = controller._key(context)
        return controller

    def test_preset_name_preserves_non_latin_titles(self):
        self.assertEqual(
            FilterEditorController._preset_name(
                "\u041c\u043e\u0438 \u0430\u0441\u0441\u0435\u0442\u044b"
            ),
            "\u043c\u043e\u0438_\u0430\u0441\u0441\u0435\u0442\u044b",
        )

    def test_preset_name_is_generated_from_the_readable_title(self):
        self.assertEqual(
            FilterEditorController._preset_name("Ready for Review"),
            "ready_for_review",
        )

    def test_new_preset_uses_the_exact_search_view_namespace(self):
        controller = self.make_controller([], [], [])
        controller._validate = lambda: True
        captured = []
        controller._preset_data = lambda title, view: captured.append(
            (title, view)
        ) or {}
        controller._run_server = lambda _callback, _handler: None

        controller._save_preset("Ready for Review")

        self.assertEqual(captured, [(
            "Ready for Review",
            "link_search:ready_for_review:demo/asset@assets",
        )])

    def test_plain_tab_saves_new_presets_under_the_search_type(self):
        controller = self.make_controller(
            [], [], [],
            context_updates={
                "preset_scope": "",
                "preset_namespace": "demo/asset",
            },
        )
        controller._validate = lambda: True
        captured = []
        controller._preset_data = lambda title, view: captured.append(
            (title, view)
        ) or {}
        controller._run_server = lambda _callback, _handler: None

        controller._save_preset("General Search")

        self.assertEqual(captured, [(
            "General Search",
            "link_search:general_search:demo/asset",
        )])

    def test_search_type_library_is_independent_from_the_tab_scope(self):
        controller = self.make_controller([], [], [])
        scoped_context = controller._current_context()
        scoped_key = controller._key(scoped_context)

        controller.prepare_search_type_library(
            "link_search:general:demo/asset"
        )
        library_context = controller._current_context()
        library_key = controller._key(library_context)

        self.assertEqual(
            scoped_context["preset_scope"],
            "demo/asset@assets",
        )
        self.assertEqual(library_context["preset_scope"], "")
        self.assertEqual(
            library_context["preset_namespace"],
            "demo/asset",
        )
        self.assertNotEqual(scoped_key, library_key)

        controller._context_key = library_key
        controller.presets.replace([{
            "code": "GENERAL",
            "title": "General",
            "view": "link_search:general:demo/asset",
            "records": [],
        }])
        controller._presets_loaded(([], scoped_key))

        self.assertEqual(controller.presets._records[0]["code"], "GENERAL")

        restored = []
        controller._begin_session = lambda: restored.append(
            controller._current_context()["preset_scope"]
        )
        controller.end_search_type_library()
        self.assertEqual(
            controller._current_context()["preset_scope"],
            "demo/asset@assets",
        )
        self.assertEqual(restored, [])
        controller.sync_search_session()
        self.assertEqual(restored, ["demo/asset@assets"])

    def test_advanced_search_does_not_restore_a_stale_preset(self):
        controller = self.make_controller([], [], [])
        controller.load_presets = lambda: None

        controller.begin_search_session()

        self.assertFalse(controller._restore_saved_selection)
        self.assertEqual(controller.selected_preset, -1)

    def test_search_session_sync_waits_for_a_real_context(self):
        context = {}
        controller = FilterEditorController(
            lambda: [],
            lambda: [
                {"label": "Name", "value": "name", "dataType": "text"},
            ],
            lambda _column: [{"label": "Contains", "value": "EQI"}],
            lambda _message: None,
            lambda: True,
            lambda: context,
        )
        loaded = []
        controller.load_presets = lambda: loaded.append(
            controller._context_key
        )

        controller.sync_search_session()
        context.update({
            "project_code": "niki_friends",
            "search_type": "dolly3d/assets",
            "tab_id": "assets-tab",
            "tab_title": "Assets",
        })
        controller.sync_search_session()
        controller.sync_search_session()

        self.assertEqual(len(loaded), 2)
        self.assertEqual(
            loaded[-1],
            ("niki_friends", "dolly3d/assets", "assets-tab", ""),
        )

    def test_update_from_advanced_search_captures_live_records(self):
        source = [{
            "column": "code",
            "relation": "EQI",
            "value": "ASSET",
            "rowEnabled": True,
            "operator": "begin",
            "isDefault": True,
        }]
        controller = self.make_controller(source, [], [])
        controller.presets.replace([{
            "code": "WIDGET_CONFIG00001",
            "title": "My assets",
            "view": "link_search:my_assets:assets",
            "records": [],
        }])
        controller._selected_preset = 0
        saved = []
        controller._save_preset = lambda title, view="": saved.append(
            (title, view, [dict(row) for row in controller.model._records])
        )

        controller.update_selected_from_current_search()

        self.assertEqual(saved[0][0], "My assets")
        self.assertEqual(saved[0][1], "link_search:my_assets:assets")
        self.assertEqual(saved[0][2][0]["column"], "code")
        self.assertEqual(saved[0][2][0]["value"], "ASSET")

    def test_selecting_saved_search_stages_its_records(self):
        applied = []
        staged = []
        controller = self.make_controller([], applied, [], staged)
        controller.presets.replace([{
            "code": "WIDGET_CONFIG00002",
            "title": "Published",
            "view": "link_search:published:assets",
            "records": [{
                "column": "status",
                "relation": "EQI",
                "value": "Published",
                "rowEnabled": True,
                "operator": "begin",
                "isDefault": True,
            }],
        }])

        controller.select_preset_for_current_search(0)

        self.assertEqual(applied, [])
        self.assertEqual(staged[0][1], "Published")
        self.assertEqual(staged[0][0][0]["column"], "status")
        self.assertEqual(staged[0][0][0]["value"], "Published")

    def test_selected_saved_search_copies_stable_deep_link(self):
        notifications = []
        controller = self.make_controller([], [], notifications)
        controller.presets.replace([{
            "code": "WIDGET_CONFIG00002",
            "title": "Published",
            "view": "link_search:published:demo/asset@assets",
            "records": [],
        }])
        controller._selected_preset = 0

        with patch("PySide6.QtGui.QGuiApplication.clipboard") as clipboard:
            controller.copy_selected_search_link()

        copied = clipboard.return_value.setText.call_args.args[0]
        self.assertEqual(copied, (
            "tactic-search://open?project=demo&"
            "search_type=demo%2Fasset&"
            "view=link_search%3Apublished%3Ademo%2Fasset%40assets"
        ))
        self.assertEqual(notifications[-1], "Saved search link copied")

    def test_legacy_relation_names_are_unpacked_to_server_codes(self):
        config = (
            '<config><filter><values type="json">'
            '[{"prefix":"main_body","main_body_enabled":"on",'
            '"main_body_column":"name",'
            '"main_body_relation":"contains",'
            '"main_body_value":"tree"}]'
            '</values></filter></config>'
        )

        records = FilterEditorController._records_from_config(config)

        self.assertEqual(records[0]["relation"], "EQI")

    def test_legacy_blank_conditions_are_preserved(self):
        config = (
            '<config><filter><values type="json">'
            '[{"prefix":"filter_mode","filter_mode":"and"},'
            '{"prefix":"main_body","main_body_enabled":"on",'
            '"main_body_column":"name",'
            '"main_body_relation":"contains",'
            '"main_body_value":""},'
            '{"prefix":"main_body","main_body_enabled":"on",'
            '"main_body_column":"_expression",'
            '"main_body_relation":"expression","main_body_op":"in",'
            '"main_body_value":"@SOBJECT(sthpw/task)"},'
            '{"prefix":"search_ops","ops":["and"]}]'
            '</values></filter></config>'
        )

        records = FilterEditorController._records_from_config(config)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["column"], "name")
        self.assertEqual(records[0]["value"], "")
        self.assertEqual(records[1]["column"], "_expression")

    def test_legacy_blank_name_card_is_valid_with_an_expression(self):
        source = [{
            "column": "name",
            "relation": "EQI",
            "value": "",
            "rowEnabled": True,
            "operator": "begin",
            "isDefault": True,
            "dataType": "text",
        }, {
            "column": "_expression",
            "relation": "in",
            "value": "@SOBJECT(sthpw/task)",
            "rowEnabled": True,
            "operator": "and",
            "isDefault": False,
            "dataType": "all",
        }]
        controller = self.make_controller(source, [], [])
        controller._relation_choices = lambda column: [{
            "label": "In" if column == "_expression" else "Contains",
            "value": "in" if column == "_expression" else "EQI",
        }]
        controller._replace_records(source)

        self.assertTrue(controller._validate())
        self.assertEqual(controller.validation_error, "")

    def test_archive_assets_preset_stages_both_saved_cards(self):
        config = (
            '<config><filter><values type="json">'
            '[{"prefix":"filter_mode","filter_mode":"and"},'
            '{"prefix":"main_body","main_body_enabled":"on",'
            '"filter_type":"_column","main_body_column":"name",'
            '"main_body_relation":"contains","main_body_value":""},'
            '{"prefix":"main_body","main_body_enabled":"on",'
            '"filter_type":"_column","main_body_column":"_expression",'
            '"main_body_relation":"expression","main_body_op":"in",'
            '"main_body_value":'
            '"@SOBJECT(sthpw/task[\'assigned\', \'$LOGIN\'])"},'
            '{"prefix":"search_ops","levels":[0],'
            '"ops":["and"],"modes":["child"]}]'
            '</values></filter></config>'
        )
        staged = []
        controller = self.make_controller([], [], [], staged)
        controller.presets.replace([{
            "code": "WIDGET_CONFIG00276",
            "title": "Archive assets",
            "view": "link_search:archive_assets:assets",
            "records": controller._records_from_config(config),
        }])

        controller.select_preset_for_current_search(0)

        self.assertEqual(len(staged[0][0]), 2)
        self.assertEqual(staged[0][0][0]["column"], "name")
        self.assertEqual(staged[0][0][0]["value"], "")
        self.assertEqual(staged[0][0][1]["column"], "_expression")

    def test_is_empty_condition_is_not_removed_as_placeholder(self):
        config = (
            '<config><filter><values type="json">'
            '[{"prefix":"main_body","main_body_enabled":"on",'
            '"main_body_column":"description",'
            '"main_body_relation":"is empty",'
            '"main_body_value":""}]'
            '</values></filter></config>'
        )

        records = FilterEditorController._records_from_config(config)

        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0]["relation"])


if __name__ == "__main__":
    unittest.main()
