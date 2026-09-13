from __future__ import annotations


def _list_value(value):
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        return value.split("|") if "|" in value else ([value] if value else [])
    return []


def _choices(source):
    source = dict(source or {})
    display = source.get("__display_values__")
    action = dict(source.get("action_options") or {})
    kwargs = dict(source.get("kwargs") or {})
    values = _list_value(source.get("values"))
    labels = _list_value(source.get("labels"))
    if isinstance(display, dict):
        if not values:
            values = _list_value(display.get("values"))
        if not labels:
            labels = _list_value(display.get("labels"))
    if not values:
        values = _list_value(action.get("values") or kwargs.get("values"))
    if not labels:
        labels = _list_value(action.get("labels") or kwargs.get("labels"))
    result = []
    for index, value in enumerate(values):
        result.append({
            "value": value,
            "label": str(labels[index] if index < len(labels) else value),
            "color": "",
        })
    return result


def _ensure_empty_choice(choices, label):
    result = [dict(item) for item in choices or []]
    empty = next((
        item for item in result
        if str(item.get("value") or "") == ""
    ), None)
    if empty is None:
        result.insert(0, {"value": "", "label": label, "color": ""})
    elif not str(empty.get("label") or "").strip():
        empty["label"] = label
    return result


def load_task_field_catalog(
        project_code, parent_search_key="", include_milestones=True):
    """Load project-stable task field data in one worker operation.

    The caller owns the per-project cache. Widget configuration is resolved by
    TACTIC itself; this module only converts its public input-widget result.
    A parent is optional and must be a native sObject search key, never a
    Search Type scope token or a Handler navigation link.
    """
    from thlib import tactic_classes as tc
    from thlib import tactic_query as tq
    import traceback

    result = {
        "priorityChoices": [{
            "value": "", "label": "No priority", "color": "",
        }],
        "milestoneChoices": [{
            "value": "", "label": "No milestone", "dueDate": "",
        }],
        "errors": [],
        "tracebacks": [],
    }
    try:
        edit = tc.execute_procedure_serverside(
            tq.query_EditWdg,
            {
                "args": {
                    "mode": "insert",
                    "input_prefix": "insert",
                    "search_key": "",
                    "parent_key": str(parent_search_key or "") or None,
                    "search_type": "sthpw/task",
                    "view": "insert",
                },
                "search_type": "sthpw/task",
            },
            project=project_code,
        )
        widgets = list((edit or {}).get("InputWidgets") or [])
        priority = next((
            item for item in widgets
            if str(dict(item or {}).get("name") or "") == "priority"
            or str(dict(dict(item or {}).get("action_options") or {}).get(
                "column"
            ) or "") == "priority"
        ), None)
        result["priorityChoices"] = _ensure_empty_choice(
            _choices(priority), "No priority"
        )
    except Exception as exc:
        result["errors"].append("Priority configuration: {}".format(exc))
        result["tracebacks"].append(traceback.format_exc())

    if include_milestones:
        try:
            server = tc.server_start(project=project_code)
            milestones = server.query(
                "sthpw/milestone",
                filters=[("project_code", project_code)],
                columns=["code", "description", "due_date"],
                order_bys=["due_date", "description"],
            )
            result["milestoneChoices"] = [{
                "value": "", "label": "No milestone", "dueDate": "",
            }] + [{
                "value": str(item.get("code") or ""),
                "label": str(
                    item.get("description")
                    or item.get("code") or "Milestone"
                ),
                "dueDate": str(item.get("due_date") or ""),
            } for item in milestones or [] if item.get("code")]
        except Exception as exc:
            result["errors"].append("Milestones: {}".format(exc))
            result["tracebacks"].append(traceback.format_exc())

    return result
