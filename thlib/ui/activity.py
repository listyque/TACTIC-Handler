from __future__ import annotations

import json
import uuid

from thlib.ui.user_identity import user_avatar_color, user_initials


# Chat correspondence has its own unread and presentation contract. These are
# every event kind owned by the read-only activity journal used by both the
# feed and user profiles.
JOURNAL_ACTIVITY_KINDS = (
    "status",
    "publication",
    "note",
    "task",
    "create",
    "change",
    "delete",
    "work_hour",
)


def activity_timestamp_labels(value: str, clock=None) -> tuple[str, str]:
    """Use the same relative/full date presentation as TACTIC objects."""
    timestamp = str(value or "").strip()
    if not timestamp:
        return "", ""
    try:
        import thlib.global_functions as gf

        parsed = (
            clock.presentation_datetime(timestamp)
            if clock is not None else gf.parce_timestamp(timestamp)
        )
        return (
            str(gf.get_pretty_datetime(parsed) or ""),
            str(gf.get_full_datetime(parsed) or ""),
        )
    except (AttributeError, TypeError, ValueError):
        # Raw transport timestamps are diagnostic data, not a UI fallback.
        return "", ""


def activity_actor_logins(source) -> set[str]:
    """Return stable actor logins carried by a raw or enriched event."""
    source = dict(source or {})
    values = [
        source.get("actor"), source.get("__actor__"), source.get("login"),
    ]
    changed_by = source.get("changed_by") or source.get("changedBy") or {}
    if isinstance(changed_by, str):
        try:
            changed_by = json.loads(changed_by)
        except (TypeError, ValueError):
            changed_by = {}
    if isinstance(changed_by, dict):
        values.extend(changed_by.values())
    elif isinstance(changed_by, (list, tuple, set)):
        values.extend(changed_by)
    return {
        str(value or "").strip().casefold()
        for value in values
        if str(value or "").strip()
    }


def present_activity_records(
        sources, users, profile: dict | None = None
) -> list[dict]:
    """Project shared user-directory identity onto activity records."""
    identities = {
        str(user.get("login") or "").casefold(): dict(user)
        for user in (users or [])
        if user.get("login")
    }
    profile = dict(profile or {})
    if profile.get("login"):
        identities[str(profile["login"]).casefold()] = profile

    records = []
    for source in sources or []:
        record = dict(source or {})
        actor = str(record.get("actor") or "")
        server_generated = bool(record.get("serverGenerated"))
        identity = identities.get(actor.casefold(), {})
        actor_login = str(identity.get("login") or actor)
        actor_label = str(
            identity.get("displayName")
            or record.get("actorLabel")
            or actor
        )
        record.update({
            "actorLabel": actor_label,
            "actorAvatar": str(
                identity.get("avatarUrl")
                or record.get("actorAvatar")
                or ""
            ),
            "actorInitials": str(
                identity.get("initials")
                or record.get("actorInitials")
                or ("" if server_generated else user_initials(
                    actor_label, actor_login
                ))
            ),
            "actorColor": str(
                identity.get("avatarColor")
                or user_avatar_color(actor_login or actor_label)
            ),
        })
        _apply_activity_colors(record)
        records.append(record)
    return records


def _apply_activity_colors(record: dict) -> None:
    """Project cached Search Type and process colors onto one feed event."""
    try:
        from thlib.environment import env_inst
        from thlib.ui.workflow_data import process_task_configuration

        project = (env_inst.projects or {}).get(str(record.get("project") or ""))
        stype_code = str(record.get("targetType") or "").split("?", 1)[0]
        stype = (project.get_stypes() or {}).get(stype_code) if project else None
        if stype:
            if not record.get("typeColor"):
                record["typeColor"] = str(
                    stype.get_stype_color(fmt="hex") or ""
                )
            if (
                    record.get("relationAction")
                    and not record.get("targetTypeTitle")):
                pretty_name = getattr(stype, "get_pretty_name", None)
                if callable(pretty_name):
                    record["targetTypeTitle"] = str(pretty_name() or "")

        item_stype_code = str(
            record.get("itemType") or ""
        ).split("?", 1)[0]
        item_stype = (
            (project.get_stypes() or {}).get(item_stype_code)
            if project and item_stype_code else None
        )
        if item_stype:
            if not record.get("itemTypeColor"):
                record["itemTypeColor"] = str(
                    item_stype.get_stype_color(fmt="hex") or ""
                )
            if not record.get("itemTypeTitle"):
                pretty_name = getattr(item_stype, "get_pretty_name", None)
                if callable(pretty_name):
                    record["itemTypeTitle"] = str(pretty_name() or "")
        process = str(record.get("process") or "")
        if not stype or not process:
            return
        pipelines = stype.get_pipeline() or {}
        pipeline_code = str(record.get("pipelineCode") or "")
        candidates = []
        if pipeline_code and pipelines.get(pipeline_code):
            candidates.append(pipelines[pipeline_code])
        candidates.extend(
            pipeline for code, pipeline in pipelines.items()
            if code != pipeline_code
        )
        matched_configuration = {}
        for pipeline in candidates:
            configuration = process_task_configuration(pipeline, process)
            if not configuration:
                continue
            matched_configuration = configuration
            if not record.get("processColor"):
                record["processColor"] = str(
                    configuration.get("color") or ""
                )
            break

        statuses = {
            str(record.get("statusBefore") or ""),
            str(record.get("statusAfter") or ""),
        } - {""}
        if not statuses:
            return
        workflow = stype.get_workflow()
        task_pipeline_code = str(
            matched_configuration.get("task_pipeline") or ""
        )
        process_type = matched_configuration.get("type")
        task_pipeline = (
            workflow.get_by_pipeline_code("sthpw/task", task_pipeline_code)
            if task_pipeline_code else
            workflow.get_by_process_node_type("sthpw/task", process_type)
        )
        status_records = task_pipeline.pipeline or {}
        for field in ("statusBefore", "statusAfter"):
            value = str(record.get(field) or "")
            status_info = dict(status_records.get(value) or {})
            record[field + "Color"] = str(status_info.get("color") or "")
    except (AttributeError, KeyError, TypeError, ValueError):
        return


