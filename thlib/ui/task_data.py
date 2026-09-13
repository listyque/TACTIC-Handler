from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta


def parse_datetime(value):
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("T", " ").rstrip("Z")
    for candidate in (normalized, normalized[:19], normalized[:10]):
        for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(candidate, pattern)
            except ValueError:
                continue
    return None


def progress_value(info):
    value = info.get("progress") or info.get("completion") or 0
    try:
        return max(0, min(100, int(float(str(value).rstrip("%")))))
    except (TypeError, ValueError):
        return 0


def _hours_value(value):
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def format_hours_value(value):
    """Return a compact hours value with a stable decimal representation."""
    text = "{:.2f}".format(_hours_value(value)).rstrip("0")
    return text + "0" if text.endswith(".") else text


def format_hours_label(logged, planned):
    return "{} / {} h".format(
        format_hours_value(logged), format_hours_value(planned)
    )


def parent_search_key(info):
    search_type = str(info.get("search_type") or "").split("?", 1)[0]
    search_code = str(info.get("search_code") or "")
    project = str(info.get("project_code") or "")
    if not search_type or not search_code:
        return ""
    query = "project={}&code={}".format(project, search_code) if project else (
        "code={}".format(search_code)
    )
    return "skey://{}?{}".format(search_type, query)


def due_state(value, today=None):
    parsed = parse_datetime(value)
    if not parsed:
        return "unscheduled"
    current = today or date.today()
    due = parsed.date()
    if due < current:
        return "overdue"
    if due == current:
        return "today"
    if (due - current).days <= 3:
        return "soon"
    return "scheduled"


def task_record(
        task, parent_title="", parent_key="", process_label="",
        process_color="#607d8b", status_color="#607d8b",
        assigned_label="", assigned_override=""):
    info = dict(task.get_info() or {})
    code = str(info.get("code") or "")
    search_key = str(task.get_search_key() or "")
    process = str(info.get("process") or "")
    assigned = str(
        info.get("assigned") or assigned_override or info.get("login") or ""
    )
    end = str(info.get("bid_end_date") or info.get("end_date") or "")
    notes = task.get_notes_count() or {}
    notes_count = sum(int(value or 0) for value in notes.values())
    return {
        "taskCode": code,
        "searchKey": search_key,
        "parentKey": str(parent_key or parent_search_key(info)),
        "parentTitle": str(parent_title or info.get("search_code") or "sObject"),
        "parentSearchType": str(info.get("search_type") or "").split("?", 1)[0],
        "parentSearchTypeLabel": "",
        "parentCode": str(info.get("search_code") or ""),
        "parentPreviewUrl": "",
        "project": str(info.get("project_code") or ""),
        "process": process,
        "processLabel": str(process_label or process or "Task"),
        "processColor": str(process_color or "#607d8b"),
        "processType": "",
        "taskPipeline": "",
        "context": str(info.get("context") or ""),
        "status": str(info.get("status") or ""),
        "statusColor": str(status_color or "#607d8b"),
        "statusChoices": [],
        "assigned": assigned,
        "assignedLabel": str(assigned_label or assigned or "Not assigned"),
        "assignedAvatar": "",
        "assignedChoiceIndex": -1,
        "supervisor": str(info.get("supervisor") or ""),
        "supervisorLabel": "",
        "supervisorAvatar": "",
        "supervisorChoices": [],
        "priority": str(info.get("priority") if info.get("priority") is not None else ""),
        "priorityLabel": str(info.get("priority") if info.get("priority") is not None else ""),
        "priorityColor": "",
        "priorityChoices": [],
        "milestoneCode": str(info.get("milestone_code") or ""),
        "milestoneLabel": "",
        "milestoneDueDate": "",
        "milestoneChoices": [],
        "dependencyId": str(info.get("depend_id") or ""),
        "userChoices": [],
        "start": str(info.get("bid_start_date") or info.get("start_date") or ""),
        "end": end,
        "actualStart": str(info.get("actual_start_date") or ""),
        "actualEnd": str(info.get("actual_end_date") or ""),
        "dueState": due_state(end),
        "progress": progress_value(info),
        "description": str(info.get("description") or ""),
        "plannedHours": _hours_value(info.get("bid_duration")),
        "loggedHours": 0.0,
        "approvedHours": 0.0,
        "pendingHours": 0.0,
        "remainingHours": _hours_value(info.get("bid_duration")),
        "overPlanHours": 0.0,
        "hoursLabel": format_hours_label(
            0.0, info.get("bid_duration")
        ),
        "notes": notes_count,
        "snapshotCount": 0,
        "snapshotFileCount": 0,
        "latestVersion": "",
        "attachmentCount": 0,
        "timestamp": str(info.get("timestamp") or ""),
        "group": "",
        "groupKey": "",
        "groupCount": 0,
        "groupFirst": False,
        "groupCollapsed": False,
        "groupColor": "",
        "selected": False,
        "checked": False,
        "dirty": False,
        "loading": False,
        "error": "",
        "conflict": False,
    }
