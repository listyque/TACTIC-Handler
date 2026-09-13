"""Bounded retry policy for explicitly read-only TACTIC requests."""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
import time
from xmlrpc.client import Fault


TRANSIENT_GATEWAY_STATUS_CODES = frozenset({502, 503, 504})
DEFAULT_READ_ATTEMPTS = 3
DEFAULT_READ_DELAYS = (0.35, 0.9)

_defer_transient_error_reporting = ContextVar(
    "defer_transient_error_reporting", default=False
)


def is_transient_gateway_error(exception: BaseException) -> bool:
    """Return whether *exception* represents a temporary gateway response."""
    pending = [exception]
    seen = set()
    while pending:
        current = pending.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        status = getattr(current, "code", None)
        if status is None:
            status = getattr(current, "errcode", None)
        try:
            if int(status) in TRANSIENT_GATEWAY_STATUS_CODES:
                return True
        except (TypeError, ValueError):
            pass
        cause = getattr(current, "__cause__", None)
        context = getattr(current, "__context__", None)
        if cause is not None:
            pending.append(cause)
        if context is not None:
            pending.append(context)
    return False


def is_transient_read_error(exception: BaseException) -> bool:
    """Return whether a read can safely retry after *exception*."""
    if is_transient_gateway_error(exception):
        return True
    pending = [exception]
    seen = set()
    while pending:
        current = pending.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if (
                isinstance(current, Fault)
                and "count of sudo" in current.faultString.lower()
        ):
            return True
        cause = getattr(current, "__cause__", None)
        context = getattr(current, "__context__", None)
        if cause is not None:
            pending.append(cause)
        if context is not None:
            pending.append(context)
    return False


@contextmanager
def defer_transient_error_reporting():
    """Keep retryable attempts out of the user-facing error surface."""
    token = _defer_transient_error_reporting.set(True)
    try:
        yield
    finally:
        _defer_transient_error_reporting.reset(token)


def transient_error_reporting_deferred() -> bool:
    return bool(_defer_transient_error_reporting.get())


def run_read_only_request(
        operation, *, attempts=DEFAULT_READ_ATTEMPTS,
        delays=DEFAULT_READ_DELAYS, on_retry=None):
    """Run an idempotent read with bounded retries for temporary failures.

    The caller must guarantee that ``operation`` has no server-side effects.
    Intermediate retryable failures are marked so the diagnostics bridge does
    not present them as application errors. The final attempt is deliberately
    unmarked and therefore retains the complete command and traceback.
    """
    attempts = max(1, int(attempts or 1))
    delays = tuple(max(0.0, float(delay)) for delay in (delays or ()))
    for index in range(attempts):
        final_attempt = index + 1 >= attempts
        error_context = (
            nullcontext() if final_attempt
            else defer_transient_error_reporting()
        )
        try:
            with error_context:
                return operation()
        except Exception as exception:
            if final_attempt or not is_transient_read_error(exception):
                raise
            delay = delays[min(index, len(delays) - 1)] if delays else 0.0
            if on_retry is not None:
                on_retry(exception, index + 1, attempts, delay)
            if delay:
                time.sleep(delay)
    raise RuntimeError("Read-only request retry loop ended unexpectedly")
