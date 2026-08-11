from __future__ import annotations


class SignalStub:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback, *_args):
        self.callbacks.append(callback)

    def emit(self, value=None):
        for callback in list(self.callbacks):
            callback(value)


class DeferredWorker:
    def __init__(self, operation=None):
        self.operation = operation
        self.result = SignalStub()
        self.error = SignalStub()
        self.started = False
        self.cancelled = False

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True

    def resolve(self, value):
        self.result.emit(value)

    def reject(self, error):
        self.error.emit(error)


class DeferredPool:
    is_stopped = False

    def __init__(self):
        self.workers = []

    def start(self):
        self.is_stopped = False

    def add_task(self, operation, *_args):
        worker = DeferredWorker(operation)
        self.workers.append(worker)
        return worker


class MemorySettings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None, type=None):
        value = self.values.get(key, default)
        return type(value) if type and value is not None else value

    def setValue(self, key, value):
        self.values[key] = value
