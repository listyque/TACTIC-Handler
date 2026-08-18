import QtQuick

// Compatibility facade backed by the official Font Awesome 5 Regular/Solid
// fonts bundled with TACTIC-Handler's qtawesome package.
Item {
    id: root
    property string name: ""
    property color color: "#1c252e"
    property real size: 24
    property real opticalScale: 0.78
    property bool forceSolid: false
    readonly property var solidGlyphs:
        typeof fontAwesomeSolidGlyphs !== "undefined"
        ? fontAwesomeSolidGlyphs : ({})
    readonly property var regularGlyphs:
        typeof fontAwesomeRegularGlyphs !== "undefined"
        ? fontAwesomeRegularGlyphs : ({})
    readonly property string solidFontFamily:
        typeof fontAwesomeSolidFontFamily !== "undefined"
        ? fontAwesomeSolidFontFamily : "Segoe UI"
    readonly property string regularFontFamily:
        typeof fontAwesomeRegularFontFamily !== "undefined"
        ? fontAwesomeRegularFontFamily : solidFontFamily
    readonly property var materialGlyphs:
        typeof materialDesignIconGlyphs !== "undefined"
        ? materialDesignIconGlyphs : ({})
    readonly property string materialFontFamily:
        typeof materialDesignIconFontFamily !== "undefined"
        ? materialDesignIconFontFamily : solidFontFamily
    implicitWidth: size
    implicitHeight: size

    readonly property var aliases: ({
        "account-circle": "user-circle",
        "account-tree": "project-diagram",
        "activity-feed": "stream",
        "advanced-search": "search-plus",
        "admin-panel-settings": "user-shield",
        "all": "layer-group",
        "add": "plus",
        "add-circle": "plus-circle",
        "add-comment": "comments",
        "add-task": "plus-circle",
        "add-alarm": "clock",
        "add-photo-alternate": "file-image",
        "api": "exchange-alt",
        "api-client": "exchange-alt",
        "arrow-forward": "arrow-right",
        "arrow-downward": "arrow-down",
        "arrow-upward": "arrow-up",
        "attach-file": "paperclip",
        "attachment": "paperclip",
        "attachments-editor": "paperclip",
        "available": "check-circle",
        "bug-report": "bug",
        "cancel": "times-circle",
        "cancelled": "times-circle",
        "category": "shapes",
        "cached": "sync-alt",
        "check-circle": "check-circle",
        "check": "check",
        "chevron-left": "chevron-left",
        "chevron-right": "chevron-right",
        "close": "times",
        "code": "code",
        "cloud-done": "cloud",
        "cloud-download": "cloud-download-alt",
        "cloud-off": "unlink",
        "cloud-sync": "cloud-sync",
        "checkin": "cloud-upload-alt",
        "checkin-options": "sliders-h",
        "checkout": "cloud-download-alt",
        "child": "level-down-alt",
        "commit-queue": "cloud-upload-alt",
        "complete": "check-circle",
        "completed": "check-circle",
        "configuration": "cog",
        "collections": "images",
        "continious": "stream",
        "content-copy": "copy",
        "content-paste": "paste",
        "control-point-duplicate": "clone",
        "create-new-folder": "folder-plus",
        "dashboard-customize": "th-large",
        "dark-mode": "moon",
        "dashboard": "th-large",
        "delete": "trash-alt",
        "delete-forever": "trash-alt",
        "delete-sweep": "broom",
        "deployed-code": "cube",
        "description": "file-alt",
        "dns": "server",
        "done-all": "check-double",
        "drag-handle": "bars",
        "drop-plate": "inbox",
        "duplicate": "clone",
        "dynamic-feed": "stream",
        "emoji": "smile",
        "drive-file-rename-outline": "edit",
        "edit-note": "sticky-note",
        "error": "exclamation-circle",
        "expand-less": "chevron-up",
        "expand-more": "chevron-down",
        "failed": "exclamation-circle",
        "fast-controls": "bolt",
        "filter-alt": "filter",
        "filter-alt-off": "eraser",
        "calendar-month": "calendar-alt",
        "calendar-today": "calendar-day",
        "floating": "window-restore",
        "donut-small": "circle-notch",
        "folder-open": "folder-open",
        "folder-special": "folder",
        "forum": "comments",
        "gantt": "stream",
        "groups": "users",
        "grid-view": "th",
        "group": "users",
        "group-add": "user-plus",
        "hierarchy": "sitemap",
        "hourglass-empty": "hourglass",
        "hub": "network-wired",
        "icon": "image",
        "import": "file-import",
        "input": "sign-in-alt",
        "open-in-new": "external-link-alt",
        "open-in-full": "expand",
        "insert-drive-file": "file",
        "inventory-2": "archive",
        "keyboard-arrow-down": "chevron-down",
        "keyboard-arrow-right": "chevron-right",
        "language": "globe",
        "layers": "layer-group",
        "light-mode": "sun",
        "link-off": "unlink",
        "loading": "spinner",
        "logout": "sign-out-alt",
        "menu": "bars",
        "matching-templates": "object-group",
        "milestone": "flag",
        "maya": "cube",
        "maya-import": "file-import",
        "maya-open": "folder-open",
        "maya-reference": "link",
        "image-edit": "image",
        "message": "comments",
        "messages": "comments",
        "more-horiz": "ellipsis-h",
        "more-vert": "ellipsis-v",
        "movie": "film",
        "monitoring": "chart-line",
        "more-time": "clock",
        "move-to-inbox": "inbox",
        "network-check": "network-wired",
        "naming-editor": "edit",
        "notes": "sticky-note",
        "notifications": "bell",
        "online": "plug",
        "open": "external-link-alt",
        "pages": "file-alt",
        "person": "user",
        "person-add": "user-plus",
        "unassigned": "user-slash",
        "payments": "money-bill-wave",
        "picture-in-picture": "clone",
        "photo-camera": "camera",
        "play-arrow": "play",
        "playlist-add": "list-ul",
        "preview-editor": "image",
        "priority-high": "exclamation",
        "process": "cogs",
        "progress": "sync-alt",
        "publication": "cloud-upload-alt",
        "approval": "check-circle",
        "bar-chart": "chart-bar",
        "publish": "cloud-upload-alt",
        "push-pin": "thumbtack",
        "refresh": "redo-alt",
        "radio-button-unchecked": "circle",
        "restart-alt": "redo-alt",
        "rename": "edit",
        "repo-sync": "cloud-sync",
        "repository-editor": "folder-open",
        "repository-sync": "cloud-sync",
        "reply": "reply",
        "running": "sync-alt",
        "save": "save",
        "schedule": "clock",
        "sidebar-link": "link",
        "sidebar-section": "folder",
        "sidebar-separator": "grip-lines",
        "select-all": "check-double",
        "science": "flask",
        "schema": "project-diagram",
        "screenshot-maker": "camera",
        "send": "paper-plane",
        "sequence": "film",
        "server-presets": "server",
        "sensors": "broadcast-tower",
        "settings": "cog",
        "settings-suggest": "tools",
        "snapshot": "camera",
        "sobject": "cube",
        "stopped": "stop-circle",
        "storage": "hdd",
        "status": "dot-circle",
        "subdirectory-arrow-right": "level-down-alt",
        "success": "check-circle",
        "sync": "sync-alt",
        "sync-problem": "exclamation-triangle",
        "swap-vert": "exchange-alt",
        "system-activity": "heartbeat",
        "system-update": "download",
        "tab": "window-maximize",
        "table-view": "table",
        "task": "tasks",
        "task-alt": "check-circle",
        "tasks": "tasks",
        "tiles": "th",
        "tune": "sliders-h",
        "type": "font",
        "undo": "undo-alt",
        "unavailable": "ban",
        "update": "redo-alt",
        "redo": "redo-alt",
        "upload": "upload",
        "verified": "check-circle",
        "view-agenda": "list-alt",
        "view-column": "columns",
        "view-in-ar": "cube",
        "view-kanban": "columns",
        "view-list": "list",
        "warning": "exclamation-triangle",
        "workspaces": "briefcase",
        "window-restore": "window-restore",
        "visibility": "eye",
        "visibility-off": "eye-slash",
        "workflow": "project-diagram",
        "zoom-in": "search-plus",
        "zoom-out": "search-minus"
    })

    function glyphName(sourceName) {
        const normalized = String(sourceName || "exclamation-triangle")
            .replace(/_/g, "-")
        const candidate = aliases[normalized] || normalized
        return solidGlyphs[candidate] !== undefined
                || regularGlyphs[candidate] !== undefined
                || materialGlyphs[candidate] !== undefined
            ? candidate : "exclamation-triangle"
    }

    Text {
        readonly property string resolvedName: root.glyphName(root.name)
        readonly property bool regularAvailable:
            !root.forceSolid
            && root.regularGlyphs[resolvedName] !== undefined
        readonly property bool materialAvailable:
            resolvedName === "cloud-sync"
            && root.materialGlyphs[resolvedName] !== undefined
        anchors.fill: parent
        text: materialAvailable
            ? root.materialGlyphs[resolvedName]
            : regularAvailable
            ? root.regularGlyphs[resolvedName]
            : root.solidGlyphs[resolvedName] || ""
        color: root.color
        font.family: materialAvailable
            ? root.materialFontFamily
            : regularAvailable
            ? root.regularFontFamily : root.solidFontFamily
        font.pixelSize: Math.max(11, Math.round(root.size * root.opticalScale))
        font.weight: materialAvailable || regularAvailable
            ? Font.Normal : Font.Black
        font.hintingPreference: Font.PreferVerticalHinting
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        renderType: Text.QtRendering
        antialiasing: true
    }
}