def is_review_record(record):
    metadata = " ".join(str(record.get(key) or "") for key in (
        "status", "processType", "taskPipeline", "process", "context",
    )).casefold()
    return any(token in metadata for token in ("approval", "review"))


def is_recent_record(record, today=None, days=7):
    timestamp = parse_datetime(record.get("timestamp"))
    if not timestamp:
        return False
    current = today or date.today()
    return current - timedelta(days=max(1, int(days))) <= timestamp.date() <= current


def _matches_quick_filters(record, quick_filters, current_login):
    active = {
        key: {str(value) for value in values if value is not None}
        for key, values in (quick_filters or {}).items()
        if values
    }
    if not active:
        return True

    presets = active.get("preset", set())
    if presets:
        assigned = str(record.get("assigned") or "")
        preset_matches = {
            "mine": bool(current_login) and assigned == current_login,
            "unassigned": not assigned,
            "overdue": record.get("dueState") == "overdue",
            "today": record.get("dueState") == "today",
            "review": is_review_record(record),
            "recent": is_recent_record(record),
        }
        if not any(preset_matches.get(value, False) for value in presets):
            return False

    exact_groups = {
        "process": "process",
        "status": "status",
        "assigned": "assigned",
        "supervisor": "supervisor",
        "priority": "priority",
        "milestone": "milestoneCode",
    }
    return all(
        str(record.get(role) or "") in active[group]
        for group, role in exact_groups.items()
        if group in active
    )


def filtered_records(records, filters, quick_filters=None, current_login=""):
    text = str(filters.get("text") or "").strip().lower()
    process = str(filters.get("process") or "")
    status = str(filters.get("status") or "")
    assigned = str(filters.get("assigned") or "")
    supervisor = str(filters.get("supervisor") or "")
    priority = str(filters.get("priority") or "")
    milestone = str(filters.get("milestone") or "")
    due = str(filters.get("due") or "")
    has_notes = bool(filters.get("hasNotes"))
    day = str(filters.get("day") or "")
    result = []
    for source in records:
        record = dict(source)
        searchable = " ".join(str(record.get(key) or "") for key in (
            "parentTitle", "process", "processLabel", "context", "status",
            "assigned", "assignedLabel", "supervisor", "supervisorLabel",
            "priority", "priorityLabel", "milestoneCode", "milestoneLabel",
            "description",
        )).lower()
        if text and text not in searchable:
            continue
        if process and record.get("process") != process:
            continue
        if status and record.get("status") != status:
            continue
        if assigned and record.get("assigned") != assigned:
            continue
        if supervisor and record.get("supervisor") != supervisor:
            continue
        if priority and str(record.get("priority") or "") != priority:
            continue
        if milestone and record.get("milestoneCode") != milestone:
            continue
        if due and record.get("dueState") != due:
            continue
        if has_notes and not int(record.get("notes") or 0):
            continue
        parsed_end = parse_datetime(record.get("end"))
        if day and (not parsed_end or parsed_end.date().isoformat() != day):
            continue
        if not _matches_quick_filters(record, quick_filters, current_login):
            continue
        result.append(record)
    return result


