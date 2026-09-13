import QtQuick

// Shared semantic icon renderer backed by the bundled icon-font catalog.
Item {
    id: root
    property string name: ""
    required property color color
    property real size: 24
    property real opticalScale: 0.78
    property bool forceSolid: false
    property bool nativeRendering: false
    readonly property string iconSet:
        typeof appController !== "undefined"
        ? String(appController.icon_set || "material-design")
        : "material-design"
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
        "checkbox-blank-circle": "circle",
        "checkbox-multiple-marked-outline": "check-double",
        "check": "check",
        "chevron-left": "chevron-left",
        "chevron-right": "chevron-right",
        "close": "times",
        "code": "code",
        "code-block": "code",
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
        "content-cut": "cut",
        "content-paste": "paste",
        "content-save": "save",
        "control-point-duplicate": "clone",
        "create-article": "plus-square",
        "create-new-folder": "folder-plus",
        "dashboard-customize": "th-large",
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
        "divider": "grip-lines",
        "dynamic-feed": "stream",
        "emoji": "smile",
        "drive-file-rename-outline": "edit",
        "edit-note": "sticky-note",
        "error": "exclamation-circle",
        "expand-less": "chevron-up",
        "expand-more": "chevron-down",
        "failed": "exclamation-circle",
        "file": "file",
        "filter-alt": "filter",
        "filter-alt-off": "eraser",
        "format-paragraph": "paragraph",
        "format-header-1": "heading",
        "format-header-2": "text-height",
        "format-header-3": "font",
        "format-header-4": "heading",
        "format-header-5": "heading",
        "format-header-6": "heading",
        "format-quote": "quote-left",
        "calendar-month": "calendar-alt",
        "calendar-today": "calendar-day",
        "floating": "window-restore",
        "donut-small": "circle-notch",
        "folder-open": "folder-open",
        "folder-special": "folder",
        "forum": "comments",
        "gantt": "stream",
        "help": "question-circle",
        "history": "history",
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
        "ui-performance": "tachometer-alt",
        "play-arrow": "play",
        "play-selection": "play-circle",
        "playlist-add": "list-ul",
        "plus-box": "plus-square",
        "preview-editor": "image",
        "priority-high": "exclamation",
        "process": "cogs",
        "process-marker": "circle",
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
        "small-text": "text-height",
        "select-all": "check-double",
        "science": "flask",
        "schema": "project-diagram",
        "screenshot-maker": "camera",
        "script-expression": "function",
        "script-javascript": "language-javascript",
        "script-python": "language-python",
        "script-xml": "xml",
        "scripts-tree": "chevron-left",
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
        "sort-items": "sort-alpha-down",
        "sort-ascending": "sort-alpha-down",
        "sort-descending": "sort-alpha-up",
        "group-items": "object-group",
        "ungroup-items": "object-ungroup",
        "subdirectory-arrow-right": "level-down-alt",
        "success": "check-circle",
        "sync": "sync-alt",
        "sync-problem": "exclamation-triangle",
        "swap-vert": "exchange-alt",
        "swap-horiz": "exchange-alt",
        "system-activity": "heartbeat",
        "system-update": "download",
        "theme-mode": "adjust",
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
        "view-sequential": "stream",
        "warning": "exclamation-triangle",
        "workspaces": "briefcase",
        "window-restore": "window-restore",
        "visibility": "eye",
        "visibility-off": "eye-slash",
        "workflow": "project-diagram",
        "wrap-lines": "wrap",
        "zoom-in": "search-plus",
        "zoom-out": "search-minus"
    })

    readonly property var materialAliases: ({
        "account-circle": "account-circle",
        "account-tree": "file-tree",
        "activity-feed": "chart-timeline-variant",
        "add": "plus",
        "add-alarm": "alarm-plus",
        "add-photo-alternate": "image-plus",
        "add-task": "clipboard-plus",
        "address-book": "contacts",
        "advanced-search": "magnify-plus",
        "admin-panel-settings": "shield-account",
        "all": "layers",
        "api": "swap-horizontal",
        "api-client": "swap-horizontal",
        "swap-horiz": "swap-horizontal",
        "arrow-forward": "arrow-right",
        "attach-file": "paperclip",
        "attachments-editor": "paperclip",
        "bug-report": "bug",
        "bar-chart": "chart-bar",
        "bolt": "lightning-bolt",
        "book-open": "book-open",
        "cached": "sync",
        "calendar": "calendar",
        "cancel": "close-circle",
        "category": "shape",
        "checkin": "cloud-upload",
        "checkin-options": "tune",
        "checkout": "cloud-download",
        "child": "subdirectory-arrow-right",
        "cloud-upload-alt": "cloud-upload",
        "code": "code-tags",
        "collections": "image-multiple",
        "commit-queue": "cloud-upload",
        "configuration": "cog",
        "content-copy": "content-copy",
        "content-cut": "content-cut",
        "content-paste": "content-paste",
        "control-point-duplicate": "content-duplicate",
        "create-article": "file-document-plus",
        "create-new-folder": "folder-plus",
        "dashboard-customize": "view-dashboard-edit",
        "delete-forever": "delete-forever",
        "delete-sweep": "delete-sweep",
        "deployed-code": "cube",
        "description": "text-box",
        "done-all": "check-all",
        "drag-handle": "drag",
        "divider": "minus",
        "donut-small": "chart-donut",
        "drive-file-rename-outline": "rename-box",
        "dynamic-feed": "chart-timeline-variant",
        "edit": "pencil",
        "edit-note": "note-edit",
        "emoji": "emoticon",
        "envelope": "email",
        "error": "alert-circle",
        "exclamation-circle": "alert-circle",
        "failed": "alert-circle",
        "filter-alt": "filter",
        "filter-alt-off": "filter-off",
        "code-block": "code-block-tags",
        "format-header-1": "format-header-1",
        "format-header-2": "format-header-2",
        "format-header-3": "format-header-3",
        "format-header-4": "format-header-4",
        "format-header-5": "format-header-5",
        "format-header-6": "format-header-6",
        "format-paragraph": "format-paragraph",
        "format-quote": "format-quote-open",
        "floating": "open-in-new",
        "folder-special": "folder-star",
        "forum": "forum",
        "gantt": "chart-gantt",
        "grid-view": "view-grid",
        "group-add": "account-multiple-plus",
        "group-items": "group",
        "security": "shield-account",
        "groups": "account-group",
        "hierarchy": "file-tree",
        "hub": "hub",
        "hourglass-empty": "timer-sand",
        "info": "information",
        "input": "login",
        "inventory-2": "archive",
        "keyboard-arrow-down": "chevron-down",
        "keyboard-arrow-right": "chevron-right",
        "language": "translate",
        "list-ul": "format-list-bulleted",
        "lock": "lock",
        "manage-accounts": "account-cog",
        "matching-templates": "shape-outline",
        "memory": "memory",
        "messages": "message-text",
        "milestone": "flag",
        "more-horiz": "dots-horizontal",
        "more-vert": "dots-vertical",
        "network-check": "lan-connect",
        "mouse": "mouse",
        "naming-editor": "rename-box",
        "notes": "note-text",
        "notifications": "bell",
        "online": "lan-connect",
        "open-in-full": "arrow-expand-all",
        "open-in-new": "open-in-new",
        "pages": "file-document-multiple",
        "person": "account",
        "person-add": "account-plus",
        "photo-library": "image-multiple",
        "photo-camera": "camera",
        "picture-in-picture": "picture-in-picture-bottom-right",
        "play-arrow": "play",
        "play-selection": "play-box-multiple",
        "playlist-add": "playlist-plus",
        "preview-editor": "image-edit",
        "priority-high": "alert",
        "process": "cogs",
        "project-diagram": "source-branch",
        "publication": "cloud-upload",
        "push-pin": "pin",
        "radio-button-unchecked": "radiobox-blank",
        "repo-sync": "cloud-sync",
        "repository-editor": "folder-cog",
        "repository-sync": "cloud-sync",
        "restart-alt": "restart",
        "route": "routes",
        "rule": "ruler-square",
        "save": "content-save",
        "schedule": "calendar-clock",
        "schema": "file-tree",
        "screenshot-maker": "camera",
        "search": "magnify",
        "sensors": "access-point",
        "settings": "cog",
        "settings-suggest": "cog-refresh",
        "sidebar-link": "link",
        "sidebar-section": "folder",
        "sidebar-separator": "drag-horizontal",
        "shapes": "shape-outline",
        "small-text": "format-font-size-decrease",
        "sobject": "cube",
        "sort-items": "sort-alphabetical-ascending",
        "sort-ascending": "sort-alphabetical-ascending",
        "sort-descending": "sort-alphabetical-descending",
        "status": "circle-double",
        "storage": "harddisk",
        "stream": "view-stream",
        "subdirectory-arrow-right": "subdirectory-arrow-right",
        "sync-problem": "sync-alert",
        "system-activity": "pulse",
        "tags": "tag-multiple",
        "task": "clipboard-check",
        "task-alt": "checkbox-marked-circle",
        "tasks": "clipboard-text",
        "terminal": "console",
        "theme-mode": "theme-light-dark",
        "times": "close",
        "type": "format-font",
        "ui-performance": "speedometer",
        "unlock-alt": "lock-open-variant",
        "upload": "upload",
        "user": "account",
        "users": "account-group",
        "view-agenda": "view-agenda",
        "view-column": "view-column",
        "view-in-ar": "cube-scan",
        "view-kanban": "view-column",
        "view-list": "view-list",
        "visibility": "eye",
        "warning": "alert",
        "window-restore": "window-restore",
        "workflow": "source-branch",
        "workspaces": "briefcase",
        "wrap-lines": "wrap",
        "zoom-in": "magnify-plus",
        "zoom-out": "magnify-minus"
    })

    readonly property var fluentAliases: ({
        "account-circle": "person-circle",
        "account-tree": "organization",
        "activity-feed": "timeline",
        "advanced-search": "search-sparkle",
        "admin-panel-settings": "person-shield",
        "all": "layer",
        "add-alarm": "clock-alarm",
        "add-comment": "chat-add",
        "add-photo-alternate": "image-add",
        "add-task": "clipboard-task-add",
        "api": "code",
        "api-client": "code",
        "arrow-downward": "arrow-down",
        "arrow-forward": "arrow-right",
        "arrow-upward": "arrow-up",
        "attach-file": "attach",
        "attachment": "attach",
        "attachments-editor": "attach",
        "available": "checkmark-circle",
        "bar-chart": "data-bar-vertical",
        "bug-report": "bug",
        "cached": "arrow-sync",
        "cancel": "dismiss-circle",
        "cancelled": "dismiss-circle",
        "category": "shapes",
        "check": "checkmark",
        "check-circle": "checkmark-circle",
        "checkbox-blank-circle": "circle",
        "checkbox-multiple-marked-outline": "checkbox-checked",
        "checkin": "cloud-arrow-up",
        "checkin-options": "options",
        "checkout": "cloud-arrow-down",
        "child": "branch",
        "close": "dismiss",
        "code-block": "code-block",
        "cloud-done": "cloud-checkmark",
        "cloud-download": "cloud-arrow-down",
        "cloud-sync": "cloud-sync",
        "commit-queue": "cloud-arrow-up",
        "complete": "checkmark-circle",
        "completed": "checkmark-circle",
        "configuration": "settings",
        "continious": "timeline",
        "content-cut": "cut",
        "content-paste": "clipboard-paste",
        "content-save": "save",
        "control-point-duplicate": "copy-add",
        "create-article": "document-add",
        "create-new-folder": "folder-add",
        "dashboard-customize": "grid-dots",
        "delete-forever": "delete",
        "delete-sweep": "broom",
        "deployed-code": "cube",
        "description": "text-description",
        "dns": "server",
        "done-all": "checkmark",
        "drag-handle": "drag",
        "divider": "divider-short",
        "drive-file-rename-outline": "edit",
        "drop-plate": "tray-item-add",
        "duplicate": "copy",
        "dynamic-feed": "timeline",
        "edit-note": "note-edit",
        "error": "error-circle",
        "expand-less": "chevron-up",
        "expand-more": "chevron-down",
        "failed": "error-circle",
        "file": "document",
        "filter-alt": "filter",
        "filter-alt-off": "filter-dismiss",
        "format-header-1": "text-header-1",
        "format-header-2": "text-header-2",
        "format-header-3": "text-header-3",
        "format-header-4": "text-header-4",
        "format-header-5": "text-header-5",
        "format-header-6": "text-header-6",
        "format-paragraph": "text-paragraph",
        "format-quote": "text-quote",
        "floating": "window-new",
        "folder-special": "folder-lightning",
        "forum": "chat-multiple",
        "gantt": "data-trending",
        "grid-view": "grid",
        "group-add": "people-add",
        "groups": "people",
        "help": "question-circle",
        "hierarchy": "organization",
        "hourglass-empty": "hourglass",
        "image-edit": "image-edit",
        "import": "arrow-import",
        "input": "arrow-enter",
        "insert-drive-file": "document",
        "inventory-2": "archive",
        "keyboard-arrow-down": "chevron-down",
        "keyboard-arrow-right": "chevron-right",
        "layers": "layer",
        "link-off": "link-dismiss",
        "loading": "spinner-ios",
        "logout": "sign-out",
        "matching-templates": "shapes",
        "maya-import": "arrow-import",
        "maya-open": "folder-open",
        "maya-reference": "link",
        "message": "chat",
        "messages": "chat-multiple",
        "milestone": "flag",
        "monitoring": "data-trending",
        "more-horiz": "more-horizontal",
        "more-time": "clock",
        "more-vert": "more-vertical",
        "move-to-inbox": "tray-item-add",
        "network-check": "plug-connected-checkmark",
        "naming-editor": "edit",
        "notes": "note",
        "online": "plug-connected",
        "open": "open",
        "open-in-full": "arrow-expand",
        "open-in-new": "open",
        "pages": "document-multiple",
        "person": "person",
        "person-add": "person-add",
        "photo-camera": "camera",
        "picture-in-picture": "picture-in-picture",
        "play-arrow": "play",
        "playlist-add": "list-bar-tree",
        "preview-editor": "image-edit",
        "priority-high": "important",
        "process": "flow",
        "progress": "arrow-sync",
        "publication": "cloud-arrow-up",
        "publish": "cloud-arrow-up",
        "push-pin": "pin",
        "radio-button-unchecked": "circle",
        "redo": "arrow-redo",
        "refresh": "arrow-clockwise",
        "rename": "edit",
        "repo-sync": "cloud-sync",
        "repository-editor": "folder-open",
        "repository-sync": "cloud-sync",
        "reply": "arrow-reply",
        "restart-alt": "arrow-reset",
        "running": "arrow-sync",
        "schedule": "clock",
        "schema": "organization",
        "science": "beaker",
        "screenshot-maker": "camera",
        "script-expression": "code",
        "script-javascript": "code",
        "script-python": "code",
        "script-xml": "code",
        "scripts-tree": "panel-left",
        "send": "send",
        "sensors": "presence-available",
        "settings-suggest": "settings-cog-multiple",
        "sidebar-link": "link",
        "sidebar-section": "folder",
        "sidebar-separator": "drag",
        "small-text": "text-font-size",
        "sobject": "cube",
        "sort-ascending": "text-sort-ascending",
        "sort-descending": "text-sort-descending",
        "sort-items": "arrow-sort",
        "status": "circle",
        "stopped": "stop",
        "subdirectory-arrow-right": "branch",
        "success": "checkmark-circle",
        "swap-horiz": "arrow-swap",
        "swap-vert": "arrow-swap",
        "sync": "arrow-sync",
        "sync-problem": "warning",
        "system-activity": "pulse",
        "system-update": "arrow-download",
        "tab": "tab-desktop",
        "table-view": "table",
        "task": "clipboard-task",
        "task-alt": "clipboard-task",
        "tasks": "clipboard-task-list-ltr",
        "theme-mode": "dark-theme",
        "tiles": "grid",
        "tune": "options",
        "undo": "arrow-undo",
        "unavailable": "prohibited",
        "update": "arrow-clockwise",
        "verified": "checkmark-circle",
        "view-agenda": "list",
        "view-column": "column-triple",
        "view-in-ar": "cube",
        "view-kanban": "grid-kanban",
        "view-list": "list",
        "view-sequential": "list-bar-tree",
        "visibility": "eye",
        "visibility-off": "eye-off",
        "warning": "warning",
        "window-restore": "window",
        "workflow": "flow",
        "wrap-lines": "text-wrap"
    })

    readonly property var automaticOutlineGlyphs: ({
        "address-book": true,
        "bell": true,
        "bookmark": true,
        "calendar": true,
        "clock": true,
        "comments": true,
        "copy": true,
        "edit": true,
        "file": true,
        "file-alt": true,
        "file-image": true,
        "folder": true,
        "folder-open": true,
        "image": true,
        "paper-plane": true,
        "sticky-note": true,
        "user": true,
        "user-circle": true,
        "window-maximize": true
    })

    function normalizedName(sourceName) {
        return String(sourceName || "warning").replace(/_/g, "-")
    }

    function fontAwesomeName(sourceName) {
        const normalized = normalizedName(sourceName)
        const candidate = aliases[normalized] || normalized
        return solidGlyphs[candidate] !== undefined
                || regularGlyphs[candidate] !== undefined
            ? candidate : ""
    }

    function materialName(sourceName) {
        const normalized = normalizedName(sourceName)
        const direct = materialAliases[normalized] || normalized
        if (materialGlyphs[direct] !== undefined)
            return direct
        const fontAwesome = aliases[normalized] || normalized
        const mapped = materialAliases[fontAwesome] || fontAwesome
        return materialGlyphs[mapped] !== undefined ? mapped : ""
    }

    function fluentName(sourceName) {
        const normalized = normalizedName(sourceName)
        return fluentAliases[normalized] || normalized
    }

    function qualifiedIcon(sourceName) {
        const normalized = normalizedName(sourceName)
        const separator = normalized.indexOf(":")
        if (separator <= 0)
            return ({})
        return {
            "set": normalized.slice(0, separator),
            "name": normalized.slice(separator + 1)
        }
    }

    function catalogIcon(setId, iconName) {
        if (typeof iconFontCatalog === "undefined")
            return ({})
        return iconFontCatalog.resolve(setId, iconName)
    }

    function iconSetOpticalScale(setId) {
        if (setId === "material-design")
            return 1.22
        return String(setId).indexOf("fluent-") === 0 ? 1.08 : 1.0
    }

    function glyphName(sourceName) {
        return fontAwesomeName(sourceName) || "exclamation-triangle"
    }

    Text {
        objectName: "materialIconGlyph"
        readonly property string fontAwesomeName:
            root.fontAwesomeName(root.name)
        readonly property string resolvedName:
            fontAwesomeName || "exclamation-triangle"
        readonly property string materialName:
            root.materialName(root.name)
        readonly property var qualifiedIcon:
            root.qualifiedIcon(root.name)
        readonly property bool exactCatalogIcon:
            String(qualifiedIcon.set || "").length > 0
        readonly property string catalogSet: {
            if (exactCatalogIcon)
                return String(qualifiedIcon.set)
            if (root.iconSet === "fluent-regular"
                    || root.iconSet === "fluent-filled")
                return root.iconSet
            const selectedMaterialMissing =
                root.iconSet === "material-design"
                && materialName.length === 0
            const selectedFontAwesomeMissing =
                (root.iconSet === "fontawesome-solid"
                    || root.iconSet === "fontawesome-outline")
                && fontAwesomeName.length === 0
            const automaticMissing = root.iconSet === "automatic"
                && fontAwesomeName.length === 0
                && materialName.length === 0
            return selectedMaterialMissing || selectedFontAwesomeMissing
                    || automaticMissing
                ? (root.forceSolid ? "fluent-filled" : "fluent-regular")
                : ""
        }
        readonly property var catalogIcon: {
            if (!catalogSet)
                return ({})
            return root.catalogIcon(
                catalogSet,
                exactCatalogIcon
                    ? String(qualifiedIcon.name || "")
                    : root.fluentName(root.name)
            )
        }
        readonly property string catalogGlyph:
            String(catalogIcon.glyph || "")
        readonly property bool useCatalog: catalogGlyph.length > 0
        readonly property bool solidAvailable:
            root.solidGlyphs[resolvedName] !== undefined
        readonly property bool regularAvailable:
            root.regularGlyphs[resolvedName] !== undefined
        readonly property bool useMaterial:
            !exactCatalogIcon && !root.forceSolid && materialName.length > 0
            && (root.iconSet === "material-design"
                || root.iconSet === "automatic"
                || fontAwesomeName.length === 0)
        readonly property bool useRegular:
            !exactCatalogIcon && !useCatalog && !root.forceSolid
            && !useMaterial && regularAvailable
            && (root.iconSet === "fontawesome-outline"
                || (root.iconSet === "automatic"
                    && root.automaticOutlineGlyphs[resolvedName] === true)
                || !solidAvailable)
        readonly property string resolvedSet: useMaterial
            ? "material-design"
            : useCatalog ? catalogSet : "fontawesome"
        anchors.fill: parent
        text: useCatalog
            ? catalogGlyph
            : useMaterial
            ? root.materialGlyphs[materialName]
            : useRegular
            ? root.regularGlyphs[resolvedName]
            : root.solidGlyphs[resolvedName] || ""
        color: root.color
        font.family: useCatalog
            ? String(catalogIcon.fontFamily || root.solidFontFamily)
            : useMaterial
            ? root.materialFontFamily
            : useRegular
            ? root.regularFontFamily : root.solidFontFamily
        font.pixelSize: Math.max(11, Math.round(
            root.size * root.opticalScale
            * root.iconSetOpticalScale(resolvedSet)
        ))
        font.weight: useCatalog || useMaterial || useRegular
            ? Font.Normal : Font.Black
        font.hintingPreference: Font.PreferVerticalHinting
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        renderType: root.nativeRendering
            ? Text.NativeRendering : Text.QtRendering
        antialiasing: true
    }
}
