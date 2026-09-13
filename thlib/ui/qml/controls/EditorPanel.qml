import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Rectangle {
    id: root

    required property var theme
    property string title: ""
    property string description: ""
    property string iconName: ""
    property bool fillContentHeight: true
    property real padding: 14
    property alias actions: headerActions.data
    default property alias contentData: body.data

    implicitHeight: layout.implicitHeight + padding * 2
    radius: theme.surfaceRadius
    color: theme.surfaceContainerLow
    border.width: 1
    border.color: theme.outlineVariant

    ColumnLayout {
        id: layout
        anchors.fill: parent
        anchors.margins: root.padding
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            visible: root.title.length > 0 || headerActions.children.length > 0
            spacing: 10
            Controls.MaterialIcon {
                visible: root.iconName.length > 0
                name: root.iconName
                size: 20
                color: root.theme.action
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                spacing: 3
                Label {
                    Layout.fillWidth: true
                    text: root.title
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
                Label {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: root.description
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
            }
            RowLayout { id: headerActions; spacing: 6 }
        }
        ColumnLayout {
            id: body
            Layout.fillWidth: true
            Layout.fillHeight: root.fillContentHeight
            Layout.minimumWidth: 0
            spacing: 10
        }
    }
}