def _group_identity(record, group_mode):
    if group_mode == "status":
        return (
            str(record.get("status") or "__none__"),
            str(record.get("status") or "No status"),
            str(record.get("statusColor") or ""),
        )
    if group_mode == "user":
        return (
            str(record.get("assigned") or "__unassigned__"),
            str(record.get("assignedLabel") or "Not assigned"),
            "",
        )
    if group_mode == "object":
        return (
            str(record.get("parentKey") or record.get("parentCode") or ""),
            str(record.get("parentTitle") or "sObject"),
            str(record.get("processColor") or ""),
        )
    if group_mode == "project":
        return (
            str(record.get("project") or "__none__"),
            str(record.get("project") or "No project"),
            "",
        )
    if group_mode == "search_type":
        return (
            str(record.get("parentSearchType") or "__none__"),
            str(
                record.get("parentSearchTypeLabel")
                or record.get("parentSearchType") or "No search type"
            ),
            "",
        )
    if group_mode == "none":
        return "", "", ""
    return (
        str(record.get("process") or "__none__"),
        str(record.get("processLabel") or record.get("process") or "Task"),
        str(record.get("processColor") or ""),
    )


def _canonical_group_catalog(records, group_mode):
    """Choose one presentation for every stable server-side group key.

    The same process code may be used by several pipelines whose configured
    labels or colors differ.  Grouping still owns one identity: the process
    code.  Sorting directly by each row's label would split that identity into
    several visual headers while repeating its aggregate count on every one.
    Use the most common configured presentation and deterministic tie-breakers
    so all rows with the same key stay in one contiguous group.
    """
    catalog = {}
    for record in records:
        key, label, color = _group_identity(record, group_mode)
        if not key:
            continue
        entry = catalog.setdefault(key, {"count": 0, "variants": {}})
        entry["count"] += 1
        variant = (label, color)
        entry["variants"][variant] = entry["variants"].get(variant, 0) + 1

    result = {}
    for key, entry in catalog.items():
        label, color = min(
            entry["variants"],
            key=lambda variant: (
                -entry["variants"][variant],
                variant[0].casefold(),
                variant[0],
                variant[1].casefold(),
            ),
        )
        result[key] = (label, color, entry["count"])
    return result


