"""Localized exact and relative time presentation."""

from __future__ import annotations

import datetime


def get_full_datetime(date_time_object: datetime.datetime) -> str:
    from thlib.side.Qt import QtCore
    if not isinstance(date_time_object, datetime.datetime):
        return ""
    return QtCore.QLocale().toString(
        QtCore.QDateTime(date_time_object), "d MMMM yyyy, HH:mm:ss"
    )


def get_pretty_datetime(
    date_time_object: datetime.datetime,
    now: datetime.datetime | None = None,
) -> str:
    from thlib.side.Qt import QtCore
    if not isinstance(date_time_object, datetime.datetime):
        return ""
    now = now or datetime.datetime.now(tz=date_time_object.tzinfo)
    seconds_lapsed = (now - date_time_object).total_seconds()
    if seconds_lapsed < 0:
        return get_full_datetime(date_time_object)
    translate = QtCore.QCoreApplication.translate
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
