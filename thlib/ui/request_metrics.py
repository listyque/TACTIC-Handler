"""Lightweight request and cache metrics used by diagnostics and tests."""

from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import threading
import time


@dataclass
class RequestMetric:
    calls: int = 0
    failures: int = 0
    duration_seconds: float = 0.0
    response_bytes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


class RequestMetrics:
    """Thread-safe process metrics with intentionally tiny overhead."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._metrics: dict[str, RequestMetric] = defaultdict(RequestMetric)

    def reset(self) -> None:
        with self._lock:
            self._metrics.clear()

    def record_request(
        self, name: str, duration_seconds: float,
        response_bytes: int = 0, failed: bool = False,
    ) -> None:
        with self._lock:
            metric = self._metrics[str(name)]
            metric.calls += 1
            metric.failures += int(bool(failed))
            metric.duration_seconds += max(0.0, float(duration_seconds or 0.0))
            metric.response_bytes += max(0, int(response_bytes or 0))

    def record_cache(self, name: str, hit: bool) -> None:
        with self._lock:
            metric = self._metrics[str(name)]
            if hit:
                metric.cache_hits += 1
            else:
                metric.cache_misses += 1

    def snapshot(self) -> dict[str, dict]:
        with self._lock:
            return {
                name: asdict(metric)
                for name, metric in sorted(self._metrics.items())
            }

    @contextmanager
    def measure(self, name: str):
        started_at = time.perf_counter()
        state = {"response_bytes": 0, "failed": False}
        try:
            yield state
        except Exception:
            state["failed"] = True
            raise
        finally:
            self.record_request(
                name,
                time.perf_counter() - started_at,
                state["response_bytes"],
                state["failed"],
            )
request_metrics = RequestMetrics()
