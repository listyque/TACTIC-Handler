import unittest
from pathlib import Path


class TopBarQmlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("thlib/ui/qml/Main.qml").read_text(
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

    def test_startup_progress_stays_in_the_top_bar(self):
        activity = self.top_bar[
            self.top_bar.index("id: notificationActivityButton"):
            self.top_bar.index("id: connectionButton")
        ]
        self.assertIn(
            'appController.server_state === "connecting"',
            activity,
        )
        self.assertIn("appController.loading", activity)
        self.assertNotIn("startupLoadingOverlay", self.source)

    def test_connection_and_ping_menu_remain_available_when_compact(self):
        connection = self.top_bar[
            self.top_bar.index("id: connectionButton"):
            self.top_bar.index("id: dccClientButton")
        ]
        self.assertNotIn("visible: window.width >= 900", connection)
        self.assertIn(
            "readonly property bool expandedLabel: window.width >= 900",
            connection,
        )
        self.assertIn("? 106 : topAppBar.controlExtent", connection)
        self.assertIn('name: "online"', connection)
        self.assertIn("connectionMenu.toggleBelow(connectionButton)", connection)

    def test_dcc_and_activity_controls_compact_before_the_window_minimum(self):
        activity = self.top_bar[
            self.top_bar.index("id: notificationActivityButton"):
            self.top_bar.index("id: connectionButton")
        ]
        dcc = self.top_bar[
            self.top_bar.index("id: dccClientButton"):
            self.top_bar.index('iconName: "commit_queue"')
        ]
        self.assertIn("compactProgress: window.width < 760", activity)
        self.assertIn("compactIconOnly: window.width < 720", dcc)
        self.assertIn("visible: dccClientButton.compactIconOnly", dcc)

    def test_dcc_menu_refreshes_details_when_opened(self):
        self.assertIn(
            "onOpened: handlerServerController.refresh_client_details()",
            self.source,
        )

    def test_theme_action_uses_a_split_light_dark_glyph(self):
        icons = Path(
            "thlib/ui/qml/controls/MaterialIcon.qml"
        ).read_text(encoding="utf-8")
        self.assertIn('"theme-mode": "adjust"', icons)
        self.assertNotIn('"light-mode"', icons)
        self.assertNotIn('"dark-mode"', icons)
        self.assertIn(
            'iconName: "theme_mode"',
            self.top_bar,
        )

    def test_user_menu_button_uses_shared_touch_activation(self):
        user_button = self.top_bar[
            self.top_bar.index("id: userButton"):
        ]
        self.assertIn('objectName: "topBarUserButton"', user_button)
        self.assertIn("id: userActivation", user_button)
        self.assertIn(
            "userActivation.lastActivationWasTouch", user_button
        )
        self.assertIn("userMenu.toggleBelow(userButton)", user_button)
        self.assertNotIn("id: userMouse", user_button)

    def test_all_top_bar_popup_buttons_use_shared_touch_activation(self):
        for button_id, activation_id, old_mouse_id in (
            ("projectButton", "projectActivation", "projectMouse"),
            ("connectionButton", "connectionActivation", "connectionMouse"),
            ("dccClientButton", "dccClientActivation", "dccClientMouse"),
        ):
            self.assertIn(f"id: {button_id}", self.top_bar)
            self.assertIn(f"id: {activation_id}", self.top_bar)
            self.assertIn(
                f"{activation_id}.lastActivationWasTouch",
                self.top_bar,
            )
            self.assertNotIn(f"id: {old_mouse_id}", self.top_bar)

if __name__ == "__main__":
    unittest.main()
