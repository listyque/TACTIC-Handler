import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root
    objectName: "userWorkSummary"

    required property var theme
    required property var userController
    required property var tasksController

    function hours(value) {
        const number = Number(value || 0)
        return Number.isInteger(number) ? number.toFixed(0) : number.toFixed(1)
    }

    spacing: 12

    RowLayout {
        Layout.fillWidth: true

        Controls.SectionLabel {
            Layout.fillWidth: true
            theme: root.theme
            text: qsTr("PROJECT TASKS")
        }
        Label {
            text: qsTr("%1 tasks").arg(
                root.userController.taskSummary.total || 0
            )
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
        }
    }

    GridLayout {
        Layout.fillWidth: true
        columns: 3
        columnSpacing: 14

        Repeater {
            model: [{
                "key": "incomplete",
                "label": qsTr("Incomplete")
            }, {
                "key": "overdue",
                "label": qsTr("Overdue")
            }, {
                "key": "dueThisWeek",
                "label": qsTr("Due this week")
            }]

            delegate: ColumnLayout {
                required property var modelData

                Layout.fillWidth: true
                spacing: 1

                Label {
                    text: Number(
                        root.userController.taskSummary[modelData.key] || 0
                    )
                    color: modelData.key === "overdue" && Number(text) > 0
                        ? root.theme.error : root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 22
                    font.weight: Font.DemiBold
                }
                Label {
                    text: modelData.label
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
            }
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: root.theme.separator
    }

    Controls.SectionLabel {
        theme: root.theme
        text: qsTr("BY STATUS")
    }
    Flow {
        Layout.fillWidth: true
        spacing: 6

        Repeater {
            model: root.userController.taskStatusSummary
            delegate: Controls.SummaryChip {
                required property var modelData
                theme: root.theme
                label: modelData.label || qsTr("Unspecified")
                count: Number(modelData.count || 0)
                accent: modelData.color || root.theme.action
            }
        }
    }

    Controls.SectionLabel {
        theme: root.theme
        text: qsTr("BY PROCESS")
    }
    Flow {
        Layout.fillWidth: true
        spacing: 6

        Repeater {
            model: root.userController.taskProcessSummary
            delegate: Controls.SummaryChip {
                required property var modelData
                theme: root.theme
                label: modelData.label || qsTr("Unspecified")
                count: Number(modelData.count || 0)
                accent: modelData.color || root.theme.action
            }
        }
    }

    ColumnLayout {
        objectName: "profileWorkHoursSection"
        visible: root.userController.canViewWorkHours
        Layout.fillWidth: true
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.separator
        }

        RowLayout {
            Layout.fillWidth: true

            Controls.SectionLabel {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("WORK HOURS")
            }
            Label {
                text: qsTr("THIS WEEK")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                font.weight: Font.DemiBold
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 3
            columnSpacing: 14

            Repeater {
                model: [{
                    "key": "loggedHours",
                    "label": qsTr("Logged")
                }, {
                    "key": "approvedHours",
                    "label": qsTr("Approved")
                }, {
                    "key": "pendingHours",
                    "label": qsTr("Pending")
                }]

                delegate: ColumnLayout {
                    required property var modelData

                    Layout.fillWidth: true
                    spacing: 1

                    Label {
                        text: qsTr("%1 h").arg(root.hours(
                            root.userController.workHourSummary[
                                modelData.key
                            ]
                        ))
                        color: modelData.key === "pendingHours"
                                && Number(root.userController.workHourSummary[
                                    modelData.key
                                ] || 0) > 0
                            ? root.theme.yellow : root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: modelData.label
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                }
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true

        Controls.Button {
            theme: root.theme
            text: qsTr("OPEN TASK MANAGER")
            icon.name: "tasks"
            highlighted: true
            enabled: !!root.userController.profile.login
            onClicked: root.tasksController.open_for_user(
                root.userController.profile.login
            )
        }
        Item { Layout.fillWidth: true }
    }

    Label {
        Layout.fillWidth: true
        visible: !root.userController.tasksBusy
            && (root.userController.taskSummary.total || 0) === 0
        text: qsTr("No assigned tasks in the current project")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
    }
}