def sort_and_group(
        records, sort_mode="due", group_mode="process",
        collapsed_groups=None, descending=False, presorted=False):
    copied = [dict(record) for record in records]
    # Unsaved task drafts are an editor surface, not ordinary query results.
    # Keep them in insertion order above every sorted/grouped server record so
    # editing process, status or assignee cannot make the active draft jump.
    pinned = [record for record in copied if record.get("isNew")]
    values = [record for record in copied if not record.get("isNew")]
    collapsed_groups = set(collapsed_groups or ())

    def due_key(record):
        parsed = parse_datetime(record.get("end"))
        return parsed or datetime.max

    def text_key(record, key, label_key=None):
        return str(record.get(label_key or key) or record.get(key) or "").casefold()

    if not presorted:
        if sort_mode == "recent":
            values.sort(
                key=lambda record: parse_datetime(record.get("timestamp"))
                    or datetime.min,
                reverse=True,
            )
        elif sort_mode == "user":
            values.sort(key=due_key)
            values.sort(
                key=lambda record: str(
                    record.get("assignedLabel") or ""
                ).lower(),
                reverse=descending,
            )
        elif sort_mode == "process":
            values.sort(key=due_key)
            values.sort(
                key=lambda record: str(
                    record.get("processLabel") or ""
                ).lower(),
                reverse=descending,
            )
        elif sort_mode == "status":
            values.sort(key=due_key)
            values.sort(
                key=lambda record: text_key(record, "status"),
                reverse=descending,
            )
        elif sort_mode == "object":
            values.sort(key=due_key)
            values.sort(
                key=lambda record: (
                    text_key(record, "parentTitle"),
                    text_key(record, "process", "processLabel"),
                ),
                reverse=descending,
            )
        elif sort_mode == "priority":
            values.sort(key=due_key)
            values.sort(
                key=lambda record: text_key(
                    record, "priority", "priorityLabel"
                ),
                reverse=descending,
            )
        elif sort_mode == "milestone":
            values.sort(key=due_key)
            values.sort(
                key=lambda record: text_key(
                    record, "milestoneCode", "milestoneLabel"
                ),
                reverse=descending,
            )
        elif sort_mode == "supervisor":
            values.sort(key=due_key)
            values.sort(
                key=lambda record: text_key(
                    record, "supervisor", "supervisorLabel"
                ),
                reverse=descending,
            )
        else:
            dated = [record for record in values if parse_datetime(record.get("end"))]
            undated = [record for record in values if not parse_datetime(record.get("end"))]
            dated.sort(key=due_key, reverse=descending)
            values = dated + undated

    group_catalog = _canonical_group_catalog(values, group_mode)

    def canonical_group_identity(record):
        key, label, color = _group_identity(record, group_mode)
        canonical = group_catalog.get(key)
        if canonical is not None:
            label, color, _count = canonical
        return key, label, color

    if group_mode != "none" and not presorted:
        values.sort(
            key=lambda record: (
                canonical_group_identity(record)[1].casefold(),
                canonical_group_identity(record)[0].casefold(),
            ),
            reverse=bool(descending) and group_mode == sort_mode,
        )

    previous = None
    for record in values:
        key, label, color = canonical_group_identity(record)
        record["group"] = label
        record["groupKey"] = key
        record["groupCount"] = (
            group_catalog.get(key, ("", "", 0))[2] if key else 0
        )
        record["groupFirst"] = bool(key) and key != previous
        record["groupCollapsed"] = bool(key) and key in collapsed_groups
        record["groupColor"] = color
        previous = key
    for record in pinned:
        record.update({
            "group": "",
            "groupKey": "",
            "groupCount": 0,
            "groupFirst": False,
            "groupCollapsed": False,
            "groupColor": "",
        })
    return pinned + values


def calendar_cells(year, month, records, today=None, milestones=None):
    """Build a fixed six-week month projection from loaded task records."""
    tasks_by_day = {}
    for record in records:
        parsed = parse_datetime(record.get("end"))
        if not parsed:
            continue
        key = parsed.date().isoformat()
        tasks_by_day.setdefault(key, []).append({
            "taskCode": str(record.get("taskCode") or ""),
            "parentKey": str(record.get("parentKey") or ""),
            "parentTitle": str(record.get("parentTitle") or "sObject"),
            "process": str(record.get("process") or ""),
            "processLabel": str(
                record.get("processLabel") or record.get("process") or "Task"
            ),
            "status": str(record.get("status") or "No status"),
            "statusColor": str(
                record.get("statusColor")
                or record.get("processColor")
                or "#607d8b"
            ),
            "assignedLabel": str(
                record.get("assignedLabel") or "Not assigned"
            ),
            "dueState": str(record.get("dueState") or "scheduled"),
            "selected": bool(record.get("selected")),
        })

    for tasks in tasks_by_day.values():
        tasks.sort(key=lambda task: (
            task["dueState"] != "overdue",
            task["parentTitle"].casefold(),
            task["processLabel"].casefold(),
        ))

    milestones_by_day = {}
    for source in milestones or []:
        due = parse_datetime(source.get("dueDate") or source.get("due_date"))
        if not due:
            continue
        key = due.date().isoformat()
        milestones_by_day.setdefault(key, []).append({
            "code": str(source.get("code") or source.get("value") or ""),
            "label": str(
                source.get("label")
                or source.get("description")
                or "Milestone"
            ),
            "completion": int(source.get("completion") or 0),
            "taskCount": int(source.get("taskCount") or 0),
        })

    first_weekday, days_in_month = calendar.monthrange(year, month)
    start = date(year, month, 1).toordinal() - first_weekday
    current = today or date.today()
    result = []
    for offset in range(42):
        value = date.fromordinal(start + offset)
        key = value.isoformat()
        tasks = tasks_by_day.get(key, [])
        day_milestones = milestones_by_day.get(key, [])
        overdue_count = sum(
            task["dueState"] == "overdue" for task in tasks
        )
        result.append({
            "date": key,
            "day": value.day,
            "inMonth": value.month == month,
            "today": value == current,
            "taskCount": len(tasks),
            "overdueCount": overdue_count,
            "tasks": tasks,
            "milestoneCount": len(day_milestones),
            "milestones": day_milestones,
            "selected": False,
        })
    return result


