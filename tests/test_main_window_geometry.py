from __future__ import annotations

import unittest

from thlib.ui.window_geometry import ScreenGeometry, resolve_window_state


class MainWindowGeometryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.primary = ScreenGeometry("primary", "DISPLAY1", 0, 0, 1920, 1040)
        self.right = ScreenGeometry("right", "DISPLAY2", 1920, 0, 2560, 1400)
        self.left = ScreenGeometry("left", "DISPLAY3", -1600, 0, 1600, 860)

    def test_restores_window_on_right_hand_monitor(self) -> None:
        state = resolve_window_state(
            {"x": 2200, "y": 120, "width": 1280, "height": 820},
            [self.primary, self.right],
            self.primary.identity,
        )
        self.assertEqual((state["x"], state["y"]), (2200, 120))
        self.assertEqual(state["screen_identity"], self.right.identity)

    def test_negative_coordinates_on_left_monitor_are_preserved(self) -> None:
        state = resolve_window_state(
            {"x": -1500, "y": 40, "width": 1200, "height": 760},
            [self.primary, self.left],
            self.primary.identity,
        )
        self.assertEqual((state["x"], state["y"]), (-1500, 40))
        self.assertEqual(state["screen_identity"], self.left.identity)

    def test_missing_monitor_maps_relative_position_to_primary(self) -> None:
        state = resolve_window_state(
            {
                "x": 2200,
                "y": 100,
                "width": 1200,
                "height": 760,
                "screen_identity": "disconnected",
                "screen_name": "DISPLAY9",
                "screen_x": 1920,
                "screen_y": 0,
                "screen_width": 2560,
                "screen_height": 1400,
            },
            [self.primary],
            self.primary.identity,
        )
        self.assertGreaterEqual(state["x"], 0)
        self.assertLessEqual(state["x"] + state["width"], 1920)
        self.assertGreaterEqual(state["y"], 0)
        self.assertLessEqual(state["y"] + state["height"], 1040)

    def test_oversized_saved_geometry_is_clamped_to_work_area(self) -> None:
        state = resolve_window_state(
            {
                "x": 2100,
                "y": -50,
                "width": 5000,
                "height": 3000,
                "screen_identity": self.right.identity,
            },
            [self.primary, self.right],
            self.primary.identity,
        )
        self.assertEqual(state["width"], self.right.width)
        self.assertEqual(state["height"], self.right.height)
        self.assertEqual((state["x"], state["y"]), (self.right.x, self.right.y))

    def test_runtime_geometry_fully_outside_desktop_returns_to_primary(self) -> None:
        state = resolve_window_state(
            {
                "x": 9000,
                "y": 7000,
                "width": 1280,
                "height": 820,
            },
            [self.primary, self.right, self.left],
            self.primary.identity,
        )
        self.assertGreaterEqual(state["x"], self.primary.x)
        self.assertGreaterEqual(state["y"], self.primary.y)
        self.assertLessEqual(
            state["x"] + state["width"],
            self.primary.x + self.primary.width,
        )
        self.assertLessEqual(
            state["y"] + state["height"],
            self.primary.y + self.primary.height,
        )


if __name__ == "__main__":
    unittest.main()
