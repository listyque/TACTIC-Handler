import QtQuick

QtObject {
    function windowMinimumWidth(kind) {
        const widths = {
            "configuration": 820,
            "server": 640,
            "project": 640,
            "checkin_preferences": 640,
            "checkinout_preferences": 640,
            "global_preferences": 560,
            "maya_preferences": 560,
            "repository_editor": 760,
            "commit_queue": 860,
            "script_editor": 840,
            "messages": 820,
            "tasks_workspace": 760,
            "handler_server": 820,
            "asset_browser": 760,
            "sobject_info": 760,
            "debug_log": 680,
            "repository_sync": 680,
            "repository_sync_editor": 900,
            "activity_feed": 680,
            "user_profile": 680,
            "sidebar_editor": 860,
            "columns_editor": 680,
            "server_presets": 560,
            "screenshot_maker": 640,
            "notifications": 560,
            "update": 520,
            "create_update": 560,
            "matching_templates": 640,
            "maya_options": 520,
            "add_sobject": 620,
            "task_editor": 620,
            "link_sobjects": 620,
            "process_filter_editor": 620,
            "advanced_search": 680,
            "preview_editor": 620,
            "attachments_editor": 620,
            "naming_editor": 840
        }
        return widths[kind] || 480
    }

    function windowMinimumHeight(kind) {
        const heights = {
            "configuration": 600,
            "server": 520,
            "project": 520,
            "checkin_preferences": 520,
            "checkinout_preferences": 520,
            "global_preferences": 440,
            "maya_preferences": 440,
            "repository_editor": 540,
            "commit_queue": 600,
            "script_editor": 580,
            "messages": 560,
            "tasks_workspace": 520,
            "handler_server": 580,
            "asset_browser": 540,
            "sobject_info": 560,
            "debug_log": 480,
            "repository_sync": 480,
            "repository_sync_editor": 620,
            "activity_feed": 480,
            "user_profile": 480,
            "sidebar_editor": 600,
            "columns_editor": 500,
            "server_presets": 420,
            "screenshot_maker": 500,
            "notifications": 420,
            "update": 380,
            "create_update": 420,
            "matching_templates": 500,
            "maya_options": 380,
            "add_sobject": 480,
            "task_editor": 480,
            "link_sobjects": 480,
            "process_filter_editor": 500,
            "advanced_search": 500,
            "preview_editor": 480,
            "attachments_editor": 480,
            "naming_editor": 600,
            "confirm": 280
        }
        return heights[kind] || 360
    }

    function dockMinimumWidth(kind) {
        const widths = {
            "results": 360,
            "snapshot": 320,
            "tasks": 320,
            "task_calendar": 380,
            "description": 320,
            "notes": 400,
            "drop_plate": 480,
            "advanced_search": 380,
            "fast_controls": 360,
            "watch_folders": 680,
            "watch_folder_editor": 520,
            "db_table": 620,
            "commit_queue": 720
        }
        return widths[kind] || 320
    }

    function dockMinimumHeight(kind) {
        const heights = {
            "results": 260,
            "snapshot": 260,
            "tasks": 220,
            "task_calendar": 360,
            "description": 220,
            "notes": 300,
            "drop_plate": 360,
            "advanced_search": 320,
            "fast_controls": 150,
            "watch_folders": 420,
            "watch_folder_editor": 350,
            "db_table": 460,
            "commit_queue": 480
        }
        return heights[kind] || 220
    }
}
