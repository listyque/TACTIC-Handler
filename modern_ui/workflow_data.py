from __future__ import annotations

import json


def _mapping(value) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return dict(value) if isinstance(value, dict) else {}
    return {}


def process_task_configuration(pipeline, process) -> dict:
    """Return task properties defined by one native workflow process."""
    if pipeline is None or not process:
        return {}
    try:
        process_info = dict(pipeline.get_process_info(process) or {})
    except (AttributeError, TypeError, ValueError):
        process_info = {}
    try:
        process_object = dict(
            pipeline.get_pipeline_process(process) or {}
        )
    except (AttributeError, TypeError, ValueError):
        process_object = {}
    workflow = _mapping(
        process_object.get("workflow") or process_info.get("workflow")
    )
    properties = _mapping(workflow.get("properties"))
    values = dict(process_info)
    # Runtime values describe the last workflow editor, not task defaults.
    runtime_only_keys = {"assigned", "supervisor"}
    for source in (process_object, workflow, properties):
        for key, value in source.items():
            if key in runtime_only_keys and source is not properties:
                continue
            if value not in (None, ""):
                values[key] = value
    if not values.get("type") and values.get("node_type"):
        values["type"] = values["node_type"]
    return values
