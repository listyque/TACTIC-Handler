"""TACTIC Search View parsing and preset discovery.

The sidebar, Advanced Search, and preset editor all consume the same
``config/widget_config`` payload.  Keeping that translation here prevents the
three interfaces from interpreting the same server record differently.
"""

from __future__ import annotations

from xml.etree import ElementTree


def records_from_packed(packed) -> list[dict]:
    """Convert TACTIC's packed Search View rows to filter cards."""
    import thlib.tactic_classes as tc

    packed = [item for item in (packed or []) if isinstance(item, dict)]
    main = [item for item in packed if item.get("prefix") == "main_body"]
    search_ops = next(
        (item for item in packed if item.get("prefix") == "search_ops"),
        {},
    )
    ops = list(search_ops.get("ops") or [])
    relation_names = {
        str(label).strip().casefold(): value
        for label, value in tc.get_match_list_by_type("all")
    }
    records: list[dict] = []
    for source_index, item in enumerate(main):
        raw_relation = item.get("main_body_relation")
        relation = raw_relation
        if raw_relation == "expression":
            relation = item.get("main_body_op")
        elif raw_relation is not None:
            relation = relation_names.get(
                str(raw_relation).strip().casefold(),
                raw_relation,
            )
        record_index = len(records)
        records.append({
            "column": item.get("main_body_column"),
            "relation": relation,
            "value": item.get("main_body_value"),
            "rowEnabled": item.get("main_body_enabled") == "on",
            "operator": (
                "begin" if record_index == 0
                else "or"
                if source_index - 1 < len(ops)
                and ops[source_index - 1] == "or"
                else "and"
            ),
            "isDefault": record_index == 0,
        })
    return records


def records_from_config(config: str) -> list[dict]:
    """Read filter cards from a ``config/widget_config.config`` XML value."""
    import json

    root = ElementTree.fromstring(str(config or ""))
    node = root.find("./filter/values")
    packed = json.loads(node.text or "[]") if node is not None else []
    return records_from_packed(packed)


def records_from_definition(definition) -> list[dict]:
    """Read filter cards from a parsed TACTIC Search View definition."""
    import thlib.global_functions as gf

    values = definition.find("values") if definition else None
    if not values or not values.string:
        return []
    return records_from_packed(gf.from_json(values.string) or [])


def preset_title(row: dict) -> str:
    """Return the readable preset title without project hardcoding."""
    view = str(row.get("view") or "")
    title = str(row.get("title") or "").strip()
    if title and title != view:
        return title
    parts = view.split(":")
    title = parts[1] if len(parts) > 1 else view
    title = title.replace("_", " ").strip()
    return title[:1].upper() + title[1:] if title else "Preset"


def query_search_presets(
    project_code: str,
    search_type: str,
    tab_name: str = "",
) -> list[dict]:
    """Query all Search Type presets or one exact Search View namespace."""
    import thlib.tactic_classes as tc

    # Search Type fields in config/widget_config contain the plain server
    # code. Runtime search keys may append a project query string; it is not
    # part of the Saved Search namespace.
    search_type = str(search_type or "").split("?", 1)[0]
    tab_name = str(tab_name or "").strip()
    if not project_code or not search_type:
        return []

    server = tc.server_start(project=project_code)
    # A scoped sidebar entry follows the original Ui_filterEditorDialog
    # contract: ``tab_name`` is its complete customized Search View name.
    # A plain Search Type tab intentionally omits it and acts as the editor's
    # library of every link_search row for that Search Type.
    filters = [("search_type", search_type)]
    if tab_name:
        filters.insert(0, ("view", "like", f"%{tab_name}"))
    rows = server.query(
        "config/widget_config",
        filters,
        ["code", "view", "title", "description", "config"],
    )
    return presets_from_rows(rows, tab_name, search_type)


def query_search_preset(
    project_code: str,
    search_type: str,
    view: str,
) -> dict | None:
    """Resolve one exact Saved Search link through the native config row."""
    import thlib.tactic_classes as tc

    project_code = str(project_code or "").strip()
    search_type = str(search_type or "").split("?", 1)[0].strip()
    view = str(view or "").strip()
    if not project_code or not search_type or not view:
        return None
    server = tc.server_start(project=project_code)
    rows = server.query(
        "config/widget_config",
        [("view", view), ("search_type", search_type)],
        ["code", "view", "title", "description", "config"],
    )
    return next((
        preset
        for preset in presets_from_rows(rows, "", search_type)
        if preset.get("view") == view
    ), None)


def presets_from_rows(
    rows,
    tab_name: str = "",
    search_type: str = "",
) -> list[dict]:
    """Parse Handler-owned link_search rows for one Search Type."""
    tab_name = str(tab_name or "").strip()
    search_type = str(search_type or "").split("?", 1)[0].strip()
    if not search_type and tab_name:
        search_type = tab_name.partition("@")[0]
    suffix = f":{tab_name}" if tab_name else ""
    result = []
    seen = set()
    for row in rows or []:
        # SQL LIKE treats underscores inside sidebar names as wildcards. The
        # original intention is still an exact tab suffix, so reject rows for
        # sibling sidebar links sharing the same Search Type.
        view = str(row.get("view") or "")
        if not view.startswith("link_search:"):
            continue
        # TACTIC's web UI stores its own link_search rows in the same table
        # and Search Type. TACTIC Handler deliberately owns only the namespace
        # encoded by the third view segment:
        #   link_search:<preset>:<search_type>[@<sidebar_entry>]
        # This prevents native web presets from leaking into Advanced Search.
        parts = view.split(":", 2)
        namespace = parts[2] if len(parts) == 3 else ""
        if search_type and not (
            namespace == search_type
            or namespace.startswith(f"{search_type}@")
        ):
            continue
        if suffix and not view.endswith(suffix):
            continue
        identity = str(row.get("code") or view)
        if identity in seen:
            continue
        seen.add(identity)
        try:
            records = records_from_config(str(row.get("config") or ""))
        except (ElementTree.ParseError, ValueError, TypeError):
            records = []
        result.append({
            "code": str(row.get("code") or ""),
            "view": view,
            "title": preset_title(row),
            "description": row.get("description"),
            "records": records,
        })
    return result
