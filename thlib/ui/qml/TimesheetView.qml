import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property bool presentationActive:
        parent ? parent.visible : visible
    property bool initialized: false
    readonly property bool wrapSupervisorTools:
        workHoursController.canManage && width < 650

    function ensureLoaded() {
        if (!presentationActive || initialized)
            return
        initialized = true
        workHoursController.load_timesheet()
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    function userIndex(login) {
        for (let index = 0; index < userListModel.count(); ++index) {
            if (String(userListModel.get(index).login || "")
                    === String(login || ""))
                return index
        }
        return -1
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: root.wrapSupervisorTools ? 82 : 46
            color: root.theme.toolBar

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 7
                anchors.topMargin: 4
                anchors.bottomMargin: 4
                spacing: 2

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    spacing: 6

                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "chevron_left"
                    toolTip: qsTr("Previous week")
                    onClicked: workHoursController.move_week(-1)
                }
                Controls.DateField {
                    theme: root.theme
                    Layout.preferredWidth: 126
                    Layout.preferredHeight: root.theme.compactControlHeight
                    text: workHoursController.weekStart
                    placeholderText: qsTr("Week")
                    onAccepted: value => workHoursController.set_week(value)
                }
                Label {
                    visible: root.width >= 760
                    text: workHoursController.weekStart + "  -  "
                        + workHoursController.weekEnd
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "chevron_right"
                    toolTip: qsTr("Next week")
                    onClicked: workHoursController.move_week(1)
                }
                Item { Layout.fillWidth: true }
                RowLayout {
                    visible: workHoursController.selectedCount > 0
                        && !root.wrapSupervisorTools
                    spacing: 3
                    Label {
                        text: workHoursController.selectedCount + qsTr(" selected")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "approval"
                        toolTip: qsTr("Approve selected entries")
                        onClicked: workHoursController.approve_selected(true)
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "undo"
                        toolTip: qsTr("Return selected entries to pending")
                        onClicked: workHoursController.approve_selected(false)
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "close"
                        toolTip: qsTr("Clear selection")
                        onClicked: workHoursController.clear_timesheet_selection()
                    }
                }
                UserComboBox {
                    visible: workHoursController.canManage
                        && !root.wrapSupervisorTools
                    theme: root.theme
                    Layout.preferredWidth: Math.min(220, root.width * 0.28)
                    Layout.preferredHeight: root.theme.compactControlHeight
                    userModel: userListModel
                    model: userListModel
                    textRole: "displayName"
                    valueRole: "login"
                    currentIndex: root.userIndex(
                        workHoursController.selectedLogin
                    )
                    onActivated: workHoursController.set_selected_login(
                        String(currentValue || "")
                    )
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "add_alarm"
                    toolTip: workHoursController.hasTask
                        ? qsTr("Log time for the selected task")
                        : qsTr("Select a task before logging time")
                    enabled: workHoursController.hasTask
                        && !workHoursController.busy
                    onClicked: entryEditor.openForCreate()
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "bar_chart"
                    toolTip: qsTr("Open work reports")
                    onClicked: workHoursController.open_work_reports()
                }
                RefreshIconButton {
                    theme: root.theme
                    toolTip: qsTr("Refresh timesheet")
                    enabled: !workHoursController.busy
                    onClicked: workHoursController.refresh_timesheet()
                }
                }

                RowLayout {
                    visible: root.wrapSupervisorTools
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? 34 : 0
                    spacing: 6
                    Label {
                        text: qsTr("Team member")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                    UserComboBox {
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.theme.compactControlHeight
                        userModel: userListModel
                        model: userListModel
                        textRole: "displayName"
                        valueRole: "login"
                        currentIndex: root.userIndex(
                            workHoursController.selectedLogin
                        )
                        onActivated: workHoursController.set_selected_login(
                            String(currentValue || "")
                        )
                    }
                    Label {
                        visible: workHoursController.selectedCount > 0
                        text: workHoursController.selectedCount + qsTr(" selected")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                    Controls.CompactIconButton {
                        visible: workHoursController.selectedCount > 0
                        theme: root.theme
                        iconName: "approval"
                        toolTip: qsTr("Approve selected entries")
                        onClicked: workHoursController.approve_selected(true)
                    }
                    Controls.CompactIconButton {
                        visible: workHoursController.selectedCount > 0
                        theme: root.theme
                        iconName: "undo"
                        toolTip: qsTr("Return selected entries to pending")
                        onClicked: workHoursController.approve_selected(false)
                    }
                    Controls.CompactIconButton {
                        visible: workHoursController.selectedCount > 0
                        theme: root.theme
                        iconName: "close"
                        toolTip: qsTr("Clear selection")
                        onClicked: workHoursController
                            .clear_timesheet_selection()
                    }
                }
            }
        }

        Controls.DockWorkspaceFooter {
            theme: root.theme
            Layout.fillWidth: true
            Layout.preferredHeight: implicitHeight

            RowLayout {
                anchors.fill: parent
                anchors.margins: 7
                spacing: 7

                Repeater {
                    model: [
                        {
                            "label": qsTr("Logged"),
                            "value": workHoursController.timesheetSummary.logged
                        },
                        {
                            "label": qsTr("Approved"),
                            "value": workHoursController.timesheetSummary.approved
                        },
                        {
                            "label": qsTr("Pending"),
                            "value": workHoursController.timesheetSummary.pending
                        },
                        {
                            "label": qsTr("Overtime"),
                            "value": workHoursController.timesheetSummary.overtime
                        }
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: root.theme.itemRadius
                        color: root.theme.surfaceContainerHigh
                        Column {
                            anchors.centerIn: parent
                            spacing: 1
                            Label {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.value + qsTr(" h")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.bodyLarge
                                font.weight: Font.DemiBold
                            }
                            Label {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.label
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                            }
                        }
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Controls.SmoothListView {
                theme: root.theme
                id: entriesView
                anchors.fill: parent
                anchors.margins: 7
                spacing: 5
                clip: true
                model: timesheetModel
                reuseItems: true
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                    flickableTarget: entriesView
                }

                delegate: Rectangle {
                    id: entryDelegate
                    required property int index
                    required property string entryCode
                    required property string taskTitle
                    required property string process
                    required property string loginLabel
                    required property string day
                    required property real totalHours
                    required property real overtimeHours
                    required property string status
                    required property string statusLabel
                    required property string description
                    required property bool canEdit
                    required property bool canApprove
                    required property bool selected

                    width: entriesView.width
                    height: 62
                    radius: root.theme.itemRadius
                    color: entryDelegate.selected
                        ? root.theme.surfaceContainerHighest
                        : entryMouse.containsMouse
                            ? root.theme.rowHover
                            : root.theme.surfaceContainerLow

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 7
                        spacing: 9

                        Controls.CheckBox {
                            visible: entryDelegate.canApprove
                            theme: root.theme
                            Layout.preferredWidth: visible ? 24 : 0
                            Layout.preferredHeight: 24
                            checked: entryDelegate.selected
                            onClicked: workHoursController
                                .toggle_timesheet_selected(entryDelegate.index)
                        }

                        Rectangle {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            radius: root.theme.itemRadius
                            color: root.theme.surfaceContainerHighest
                            Column {
                                anchors.centerIn: parent
                                Label {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: entryDelegate.day.slice(8, 10)
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                }
                                Label {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: entryDelegate.day.slice(5, 7)
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.micro
                                }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                Layout.fillWidth: true
                                text: entryDelegate.taskTitle
                                    + (entryDelegate.process
                                        ? "  ·  " + entryDelegate.process : "")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: [
                                    entryDelegate.loginLabel === "Removed user"
                                        ? qsTr("Removed user")
                                        : entryDelegate.loginLabel,
                                    entryDelegate.description].filter(Boolean).join("  ·  ")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                        Label {
                            visible: entryDelegate.overtimeHours > 0
                            text: qsTr("OT ") + entryDelegate.overtimeHours
                                + qsTr(" h")
                            color: root.theme.yellow
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }
                        Label {
                            text: entryDelegate.totalHours + qsTr(" h")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                        Rectangle {
                            Layout.preferredWidth: statusText.implicitWidth + 14
                            Layout.preferredHeight: 24
                            radius: 12
                            color: entryDelegate.status === "approved"
                                ? root.theme.surfaceContainerHighest
                                : root.theme.surfaceContainerHighest
                            Label {
                                id: statusText
                                anchors.centerIn: parent
                                text: entryDelegate.status === "approved"
                                    ? qsTr("Approved")
                                    : qsTr("Pending")
                                color: entryDelegate.status === "approved"
                                    ? root.theme.green : root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                            }
                        }
                        Controls.CompactIconButton {
                            visible: entryDelegate.canApprove
                            theme: root.theme
                            iconName: entryDelegate.status === "approved"
                                ? "undo" : "approval"
                            toolTip: entryDelegate.status === "approved"
                                ? qsTr("Return to pending")
                                : qsTr("Approve entry")
                            onClicked: workHoursController.set_approved(
                                entryDelegate.entryCode,
                                entryDelegate.status !== "approved"
                            )
                        }
                        Controls.CompactIconButton {
                            visible: entryDelegate.canEdit
                            theme: root.theme
                            iconName: "edit"
                            toolTip: qsTr("Edit entry")
                            onClicked: entryEditor.openForEdit(
                                timesheetModel.get(entryDelegate.index)
                            )
                        }
                        Controls.CompactIconButton {
                            visible: entryDelegate.canEdit
                            theme: root.theme
                            iconName: "delete"
                            iconColor: root.theme.error
                            toolTip: qsTr("Delete entry")
                            onClicked: workHoursController.remove_entry(
                                entryDelegate.entryCode
                            )
                        }
                    }

                    MouseArea {
                        id: entryMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton
                    }
                }

                Label {
                    anchors.centerIn: parent
                    visible: timesheetModel.count() === 0
                        && !workHoursController.busy
                    text: qsTr("No work hours for this week")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                }
            }

            Controls.BusyIndicator {
                uiTheme: root.theme
                anchors.centerIn: parent
                running: workHoursController.busy
                visible: running
            }
        }

        Label {
            visible: workHoursController.error.length > 0
            Layout.fillWidth: true
            Layout.margins: 8
            text: workHoursController.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }
    }

    WorkHourEditorDialog {
        id: entryEditor
        parent: Overlay.overlay
        theme: root.theme
        controller: workHoursController
    }

    Component.onCompleted: ensureLoaded()
    onPresentationActiveChanged: ensureLoaded()
}
