from __future__ import annotations

from collections import OrderedDict
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal

from modern_ui.request_metrics import request_metrics
from modern_ui.server_updates import ServerUpdateService
from modern_ui.skey_previews import SearchKeyPreviewResolver
from modern_ui.task_workspace.store import TaskWorkspaceStore
from modern_ui.workspace_models.windows import FloatingWindowModel
from tests.support.async_scenarios import DeferredWorker, MemorySettings


class _Application(QObject):
    project_changed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.current_project_code = "test_project"


class _RepositorySync(QObject):
    file_download_done = Signal(object)


class _PreviewApplication(QObject):
    def __init__(self):
        super().__init__()
        self.repository_sync = _RepositorySync(self)


class _Task:
    def __init__(self, code):
        self._info = {"code": code}

    def get_info(self):
        return dict(self._info)


class ControllerScenarioTests(unittest.TestCase):
    def test_selection_change_invalidates_inflight_task_result(self):
        store = TaskWorkspaceStore()
        store.set_scope("object", target_key="skey://demo/asset?code=A")
        first_request = store.begin_load()
        self.assertTrue(store.accepts(first_request))

        store.set_scope("object", target_key="skey://demo/asset?code=B")

        self.assertFalse(store.accepts(first_request))
        self.assertFalse(store.fail_load(first_request, "late failure"))
        self.assertEqual(store.error, "")

    def test_selection_worker_result_populates_canonical_store_once(self):
        store = TaskWorkspaceStore()
        request_id = store.begin_load()
        self.assertTrue(request_id)
        if store.accepts(request_id):
            store.apply_source([_Task("TASK001")], [], {"loaded": 1})
            store.finish_load()

        self.assertEqual([task.get_info()["code"] for task in store.task_objects()],
                         ["TASK001"])
        self.assertFalse(store.busy)

    def test_repeat_launch_is_rejected_while_task_store_is_busy(self):
        store = TaskWorkspaceStore()
        self.assertTrue(store.begin_load())
        self.assertEqual(store.begin_load(), "")

    def test_service_stop_cancels_worker_and_ignores_late_result(self):
        service = ServerUpdateService(_Application())
        worker = DeferredWorker()
        service._worker = worker
        service._running = True
        service._busy = True
        service._request_generation = 4
        batches = []
        service.batchReady.connect(batches.append)

        service.stop()
        service._ready_for(4, {"messages": [{"code": "LATE"}]})

        self.assertTrue(worker.cancelled)
        self.assertFalse(service.busy)
        self.assertEqual(batches, [])

    def test_repeat_server_poll_is_ignored_while_busy(self):
        service = ServerUpdateService(_Application())
        service._running = True
        service._busy = True
        with patch.object(service, "_schedule") as schedule:
            service.poll()
        schedule.assert_not_called()

    def test_window_state_survives_close_and_reopen(self):
        settings = MemorySettings()
        first = FloatingWindowModel(settings)
        first.show_window("messages")
        first.set_geometry("messages", 25, 30, 900, 700)
        first.close_window("messages")

        restored = FloatingWindowModel(settings)
        row = restored._row("messages")
        window = restored._windows[row]
        self.assertFalse(window.visible)
        self.assertEqual((window.x, window.y, window.width, window.height),
                         (25, 30, 900, 700))

    def test_profile_and_user_directory_keep_independent_geometry(self):
        settings = MemorySettings()
        first = FloatingWindowModel(settings)
        first.set_geometry("user_profile", 20, 30, 760, 620)
        first.set_geometry("users", 80, 50, 1180, 820)

        restored = FloatingWindowModel(settings)
        profile = restored._windows[restored._row("user_profile")]
        users = restored._windows[restored._row("users")]

        self.assertEqual(
            (profile.x, profile.y, profile.width, profile.height),
            (20, 30, 760, 620),
        )
        self.assertEqual(
            (users.x, users.y, users.width, users.height),
            (80, 50, 1180, 820),
        )

    def test_cache_hit_invalidation_and_refresh_are_observable(self):
        resolver = SearchKeyPreviewResolver(_PreviewApplication())
        search_key = "skey://sthpw/task?code=TASK001"
        scope = resolver._scope()
        resolver._cache = OrderedDict({
            (*scope, search_key): {
                **resolver._placeholder(search_key), "status": "ready",
            }
        })
        requested = []
        resolver.request_many = lambda values: requested.extend(values)
        request_metrics.reset()

        self.assertEqual(resolver.records_for_text(search_key)[0]["status"],
                         "ready")
        resolver.retry(search_key)
        resolver.records_for_text(search_key)

        metrics = request_metrics.snapshot()["cache.skey_preview"]
        self.assertEqual(metrics["cache_hits"], 1)
        self.assertEqual(metrics["cache_misses"], 1)
        self.assertEqual(requested, [search_key, search_key])


if __name__ == "__main__":
    unittest.main()
