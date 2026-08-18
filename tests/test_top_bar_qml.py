import unittest
from pathlib import Path


class TopBarQmlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("modern_ui/qml/Main.qml").read_text(
            encoding="utf-8"
        )
        cls.top_bar = cls.source[
            cls.source.index("id: topAppBar"):
            cls.source.index("id: workspaceLayer")
        ]

    def test_bar_stays_compact_when_pointer_or_popup_state_changes(self):
        self.assertIn("height: 44", self.top_bar)
        self.assertIn("controlExtent: 36", self.top_bar)
        self.assertIn("controlSurfaceExtent: 32", self.top_bar)
        self.assertNotIn("expansionProgress", self.top_bar)
        self.assertNotIn("id: topAppBarHover", self.top_bar)
        self.assertNotIn("topAppBarCollapseTimer", self.top_bar)
    def test_activity_expansion_uses_one_animation_phase(self):
        activity = self.top_bar[
            self.top_bar.index("id: notificationActivityButton"):
            self.top_bar.index("id: connectionButton")
        ]
        self.assertIn("property real progressReveal", activity)
        self.assertIn("Behavior on progressReveal", activity)
        self.assertNotIn("Behavior on Layout.preferredWidth", activity)
        self.assertIn(
            "opacity: 1.0 - notificationActivityButton.progressReveal",
            activity,
        )


if __name__ == "__main__":
    unittest.main()