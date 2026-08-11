import QtQuick
import QtQuick.Window

// Native Windows dialog frame with application-owned MD3 content.
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
        || kind === "repository_editor"
    readonly property bool contentRequested: windowVisible
        && (workspaceEnabled || availableWhileSignedOut)
    visible: contentRequested
    title: qsTr(root.windowTitle)
    color: root.theme.workspace
    minimumWidth: sizing.windowMinimumWidth(root.kind)
    minimumHeight: sizing.windowMinimumHeight(root.kind)
    width: minimumWidth
    height: minimumHeight

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
            if (!windowContentLoader.source.toString().length) {
                windowContentLoader.setSource(
                    Qt.resolvedUrl("WindowContent.qml"),
                    {
                        "theme": root.theme,
                        "kind": root.kind,
                        "windowId": root.windowId
                    }
                )
            }
            windowContentLoader.active = true
        }
    }

    Component.onCompleted: {
        restoreGeometry()
        syncContent()
    }
    onContentRequestedChanged: syncContent()

    onWindowVisibleChanged: {
        if (windowVisible) {
            if (root.kind === "configuration")
                configurationController.begin_session()
            else if (root.kind === "filter_editor")
                filterEditorController.begin_session()
            else if (root.kind === "add_sobject"
                    || root.kind === "task_editor")
                sobjectEditorController.begin_session()
            else if (root.kind === "link_sobjects")
                sobjectLinkController.begin_session()
            else if (root.kind === "user_profile")
                userController.window_opened()
            Qt.callLater(function() { root.requestActivate() })
        }
    }
    onClosing: function(close) {
        close.accepted = false
        if (root.kind === "configuration")
            configurationController.request_close()
        else {
            if (root.kind === "filter_editor")
                filterEditorController.cancel()
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
