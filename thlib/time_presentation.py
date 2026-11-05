"""Localized exact and relative time presentation."""

from __future__ import annotations

import datetime
import functools


@functools.lru_cache(maxsize=512)
def _cached_date(
    locale_name: str, year: int, month: int, day: int, fmt: str
) -> str:
    from PySide6.QtCore import QDate, QLocale

    return QLocale(locale_name).toString(QDate(year, month, day), fmt)


def _date_value(value) -> datetime.date | None:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def get_compact_date(value) -> str:
    from PySide6.QtCore import QLocale

    parsed = _date_value(value)
    if parsed is None:
        return ""
    return _cached_date(
        QLocale().name(), parsed.year, parsed.month, parsed.day, "d MMM"
    )


def get_full_date(value) -> str:
    from PySide6.QtCore import QLocale

    parsed = _date_value(value)
    if parsed is None:
        return ""
    return _cached_date(
        QLocale().name(), parsed.year, parsed.month, parsed.day, "d MMMM yyyy"
    )


def get_full_datetime(date_time_object: datetime.datetime) -> str:
    from PySide6.QtCore import QLocale

    if not isinstance(date_time_object, datetime.datetime):
        return ""
    date_part = _cached_date(
        QLocale().name(),
        date_time_object.year,
        date_time_object.month,
        date_time_object.day,
        "d MMMM yyyy",
    )
    return (
        f"{date_part}, "
        f"{date_time_object.hour:02d}:{date_time_object.minute:02d}:{date_time_object.second:02d}"
    )


def get_pretty_datetime(
    date_time_object: datetime.datetime,
    now: datetime.datetime | None = None,
) -> str:
    from PySide6.QtCore import QCoreApplication

    if not isinstance(date_time_object, datetime.datetime):
        return ""
    now = now or datetime.datetime.now(tz=date_time_object.tzinfo)
    seconds_lapsed = (now - date_time_object).total_seconds()
    if seconds_lapsed < 0:
        return get_full_datetime(date_time_object)
    translate = QCoreApplication.translate
    if seconds_lapsed < 60:
        return translate("Dates", "Just now")
    if seconds_lapsed < 3600:
        return translate("Dates", "%1 min ago").replace("%1", str(int(seconds_lapsed // 60)))
    if seconds_lapsed < 86400:
        return translate("Dates", "%1 h ago").replace("%1", str(int(seconds_lapsed // 3600)))
    if seconds_lapsed < 172800:
        return translate("Dates", "Yesterday")
    if seconds_lapsed < 604800:
        return translate("Dates", "%1 days ago").replace("%1", str(int(seconds_lapsed // 86400)))
    if seconds_lapsed < 2629800:
        return translate("Dates", "%1 wk ago").replace("%1", str(int(seconds_lapsed // 604800)))
    return get_full_datetime(date_time_object)


def get_pretty_and_full_datetime(
    date_time_object: datetime.datetime,
    now: datetime.datetime | None = None,
) -> tuple[str, str]:
    if not isinstance(date_time_object, datetime.datetime):
        return "", ""
    full = get_full_datetime(date_time_object)
    now = now or datetime.datetime.now(tz=date_time_object.tzinfo)
    seconds_lapsed = (now - date_time_object).total_seconds()
    if seconds_lapsed < 0 or seconds_lapsed >= 2629800:
        return full, full
    return get_pretty_datetime(date_time_object, now=now), full
