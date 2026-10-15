import QtQuick
import "controls" as Controls

Rectangle {
    id: root
    objectName: "ganttProgressHandle"

    required property var theme
    required property var controller
    required property string taskCode
    required property int progress
    required property real barWidth
    required property bool rowHovered
    required property bool scheduled
    required property bool progressSupported
    property bool editing: false
    property int editProgress: progress
    readonly property int displayProgress: editing ? editProgress : progress

    visible: progressSupported && scheduled && barWidth >= 36
        && (rowHovered || progressPointer.pressed)
    x: Math.max(18, Math.min(
        barWidth - 18, barWidth * displayProgress / 100
    )) - width / 2
    anchors.verticalCenter: parent.verticalCenter
    width: 18
    height: 22
    radius: 6
    color: theme.surfaceContainerHighest
    border.width: 1
    border.color: theme.primaryText

    Row {
        anchors.centerIn: parent
        spacing: 3
        Repeater {
            model: 2
            Rectangle {
                width: 2
                height: 9
                radius: 1
                color: root.theme.primaryText
            }
        }
    }

    onProgressChanged: {
        if (!editing)
            editProgress = progress
    }

    MouseArea {
        id: progressPointer
        anchors.fill: parent
        anchors.margins: -2
        cursorShape: Qt.SizeHorCursor
        preventStealing: true

        onPressed: function(mouse) {
            root.editProgress = root.progress
            root.editing = true
            mouse.accepted = true
        }
        onPositionChanged: function(mouse) {
            if (!pressed)
                return
            const mapped = mapToItem(root.parent, mouse.x, mouse.y)
            root.editProgress = Math.max(0, Math.min(100, Math.round(
                mapped.x / root.barWidth * 100
            )))
        }
        onReleased: {
            root.editing = false
            if (root.editProgress !== root.progress)
                root.controller.stage_gantt_progress(
                    root.taskCode, root.editProgress
                )
        }
        onCanceled: {
            root.editing = false
            root.editProgress = root.progress
        }
    }

    Controls.ToolTip {
        theme: root.theme
        visible: progressPointer.pressed
        text: qsTr("Progress ") + root.editProgress + "%"
    }
}
