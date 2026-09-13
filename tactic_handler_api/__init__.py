"""Explicit, object-oriented TACTIC Handler API (no import-time UI or connection)."""

from .api import (
    HandlerAPI,
    _bind_current,
    _unbind_current,
    from_client,
    get_api,
    local,
)
from .errors import (
    ApiError,
    BlockingCallError,
    ConcurrentEdit,
    DirtyObject,
    NotFound,
    NotReady,
    QueueFull,
    UIUnavailable,
)
from .identity import SearchKey
from .objects import Project, SearchResult, SObject, Snapshot, SType
from .operations import Operation, Subscription

__all__ = [
    "HandlerAPI",
    "get_api",
    "local",
    "from_client",
    "SearchKey",
    "Project",
    "SType",
    "SObject",
    "Snapshot",
    "SearchResult",
    "Operation",
    "Subscription",
    "ApiError",
    "BlockingCallError",
    "ConcurrentEdit",
    "DirtyObject",
    "NotFound",
    "NotReady",
    "QueueFull",
    "UIUnavailable",
]
