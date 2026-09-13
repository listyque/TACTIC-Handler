"""Canonical search definitions shared by every search entry point.

The sidebar, the primary search field, Advanced Search, saved Search Views,
related-object navigation, and skey navigation do not own separate search
engines.  They all create or edit the same filter-card records stored by a
``SearchTabSession``.  Executable TACTIC filters are derived from those cards.
"""

from __future__ import annotations

from collections.abc import Iterable
import re
import uuid

from thlib.search_helpers import get_suggestion_filter

from .controllers.types import (
    STANDARD_QUICK_FILTER_TAB_KINDS,
    SearchTabSession,
)


_RESULT_SORT_MODES = frozenset({
    "name_asc", "name_desc", "updated_desc", "updated_asc",
})
_COLUMN_SORT_MODE = re.compile(
    r"column:([A-Za-z_][A-Za-z0-9_]*):(asc|desc)"
)


def parse_column_sort_mode(mode: str) -> tuple[str, bool] | None:
    match = _COLUMN_SORT_MODE.fullmatch(str(mode or ""))
    if not match:
        return None
    return match.group(1), match.group(2) == "desc"


def is_result_sort_mode(mode: str) -> bool:
    return mode in _RESULT_SORT_MODES or parse_column_sort_mode(mode) is not None


def result_order_bys(mode: str) -> list[str]:
    column_sort = parse_column_sort_mode(mode)
    if column_sort:
        column, descending = column_sort
        return [column + (" desc" if descending else "")]
    return {
        "name_asc": ["name"],
        "name_desc": ["name desc"],
        "updated_desc": ["timestamp desc"],
        "updated_asc": ["timestamp"],
    }.get(mode, ["name"])


def default_name_record(value: str = "") -> dict:
    """Return the editable first row used by Handler search."""
    return {
        "column": "name",
        "relation": "EQI",
        "value": value,
        "rowEnabled": True,
        "operator": "begin",
        "isDefault": True,
    }


def normalize_records(records: Iterable[dict] | None) -> list[dict]:
    """Clone filter cards and normalize their ordering metadata."""
    normalized: list[dict] = []
    for source in records or ():
        record = dict(source)
        index = len(normalized)
        record.setdefault("rowEnabled", True)
        record["operator"] = (
            "begin"
            if index == 0
            else "or" if record.get("operator") == "or" else "and"
        )
        record["isDefault"] = index == 0
        normalized.append(record)
    return normalized


def records_from_filters(filters: Iterable | None) -> list[dict]:
    """Convert executable TACTIC filters to visible Advanced Search cards."""
    values = list(filters or ())
    tuples = [
        (index, value)
        for index, value in enumerate(values)
        if isinstance(value, tuple) and len(value) == 3
    ]
    records = []
    for row, (position, value) in enumerate(tuples):
        operator = "begin" if row == 0 else "and"
        if row > 0 and position + 1 < len(values):
            candidate = values[position + 1]
            if candidate in {"and", "or"}:
                operator = candidate
        records.append({
            "column": str(value[0]),
            "relation": value[1],
            "value": value[2],
            "rowEnabled": True,
            "operator": operator,
            "isDefault": row == 0,
        })
    return normalize_records(records)


def filters_from_records(records: Iterable[dict] | None) -> list:
    """Derive the only server-query representation from filter cards."""
    active_records = []
    for record in records or ():
        column = str(record.get("column") or "")
        if not record.get("rowEnabled") or not column:
            continue
        value = record.get("value")
        relation = record.get("relation")
        if str(value or "").strip() == "" and relation is not None:
            continue
        active_records.append((record, (column, relation, value)))

    filters = []
    for index, (record, filter_value) in enumerate(active_records):
        if index == 0:
            if len(active_records) > 1:
                filters.append("begin")
            filters.append(filter_value)
            continue
        filters.append(filter_value)
        filters.append("or" if record.get("operator") == "or" else "and")
    return filters


def set_primary_name(
    records: Iterable[dict] | None,
    value: str,
    *,
    relation: str = "EQI",
    columns: Iterable[str] = ("name",),
) -> list[dict]:
    """Replace the leading text-search group, retaining other filter cards.

    Its ordinary OR cards share the first row's value and relation. Keeping
    that native card shape also works after a Saved Search round trip, without
    adding a second query representation or private preset metadata.
    """
    normalized = normalize_records(records)
    columns = list(dict.fromkeys(columns)) or ["name"]
    if normalized and normalized[0].get("column") in {"name", columns[0]}:
        previous = normalized.pop(0)
        previous_fields = {
            part[0] for part in get_suggestion_filter(
                previous["column"], previous.get("value"),
                [record.get("column") for record in normalized],
            ) if isinstance(part, tuple)
        } - {previous["column"]}
        while normalized and (
            normalized[0].get("column") in previous_fields
            and normalized[0].get("operator") == "or"
            and normalized[0].get("relation") == previous.get("relation")
            and normalized[0].get("value") == previous.get("value")
        ):
            normalized.pop(0)
    # Picking a suggestion is an exact label search; clearing the
    # field leaves one editable placeholder, not several empty OR conditions.
    active_columns = columns if value and relation == "EQI" else columns[:1]
    primary = [
        {**default_name_record(value), "column": column,
         "relation": relation, "operator": "begin" if index == 0 else "or"}
        for index, column in enumerate(active_columns)
    ]
    return normalize_records(primary + normalized)


def create_search_tab(
    section_key: str,
    title: str,
    *,
    tab_kind: str,
    limit: int,
    view_mode: str,
    records: Iterable[dict] | None = None,
    filters: Iterable | None = None,
    ensure_name_row: bool = False,
    tab_id: str = "",
    navigation_target: str = "",
    quick_filter_personalized: bool | None = None,
) -> SearchTabSession:
    """Create one runtime tab from any search source."""
    filter_records = normalize_records(records)
    if not filter_records:
        filter_records = records_from_filters(filters)
    if ensure_name_row:
        filter_records = set_primary_name(filter_records, "")
    return SearchTabSession(
        tab_id=tab_id or (
            f"{section_key}:{tab_kind}:{uuid.uuid4().hex[:8]}"
        ),
        title=title,
        tab_kind=tab_kind,
        navigation_target=navigation_target,
        extra_filters=filters_from_records(filter_records),
        filter_records=filter_records,
        limit=limit,
        view_mode=view_mode,
        quick_filter_personalized=(
            tab_kind not in STANDARD_QUICK_FILTER_TAB_KINDS
            if quick_filter_personalized is None
            else bool(quick_filter_personalized)
        ),
    )
