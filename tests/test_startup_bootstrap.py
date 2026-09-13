import io
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from thlib.ui.controllers.connection import ConnectionMixin


class _Signal:
    def __init__(self):
        self.connections = []

    def connect(self, callback, *_args):
        self.connections.append(callback)


class _Worker:
    def __init__(self):
        self.result = _Signal()
        self.error = _Signal()
        self.data = None
        self.started = False

    def add_result_data(self, data):
        self.data = data

    def start(self):
        self.started = True


class _Pool:
    is_stopped = False

    def __init__(self):
        self.worker = _Worker()
        self.task = None
        self.args = ()

    def add_task(self, task, *args):
        self.task = task
        self.args = args
        return self.worker


class _Settings:
    def value(self, _key, default=None, type=None):
        return type("demo") if type else "demo"

    def get(self, _key, default=None):
        return "demo"


class _Controller(ConnectionMixin):
    def __init__(self):
        self._settings = _Settings()
        self._bootstrap_request_id = ""
        self._bootstrap_worker = None
        self._bootstrap_started_at = 0.0
        self.loading = []
        self.states = []

    def _set_loading(self, value, message=""):
        self.loading.append((value, message))

    def _set_server_state(self, state, message):
        self.states.append((state, message))

    def _request_authentication(self):
        raise AssertionError("Authentication was not expected")

    def _bootstrap_failed(self, error):
        raise AssertionError(f"Bootstrap failed unexpectedly: {error}")


