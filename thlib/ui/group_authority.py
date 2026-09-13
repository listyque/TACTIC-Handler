"""Presentation-only ordering for TACTIC login groups.

TACTIC access rules remain authoritative for permissions.  This module only
chooses the most representative group when a login belongs to several groups.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET


_LEVEL_TIERS = {
    # Native pyasm.security.LoginGroup.ACCESS_DICT levels.
    "high": 700,
    "medium": 500,
    "low": 300,
    "min": 100,
    "none": 0,
}

_CAPABILITY_TIERS = (
    (900, ("security", "login_group", "login_in_group", "admin")),
    (750, ("supervisor", "approve", "approval", "work_hour", "cost")),
    (620, ("lead", "assign", "schedule", "milestone")),
    (500, ("delete", "create", "insert", "edit", "update", "write")),
    (250, ("read", "view")),
)

_PRESENTATION_FALLBACKS = (
    (1000, ("administrator", "admin")),
    (800, ("supervisor", "manager")),
    (650, ("lead",)),
    (100, ("guest", "viewer")),
)


def _normalized(value) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _explicit_tier(value) -> int | None:
    text = _normalized(value)
    if not text:
        return None
    return _LEVEL_TIERS.get(text)


def _rules_tier(access_rules) -> int:
    text = str(access_rules or "").strip()
    if not text:
        return 0
    fragments = []
    try:
        root = ET.fromstring(text)
        for element in root.iter():
            if element.tag.lower().endswith("rule"):
                access = _normalized(element.attrib.get("access"))
                if access in {"deny", "denied", "false", "no", "none"}:
                    continue
                fragments.append(" ".join(
                    str(value or "") for value in element.attrib.values()
                ))
    except (ET.ParseError, TypeError, ValueError):
        fragments.append(text)
    normalized = _normalized(" ".join(fragments))
    for tier, tokens in _CAPABILITY_TIERS:
        if any(token in normalized for token in tokens):
            return tier
    return 0


def _fallback_tier(record: dict) -> int:
    value = _normalized("%s %s" % (
        record.get("code") or "", record.get("label") or ""
    ))
    for tier, tokens in _PRESENTATION_FALLBACKS:
        if any(token in value for token in tokens):
            return tier
    return 300


def authority_sort_key(record: dict, project_code: str = "") -> tuple:
    """Return a stable descending authority key for presentation grouping."""
    explicit = _explicit_tier(record.get("accessLevel"))
    rules = _rules_tier(record.get("accessRules"))
    tier = max(
        explicit if explicit is not None else 0,
        rules,
        _fallback_tier(record),
    )
    group_project = str(record.get("projectCode") or "")
    project_match = int(bool(project_code) and group_project == project_code)
    global_group = int(not group_project)
    is_default = int(bool(record.get("isDefault")))
    subgroups = len(record.get("subGroups") or [])
    return (
        tier,
        project_match,
        global_group,
        is_default,
        subgroups,
        str(record.get("label") or record.get("code") or "").casefold(),
    )


def ranked_groups(records, project_code: str = "") -> list[dict]:
    """Return group records with the representative group first."""
    def order(record):
        tier, project, global_group, default, subgroups, label = (
            authority_sort_key(record, project_code)
        )
        return (-tier, -project, -default, -subgroups, -global_group, label)

    return sorted((dict(record) for record in (records or [])), key=order)


def primary_group(records, project_code: str = "") -> dict:
    groups = ranked_groups(records, project_code)
    return groups[0] if groups else {}
