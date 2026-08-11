from __future__ import annotations

import uuid


def activity_record(
        source, *, default_actor: str = "", default_project: str = ""
) -> dict:
    """Normalize the shared TACTIC activity entity for every modern view."""
    source = dict(source or {})
    search_key = str(source.get("searchKey") or "")
    target_key = str(source.get("targetSearchKey") or "")
    return {
        "eventId": str(
            source.get("eventId") or search_key or uuid.uuid4().hex
        ),
        "kind": str(source.get("kind") or "activity"),
        "title": str(source.get("title") or "Activity"),
        "detail": str(source.get("detail") or ""),
        "actor": str(source.get("actor") or default_actor),
        "timestamp": str(source.get("timestamp") or ""),
        "searchKey": search_key,
        "targetSearchKey": target_key,
        "targetTitle": str(source.get("targetTitle") or ""),
        "targetType": str(source.get("targetType") or ""),
        "project": str(source.get("project") or default_project),
        "process": str(source.get("process") or ""),
        "context": str(source.get("context") or ""),
        "version": str(source.get("version") or ""),
        "canOpen": bool(search_key or target_key),
    }
