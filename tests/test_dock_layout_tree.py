import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QSettings

from modern_ui.menu_schema import MenuRegistry
from modern_ui.workspace_models.docks import DockPanelModel
from modern_ui.workspace_models.docks_tree import (
    DockSplit,
    DockStack,
    default_layout,
    insert_relative,
    layout_from_rectangles,
    layout_rectangles,
    panel_ids,
    stack_for_panel,
    swap_panels,
    tabify,
)


class DockLayoutTreeTests(unittest.TestCase):
    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.settings_path = Path(self._temporary_directory.name) / "settings.ini"
        self.model = DockPanelModel(
            QSettings(str(self.settings_path), QSettings.Format.IniFormat)
        )

    def tearDown(self):
        self._temporary_directory.cleanup()

    def panel(self, panel_id):
        return next(
            panel for panel in self.model._panels
            if panel.panel_id == panel_id
        )

    def test_default_tree_reproduces_the_three_column_workspace(self):
        rectangles = layout_rectangles(
            default_layout(), {
                "results", "tasks", "notes", "task_calendar", "snapshot",
            }
        )
        expected = {
            "results": (0.0000, 0.0, 0.2244, 1.0),
            "tasks": (0.2244, 0.0, 0.4356, 1.0),
            "notes": (0.6600, 0.0, 0.3400, 1.0),
            "task_calendar": (0.6600, 0.0, 0.3400, 1.0),
            "snapshot": (0.6600, 0.0, 0.3400, 1.0),
        }
        for panel_id, rectangle in expected.items():
            for actual, value in zip(rectangles[panel_id], rectangle):
                self.assertAlmostEqual(actual, value)

    def test_hidden_stack_tab_keeps_its_tree_position(self):
        self.model.close_panel("notes")
        stack = stack_for_panel(self.model._layout_root, "task_calendar")
        self.assertEqual(stack.active_panel_id, "task_calendar")
        self.assertAlmostEqual(self.panel("task_calendar").x, 0.66)
        self.assertAlmostEqual(self.panel("task_calendar").width, 0.34)

        self.model.show_panel("notes")
        stack = stack_for_panel(self.model._layout_root, "notes")
        self.assertEqual(stack.active_panel_id, "notes")
        self.assertAlmostEqual(self.panel("notes").x, 0.66)
        self.assertAlmostEqual(self.panel("notes").width, 0.34)

    def test_work_hour_surfaces_are_real_stackable_docks(self):
        ids = {panel.panel_id for panel in self.model._panels}
        self.assertTrue({
            "timesheet", "work_reports", "cost_reports"
        }.issubset(ids))
        self.model.show_panel("timesheet")
        stack = stack_for_panel(self.model._layout_root, "timesheet")
        self.assertIsNotNone(stack)
        self.assertEqual(stack.active_panel_id, "timesheet")

    def test_tabify_changes_only_the_target_stack(self):
        root = tabify(default_layout(), "tasks", "drop_plate")
        self.assertIsNotNone(root)
        self.assertIn("drop_plate", panel_ids(root))

        def find_stack(node):
            if isinstance(node, DockStack):
                return node if "tasks" in node.panel_ids else None
            self.assertIsInstance(node, DockSplit)
            return find_stack(node.first) or find_stack(node.second)

        tasks_stack = find_stack(root)
        self.assertEqual(tasks_stack.panel_ids, ("tasks", "drop_plate"))
        self.assertEqual(tasks_stack.active_panel_id, "drop_plate")

    def test_rectangles_recover_the_same_split_topology(self):
        values = {
            panel.panel_id: (panel.x, panel.y, panel.width, panel.height)
            for panel in self.model._panels
            if panel.dock_area != "floating"
        }
        root = layout_from_rectangles(values)
        self.assertEqual(set(panel_ids(root)), set(values))
        recovered = layout_rectangles(root, set(values))
        for panel_id, rectangle in values.items():
            for actual, expected in zip(recovered[panel_id], rectangle):
                self.assertAlmostEqual(actual, expected)

    def test_committed_split_ratio_survives_panel_close_and_reopen(self):
        self.model.resize_panel(
            "results", "right", 0.0, 0.0, 0.30, 1.0, 1600, 900
        )
        self.model.close_panel("snapshot")
        self.model.show_panel("snapshot")
        self.assertAlmostEqual(self.panel("results").width, 0.30)
        self.assertAlmostEqual(self.panel("tasks").x, 0.30)
        self.assertAlmostEqual(self.panel("tasks").width, 0.36)
        self.assertAlmostEqual(self.panel("snapshot").x, 0.66)

    def test_saved_geometry_restores_the_structural_split(self):
        self.model.resize_panel(
            "results", "right", 0.0, 0.0, 0.30, 1.0, 1600, 900
        )
        self.model._settings.sync()
        restored = DockPanelModel(
            QSettings(str(self.settings_path), QSettings.Format.IniFormat)
        )
        restored.close_panel("snapshot")
        restored.show_panel("snapshot")
        panel_by_id = {panel.panel_id: panel for panel in restored._panels}
        self.assertAlmostEqual(panel_by_id["results"].width, 0.30)
        self.assertAlmostEqual(panel_by_id["tasks"].x, 0.30)
        self.assertAlmostEqual(panel_by_id["snapshot"].x, 0.66)

    def test_relative_insert_splits_only_the_target_cell(self):
        root = insert_relative(
            default_layout(), "tasks", "drop_plate", "bottom"
        )
        rectangles = layout_rectangles(
            root,
            {
                "results", "tasks", "drop_plate", "notes",
                "task_calendar", "snapshot",
            },
        )
        self.assertAlmostEqual(rectangles["results"][2], 0.2244)
        self.assertAlmostEqual(rectangles["tasks"][2], 0.4356)
        self.assertAlmostEqual(rectangles["tasks"][3], 0.5)
        self.assertAlmostEqual(rectangles["drop_plate"][1], 0.5)
        self.assertAlmostEqual(rectangles["notes"][0], 0.66)

    def test_swap_exchanges_panel_cells_without_changing_ratios(self):
        root = default_layout()
        before = layout_rectangles(
            root, {"results", "tasks", "snapshot", "description"}
        )
        root = swap_panels(root, "tasks", "snapshot")
        after = layout_rectangles(
            root, {"results", "tasks", "snapshot", "description"}
        )
        self.assertEqual(after["tasks"], before["snapshot"])
        self.assertEqual(after["snapshot"], before["tasks"])
        self.assertEqual(after["results"], before["results"])
        self.assertEqual(after["description"], before["description"])

    def test_model_places_floating_panel_relative_to_target(self):
        self.model.place_panel("notes", "snapshot", "bottom")
        notes = self.panel("notes")
        snapshot = self.panel("snapshot")
        self.assertEqual(notes.dock_area, "docked")
        self.assertAlmostEqual(notes.x, snapshot.x)
        self.assertAlmostEqual(notes.y, snapshot.y + snapshot.height)
        self.assertAlmostEqual(notes.height, snapshot.height)

    def test_center_drop_creates_an_active_stack(self):
        self.model.place_panel("notes", "snapshot", "center")
        stack = stack_for_panel(self.model._layout_root, "snapshot")
        self.assertEqual(
            stack.panel_ids,
            (
                "task_calendar", "timesheet", "work_reports",
                "cost_reports", "snapshot", "description", "notes",
            ),
        )
        self.assertEqual(stack.active_panel_id, "notes")
        self.assertEqual(
            (self.panel("notes").x, self.panel("notes").y,
             self.panel("notes").width, self.panel("notes").height),
            (self.panel("snapshot").x, self.panel("snapshot").y,
             self.panel("snapshot").width, self.panel("snapshot").height),
        )

    def test_stack_activation_and_close_select_the_remaining_panel(self):
        self.model.place_panel("notes", "snapshot", "center")
        self.model.activate_stack_panel("snapshot")
        stack = stack_for_panel(self.model._layout_root, "snapshot")
        self.assertEqual(stack.active_panel_id, "snapshot")

        self.model.close_panel("snapshot")
        stack = stack_for_panel(self.model._layout_root, "notes")
        self.assertEqual(stack.active_panel_id, "task_calendar")

    def test_stack_roles_expose_only_docked_visible_members(self):
        self.model.place_panel("notes", "snapshot", "center")
        snapshot_row = self.model._index_for("snapshot")
        notes_row = self.model._index_for("notes")
        snapshot_index = self.model.index(snapshot_row, 0)
        notes_index = self.model.index(notes_row, 0)
        self.assertFalse(self.model.data(
            snapshot_index, self.model.StackActiveRole
        ))
        self.assertTrue(self.model.data(
            notes_index, self.model.StackActiveRole
        ))
        records = self.model.data(notes_index, self.model.StackPanelsRole)
        self.assertEqual(
            [record["panelId"] for record in records],
            ["task_calendar", "snapshot", "notes"],
        )

    def test_reorder_and_float_preserve_access_to_remaining_stack(self):
        self.model.place_panel("notes", "snapshot", "center")
        self.model.place_panel("task_calendar", "notes", "center")
        self.model.reorder_stack_panel("task_calendar", 0)
        stack = stack_for_panel(self.model._layout_root, "notes")
        self.assertEqual(
            stack.panel_ids,
            (
                "task_calendar", "timesheet", "work_reports",
                "cost_reports", "snapshot", "description", "notes",
            ),
        )

        self.model.float_panel_inside("task_calendar")
        stack = stack_for_panel(self.model._layout_root, "notes")
        self.assertEqual(stack.active_panel_id, "snapshot")
        self.assertEqual(self.panel("task_calendar").dock_area, "floating")

    def test_v2_restores_tree_stack_active_tab_and_window_modes(self):
        self.model.place_panel("notes", "snapshot", "center")
        self.model.place_panel("task_calendar", "notes", "center")
        self.model.reorder_stack_panel("task_calendar", 0)
        self.model.activate_stack_panel("snapshot")
        self.model.resize_panel(
            "results", "right", 0.0, 0.0, 0.30, 1.0,
            1600, 900,
        )
        self.model.float_panel(
            "drop_plate", 0.11, 0.13, 0.46, 0.51
        )
        self.model.detach_panel("description")
        self.model._settings.sync()

        restored = DockPanelModel(
            QSettings(str(self.settings_path), QSettings.Format.IniFormat)
        )
        stack = stack_for_panel(restored._layout_root, "snapshot")
        self.assertEqual(
            stack.panel_ids,
            (
                "task_calendar", "timesheet", "work_reports",
                "cost_reports", "snapshot", "description", "notes",
            ),
        )
        self.assertEqual(stack.active_panel_id, "snapshot")
        panel_by_id = {panel.panel_id: panel for panel in restored._panels}
        self.assertAlmostEqual(panel_by_id["results"].width, 0.30)
        self.assertEqual(panel_by_id["drop_plate"].dock_area, "floating")
        self.assertAlmostEqual(panel_by_id["drop_plate"].x, 0.11)
        self.assertTrue(panel_by_id["description"].detached)

    def test_corrupt_v2_restores_defaults_and_repairs_document(self):
        settings = QSettings(
            str(self.settings_path), QSettings.Format.IniFormat
        )
        settings.clear()
        settings.setValue("workspace/dockLayoutV2", "{broken")
        settings.sync()

        restored = DockPanelModel(settings)
        self.assertEqual(len(restored._panels), len(self.model._defaults()))
        repaired = json.loads(settings.value(
            "workspace/dockLayoutV2", "", type=str
        ))
        self.assertEqual(repaired["version"], 2)

    def test_invalid_layout_references_are_removed_on_restore(self):
        settings = QSettings(
            str(self.settings_path), QSettings.Format.IniFormat
        )
        payload = {
            "version": 2,
            "panels": [asdict(panel) for panel in self.model._defaults()],
            "layout": {
                "type": "stack",
                "panels": ["snapshot", "missing", "snapshot", "notes"],
                "active": "missing",
            },
        }
        settings.clear()
        settings.setValue(
            "workspace/dockLayoutV2", json.dumps(payload)
        )
        settings.sync()

        restored = DockPanelModel(settings)
        stack = stack_for_panel(restored._layout_root, "snapshot")
        self.assertEqual(stack.panel_ids, ("snapshot", "notes"))
        self.assertEqual(stack.active_panel_id, "snapshot")

    def test_reset_layout_restores_all_dock_parameters(self):
        visibility_changes = []
        self.model.panelVisibilityChanged.connect(
            lambda panel_id, visible: visibility_changes.append(
                (panel_id, visible)
            )
        )
        self.model.place_panel("notes", "snapshot", "center")
        self.model.float_panel_inside("tasks")
        self.model.detach_panel("description")
        self.model.close_panel("snapshot")
        visibility_changes.clear()

        self.model.reset_layout()

        self.assertEqual(self.model._panels, self.model._defaults())
        self.assertEqual(self.model._layout_root, default_layout())
        saved = json.loads(self.model._settings.value(
            "workspace/dockLayoutV2", "", type=str
        ))
        self.assertEqual(saved["layout"]["type"], "split")
        self.assertIn(("snapshot", True), visibility_changes)
        self.assertIn(("description", False), visibility_changes)

    def test_top_bar_menu_exposes_workspace_layout_reset(self):
        actions = MenuRegistry().actions("configuration")
        reset = next(
            action for action in actions
            if action.get("command") == "reset_workspace_layout"
        )
        self.assertEqual(reset["title"], "Reset workspace layout")
        self.assertEqual(reset["icon"], "restart-alt")


if __name__ == "__main__":
    unittest.main()
