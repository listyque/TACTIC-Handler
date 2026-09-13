"""Public queue access marshalled to the existing desktop queue owner."""

from concurrent.futures import Future
from copy import deepcopy

from tactic_handler_api.errors import ConcurrentEdit, NotFound


class DesktopQueue:
    def __init__(self, queue, dispatch):
        self._queue = queue
        self._send = dispatch
        self._pending = {}
        self._scheduled = set()
        self._results = {}
        self._completed = {}
        self._closed = False
        self._dispatch(self._attach)

    def _dispatch(self, callback, *args):
        if self._closed:
            raise RuntimeError("The desktop API queue is closed")
        from PySide6.QtCore import QThread

        if QThread.currentThread() == self._queue.thread():
            return callback(*args)
        return self._send(callback, *args)

    def _attach(self):
        self._queue.stateChanged.connect(self._changed)
        self._queue._executor.operationResult.connect(self._result)
        self._queue._executor.operationFinished.connect(self._changed)

    def _result(self, result):
        identity = self._queue._active_id
        if identity:
            self._results[identity] = deepcopy(result)
            self._completed[identity] = {
                "id": identity,
                "payload": self._queue.operation(identity),
                "state": "finished",
                "result": deepcopy(result),
            }
            if len(self._completed) > 1000:
                oldest = next(iter(self._completed))
                self._completed.pop(oldest)
                self._results.pop(oldest, None)

    def _changed(self, *_args):
        queue = self._queue
        for identity, future in tuple(self._pending.items()):
            if future.done():
                self._pending.pop(identity, None)
                self._scheduled.discard(identity)
                continue
            if identity in self._results:
                future.set_result(deepcopy(self._results[identity]))
                self._pending.pop(identity, None)
                self._scheduled.discard(identity)
                continue
            row = queue._row_for_id(identity)
            if row < 0:
                future.set_exception(
                    NotFound("Queue item was removed before completion")
                )
                continue
            record = queue.model._records[row]
            if record.get("status") in {
                "Failed",
                "Invalid",
                "Missing files",
                "Cancelled",
            }:
                future.set_exception(
                    RuntimeError(record.get("error") or record["status"])
                )
                continue
            if identity == queue._active_id:
                if not future.running():
                    future.set_running_or_notify_cancel()
                continue
            if (
                identity not in self._scheduled
                and record.get("canCommit")
                and not (queue._executor.operationBusy and not queue._active_id)
            ):
                self._scheduled.add(identity)
                if identity not in queue._batch_ids:
                    queue._batch_ids.append(identity)
                queue._start_next()

    def _get(self, identity):
        if identity in self._completed:
            return deepcopy(self._completed[identity])
        payload = self._queue.operation(identity)
        row = self._queue._row_for_id(identity)
        if payload is None or row < 0:
            raise NotFound(f"Queue item {identity!r} is unavailable")
        record = self._queue.model._records[row]
        status = record.get("status")
        state = (
            "running"
            if identity == self._queue._active_id
            else "finished"
            if status == "Completed"
            else "failed"
            if status in {"Failed", "Invalid", "Missing files"}
            else "cancelled"
            if status == "Cancelled"
            else "prepared"
        )
        return {"id": identity, "payload": payload, "state": state}

    def get(self, identity):
        return self._dispatch(self._get, identity)

    def items(self):
        return self._dispatch(
            lambda: [self._get(identity) for identity in self._queue._operations]
        )

    def add(self, payload, title):
        from tactic_handler_api.checkin import validate_payload

        validate_payload(payload)

        def add():
            identity = self._queue._identity(payload)
            if any(
                self._queue._identity(existing) == identity
                for existing in self._queue._operations.values()
            ):
                raise ValueError("This check-in is already in the queue")
            return self._queue.add_prepared(payload, title)

        return self._dispatch(add)

    def update(self, identity, values):
        if set(values) != {"description"}:
            raise ValueError(
                "Only description edits are supported on queued desktop entries"
            )
        return self._dispatch(
            self._queue.update_operation_description, identity, values["description"]
        )

    def remove(self, identity):
        def remove():
            if identity == self._queue._active_id:
                raise ConcurrentEdit("Cannot remove a running check-in")
            row = self._queue._row_for_id(identity)
            if row >= 0:
                self._queue.remove_row(row)
            self._completed.pop(identity, None)
            self._results.pop(identity, None)

        return self._dispatch(remove)

    def commit(self, identity):
        from tactic_handler_api.operations import check_blocking_call

        check_blocking_call()

        def start():
            if identity in self._results:
                future = Future()
                future.set_result(deepcopy(self._results[identity]))
                return future
            self._get(identity)
            future = self._pending.get(identity)
            if future is None:
                future = Future()
                self._pending[identity] = future
                self._changed()
            return future

        return self._dispatch(start).result()

    def close(self):
        if self._closed:
            return

        def detach():
            self._queue.stateChanged.disconnect(self._changed)
            self._queue._executor.operationResult.disconnect(self._result)
            self._queue._executor.operationFinished.disconnect(self._changed)
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(
                        RuntimeError(
                            "Handler is shutting down; verify pending check-ins"
                        )
                    )
            self._pending.clear()
            self._scheduled.clear()
            self._closed = True

        self._dispatch(detach)
