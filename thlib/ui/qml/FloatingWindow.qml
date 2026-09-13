import QtQuick
import QtQuick.Window

// Native Windows dialog frame with application-owned themed content.
// Keeping the operating-system frame gives dialogs the same DWM corners,
// shadow, resize behaviour and window controls as the main ApplicationWindow.
Window {
    id: root

    required property var ownerWindow
    required property var theme
    required property bool workspaceEnabled
    required property string windowId
    required property string windowTitle
    required property string kind
    required property real windowX
    required property real windowY
    required property real windowWidth
    required property real windowHeight
    required property bool windowVisible
    required property int stackOrder
    required property bool windowBlocking
    required property string geometryMode
    required property string contentSource
    required property var contentProperties
    property bool geometryReady: false
    property bool restoringGeometry: false

    WindowSizing { id: sizing }

    transientParent: ownerWindow
    modality: root.windowBlocking ? Qt.WindowModal : Qt.NonModal
    flags: Qt.Dialog
        | Qt.WindowTitleHint
        | Qt.WindowSystemMenuHint
        | Qt.WindowMinMaxButtonsHint
        | Qt.WindowCloseButtonHint
    readonly property bool availableWhileSignedOut:
        kind === "configuration" || kind === "server_presets"
        || kind === "repository_editor" || kind === "help"
        || kind === "error" || kind === "debug_log"
    readonly property bool contentRequested: windowVisible
        && (workspaceEnabled || availableWhileSignedOut)
    readonly property bool keepWorkspaceWarm: workspaceEnabled
        && ["tasks_workspace", "messages", "activity_feed", "notifications"].indexOf(kind) >= 0
    visible: contentRequested
    function localizedErrorTitle(errorType) {
        const titles = {
            "ticket_error": qsTr("TACTIC session expired"),
            "connection_timeout": qsTr("TACTIC connection timed out"),
            "connection_refused": qsTr("Cannot connect to TACTIC"),
            "login_pass_error": qsTr("Incorrect login or password"),
            "sql_connection_error": qsTr("TACTIC database connection error"),
            "protocol_error": qsTr("TACTIC protocol error"),
            "server_error": qsTr("TACTIC server request failed"),
            "no_project_error": qsTr("Project is unavailable"),
            "attribute_error": qsTr("Application attribute error"),
            "database_query_error": qsTr("TACTIC database query failed"),
            "type_error": qsTr("Application type error"),
            "value_error": qsTr("Invalid application value"),
            "key_error": qsTr("Required application data is missing"),
            "index_error": qsTr("Application index error"),
            "file_not_found_error": qsTr("File was not found"),
            "permission_error": qsTr("Permission denied"),
            "import_error": qsTr("Application component could not be loaded"),
            "runtime_error": qsTr("Application runtime error"),
            "assertion_error": qsTr("Application assertion failed"),
            "os_error": qsTr("Operating system error"),
            "qml_error": qsTr("Interface error")
        }
        return titles[String(errorType || "")] || ""
    }
    readonly property string effectiveWindowTitle: {
        if (root.kind === "error") {
            const localizedTitle = root.localizedErrorTitle(
                debugLog.error_type)
            return localizedTitle.length > 0
                ? localizedTitle
                : String(debugLog.error_title || qsTr("Application Error"))
        }
        if (root.kind !== "watch_folder_editor")
            return qsTr(root.windowTitle)
        const target = String(watchFoldersController.editor.title || "")
        const action = watchFoldersController.editingExisting
            ? qsTr("Editing Watch Folder")
            : qsTr("Choose Repositories to Watch")
        return target.length > 0 ? action + " - " + target : action
    }
    title: root.effectiveWindowTitle
    color: root.theme.workspace
    minimumWidth: sizing.windowMinimumWidth(root.kind)
    minimumHeight: sizing.windowMinimumHeight(root.kind)
    width: minimumWidth
    height: minimumHeight

    function syncNativeFrame() {
        windowAppearanceController.apply(
            root,
            root.theme.dark,
            root.theme.topBar,
            root.theme.primaryText
        )
    }

    function restoreGeometry() {
        const relative = root.geometryMode !== "absolute"
        const ownerX = root.ownerWindow ? root.ownerWindow.x : 0
        const ownerY = root.ownerWindow ? root.ownerWindow.y : 0
        const ownerWidth = root.ownerWindow && root.ownerWindow.width > 0
            ? root.ownerWindow.width : 900
        const ownerHeight = root.ownerWindow && root.ownerWindow.height > 0
            ? root.ownerWindow.height : 700

        root.restoringGeometry = true
        root.width = Math.max(
            root.minimumWidth,
            relative ? root.windowWidth * ownerWidth : root.windowWidth
        )
        root.height = Math.max(
            root.minimumHeight,
            relative ? root.windowHeight * ownerHeight : root.windowHeight
        )
        root.x = relative ? ownerX + root.windowX * ownerWidth : root.windowX
        root.y = relative ? ownerY + root.windowY * ownerHeight : root.windowY
        root.restoringGeometry = false
        root.geometryReady = true

        if (relative)
            Qt.callLater(root.saveGeometry)
    }

    function saveGeometry() {
        if (!root.geometryReady || root.restoringGeometry)
            return
        windowModel.set_geometry(
            root.windowId,
            root.x,
            root.y,
            root.width,
            root.height
        )
    }

    function syncContent() {
        if (root.contentRequested) {
            contentRelease.stop()
            if (!windowContentLoader.source.toString().length) {
                windowContentLoader.setSource(
                    Qt.resolvedUrl("WindowContent.qml"),
                    {
                        "theme": root.theme,
                        "contentSource": root.contentSource,
                        "contentProperties": root.contentProperties
                    }
                )
            }
            windowContentLoader.active = true
        } else if (windowContentLoader.active) {
            contentRelease.restart()
        }
    }

    Component.onCompleted: {
        restoreGeometry()
        syncContent()
        Qt.callLater(root.syncNativeFrame)
    }
    onContentRequestedChanged: syncContent()
    onVisibleChanged: {
        if (visible)
            Qt.callLater(root.syncNativeFrame)
    }

    Connections {
        target: root.theme

        function onDarkChanged() {
            Qt.callLater(root.syncNativeFrame)
        }

        function onStyleChanged() {
            Qt.callLater(root.syncNativeFrame)
        }
    }

    onWindowVisibleChanged: {
        if (windowVisible) {
            if (root.kind === "configuration")
                configurationController.begin_session()
            else if (root.kind === "server_presets")
                serverPresetsController.begin_session()
            else if (root.kind === "process_filter_editor")
                processFilterEditorController.begin_session()
            else if (root.kind === "repository_sync_editor")
                repositorySyncEditorController.begin_session()
            else if (root.kind === "advanced_search")
                filterEditorController.begin_session()
            else if (root.kind === "user_profile")
                userController.window_opened()
            else if (root.kind === "sobject_info")
                sobjectInfoController.window_opened()
            else if (root.kind === "watch_folders")
                watchFoldersController.reload()
            Qt.callLater(function() { root.requestActivate() })
        }
    }
    onClosing: function(close) {
        close.accepted = false
        if (root.kind === "error")
            debugLog.dismiss_error()
        else if (root.kind === "configuration")
            configurationController.request_close()
        else if (root.kind === "schema_search_type")
            administrationController.schemaTypeEditor.discard()
        else if (root.kind === "process_dependencies")
            administrationController.workflowEditor.rulesEditor.request_close()
        else {
            if (root.kind === "process_filter_editor")
                processFilterEditorController.cancel()
            else if (root.kind === "server_presets")
                serverPresetsController.cancel()
            else if (root.kind === "repository_sync_editor")
                repositorySyncEditorController.cancel()
            else if (root.kind === "watch_folder_editor")
                watchFoldersController.cancel_edit()
            windowModel.close_window(root.windowId)
        }
    }

    onXChanged: if (geometryReady && visible
            && visibility === Window.Windowed && !restoringGeometry)
        geometrySave.restart()
    onYChanged: if (geometryReady && visible
            && visibility === Window.Windowed && !restoringGeometry)
        geometrySave.restart()
    onWidthChanged: if (geometryReady && visible
            && visibility === Window.Windowed && !restoringGeometry)
        geometrySave.restart()
    onHeightChanged: if (geometryReady && visible
            && visibility === Window.Windowed && !restoringGeometry)
        geometrySave.restart()

    Timer {
        id: geometrySave
        interval: 180
        onTriggered: root.saveGeometry()
    }

    Timer {
        id: contentRelease
        interval: 500
        onTriggered: {
            if (!root.contentRequested && !root.keepWorkspaceWarm)
                windowContentLoader.active = false
        }
    }

    Connections {
        target: windowModel

        function onLayoutReset() {
            geometrySave.stop()
            root.restoreGeometry()
        }
    }

    Connections {
        target: configurationController
        enabled: root.kind === "configuration"

        function onCloseAllowed() {
            windowModel.close_window(root.windowId)
        }
    }

    Loader {
        id: windowContentLoader
        anchors.fill: parent
        active: false
    }
}
