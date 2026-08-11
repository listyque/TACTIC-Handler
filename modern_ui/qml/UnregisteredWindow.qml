import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        Label {
            text: qsTr("TACTIC-Handler")
            color: root.theme.primaryText
            font.pixelSize: 13
        }
        Label {
            text: qsTr("No view is registered for this window.")
            color: root.theme.secondaryText
            font.pixelSize: 10
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
