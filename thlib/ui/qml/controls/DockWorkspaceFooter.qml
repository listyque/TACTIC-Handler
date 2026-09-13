import QtQuick

Rectangle {
    id: root

    required property var theme
    property bool roundTopLeft: false
    property bool roundTopRight: false
    property bool roundBottomLeft: true
    property bool roundBottomRight: true
    property bool topDividerVisible: true
    readonly property real cornerRadius: Math.max(
        0, theme.surfaceRadius - 1
    )

    implicitHeight: theme.dockWorkspaceFooterHeight
    radius: cornerRadius
    topLeftRadius: roundTopLeft ? cornerRadius : 0
    topRightRadius: roundTopRight ? cornerRadius : 0
    bottomLeftRadius: roundBottomLeft ? cornerRadius : 0
    bottomRightRadius: roundBottomRight ? cornerRadius : 0
    color: theme.surfaceContainer
    antialiasing: true

    Rectangle {
        objectName: "dockWorkspaceFooterDivider"
        visible: root.topDividerVisible
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 1
        color: root.theme.outlineVariant
        z: 100
    }
}
