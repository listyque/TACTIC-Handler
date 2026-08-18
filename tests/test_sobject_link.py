from __future__ import annotations

from collections import OrderedDict
import unittest
from unittest.mock import Mock, patch

from modern_ui.sobject_link import (
    LinkObjectModel,
    SObjectLinkController,
    configured_instance_relation,
)


class _Project:
    def __init__(self, code="demo"):
        self._code = code

    def get_code(self):
        return self._code


class _Schema:
    def __init__(self, path="assets_in_episode"):
        self.path = path
        self.calls = []

    def get_parent_instance(self, instance_type, target_code):
        self.calls.append((instance_type, target_code))
        return {"path": self.path}


class _Stype:
    def __init__(self, code, project="demo", schema=None, title=None):
        self._code = code
        self._project = _Project(project)
        self._schema = schema or _Schema()
        self._title = title or code
        self.info = {"title": self._title}

    def get_code(self):
        return self._code

    def get_project(self):
        return self._project

    def get_schema(self):
        return self._schema

    def get_pretty_name(self):
        return self._title

    def get_stype_color(self, fmt=None):
        assert fmt == "hex"
        return "#445566"


class _SObject:
    def __init__(self, code, stype=None, title=None):
        self.code = code
        self._stype = stype
        self._title = title or code
        self.related_calls = []

    def get_search_key(self):
        return "skey://demo/item?code={}".format(self.code)

    def get_title(self):
        return self._title

    def get_code(self):
        return self.code

    def get_stype(self):
        return self._stype

    def get_info(self):
        return {"code": self.code, "name": self._title}

    def get_all_processes(self):
        return {}

    def get_related_sobjects(self, **kwargs):
        self.related_calls.append(dict(kwargs))
        return []


def _context(*, relationship="instance", instance_type="asset_in_episode",
             target_project="demo", path="assets_in_episode"):
    schema = _Schema(path)
    target = _Stype("demo/asset", target_project, schema, "Assets")
    parent_stype = _Stype("demo/episode", "demo", _Schema(), "Episodes")
    parent = _SObject("EPISODE001", parent_stype, "Episode 1")
    return {
        "stype": target,
        "parent_sobject": parent,
        "project_code": "demo",
        "relation": {
            "relationship": relationship,
            "instance_type": instance_type,
        },
    }, schema, parent


def _ready_controller(initial=(), available=()):
    context, _schema, _parent = _context()
    controller = SObjectLinkController(lambda: context)
    controller._reset()
    controller._context_data = controller._validated_context(context)
    controller._linked = OrderedDict(
        (item.get_search_key(), item) for item in initial
    )
    controller._initial_keys = set(controller._linked)
    controller._available = OrderedDict(
        (item.get_search_key(), item) for item in available
    )
    controller._sync_models()
    return controller


class LinkObjectModelTests(unittest.TestCase):
    def test_role_and_extended_selection_contract(self):
        model = LinkObjectModel()
        model.replace([
            {"searchKey": "A", "title": "A", "selected": False},
            {"searchKey": "B", "title": "B", "selected": False},
            {"searchKey": "C", "title": "C", "selected": False},
        ])

        self.assertEqual(model.roleNames()[model.SearchKeyRole], b"searchKey")
        self.assertEqual(model.roleNames()[model.PreviewUrlRole], b"previewUrl")
        self.assertEqual(model.roleNames()[model.SelectedRole], b"selected")
        self.assertTrue(model.toggle(0, additive=False))
        self.assertTrue(model.toggle(2, additive=True))
        self.assertEqual(model.selected_keys(), ["A", "C"])
        self.assertEqual(model.selected_count, 2)
        model.clear_selection()
        self.assertEqual(model.selected_keys(), [])


