"""Explicit background execution; importing this module never imports Qt."""

from __future__ import annotations

from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
import logging
import sys
import threading
from typing import Callable, Generic, TypeVar
import uuid

from .errors import BlockingCallError, NotReady, QueueFull


T = TypeVar("T")
_logger = logging.getLogger("tactic_handler_api.operations")
_progress = ContextVar("handler_api_progress", default=None)
_blocking_calls_allowed = ContextVar(
    "handler_api_blocking_calls_allowed", default=False
)


class Progress:
    def __init__(self):
        self._lock = threading.Lock()
        self._value = None
        self._subscriptions = []
        self._closed = False

    def publish(self, value):
        from copy import deepcopy

        with self._lock:
            self._value = deepcopy(value)
            subscriptions = tuple(self._subscriptions)
        for subscription in subscriptions:
            subscription._deliver(deepcopy(value))

    def subscribe(self, callback, dispatch=None):
        subscription = Subscription(callback, dispatch)
        with self._lock:
            if self._closed:
                subscription.close()
            else:
                self._subscriptions.append(subscription)
        return subscription

    def close(self):
        with self._lock:
            self._closed = True
            subscriptions, self._subscriptions = self._subscriptions, []
        for subscription in subscriptions:
            subscription.close()


def report_progress(value) -> None:
    progress = _progress.get()
    if progress is not None:
        progress.publish(value)


@contextmanager
def allow_blocking_calls():
    """Allow one explicitly synchronous integration flow to use the API."""
    token = _blocking_calls_allowed.set(True)
    try:
        yield
    finally:
        _blocking_calls_allowed.reset(token)


def check_blocking_call() -> None:
    """Reject known UI threads without initializing a UI or a DCC runtime."""
    if _blocking_calls_allowed.get():
        return
    for name in ("PySide6.QtCore", "PySide2.QtCore", "PyQt6.QtCore", "PyQt5.QtCore"):
        core = sys.modules.get(name)
        if core is not None:
            app = core.QCoreApplication.instance()
            if app is not None and core.QThread.currentThread() == app.thread():
                raise BlockingCallError(
                    "Use th.submit() instead of waiting on the Qt thread"
                )
    if (
        "maya.cmds" in sys.modules
        and threading.current_thread() is threading.main_thread()
    ):
        raise BlockingCallError("Use th.submit() instead of waiting on the Maya thread")


class Subscription:
    """Disconnect one callback without changing the underlying operation."""

    def __init__(self, callback, dispatch=None, *, once=False):
        if not callable(callback) or (dispatch is not None and not callable(dispatch)):
            raise TypeError("callback and dispatch must be callable")
        self._callback = callback
        self._dispatch = dispatch
        self._lock = threading.RLock()
        self._once = once
        self.error = None

    def close(self) -> None:
        with self._lock:
            self._callback = None

    def _deliver(self, value) -> None:
        def invoke():
            with self._lock:
                callback = self._callback
            if callback is not None:
                try:
                    callback(value)
                except Exception as error:
                    self._failed(error)
                finally:
                    if self._once:
                        self.close()

        try:
            if self._dispatch is None:
                invoke()
            else:
                self._dispatch(invoke)
        except Exception as error:
            self._failed(error)
            self.close()

    def _failed(self, error):
        # Observers cannot turn a successful write into a failed operation.
        # Keep the full exception for inspection without leaking its payload.
        self.error = error
        _logger.error(
            "API callback failed (%s); inspect subscription.error", type(error).__name__
        )


