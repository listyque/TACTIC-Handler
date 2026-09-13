import QtQuick
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme

    implicitWidth: modeRow.implicitWidth
    implicitHeight: root.theme.controlHeight

    RowLayout {
        id: modeRow
        anchors.fill: parent
        spacing: 4

        Controls.SegmentedButton {
            id: viewModeSwitcher
            objectName: "taskBrowserViewSwitcher"
            Layout.preferredWidth: implicitWidth
            Layout.preferredHeight: root.theme.controlHeight
            theme: root.theme
            iconOnly: true
            segmentWidth: 34
            minimumSegmentWidth: 34
            model: [
                {"label": "Task table", "icon": "table_view",
                 "value": "list"},
                {"label": "Gantt view", "icon": "gantt",
                 "value": "gantt"}
            ]
            currentValue: tasksController.viewMode
            onActivated: value => tasksController.set_view_mode(value)
        }

        Controls.CompactIconButton {
            objectName: "taskCalendarButton"
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28
            theme: root.theme
            iconName: "calendar_month"
            toolTip: qsTr("Open task calendar")
            onClicked: tasksController.open_calendar()
        }
    }
}
