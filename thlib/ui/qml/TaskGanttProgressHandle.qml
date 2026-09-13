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
    property real edgeResizeRadius: 12
    property bool editing: false
    property int editProgress: progress
    readonly property int displayProgress: editing ? editProgress : progress

    visible: progressSupported && scheduled && barWidth >= 36
        && (rowHovered || progressPointer.pressed)
    x: Math.max(7, Math.min(
        barWidth - 7, barWidth * displayProgress / 100
    )) - width / 2
    anchors.verticalCenter: parent.verticalCenter
    width: 10
    height: 10
    radius: 5
    color: theme.primaryText
    border.width: 2
    border.color: theme.surfaceContainer

    onProgressChanged: {
        if (!editing)
            editProgress = progress
    }

    MouseArea {
        id: progressPointer
        anchors.fill: parent
        anchors.margins: -5
        cursorShape: Qt.SizeHorCursor
        preventStealing: true

        onPressed: function(mouse) {
            const mapped = mapToItem(root.parent, mouse.x, mouse.y)
            if (mapped.x <= root.edgeResizeRadius
                    || mapped.x >= root.barWidth - root.edgeResizeRadius) {
                mouse.accepted = false
                return
            }
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
