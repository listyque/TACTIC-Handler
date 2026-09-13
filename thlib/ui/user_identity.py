from __future__ import annotations


def _append_unique_file(result: list, seen: set[int], file_object) -> None:
    if file_object is None:
        return
    identity = id(file_object)
    if identity in seen:
        return
    seen.add(identity)
    result.append(file_object)


def user_avatar_file_candidates(login_object) -> list:
    """Return native avatar files from display quality to icon fallback.

    A login avatar snapshot normally contains an original main file plus web
    and icon derivatives.  The icon derivative is intentionally tiny and must
    not become the shared avatar source because the same URL is also rendered
    by the large profile control.  Consumers retain ownership of repository
    availability and download scheduling.
    """
    if login_object is None:
        return []
    processes = getattr(login_object, "process", {}) or {}
    result = []
    seen = set()
    for process_name in ("icon", "publish"):
        process = processes.get(process_name)
        contexts = getattr(process, "contexts", {}) if process else {}
        for context in (contexts or {}).values():
            versionless = getattr(context, "versionless", {}) or {}
            versions = getattr(context, "versions", {}) or {}
            snapshots = list(versionless.values()) or list(versions.values())
            for snapshot in reversed(snapshots):
                try:
                    grouped = snapshot.get_files_objects(
                        group_by="type"
                    ) or {}
                except (AttributeError, KeyError, TypeError):
                    continue
                preferred_types = (
                    "web", "preview", "image", "main", "icon"
                )
                files = [
                    file_object
                    for file_type in preferred_types
                    for file_object in (grouped.get(file_type) or [])
                ]
                files.extend(
                    file_object
                    for file_type, values in grouped.items()
                    if file_type not in preferred_types
                    for file_object in (values or [])
                )
                for file_object in files:
                    try:
                        web_preview = file_object.get_web_preview()
                    except (AttributeError, KeyError, TypeError):
                        web_preview = None
                    _append_unique_file(result, seen, web_preview)
                for file_type in ("web", "preview", "image", "main"):
                    for file_object in grouped.get(file_type) or []:
                        _append_unique_file(result, seen, file_object)
                for file_type, values in grouped.items():
                    if file_type in preferred_types:
                        continue
                    for file_object in values or []:
                        _append_unique_file(result, seen, file_object)
                for file_object in files:
                    try:
                        icon_preview = file_object.get_icon_preview()
                    except (AttributeError, KeyError, TypeError):
                        icon_preview = None
                    _append_unique_file(result, seen, icon_preview)
                for file_object in grouped.get("icon") or []:
                    _append_unique_file(result, seen, file_object)
    return result


def user_initials(display_name: str, login: str = "") -> str:
    """Return the shared two-letter fallback for a user identity."""
    label = str(display_name or login or "").strip()
    parts = [part for part in label.split() if part]
    return "".join(part[0] for part in parts[:2]).upper() or "?"


def user_avatar_color(login: str) -> str:
    """Return the stable avatar color derived only from login."""
    import thlib.global_functions as gf

    return str(gf.gen_color(str(login or "removed user").strip()))
