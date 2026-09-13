import QtQuick
import "controls" as Controls

Item {
    id: root

    required property var theme

    implicitWidth: surfaceSwitcher.implicitWidth
    implicitHeight: root.theme.controlHeight

    function activateSurface(value) {
        if (value === "workspace") {
            tasksController.open_workspace()
            return
        }
        tasksController.set_quick_view_mode(value)
        if (tasksController.workspaceSurface !== "quick")
            tasksController.open_quick_workspace()
    }

    Controls.SegmentedButton {
        id: surfaceSwitcher
        objectName: "quickTaskViewSwitcher"
        anchors.fill: parent
        theme: root.theme
        iconOnly: true
        segmentWidth: 34
        minimumSegmentWidth: 34
        model: [
            {"label": "Task cards", "icon": "grid_view",
             "value": "cards"},
            {"label": "Compact task list", "icon": "view_list",
             "value": "compact"},
            {"label": "Open task workspace", "icon": "dashboard_customize",
             "value": "workspace"}
        ]
        currentValue: tasksController.workspaceSurface === "browser"
            ? "workspace" : tasksController.quickViewMode
        onActivated: value => root.activateSurface(value)
    }
}
