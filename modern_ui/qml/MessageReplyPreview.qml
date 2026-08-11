import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    required property var theme
    property string sender: ""
    property string body: ""
    property bool dismissible: false
    property bool available: true
    signal activated()
    signal dismissed()

    implicitHeight: Math.max(54, replyContent.implicitHeight + 14)
    radius: 10
    color: root.theme.surfaceContainerHighest
    border.width: 1
    border.color: root.theme.outlineVariant

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 4
        radius: 2
        color: root.available ? root.theme.action : root.theme.error
    }

    RowLayout {
        id: replyContent
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 7
        anchors.topMargin: 7
        anchors.bottomMargin: 7
        spacing: 8

        MaterialIcon {
            name: "reply"
            size: 18
            color: root.available ? root.theme.action : root.theme.error
            Layout.alignment: Qt.AlignTop
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            Label {
                Layout.fillWidth: true
                text: root.available
                    ? qsTr("Reply to ")
                        + (root.sender || qsTr("Unknown user"))
                    : qsTr("Original message unavailable")
                color: root.available ? root.theme.action : root.theme.error
                font.family: root.theme.fontFamily
                font.pixelSize: 10
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            Label {
                Layout.fillWidth: true
                visible: root.available && root.body.length > 0
                text: root.body
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 11
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
        }

        CompactIconButton {
            visible: root.dismissible
            theme: root.theme
            iconName: "close"
            toolTip: qsTr("Cancel reply")
            onClicked: root.dismissed()
        }
    }

    TapHandler {
        enabled: !root.dismissible && root.available
        acceptedButtons: Qt.LeftButton
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onTapped: root.activated()
    }
}
