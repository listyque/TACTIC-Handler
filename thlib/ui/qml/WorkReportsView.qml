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
            return
        initialized = true
        workHoursController.load_report()
    }

    function localizedValueLabel(value) {
        const text = String(value || "")
        if (workHoursController.selectedReport === "bid_actual" && text === "Planned")
            return qsTr("Planned")
        if (workHoursController.selectedReport === "bid_actual" && text === "Logged")
            return qsTr("Logged")
        if (workHoursController.selectedReport === "approval" && text === "Approved")
            return qsTr("Approved")
        if (workHoursController.selectedReport === "approval" && text === "Pending")
            return qsTr("Pending")
        if (workHoursController.selectedReport === "my_hours" && text === "Unscheduled")
            return qsTr("Unscheduled")
        if ((workHoursController.selectedReport === "team"
                || workHoursController.selectedReport === "labor_cost")
                && text === "Unassigned")
            return qsTr("Unassigned")
        if (workHoursController.selectedReport === "process" && text === "Unspecified")
            return qsTr("Unspecified")
        return text
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Controls.DockWorkspaceFooter {
            theme: root.theme
            topDividerVisible: false
            roundBottomRight: false
            Layout.preferredWidth: Math.min(230, Math.max(170, root.width * 0.28))
            Layout.fillHeight: true
            color: root.theme.surfaceContainerLow

            ListView {
                id: reportTypeList
                anchors.fill: parent
                anchors.margins: 7
                spacing: 4
                clip: true
                model: workReportModel
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                    flickableTarget: reportTypeList
                }
                delegate: Rectangle {
                    required property string key
                    required property string title
                    required property string description
                    required property string icon
                    required property string permission
                    required property bool selected
                    readonly property bool allowed:
                        permission === "user"
                        || permission === "supervisor"
                            && workHoursController.canManage
                        || permission === "finance"
                            && workHoursController.canViewCosts
                    width: ListView.view.width
                    height: 54
                    radius: root.theme.itemRadius
                    color: selected
                        ? root.theme.primaryContainer
                        : reportMouse.containsMouse
                            ? root.theme.rowHover : "transparent"
                    opacity: allowed ? 1 : 0.45

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8
                        Controls.MaterialIcon {
                            name: icon
                            size: 18
                            color: selected
                                ? root.theme.action : root.theme.secondaryText
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Label {
                                Layout.fillWidth: true
                                text: root.reportTitles[key] || title
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: root.reportDescriptions[key] || description
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.micro
                                elide: Text.ElideRight
                            }
                        }
                    }
                    MouseArea {
                        id: reportMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: parent.allowed
                        cursorShape: enabled
                            ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onClicked: workHoursController.select_report(key)
                    }
                }
            }
        }

        Controls.DockWorkspaceFooter {
            theme: root.theme
            topDividerVisible: false
            roundBottomLeft: false
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: root.theme.workspace

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 9
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 34
                    Label {
                        Layout.fillWidth: true
                        text: root.reportTitles[
                            workHoursController.selectedReport] || ""
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: workHoursController.weekStart + " — "
                            + workHoursController.weekEnd
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                    RefreshIconButton {
                        theme: root.theme
                        toolTip: qsTr("Refresh report")
                        onClicked: workHoursController.refresh_report()
                    }
                }

                Label {
                    visible: workHoursController.reportMessage.length > 0
                    Layout.fillWidth: true
                    text: workHoursController.reportMessage
                        === "No authorized hourly wages are configured."
                        ? qsTr("No authorized hourly wages are configured.") : workHoursController.reportMessage
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }

                Controls.SmoothListView {
                    theme: root.theme
                    id: reportValuesList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 6
                    clip: true
                    model: workReportValueModel
                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: reportValuesList
                    }
                    delegate: Rectangle {
                        required property string label
                        required property string valueLabel
                        required property real share
                        width: ListView.view.width
                        height: 52
                        radius: root.theme.itemRadius
                        color: root.theme.surfaceContainerLow

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 10
                            Label {
                                Layout.preferredWidth: Math.min(
                                    180, parent.width * 0.34
                                )
                                text: root.localizedValueLabel(label)
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                elide: Text.ElideRight
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 6
                                radius: 3
                                color: root.theme.surfaceContainerHighest
                                Rectangle {
                                    width: parent.width * Math.max(
                                        0, Math.min(1, share)
                                    )
                                    height: parent.height
                                    radius: parent.radius
                                    color: root.theme.action
                                }
                            }
                            Label {
                                Layout.preferredWidth: 70
                                text: String(valueLabel)
                                    .replace(/ h$/, qsTr(" h"))
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignRight
                            }
                        }
                    }
                }
            }
        }
    }

    Component.onCompleted: ensureLoaded()
    onPresentationActiveChanged: ensureLoaded()
}
