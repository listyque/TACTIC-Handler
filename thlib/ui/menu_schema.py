"""Procedural menu schemas consumed by QML.

Menu content lives on the Python side so callers can replace or extend any
menu at runtime without editing a QML component.
"""

from __future__ import annotations

import json
from pathlib import Path


def action(title: str, icon: str, command: str) -> dict:
    return {"title": title, "icon": icon, "command": command}


SEPARATOR = {"separator": True}


TOOL_WINDOWS = {}


DEFAULT_MENUS = {
    "tools": [],
    "result_filters": [
        action("Advanced Search", "advanced-search", "advanced_search"),
        action("Filter Processes", "filter-alt", "filter_processes"),
    ],
    "sobject": [
        action("Open scene / file", "movie", "open"),
        action("Save snapshot", "publish", "save"),
        action("Import snapshot", "file-import", "import"),
        action("Reference snapshot", "link", "reference"),
        SEPARATOR,
        action("Duplicate sObject", "control_point_duplicate", "duplicate"),
        action("Change preview", "image", "preview"),
        action("Paste snapshot from clipboard", "content_paste", "paste"),
        SEPARATOR,
        action("Open folder", "folder", "folder"),
        action("Copy search key", "key", "copy_skey"),
        action("Open on new tab", "tab", "new_tab"),
        action("SObject Info", "info", "sobject_info"),
        action("Edit info", "edit", "edit"),
        action("Delete sObject", "delete", "delete"),
        SEPARATOR,
        action("Edit DB table", "view_kanban", "db"),
        action("Ingest files", "publish", "ingest"),
    ],
    "snapshot_settings": [
        action("Show all", "visibility", "show_all"),
        action("Show more", "add", "show_more"),
        SEPARATOR,
        action("Horizontal orientation", "view_kanban", "horizontal"),
        action("Vertical orientation", "view_kanban", "vertical"),
    ],
    "snapshot": [
        action("Open file", "movie", "open"),
        action("Open file folder", "folder", "folder"),
        SEPARATOR,
        action("Copy path", "content_copy", "copy_path"),
        action("Copy web path", "link", "copy_web_path"),
        action("Copy to clipboard", "content_copy", "copy"),
        SEPARATOR,
        action("Edit info", "edit", "edit"),
        action("Delete", "delete", "delete"),
    ],
    "task": [
        action("Edit task", "edit", "edit"),
        action("Add task", "add_circle", "add"),
        action("Delete task", "delete", "delete"),
    ],
    "note": [
        action("Edit message", "edit", "edit"),
        action("Delete message", "delete", "delete"),
    ],
    "drop": [
        action("Open file", "movie", "open"),
        action("Open file folder", "folder", "folder"),
        SEPARATOR,
        action("Copy path", "content_copy", "copy_path"),
        action("Copy absolute path", "content_copy", "copy_absolute"),
        SEPARATOR,
        action("Add file", "add_circle", "add"),
        action("Paste from clipboard", "content_paste", "paste"),
    ],
    "repo_sync": [
        action("Sync selected", "repository-sync", "sync"),
        action("Remove from queue", "delete", "remove"),
    ],
    "commit": [
        action("Commit current", "publish", "commit"),
        action("Delete current", "delete", "delete"),
    ],
    "watch": [
        action("Enable watch", "check_circle", "enable"),
        action("Disable watch", "visibility_off", "disable"),
        action("Edit watch", "edit", "edit"),
        action("Delete watch", "delete", "delete"),
    ],
}


# Each product ships its own catalog; runtime replacements still belong to this registry.
_catalog = json.loads(
    (Path(__file__).parent / "qml/tactic_frame/shell/main.menus.json").read_text(
        encoding="utf-8"
    )
)
for _name, _actions in _catalog.items():
    DEFAULT_MENUS[_name] = [
        dict(item) for item in _actions if item.get("platform", "native") == "native"
    ]


class MenuRegistry:
    def __init__(self) -> None:
        self._menus = {
            name: [dict(item) for item in items]
            for name, items in DEFAULT_MENUS.items()
        }

    def actions(self, menu_id: str) -> list[dict]:
        return [dict(item) for item in self._menus.get(menu_id, ())]

    def replace(self, menu_id: str, actions: list[dict]) -> None:
        self._menus[menu_id] = [dict(item) for item in actions]

    def extend(self, menu_id: str, actions: list[dict]) -> None:
        self._menus.setdefault(menu_id, []).extend(dict(item) for item in actions)
