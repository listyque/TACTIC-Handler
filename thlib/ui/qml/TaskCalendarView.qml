import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property bool compact: width < 500 || height < 430
    readonly property real cellGap: compact ? 2 : 4
    readonly property real cellWidth: Math.max(
        1, (calendarGrid.width - cellGap * 6) / 7
    )
    readonly property real cellHeight: Math.max(
        1, (calendarGrid.height - cellGap * 5) / 6
    )

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.compact ? 6 : 10
        spacing: root.compact ? 5 : 8

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            spacing: 4

            Controls.CompactIconButton {
                theme: root.theme
                iconName: "chevron_left"
                toolTip: qsTr("Previous month")
                onClicked: tasksController.change_calendar_month(-1)
            }
            Label {
                Layout.fillWidth: true
                text: tasksController.calendarTitle
                color: root.theme.primaryText
                horizontalAlignment: Text.AlignHCenter
                font.family: root.theme.fontFamily
                font.pixelSize: root.compact ? 12 : 14
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "chevron_right"
                toolTip: qsTr("Next month")
                onClicked: tasksController.change_calendar_month(1)
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "calendar_today"
                toolTip: qsTr("Today")
                onClicked: tasksController.calendar_today()
            }
            Controls.CompactIconButton {
                visible: tasksController.selectedDay.length > 0
                theme: root.theme
                iconName: "filter_alt_off"
                toolTip: qsTr("Clear selected day")
                onClicked: tasksController.select_calendar_day("")
            }
        }

        Row {
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            spacing: root.cellGap

            Repeater {
                model: ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
                delegate: Label {
                    required property string modelData
                    width: root.cellWidth
                    height: parent.height
                    text: modelData
                    color: root.theme.secondaryText
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.DemiBold
                }
            }
        }

        Grid {
            id: calendarGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 7
            rows: 6
            columnSpacing: root.cellGap
            rowSpacing: root.cellGap

            Repeater {
                model: taskCalendarModel

                delegate: Rectangle {
                    id: dayCell

                    required property int index
                    required property string date
                    required property int day
                    required property bool inMonth
                    required property bool today
                    required property int taskCount
                    required property int overdueCount
                    required property var tasks
                    required property int milestoneCount
                    required property var milestones
                    required property bool selected

                    readonly property bool weekend: index % 7 >= 5
                    readonly property var firstMilestone:
                        milestoneCount > 0 && milestones && milestones.length > 0
                            ? milestones[0]
                            : ({"label": "", "completion": 0, "taskCount": 0})
                    readonly property int visibleTaskLimit: root.compact
                        ? 0 : Math.max(1, Math.min(3, Math.floor(
                            (height - (dayCell.milestoneCount > 0 ? 54 : 30)) / 22
                        )))

                    width: root.cellWidth
                    height: root.cellHeight
                    radius: root.theme.itemRadius
                    color: selected
                        ? root.theme.secondaryContainer
                        : dayMouse.containsMouse
                            ? root.theme.surfaceContainerHighest
                            : weekend
                                ? root.theme.surfaceContainerLow
                                : root.theme.surfaceContainer
                    opacity: inMonth ? 1 : 0.55

                    Behavior on color {
                        ColorAnimation { duration: root.theme.hoverMotionFast }
                    }

                    MouseArea {
                        id: dayMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: tasksController.select_calendar_day(
                            dayCell.date
                        )
                    }

                    Rectangle {
                        visible: dayCell.today
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.margins: 5
                        width: 23
                        height: 23
                        radius: width / 2
                        color: root.theme.action
                    }

                    Label {
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.margins: 5
                        width: 23
                        height: 23
                        text: dayCell.day
                        color: dayCell.today
                            ? root.theme.selectedText : root.theme.primaryText
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: dayCell.today ? Font.DemiBold : Font.Normal
                    }

                    Rectangle {
                        id: milestoneBand
                        visible: dayCell.milestoneCount > 0
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.topMargin: 31
                        anchors.leftMargin: 5
                        anchors.rightMargin: 5
                        height: root.compact ? 8 : 20
                        radius: root.theme.fieldRadius
                        color: root.theme.tertiaryContainer
                        border.width: 1
                        border.color: root.theme.tertiary

                        RowLayout {
                            visible: !root.compact
                            anchors.fill: parent
                            anchors.leftMargin: 5
                            anchors.rightMargin: 5
                            spacing: 4
                            Controls.MaterialIcon {
                                name: "milestone"
                                size: 11
                                color: root.theme.tertiary
                            }
                            Label {
                                Layout.fillWidth: true
                                text: dayCell.firstMilestone.label
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                text: dayCell.firstMilestone.taskCount > 0
                                    ? dayCell.firstMilestone.completion + "%" : ""
                                color: root.theme.tertiary
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.Bold
                            }
                        }
                        Controls.ToolTip {
                            theme: root.theme
                            visible: milestoneHover.hovered
                            text: dayCell.firstMilestone.label
                                + (dayCell.firstMilestone.taskCount > 0
                                    ? "  ·  "
                                        + dayCell.firstMilestone.completion + "%"
                                    : "")
                        }
                        HoverHandler { id: milestoneHover }
                    }

                    Label {
                        visible: dayCell.taskCount > 0
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: 7
                        text: dayCell.taskCount
                        color: dayCell.overdueCount > 0
                            ? root.theme.error : root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.DemiBold
                    }

                    Column {
                        z: 1
                        visible: dayCell.visibleTaskLimit > 0
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.topMargin: dayCell.milestoneCount > 0 ? 55 : 31
                        anchors.leftMargin: 5
                        anchors.rightMargin: 5
                        spacing: 3

                        Repeater {
                            model: Math.min(
                                dayCell.visibleTaskLimit,
                                dayCell.tasks ? dayCell.tasks.length : 0
                            )

                            delegate: Rectangle {
                                id: taskMarker
                                required property int index
                                property var task: dayCell.tasks[index]
                                width: parent.width
                                height: 19
                                radius: root.theme.fieldRadius
                                color: taskMarker.task.selected
                                    ? root.theme.secondaryContainer
                                    : markerMouse.containsMouse
                                    ? root.theme.rowHover : root.theme.row

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 5
                                    anchors.rightMargin: 5
                                    spacing: 4

                                    Rectangle {
                                        Layout.preferredWidth: 6
                                        Layout.preferredHeight: 6
                                        radius: 3
                                        color: taskMarker.task.statusColor
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: taskMarker.task.parentTitle
                                            + " · " + taskMarker.task.processLabel
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        elide: Text.ElideRight
                                    }
                                }

                                MouseArea {
                                    id: markerMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: mouse => {
                                        mouse.accepted = true
                                        tasksController.activate_calendar_task(
                                            taskMarker.task.taskCode,
                                            taskMarker.task.parentKey,
                                            taskMarker.task.process
                                        )
                                    }
                                }
                                Controls.ToolTip {
                                    theme: root.theme
                                    visible: markerMouse.containsMouse
                                    text: taskMarker.task.parentTitle
                                        + "\n" + taskMarker.task.processLabel
                                        + " · " + taskMarker.task.status
                                        + "\n" + taskMarker.task.assignedLabel
                                }
                            }
                        }

                        Label {
                            visible: dayCell.taskCount > dayCell.visibleTaskLimit
                            width: parent.width
                            height: 14
                            text: qsTr("+") + (dayCell.taskCount - dayCell.visibleTaskLimit)
                                + qsTr(" more")
                            color: root.theme.secondaryText
                            horizontalAlignment: Text.AlignRight
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }
                    }

                    Flow {
                        visible: root.compact && dayCell.taskCount > 0
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 6
                        height: 8
                        spacing: 3

                        Repeater {
                            model: Math.min(
                                5, dayCell.tasks ? dayCell.tasks.length : 0
                            )
                            delegate: Rectangle {
                                required property int index
                                width: 6
                                height: 6
                                radius: 3
                                color: dayCell.tasks[index].statusColor
                            }
                        }
                    }

                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            spacing: 6

            Controls.MaterialIcon {
                name: "calendar_month"
                size: 13
                color: root.theme.secondaryText
            }
            Label {
                Layout.fillWidth: true
                text: tasksController.selectedDay.length
                    ? qsTr("Task Browser filtered by ")
                        + tasksController.selectedDay
                    : qsTr("Select a day to filter Task Browser")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                elide: Text.ElideRight
            }
        }
    }
}
