import QtQuick
import QtQuick.Controls
import "controls" as Controls

Item {
    id: root
    objectName: "tableCellCompletion"

    required property var theme
    property real percent: 0
    property string text: ""
    readonly property real boundedPercent: Math.max(
        0, Math.min(100, percent)
    )

    Accessible.role: Accessible.ProgressBar
    Accessible.name: qsTr("Completion")
    Accessible.description: text || Number(boundedPercent).toFixed(1) + "%"

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.margins: 10
        height: 18
        radius: height / 2
        color: root.theme.surfaceContainer
        border.width: 1
        border.color: root.theme.outlineVariant

        Rectangle {
            objectName: "tableCellCompletionFill"
            width: parent.width * root.boundedPercent / 100
            height: parent.height
            radius: parent.radius
            color: root.theme.action
        }
        Label {
            anchors.centerIn: parent
            text: root.text || Number(root.boundedPercent).toFixed(1) + "%"
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
            font.weight: Font.DemiBold
        }
    }
}
