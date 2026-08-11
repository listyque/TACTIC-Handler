"""Watch-folder settings used by workspace state."""

from __future__ import annotations

def _watch_folder_settings(project) -> dict:
    """Read ui_watch_folder settings without constructing its QWidget."""
    if not project:
        return {}
    try:
        from thlib.environment import env_read_config
        settings = env_read_config(
            filename="ui_watch_folder",
            unique_id=f"ui_main/{project.get_type()}/{project.get_code()}",
            long_abs_path=True,
        ) or {}
        return dict(settings.get("watch_folders_dict") or {})
    except (AttributeError, KeyError, TypeError, OSError):
        return {}

def _watch_folder_record(project, search_key: str) -> dict:
    settings = _watch_folder_settings(project)
    keys = list(settings.get("assets_skeys") or [])
    try:
        index = keys.index(search_key)
    except ValueError:
        return {}

    def value(name, default=""):
        values = list(settings.get(name) or [])
        return values[index] if index < len(values) else default

    return {
        "asset_code": value("assets_codes"),
        "asset_name": value("assets_names"),
        "asset_stype": value("assets_stypes"),
        "asset_skey": search_key,
        "asset_pipeline": value("assets_pipelines"),
        "path": value("paths"),
        "rep": value("repos", []),
        "status": bool(value("statuses", False)),
        "idx": index,
    }
