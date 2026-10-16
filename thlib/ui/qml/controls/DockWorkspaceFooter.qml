import QtQuick
import QtQuick.Window
import "../tactic_frame/shell/dock.surface.mjs" as Surface

Rectangle {
    id: root

    required property var theme
    property bool roundTopLeft: false
    property bool roundTopRight: false
    // Native dialog frames own their exterior corners; rounding the content
    // a second time exposes a strip of the window background underneath.
    readonly property bool nativeDialog: Window.window !== null && (Window.window.flags & Qt.WindowType_Mask) === Qt.Dialog
    property bool roundBottomLeft: !nativeDialog
    property bool roundBottomRight: !nativeDialog
    property bool topDividerVisible: true
    readonly property real cornerRadius: frameSurface.radius

    readonly property var frameSurface: Surface.footer(theme.surfaceRadius, nativeDialog, {
        topLeft: roundTopLeft,
        topRight: roundTopRight,
        bottomLeft: roundBottomLeft,
        bottomRight: roundBottomRight,
        divider: topDividerVisible
    })
    implicitHeight: frameSurface.height
    radius: cornerRadius
    topLeftRadius: frameSurface.topLeft
    topRightRadius: frameSurface.topRight
    bottomLeftRadius: frameSurface.bottomLeft
    bottomRightRadius: frameSurface.bottomRight
    color: theme.surfaceContainer
    antialiasing: true

    Rectangle {
        objectName: "dockWorkspaceFooterDivider"
        visible: root.topDividerVisible
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: root.frameSurface.divider
        color: root.theme.outlineVariant
        z: 100
    }
}