def gantt_layout(records, today=None, milestones=None):
    """Build flat Gantt geometry from already filtered task records."""
    current = today or date.today()
    scheduled = []
    unscheduled = []
    drawable = []
    starts = []
    ends = []
    milestone_sources = []
    for source in milestones or []:
        value = parse_datetime(source.get("dueDate") or source.get("due_date"))
        code = str(source.get("value") or source.get("code") or "")
        if not code or not value:
            continue
        milestone_sources.append((source, value.date()))
        starts.append(value.date())
        ends.append(value.date())

    for source in records:
        record = dict(source)
        start_value = parse_datetime(record.get("start"))
        end_value = parse_datetime(record.get("end"))
        issue = ""
        if not start_value and not end_value:
            issue = "Start and deadline are not set"
        elif not start_value:
            issue = "Start is not set"
        elif not end_value:
            issue = "Deadline is not set"
        elif end_value.date() < start_value.date():
            issue = "Deadline precedes start"

        section_scheduled = source.get("_ganttSectionScheduled")
        if section_scheduled is None:
            section_scheduled = not issue
        section = "scheduled" if section_scheduled else "unscheduled"

        record.update({
            "ganttScheduled": not issue,
            "ganttStartDay": 0,
            "ganttDurationDays": 0,
            "ganttStartLabel": (
                start_value.date().isoformat() if start_value else ""
            ),
            "ganttEndLabel": end_value.date().isoformat() if end_value else "",
            "ganttIssue": issue,
            "ganttColor": str(
                record.get("statusColor") or record.get("processColor") or ""
            ),
            "ganttSection": section,
            "ganttSectionFirst": False,
            "ganttWarning": "",
            "ganttGroupStartDay": 0,
            "ganttGroupDurationDays": 0,
            "ganttGroupProgress": 0,
        })
        if section_scheduled:
            scheduled.append(record)
        else:
            unscheduled.append(record)
        if not issue:
            starts.append(start_value.date())
            ends.append(end_value.date())
            drawable.append(record)

    if starts:
        range_start = min(starts)
        range_start -= timedelta(days=range_start.weekday() + 7)
        range_end = max(ends)
        range_end += timedelta(days=(6 - range_end.weekday()) + 7)
    else:
        range_start = current - timedelta(days=current.weekday() + 7)
        range_end = range_start + timedelta(days=41)
    if (range_end - range_start).days < 27:
        range_end = range_start + timedelta(days=27)

    for record in drawable:
        start_value = parse_datetime(record["start"]).date()
        end_value = parse_datetime(record["end"]).date()
        record["ganttStartDay"] = (start_value - range_start).days
        record["ganttDurationDays"] = (end_value - start_value).days + 1

    warning_parts = {}
    for record in drawable:
        code = str(record.get("taskCode") or "")
        parts = []
        end_value = parse_datetime(record.get("end")).date()
        if end_value < current and int(record.get("progress") or 0) < 100:
            parts.append("Task is overdue")
        if not str(record.get("assigned") or ""):
            parts.append("Task has no assignee")
        if end_value.weekday() >= 5:
            parts.append("Deadline falls on a weekend")
        warning_parts[code] = parts

    by_user = {}
    for record in drawable:
        login = str(record.get("assigned") or "")
        if login:
            by_user.setdefault(login, []).append(record)
    for values in by_user.values():
        values.sort(key=lambda item: item["ganttStartDay"])
        latest_end = -1
        for index, record in enumerate(values):
            start = record["ganttStartDay"]
            end = start + record["ganttDurationDays"] - 1
            # An earlier interval with the furthest end, or the next start,
            # proves overlap. We need a flag, not every intersecting pair.
            if latest_end >= start or (
                    index + 1 < len(values)
                    and values[index + 1]["ganttStartDay"] <= end):
                warning_parts[str(record.get("taskCode") or "")].append(
                    "Assignee has overlapping tasks"
                )
            latest_end = max(latest_end, end)

    for record in drawable:
        parts = warning_parts.get(str(record.get("taskCode") or ""), [])
        record["ganttWarning"] = "\n".join(dict.fromkeys(parts))

    def prepare_section(values, section):
        counts = {}
        for record in values:
            key = str(record.get("groupKey") or "")
            if key:
                counts[key] = counts.get(key, 0) + 1
        previous = None
        summaries = {}
        for record in values:
            key = str(record.get("groupKey") or "")
            if not key or not record.get("ganttScheduled"):
                continue
            start_day = int(record.get("ganttStartDay") or 0)
            end_day = start_day + int(record.get("ganttDurationDays") or 1)
            summary = summaries.setdefault(key, {
                "start": start_day,
                "end": end_day,
                "progress": 0,
                "count": 0,
            })
            summary["start"] = min(summary["start"], start_day)
            summary["end"] = max(summary["end"], end_day)
            summary["progress"] += int(record.get("progress") or 0)
            summary["count"] += 1
        for index, record in enumerate(values):
            key = str(record.get("groupKey") or "")
            record["ganttSection"] = section
            record["ganttSectionFirst"] = index == 0
            record["groupFirst"] = bool(key) and key != previous
            record["groupCount"] = counts.get(key, 0)
            summary = summaries.get(key)
            if summary:
                record["ganttGroupStartDay"] = summary["start"]
                record["ganttGroupDurationDays"] = (
                    summary["end"] - summary["start"]
                )
                record["ganttGroupProgress"] = round(
                    summary["progress"] / summary["count"]
                )
            previous = key

    prepare_section(scheduled, "scheduled")
    prepare_section(unscheduled, "unscheduled")

    day_count = (range_end - range_start).days + 1
    tick_step = 7 if day_count <= 180 else 14 if day_count <= 730 else 28
    ticks = {}
    cursor = range_start
    while cursor <= range_end:
        offset = (cursor - range_start).days
        ticks[offset] = {
            "date": cursor.isoformat(),
            "label": "{:02d} {}".format(
                cursor.day, calendar.month_abbr[cursor.month]
            ),
            "offsetDay": offset,
            "major": False,
        }
        cursor += timedelta(days=tick_step)
    cursor = date(range_start.year, range_start.month, 1)
    if cursor < range_start:
        cursor = (
            date(cursor.year + 1, 1, 1)
            if cursor.month == 12
            else date(cursor.year, cursor.month + 1, 1)
        )

    def tick_item(value, label, span_days=1, major=False):
        return {
            "date": value.isoformat(),
            "label": label,
            "offsetDay": (value - range_start).days,
            "spanDays": span_days,
            "major": major,
        }

    day_ticks = []
    day_step = max(1, (day_count + 719) // 720)
    cursor = range_start
    while cursor <= range_end:
        day_ticks.append(tick_item(
            cursor,
            "{:02d} {}".format(cursor.day, calendar.month_abbr[cursor.month]),
            day_step,
            cursor.day == 1,
        ))
        cursor += timedelta(days=day_step)

    week_ticks = []
    cursor = range_start
    while cursor <= range_end:
        week_ticks.append(tick_item(
            cursor,
            "{:02d} {}".format(cursor.day, calendar.month_abbr[cursor.month]),
            7,
            cursor.day <= 7,
        ))
        cursor += timedelta(days=7)

    month_ticks = []
    cursor = date(range_start.year, range_start.month, 1)
    if cursor < range_start:
        cursor = (
            date(cursor.year + 1, 1, 1)
            if cursor.month == 12
            else date(cursor.year, cursor.month + 1, 1)
        )
    while cursor <= range_end:
        month_ticks.append(tick_item(
            cursor,
            "{} {}".format(calendar.month_abbr[cursor.month], cursor.year),
            calendar.monthrange(cursor.year, cursor.month)[1],
            cursor.month == 1,
        ))
        cursor = (
            date(cursor.year + 1, 1, 1)
            if cursor.month == 12
            else date(cursor.year, cursor.month + 1, 1)
        )

    quarter_ticks = []
    quarter_month = ((range_start.month - 1) // 3) * 3 + 1
    cursor = date(range_start.year, quarter_month, 1)
    while cursor <= range_end:
        marker = max(cursor, range_start)
        quarter_ticks.append(tick_item(
            marker,
            "Q{} {}".format((cursor.month - 1) // 3 + 1, cursor.year),
            90,
            cursor.month == 1,
        ))
        next_month = cursor.month + 3
        cursor = (
            date(cursor.year + 1, next_month - 12, 1)
            if next_month > 12
            else date(cursor.year, next_month, 1)
        )
    while cursor <= range_end:
        offset = (cursor - range_start).days
        ticks[offset] = {
            "date": cursor.isoformat(),
            "label": "{} {}".format(
                calendar.month_abbr[cursor.month], cursor.year
            ),
            "offsetDay": offset,
            "major": True,
        }
        cursor = (
            date(cursor.year + 1, 1, 1)
            if cursor.month == 12
            else date(cursor.year, cursor.month + 1, 1)
        )

    today_offset = (current - range_start).days
    if not 0 <= today_offset < day_count:
        today_offset = -1
    weekend_spans = []
    cursor = range_start
    while cursor <= range_end:
        if cursor.weekday() == 5:
            weekend_spans.append({
                "offsetDay": (cursor - range_start).days,
                "durationDays": min(2, (range_end - cursor).days + 1),
            })
            cursor += timedelta(days=2)
        else:
            cursor += timedelta(days=1)
    overview = [{
        "startDay": int(record.get("ganttStartDay") or 0),
        "durationDays": int(record.get("ganttDurationDays") or 1),
        "color": str(record.get("ganttColor") or ""),
        "warning": bool(record.get("ganttWarning")),
    } for record in scheduled]
    if len(overview) > 400:
        bucket_days = max(1, (day_count + 179) // 180)
        buckets = {}
        for item in overview:
            key = item["startDay"] // bucket_days
            bucket = buckets.setdefault(key, {
                "startDay": key * bucket_days,
                "durationDays": bucket_days,
                "color": item["color"],
                "warning": False,
            })
            bucket["warning"] = bucket["warning"] or item["warning"]
        overview = [buckets[key] for key in sorted(buckets)]
    milestone_markers = [{
        "code": str(source.get("value") or source.get("code") or ""),
        "label": str(
            source.get("label") or source.get("description") or "Milestone"
        ),
        "dueDate": due_date.isoformat(),
        "offsetDay": (due_date - range_start).days,
        "completion": int(source.get("completion") or 0),
        "taskCount": int(source.get("taskCount") or 0),
    } for source, due_date in milestone_sources]
    return {
        "rangeStart": range_start.isoformat(),
        "rangeEnd": range_end.isoformat(),
        "days": day_count,
        "todayDay": today_offset,
        "scheduled": len(scheduled),
        "unscheduled": len(unscheduled),
        "ticks": [ticks[key] for key in sorted(ticks)],
        "tickSets": {
            "days": day_ticks,
            "weeks": week_ticks,
            "months": month_ticks,
            "quarters": quarter_ticks,
        },
        "weekends": weekend_spans,
        "overview": overview,
        "milestones": milestone_markers,
        "warnings": sum(
            bool(record.get("ganttWarning")) for record in scheduled
        ) + len(unscheduled),
        "records": scheduled + unscheduled,
    }
