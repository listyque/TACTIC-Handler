import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/workhours/reports.ui.mjs" as UI

Item {
    id: root

    required property var theme
    property bool presentationActive: parent ? parent.visible : visible
    property bool initialized: false

    readonly property var reportTitles: ({
            "my_hours": qsTr("My Work Hours"),
            "bid_actual": qsTr("Bid vs Actual"),
            "approval": qsTr("Approval"),
            "team": qsTr("Team Hours"),
            "process": qsTr("Process Hours"),
            "labor_cost": qsTr("Labor Cost")
        })
    readonly property var reportDescriptions: ({
            "my_hours": qsTr("Daily logged time"),
            "bid_actual": qsTr("Planned and approved hours"),
            "approval": qsTr("Approved and pending time"),
            "team": qsTr("Hours by user"),
            "process": qsTr("Hours by process"),
            "labor_cost": qsTr("Authorized wage-based cost")
        })

    function ensureLoaded() {
        if (!presentationActive || initialized)
            return;
        initialized = true;
        workHoursController.load_report();
    }

    function localizedValueLabel(value) {
        const text = String(value || "");
        if (workHoursController.selectedReport === "bid_actual" && text === "Planned")
            return qsTr("Planned");
        if (workHoursController.selectedReport === "bid_actual" && text === "Logged")
            return qsTr("Logged");
        if (workHoursController.selectedReport === "approval" && text === "Approved")
            return qsTr("Approved");
        if (workHoursController.selectedReport === "approval" && text === "Pending")
            return qsTr("Pending");
        if (workHoursController.selectedReport === "my_hours" && text === "Unscheduled")
            return qsTr("Unscheduled");
        if ((workHoursController.selectedReport === "team" || workHoursController.selectedReport === "labor_cost") && text === "Unassigned")
            return qsTr("Unassigned");
        if (workHoursController.selectedReport === "process" && text === "Unspecified")
            return qsTr("Unspecified");
        return text;
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    readonly property var presentation: ({
            report: workHoursController.selectedReport,
            busy: workHoursController.busy,
            count: workReportValueModel.count(),
            options: workReportModel.records(),
            weekStart: workHoursController.weekStart,
            weekEnd: workHoursController.weekEnd,
            error: workHoursController.error,
            message: workHoursController.reportMessage,
            canManage: workHoursController.canManage,
            canViewCosts: workHoursController.canViewCosts
        })
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.presentation, width, height, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
        models: ({
                reports: workReportModel,
                values: workReportValueModel
            })
        describeRow: (list, record) => list.source === "reports" ? UI.descriptor(record, root.presentation, Math.max(0, list.width - 16), (typeof localizationController !== "undefined" ? localizationController.current_language : "en")) : UI.valueRow(Object.assign({}, record, {
                label: root.localizedValueLabel(record.label)
            }), Math.max(0, list.width - 16), (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
        onEvent: action => {
            if (action.type === "report")
                workHoursController.select_report(action.value);
            else
                workHoursController.refresh_report();
        }
    }

    Component.onCompleted: ensureLoaded()
    onPresentationActiveChanged: ensureLoaded()
}
