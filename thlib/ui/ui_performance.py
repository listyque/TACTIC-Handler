"""Bounded, window-specific input/frame diagnostics; no per-delegate probes."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
import json
import time
import weakref

from PySide6.QtCore import QEvent, QObject, Property, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow

from .workspace_models.records import RecordListModel


def measure_ui(name: str) -> Callable:
    """Measure a controller boundary, never each row/binding evaluation."""
    def decorate(method):
        @wraps(method)
        def measured(self, *args, **kwargs):
            monitor = getattr(self, "_performance", None)
            if monitor is None:
                return method(self, *args, **kwargs)
            with monitor.measure(name):
                return method(self, *args, **kwargs)
        return measured
    return decorate


class UiPerformanceMonitor(QObject):
    changed = Signal()
    sampleFinished = Signal(int, object)
    frameReported = Signal(object, float, float)
    _dispatchRequested = Signal(int)
    _callbackRequested = Signal(object)
    LIMIT = 250
    INPUTS = {
        QEvent.MouseButtonPress: "Pointer press",
        QEvent.MouseButtonRelease: "Pointer release",
        QEvent.KeyPress: "Keyboard",
        QEvent.TouchBegin: "Touch",
        QEvent.TouchEnd: "Touch release",
        QEvent.Wheel: "Scroll",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = RecordListModel((
            "sampleId", "action", "window", "handlerMs", "frameMs", "readyMs",
            "details", "slow", "status",
        ), identity_role="sampleId")
        self._samples = deque(maxlen=self.LIMIT)
        self._pending = {}
        self._windows = {}
        self._serial = 0
        self._input_sample = 0
        self._visible = False
        # Diagnostics are opt-in: normal application use must not collect UI
        # timings until the user explicitly resumes recording.
        self._enabled = False
        self._installed = False
        self._feedback_callbacks = {}
        self._publish_timer = QTimer(self)
        self._publish_timer.setSingleShot(True)
        self._publish_timer.setInterval(100)
        self._publish_timer.timeout.connect(self._publish)
        self._expiry = QTimer(self)
        self._expiry.setInterval(1000)
        self._expiry.timeout.connect(self._expire)
        self.frameReported.connect(self._frame, Qt.QueuedConnection)
        self._dispatchRequested.connect(
            self._dispatch_done,
            Qt.ConnectionType.QueuedConnection,
        )
        self._callbackRequested.connect(
            self._run_callback,
            Qt.ConnectionType.QueuedConnection,
        )

    @Property(bool, notify=changed)
    def recording(self) -> bool:
        return self._enabled

    @Property(int, constant=True)
    def feedbackBudgetMs(self) -> int:
        return 50

    @Property("QVariantMap", notify=changed)
    def summary(self) -> dict[str, int | float]:
        values = sorted(row["frameMs"] for row in self._samples if row["frameMs"] >= 0)
        return {
            "count": len(self._samples),
            "overBudget": sum(value > 50 for value in values),
            "p95": round(values[min(len(values) - 1, int(len(values) * .95))], 1) if values else 0,
            "maximum": round(max(values), 1) if values else 0,
        }

    def install(self) -> None:
        app = QGuiApplication.instance()
        if app is not None and not self._installed:
            self._installed = True
            app.focusWindowChanged.connect(self._observe_input_window)
            for window in app.allWindows():
                self._observe_input_window(window)

    @Slot(object)
    def _observe_input_window(self, window):
        if isinstance(window, QQuickWindow):
            self._observe(window)

    def shutdown(self) -> None:
        app = QGuiApplication.instance()
        if app is not None and self._installed:
            app.focusWindowChanged.disconnect(self._observe_input_window)
        self._installed = False
        self._expiry.stop()
        self._publish_timer.stop()
        self._pending.clear()
        self._input_sample = 0
        self._feedback_callbacks.clear()
        for reference, callback, synchronizing, destroyed in self._windows.values():
            window = reference()
            if window is not None:
                try:
                    window.removeEventFilter(self)
                    window.frameSwapped.disconnect(callback)
                    window.beforeSynchronizing.disconnect(synchronizing)
                    window.destroyed.disconnect(destroyed)
                except (RuntimeError, TypeError):
                    pass  # The native window can already be destroyed at shutdown.
        self._windows.clear()

    def _observe(self, window):
        key = id(window)
        if key not in self._windows:
            sync_time = [0.0]
            def synchronizing():
                sync_time[0] = time.perf_counter()
            def presented():
                if self._pending or self._feedback_callbacks:
                    self.frameReported.emit(key, time.perf_counter(), sync_time[0])
            destroyed = lambda: self._forget_window(key)
            self._windows[key] = (weakref.ref(window), presented, synchronizing, destroyed)
            window.frameSwapped.connect(presented, Qt.DirectConnection)
            window.beforeSynchronizing.connect(synchronizing, Qt.DirectConnection)
            window.destroyed.connect(destroyed)
        if self._installed:
            # A global application filter also receives every delegate's paint,
            # layout and timer event. Diagnostics must not create that overhead.
            window.installEventFilter(self)
        return key

    def _forget_window(self, key):
        self._windows.pop(key, None)
        self._feedback_callbacks.pop(key, None)
        for serial, sample in list(self._pending.items()):
            if sample["windowKey"] == key:
                self._finish(serial, "Window closed")

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        kind = event.type()
        if not self._enabled or kind not in self.INPUTS or not isinstance(watched, QQuickWindow):
            return False
        # Typing content, key values and field text are deliberately not logged.
        if kind == QEvent.KeyPress and event.isAutoRepeat():
            return False
        key = self._observe(watched)
        if kind == QEvent.Wheel and any(
            row["windowKey"] == key and row["action"] == "Scroll"
            for row in self._pending.values()
        ):
            return False
        serial = self._begin(self.INPUTS[kind], watched.title(), key)
        self._input_sample = serial
        self._dispatchRequested.emit(serial)
        return False

    @Slot(object)
    def _run_callback(self, callback) -> None:
        callback()

    def _begin(self, action, window="", window_key=0):
        self._serial += 1
        serial = self._serial
        self._pending[serial] = {
            "sampleId": serial, "action": str(action), "window": str(window),
            "windowKey": window_key, "started": time.perf_counter(),
            "handlerMs": -1., "frameMs": -1., "readyMs": -1.,
            "details": "", "slow": False, "status": "Waiting for frame",
        }
        if len(self._pending) > 64:
            self._finish(next(iter(self._pending)), "Superseded")
        if not self._expiry.isActive():
            self._expiry.start()
        return serial

    def _dispatch_done(self, serial):
        if self._input_sample == serial:
            self._input_sample = 0
        row = self._pending.get(serial)
        if row is not None:
            row["handlerMs"] = (time.perf_counter() - row["started"]) * 1000
            if row["frameMs"] >= 0:
                self._finish(serial, "Frame presented")

    @Slot(object, float, float)
    def _frame(self, window_key, timestamp, synchronized_at=None):
        synchronized_at = timestamp if synchronized_at is None else synchronized_at
        for serial, row in list(self._pending.items()):
            if row["windowKey"] != window_key or row["started"] > synchronized_at:
                continue
            if row["frameMs"] < 0:
                row["frameMs"] = (timestamp - row["started"]) * 1000
            if row["handlerMs"] >= 0:
                if row.get("operation"):
                    if row.get("committedAt", timestamp) > synchronized_at:
                        continue
                    row["readyMs"] = (timestamp - row["started"]) * 1000
                self._finish(serial, "Frame presented")
        callbacks = self._feedback_callbacks.get(window_key, [])
        ready = [entry for entry in callbacks if entry[0] <= synchronized_at]
        remaining = [entry for entry in callbacks if entry[0] > synchronized_at]
        if remaining:
            self._feedback_callbacks[window_key] = remaining
        else:
            self._feedback_callbacks.pop(window_key, None)
        for _, callback in ready:
            callback()

    def after_feedback(self, callback: Callable[[], None]) -> None:
        """Yield expensive navigation until the source window paints feedback."""
        window = QGuiApplication.focusWindow()
        if not isinstance(window, QQuickWindow) or not window.isExposed():
            self._callbackRequested.emit(callback)
            return
        key = self._observe(window)
        entry = (time.perf_counter(), callback)
        self._feedback_callbacks.setdefault(key, []).append(entry)
        window.update()
        # The user can minimize/close the window before the next frame.
        def fallback():
            pending = self._feedback_callbacks.get(key, [])
            if entry in pending:
                pending.remove(entry)
                if not pending:
                    self._feedback_callbacks.pop(key, None)
                callback()
        QTimer.singleShot(250, self, fallback)

    @contextmanager
    def measure(self, action: str) -> Iterator[None]:
        if not self._enabled:
            yield
            return
        # Background publications have no owning input window. Recording their
        # CPU work is useful; attributing a random focused window's frame to
        # them would falsely report that the consuming UI was ready.
        source = self._pending.get(self._input_sample, {})
        serial = self._begin(action, source.get("window", ""), source.get("windowKey", 0))
        self._pending[serial]["operation"] = True
        try:
            yield
        finally:
            self.end_operation(serial)

    def begin_operation(self, action: str) -> int:
        if not self._enabled:
            return 0
        window = QGuiApplication.focusWindow()
        key = self._observe(window) if isinstance(window, QQuickWindow) else 0
        serial = self._begin(action, window.title() if window else "", key)
        self._pending[serial]["operation"] = True
        return serial

    def end_operation(self, serial: int) -> None:
        row = self._pending.get(serial)
        if row is None:
            return
        row["handlerMs"] = (time.perf_counter() - row["started"]) * 1000
        row["committedAt"] = time.perf_counter()
        if not row["windowKey"]:
            self._finish(serial, "Controller work")

    def cancel_operation(self, serial: int) -> None:
        self._finish(serial, "Superseded")

    def set_details(self, serial: int, details: dict) -> None:
        row = self._pending.get(serial)
        if row is not None:
            row["details"] = json.dumps(details, ensure_ascii=False)

    def _finish(self, serial, status):
        row = self._pending.pop(serial, None)
        if row is None:
            return
        row.pop("started", None)
        row.pop("windowKey", None)
        row.pop("committedAt", None)
        row["status"] = status
        row["slow"] = max(row["handlerMs"], row["frameMs"]) > 50
        self._samples.appendleft(row)
        self.sampleFinished.emit(serial, dict(row))
        self._schedule_publish()
        if not self._pending:
            self._expiry.stop()

    def _expire(self):
        now = time.perf_counter()
        for serial, row in list(self._pending.items()):
            if now - row["started"] > 5:
                # A timeout is NOT a rendered frame or successful readiness.
                self._finish(serial, "No frame")

    def _schedule_publish(self):
        if self._visible and not self._publish_timer.isActive():
            self._publish_timer.start()

    def _publish(self):
        if self._visible:
            self.model.replace(list(self._samples))
            self.changed.emit()

    @Slot(bool)
    def set_visible(self, value: bool) -> None:
        self._visible = bool(value)
        if self._visible:
            self._publish()

    @Slot(bool)
    def set_recording(self, value: bool) -> None:
        self._enabled = bool(value)
        self.changed.emit()

    @Slot()
    def clear(self) -> None:
        self._samples.clear()
        self.model.clear()
        self.changed.emit()

    @Slot()
    def copy_results(self) -> None:
        QGuiApplication.clipboard().setText(json.dumps(
            list(self._samples), ensure_ascii=False, indent=2,
        ))
