import QtQuick

Item {
    id: root
    required property var panel
    property string edge: "right"
    property int edgeCursor: edge === "left" || edge === "right"
        ? Qt.SizeHorCursor
        : edge === "top" || edge === "bottom"
            ? Qt.SizeVerCursor
            : edge === "top_left" || edge === "bottom_right"
                ? Qt.SizeFDiagCursor : Qt.SizeBDiagCursor
    readonly property bool verticalEdge:
        edge === "left" || edge === "right"

    Rectangle {
        anchors.centerIn: parent
        width: root.verticalEdge ? 2 : Math.min(34, parent.width)
        height: root.verticalEdge ? Math.min(34, parent.height) : 2
        radius: 1
        color: handle.pressed
            ? root.panel.theme.action : root.panel.theme.outlineVariant
        opacity: handle.pressed ? 1 : handle.containsMouse ? 0.85 : 0.28
        Behavior on opacity {
            NumberAnimation { duration: root.panel.theme.hoverMotionFast; easing.type: Easing.OutCubic }
        }
        Behavior on color {
            ColorAnimation { duration: root.panel.theme.hoverMotionFast; easing.type: Easing.OutCubic }
        }
    }

    MouseArea {
        id: handle
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton
        cursorShape: root.edgeCursor
        preventStealing: true

        onPressed: function(mouse) {
            root.panel.beginResize(root.edge, handle, mouse.x, mouse.y)
            mouse.accepted = true
        }
        onPositionChanged: function(mouse) {
            if (pressed)
                root.panel.updateResize(handle, mouse.x, mouse.y)
        }
        onReleased: root.panel.finishResize()
        onCanceled: root.panel.finishResize()
    }
}
