import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root

    required property var theme

    implicitWidth: 104
    implicitHeight: 32
    Layout.minimumWidth: implicitWidth
    Layout.maximumWidth: implicitWidth
    Layout.minimumHeight: implicitHeight
    Layout.maximumHeight: implicitHeight
    radius: theme.itemRadius
    color: theme.surfaceContainerHigh

    RowLayout {
        anchors.centerIn: parent
        spacing: 2

        CompactIconButton {
            Layout.preferredWidth: 32
            Layout.preferredHeight: 28
            Layout.minimumWidth: 32
            Layout.maximumWidth: 32
            theme: root.theme
            iconName: "table-view"
            toolTip: qsTr("Task table")
            elevated: tasksController.viewMode === "list"
            onClicked: tasksController.set_view_mode("list")
        }
        CompactIconButton {
            Layout.preferredWidth: 32
            Layout.preferredHeight: 28
            Layout.minimumWidth: 32
            Layout.maximumWidth: 32
            theme: root.theme
            iconName: "gantt"
            toolTip: qsTr("Gantt view")
            elevated: tasksController.viewMode === "gantt"
            onClicked: tasksController.set_view_mode("gantt")
        }
        CompactIconButton {
            Layout.preferredWidth: 32
            Layout.preferredHeight: 28
            Layout.minimumWidth: 32
            Layout.maximumWidth: 32
            theme: root.theme
            iconName: "calendar_month"
            toolTip: qsTr("Open task calendar")
            onClicked: tasksController.open_calendar()
        }
    }
}
