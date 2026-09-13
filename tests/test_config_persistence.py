from __future__ import annotations

import threading
import time
import unittest
from unittest.mock import patch

from thlib.environment import Controls
from thlib.ui.config_persistence import ConfigWriteQueue


class ConfigWriteQueueTests(unittest.TestCase):
    def test_slow_write_does_not_block_the_calling_thread(self):
        started = threading.Event()
        release = threading.Event()
        received = []

        def writer(payload, **location):
            started.set()
            release.wait(2)
            received.append((payload, location, threading.get_ident()))

        queue = ConfigWriteQueue(writer=writer)
        payload = {"sections": [{"title": "Assets"}]}
        caller_thread = threading.get_ident()
        try:
            before = time.perf_counter()
            self.assertTrue(queue.submit(
                payload,
                filename="search_tabs",
                unique_id="cache",
                long_abs_path=True,
            ))
            submit_ms = (time.perf_counter() - before) * 1000
            self.assertTrue(started.wait(1))
            self.assertLess(submit_ms, 100)

            payload["sections"][0]["title"] = "Changed later"
            release.set()
            queue.flush()

            self.assertEqual(received[0][0], {
                "sections": [{"title": "Assets"}],
            })
            self.assertNotEqual(received[0][2], caller_thread)
        finally:
            release.set()
            queue.shutdown()

    def test_controls_can_publish_memory_state_without_sync_disk_io(self):
        controls = Controls()
        payload = {"demo": {"active_stype": "demo/assets"}}
        with patch("thlib.environment.env_write_config") as write:
            controls.set_checkin_out_projects(payload, persist=False)

        self.assertIs(controls.checkin_out_projects, payload)
        write.assert_not_called()

    def test_pending_writes_to_one_file_are_coalesced_to_latest_snapshot(self):
        started = threading.Event()
        release = threading.Event()
        received = []

        def writer(payload, **_location):
            received.append(payload["generation"])
            if payload["generation"] == 1:
                started.set()
                release.wait(2)

        queue = ConfigWriteQueue(writer=writer)
        location = {
            "filename": "search_tabs",
            "unique_id": "cache",
            "long_abs_path": True,
        }
        try:
            queue.submit({"generation": 1}, **location)
            self.assertTrue(started.wait(1))
            queue.submit({"generation": 2}, **location)
            queue.submit({"generation": 3}, **location)
            release.set()
            queue.flush()

            self.assertEqual(received, [1, 3])
        finally:
            release.set()
            queue.shutdown()


if __name__ == "__main__":
    unittest.main()
