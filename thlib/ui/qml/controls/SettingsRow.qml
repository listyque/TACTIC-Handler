import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Item {
    id: root

    required property var theme
    property string title: ""
    property string description: ""
    property bool showDivider: true
    property int controlAlignment: Qt.AlignVCenter
    default property alias controlData: accessory.data
    readonly property bool stackControl: width > 0
        && accessory.implicitWidth > 0
        && width - 8 - settingLayout.columnSpacing - accessory.implicitWidth < 210

    Layout.fillWidth: true
    implicitHeight: Math.max(54, settingLayout.implicitHeight + 20)

    GridLayout {
        id: settingLayout
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 4
        anchors.rightMargin: 4
        columns: root.stackControl ? 1 : 2
        columnSpacing: 20
        rowSpacing: 8

        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.row: 0
            Layout.column: 0
            spacing: 3

            Label {
                Layout.fillWidth: true
                text: root.title
                color: root.enabled
                    ? root.theme.primaryText : root.theme.disabledText
                font.family: root.theme.fontFamily
                font.pixelSize: 13
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            Label {
                visible: root.description.length > 0
                Layout.fillWidth: true
                text: root.description
                color: root.enabled
                    ? root.theme.secondaryText : root.theme.disabledText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                wrapMode: Text.WordWrap
            }
        }

        RowLayout {
            id: accessory
            Layout.row: root.stackControl ? 1 : 0
            Layout.column: root.stackControl ? 0 : 1
            Layout.fillWidth: root.stackControl
            Layout.alignment: root.stackControl
                ? Qt.AlignRight
                : root.controlAlignment | Qt.AlignRight
            spacing: 8

            Item {
                visible: root.stackControl
                Layout.fillWidth: visible
            }
        }
    }

    Rectangle {
        visible: root.showDivider
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 4
        anchors.rightMargin: 4
        height: 1
        color: root.theme.outlineVariant
    }
}
