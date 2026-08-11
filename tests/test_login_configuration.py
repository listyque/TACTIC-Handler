from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from modern_ui.configuration import ConfigurationController
from modern_ui.controllers.connection import ConnectionMixin


class _SignalStub:
    def __init__(self):
        self.calls = []

    def emit(self, *args):
        self.calls.append(args)


class _Settings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None, type=None):
        value = self.values.get(key, default)
        return type(value) if type and value is not None else value

    def setValue(self, key, value):
        self.values[key] = value


class _Model:
    def __init__(self):
        self.values = ["old"]

    def replace(self, values):
        self.values = list(values)

    def clear(self):
        self.values = []


class _WorkspaceState:
    def __init__(self):
        self.cleared = False

    def clear_selection(self):
        self.cleared = True


class _AuthController(ConnectionMixin):
    def __init__(self):
        self._settings = _Settings()
        self._ping_timer = Mock()
        self._active_request_id = "active"
        self._project_request_id = "project"
        self.project_model = _Model()
        self.navigation_model = _Model()
        self.section_model = _Model()
        self.workspace_model = _Model()
        self.versions_model = _Model()
        self.workspace_state = _WorkspaceState()
        self._sessions = {"session": object()}
        self._current_section_key = "section"
        self._current_project_code = "project"
        self._current_project_title = "Project"
        self._current_user_initials = "AB"
        self._authentication_busy = False
        self._authentication_required = False
        self._authentication_dialog_visible = False
        self._authentication_error = ""
        self._login_name = ""
        self._authentication_started_at = 0.0
        self.authentication_changed = _SignalStub()
        self.server_state_changed = _SignalStub()
        self.project_changed = _SignalStub()
        self.project_state_changed = _SignalStub()
        self.section_state_changed = _SignalStub()
        self.loading = []
        self.states = []
        self.bootstraps = 0

    def _set_loading(self, value, message=""):
        self.loading.append((value, message))

    def _set_server_state(self, state, message):
        self.states.append((state, message))

    def _transaction_metrics(self, _started_at):
        return "0 requests"

    def bootstrap_server(self):
        self.bootstraps += 1


class LoginConfigurationTests(unittest.TestCase):
    def test_authentication_result_persists_ticket_then_bootstraps(self):
        from thlib.environment import env_server

        controller = _AuthController()
        with (
            patch.object(env_server, "set_user") as set_user,
            patch.object(env_server, "set_ticket") as set_ticket,
            patch.object(env_server, "save_defaults") as save_defaults,
        ):
            controller._authentication_result(("artist", "ticket-code"))

        set_user.assert_called_once_with("artist")
        set_ticket.assert_called_once_with("ticket-code")
        save_defaults.assert_called_once_with()
        self.assertEqual(controller._settings.values["server/lastLogin"], "artist")
        self.assertFalse(controller._authentication_required)
        self.assertFalse(controller._authentication_dialog_visible)
        self.assertEqual(controller.bootstraps, 1)

    def test_logout_clears_server_and_workspace_state(self):
        from thlib.environment import env_server

        controller = _AuthController()
        with (
            patch.object(env_server, "set_ticket") as set_ticket,
            patch.object(env_server, "save_defaults") as save_defaults,
        ):
            controller.logout()

        set_ticket.assert_called_once_with(None)
        save_defaults.assert_called_once_with()
        self.assertTrue(controller.workspace_state.cleared)
        self.assertEqual(controller._sessions, {})
        self.assertEqual(controller.project_model.values, [])
        self.assertEqual(controller.states[-1][0], "authentication")
        self.assertTrue(controller._authentication_dialog_visible)

    def test_server_normalization_keeps_supported_polling_defaults(self):
        values = ConfigurationController._normalize_server({
            "serverUrl": "http://tactic.example/tactic/",
            "presetName": "studio",
            "userName": "artist",
            "serverUpdateInterval": 99,
            "presenceHeartbeatInterval": 99,
        })
        self.assertEqual(values["serverUrl"], "http://tactic.example")
        self.assertEqual(values["serverUpdateInterval"], 30)
        self.assertEqual(values["presenceHeartbeatInterval"], 120)

    def test_saving_server_page_preserves_existing_proxy_password(self):
        from thlib.environment import env_server

        applied = []
        background = []
        controller = ConfigurationController(
            lambda *args: applied.append(args),
            self.fail,
            background_values=lambda: {},
            apply_background_configuration=background.append,
        )
        values = ConfigurationController._normalize_server({
            "serverUrl": "http://tactic.example",
            "presetName": "studio",
            "userName": "artist",
            "proxyEnabled": True,
            "proxyLogin": "proxy-user",
            "proxyServer": "http://proxy.example",
            "proxyPassword": "",
            "hasProxyPassword": True,
            "serverUpdateInterval": 30,
            "presenceHeartbeatInterval": 120,
        })
        controller._pending_values["server"] = values
        controller._dirty_pages.add("server")
        with (
            patch.object(
                env_server, "get_server_presets",
                return_value={"presets_list": ["studio"]},
            ),
            patch.object(
                env_server, "get_server_preset",
                return_value={"proxy": {"pass": "saved-secret"}},
            ),
            patch.object(env_server, "set_user"),
            patch.object(env_server, "set_site"),
            patch.object(env_server, "set_proxy") as set_proxy,
        ):
            self.assertTrue(controller._apply_page("server"))

        set_proxy.assert_called_once_with(
            "proxy-user", "saved-secret", "http://proxy.example", True,
        )
        self.assertEqual(applied, [("http://tactic.example", "studio", True)])
        self.assertEqual(controller._original_values["server"]["proxyPassword"], "")
        self.assertTrue(controller._original_values["server"]["hasProxyPassword"])

    def test_discard_closes_and_drops_unsaved_configuration(self):
        controller = ConfigurationController(lambda *_args: None, self.fail)
        controller._pending_values["server"] = {"serverUrl": "changed"}
        controller._dirty_pages.add("server")
        closed = []
        controller.closeAllowed.connect(lambda: closed.append(True))

        controller.discard_and_close()

        self.assertEqual(controller._pending_values, {})
        self.assertFalse(controller.dirty)
        self.assertEqual(closed, [True])


if __name__ == "__main__":
    unittest.main()
