"""Frame timing and transient-motion lifecycle for Search Tab switches."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, Property, QTimer, Signal

from ..request_metrics import request_metrics


class SearchTabSwitchMonitor(QObject):
    """Own one cached presentation swap through its first rendered frame."""

    changed = Signal()
    committed = Signal(int)

    def __init__(self, debug_log=None, parent: QObject | None = None, *, performance=None) -> None:
        super().__init__(parent)
        self._debug_log = debug_log
        self._switching = False
        self._serial = 0
        self._started_at = 0.0
        self._metrics = {}
        self._performance = performance
        self._sample = 0
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.setInterval(5000)
        self._timeout.timeout.connect(lambda: self._abandon(self._serial))
        if performance is not None:
            performance.sampleFinished.connect(self._sample_finished)
            performance.changed.connect(self.changed)

    @property
    def started_at(self) -> float:
        return self._started_at

    @Property(bool, notify=changed)
    def switching(self) -> bool:
        return self._switching

    @Property(bool, notify=changed)
    def recording(self) -> bool:
        return bool(self._performance and self._performance.recording)

    @Property("QVariantMap", notify=changed)
    def metrics(self) -> dict:
        return dict(self._metrics)

    def begin(self, tab_title: str) -> int:
        self.cancel()
        self._serial += 1
        serial = self._serial
        self._started_at = time.perf_counter()
        self._metrics = {"serial": serial, "tab": str(tab_title or "")}
        self._switching = True
        self.changed.emit()
        if self._performance is not None:
            self._sample = self._performance.begin_operation("Search tab: " + str(tab_title))
        # A hidden/minimized window may not produce frameSwapped. Never leave
        # transient motion disabled indefinitely in that case.
        if self._sample:
            self._timeout.start()
        return serial

    def commit(
        self,
        serial: int,
        metrics: dict[str, float | int | str],
    ) -> None:
        if serial != self._serial:
            return
        self._metrics = {**self._metrics, **metrics}
        self.committed.emit(serial)
        if self._performance is not None:
            self._performance.set_details(self._sample, self._metrics)
            self._performance.end_operation(self._sample)
            if not self._sample:
                # Pausing diagnostics must not leave navigation in its transient
                # switching state until the missing-frame timeout.
                self._switching = False
                self._timeout.stop()
                self.changed.emit()

    def _sample_finished(self, sample, record):
        if sample != self._sample or not self._switching:
            return
        if record["readyMs"] >= 0:
            self._finish(self._serial, record["readyMs"])
        else:
            self._abandon(self._serial)

    def _abandon(self, serial):
        if serial != self._serial or not self._switching:
            return
        self._switching = False
        self._timeout.stop()
        self._metrics["noFrame"] = True
        self.changed.emit()

    def record_phase(self, name: str, duration_ms: float) -> None:
        if not self._switching:
            return
        self._metrics[str(name)] = round(max(0.0, duration_ms), 3)

    def cancel(self) -> None:
        """Invalidate a navigation request superseded before its feedback frame."""
        if not self._switching:
            return
        self._serial += 1
        self._switching = False
        self._timeout.stop()
        self._metrics = {**self._metrics, "serial": self._serial}
        if self._performance is not None:
            self._performance.cancel_operation(self._sample)
        self.changed.emit()

    def _finish(self, serial, elapsed_ms):
        if serial != self._serial or not self._switching:
            return
        metrics = dict(self._metrics)
        metrics["firstFrameMs"] = round(elapsed_ms, 3)
        metrics["afterPythonMs"] = round(max(
            0.0,
            elapsed_ms - float(metrics.get("pythonMs", 0.0) or 0.0),
        ), 3)
        self._metrics = metrics
        self._switching = False
        self._timeout.stop()
        self.changed.emit()
        request_metrics.record_request(
            "ui.search_tab_switch",
            elapsed_ms / 1000,
        )
        if not self._debug_log:
            return
        details = "; ".join(
            f"{key}={value}"
            for key, value in metrics.items()
            if key not in {"serial", "tab"}
        )
        self._debug_log.log(
            "LOG",
            f"Search tab ready: {metrics.get('tab', '')}",
            group="performance/search-tabs",
            source="Search workspace",
            duration=elapsed_ms / 1000,
            details=details,
        )
