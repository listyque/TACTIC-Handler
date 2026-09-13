"""Pure schedule transformations used by the Tasks Gantt presentation."""

from __future__ import annotations

from datetime import datetime, timedelta

from thlib.ui.task_data import parse_datetime


def date_value(original, target):
    """Move a date while preserving the original time when it exists."""
    parsed = parse_datetime(original)
    if parsed is None:
        parsed_time = datetime.min.time()
    else:
        parsed_time = parsed.time()
    return datetime.combine(target, parsed_time).strftime("%Y-%m-%d %H:%M:%S")


def next_workday(value, direction=1):
    direction = 1 if direction >= 0 else -1
    while value.weekday() >= 5:
        value += timedelta(days=direction)
    return value


def add_workdays(value, amount):
    value = next_workday(value, 1 if amount >= 0 else -1)
    direction = 1 if amount >= 0 else -1
    for _index in range(abs(int(amount))):
        value += timedelta(days=direction)
        value = next_workday(value, direction)
    return value


def workday_duration(start_value, end_value):
    if end_value < start_value:
        return 1
    return max(1, sum(
        1 for offset in range((end_value - start_value).days + 1)
        if (start_value + timedelta(days=offset)).weekday() < 5
    ))


def schedule_dates(
    record, range_start_value, start_day, duration_days, working_days=False,
):
    range_start = parse_datetime(range_start_value)
    if range_start is None:
        return {}
    start_date = range_start.date() + timedelta(days=int(start_day))
    duration_days = max(1, int(duration_days))
    if working_days:
        start_date = next_workday(start_date)
        end_date = add_workdays(start_date, duration_days - 1)
    else:
        end_date = start_date + timedelta(days=duration_days - 1)
    return {
        "start": date_value(record.get("start"), start_date),
        "end": date_value(record.get("end"), end_date),
    }


def shifted_selection_edits(
    primary_record, desired_start_value, selected_records, working_days=False,
):
    """Shift peer records by the primary record's staged date delta."""
    original_start = parse_datetime(primary_record.get("start"))
    desired_start = parse_datetime(desired_start_value)
    if original_start is None or desired_start is None:
        return {}
    delta = desired_start.date() - original_start.date()
    edits = {}
    for code, record in selected_records:
        other_start = parse_datetime(record.get("start"))
        other_end = parse_datetime(record.get("end"))
        if other_start is None or other_end is None:
            continue
        start_date = other_start.date() + delta
        if working_days:
            start_date = next_workday(
                start_date, 1 if delta.days >= 0 else -1
            )
            duration = workday_duration(
                other_start.date(), other_end.date()
            )
            end_date = add_workdays(start_date, duration - 1)
        else:
            end_date = other_end.date() + delta
        edits[str(code)] = {
            "start": date_value(record.get("start"), start_date),
            "end": date_value(record.get("end"), end_date),
        }
    return edits


def batch_schedule_edits(
    records, action, amount=1, working_days=False,
):
    """Return pure date edits for a Gantt multi-selection action."""
    action = str(action or "")
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        amount = 1

    prepared = []
    for code, record in records:
        start_value = parse_datetime(record.get("start"))
        end_value = parse_datetime(record.get("end"))
        if start_value is not None and end_value is not None:
            prepared.append((
                str(code), record, start_value.date(), end_value.date(),
            ))
    if not prepared:
        return {}

    anchor_start = min(item[2] for item in prepared)
    anchor_end = max(item[3] for item in prepared)
    sequence_cursor = anchor_start
    edits = {}

    for code, record, start_date, end_date in prepared:
        if action == "shift":
            if working_days:
                next_start = add_workdays(start_date, amount)
                next_end = add_workdays(end_date, amount)
            else:
                delta = timedelta(days=amount)
                next_start = start_date + delta
                next_end = end_date + delta
        elif action == "align-start":
            next_start, next_end = anchor_start, end_date
        elif action == "align-end":
            next_start, next_end = start_date, anchor_end
        elif action in {"extend", "shorten"}:
            delta = amount if action == "extend" else -amount
            next_start = start_date
            next_end = (
                add_workdays(end_date, delta)
                if working_days
                else end_date + timedelta(days=delta)
            )
            if next_end < next_start:
                next_end = next_start
        elif action == "sequence":
            if working_days:
                duration = workday_duration(start_date, end_date)
                next_start = next_workday(sequence_cursor)
                next_end = add_workdays(next_start, duration - 1)
                sequence_cursor = add_workdays(next_end, 1)
            else:
                duration = (end_date - start_date).days + 1
                next_start = sequence_cursor
                next_end = next_start + timedelta(days=duration - 1)
                sequence_cursor = next_end + timedelta(days=1)
        else:
            return {}

        edits[code] = {
            "start": date_value(record.get("start"), next_start),
            "end": date_value(record.get("end"), next_end),
        }

    return edits


__all__ = [
    "add_workdays",
    "batch_schedule_edits",
    "date_value",
    "next_workday",
    "schedule_dates",
    "shifted_selection_edits",
    "workday_duration",
]
