import unittest
from unittest.mock import patch

from modern_ui.controllers.connection import ConnectionMixin


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
    def test_native_cache_only_reads_never_fall_back_to_server(self):
        import thlib.tactic_classes as tc

        project = tc.Project({"code": "demo", "title": "Demo"})
        with (
            patch.object(tc.env_mode, "get_mode", return_value="standalone"),
            patch.object(tc, "env_read_config", return_value=None),
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

    def test_entrypoint_defers_startup_work_until_after_qml_load(self):
        from pathlib import Path

        source = Path("main_qml.py").read_text(encoding="utf-8")
        load_at = source.index("engine.load(")
        cache_at = source.index("controller.restore_cached_workspace")
        server_at = source.index("controller.bootstrap_server")
        self.assertLess(load_at, cache_at)
        self.assertLess(load_at, server_at)
        self.assertIn(
            "controller.project_changed.connect(server_update_service.start)",
            source,
        )
        self.assertIn(
            "controller.project_changed.connect(watch_folders_controller.reload)",
            source,
        )
        self.assertNotIn("watch_folders_controller.reload()", source)
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


if __name__ == "__main__":
    unittest.main()
