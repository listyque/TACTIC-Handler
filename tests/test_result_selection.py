from __future__ import annotations

from types import SimpleNamespace
import unittest

from PySide6.QtCore import Qt

from thlib.ui.controllers.selection import SelectionMixin
from thlib.ui.workspace_models.results_types import WorkspaceNode
from thlib.ui.workspace_models.state_selection_state import (
    SelectionStateMixin,
)


class _Signal:
    def __init__(self):
        self.count = 0

    def emit(self, *_args):
        self.count += 1


class _RecordModel:
    def __init__(self, records=None):
        self._records = [dict(record) for record in (records or [])]

    def records(self):
        return [dict(record) for record in self._records]

    def replace(self, records):
        self._records = [dict(record) for record in records]


class _SelectionStateHarness(SelectionStateMixin):
    def __init__(self):
        self._selected_sobject = object()
        self._task_sobjects = ["task"]
        self._note_sobjects = ["note"]
        self._notes_process = "publish"
        self._notes_loaded = True
        self._selected_title = "Asset"
        self._description = "Description"
        self._description_original = "Description"
        self._description_editing = False
        self._description_pinned = True
        self._description_saving = False
        self._description_error = ""
        self._description_target = object()
        self._description_target_key = "demo/asset?code=ASSET001"
        self._description_target_kind = "sobject"
        self._description_target_title = "Asset"
        self._snapshot_file_objects = {"file": object()}
        self.snapshot_model = _RecordModel([{"title": "Snapshot"}])
        self.snapshot_preview_model = _RecordModel([{"title": "Preview"}])
        self.snapshot_file_model = _RecordModel([{"title": "File"}])
        self.task_model = _RecordModel([{"title": "Task"}])
        self.task_status_model = _RecordModel([{"title": "Ready"}])
        self.note_model = _RecordModel([{"title": "Note"}])
        self.selection_changed = _Signal()
        self.description_changed = _Signal()
        self.description_editor_changed = _Signal()


class _Timer:
    def __init__(self):
        self.started = 0

    def start(self):
        self.started += 1


class _SelectionHarness(SelectionMixin):
    def __init__(self, nodes):
        self.workspace_model = SimpleNamespace(
            _items=list(nodes),
            node_for=lambda node_id: next(
                (node for node in nodes if node.node_id == node_id), None
            ),
            row_for_node=lambda node_id: next(
                (
                    index
                    for index, node in enumerate(nodes)
                    if node.node_id == node_id
                ),
                -1,
            ),
        )
        self.tab = SimpleNamespace(
            selected_node_id="",
            selected_node_ids=[],
            selection_anchor_id="",
            clear_details=lambda: None,
        )
        self.repository_sync = SimpleNamespace(
            request_presets=lambda _source: None
        )
        self.selected_node_changed = _Signal()
        self._detail_worker = None
        self._versions_worker = None
        self._pending_versions_node_id = ""
        self._versions_request_id = ""
        self._detail_request_id = ""
        self._pending_selection_load = None
        self._selection_load_timer = _Timer()
        self.versions_model = SimpleNamespace(clear=lambda: None)
        self.dock_model = SimpleNamespace(show_panel=lambda _panel: None)

    def _current_tab(self):
        return self.tab

    def _save_search_cache(self):
        pass


def _sobject(node_id, parent_id=""):
    return WorkspaceNode(
        node_id=node_id,
        node_type="sobject",
        search_key=f"demo/asset?code={node_id}",
        code=node_id,
        title=node_id,
        parent_id=parent_id,
    )


def _relation(node_id):
    return WorkspaceNode(
        node_id=node_id,
        node_type="relation",
        search_key="",
        code="assets",
        title="Assets",
    )


