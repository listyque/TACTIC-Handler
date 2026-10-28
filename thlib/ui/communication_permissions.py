"""Editing rights for published notes and chat messages."""

from datetime import datetime, timezone

from thlib.global_functions import parce_timestamp


def can_change_published_text(
    author: str,
    timestamp,
    current_login: str,
    privileged: bool,
    clock=None,
    *,
    now=None,
) -> bool:
    if not author or not current_login:
        return False
    if author != current_login:
        return bool(privileged)
    try:
        created = (
            clock.presentation_datetime(timestamp)
            if clock is not None else parce_timestamp(timestamp)
        )
        if created is None:
            return False
        current = now or (
            clock.now() if clock is not None else datetime.now(timezone.utc)
        )
        age = (current - created).total_seconds()
    except (TypeError, ValueError, OverflowError):
        return False
    return 0 <= age < 3600
