from __future__ import annotations

import importlib
from pathlib import Path
import os
import sys
from tempfile import TemporaryDirectory
import threading
import time
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tactic_handler_dcc.maya import MayaRuntime
from tactic_handler_dcc import maya as maya_module
from tactic_handler_dcc import runtime as runtime_module
from tactic_handler_api import BlockingCallError
from tactic_handler_api.operations import check_blocking_call


class _Connector:
    dispatch = staticmethod(lambda callback: callback())

    @staticmethod
    def register(registry):
        registry.register("maya_test", lambda _payload: {"success": True})
        return registry


class _Client:
    def __init__(self, on_event):
        self._connected = threading.Event()
        self.on_event = on_event
        self.started = False
        self.stopped = False
        self.stop_completed = threading.Event()
        self.requests = []
        self.events = []
        self.capability_refreshes = 0

    @property
    def connected(self):
        return self._connected.is_set()

    def start(self):
        self.started = True

    def connect(self):
        self._connected.set()
        self.on_event({"type": "capabilities"})

    def disconnect(self):
        self._connected.clear()
        self.on_event({"type": "client_disconnected"})

    def wait_connected(self, timeout):
        return self._connected.wait(timeout)

    def stop(self, wait=True):
        self.stopped = True
        self._connected.clear()
        self.stop_completed.set()

    def request(self, target, action, payload, timeout):
        self.requests.append((target, action, payload, timeout))
        return {"accepted": True}

    def publish_event(self, action, status, payload):
        self.events.append((action, status, payload))

    def refresh_capabilities(self):
        self.capability_refreshes += 1


class MayaRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "launch.pyw").write_text(
            "# test launcher\n",
            encoding="utf-8",
        )
        self.clients = []
        self.notifications = []

    def tearDown(self):
        self.temporary.cleanup()

    def factory(self, _application_type, **options):
        client = _Client(options["on_event"])
        self.clients.append(client)
        return client

    def runtime(self, **options):
        return MayaRuntime(
            self.root,
            connector=_Connector(),
            client_factory=self.factory,
            notifier=lambda message, level: self.notifications.append(
                (message, level)
            ),
            register_exit=False,
            **options,
        )

    def test_start_returns_without_waiting_and_launches_missing_handler(self):
        launch_called = threading.Event()

        def launch(_root, _python):
            launch_called.set()
            threading.Timer(0.01, self.clients[0].connect).start()
            return 4321

        runtime = self.runtime(
            session_finder=lambda: None,
            handler_launcher=launch,
        )
        started = time.monotonic()
        runtime.start()

        self.assertLess(time.monotonic() - started, 0.5)
        self.assertTrue(launch_called.wait(1.0))
        self.assertTrue(runtime.wait_until_connected(1.0))
        self.assertEqual(runtime.status["launched_process_id"], 4321)
        runtime.stop()

    def test_existing_handler_is_reused_and_window_is_requested(self):
        launch_calls = []
        runtime = self.runtime(
            session_finder=lambda: {"host": "127.0.0.1"},
            handler_launcher=lambda *_args: launch_calls.append(True),
        )
        runtime.start()
        self.clients[0].connect()

        self.assertTrue(runtime.wait_until_connected(1.0))
        deadline = time.monotonic() + 1.0
        while not self.clients[0].requests and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(launch_calls, [])
        self.assertEqual(
            self.clients[0].requests[0][0:2],
            ("@tactic_handler", "show_handler_window"),
        )
        runtime.stop()

    def test_stop_is_non_blocking_and_clears_the_client(self):
        runtime = self.runtime(
            session_finder=lambda: {"host": "127.0.0.1"},
        ).start()
        client = self.clients[0]

        runtime.stop()

        self.assertTrue(client.stop_completed.wait(3))
        self.assertIsNone(runtime.client)
        self.assertEqual(runtime.state, "stopped")

    def test_stop_keeps_transport_alive_until_api_cleanup_finishes(self):
        runtime = self.runtime(session_finder=lambda: {"host": "127.0.0.1"}).start()
        client = self.clients[0]
        entered, release = threading.Event(), threading.Event()
        original = runtime._api

        def close(*, wait):
            self.assertTrue(wait)
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test gate")
            original.close()

        runtime._api = SimpleNamespace(close=close)
        try:
            runtime.stop()
            self.assertTrue(entered.wait(3))
            self.assertFalse(client.stopped)
            self.assertIsNone(runtime._api)
        finally:
            release.set()
            self.assertTrue(client.stop_completed.wait(3))

    def test_repeated_startup_reuses_the_connected_client(self):
        options = {
            "connector": _Connector(),
            "client_factory": self.factory,
            "session_finder": lambda: {"host": "127.0.0.1"},
            "notifier": lambda *_args: None,
            "register_exit": False,
        }
        first = maya_module.startup(self.root, **options)
        first_client = self.clients[0]
        first_client.connect()
        self.assertTrue(first.wait_until_connected(1.0))
        deadline = time.monotonic() + 1.0
        while not first_client.requests and time.monotonic() < deadline:
            time.sleep(0.01)
        request_count = len(first_client.requests)

        second = maya_module.startup(self.root, **options)
        deadline = time.monotonic() + 1.0
        while (
            len(first_client.requests) == request_count
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        self.assertFalse(first_client.stopped)
        self.assertIs(first, second)
        self.assertEqual(len(self.clients), 1)
        self.assertGreater(len(first_client.requests), request_count)
        self.assertEqual(
            first_client.requests[-1][0:2],
            ("@tactic_handler", "show_handler_window"),
        )
        maya_module.stop()

    def test_module_reload_preserves_the_connected_client(self):
        options = {
            "connector": _Connector(),
            "client_factory": self.factory,
            "session_finder": lambda: {"host": "127.0.0.1"},
            "notifier": lambda *_args: None,
            "register_exit": False,
        }
        first = maya_module.startup(self.root, **options)
        first_client = self.clients[0]
        first_client.connect()
        self.assertTrue(first.wait_until_connected(1.0))

        reloaded = importlib.reload(maya_module)
        second = reloaded.startup(self.root, **options)

        self.assertIs(first, second)
        self.assertFalse(first_client.stopped)
        self.assertEqual(len(self.clients), 1)
        maya_module.stop()

    def test_module_reload_relaunches_handler_without_stopping_client(self):
        session = {"available": True}
        launched = threading.Event()
        options = {
            "connector": _Connector(),
            "client_factory": self.factory,
            "session_finder": lambda: (
                {"host": "127.0.0.1"} if session["available"] else None
            ),
            "handler_launcher": lambda *_args: launched.set(),
            "notifier": lambda *_args: None,
            "register_exit": False,
        }
        first = maya_module.startup(self.root, **options)
        client = self.clients[0]
        client.connect()
        self.assertTrue(first.wait_until_connected(1.0))
        while first._bootstrap_thread.is_alive():
            time.sleep(0.01)

        session["available"] = False
        client.disconnect()

        reloaded = importlib.reload(maya_module)
        second = reloaded.startup(self.root, **options)

        self.assertTrue(launched.wait(1.0))
        self.assertIs(first, second)
        self.assertFalse(client.stopped)
        self.assertEqual(len(self.clients), 1)
        client.connect()
        self.assertTrue(second.wait_until_connected(1.0))
        reloaded.stop()

    def test_startup_reloads_default_maya_client_modules(self):
        reloaded = []

        class RuntimeStub:
            def __init__(self, *_args, **_kwargs):
                self.stopped = False

            def start(self):
                return self

            def stop(self):
                self.stopped = True

        class ConnectorClass:
            @staticmethod
            def instance(_handler_path=None):
                return _Connector()

        def reload_module(module):
            reloaded.append(module.__name__)
            if module.__name__ == "tactic_handler_dcc.connectors.maya":
                return SimpleNamespace(
                    DCC_MANIFEST={"application": "maya", "title": "Maya"},
                    MayaConnector=ConnectorClass,
                )
            return module

        maya_module.stop()
        with patch.object(
            runtime_module.importlib,
            "reload",
            side_effect=reload_module,
        ), patch.object(maya_module, "MayaRuntime", RuntimeStub):
            runtime = maya_module.startup(self.root)

        self.assertEqual(reloaded, [
            "tactic_handler_api.errors", "tactic_handler_api.identity",
            "tactic_handler_api.operations", "tactic_handler_api.objects",
            "tactic_handler_api.api", "tactic_handler_api.contract",
            "tactic_handler_api.wire", "tactic_handler_api.remote", "tactic_handler_api",
            "tactic_handler_dcc.connectors.maya",
        ])
        maya_module.stop()
        self.assertTrue(runtime.stopped)

    def test_startup_reloads_commands_without_reconnecting_maya(self):
        handler_paths = []

        class Connector:
            dispatch = staticmethod(lambda callback: callback())

            def register(self, registry):
                registry.register("updated", lambda _payload: {})
                return registry

        class ConnectorClass:
            @staticmethod
            def instance(handler_path=None):
                handler_paths.append(handler_path)
                return Connector()

        client = _Client(lambda _event: None)
        client.registry = None
        runtime = SimpleNamespace(
            state="connected",
            connected=True,
            client=client,
            connector=None,
            handler_path=self.root,
            show_handler=lambda: None,
            _api=SimpleNamespace(close=Mock()),
        )
        maya_module._entrypoint._runtime = runtime

        def reload_module(module):
            if module.__name__ == "tactic_handler_dcc.connectors.maya":
                return SimpleNamespace(
                    DCC_MANIFEST={"application": "maya", "title": "Maya"},
                    MayaConnector=ConnectorClass,
                )
            return module

        with patch.object(
            runtime_module.importlib, "reload", side_effect=reload_module
        ), patch.object(
            maya_module, "MayaConnector", maya_module.MayaConnector
        ):
            result = maya_module.startup(self.root)

        self.assertIs(result, runtime)
        self.assertFalse(client.stopped)
        self.assertEqual(client.registry.capabilities(), ["updated"])
        self.assertEqual(client.capability_refreshes, 1)
        self.assertEqual(handler_paths, [self.root])
        self.assertIs(runtime._api._client, client)
        runtime._api.close(wait=False)
        maya_module._entrypoint._runtime = None

    def test_public_module_does_not_export_legacy_names(self):
        for name in ("api", "tc", "gf", "mf", "env_inst", "environment"):
            self.assertFalse(hasattr(maya_module, name))

    def test_public_maya_helpers_use_the_active_connector(self):
        connector = Mock()
        connector.get_current_scene_format.return_value = "mayaAscii"
        connector.get_maya_window.return_value = "MayaWindow"
        connector.get_skey_from_scene.return_value = "skey://demo/asset?code=A1"
        maya_module._entrypoint._runtime = SimpleNamespace(connector=connector)

        try:
            self.assertEqual(
                maya_module.get_current_scene_format(), "mayaAscii"
            )
            self.assertEqual(maya_module.get_maya_window(), "MayaWindow")
            self.assertEqual(
                maya_module.get_skey_from_scene(),
                "skey://demo/asset?code=A1",
            )
            maya_module.set_info_to_scene("demo/asset?code=A1", "publish")
        finally:
            maya_module._entrypoint._runtime = None

        connector.get_current_scene_format.assert_called_once_with()
        connector.get_maya_window.assert_called_once_with()
        connector.get_skey_from_scene.assert_called_once_with()
        connector.set_info_to_scene.assert_called_once_with(
            "demo/asset?code=A1", "publish"
        )

    def test_custom_script_uses_its_requested_project_context(self):
        script = (
            self.root
            / "custom_scripts"
            / "demo"
            / "tools"
            / "runner.py"
        )
        script.parent.mkdir(parents=True)
        script.write_text(
            "from tactic_handler_api import get_api\n"
            "RESULT = (TACTIC_PROJECT_CODE, get_api() is not None)\n",
            encoding="utf-8",
        )
        runtime = self.runtime(
            session_finder=lambda: {"host": "127.0.0.1"},
        ).start()
        self.clients[0].connect()
        self.assertTrue(runtime.wait_until_connected(1.0))

        result = runtime.execute_custom_script(
            "tools/runner", project="demo"
        ).wait(1.0)
        self.assertEqual(result, ("demo", True))
        runtime.stop()

    def test_custom_script_runs_from_the_configured_handler_tree(self):
        script = (
            self.root
            / "custom_scripts"
            / "demo"
            / "tools"
            / "runner.py"
        )
        script.parent.mkdir(parents=True)
        script.write_text(
            "RESULT = TACTIC_SCRIPT_KWARGS['value'] + 1\n",
            encoding="utf-8",
        )
        runtime = self.runtime(
            session_finder=lambda: {"host": "127.0.0.1"},
        ).start()
        self.clients[0].connect()
        self.assertTrue(runtime.wait_until_connected(1.0))

        job = runtime.execute_custom_script(
            "tools/runner", project="demo", kwargs={"value": 41},
        )
        self.assertEqual(job.wait(1.0), 42)
        runtime.stop()

    def test_custom_script_keeps_legacy_synchronous_api_calls_scoped(self):
        script = self.root / "runner.py"
        script.write_text(
            "from tactic_handler_api.operations import check_blocking_call\n"
            "check_blocking_call()\n"
            "RESULT = True\n",
            encoding="utf-8",
        )

        with patch.dict(sys.modules, {"maya.cmds": ModuleType("maya.cmds")}):
            self.assertTrue(MayaRuntime._load_script(script, {}, project="demo"))
            with self.assertRaises(BlockingCallError):
                check_blocking_call()


    def test_real_client_connects_without_demo_client(self):
        from handler_server.client import ThinClient
        from handler_server.discovery import publish_session, remove_session
        from handler_server.registry import CommandRegistry
        from handler_server.server import HandlerServer

        discovery = self.root / "discovery"
        discovery.mkdir()
        previous = os.environ.get("TACTIC_HANDLER_DISCOVERY_DIR")
        os.environ["TACTIC_HANDLER_DISCOVERY_DIR"] = str(discovery)
        server = HandlerServer(token="maya-runtime-integration")
        server.start()
        record = publish_session(server.host, server.port, server.token)
        opened = threading.Event()
        registry = CommandRegistry()
        registry.register(
            "show_handler_window",
            lambda _payload: (opened.set(), {"accepted": True})[1],
        )
        operator = ThinClient(
            server.host,
            server.port,
            server.token,
            "tactic_handler",
            registry=registry,
            client_id="runtime-tactic-handler",
        )
        runtime = None
        try:
            operator.start()
            self.assertTrue(operator.wait_connected(2.0))
            runtime = MayaRuntime(
                self.root,
                connector=_Connector(),
                notifier=lambda *_args: None,
                register_exit=False,
            ).start()

            self.assertTrue(runtime.wait_until_connected(3.0))
            self.assertTrue(opened.wait(2.0))
            self.assertEqual(len(server.clients), 2)
        finally:
            if runtime:
                runtime.stop()
            operator.stop()
            remove_session(record)
            server.stop()
            if previous is None:
                os.environ.pop("TACTIC_HANDLER_DISCOVERY_DIR", None)
            else:
                os.environ["TACTIC_HANDLER_DISCOVERY_DIR"] = previous

if __name__ == "__main__":
    unittest.main()