class Operation(Generic[T]):
    """One Future with explicit nonblocking inspection and guarded waiting."""

    def __init__(
        self, future: Future[T], operation_id: str | None = None, progress=None
    ):
        self.id = operation_id or uuid.uuid4().hex
        self._future = future
        self._progress = progress or Progress()
        future.add_done_callback(lambda _future: self._progress.close())

    def on_progress(self, callback, *, dispatch=None) -> Subscription:
        return self._progress.subscribe(callback, dispatch)

    @property
    def done(self) -> bool:
        return self._future.done()

    @property
    def state(self) -> str:
        if self._future.cancelled():
            return "cancelled"
        if self.done:
            return "failed" if self._future.exception() is not None else "finished"
        return "running" if self._future.running() else "queued"

    def result(self) -> T:
        if not self.done:
            raise NotReady(f"Operation {self.id} is not finished")
        return self._future.result()

    def wait(self, timeout: float | None = None) -> T:
        if not self.done:
            check_blocking_call()
        return self._future.result(timeout=timeout)

    def cancel(self) -> bool:
        """Cancel pending work only; never imply rollback of a running write."""
        return self._future.cancel()

    def on_done(self, callback: Callable[[T], None], *, dispatch=None) -> Subscription:
        subscription = Subscription(callback, dispatch, once=True)

        def completed(future):
            if not future.cancelled() and future.exception() is None:
                subscription._deliver(future.result())
            else:
                subscription.close()

        self._future.add_done_callback(completed)
        return subscription

    def on_error(
        self, callback: Callable[[Exception], None], *, dispatch=None
    ) -> Subscription:
        subscription = Subscription(callback, dispatch, once=True)

        def completed(future):
            if future.cancelled():
                subscription._deliver(CancelledError())
            elif future.exception() is not None:
                subscription._deliver(future.exception())
            else:
                subscription.close()

        self._future.add_done_callback(completed)
        return subscription


class Executor:
    """A bounded, lazy, session-owned executor; no event loop is required."""

    def __init__(self, max_workers: int = 4, max_pending: int = 64):
        if max_workers < 1 or max_pending < max_workers:
            raise ValueError("Expected 1 <= max_workers <= max_pending")
        self._max_workers = max_workers
        self._slots = threading.BoundedSemaphore(max_pending)
        self._lock = threading.Lock()
        self._pool = None
        self._closed = False
        self._running = threading.local()

    @property
    def running_here(self) -> bool:
        return bool(getattr(self._running, "active", False))

    def submit(self, function: Callable[..., T], *args, **kwargs) -> Operation[T]:
        if not callable(function):
            raise TypeError("submit() expects a callable, not its result")
        if getattr(self._running, "active", False):
            raise BlockingCallError(
                "Call sequential methods inside a submitted function"
            )
        if not self._slots.acquire(blocking=False):
            raise QueueFull("The API executor is full; wait for a pending operation")
        try:
            context = copy_context()
            progress = Progress()

            def in_context():
                token = _progress.set(progress)
                try:
                    return function(*args, **kwargs)
                finally:
                    _progress.reset(token)

            def execute():
                self._running.active = True
                try:
                    return context.run(in_context)
                finally:
                    self._running.active = False

            with self._lock:
                if self._closed:
                    raise RuntimeError("The API session is closed")
                if self._pool is None:
                    self._pool = ThreadPoolExecutor(
                        max_workers=self._max_workers,
                        thread_name_prefix="handler-api",
                    )
                future = self._pool.submit(execute)
        except BaseException:
            self._slots.release()
            raise
        future.add_done_callback(lambda _future: self._slots.release())
        operation = Operation(future, progress=progress)

        def report_failure(completed):
            if not completed.cancelled() and completed.exception() is not None:
                # The complete exception remains on Operation. Do not print unredacted
                # server payloads or credentials through the generic Python logger.
                _logger.error(
                    "Operation %s failed (%s); inspect operation.result()",
                    operation.id,
                    type(completed.exception()).__name__,
                )

        future.add_done_callback(report_failure)
        return operation

    def close(self, *, wait: bool = True) -> None:
        if wait:
            check_blocking_call()
        if getattr(self._running, "active", False):
            raise BlockingCallError("An operation cannot close its own executor")
        with self._lock:
            self._closed = True
            pool = self._pool
        if pool is not None:
            pool.shutdown(wait=wait, cancel_futures=True)
