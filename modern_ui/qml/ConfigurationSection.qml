import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

Rectangle {
    id: root

    required property var theme
    property string title: ""
    property string description: ""
    property string iconName: "settings"
    default property alias contentData: sectionContent.data

    implicitHeight: sectionLayout.implicitHeight + 32
    radius: theme.sectionRadius
    color: theme.surfaceContainerLow
    border.width: 1
    border.color: theme.outlineVariant

    ColumnLayout {
        id: sectionLayout
        anchors.fill: parent
        anchors.margins: 16
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            spacing: 11

            Rectangle {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                radius: root.theme.itemRadius
                color: root.theme.secondaryContainer

                MaterialIcon {
                    anchors.centerIn: parent
                    name: root.iconName
                    size: 18
                    color: root.theme.action
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Label {
                    Layout.fillWidth: true
                    text: qsTr(root.title)
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
                Label {
                    visible: root.description.length > 0
                    Layout.fillWidth: true
                    text: root.description
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 9
                    wrapMode: Text.WordWrap
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.outlineVariant
        }

        ColumnLayout {
            id: sectionContent
            Layout.fillWidth: true
            spacing: 10
        }
    }
}
