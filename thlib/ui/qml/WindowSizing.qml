import QtQuick

QtObject {
    function windowMinimumWidth(kind) {
        if (String(kind).indexOf("dcc.") === 0)
            return 560
        const widths = {
            "main": 560,
            "configuration": 820,
            "server": 640,
            "project": 640,
            "project_wizard": 680,
            "checkin_preferences": 640,
            "global_preferences": 560,
            "repository_editor": 760,
            "commit_queue": 860,
            "ingest_files": 760,
            "script_editor": 720,
            "script_shelf_editor": 720,
            "script_trigger_editor": 760,
            "help": 760,
            "messages": 820,
            "tasks_workspace": 760,
            "handler_server": 820,
            "sobject_info": 760,
            "debug_log": 680,
            "ui_performance": 720,
            "error": 560,
            "repository_sync": 680,
            "repository_sync_editor": 900,
            "activity_feed": 680,
            "user_profile": 680,
            "sidebar_editor": 860,
            "administration": 900,
            "schema_search_type": 600,
            "process_dependencies": 860,
            "sidebar_search_preview": 960,
            "columns_editor": 820,
            "server_presets": 720,
            "screenshot_maker": 640,
            "notifications": 560,
            "update": 520,
            "create_update": 560,
            "matching_templates": 640,
            "dcc_options": 520,
            "add_sobject": 620,
            "task_editor": 620,
            "link_sobjects": 620,
            "delete_sobject": 720,
            "duplicate_sobject": 680,
            "process_filter_editor": 440,
            "quick_filter_editor": 620,
            "advanced_search": 680,
            "naming_editor": 840
        }
        return widths[kind] || 480
    }

    function windowMinimumHeight(kind) {
        if (String(kind).indexOf("dcc.") === 0)
            return 440
        const heights = {
            "main": 480,
            "configuration": 600,
            "server": 520,
            "project": 520,
            "project_wizard": 520,
            "checkin_preferences": 520,
            "global_preferences": 440,
            "repository_editor": 540,
            "commit_queue": 600,
            "ingest_files": 560,
            "script_editor": 500,
            "script_shelf_editor": 480,
            "script_trigger_editor": 520,
            "help": 520,
            "messages": 560,
            "tasks_workspace": 520,
            "handler_server": 580,
            "sobject_info": 560,
            "debug_log": 480,
            "ui_performance": 520,
            "error": 400,
            "repository_sync": 480,
            "repository_sync_editor": 620,
            "activity_feed": 480,
            "user_profile": 480,
            "sidebar_editor": 600,
            "administration": 620,
            "schema_search_type": 560,
            "process_dependencies": 600,
            "sidebar_search_preview": 620,
            "columns_editor": 560,
            "server_presets": 520,
            "screenshot_maker": 500,
            "notifications": 420,
            "update": 380,
            "create_update": 420,
            "matching_templates": 500,
            "dcc_options": 420,
            "add_sobject": 480,
            "task_editor": 480,
            "link_sobjects": 480,
            "delete_sobject": 520,
            "duplicate_sobject": 520,
            "process_filter_editor": 360,
            "quick_filter_editor": 520,
            "advanced_search": 500,
            "naming_editor": 600
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
            "watch_folders": 420,
            "watch_folder_editor": 350,
            "db_table": 460,
            "commit_queue": 480
        }
        return heights[kind] || 220
    }
}
