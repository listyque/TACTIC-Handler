import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    property string sender: ""
    property string body: ""
    property int attachmentCount: 0
    property bool available: true
    signal activated()

    implicitHeight: Math.max(62, content.implicitHeight + 16)
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
        color: root.available ? root.theme.tertiary : root.theme.error
    }

    RowLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 8
        anchors.leftMargin: 12
        spacing: 8

        Controls.MaterialIcon {
            name: "share"
            size: 18
            color: root.available ? root.theme.tertiary : root.theme.error
            Layout.alignment: Qt.AlignTop
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3

            Label {
                Layout.fillWidth: true
                text: root.available
                    ? qsTr("Forwarded from ")
                        + (root.sender || qsTr("Unknown user"))
                    : qsTr("Forwarded message unavailable")
                color: root.available ? root.theme.tertiary : root.theme.error
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            Label {
                Layout.fillWidth: true
                visible: root.available && root.body.length > 0
                text: root.body
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                wrapMode: Text.Wrap
                maximumLineCount: 3
                elide: Text.ElideRight
            }

            Label {
                visible: root.available && root.attachmentCount > 0
                text: root.attachmentCount + (root.attachmentCount === 1
                    ? qsTr(" attachment") : qsTr(" attachments"))
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
            }
        }
    }

    Controls.ActivationHandler {
        enabled: root.available
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onActivated: root.activated()
    }
}
