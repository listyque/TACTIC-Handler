"""Canonical search definitions shared by every modern search entry point.

The sidebar, the primary search field, Advanced Search, saved Search Views,
related-object navigation, and skey navigation do not own separate search
engines.  They all create or edit the same filter-card records stored by a
``SearchTabSession``.  Executable TACTIC filters are derived from those cards.
"""

from __future__ import annotations

from collections.abc import Iterable
import uuid

from .controllers.types import SearchTabSession


def default_name_record(value: str = "") -> dict:
    """Return the editable first row used by the legacy Search widget."""
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
) -> list[dict]:
    """Change the main search row without discarding preset constraints."""
    normalized = normalize_records(records)
    primary = default_name_record(value)
    primary["relation"] = relation
    if normalized and str(normalized[0].get("column") or "") == "name":
        normalized[0].update(primary)
    else:
        normalized.insert(0, primary)
    return normalize_records(normalized)


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
    )
