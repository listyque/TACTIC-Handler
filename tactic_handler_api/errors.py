"""Actionable errors at the public Handler API boundary."""


class ApiError(RuntimeError):
    """Base class for errors introduced by this API (native errors retain cause)."""


class NotFound(ApiError):
    pass


class DirtyObject(ApiError):
    pass


class ConcurrentEdit(ApiError):
    pass


class UIUnavailable(ApiError):
    pass


class BlockingCallError(ApiError):
    pass


class QueueFull(ApiError):
    pass


class NotReady(ApiError):
    pass
