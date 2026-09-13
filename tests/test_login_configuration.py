from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from thlib.ui.configuration import ConfigurationController
from thlib.ui.editor_tools import ServerPresetsController
from thlib.ui.controllers.connection import ConnectionMixin
from thlib.ui.controllers.navigation import NavigationMixin
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.models import NavigationEntry


class _SignalStub:
    def __init__(self):
        self.calls = []

    def emit(self, *args):
        self.calls.append(args)


class _Settings:
    def __setitem__(self, key, value):
        self.values[key] = value

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
        self.tabs = []
        self.result_surfaces = []

    def clear_selection(self):
        self.cleared = True

    def set_tabs(self, records):
        self.tabs = list(records)

    def set_result_surfaces(self, records):
        self.result_surfaces = list(records)


class _AuthController(ConnectionMixin):
    def __init__(self):
        self._settings = _Settings()
        self._search_cache = {}
        self.search_cache_writes = 0
        self._ping_timer = Mock()
        self._section_state_save_timer = Mock()
        self._search_cache_save_timer = Mock()
        self._active_request_id = "active"
        self._project_request_id = "project"
        self.project_model = _Model()
        self.navigation_model = _Model()
        self.section_model = _Model()
        self.workspace_model = _Model()
        self.versions_model = _Model()
        self.workspace_state = _WorkspaceState()
        self._sessions = {
            "session": SimpleNamespace(
                current_tab_id="tab",
                tabs=[SimpleNamespace(
                    tab_id="tab", workspace_layout={"dock": "live"}
                )],
            ),
        }
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
        self._bootstrap_worker = None
        self._bootstrap_request_id = ""
        self._bootstrap_started_at = 0.0
        self.debug_log = None
        self.authentication_changed = _SignalStub()
        self.server_state_changed = _SignalStub()
        self.notification_changed = _SignalStub()
        self.project_changed = _SignalStub()
        self.project_state_changed = _SignalStub()
        self.section_state_changed = _SignalStub()
        self.loading = []
        self.states = []
        self.bootstraps = 0
        self.lifecycle = []

    def _set_loading(self, value, message=""):
        self.loading.append((value, message))

    def _set_server_state(self, state, message):
        self.states.append((state, message))

    def _transaction_metrics(self, _started_at, _result=None):
        return "0 requests"

    def bootstrap_server(self):
        self.bootstraps += 1

    def _write_settings(self):
        return None

    def _write_search_cache_config(self):
        self.search_cache_writes += 1

    @staticmethod
    def tr(value):
        return value

    def _dispose_all_tab_workspace_models(self):
        self.lifecycle.append("dispose")

    def _capture_current_workspace_layout(self):
        self.lifecycle.append("capture")

    def _write_opened_sections(self):
        self.lifecycle.append("opened")

    def _write_search_cache(self):
        self.lifecycle.append("cache")

    def _invalidate_sidebar_preset_requests(self):
        self.lifecycle.append("invalidate")


