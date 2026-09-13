"""Typed TACTIC TEL filters shared by Quick Filters and Advanced Search.

The UI never concatenates TEL. Quick-filter selections are normalized here
and compiled into one relationship expression so every predicate is evaluated
against the same ``sthpw/task`` row.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping


CURRENT_LOGIN_FILTER = "__current_login__"
GENERATED_QUICK_FILTER_KIND = "quick_filters"
TASK_FILTER_FIELDS = {
    "assigned": "assigned",
    "process": "process",
    "status": "status",
}
TASK_FILTER_ORDER = ("assigned", "process", "status")


def normalized_task_selection(
    selections: Mapping[str, Iterable[str]] | None,
) -> dict[str, list[str]]:
    """Return stable, JSON-safe selections for supported task facets."""
    result: dict[str, list[str]] = {}
    for key in TASK_FILTER_ORDER:
        values = sorted({
            str(value)
            for value in (selections or {}).get(key, ())
            if str(value or "")
        })
        if values:
            result[key] = values
    return result


def _tel_literal(value: str) -> str:
    """Quote one TEL string literal without allowing expression injection."""
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _task_values(
    key: str,
    values: list[str],
    current_login: str,
) -> tuple[list[str], bool]:
    uses_login_variable = CURRENT_LOGIN_FILTER in values
    concrete = [value for value in values if value != CURRENT_LOGIN_FILTER]
    if uses_login_variable and concrete:
        if not current_login:
            raise ValueError("Current TACTIC login is not available")
        concrete.append(current_login)
        concrete = sorted(set(concrete))
        uses_login_variable = False
    return concrete, uses_login_variable


def compile_task_filter_tel(
    selections: Mapping[str, Iterable[str]] | None,
    current_login: str = "",
) -> str:
    """Compile task facets into one related-object TEL expression.

    Combining every condition inside one ``@SOBJECT(sthpw/task...)`` is
    significant: process, status, and assignee must belong to the same task.
    The single My Tasks case intentionally matches the TACTIC expression.
    """
    normalized = normalized_task_selection(selections)
    conditions: list[str] = []
    for key in TASK_FILTER_ORDER:
        values = normalized.get(key, [])
        if not values:
            continue
        concrete, uses_login_variable = _task_values(
            key, values, str(current_login or "")
        )
        field = TASK_FILTER_FIELDS[key]
        if uses_login_variable:
            conditions.append(f"['{field}', '$LOGIN']")
        elif len(concrete) == 1:
            conditions.append(f"['{field}', {_tel_literal(concrete[0])}]")
        elif concrete:
            conditions.append(
                f"['{field}', 'in', {_tel_literal('|'.join(concrete))}]"
            )
    if not conditions:
        return ""
    return f"@SOBJECT(sthpw/task{''.join(conditions)})"


def generated_task_filter_record(
    selections: Mapping[str, Iterable[str]] | None,
    current_login: str = "",
) -> dict | None:
    """Build the locked Advanced Search card backing task quick filters."""
    state = normalized_task_selection(selections)
    expression = compile_task_filter_tel(state, current_login)
    if not expression:
        return None
    return {
        "column": "_expression",
        "relation": "in",
        "value": expression,
        "rowEnabled": True,
        "operator": "and",
        "isDefault": False,
        "generatedFilterKind": GENERATED_QUICK_FILTER_KIND,
        "generatedFilterState": {
            "title": "Related task filters",
            "translatable": True,
            "selections": state,
        },
    }


def generated_column_filter_record(
    group_key: str,
    title: str,
    column: str,
    values: Iterable[str],
) -> dict | None:
    """Build one Advanced Search card for a direct Search Type facet."""
    normalized_values = sorted({
        str(value)
        for value in values or ()
        if str(value or "")
    })
    if not group_key or not column or not normalized_values:
        return None
    return {
        "column": str(column),
        "relation": "=" if len(normalized_values) == 1 else "in",
        "value": (
            normalized_values[0]
            if len(normalized_values) == 1
            else "|".join(normalized_values)
        ),
        "rowEnabled": True,
        "operator": "and",
        "isDefault": False,
        "generatedFilterKind": GENERATED_QUICK_FILTER_KIND,
        "generatedFilterState": {
            "title": str(title or column),
            "translatable": False,
            "selections": {str(group_key): normalized_values},
        },
    }


def generated_quick_filter_records(
    selections: Mapping[str, Iterable[str]] | None,
    groups: Iterable[Mapping] | None,
    current_login: str = "",
) -> list[dict]:
    """Materialize every selected facet as executable search cards.

    Related task facets share one TEL expression so their predicates must
    match the same task. Direct Search Type facets use ordinary ``=``/``in``
    records and therefore travel through the canonical Advanced Search path.
    """
    selected = selections or {}
    records: list[dict] = []
    task_record = generated_task_filter_record(selected, current_login)
    known_keys: set[str] = set()
    for group in groups or ():
        key = str(group.get("key") or "")
        if not key or key in TASK_FILTER_FIELDS:
            continue
        known_keys.add(key)
        record = generated_column_filter_record(
            key,
            str(group.get("title") or ""),
            str(group.get("column") or ""),
            selected.get(key, ()),
        )
        if record is not None:
            records.append(record)
    for raw_key in sorted(selected, key=lambda value: str(value)):
        key = str(raw_key or "")
        if key in known_keys or not key.startswith("column:"):
            continue
        column = key.partition(":")[2]
        record = generated_column_filter_record(
            key,
            column.replace("_", " ").title(),
            column,
            selected.get(raw_key, ()),
        )
        if record is not None:
            records.append(record)
    if task_record is not None:
        records.append(task_record)
    return records


def is_generated_quick_filter(record: Mapping | None) -> bool:
    return bool(
        record
        and record.get("generatedFilterKind") == GENERATED_QUICK_FILTER_KIND
    )


def quick_selection_from_records(
    records: Iterable[Mapping] | None,
) -> dict[str, set[str]]:
    """Restore every Quick Filter chip from generated search cards."""
    result: dict[str, set[str]] = {}
    for record in records or ():
        if not is_generated_quick_filter(record):
            continue
        state = record.get("generatedFilterState")
        if not isinstance(state, Mapping):
            continue
        selections = state.get("selections")
        if not isinstance(selections, Mapping):
            continue
        for key, values in selections.items():
            normalized = {
                str(value)
                for value in values or ()
                if str(value or "")
            }
            if normalized:
                result[str(key)] = normalized
    return result


def generated_quick_filter_keys(record: Mapping | None) -> frozenset[str]:
    if not is_generated_quick_filter(record):
        return frozenset()
    state = record.get("generatedFilterState")
    selections = state.get("selections") if isinstance(state, Mapping) else {}
    if not isinstance(selections, Mapping):
        return frozenset()
    return frozenset(str(key) for key in selections)
