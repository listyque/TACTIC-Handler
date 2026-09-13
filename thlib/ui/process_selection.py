"""Shared TACTIC process-selection tree construction."""

from __future__ import annotations


PROCESS_SELECTION_ROLES = (
    "nodeId", "parentId", "dataKey", "key", "title", "subtitle",
    "kind", "group", "depth", "checkable", "checked", "expanded",
    "rowVisible", "selected", "accent", "hasChildren",
)


def resolve_process_selection_context(context: dict) -> tuple[object, object]:
    """Resolve an already-loaded native SearchType and Project.

    Search windows can become visible before the active tab has copied its
    ``stype`` reference. The project and Search Type code are nevertheless
    already part of the window context, so use the project's native
    ``stypes`` collection instead of leaving both process trees empty. This
    helper deliberately performs no server query.
    """
    context = dict(context or {})
    sobject = context.get("sobject")
    stype = context.get("stype")
    if stype is None and sobject is not None:
        try:
            stype = sobject.get_stype()
        except (AttributeError, KeyError, TypeError):
            stype = None

    project = context.get("project")
    if project is None and stype is not None:
        try:
            project = stype.get_project()
        except (AttributeError, KeyError, TypeError):
            project = getattr(stype, "project", None)
    if project is None:
        project_code = str(context.get("project_code") or "")
        if project_code:
            try:
                from thlib.environment import env_inst

                project = (env_inst.projects or {}).get(project_code)
            except (AttributeError, KeyError, TypeError):
                project = None

    if stype is None and project is not None:
        search_type = str(context.get("search_type") or "")
        project_stypes = getattr(project, "stypes", None) or {}
        if search_type:
            stype = project_stypes.get(search_type)
    return stype, project


def _info(source) -> dict:
    return dict(getattr(source, "info", None) or {})


def _pipeline_values(stype) -> list:
    pipelines = getattr(stype, "pipeline", None)
    if pipelines is None:
        try:
            pipelines = stype.get_pipeline()
        except (AttributeError, KeyError, TypeError):
            pipelines = None
    pipelines = pipelines or {}
    if hasattr(pipelines, "values"):
        return list(pipelines.values())
    return list(pipelines.itervalues())


def _pipeline_processes(pipeline) -> list[tuple[str, object]]:
    processes = (
        getattr(pipeline, "pipeline", None)
        or getattr(pipeline, "process", None)
        or {}
    )
    if hasattr(processes, "items"):
        return [(str(key), value) for key, value in processes.items()]
    return [(str(key), value) for key, value in processes.iteritems()]


def _schema(stype):
    schema = getattr(stype, "schema", None)
    if schema is not None:
        return schema
    try:
        return stype.get_schema()
    except (AttributeError, KeyError, TypeError):
        return None


def _stype_code(stype) -> str:
    try:
        return str(stype.get_code() or "")
    except (AttributeError, TypeError):
        return str(_info(stype).get("code") or "")


def _stype_title(stype) -> str:
    try:
        value = stype.get_pretty_name()
    except (AttributeError, KeyError, TypeError):
        value = ""
    info = _info(stype)
    return str(
        value or info.get("title") or info.get("name")
        or info.get("code") or ""
    )


def _stype_color(stype) -> str:
    try:
        value = stype.get_stype_color(fmt="hex")
    except (AttributeError, KeyError, TypeError):
        value = _info(stype).get("color")
    if isinstance(value, (tuple, list)) and len(value) >= 3:
        try:
            return "#{:02x}{:02x}{:02x}".format(*map(int, value[:3]))
        except (TypeError, ValueError):
            return ""
    return str(value or "")


def _process_info(pipeline, process: str, source) -> dict:
    try:
        result = dict(pipeline.get_pipeline_process(process) or {})
    except (AttributeError, KeyError, TypeError):
        result = {}
    if result:
        return result
    try:
        result = dict(pipeline.get_process_info(process) or {})
    except (AttributeError, KeyError, TypeError):
        result = dict(source) if isinstance(source, dict) else {}
    return result