class _ProjectApplyController(ConnectionMixin, NavigationMixin):
    def __init__(self, entry):
        self.entry_key = entry.key
        self._settings = {"workspace/cacheProcessTabs": False}
        self._current_project_code = "demo"
        self._current_project_title = "Demo"
        self._current_project_preview = ""
        self._current_section_key = entry.key
        self._section_state_save_timer = Mock()
        self._search_cache_save_timer = Mock()
        self._search_cache = {}
        self._sidebar_preset_workers = {}
        self._sidebar_preset_requests = {}
        old_tab = SearchTabSession(
            tab_id="old", title=entry.title,
            workspace_layout={"root": {"ratio": 0.25}},
        )
        old_section = SectionSession(
            entry_key=entry.key,
            title=entry.title,
            accent=entry.accent,
            search_type=entry.search_type,
            tabs=[old_tab],
            current_tab_id=old_tab.tab_id,
        )
        self._sessions = {entry.key: old_section}
        self.live_layout = {"root": {"ratio": 0.64}}
        self.capture_calls = 0
        self.lifecycle = []
        self.project_model = SimpleNamespace(
            preview_for=lambda _project: "preview",
        )
        self.navigation_model = SimpleNamespace(
            replace=lambda _entries: None,
            entry=lambda key: entry if key == entry.key else None,
        )
        self.section_model = SimpleNamespace(replace=lambda _rows: None)
        self.workspace_model = SimpleNamespace(clear=lambda: None)
        self.workspace_state = SimpleNamespace(
            load_project=lambda _project: None,
            set_result_surfaces=lambda _rows: None,
            set_tabs=lambda _rows: None,
        )
        signal = lambda: SimpleNamespace(emit=lambda *_args: None)
        self.project_changed = signal()
        self.project_state_changed = signal()

    def _capture_current_workspace_layout(self):
        self.capture_calls += 1
        section = self._sessions[self._current_section_key]
        current = next(
            tab for tab in section.tabs
            if tab.tab_id == section.current_tab_id
        )
        current.workspace_layout = {
            "root": {"ratio": self.live_layout["root"]["ratio"]},
        }
        self.lifecycle.append("capture")

    def _write_opened_sections(self):
        self.lifecycle.append("opened")

    def _write_search_cache_config(self):
        raise AssertionError("disabled process-tab cache must not be written")

    def _write_settings(self):
        pass

    def _dispose_all_tab_workspace_models(self):
        self.lifecycle.append("dispose")

    def _opened_section_keys(self, _project_code):
        return [self.entry_key]

    def _saved_active_section_key(self, _project_code):
        return self.entry_key

    def _create_section(self, key, title, accent=""):
        entry = self.navigation_model.entry(key)
        section = SectionSession(
            entry_key=key,
            title=title,
            accent=accent,
            search_type=entry.search_type,
            layout_preset=entry.layout_preset,
        )
        tab = SearchTabSession(tab_id="new", title=title)
        section.tabs = [tab]
        section.current_tab_id = tab.tab_id
        self._sessions[key] = section
        return section

    def activate_section(self, key):
        self._current_section_key = key


