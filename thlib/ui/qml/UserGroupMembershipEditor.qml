import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var model
    required property var selectedGroups
    property bool showAccessLevels: false
    property var accessLevels: ({})
    readonly property var accessLevelOptions: [
        {label: qsTr("Server default (Low)"), value: ""},
        {label: qsTr("High"), value: "high"},
        {label: qsTr("Medium"), value: "medium"},
        {label: qsTr("Low"), value: "low"},
        {label: qsTr("Minimum"), value: "min"},
        {label: qsTr("None"), value: "none"}
    ]
    signal groupToggled(string code, bool selected)
    signal accessLevelEdited(string code, string value)

    function accessLevelIndex(value) {
        const normalized = String(value || "").trim().toLowerCase()
        for (let index = 0; index < accessLevelOptions.length; ++index) {
            if (accessLevelOptions[index].value === normalized)
                return index
        }
        return 0
    }

    spacing: 6

    Label {
        Layout.fillWidth: true
        text: qsTr("Group membership changes affect this user's permissions.")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.body
        wrapMode: Text.WordWrap
    }
    Label {
        visible: root.showAccessLevels
        Layout.fillWidth: true
        text: qsTr("Access level is shared by every member of the group. Empty uses TACTIC's Low default.")
        color: root.theme.yellow
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        wrapMode: Text.WordWrap
    }
    Repeater {
        model: root.visible ? root.model : null
        delegate: Rectangle {
            id: groupRow
            required property string code
            required property string label
            required property string description
            required property string accessLevel
            required property string projectCode
            required property bool isDefault
            Layout.fillWidth: true
            Layout.preferredHeight: root.showAccessLevels ? 78 : 58
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerHigh
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 8
                Controls.CheckBox {
                    objectName: "userGroupMembership_" + groupRow.code
                    theme: root.theme
                    checked: root.selectedGroups.indexOf(groupRow.code) >= 0
                    prominent: true
                    Accessible.name: groupRow.label
                    onToggled: root.groupToggled(groupRow.code, checked)
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 1
                    Label {
                        Layout.fillWidth: true
                        text: groupRow.label
                        textFormat: Text.PlainText
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        visible: groupRow.description.length > 0
                        Layout.fillWidth: true
                        text: groupRow.description
                        textFormat: Text.PlainText
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                    Label {
                        visible: groupRow.projectCode.length > 0 || groupRow.isDefault
                        Layout.fillWidth: true
                        text: groupRow.projectCode.length > 0
                            ? qsTr("Project: %1").arg(groupRow.projectCode) : qsTr("Default group")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                }
                Controls.ComboBox {
                    objectName: "userGroupAccessLevel_" + groupRow.code
                    visible: root.showAccessLevels
                    Layout.preferredWidth: 184
                    theme: root.theme
                    model: root.accessLevelOptions
                    textRole: "label"
                    valueRole: "value"
                    currentIndex: root.accessLevelIndex(root.accessLevels[groupRow.code] ?? groupRow.accessLevel)
                    onActivated: index => root.accessLevelEdited(
                        groupRow.code, root.accessLevelOptions[index].value)
                }
            }
        }
    }
}