def _record(
        node_id: str,
        parent_id: str,
        data_key: str,
        key: str,
        title: str,
        subtitle: str,
        kind: str,
        group: str,
        depth: int,
        checked: bool,
        accent: str = "",
) -> dict:
    return {
        "nodeId": node_id,
        "parentId": parent_id,
        "dataKey": data_key,
        "key": key,
        "title": title,
        "subtitle": subtitle,
        "kind": kind,
        "group": group,
        "depth": depth,
        "checkable": kind != "pipeline",
        "checked": bool(checked),
        "expanded": True,
        "rowVisible": True,
        "selected": False,
        "accent": accent,
        "hasChildren": False,
    }


def build_process_selection_tree(
        stype,
        project=None,
        *,
        checked_kinds: frozenset[str] = frozenset(),
) -> list[dict]:
    """Build the recursive tree used by Repository Sync.

    The order deliberately matches ``Ui_repoSyncDialog``: built-ins and
    pipelines for the current Search Type, followed by each child Search Type
    containing its own built-ins, pipelines, processes, and descendants.
    """
    if stype is None:
        return []
    if project is None:
        try:
            project = stype.get_project()
        except (AttributeError, KeyError, TypeError):
            project = getattr(stype, "project", None)
    project_stypes = getattr(project, "stypes", None) or {}
    records: list[dict] = []

    def checked(kind: str) -> bool:
        return kind in checked_kinds

    def append_stype(
            current,
            parent_id: str,
            depth: int,
            ancestors: tuple[str, ...],
    ) -> None:
        stype_code = _stype_code(current)
        for builtin in ("publish", "attachment", "icon"):
            records.append(_record(
                f"{parent_id or 'root'}:builtin:{builtin}",
                parent_id,
                f"{builtin}:{{b}}",
                builtin,
                builtin.title(),
                "Built-in process",
                "builtin",
                "",
                depth,
                checked("builtin"),
            ))

        for pipeline_index, pipeline in enumerate(_pipeline_values(current)):
            info = _info(pipeline)
            code = str(
                info.get("code") or info.get("name")
                or f"pipeline_{pipeline_index}"
            )
            title = str(info.get("name") or info.get("code") or code)
            pipeline_id = (
                f"{parent_id or 'root'}:pipeline:{pipeline_index}:{code}"
            )
            records.append(_record(
                pipeline_id,
                parent_id,
                f"{code}:{{pp}}",
                code,
                title,
                "Pipeline",
                "pipeline",
                code,
                depth,
                False,
                str(info.get("color") or ""),
            ))
            for process_index, (process, source) in enumerate(
                _pipeline_processes(pipeline)
            ):
                process_info = _process_info(pipeline, process, source)
                records.append(_record(
                    f"{pipeline_id}:process:{process_index}:{process}",
                    pipeline_id,
                    f"{process}:{{pr}}",
                    process,
                    process.capitalize(),
                    str(process_info.get("type") or "Process"),
                    "process",
                    code,
                    depth + 1,
                    checked("process"),
                    str(
                        process_info.get("color")
                        or info.get("color") or ""
                    ),
                ))

        for relation_index, relation in enumerate(
            getattr(_schema(current), "children", None) or ()
        ):
            if relation.get("type") == "many_to_many":
                continue
            child_code = str(relation.get("from") or "")
            # Match legacy Ui_repoSyncDialog recursion: a child Search Type
            # may repeat once (Asset -> Asset, Texture -> Asset, etc.). Only
            # stop when the next edge returns to an earlier ancestor above
            # the immediate parent; this keeps the useful nested branch while
            # still breaking cycles.
            if not child_code or child_code in ancestors[:-1]:
                continue
            child_stype = project_stypes.get(child_code)
            if child_stype is None:
                continue
            child_id = (
                f"{parent_id or 'root'}:child:{relation_index}:{child_code}"
            )
            records.append(_record(
                child_id,
                parent_id,
                f"{child_code}:{{s}}",
                child_code,
                _stype_title(child_stype) or child_code,
                "Child Search Type",
                "child",
                "",
                depth,
                checked("child"),
                _stype_color(child_stype),
            ))
            append_stype(
                child_stype, child_id, depth + 1, (*ancestors, child_code)
            )

    append_stype(stype, "", 0, ())
    parent_ids = {
        str(record.get("parentId") or "") for record in records
        if record.get("parentId")
    }
    for record in records:
        record["hasChildren"] = record.get("nodeId") in parent_ids
    return records


__all__ = [
    "PROCESS_SELECTION_ROLES",
    "build_process_selection_tree",
    "resolve_process_selection_context",
]
