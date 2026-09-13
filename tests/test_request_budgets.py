from __future__ import annotations

from collections import OrderedDict
import json
from pathlib import Path
import unittest

from PySide6.QtCore import QObject, Signal

from thlib.ui.request_metrics import RequestMetrics, request_metrics
from thlib.ui.skey_previews import SearchKeyPreviewResolver
from thlib.ui.workspace_models.windows import FloatingWindowModel
from tests.support.async_scenarios import MemorySettings


ROOT = Path(__file__).resolve().parents[1]
BUDGETS = json.loads(
    (ROOT / "tests" / "contracts" / "request_budgets.json").read_text(
        encoding="utf-8"
    )
)


class _RepositorySync(QObject):
    file_download_done = Signal(object)


class _Application(QObject):
    def __init__(self):
        super().__init__()
        self.repository_sync = _RepositorySync(self)


class RequestBudgetTests(unittest.TestCase):
    def setUp(self):
        request_metrics.reset()

    def test_metrics_track_count_duration_size_and_failures(self):
        metrics = RequestMetrics()
        metrics.record_request("xmlrpc.query", 0.25, 4096)
        metrics.record_request("xmlrpc.query", 0.10, failed=True)
        snapshot = metrics.snapshot()["xmlrpc.query"]
        self.assertEqual(snapshot["calls"], 2)
        self.assertEqual(snapshot["failures"], 1)
        self.assertEqual(snapshot["response_bytes"], 4096)
        self.assertAlmostEqual(snapshot["duration_seconds"], 0.35)

    def test_reopening_a_window_has_zero_xmlrpc_budget(self):
        model = FloatingWindowModel(MemorySettings())
        model.show_window("messages")
        model.close_window("messages")
        model.show_window("messages")
        calls = sum(
            metric["calls"] for name, metric in request_metrics.snapshot().items()
            if name.startswith("xmlrpc.")
        )
        self.assertLessEqual(calls, BUDGETS["window.reopen"]["xmlrpcCalls"])

    def test_skey_preview_reuse_stays_inside_cache_budget(self):
        resolver = SearchKeyPreviewResolver(_Application())
        search_key = "skey://sthpw/task?code=TASK001"
        resolver._cache = OrderedDict({
            (*resolver._scope(), search_key): {
                **resolver._placeholder(search_key), "status": "ready",
            }
        })
        resolver.request_many = lambda _values: None
        resolver.records_for_text(search_key)
        resolver.records_for_text(search_key)

        metric = request_metrics.snapshot()["cache.skey_preview"]
        budget = BUDGETS["cache.skey_preview"]
        self.assertGreaterEqual(metric["cache_hits"], budget["minimumCacheHits"])
        self.assertLessEqual(metric["cache_misses"], budget["cacheMisses"])

    def test_one_batch_is_one_logical_server_poll(self):
        metrics = RequestMetrics()
        with metrics.measure("server.poll") as state:
            state["response_bytes"] = 128
        snapshot = metrics.snapshot()["server.poll"]
        self.assertEqual(snapshot["calls"], BUDGETS["server.poll"]["calls"])
        self.assertEqual(snapshot["response_bytes"], 128)


if __name__ == "__main__":
    unittest.main()
