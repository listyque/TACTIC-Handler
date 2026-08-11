import QtQuick
import QtQuick.Controls

Item {
    id: root

    required property var theme
    property bool activated: false

    function activateWhenAllowed() {
        if (!workHoursController.canViewCosts || activated)
            return
        activated = true
        workHoursController.select_report("labor_cost")
    }

    Loader {
        anchors.fill: parent
        active: workHoursController.canViewCosts
        sourceComponent: WorkReportsView { theme: root.theme }
    }

    Label {
        anchors.centerIn: parent
        visible: !workHoursController.busy
            && !workHoursController.canViewCosts
        width: Math.min(320, parent.width - 32)
        text: qsTr("Cost reports require financial reporting permission.")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pixelSize: 10
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
    }

    Md3BusyIndicator {
        uiTheme: root.theme
        anchors.centerIn: parent
        running: workHoursController.busy
        visible: running
    }

    Connections {
        target: workHoursController
        function onStateChanged() { root.activateWhenAllowed() }
    }

    Component.onCompleted: {
        workHoursController.refresh_timesheet()
        activateWhenAllowed()
    }
}
