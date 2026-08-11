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


TEMPORARY_TOOL_WINDOWS = {
    "temporary_configuration": "configuration",
    "temporary_filter_editor": "filter_editor",
    "temporary_repository_editor": "repository_editor",
    "temporary_add_sobject": "add_sobject",
    "temporary_link_sobjects": "link_sobjects",
    "temporary_messages": "messages",
    "temporary_chat_messages": "messages",
    "temporary_notifications": "notifications",
    "temporary_activity_feed": "activity_feed",
    "temporary_attachments": "attachments_editor",
    "temporary_columns_editor": "columns_editor",
    "temporary_naming_editor": "naming_editor",
    "temporary_preview_editor": "preview_editor",
    "temporary_attachments_editor": "attachments_editor",
    "temporary_matching_templates": "matching_templates",
    "temporary_script_editor": "script_editor",
    "temporary_server_presets": "server_presets",
    "temporary_assets_browser": "asset_browser",
    "temporary_sobject_info": "sobject_info",
    "temporary_screenshot_maker": "screenshot_maker",
    "temporary_update": "update",
    "temporary_create_update": "create_update",
    "temporary_maya_import": "maya_import",
    "temporary_maya_open": "maya_open",
    "temporary_maya_reference": "maya_reference",
    "temporary_handler_server": "handler_server",
    "temporary_thin_client_demo": "handler_server",
    "temporary_debug_log": "debug_log",
    "temporary_repository_sync": "repository_sync",
    "temporary_commit_queue": "commit_queue",
    "temporary_tasks": "tasks_workspace",
}


TEMPORARY_TOOL_DOCKS = {
    "temporary_drop_plate": "drop_plate",
    "temporary_watch_folders": "watch_folders",
    "temporary_database_editor": "db_table",
    "temporary_notes": "notes",
    "temporary_timesheet": "timesheet",
    "temporary_work_reports": "work_reports",
    "temporary_cost_reports": "cost_reports",
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
        action(
            "Tools and Test Windows",
            "dashboard_customize",
            "show_temporary_tools",
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
        action(
            "Repository Sync Queue",
            "sync",
            "show_repository_sync",
        ),
        action("TACTIC Handler Server", "hub", "show_handler_server"),
        SEPARATOR,
        action("Exit", "logout", "exit"),
    ],
    "temporary_tools": [
        tool_header("Core"),
        tool_action("Configuration", "settings", "temporary_configuration"),
        tool_action("Filter Editor", "filter_alt", "temporary_filter_editor"),
        tool_action("Commit Queue", "commit-queue", "temporary_commit_queue"),
        tool_action("Drop Plate", "move_to_inbox", "temporary_drop_plate"),
        tool_action("Watch Folders", "folder_special", "temporary_watch_folders"),
        tool_action("Repository Editor", "folder", "temporary_repository_editor"),
        tool_action("Repository Sync", "sync", "temporary_repository_sync"),
        tool_action("Database Editor", "table", "temporary_database_editor"),
        tool_action("SObject Info", "info", "temporary_sobject_info", "Experimental"),
        tool_action("Add sObject", "add", "temporary_add_sobject"),
        tool_action("Edit selected sObject", "edit", "temporary_edit_sobject"),
        tool_action("Link sObjects", "link", "temporary_link_sobjects"),
        tool_action("Tasks", "task_alt", "temporary_tasks"),
        tool_action("Timesheet", "calendar_month", "temporary_timesheet"),
        tool_action("Work Reports", "bar_chart", "temporary_work_reports"),
        tool_action("Cost Reports", "payments", "temporary_cost_reports"),
        tool_action("Notes", "comment", "temporary_notes"),
        tool_action("Messages", "comment", "temporary_messages", "Experimental"),
        SEPARATOR,
        tool_header("User and Communication"),
        tool_action("User Profile", "account_circle", "show_user_profile"),
        tool_action("Users", "users", "show_users"),
        tool_action("Notifications", "notifications", "temporary_notifications"),
        tool_action("Activity Feed", "rss", "temporary_activity_feed", "Experimental"),
        tool_action("Chat / Messages", "comment", "temporary_chat_messages", "Experimental"),
        tool_action("Attachments", "attach_file", "temporary_attachments", "Experimental"),
        SEPARATOR,
        tool_header("Editors"),
        tool_action("Columns Editor", "view_column", "temporary_columns_editor"),
        tool_action("TACTIC Column Editor", "table_view", status="Not implemented", enabled=False),
        tool_action("Naming Editor", "drive_file_rename_outline", "temporary_naming_editor"),
        tool_action("Preview Editor", "image", "temporary_preview_editor", "Experimental"),
        tool_action("Attachments Editor", "attachment", "temporary_attachments_editor", "Experimental"),
        tool_action("Matching Templates", "filter", "temporary_matching_templates"),
        tool_action("Script Editor", "code", "temporary_script_editor"),
        tool_action("Server Presets", "server", "temporary_server_presets", "Experimental"),
        SEPARATOR,
        tool_header("Integrations and Service Tools"),
        tool_action("Assets Browser", "inventory_2", "temporary_assets_browser", "Experimental"),
        tool_action("Screenshot Maker", "photo_camera", "temporary_screenshot_maker"),
        tool_action("Update", "download", "temporary_update", "Experimental"),
        tool_action("Create Update", "archive", "temporary_create_update", "Experimental"),
        tool_action("Maya Import Options", "upload", "temporary_maya_import"),
        tool_action("Maya Open Options", "folder_open", "temporary_maya_open"),
        tool_action("Maya Reference Options", "link", "temporary_maya_reference"),
        tool_action("TACTIC Handler Server", "hub", "temporary_handler_server"),
        tool_action("Thin Client Demo", "desktop", "temporary_thin_client_demo", "Experimental"),
        tool_action("Debug Log", "bug_report", "temporary_debug_log"),
    ],
    "result_filters": [
        action("Advanced Search", "search", "advanced_search"),
        action("Edit presets", "settings", "edit_presets"),
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
        action("Edit info", "edit", "edit"),
        action("Link / unlink sObjects", "link", "link"),
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
        action("Sync selected", "sync", "sync"),
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
