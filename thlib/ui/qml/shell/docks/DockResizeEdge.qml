import QtQuick
import "../../controls" as Controls

Item {
    id: root
    objectName: "dockResizeEdge_" + edge
    required property var panel
    property string edge: "right"
    property int edgeCursor: edge === "left" || edge === "right" ? Qt.SizeHorCursor : edge === "top" || edge === "bottom" ? Qt.SizeVerCursor : edge === "top_left" || edge === "bottom_right" ? Qt.SizeFDiagCursor : Qt.SizeBDiagCursor
    readonly property bool verticalEdge: edge === "left" || edge === "right"

    Controls.ResizeGripVisual {
        objectName: "dockResizeGripVisual"
        theme: root.panel.theme
        vertical: root.verticalEdge
        hovered: handle.containsMouse
        pressed: handle.pressed
    }

    MouseArea {
        id: handle
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton
        cursorShape: root.edgeCursor
        preventStealing: true

        onPressed: function (mouse) {
            root.panel.beginResize(root.edge, handle, mouse.x, mouse.y);
            mouse.accepted = true;
        }
        onPositionChanged: function (mouse) {
            if (pressed)
                root.panel.updateResize(handle, mouse.x, mouse.y);
        }
        onReleased: root.panel.finishResize()
        onCanceled: root.panel.cancelResize()
    }
}
