"""Single-process ownership for the standalone TACTIC Handler client."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import (
    QIODevice,
    QLockFile,
    QObject,
    QStandardPaths,
    Signal,
)
from PySide6.QtNetwork import QLocalServer, QLocalSocket


def instance_server_name(
    application_name: str,
    isolation_path: str = "",
) -> str:
    """Return the stable local-server name for this application session."""
    name = str(application_name or "").strip()
    if not name:
        raise ValueError("Application name is required for single-instance mode")
    if not isolation_path:
        return name
    normalized_path = str(Path(isolation_path).resolve()).casefold()
    digest = hashlib.sha256(normalized_path.encode("utf-8")).hexdigest()[:16]
    return f"{name}-isolated-{digest}"


class SingleInstanceGuard(QObject):
    """Own one local server and activate the existing process on re-entry."""

    activationRequested = Signal()

    def __init__(
        self,
        server_name: str,
        parent: QObject | None = None,
        connect_timeout_ms: int = 500,
    ) -> None:
        super().__init__(parent)
        self._server_name = str(server_name or "").strip()
        if not self._server_name:
            raise ValueError("Local server name must not be empty")
        self._connect_timeout_ms = max(1, int(connect_timeout_ms))
        lock_root = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.TempLocation
        )
        lock_digest = hashlib.sha256(
            self._server_name.encode("utf-8")
        ).hexdigest()[:24]
        self._lock = QLockFile(
            str(Path(lock_root) / f"tactic-handler-{lock_digest}.lock")
        )
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._accept_connections)
        self._activation_handler: Callable[[], None] | None = None
        self._activation_pending = False
        self._started = False
        self._primary = False

    @property
    def is_primary(self) -> bool:
        return self._primary

    def start(self) -> bool:
        """Acquire ownership, or notify the existing owner and return False."""
        if self._started:
            return self._primary
        self._started = True
        if not self._lock.tryLock(0):
            self._notify_existing_instance()
            return False

        # The lock proves that no live owner exists, so removing a stale local
        # endpoint cannot disconnect another TACTIC Handler process.
        QLocalServer.removeServer(self._server_name)
        if self._server.listen(self._server_name):
            self._primary = True
            return True

        final_error = self._server.errorString()
        self._lock.unlock()
        self._started = False
        raise RuntimeError(
            "Unable to establish single-instance ownership for "
            f"{self._server_name}: {final_error}"
        )

    def set_activation_handler(self, handler: Callable[[], None]) -> None:
        """Install the window activation callback and replay an early request."""
        self._activation_handler = handler
        if not self._activation_pending:
            return
        self._activation_pending = False
        handler()

    def close(self) -> None:
        if self._server.isListening():
            self._server.close()
        if self._lock.isLocked():
            self._lock.unlock()
        self._primary = False
        self._started = False

    def _notify_existing_instance(self) -> bool:
        deadline = time.monotonic() + (self._connect_timeout_ms / 1000.0)
        while True:
            socket = QLocalSocket(self)
            socket.connectToServer(
                self._server_name,
                QIODevice.OpenModeFlag.WriteOnly,
            )
            if socket.waitForConnected(min(50, self._connect_timeout_ms)):
                socket.write(b"activate\n")
                socket.waitForBytesWritten(self._connect_timeout_ms)
                socket.disconnectFromServer()
                socket.deleteLater()
                return True
            socket.abort()
            socket.deleteLater()
            if time.monotonic() >= deadline:
                return False
            # The primary owns the lock before opening its activation socket.
            # Bound this startup race without starting a second runtime.
            time.sleep(0.01)

    def _accept_connections(self) -> None:
        accepted = False
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            accepted = True
            socket.disconnectFromServer()
            socket.deleteLater()
        if not accepted:
            return
        self.activationRequested.emit()
        if self._activation_handler is None:
            self._activation_pending = True
            return
        self._activation_handler()
