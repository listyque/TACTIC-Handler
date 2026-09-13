import QtQuick
import QtQuick.Controls
import "controls" as Controls

Item {
    id: root

    required property var theme
    property bool presentationActive:
        parent ? parent.visible : visible
    property bool activated: false
    property bool initialized: false

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    function activateWhenAllowed() {
        if (!presentationActive
                || activated)
            return
        if (!initialized) {
            initialized = true
            workHoursController.load_timesheet()
        }
        if (!workHoursController.canViewCosts)
            return
        activated = true
        workHoursController.select_report("labor_cost")
    }

    Loader {
        anchors.fill: parent
        active: root.activated && workHoursController.canViewCosts
        sourceComponent: WorkReportsView {
            theme: root.theme
            presentationActive: root.presentationActive
        }
    }

    Label {
        anchors.centerIn: parent
        visible: !workHoursController.busy
            && !workHoursController.canViewCosts
        width: Math.min(320, parent.width - 32)
        text: qsTr("Cost reports require financial reporting permission.")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.body
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
    }

    Controls.BusyIndicator {
        uiTheme: root.theme
        anchors.centerIn: parent
        running: workHoursController.busy
        visible: running
    }

    Connections {
        target: workHoursController
        enabled: root.presentationActive
        function onStateChanged() { root.activateWhenAllowed() }
    }

    Component.onCompleted: {
        activateWhenAllowed()
    }
    onPresentationActiveChanged: activateWhenAllowed()
}
