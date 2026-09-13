import sys
import traceback
import logging

from thlib.side.Qt import QtCore


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(message)s"
)

logger = logging.getLogger("connection.log")


class _OperationRunnable(QtCore.QRunnable):
    """Run an OperationWorker without moving its signal facade."""

    def __init__(self, worker):
        super(_OperationRunnable, self).__init__()
        self.worker = worker
        self.setAutoDelete(True)

    def run(self):
        self.worker._execute()


class ThreadsPool(QtCore.QObject):
    """Bounded Qt thread pool preserving the public worker API."""

    finished = QtCore.Signal()
    started = QtCore.Signal()

    def __init__(self, max_threads=1, parent=None):
        super(ThreadsPool, self).__init__(parent=parent)
        self.max_threads = max(1, int(max_threads))
        self.poll_time = 10
        self._started = False
        self._stopping = False
        self._closed = False
        self._active_workers = set()
        self._retained_workers = []
        self._pool = QtCore.QThreadPool(self)
        self._pool.setMaxThreadCount(self.max_threads)

    @property
    def is_started(self):
        return self._started

    @property
    def is_stopped(self):
        return not self._started

    def add_task(self, func, *args, **kwargs):
        if not self._started or self._stopping or self._closed:
            return None
        return OperationWorker(self, func, *args, **kwargs)

    def set_max_threads(self, value):
        self.max_threads = max(1, int(value))
        self._pool.setMaxThreadCount(self.max_threads)

    def start(self):
        if self._started:
            return True
        if self._stopping or self._closed:
            return False
        self._started = True
        self.started.emit()
        return True

    def reopen(self):
        if self._stopping or self._active_workers:
            return False
        self._closed = False
        return True

    def _submit(self, worker):
        if (
            not self._started or self._stopping or self._closed
            or worker in self._active_workers
        ):
            return False
        self._release_retained(worker)
        self._active_workers.add(worker)
        self._pool.start(_OperationRunnable(worker))
        return True

    @QtCore.Slot(object, bool)
    def _worker_completed(self, worker, succeeded):
        self._active_workers.discard(worker)
        self.finished.emit()
        if worker._disposed:
            return
        if succeeded:
            worker.dispose()
        elif worker._retry_pending:
            worker._retry_pending = False
            worker._started = self._submit(worker)
        else:
            # Error dialogs may retry the same worker. Bound its lifetime in
            # case no error surface keeps or explicitly disposes it.
            if worker not in self._retained_workers:
                self._retained_workers.append(worker)
            worker.arm_expiry()
            while len(self._retained_workers) > 32:
                self._retained_workers[0].dispose()

    def _release_retained(self, worker):
        try:
            self._retained_workers.remove(worker)
        except ValueError:
            pass

    def exit(self, timeout_ms=15000):
        if self._stopping:
            return False
        if not self._started and not self._active_workers:
            self._closed = True
            return True
        self._stopping = True
        self._started = False
        self._closed = True
        # Pending runnables are not useful during application shutdown.
        self._pool.clear()
        for worker in tuple(self._active_workers):
            worker.cancel()
        timeout_ms = 15000 if timeout_ms is None else timeout_ms
        completed = self._pool.waitForDone(max(0, int(timeout_ms)))
        if completed:
            for worker in tuple(self._active_workers):
                worker.dispose()
            self._active_workers.clear()
        else:
            logger.warning(
                "Worker pool shutdown timed out with %s active task(s)",
                len(self._active_workers),
            )
        for worker in tuple(self._retained_workers):
            worker.dispose()
        self._retained_workers.clear()
        self._stopping = False
        return bool(completed)


class OperationWorker(QtCore.QObject):

    started = QtCore.Signal()
    finished = QtCore.Signal()
    error = QtCore.Signal(object)
    result = QtCore.Signal(object)
    progress = QtCore.Signal(object)
    stop = QtCore.Signal(object)
    settled = QtCore.Signal(object)
    _completed = QtCore.Signal(object, bool)

    def __init__(self, pool, func, *args, **kwargs):
        super(OperationWorker, self).__init__(parent=pool)
        self._pool = pool
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self.signals_enabled = True
        self._started = False
        self._running = False
        self._disposed = False
        self._retry_pending = False
        self._cancel_requested = False
        self._progress_connected = False
        self._attempts = 0
        self._max_attempts = 3
        self._result = None
        self._data = None
        self._expiry_timer = QtCore.QTimer(self)
        self._expiry_timer.setSingleShot(True)
        self._expiry_timer.setInterval(300000)
        self._expiry_timer.timeout.connect(self.dispose)
        self._completed.connect(
            pool._worker_completed,
            QtCore.Qt.ConnectionType.QueuedConnection,
        )

    @property
    def is_started(self):
        return self._started

    def add_result_data(self, data):
        self._data = data

    def connect_progress(self, func):
        self.progress.connect(func)
        self._progress_connected = True
        self._kwargs['progress_signal'] = self.progress

    def get_result_data(self):
        return self._data

    def start(self):
        if self._disposed or self._started or self._running:
            return
        self._started = self._pool._submit(self)

    @property
    def can_retry(self):
        return (
            not self._disposed
            and not self._running
            and not self._cancel_requested
            and self._pool.is_started
            and self._attempts < self._max_attempts
        )

    def retry(self):
        if not self.can_retry:
            return False
        self._started = False
        self._cancel_requested = False
        self.signals_enabled = True
        self._result = None
        self._expiry_timer.stop()
        if self in self._pool._active_workers:
            self._retry_pending = True
            return True
        self.start()
        return self._started

    @QtCore.Slot()
    def cancel(self):
        if self._disposed:
            return False
        self._cancel_requested = True
        self.signals_enabled = False
        self._retry_pending = False
        if self._progress_connected:
            try:
                self.progress.disconnect()
            except RuntimeError:
                pass
            self._progress_connected = False
        return not self._running

    @QtCore.Slot()
    def arm_expiry(self):
        if not self._disposed:
            self._expiry_timer.start()

    @QtCore.Slot()
    def dispose(self):
        if self._disposed or self._running:
            return
        self._disposed = True
        self._pool._release_retained(self)
        self._retry_pending = False
        self._expiry_timer.stop()
        self.signals_enabled = False
        self._func = None
        self._args = ()
        self._kwargs = {}
        self._result = None
        self._data = None
        self.setParent(None)
        self.deleteLater()

    def _execute(self):
        if self._disposed or self._cancel_requested or not self.signals_enabled:
            self.settled.emit(self)
            self._completed.emit(self, True)
            return
        self._running = True
        self._attempts += 1
        self.started.emit()
        succeeded = False
        try:
            self._result = self._func(*self._args, **self._kwargs)
            if self._cancel_requested or not self.signals_enabled:
                succeeded = True
                return
            if self._data:
                self._result = self._result + (self._data,)
            self.result.emit(self._result)
            self.finished.emit()
            succeeded = True
        except Exception as expected:
            if self._cancel_requested or not self.signals_enabled:
                succeeded = True
            else:
                traceback.print_exc(file=sys.stdout)
                self.error.emit(({
                    'exception': expected,
                    'stacktrace': traceback.format_exc(),
                }, self))
        finally:
            self._running = False
            self._started = False
            self.settled.emit(self)
            self._completed.emit(self, succeeded)
