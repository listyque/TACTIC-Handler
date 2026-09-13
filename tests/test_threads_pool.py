import threading
import time
import unittest

from tests.qt_application import gui_test_application
from thlib.pool import ThreadsPool


class ThreadsPoolTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def _wait(self, predicate, timeout=2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return True
            time.sleep(0.005)
        return predicate()

    def test_max_thread_count_can_be_changed_at_runtime(self):
        pool = ThreadsPool(max_threads=1)

        pool.set_max_threads(4)

        self.assertEqual(pool.max_threads, 4)
        self.assertEqual(pool._pool.maxThreadCount(), 4)

    def test_cancelled_queued_worker_does_not_run(self):
        pool = ThreadsPool(max_threads=1)
        pool.start()
        release = threading.Event()
        calls = []

        first = pool.add_task(lambda: release.wait(1.0))
        second = pool.add_task(lambda: calls.append("second"))
        first.start()
        second.start()
        second.cancel()
        release.set()

        self.assertTrue(self._wait(lambda: not pool._active_workers))
        self.assertEqual([], calls)
        self.assertTrue(pool.exit(1000))

    def test_pool_requires_explicit_reopen_after_exit(self):
        pool = ThreadsPool(max_threads=1)
        pool.start()
        self.assertTrue(pool.exit(1000))
        self.assertFalse(pool.start())
        self.assertIsNone(pool.add_task(lambda: None))
        self.assertTrue(pool.reopen())
        self.assertTrue(pool.start())
        worker = pool.add_task(lambda: "ok")
        results = []
        worker.result.connect(results.append)
        worker.start()
        self.assertTrue(self._wait(lambda: bool(results)))
        self.assertEqual(["ok"], results)
        self.assertTrue(pool.exit(1000))

    def test_cancelled_running_worker_suppresses_late_error(self):
        pool = ThreadsPool(max_threads=1)
        pool.start()
        entered = threading.Event()
        release = threading.Event()
        errors = []

        def fail_late():
            entered.set()
            release.wait(1.0)
            raise RuntimeError("stale failure")

        worker = pool.add_task(fail_late)
        worker.error.connect(errors.append)
        worker.start()
        self.assertTrue(entered.wait(1.0))
        worker.cancel()
        release.set()
        self.assertTrue(self._wait(lambda: not pool._active_workers))
        self.assertEqual([], errors)
        self.assertTrue(pool.exit(1000))

    def test_cancelled_worker_emits_settled_after_function_returns(self):
        pool = ThreadsPool(max_threads=1)
        pool.start()
        entered = threading.Event()
        release = threading.Event()
        settled = []

        def wait_for_release():
            entered.set()
            release.wait(1.0)

        worker = pool.add_task(wait_for_release)
        worker.settled.connect(lambda value: settled.append(value))
        worker.start()
        self.assertTrue(entered.wait(1.0))
        worker.cancel()
        self.app.processEvents()
        self.assertEqual([], settled)
        release.set()
        self.assertTrue(self._wait(lambda: bool(settled)))
        self.assertIs(worker, settled[0])
        self.assertTrue(pool.exit(1000))


if __name__ == "__main__":
    unittest.main()
