import QtQuick
import QtQuick.Controls
import "." as Controls

Rectangle {
    id: root
    required property var theme
    property bool vertical: true

    implicitWidth: 10
    implicitHeight: 10
    color: "transparent"

    Controls.ResizeGripVisual {
        objectName: "splitterGripVisual"
        anchors.centerIn: parent
        theme: root.theme
        vertical: root.vertical
        hovered: root.SplitHandle.hovered
        pressed: root.SplitHandle.pressed
    }
}
