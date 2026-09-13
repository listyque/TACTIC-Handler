import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    required property var controller
    property bool compact: false
    property var summary: controller.currentSummary

    implicitHeight: compact ? 32 : 80
    radius: theme.itemRadius
    color: theme.surfaceContainerHigh
    border.width: 1
    border.color: theme.outlineVariant

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 9
        anchors.rightMargin: 7
        anchors.topMargin: 3
        anchors.bottomMargin: root.compact ? 3 : 10
        spacing: 5

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 26
            Layout.minimumHeight: 26
            Layout.maximumHeight: 26
            spacing: 7

            Controls.MaterialIcon {
                name: "schedule"
                size: 15
                Layout.alignment: Qt.AlignVCenter
                color: root.summary.overPlan > 0
                    ? root.theme.error : root.theme.action
            }
            Label {
                text: qsTr("WORK HOURS")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                font.weight: Font.DemiBold
                font.letterSpacing: 0.45
                Layout.alignment: Qt.AlignVCenter
            }
            Label {
                visible: root.compact
                text: String(root.summary.label || "")
                    .replace(/ h$/, qsTr(" h"))
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
                Layout.alignment: Qt.AlignVCenter
            }
            Label {
                visible: !root.compact && root.summary.pending > 0
                text: root.summary.pending + qsTr(" h pending")
                color: root.theme.yellow
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                Layout.alignment: Qt.AlignVCenter
            }
            Item { Layout.fillWidth: true }
            Controls.CompactIconButton {
                Layout.preferredWidth: 25
                Layout.preferredHeight: 25
                Layout.alignment: Qt.AlignVCenter
                theme: root.theme
                iconName: "add_alarm"
                toolTip: qsTr("Log time")
                enabled: root.controller.hasTask && !root.controller.busy
                onClicked: logDialog.openForCreate()
            }
            Controls.CompactIconButton {
                Layout.preferredWidth: 25
                Layout.preferredHeight: 25
                Layout.alignment: Qt.AlignVCenter
                theme: root.theme
                iconName: "calendar_month"
                toolTip: qsTr("Open timesheet")
                enabled: !root.controller.busy
                onClicked: root.controller.open_timesheet()
            }
        }

        RowLayout {
            visible: !root.compact
            Layout.fillWidth: true
            Layout.preferredHeight: 28
            spacing: 10

            Repeater {
                model: [
                    {
                        "key": "planned",
                        "label": qsTr("Planned"),
                        "value": root.summary.planned
                    },
                    {
                        "key": "approved",
                        "label": qsTr("Approved"),
                        "value": root.summary.approved
                    },
                    {
                        "key": "remaining",
                        "label": qsTr("Remaining"),
                        "value": root.summary.remaining
                    },
                    {
                        "key": "over_plan",
                        "label": qsTr("Over plan"),
                        "value": root.summary.overPlan
                    }
                ]
                delegate: ColumnLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        text: modelData.value + qsTr(" h")
                        color: modelData.key === "over_plan"
                               && Number(modelData.value) > 0
                            ? root.theme.error : root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        Layout.fillWidth: true
                        text: modelData.label
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.micro
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        }

        Rectangle {
            visible: !root.compact
            Layout.fillWidth: true
            Layout.preferredHeight: 3
            radius: 1.5
            color: root.theme.surfaceContainerHighest
            Rectangle {
                width: parent.width * Math.max(
                    0, Math.min(100, Number(root.summary.progress || 0))
                ) / 100
                height: parent.height
                radius: parent.radius
                color: Number(root.summary.overPlan || 0) > 0
                    ? root.theme.error : root.theme.action
            }
        }
    }

    WorkHourEditorDialog {
        id: logDialog
        parent: Overlay.overlay
        theme: root.theme
        controller: root.controller
    }
}
