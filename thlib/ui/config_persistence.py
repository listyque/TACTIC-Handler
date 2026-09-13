"""Non-blocking persistence for immutable UI configuration snapshots."""

from __future__ import annotations

from concurrent.futures import CancelledError, Future, ThreadPoolExecutor, wait
from copy import deepcopy
import threading
import traceback
from typing import Callable

from PySide6.QtCore import QObject, Signal

from thlib.environment import env_write_config


class ConfigWriteQueue(QObject):
    """Serialize configuration writes away from the Qt presentation thread."""

    failed = Signal(str, str)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        writer: Callable = env_write_config,
    ) -> None:
        super().__init__(parent)
        self._writer = writer
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="tactic-config",
        )
        self._lock = threading.RLock()
        self._futures: set[Future] = set()
        self._latest_by_location: dict[tuple, Future] = {}
        self._closed = False

    def submit(self, payload, **location) -> bool:
        """Queue an owned snapshot while preserving write order."""
        snapshot = deepcopy(payload)
        location = dict(location)
        location_key = tuple(sorted(location.items()))
        with self._lock:
            if self._closed:
                return False
            previous = self._latest_by_location.get(location_key)
            if previous is not None and previous.cancel():
                self._futures.discard(previous)
            future = self._executor.submit(
                self._writer,
                snapshot,
                **location,
            )
            self._futures.add(future)
            self._latest_by_location[location_key] = future
        future.add_done_callback(
            lambda completed: self._settled(location_key, completed)
        )
        return True

    def _settled(self, location_key: tuple, future: Future) -> None:
        with self._lock:
            self._futures.discard(future)
            if self._latest_by_location.get(location_key) is future:
                self._latest_by_location.pop(location_key, None)
        try:
            future.result()
        except CancelledError:
            return
        except Exception as error:  # preserve the full persistence failure
            self.failed.emit(str(error), traceback.format_exc())

    def flush(self) -> None:
        """Wait for snapshots accepted before this call."""
        while True:
            with self._lock:
                futures = tuple(self._futures)
            if not futures:
                return
            wait(futures)

    def shutdown(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._executor.shutdown(wait=True, cancel_futures=False)
