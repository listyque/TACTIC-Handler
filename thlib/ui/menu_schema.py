"""Procedural menu schemas consumed by QML.

Menu content lives on the Python side so callers can replace or extend any
menu at runtime without editing a QML component.
"""

from __future__ import annotations


def action(title: str, icon: str, command: str) -> dict:
    return {"title": title, "icon": icon, "command": command}


SEPARATOR = {"separator": True}


def tool_action(
        title: str,
        icon: str,
        command: str = "",
        status: str = "",
        enabled: bool = True) -> dict:
    return {
        "title": title,
        "icon": icon,
        "command": command,
        "status": status,
        "enabled": enabled,
    }


def tool_header(title: str) -> dict:
    return {"title": title, "header": True}


TOOL_WINDOWS = {
    "tool_columns_editor": "columns_editor",
    "tool_update": "update",
    "tool_create_update": "create_update",
}


DEFAULT_MENUS = {
    "user": [
        action("My Profile", "account_circle", "show_user_profile"),
        action("Users", "users", "show_users"),
        action("Messages", "comment", "show_messages"),
        SEPARATOR,
        action("Sign Out", "logout", "sign_out"),
    ],
    "configuration": [
        action("Configuration", "settings", "open_configuration"),
        action("Administration", "security", "show_administration"),
        action(
            "Tools",
            "dashboard_customize",
            "show_tools",
        ),
        action("Save Preferences", "save", "save_preferences"),
        action("Reload Cache", "refresh", "reload_cache"),
        action("Current view to All Tabs", "layers", "apply_view_to_all_tabs"),
        action(
            "Reset workspace layout",
            "restart-alt",
            "reset_workspace_layout",
        ),
        SEPARATOR,
        action("Script Editor", "code", "open_script_editor"),
        action("Debug Log", "bug_report", "show_debug_log"),
        action("UI responsiveness", "ui-performance", "show_ui_performance"),
        action(
            "Repository Sync Queue",
            "repository-sync",
            "show_repository_sync",
        ),
        action("Watch Folders", "folder_special", "show_watch_folders"),
        action("TACTIC Handler Server", "hub", "show_handler_server"),
        action("Help", "help", "show_help"),
        SEPARATOR,
        action("Exit", "logout", "exit"),
    ],
    "tools": [
        tool_header("Editors"),
        tool_action("Columns Editor", "view_column", "tool_columns_editor"),
        SEPARATOR,
        tool_header("Integrations and Service Tools"),
        tool_action("Update", "download", "tool_update", "Experimental"),
        tool_action(
            "Create Update",
            "archive",
            "tool_create_update",
            "Experimental",
        ),
    ],
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


class MenuRegistry:
    def __init__(self) -> None:
        self._menus = {name: [dict(item) for item in items] for name, items in DEFAULT_MENUS.items()}

    def actions(self, menu_id: str) -> list[dict]:
        return [dict(item) for item in self._menus.get(menu_id, ())]

    def replace(self, menu_id: str, actions: list[dict]) -> None:
        self._menus[menu_id] = [dict(item) for item in actions]

    def extend(self, menu_id: str, actions: list[dict]) -> None:
        self._menus.setdefault(menu_id, []).extend(dict(item) for item in actions)
