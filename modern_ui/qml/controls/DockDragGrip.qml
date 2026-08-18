import QtQuick

Item {
    id: root
    required property var theme
    property string toolTip: ""
    property real dragThreshold: 6

    signal pressed()
    signal clicked()
    signal dragStarted(real pressX, real pressY)
    signal dragMoved(real pointerX, real pointerY)
    signal dragFinished()
    signal dragCanceled()

    readonly property bool dragActive: pointerArea.dragging
    implicitWidth: 30
    implicitHeight: 34

    Column {
        anchors.centerIn: parent
        spacing: 4

        Repeater {
            model: 3

            Row {
                spacing: 5

                Repeater {
                    model: 2

                    Rectangle {
                        width: 3
                        height: 3
                        radius: 1.5
                        antialiasing: true
                        color: root.enabled
                            ? root.theme.secondaryText
                            : root.theme.disabledText
                        opacity: pointerArea.pressed ? 1
                            : pointerArea.containsMouse ? 0.9 : 0.72
                        Behavior on opacity {
                            NumberAnimation {
                                duration: root.theme.motionFast
                                easing.type: Easing.OutCubic
                            }
                        }
                    }
                }
            }
        }
    }

    MouseArea {
        id: pointerArea
        anchors.fill: parent
        hoverEnabled: true
        preventStealing: true
        cursorShape: root.enabled
            ? (dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor)
            : Qt.ArrowCursor
        property bool dragging: false
        property real pressX: 0
        property real pressY: 0

        onPressed: mouse => {
            pressX = mouse.x
            pressY = mouse.y
            dragging = false
            root.pressed()
        }
        onPositionChanged: mouse => {
            if (!pressed)
                return
            if (!dragging && Math.hypot(
                    mouse.x - pressX, mouse.y - pressY
                ) >= root.dragThreshold) {
                dragging = true
                root.dragStarted(pressX, pressY)
            }
            if (dragging)
                root.dragMoved(mouse.x, mouse.y)
        }
        onReleased: mouse => {
            const wasDragging = dragging
            if (wasDragging)
                root.dragFinished()
            dragging = false
            if (!wasDragging && mouse.x >= 0 && mouse.x <= width
                    && mouse.y >= 0 && mouse.y <= height)
                root.clicked()
        }
        onCanceled: {
            if (dragging)
                root.dragCanceled()
            dragging = false
        }
    }

    Md3ToolTip {
        theme: root.theme
        visible: pointerArea.containsMouse && root.toolTip.length > 0
            && !root.theme.suppressToolTips
        delay: 500
        text: qsTr(root.toolTip)
    }
}
