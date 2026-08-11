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
