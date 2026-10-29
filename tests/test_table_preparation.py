"""Table preparation keeps cache ownership and resolves metadata per batch."""

import copy
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests.qt_application import gui_test_application
from tests.test_workspace_info_items import _SType
from thlib import server_cache
from thlib import tactic_classes as tc
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


class _CopyProbe:
    def __init__(self, copies):
        self.copies = copies

    def __deepcopy__(self, memo):
        self.copies.append(1)
        return _CopyProbe(self.copies)


class TablePreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        for context in (
            patch.object(tc.env_mode, "current_path", directory.name),
            patch.object(tc.env_inst, "projects", {
                "demo": SimpleNamespace(get_code=lambda: "demo"),
            }),
        ):
            context.start()
            self.addCleanup(context.stop)

    @staticmethod
    def payload():
        return {
            "sobjects_list": [{
                "__search_key__": "demo/asset?project=demo&code=A1",
                "code": "A1", "name": "Asset", "status": "ready",
                "__snapshots__": [{
                    "__search_key__": "sthpw/snapshot?code=S1",
                    "code": "S1", "process": "publish", "context": "publish",
                    "version": -1, "snapshot": "<snapshot/>",
                    "__files__": [{
                        "code": "F1", "type": "main",
                        "metadata": {"tag": "original"},
                    }],
                }],
                "__task_details_by_process__": {
                    "publish": [{"code": "T1", "assigned": "artist"}],
                },
                "__tasks_count__": 1,
                "__tasks_count_by_process__": {"publish": 1},
                "__notes_count_by_process__": {"publish": 2},
            }],
            "total_sobjects_count": 1, "limit": 20, "offset": 0,
        }

    def test_receive_copies_once_and_hydrations_do_not_mutate_the_cache(self):
        payload = self.payload()
        expected = copy.deepcopy(payload)
        copies = []
        payload["copy_probe"] = _CopyProbe(copies)
        with (
            patch.object(
                tc, "_execute_read_only_procedure_serverside", return_value=payload,
            ),
            patch.object(server_cache, "token", return_value="revision-1"),
        ):
            (objects, counts), raw = tc.get_sobjects(
                "demo/asset?project=demo", project_code="demo", return_payload=True,
            )
            self.assertEqual(len(copies), 1)
            self.assertIs(raw, payload)
            cached_objects, _ = tc.hydrate_sobjects_payload(raw, "demo")
        first = next(iter(objects.values()))
        second = next(iter(cached_objects.values()))
        first.get_info()["name"] = "Edited"
        snapshot = (
            first.process["publish"].get_contexts()["publish"]
            .get_versionless()["S1"]
        )
        snapshot.get_files()["main"][0]["metadata"]["tag"] = "edited"
        first.get_task_summaries("publish")[0]["assigned"] = "other"
        self.assertEqual(second.get_info()["name"], "Asset")
        other_snapshot = (
            second.process["publish"].get_contexts()["publish"]
            .get_versionless()["S1"]
        )
        self.assertEqual(
            other_snapshot.get_files()["main"][0]["metadata"]["tag"], "original",
        )
        self.assertEqual(
            second.get_task_summaries("publish")[0]["assigned"], "artist",
        )
        self.assertEqual(second.get_tasks_count("publish"), 1)
        self.assertEqual(second.get_notes_count("publish"), 2)
        self.assertEqual(counts["total_sobjects_count"], 1)
        self.assertEqual(
            {k: v for k, v in raw.items() if k != "copy_probe"}, expected,
        )

    def test_snapshot_revision_is_read_once_per_batch_and_refreshed_next_time(self):
        payload = self.payload()
        original = payload["sobjects_list"][0]
        payload["sobjects_list"] = [copy.deepcopy(original) for _ in range(4)]
        for index, record in enumerate(payload["sobjects_list"]):
            record["__search_key__"] += str(index)
        with patch.object(server_cache, "token", return_value="R1") as token:
            first, _ = tc.hydrate_sobjects_payload(payload, "demo")
            token.assert_called_once_with("snapshots", "demo")
            token.return_value = "R2"
            second, _ = tc.hydrate_sobjects_payload(payload, "demo")
            self.assertEqual(token.call_count, 2)
        self.assertEqual(
            {item._snapshot_cache_token for item in first.values()}, {"R1"},
        )
        self.assertEqual(
            {item._snapshot_cache_token for item in second.values()}, {"R2"},
        )
        with patch.object(server_cache, "token") as token:
            tc.hydrate_sobjects_payload(payload, "demo", include_snapshots=False)
            tc.hydrate_sobjects_payload({"sobjects_list": []}, "demo")
            token.assert_not_called()

    def objects(self):
        return [tc.SObject({
            "__search_key__": f"demo/asset?project=demo&code=A{index}",
            "code": f"A{index}", "name": f"Asset {index}", "status": "ready",
        }, tc.env_inst.projects["demo"]) for index in range(4)]

    def test_roots_and_field_updates_resolve_definitions_once_per_batch(self):
        stype = _SType()
        model = WorkspaceItemModel()
        objects = self.objects()
        model.replace_sobjects(objects, stype)
        self.assertEqual(len(stype.calls), 3)
        self.assertEqual(
            [node.chips[0]["text"] for node in model._roots],
            ["Ready for review"] * 4,
        )
        stype.calls.clear()
        model.update_item_fields({
            item.get_search_key(): {"status": "hold"} for item in objects
        })
        self.assertEqual(len(stype.calls), 3)
        self.assertEqual(
            [node.chips[0]["text"] for node in model._roots], ["On hold"] * 4,
        )
        # An edited definition must be re-read by the next projection.
        with patch.object(stype, "get_definition", return_value=[]):
            model.replace_sobjects(objects, stype)
        self.assertTrue(all(node.chips == [] for node in model._roots))

    def test_relation_rows_share_the_child_type_metadata(self):
        stype = _SType()
        stype.get_stype_color = lambda **kwargs: "#607d8b"
        source = Mock()
        source.get_related_sobjects.return_value = self.objects()
        parent = WorkspaceNode(
            node_id="related", node_type="relation", source=source,
            search_key="", code="", title="Related",
            relation={"stype": stype, "definition": {"from": "demo/asset"}},
        )
        model = WorkspaceItemModel()
        model._load_relation(parent, register=False)
        self.assertEqual(len(stype.calls), 3)
        self.assertEqual(len(parent.children), 4)
        self.assertEqual(
            [child.chips[0]["text"] for child in parent.children],
            ["Ready for review"] * 4,
        )


if __name__ == "__main__":
    unittest.main()
