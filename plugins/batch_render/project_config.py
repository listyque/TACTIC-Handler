"""Batch project config functions."""
from __future__ import annotations


BATCH_DISPATCHER_CONFIG = {
    "project_config": {
        "episode_search_type": "complex/scenes",
        "shot_search_type": "complex/shot",
        "scene_process": "publish",
        "cache_process": "cache",
        "render_process": "render",
        "render_sync_preset": "render_sync",
        "rendered_field": "rendered",
        "cache_path": "niki_friends/cache/nCache",
        "asset_search_type": "dolly3d/assets",
        "alembic_category": "cache/abc",
        "alembic_cache_path": "cache/alembic",
        "queue_statuses": ["Рендер", "В очереди"],
        "status_options": ["Подготовлен", "Рендер", "В очереди", "Проверен"],
        "running_status": "Рендерится",
        "complete_status": "Готов",
        "failed_status": "Ошибки",
        "terminal_status": "Проверен",
        "maya_render_executable": "C:/Program Files/Autodesk/Maya2022/bin/Render.exe",
        "output_directory": "D:/sequences_path",
        "camera": "ubercam",
        "update_interval": 10,
        "stop_on_error": False,
        "skip_dependency_errors": False,
        "render_timeout_minutes": 0,
        "log_checkin": "always",
        "web_enabled": True,
        "web_port": 92,
        "web_security": True,
    },
}


def _preset_state(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "2",
            "true",
            "on",
            "yes",
            "checked",
            "enabled",
        }
    return bool(value)


def _preset_items(mapping: dict, suffix: str, enabled=False) -> dict:
    return {
        str(key).removesuffix(suffix): value
        for key, value in (mapping or {}).items()
        if str(key).endswith(suffix)
        and isinstance(value, dict)
        and (not enabled or _preset_state(value.get("state")))
    }