class LoginConfigurationTests(unittest.TestCase):
    def test_missing_proxy_configuration_means_direct_connection(self):
        from thlib import proxy
        from thlib.environment import env_server

        previous_proxy = env_server.proxy
        previous_defaults = env_server.defaults
        try:
            env_server.proxy = None
            env_server.defaults = {"proxy": None}

            self.assertEqual(env_server.get_proxy(), {
                "login": "",
                "pass": "",
                "server": "",
                "enabled": False,
            })
            with patch.object(
                proxy.env_server, "get_proxy", return_value=None
            ):
                transport = proxy.UrllibTransport()
            self.assertFalse(transport.proxy_enabled)
            self.assertEqual(transport.proxy_server, "")
        finally:
            env_server.proxy = previous_proxy
            env_server.defaults = previous_defaults

    def test_missing_site_configuration_means_no_site(self):
        from thlib.environment import env_server

        previous_site = env_server.site
        previous_defaults = env_server.defaults
        try:
            env_server.site = None
            env_server.defaults = {"site": None}

            self.assertEqual(env_server.get_site(), {
                "site_name": "",
                "enabled": False,
            })
        finally:
            env_server.site = previous_site
            env_server.defaults = previous_defaults

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

    def test_authentication_failure_is_written_at_default_error_level(self):
        controller = _AuthController()
        controller.debug_log = Mock()

        controller._authentication_error_result(({
            "exception": TypeError(
                "'NoneType' object is not subscriptable"
            ),
            "stacktrace": "transport traceback",
        }, None))

        controller.debug_log.log.assert_called_once()
        call = controller.debug_log.log.call_args
        self.assertEqual(call.args[:2], (
            "ERROR", "'NoneType' object is not subscriptable",
        ))
        self.assertEqual(call.kwargs["group"], "server/authentication")
        self.assertEqual(call.kwargs["stacktrace"], "transport traceback")
        self.assertIn(
            "'NoneType' object is not subscriptable",
            controller._authentication_error,
        )

    def test_generated_ticket_failures_use_localizable_login_messages(self):
        expected_messages = {
            "TACTIC did not issue an authentication ticket.":
                "TACTIC did not issue an authentication ticket.",
            "TACTIC did not accept the generated ticket.":
                "TACTIC did not accept the generated ticket.",
        }
        for raw_message, expected in expected_messages.items():
            with self.subTest(raw_message=raw_message):
                controller = _AuthController()
                controller._authentication_error_result(({
                    "exception": RuntimeError(raw_message),
                    "stacktrace": "authentication traceback",
                }, None))
                self.assertEqual(controller._authentication_error, expected)

    def test_debug_log_is_available_from_the_sign_in_window(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        login = (root / "thlib/ui/qml/LoginDialog.qml").read_text(
            encoding="utf-8"
        )
        floating = (root / "thlib/ui/qml/FloatingWindow.qml").read_text(
            encoding="utf-8"
        )

        self.assertNotIn('toolTip: qsTr("Open Debug Log")', login)
        signed_out = floating.split(
            "readonly property bool availableWhileSignedOut:", 1
        )[1].split("readonly property bool contentRequested:", 1)[0]
        self.assertIn('kind === "debug_log"', signed_out)

    def test_bootstrap_worker_error_opens_the_error_dialog_with_traceback(self):
        controller = _AuthController()
        controller.debug_log = Mock()
        controller.debug_log.classify_error.return_value = "type_error"
        controller._bootstrap_request_id = "bootstrap-request"
        worker = Mock()
        worker.get_result_data.return_value = "bootstrap-request"
        exception = TypeError("'NoneType' object is not subscriptable")

        controller._async_bootstrap_error(({
            "exception": exception,
            "stacktrace": "bootstrap traceback",
        }, worker))

        controller.debug_log.raise_error.assert_called_once_with(
            exception,
            stacktrace="bootstrap traceback",
            group="server/bootstrap",
            retry_worker=worker,
        )
        controller.debug_log.log.assert_not_called()
        self.assertEqual(
            controller.notification_changed.calls[-1],
            ("'NoneType' object is not subscriptable",),
        )

    def test_logout_clears_server_and_workspace_state(self):
        from thlib.environment import env_server

        controller = _AuthController()
        bootstrap_worker = Mock()
        controller._bootstrap_worker = bootstrap_worker
        controller._bootstrap_request_id = "bootstrap"
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
        bootstrap_worker.cancel.assert_called_once_with()
        self.assertIsNone(controller._bootstrap_worker)
        self.assertEqual(controller._bootstrap_request_id, "")
        self.assertEqual(
            controller.lifecycle,
            ["capture", "opened", "cache", "invalidate", "dispose"],
        )
        controller._section_state_save_timer.stop.assert_called_once_with()
        controller._search_cache_save_timer.stop.assert_called_once_with()

    def test_same_project_refresh_retains_layout_with_tab_cache_disabled(self):
        from thlib.environment import env_inst

        entry = NavigationEntry(
            key="demo/assets@review",
            title="Review",
            glyph="sobject",
            group="",
            command="open_sidebar_item",
            search_type="demo/assets",
            layout_preset="workspace_layout@review",
        )
        controller = _ProjectApplyController(entry)
        project = SimpleNamespace()

        with patch.object(env_inst, "set_current_project") as set_project:
            controller._apply_selected_project(
                "demo", "Demo", [entry], project,
            )

        set_project.assert_called_once_with("demo")
        self.assertEqual(controller.capture_calls, 1)
        self.assertEqual(
            controller._sessions[entry.key].tabs[0].workspace_layout,
            controller.live_layout,
        )
        self.assertLess(
            controller.lifecycle.index("capture"),
            controller.lifecycle.index("dispose"),
        )
        controller._section_state_save_timer.stop.assert_called_once_with()
        controller._search_cache_save_timer.stop.assert_called_once_with()

    def test_project_preparation_does_not_change_the_global_project(self):
        from thlib.environment import env_inst

        project = SimpleNamespace(
            query_search_types=lambda **_kwargs: ["loaded"],
        )
        controller = SimpleNamespace(
            navigation_model=SimpleNamespace(
                build_project_entries=lambda *_args: ["entry"],
            ),
        )
        with (
            patch.object(env_inst, "projects", {"second": project}),
            patch.object(
                env_inst,
                "get_current_login_object",
                return_value=SimpleNamespace(),
            ),
            patch.object(env_inst, "set_current_project") as set_project,
        ):
            result = ConnectionMixin._prepare_project_selection(
                controller, "second", "Second",
            )

        self.assertEqual(result, (
            "second", "Second", ["entry"], project,
        ))
        set_project.assert_not_called()

    def test_manual_project_selection_cancels_the_startup_selection(self):
        from thlib.environment import env_inst

        controller = _AuthController()
        controller._current_project_code = "first"
        controller._project_started_at = {}
        bootstrap_worker = Mock()
        controller._bootstrap_worker = bootstrap_worker
        controller._bootstrap_request_id = "bootstrap"
        project_worker = Mock()
        pool = SimpleNamespace(
            is_stopped=False,
            add_task=Mock(return_value=project_worker),
        )
        project = SimpleNamespace(info={"title": "Second"})

        with (
            patch.object(env_inst, "projects", {"second": project}),
            patch.object(env_inst, "server_pool", pool),
        ):
            controller.select_project("second")

        bootstrap_worker.cancel.assert_called_once_with()
        self.assertIsNone(controller._bootstrap_worker)
        project_worker.start.assert_called_once_with()

    def test_new_login_reloads_presets_but_keeps_personal_workspace(self):
        from thlib.environment import env_server

        controller = _AuthController()
        personal_layout = {"root": {"ratio": 0.61}}
        controller._search_cache = {
            "bootstrapIdentity": "http://server|first-user",
            "demo": {
                "sections": [{
                    "entry_key": "demo/assets@review",
                    "sidebar_presets_initialized": True,
                    "tabs": [
                        {"tab_id": "base", "tab_kind": "base",
                         "workspace_layout": personal_layout},
                        {"tab_id": "mine", "tab_kind": "user"},
                        {"tab_id": "saved", "tab_kind": "preset"},
                    ],
                }],
            },
        }
        with (
            patch.object(env_server, "set_ticket"),
            patch.object(env_server, "save_defaults"),
        ):
            controller.logout()
        with (
            patch.object(env_server, "set_user"),
            patch.object(env_server, "set_ticket"),
            patch.object(env_server, "save_defaults"),
            patch.object(
                controller,
                "_bootstrap_cache_identity",
                return_value="http://server|second-user",
            ),
        ):
            controller._authentication_result((
                "second-user", "second-ticket",
            ))

        section = controller._search_cache["demo"]["sections"][0]
        self.assertFalse(section["sidebar_presets_initialized"])
        self.assertEqual(
            [tab["tab_id"] for tab in section["tabs"]],
            ["base", "mine"],
        )
        self.assertEqual(
            section["tabs"][0]["workspace_layout"], personal_layout
        )
        self.assertEqual(
            controller._search_cache["bootstrapIdentity"],
            "http://server|second-user",
        )
        self.assertEqual(controller.search_cache_writes, 1)
        self.assertEqual(controller.bootstraps, 1)

    def test_server_normalization_keeps_supported_polling_defaults(self):
        values = ConfigurationController._normalize_server({
            "serverUrl": "http://tactic.example/tactic/",
            "presetName": "studio",
            "userName": "artist",
            "serverUpdateInterval": 99,
            "presenceHeartbeatInterval": 99,
        })
        self.assertNotIn("userName", values)
        self.assertEqual(values["serverUrl"], "http://tactic.example")
        self.assertEqual(values["serverUpdateInterval"], 30)
        self.assertEqual(values["presenceHeartbeatInterval"], 120)

    def test_bare_tactic_host_is_normalized_to_http(self):
        values = ConfigurationController._normalize_server({
            "serverUrl": "192.168.2.144/tactic/",
            "presetName": "studio",
        })

        self.assertEqual(values["serverUrl"], "http://192.168.2.144")
        self.assertEqual(
            ConfigurationController._server_validation_error(values), ""
        )

    def test_saving_server_page_uses_selected_preset_account_and_routing(self):
        from thlib.environment import env_server

        applied = []
        controller = ConfigurationController(
            lambda *args: applied.append(args),
            self.fail,
            background_values=lambda: {},
        )
        values = ConfigurationController._normalize_server({
            "serverUrl": "http://tactic.example",
            "presetName": "studio",
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
            patch.object(env_server, "set_user") as set_user,
            patch.object(env_server, "set_site") as set_site,
            patch.object(env_server, "set_proxy") as set_proxy,
        ):
            self.assertTrue(controller._apply_page("server"))

        set_user.assert_not_called()
        set_site.assert_not_called()
        set_proxy.assert_not_called()
        self.assertEqual(
            applied, [("http://tactic.example", "studio", False)]
        )
        self.assertNotIn("userName", controller._original_values["server"])
        self.assertNotIn("proxyPassword", controller._original_values["server"])

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

class ServerPresetEditorTests(unittest.TestCase):
    def test_editor_loads_and_saves_native_preset_routing(self):
        from thlib.environment import env_mode, env_server

        workspace = _WorkspaceState()
        workspace.server_preset_model = _Model()
        controller = ServerPresetsController(workspace)
        presets = {
            "presets_list": ["default", "studio"],
            "current": "studio",
        }
        defaults = {
            "server": "http://default.example",
            "user": "",
            "ticket": None,
            "site": {"site_name": "", "enabled": False},
            "proxy": {
                "login": "",
                "pass": "",
                "server": "",
                "enabled": False,
            },
        }
        payloads = {
            "default": dict(defaults),
            "studio": {
                **defaults,
                "server": "http://studio.example",
                "user": "artist",
                "ticket": "stored-ticket",
                "site": {"site_name": "portal", "enabled": True},
                "proxy": {
                    "login": "proxy-user",
                    "pass": "stored-secret",
                    "server": "http://proxy.example",
                    "enabled": True,
                },
            },
        }

        def load_presets():
            env_server.server_presets = presets
            return presets

        def load_preset_defaults():
            env_server.server_presets_defaults = {
                "server_presets": presets
            }

        with (
            patch.object(
                env_server, "get_server_presets_defaults",
                side_effect=load_preset_defaults,
            ),
            patch.object(
                env_server, "get_server_presets",
                side_effect=load_presets,
            ),
            patch.object(
                env_server, "get_default_preset",
                return_value=defaults,
            ),
            patch.object(
                env_server, "get_server_preset",
                side_effect=lambda name: payloads[name],
            ),
        ):
            controller.reload()

        self.assertEqual(controller.selected_name, "studio")
        self.assertEqual(
            controller.selected_values["storedUser"], "artist"
        )
        self.assertTrue(controller.selected_values["hasTicket"])
        self.assertEqual(
            controller.selected_values["proxyServer"],
            "http://proxy.example",
        )

        controller.update_selected({
            **controller.selected_values,
            "serverUrl": "studio.example",
            "proxyPassword": "",
        })
        with (
            patch("thlib.environment.env_write_config") as write_config,
            patch.object(
                env_server, "save_server_presets_defaults"
            ) as save_defaults,
        ):
            self.assertTrue(controller.save())

        studio_write = next(
            call for call in write_config.call_args_list
            if call.kwargs["filename"] == "studio"
        )
        saved = studio_write.args[0]
        self.assertEqual(saved["server"], "http://studio.example")
        self.assertEqual(saved["proxy"]["pass"], "stored-secret")
        self.assertEqual(
            studio_write.kwargs["unique_id"],
            f"{env_mode.node}/environment_config/server_presets",
        )
        save_defaults.assert_called_once_with()

    def test_editor_rejects_invalid_server_urls(self):
        workspace = _WorkspaceState()
        workspace.server_preset_model = _Model()
        controller = ServerPresetsController(workspace)
        controller._active_name = "default"
        controller._drafts = {
            "default": {
                "server": "http://",
                "site": {"site_name": "", "enabled": False},
                "proxy": {
                    "login": "", "pass": "", "server": "",
                    "enabled": False,
                },
            },
        }
        controller._replace(["default"], "default")

        self.assertEqual(
            controller._validation_error(),
            "Enter a valid server address for every preset",
        )

        controller._drafts["default"]["server"] = (
            "HTTPS://tactic.example"
        )
        self.assertEqual(controller._validation_error(), "")

        controller._drafts["default"]["server"] = "192.168.2.144"
        self.assertEqual(controller._validation_error(), "")

    def test_editor_does_not_remove_the_active_preset(self):
        workspace = _WorkspaceState()
        workspace.server_preset_model = _Model()
        controller = ServerPresetsController(workspace)
        controller._active_name = "studio"
        controller._drafts = {
            "default": {},
            "studio": {},
        }
        controller._replace(["default", "studio"], "studio")

        controller.remove(1)

        self.assertEqual(
            [record["name"] for record in controller.model._records],
            ["default", "studio"],
        )
        self.assertTrue(controller.model._records[1]["isActive"])
        self.assertEqual(
            controller.error,
            "Switch to another server preset before deleting the active "
            "preset",
        )

    def test_begin_session_reloads_persisted_presets(self):
        workspace = _WorkspaceState()
        workspace.server_preset_model = _Model()
        controller = ServerPresetsController(workspace)
        started = []
        controller.sessionStarted.connect(lambda: started.append(True))

        with patch.object(controller, "reload") as reload_presets:
            controller.begin_session()

        reload_presets.assert_called_once_with()
        self.assertEqual(started, [True])



if __name__ == "__main__":
    unittest.main()
