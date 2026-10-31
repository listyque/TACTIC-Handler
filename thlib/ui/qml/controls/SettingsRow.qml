import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    property string title: ""
    property string description: ""
    property bool showDivider: true
    property int controlAlignment: Qt.AlignVCenter
    default property alias controlData: accessory.data
    readonly property bool stackControl: width > 0 && accessory.implicitWidth > 0 && width - settingLayout.columnSpacing - accessory.implicitWidth < 210

    Layout.fillWidth: true
    implicitHeight: Math.max(theme.controlHeight, settingLayout.implicitHeight) + theme.spacing.content

    GridLayout {
        id: settingLayout
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 0
        anchors.rightMargin: 0
        columns: root.stackControl ? 1 : 2
        columnSpacing: root.theme.spacing.content
        rowSpacing: root.theme.spacing.compact

        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.row: 0
            Layout.column: 0
            spacing: root.theme.spacing.tight

            Label {
                Layout.fillWidth: true
                text: root.title
                color: root.enabled ? root.theme.primaryText : root.theme.disabledText
                font.family: root.theme.fontFamily
                font.hintingPreference: Font.PreferVerticalHinting
                font.pixelSize: 13
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            Label {
                visible: root.description.length > 0
                Layout.fillWidth: true
                text: root.description
                color: root.enabled ? root.theme.secondaryText : root.theme.disabledText
                font.family: root.theme.fontFamily
                font.hintingPreference: Font.PreferVerticalHinting
                font.pixelSize: Foundation.textStyles.caption
                wrapMode: Text.WordWrap
            }
        }

        RowLayout {
            id: accessory
            Layout.row: root.stackControl ? 1 : 0
            Layout.column: root.stackControl ? 0 : 1
            Layout.fillWidth: root.stackControl
            Layout.alignment: root.stackControl ? Qt.AlignRight : root.controlAlignment | Qt.AlignRight
            spacing: root.theme.spacing.compact

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
        anchors.leftMargin: 0
        anchors.rightMargin: 0
        height: 1
        color: root.theme.outlineVariant
    }
}