def activity_record(
        source, *, default_actor: str = "", default_project: str = "",
        clock=None,
) -> dict:
    """Normalize the shared TACTIC activity entity for every application view."""
    source = dict(source or {})
    search_key = str(source.get("searchKey") or "")
    target_key = str(source.get("targetSearchKey") or "")
    actor = str(source.get("actor") or default_actor)
    actor_label = str(source.get("actorLabel") or actor)
    timestamp = str(source.get("timestamp") or "")
    timestamp_pretty, timestamp_full = activity_timestamp_labels(
        timestamp, clock
    )
    work_day = str(source.get("workDay") or "")
    work_day_pretty, _work_day_full = activity_timestamp_labels(work_day)
    try:
        hours = float(source.get("hours") or 0.0)
    except (TypeError, ValueError):
        hours = 0.0
    server_generated = bool(source.get("serverGenerated"))
    return {
        "eventId": str(
            source.get("eventId") or search_key or uuid.uuid4().hex
        ),
        "kind": str(source.get("kind") or "activity"),
        "title": str(source.get("title") or "Activity"),
        "detail": str(source.get("detail") or ""),
        "actor": actor,
        "actorLabel": actor_label,
        "actorAvatar": str(source.get("actorAvatar") or ""),
        "actorInitials": str(
            source.get("actorInitials")
            or ("" if server_generated else user_initials(actor_label, actor))
        ),
        "actorColor": str(
            source.get("actorColor")
            or user_avatar_color(actor or actor_label)
        ),
        "timestamp": timestamp,
        "timestampPretty": str(
            timestamp_pretty
            or (source.get("timestampPretty") if not timestamp else "")
            or ""
        ),
        "timestampFull": str(
            timestamp_full
            or (source.get("timestampFull") if not timestamp else "")
            or ""
        ),
        "searchKey": search_key,
        "targetSearchKey": target_key,
        "targetTitle": str(source.get("targetTitle") or ""),
        "targetType": str(source.get("targetType") or ""),
        "targetTypeTitle": str(source.get("targetTypeTitle") or ""),
        "pipelineCode": str(source.get("pipelineCode") or ""),
        "typeColor": str(source.get("typeColor") or ""),
        "processColor": str(source.get("processColor") or ""),
        "itemCode": str(source.get("itemCode") or ""),
        "itemTitle": str(source.get("itemTitle") or ""),
        "itemType": str(source.get("itemType") or ""),
        "itemTypeTitle": str(source.get("itemTypeTitle") or ""),
        "itemTypeColor": str(source.get("itemTypeColor") or ""),
        "relationAction": str(source.get("relationAction") or ""),
        "project": str(source.get("project") or default_project),
        "process": str(source.get("process") or ""),
        "context": str(source.get("context") or ""),
        "taskCode": str(source.get("taskCode") or ""),
        "hours": hours,
        "workDay": work_day,
        "workDayPretty": str(
            source.get("workDayPretty") or work_day_pretty
        ),
        "workHourAction": str(source.get("workHourAction") or ""),
        "workHourCategory": str(source.get("workHourCategory") or ""),
        "workHourStatus": str(source.get("workHourStatus") or ""),
        "workHourOwner": str(source.get("workHourOwner") or ""),
        "serverGenerated": server_generated,
        "statusBefore": str(source.get("statusBefore") or ""),
        "statusAfter": str(source.get("statusAfter") or ""),
        "changes": [
            dict(change) for change in (source.get("changes") or ())
            if isinstance(change, dict)
        ],
        "statusBeforeColor": str(source.get("statusBeforeColor") or ""),
        "statusAfterColor": str(source.get("statusAfterColor") or ""),
        "version": str(source.get("version") or ""),
        "canOpen": bool(search_key or target_key),
    }