class SObjectLinkControllerTests(unittest.TestCase):
    def test_unconfigured_instance_relation_is_not_linkable(self):
        class MissingInstanceSchema:
            @staticmethod
            def get_parent_instance(_instance_type, _target_code):
                return None

        stype = _Stype("demo/asset", schema=MissingInstanceSchema())
        relation = {
            "relationship": "instance",
            "instance_type": "asset_in_episode",
        }

        self.assertIsNone(configured_instance_relation(relation, stype))

    def test_validation_accepts_only_configured_instance_relation_and_derives_path(self):
        context, schema, _parent = _context(path="episode_assets")

        validated = SObjectLinkController._validated_context(context)

        self.assertEqual(schema.calls, [("asset_in_episode", "demo/asset")])
        self.assertEqual(validated["path"], "episode_assets")
        self.assertEqual(validated["instance_type"], "asset_in_episode")
        self.assertEqual(validated["parent_key"],
                         "skey://demo/item?code=EPISODE001")
        self.assertEqual(validated["search_type"], "demo/asset")
        self.assertIs(validated["parent_stype"], context["parent_sobject"].get_stype())

        bad_relationship, _schema, _parent = _context(relationship="search")
        with self.assertRaisesRegex(ValueError, "instance relations only"):
            SObjectLinkController._validated_context(bad_relationship)

        missing_type, _schema, _parent = _context(instance_type="")
        with self.assertRaisesRegex(ValueError, "no instance type"):
            SObjectLinkController._validated_context(missing_type)

        wrong_project, _schema, _parent = _context(target_project="other")
        with self.assertRaisesRegex(ValueError, "another project"):
            SObjectLinkController._validated_context(wrong_project)

    def test_linked_load_uses_native_related_sobjects_contract(self):
        context, _schema, parent = _context()
        controller = SObjectLinkController(lambda: context)
        controller._reset()
        controller._context_data = controller._validated_context(context)

        def run_immediately(operation, result_handler, failure_handler=None):
            result_handler(operation())

        with patch.object(controller, "_start_worker", side_effect=run_immediately):
            controller._load_linked()

        self.assertEqual(parent.related_calls, [{
            "child_stype": context["stype"],
            "parent_stype": parent.get_stype(),
            "path": "child",
            "get_all_snapshots": False,
        }])

    def test_multi_add_then_multi_remove_back_cancels_staged_delta(self):
        linked = _SObject("A")
        candidate_b = _SObject("B")
        candidate_c = _SObject("C")
        controller = _ready_controller([linked], [candidate_b, candidate_c])

        controller.select_available(0, False)
        controller.select_available(1, True)
        self.assertEqual(controller.selected_count, 2)
        controller.transfer_selected()

        self.assertEqual(set(controller._linked), {
            linked.get_search_key(), candidate_b.get_search_key(),
            candidate_c.get_search_key(),
        })
        self.assertTrue(controller.dirty)

        controller.select_linked(1, False)
        controller.select_linked(2, True)
        self.assertEqual(controller.transfer_direction, "remove")
        self.assertEqual(controller.selected_count, 2)
        controller.transfer_selected()

        self.assertEqual(list(controller._linked), [linked.get_search_key()])
        self.assertFalse(controller.dirty)

    def test_save_computes_deterministic_delta_and_calls_native_mutation_once(self):
        initial_a = _SObject("A")
        retained_b = _SObject("B")
        inserted_c = _SObject("C")
        controller = _ready_controller([initial_a, retained_b], [inserted_c])
        controller._remove_keys([initial_a.get_search_key()])
        controller._add_keys([inserted_c.get_search_key()])
        self.assertTrue(controller.dirty)
        native_result = Mock()

        def run_immediately(operation, result_handler, failure_handler=None):
            result_handler(operation())

        with patch("thlib.tactic_classes.edit_multiple_instance_sobjects",
                   return_value=native_result) as mutate:
            with patch.object(controller, "_start_worker",
                              side_effect=run_immediately):
                controller.save()

        mutate.assert_called_once_with(
            "demo",
            insert_search_keys=[inserted_c.get_search_key()],
            exclude_search_keys=[initial_a.get_search_key()],
            parent_key="skey://demo/item?code=EPISODE001",
            instance_type="asset_in_episode",
            path="assets_in_episode",
        )
        self.assertFalse(controller.dirty)
        self.assertFalse(controller.busy)
        self.assertEqual(controller._initial_keys, set(controller._linked))

    def test_available_results_are_paged_and_never_duplicate_linked_objects(self):
        linked_a = _SObject("A")
        candidate_b = _SObject("B")
        candidate_c = _SObject("C")
        candidate_d = _SObject("D")
        candidate_e = _SObject("E")
        controller = _ready_controller([linked_a], [])
        session = controller._session_token

        controller._loading_available = True
        controller._available_loaded(
            session, 1, "", 0, False,
            ([linked_a, candidate_b], {"total_sobjects_count": 5}),
        )
        self.assertEqual(list(controller._available), [candidate_b.get_search_key()])
        self.assertEqual(controller._available_offset, 2)
        self.assertEqual(controller.available_total, 5)
        self.assertTrue(controller.can_load_more)

        controller._loading_available = True
        controller._available_loaded(
            session, 2, "", 2, True,
            ([candidate_c, candidate_d], {"total_sobjects_query_count": 5}),
        )
        self.assertEqual(list(controller._available), [
            candidate_b.get_search_key(), candidate_c.get_search_key(),
            candidate_d.get_search_key(),
        ])
        self.assertEqual(controller._available_offset, 4)
        self.assertTrue(controller.can_load_more)

        controller._loading_available = True
        controller._available_loaded(
            session, 3, "", 4, True,
            ([candidate_e], {"total_sobjects_count": 5}),
        )
        self.assertEqual(controller._available_offset, 5)
        self.assertFalse(controller.can_load_more)
        self.assertEqual(controller.available_model.count, 4)

    def test_stale_result_is_ignored_and_server_failure_keeps_staged_state(self):
        linked_a = _SObject("A")
        candidate_b = _SObject("B")
        controller = _ready_controller([linked_a], [candidate_b])
        controller._add_keys([candidate_b.get_search_key()])
        before = list(controller._linked)
        self.assertTrue(controller.dirty)

        controller._available_loaded(
            "stale-session", 99, "", 0, False,
            ([_SObject("STALE")], {"total_sobjects_count": 1}),
        )
        self.assertEqual(list(controller._linked), before)

        controller._busy = True
        controller._save_failed(
            controller._session_token,
            ({"exception": "TACTIC unavailable"},),
        )
        self.assertEqual(list(controller._linked), before)
        self.assertTrue(controller.dirty)
        self.assertFalse(controller.busy)
        self.assertEqual(controller.error, "TACTIC unavailable")

    def test_failed_available_request_still_runs_latest_queued_search(self):
        controller = _ready_controller([], [])
        controller._loading_available = True
        controller._available_query = "older"
        controller._pending_available_query = "latest"

        with patch.object(controller, "_load_available") as load:
            controller._available_failed(
                controller._session_token,
                1,
                ({"exception": "temporary failure"},),
            )

        self.assertEqual(controller._available_query, "latest")
        self.assertIsNone(controller._pending_available_query)
        load.assert_called_once_with(0, append=False)


if __name__ == "__main__":
    unittest.main()
