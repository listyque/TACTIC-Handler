import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/workhours/sheet.ui.mjs" as UI

Item {
    id: root

    required property var theme
    property bool presentationActive: parent ? parent.visible : visible
    property bool initialized: false
    readonly property bool wrapSupervisorTools: workHoursController.canManage && width < 650

    function ensureLoaded() {
        if (!presentationActive || initialized)
            return;
        initialized = true;
        workHoursController.load_timesheet();
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    function userIndex(login) {
        for (let index = 0; index < userListModel.count(); ++index) {
            if (String(userListModel.get(index).login || "") === String(login || ""))
                return index;
        }
        return -1;
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Frame.FrameView {
            id: toolbar
            Layout.fillWidth: true
            Layout.preferredHeight: scene.height
            theme: root.theme
            readonly property var presentation: ({
                    weekStart: workHoursController.weekStart,
                    login: workHoursController.selectedLogin,
                    busy: workHoursController.busy,
                    canCreate: workHoursController.hasTask,
                    canManage: workHoursController.canManage,
                    selectedCount: workHoursController.selectedCount,
                    users: userListModel.records().map(row => Object.assign({}, row, {
                            value: row.login,
                            label: row.displayName || row.login
                        }))
                })
            scene: UI.toolbar(presentation, width, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
            onEvent: action => {
                if (action.type === "week")
                    workHoursController.move_week(action.value);
                else if (action.type === "date")
                    workHoursController.set_week(action.value);
                else if (action.type === "user")
                    workHoursController.set_selected_login(action.value);
                else if (action.type === "refresh")
                    workHoursController.refresh_timesheet();
                else if (action.type === "reports")
                    workHoursController.open_work_reports();
                else if (action.type === "create")
                    entryEditor.openForCreate();
                else if (action.type === "clear")
                    workHoursController.clear_timesheet_selection();
                else
                    workHoursController.approve_selected(action.type === "approve");
            }
        }

        Frame.FrameView {
            Layout.fillWidth: true
            Layout.preferredHeight: scene.height
            theme: root.theme
            scene: UI.summary(workHoursController.timesheetSummary, width, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Controls.SmoothListView {
                id: entriesView
                theme: root.theme
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

                delegate: Frame.FrameView {
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
                    height: scene.height
                    theme: root.theme
                    scene: UI.entry({
                        id: entryCode,
                        taskTitle: taskTitle,
                        process: process,
                        loginLabel: loginLabel,
                        day: day,
                        hours: totalHours,
                        overtimeHours: overtimeHours,
                        status: status,
                        description: description,
                        canEdit: canEdit,
                        canApprove: canApprove,
                        selectable: canApprove,
                        selected: selected,
                        disabled: workHoursController.busy
                    }, width, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
                    onEvent: action => {
                        if (action.type === "select")
                            workHoursController.toggle_timesheet_selected(index);
                        else if (action.type === "edit")
                            entryEditor.openForEdit(timesheetModel.get(index));
                        else if (action.type === "delete")
                            workHoursController.remove_entry(entryCode);
                        else if (action.type === "approval")
                            workHoursController.set_approved(entryCode, status !== "approved");
                    }
                }

                Label {
                    anchors.centerIn: parent
                    visible: timesheetModel.count() === 0 && !workHoursController.busy
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
