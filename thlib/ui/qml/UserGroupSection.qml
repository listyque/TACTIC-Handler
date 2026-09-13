import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property string title: ""
    property bool compact: false
    property bool shown: true

    visible: shown
    implicitHeight: shown ? (compact ? 28 : 34) : 0

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        spacing: 7

        Controls.MaterialIcon {
            name: "groups"
            size: root.compact ? 11 : 13
            color: root.theme.secondaryText
        }
        Label {
            text: root.title === "Ungrouped"
                ? qsTr("UNGROUPED") : root.title.toUpperCase()
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pixelSize: root.compact ? 8 : 9
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.separator
        }
    }
}
