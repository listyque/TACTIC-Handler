import QtQuick
import "." as Controls

Item {
    id: root
    required property var theme
    property string toolTip: ""
    property real dragThreshold: 6

    signal pressed()
    signal clicked()
    signal contextRequested(real pointerX, real pointerY)
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
                                duration: pointerArea.pressed
                                    ? root.theme.clickMotionFast
                                    : root.theme.hoverMotionFast
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
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        preventStealing: true
        cursorShape: root.enabled
            ? (dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor)
            : Qt.ArrowCursor
        property bool dragging: false
        property real pressX: 0
        property real pressY: 0
        property int pressButton: Qt.NoButton

        onPressed: mouse => {
            pressButton = mouse.button
            if (mouse.button === Qt.RightButton) {
                root.contextRequested(mouse.x, mouse.y)
                return
            }
            pressX = mouse.x
            pressY = mouse.y
            dragging = false
            root.pressed()
        }
        onPositionChanged: mouse => {
            if (!pressed || pressButton !== Qt.LeftButton)
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
            if (pressButton !== Qt.LeftButton) {
                pressButton = Qt.NoButton
                dragging = false
                return
            }
            const wasDragging = dragging
            if (wasDragging)
                root.dragFinished()
            dragging = false
            pressButton = Qt.NoButton
            if (!wasDragging && mouse.x >= 0 && mouse.x <= width
                    && mouse.y >= 0 && mouse.y <= height)
                root.clicked()
        }
        onCanceled: {
            if (dragging)
                root.dragCanceled()
            dragging = false
            pressButton = Qt.NoButton
        }
    }

    Controls.ToolTip {
        theme: root.theme
        visible: pointerArea.containsMouse && root.toolTip.length > 0
            && !root.theme.suppressToolTips
        delay: 500
        text: qsTr(root.toolTip)
    }
}