class StartupBootstrapTests(unittest.TestCase):
    def test_qt_bootstrap_logging_survives_missing_stderr(self):
        from thlib.ui.application import (
            _bootstrap_message_handler,
            _write_stderr,
        )

        stream = io.StringIO()
        with patch.object(sys, "stderr", stream):
            self.assertTrue(_write_stderr("Qt startup message"))
        self.assertEqual(stream.getvalue(), "Qt startup message\n")

        with (
            patch.object(sys, "stderr", None),
            patch.object(sys, "__stderr__", None),
        ):
            self.assertFalse(_write_stderr("late Qt message"))
            _bootstrap_message_handler(None, None, "late Qt message")

    def test_native_cache_only_reads_never_fall_back_to_server(self):
        import thlib.tactic_classes as tc
        from thlib import server_cache

        project = tc.Project({"code": "demo", "title": "Demo"})
        with (
            patch.object(tc.env_mode, "get_mode", return_value="standalone"),
            patch.object(server_cache, "read_entry", return_value=None),
            patch.object(
                tc,
                "execute_procedure_serverside",
                side_effect=AssertionError("cache restore touched server"),
            ),
        ):
            self.assertEqual(
                tc.get_all_projects_and_logins(cache_only=True), {}
            )
            self.assertEqual(
                project.query_search_types(cache_only=True), []
            )

    def test_warm_server_bootstrap_initializes_repository_paths(self):
        import thlib.tactic_classes as tc
        from thlib.environment import env_mode

        with (
            patch.object(tc, "get_all_projects_and_logins", return_value={}),
            patch.object(env_mode, "set_online") as set_online,
        ):
            ConnectionMixin._load_projects(force=False)

        set_online.assert_called_once_with()

    def test_entrypoint_defers_startup_work_until_after_qml_load(self):
        from pathlib import Path

        source = Path("thlib/ui/application.py").read_text(encoding="utf-8")
        load_at = source.index("engine.load(")
        cache_at = source.index("controller.restore_cached_workspace")
        server_at = source.index("controller.bootstrap_server")
        self.assertLess(load_at, cache_at)
        self.assertLess(load_at, server_at)
        self.assertIn(
            "controller.authentication_changed.connect(\n"
            "            runtime.server_updates.sync_authentication\n"
            "        )",
            source,
        )
        startup = source[source.index("def start_after_first_frame"):]
        self.assertNotIn(
            "runtime.server_updates.sync_authentication()",
            startup.split("root_window.frameSwapped.connect", 1)[0],
        )
        self.assertNotIn(
            "controller.project_changed.connect(runtime.server_updates.start)",
            source,
        )
        self.assertIn(
            "controller.project_changed.connect(runtime.watch_folders.reload)",
            source,
        )
        self.assertNotIn("runtime.watch_folders.reload()", source)
    def test_bootstrap_enqueues_server_work_without_running_it_inline(self):
        from thlib.environment import env_inst, env_server

        controller = _Controller()
        pool = _Pool()
        with (
            patch.object(env_inst, "server_pool", pool),
            patch.object(
                env_server, "get_server", return_value="http://server"
            ),
            patch.object(env_server, "get_ticket", return_value="ticket"),
        ):
            controller.bootstrap_server()

        self.assertIsNotNone(pool.task)
        self.assertEqual(pool.args, ("demo",))
        self.assertTrue(pool.worker.started)
        self.assertIs(controller._bootstrap_worker, pool.worker)
        self.assertEqual(
            controller.states[-1],
            ("connecting", "Loading TACTIC projects and workspace"),
        )
        self.assertTrue(controller.loading[-1][0])

    def test_bootstrap_reuses_reference_cache_without_server_changes(self):
        import thlib.tactic_classes as tc
        from thlib import server_cache
        from thlib.environment import env_inst, env_server

        controller = _Controller()
        project = SimpleNamespace(
            get_code=lambda: "demo",
            get_title=lambda: "Demo",
            get_info=lambda: {},
            is_template=lambda: False,
            is_builtin=lambda: False,
        )
        login = SimpleNamespace(
            get_display_name=lambda: "Artist",
            get_info=lambda: {"__is_admin__": False},
        )
        with (
            patch.object(
                tc, "get_server_updates",
                return_value={"cacheCursor": "2026-09-08|cursor"},
            ),
            patch.object(
                server_cache, "read_cursor", return_value="existing-cursor"
            ),
            patch.object(server_cache, "apply_change_batch", return_value={}),
            patch.object(server_cache, "write_cursor") as write_cursor,
            patch.object(
                controller, "_load_projects", return_value=[project]
            ) as load_projects,
            patch.object(
                controller, "_prepare_project_selection",
                return_value=("demo", "Demo", [], project),
            ) as prepare_project,
            patch.object(env_inst, "logins", {"artist": login}),
            patch.object(env_server, "get_user", return_value="artist"),
        ):
            controller._bootstrap_server_task("demo")

        load_projects.assert_called_once_with(force=False)
        prepare_project.assert_called_once_with(
            "demo", "Demo", force_search_types=False
        )
        write_cursor.assert_called_once_with(
            "server_changes", "2026-09-08|cursor", "demo"
        )

    def test_login_change_does_not_reload_project_search_types(self):
        import thlib.tactic_classes as tc
        from thlib import server_cache
        from thlib.environment import env_inst, env_server

        controller = _Controller()
        project = SimpleNamespace(
            get_code=lambda: "demo",
            get_title=lambda: "Demo",
            get_info=lambda: {},
            is_template=lambda: False,
            is_builtin=lambda: False,
        )
        login = SimpleNamespace(
            get_display_name=lambda: "Artist",
            get_info=lambda: {"__is_admin__": False},
        )
        with (
            patch.object(
                tc, "get_server_updates",
                return_value={"cacheCursor": "new-cursor"},
            ),
            patch.object(
                server_cache, "read_cursor", return_value="old-cursor"
            ),
            patch.object(
                server_cache, "apply_change_batch",
                return_value={"sthpw": ["reference"]},
            ),
            patch.object(server_cache, "write_cursor"),
            patch.object(
                controller, "_load_projects", return_value=[project]
            ) as load_projects,
            patch.object(
                controller, "_prepare_project_selection",
                return_value=("demo", "Demo", [], project),
            ) as prepare_project,
            patch.object(env_inst, "logins", {"artist": login}),
            patch.object(env_server, "get_user", return_value="artist"),
        ):
            controller._bootstrap_server_task("demo")

        load_projects.assert_called_once_with(force=True)
        prepare_project.assert_called_once_with(
            "demo", "Demo", force_search_types=False
        )


if __name__ == "__main__":
    unittest.main()