class ResultSelectionTests(unittest.TestCase):
    def test_ctrl_toggling_active_row_emits_selection_without_reloading_details(self):
        controller = _SelectionHarness([_sobject("one"), _sobject("two")])
        controller.select_result_node("one", "demo/asset?code=one", "sobject")
        controller.select_result_node(
            "two", "demo/asset?code=two", "sobject", Qt.ControlModifier.value,
        )
        notifications = controller.selected_node_changed.count
        loads = controller._selection_load_timer.started

        controller.select_result_node(
            "two", "demo/asset?code=two", "sobject", Qt.ControlModifier.value,
        )

        self.assertEqual(controller.tab.selected_node_ids, ["one"])
        self.assertEqual(controller.selected_node_changed.count, notifications + 1)
        self.assertEqual(controller._selection_load_timer.started, loads)

    def test_cancelled_detail_worker_releases_selection_slot_immediately(self):
        controller = _SelectionHarness([_sobject("one")])

        class Worker:
            def __init__(self):
                self.cancelled = False

            def cancel(self):
                self.cancelled = True

        worker = Worker()
        controller._detail_worker = worker

        controller._cancel_selected_payload_worker()

        self.assertTrue(worker.cancelled)
        self.assertIsNone(controller._detail_worker)

        controller._versions_worker = worker
        worker.cancelled = False

        controller._cancel_versions_worker()

        self.assertTrue(worker.cancelled)
        self.assertIsNone(controller._versions_worker)

    def test_selection_projection_restores_prepared_detail_models(self):
        state = _SelectionStateHarness()
        selected_sobject = state._selected_sobject
        file_object = state._snapshot_file_objects["file"]
        projection = state.capture_selection_projection()
        state._selected_sobject = None
        state._selected_title = "Other"
        state._description = "Other"
        state.snapshot_model.replace([])
        state.snapshot_preview_model.replace([])
        state.snapshot_file_model.replace([])
        state.task_model.replace([])
        state.task_status_model.replace([])
        state.note_model.replace([])
        state._snapshot_file_objects.clear()

        restored = state.restore_selection_projection(projection)

        self.assertTrue(restored)
        self.assertIs(state._selected_sobject, selected_sobject)
        self.assertEqual(state._selected_title, "Asset")
        self.assertEqual(state._description, "Description")
        self.assertEqual(
            state.snapshot_model.records(), [{"title": "Snapshot"}]
        )
        self.assertEqual(state.task_model.records(), [{"title": "Task"}])
        self.assertEqual(state.note_model.records(), [{"title": "Note"}])
        self.assertIs(state._snapshot_file_objects["file"], file_object)

    def test_hidden_detail_models_publish_only_when_panel_returns(self):
        state = _SelectionStateHarness()
        state._detail_presentation_visible = True
        state._task_records_cache = state.task_model.records()
        state._task_status_records_cache = state.task_status_model.records()
        state._note_records_cache = state.note_model.records()

        state.set_detail_presentation_visible(False)
        state.replace_note_records([{"title": "Updated note"}])

        self.assertEqual(state.note_model.records(), [{"title": "Note"}])
        self.assertEqual(
            state._note_records_cache, [{"title": "Updated note"}]
        )

        state.set_detail_presentation_visible(True)

        self.assertEqual(
            state.note_model.records(), [{"title": "Updated note"}]
        )

    def test_ctrl_toggles_sibling_sobjects(self):
        nodes = [_sobject("one"), _sobject("two"), _sobject("three")]
        controller = _SelectionHarness(nodes)

        controller.select_result_node(
            "one", nodes[0].search_key, "sobject", Qt.NoModifier.value, False
        )
        controller.select_result_node(
            "three",
            nodes[2].search_key,
            "sobject",
            Qt.ControlModifier.value,
            False,
        )

        self.assertEqual(controller.tab.selected_node_ids, ["one", "three"])

    def test_shift_selects_contiguous_sobject_range(self):
        nodes = [_sobject("one"), _sobject("two"), _sobject("three")]
        controller = _SelectionHarness(nodes)

        controller.select_result_node(
            "one", nodes[0].search_key, "sobject", Qt.NoModifier.value, False
        )
        controller.select_result_node(
            "three",
            nodes[2].search_key,
            "sobject",
            Qt.ShiftModifier.value,
            False,
        )

        self.assertEqual(
            controller.tab.selected_node_ids, ["one", "two", "three"]
        )

    def test_ctrl_and_shift_select_sobjects_inside_relation_branch(self):
        relation = _relation("relation:assets")
        nodes = [
            relation,
            _sobject("one", relation.node_id),
            _sobject("two", relation.node_id),
            _sobject("three", relation.node_id),
        ]
        controller = _SelectionHarness(nodes)

        controller.select_result_node(
            "one", nodes[1].search_key, "sobject", Qt.NoModifier.value, False
        )
        controller.select_result_node(
            "two",
            nodes[2].search_key,
            "sobject",
            Qt.ControlModifier.value,
            False,
        )
        self.assertEqual(controller.tab.selected_node_ids, ["one", "two"])

        controller.select_result_node(
            "three",
            nodes[3].search_key,
            "sobject",
            Qt.ShiftModifier.value,
            False,
        )
        self.assertEqual(controller.tab.selected_node_ids, ["two", "three"])


if __name__ == "__main__":
    unittest.main()
