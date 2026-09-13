import unittest

from thlib.ui.workspace_models.docks import DockPanelModel


class DockResizingTests(unittest.TestCase):
    def setUp(self):
        self.model = DockPanelModel({})

    def panel(self, panel_id):
        return next(
            panel for panel in self.model._panels
            if panel.panel_id == panel_id
        )

    def resize_results(self, width, host_width=1600, host_height=900):
        self.model.preview_resize_panel(
            "results", "right", 0.0, 0.0, width, 1.0,
            host_width, host_height,
        )

    def resize_work(self, boundary, host_width=1600, host_height=900):
        tasks = self.panel("tasks")
        self.model.preview_resize_panel(
            "tasks", "right", tasks.x, 0.0,
            boundary - tasks.x, 1.0,
            host_width, host_height,
        )

    def test_results_task_divider_keeps_right_stack_fixed(self):
        self.resize_results(0.24)
        self.assertAlmostEqual(self.panel("results").width, 0.24)
        self.assertAlmostEqual(self.panel("tasks").x, 0.24)
        self.assertAlmostEqual(self.panel("tasks").width, 0.42)
        self.assertAlmostEqual(self.panel("notes").x, 0.66)
        self.assertAlmostEqual(self.panel("snapshot").x, 0.66)
        self.assertAlmostEqual(
            self.panel("snapshot").x + self.panel("snapshot").width,
            1.0,
        )

    def test_active_and_adjacent_panels_stop_at_same_pixel_minimum(self):
        self.resize_results(0.10)
        expected_boundary = 360 / 1600
        self.assertAlmostEqual(self.panel("results").width, expected_boundary)
        self.assertAlmostEqual(self.panel("tasks").x, expected_boundary)
        self.assertAlmostEqual(self.panel("notes").x, 0.66)

        self.resize_results(0.05)
        self.assertAlmostEqual(self.panel("results").width, expected_boundary)
        self.assertAlmostEqual(self.panel("tasks").x, expected_boundary)

    def test_host_resize_projects_minimums_without_losing_preferred_ratios(self):
        self.resize_results(0.05, host_width=1800, host_height=1000)
        preferred_boundary = 360 / 1800
        self.assertAlmostEqual(
            self.panel("results").width, preferred_boundary
        )

        self.model.ensure_minimum_sizes(760, 640)

        expected_boundary = 360 / (360 + 320 + 400)
        self.assertAlmostEqual(self.panel("results").width, expected_boundary)
        self.assertAlmostEqual(self.panel("tasks").x, expected_boundary)
        self.assertAlmostEqual(
            self.panel("snapshot").x,
            (360 + 320) / (360 + 320 + 400),
        )

        self.model.ensure_minimum_sizes(1800, 1000)
        self.assertAlmostEqual(
            self.panel("results").width, preferred_boundary
        )
        self.assertAlmostEqual(self.panel("snapshot").x, 0.66)

    def test_default_three_columns_remain_unmodified_when_minimums_fit(self):
        save_calls = []
        self.model._save = lambda: save_calls.append(True)

        self.model.ensure_minimum_sizes(1800, 700)

        self.assertAlmostEqual(self.panel("results").width, 0.66 * 0.34)
        self.assertAlmostEqual(self.panel("tasks").x, 0.66 * 0.34)
        self.assertAlmostEqual(self.panel("snapshot").x, 0.66)
        self.assertEqual(save_calls, [])

    def test_minimum_host_size_tracks_the_visible_split_tree(self):
        self.assertEqual(self.model.minimumHostWidth, 1080)
        self.assertEqual(self.model.minimumHostHeight, 360)

        for panel_id in (
            "snapshot", "tasks", "notes", "task_calendar",
        ):
            self.model.close_panel(panel_id)

        self.assertEqual(self.model.minimumHostWidth, 360)
        self.assertEqual(self.model.minimumHostHeight, 260)

    def test_opening_a_larger_tab_updates_the_required_cell_size(self):
        self.model.show_panel("drop_plate")

        self.assertEqual(self.model.minimumHostWidth, 1240)
        self.assertEqual(self.model.minimumHostHeight, 360)

        self.model.ensure_minimum_sizes(
            self.model.minimumHostWidth,
            self.model.minimumHostHeight,
        )
        for panel in self.model._visible_docked_panels():
            minimum_width, minimum_height = (
                self.model._minimum_panel_pixel_size(panel)
            )
            self.assertGreaterEqual(
                panel.width * self.model.minimumHostWidth + 1e-7,
                minimum_width,
            )
            self.assertGreaterEqual(
                panel.height * self.model.minimumHostHeight + 1e-7,
                minimum_height,
            )

    def test_vertical_dock_split_adds_minimum_height_not_width(self):
        self.model.place_panel("drop_plate", "snapshot", "bottom")

        self.assertEqual(self.model.minimumHostWidth, 1160)
        self.assertEqual(self.model.minimumHostHeight, 720)

    def test_right_subtree_minimum_clamps_the_same_root_split(self):
        self.resize_work(0.90, host_width=1600, host_height=900)
        expected_boundary = 1.0 - 400 / 1600
        self.assertAlmostEqual(self.panel("notes").x, expected_boundary)
        self.assertAlmostEqual(
            self.panel("tasks").x + self.panel("tasks").width,
            expected_boundary,
        )

    def test_outer_resize_reclamps_every_nested_panel_minimum(self):
        # First put the inner results/tasks divider at the results minimum.
        # Shrinking their shared parent afterwards used to keep this stale
        # ratio, squeezing results below 360 px even though the parent had the
        # required aggregate width for both children.
        self.resize_results(360 / 1600, host_width=1600, host_height=900)
        self.resize_work(
            (360 + 320) / 1600,
            host_width=1600,
            host_height=900,
        )

        self.assertGreaterEqual(
            self.panel("results").width + 1e-9,
            360 / 1600,
        )
        self.assertGreaterEqual(
            self.panel("tasks").width + 1e-9,
            320 / 1600,
        )
        self.assertAlmostEqual(
            self.panel("notes").x,
            (360 + 320) / 1600,
        )

    def test_stack_uses_the_largest_member_minimum(self):
        self.resize_work(0.90, host_width=1600, host_height=900)
        self.assertAlmostEqual(self.panel("notes").x, 1.0 - 400 / 1600)

        self.model.reset_layout()
        self.model.close_panel("notes")
        self.resize_work(0.90, host_width=1600, host_height=900)
        self.assertAlmostEqual(
            self.panel("task_calendar").x,
            1.0 - 380 / 1600,
        )

    def test_nested_resize_keeps_unrelated_ancestor_ratios(self):
        self.model.place_panel("drop_plate", "snapshot", "bottom")
        results_before = self.panel("results")
        self.model.preview_resize_panel(
            "snapshot", "bottom", 0.66, 0.0, 0.34, 0.30,
            1800, 2000,
        )
        self.assertAlmostEqual(self.panel("snapshot").height, 0.30)
        self.assertAlmostEqual(self.panel("notes").height, 0.30)
        self.assertAlmostEqual(self.panel("drop_plate").y, 0.30)
        self.assertAlmostEqual(self.panel("results").x, results_before.x)
        self.assertAlmostEqual(
            self.panel("results").width, results_before.width
        )

    def test_preview_does_not_save_and_release_saves_once(self):
        save_calls = []
        self.model._save = lambda: save_calls.append(True)
        self.model.preview_resize_panel(
            "results", "right", 0.0, 0.0, 0.30, 1.0,
            1600, 900,
        )
        self.assertEqual(save_calls, [])
        self.model.resize_panel(
            "results", "right", 0.0, 0.0, 0.30, 1.0,
            1600, 900,
        )
        self.assertEqual(len(save_calls), 1)


if __name__ == "__main__":
    unittest.main()
