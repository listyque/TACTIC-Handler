import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects

Item {
    id: root
    property var theme
    property string iconName: ""
    property color iconColor: theme.primaryText
    property real iconSize: 17
    property string toolTip: ""
    property bool round: false
    property bool elevated: false
    property bool dragHandle: false
    property real dragThreshold: 6
    property int badgeCount: 0
    property color backgroundColor: elevated
        ? theme.surfaceContainerHigh : "transparent"
    signal pressed()
    signal clicked()
    signal dragStarted(real pressX, real pressY)
    signal dragMoved(real pointerX, real pointerY)
    signal dragFinished()
    signal dragCanceled()
    readonly property bool dragActive: mouse.dragging
    implicitWidth: 28
    implicitHeight: 28

    DropShadow {
        anchors.fill: buttonBackground
        source: buttonBackground
        visible: root.elevated
        horizontalOffset: 0
        verticalOffset: 3
        radius: 8
        samples: 17
        color: root.theme.dialogShadow
        transparentBorder: true
    }
    Rectangle {
        id: buttonBackground
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height) - 2
        height: width
        radius: root.round ? width / 2 : root.theme.iconButtonRadius
        color: root.backgroundColor
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            color: root.iconColor
            opacity: mouse.pressed ? 0.12
                : mouse.containsMouse ? 0.08 : 0
            Behavior on opacity {
                NumberAnimation {
                    duration: mouse.containsMouse
                        ? root.theme.motionFast : root.theme.motionMedium
                    easing.type: Easing.OutCubic
                }
            }
        }
        MaterialRipple {
            id: ripple
            color: Qt.rgba(
                root.iconColor.r,
                root.iconColor.g,
                root.iconColor.b,
                0.28
            )
            shapeRadius: buttonBackground.radius
        }
    }
    MaterialIcon {
        anchors.centerIn: parent
        name: root.iconName
        size: root.iconSize
        color: root.enabled ? root.iconColor : root.theme.disabledText
    }
    Rectangle {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: -1
        anchors.topMargin: -1
        visible: root.badgeCount > 0
        implicitWidth: Math.max(16, badgeLabel.implicitWidth + 7)
        implicitHeight: 16
        radius: 8
        color: root.theme.error
        border.width: 2
        border.color: root.theme.surface
        Label {
            id: badgeLabel
            anchors.centerIn: parent
            text: root.badgeCount > 99 ? "99+" : String(root.badgeCount)
            color: root.theme.selectedText
            font.family: root.theme.fontFamily
            font.pointSize: Typography.caption
            font.weight: Font.Bold
        }
    }
    MouseArea {
        id: mouse
        objectName: "compactIconButtonCursorArea"
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.enabled
            ? (root.dragHandle
                ? (dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor)
                : Qt.PointingHandCursor)
            : Qt.ArrowCursor
        property bool dragging: false
        property real pressX: 0
        property real pressY: 0
        onPressed: mouse => {
            ripple.burst(mouse.x - buttonBackground.x, mouse.y - buttonBackground.y)
            pressX = mouse.x
            pressY = mouse.y
            dragging = false
            root.pressed()
        }
        onPositionChanged: mouse => {
            if (!root.dragHandle || !pressed)
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
            if (!root.dragHandle)
                return
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
        onClicked: {
            if (!root.dragHandle)
                root.clicked()
        }
    }
    Md3ToolTip {
        theme: root.theme
        visible: mouse.containsMouse && root.toolTip.length > 0 && !root.theme.suppressToolTips
        delay: 500
        text: qsTr(root.toolTip)
    }
}
