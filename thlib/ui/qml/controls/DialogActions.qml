import QtQuick
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    default property alias content: actionRow.data
    property real horizontalMargin: 14
    property real verticalMargin: 12

    implicitWidth: actionRow.implicitWidth + horizontalMargin * 2
    implicitHeight: actionRow.implicitHeight + verticalMargin * 2

    RowLayout {
        id: actionRow
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: root.horizontalMargin
        anchors.bottomMargin: root.verticalMargin
        spacing: 8
    }
}
