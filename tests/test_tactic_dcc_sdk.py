from __future__ import annotations

import unittest

from handler_server.client import ThinClient
from handler_server.registry import CommandRegistry
from handler_server.server import HandlerServer
from modern_ui.tactic_rpc import TacticObjectService
from tactic_handler_dcc.session import TacticSession


class _ApplicationStub:
    def __init__(self):
        self.calls = []
        self.dock_model = self
        self.window_model = self

    def select_project(self, value):
        self.calls.append(("project", value))

    def open_search_key(self, value):
        self.calls.append(("search_key", value))

    def select_sobject(self, value):
        self.calls.append(("sobject", value))

    def show_panel(self, value):
        self.calls.append(("panel", value))

    def show_window(self, value):
        self.calls.append(("window", value))


class _CheckinStub:
    def __init__(self):
        self.mode = ""

    def set_mode(self, value):
        self.mode = value


class TacticDccSdkTests(unittest.TestCase):
    def setUp(self):
        self.server = HandlerServer(token="sdk-test-token")
        self.port = self.server.start()
        registry = CommandRegistry()
        self.service = TacticObjectService()
        self.application = _ApplicationStub()
        self.checkin = _CheckinStub()
        self.shown = []
        self.service._gui_dispatch = lambda callback, *args: callback(*args)
        self.service.attach_application(
            self.application, self.checkin,
            lambda _payload: self.shown.append(True),
        )
        self.service.register(registry)
        self.operator = ThinClient(
            "127.0.0.1", self.port, "sdk-test-token", "modern_ui",
            registry=registry, client_id="sdk-operator",
        )
        self.dcc = ThinClient(
            "127.0.0.1", self.port, "sdk-test-token", "maya",
            client_id="sdk-maya",
        )
        self.operator.start()
        self.dcc.start()
        self.assertTrue(self.operator.wait_connected(3.0))
        self.assertTrue(self.dcc.wait_connected(3.0))
        self.session = TacticSession(self.dcc, timeout=3.0)

    def tearDown(self):
        self.dcc.stop()
        self.operator.stop()
        self.server.stop()

    def test_native_module_functions_keep_original_names(self):
        tc = self.session.module("tactic_classes")
        parsed = tc.split_search_key(
            "dolly3d/assets?project=niki_friends&code=ASSETS00001"
        )
        self.assertEqual(parsed["project_code"], "niki_friends")
        self.assertEqual(parsed["pipeline_code"], "dolly3d/assets")

        gf = self.session.module("global_functions")
        self.assertEqual(
            gf.form_path("folder\\file.ma", "linux"), "folder/file.ma"
        )

    def test_native_objects_are_chainable_remote_handles(self):
        tc = self.session.module("tactic_classes")
        sobject = tc.SObject({
            "__search_key__": "dolly3d/assets?project=niki_friends&code=A1",
            "code": "A1", "name": "Hero", "description": "Main asset",
        })
        self.assertEqual(sobject.get_code(), "A1")
        self.assertEqual(sobject.get_value("description"), "Main asset")
        self.assertEqual(sobject.info["name"], "Hero")
        sobject.set_value("description", "Updated")
        self.assertEqual(sobject.get_value("description"), "Main asset")
        self.assertIn("SObject", repr(sobject))

    def test_private_members_are_not_exposed(self):
        tc = self.session.module("tactic_classes")
        with self.assertRaises(AttributeError):
            getattr(tc, "_forbidden")

    def test_original_ui_shortcuts_target_modern_application(self):
        ui_main = self.session.environment.ui_main
        self.assertTrue(ui_main.create_project_dock("niki_friends", False))
        checkin = self.session.environment.get_check_tree(
            "niki_friends", "checkin_out", "dolly3d/assets"
        )
        self.assertTrue(checkin.do_creating_ui())
        self.assertIn(("project", "niki_friends"), self.application.calls)
        self.assertIn(("window", "commit_queue"), self.application.calls)
        self.assertEqual(self.checkin.mode, "checkin")
        self.assertTrue(self.shown)


if __name__ == "__main__":
    unittest.main()
