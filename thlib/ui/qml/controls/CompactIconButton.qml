import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects
import "." as Controls

Item {
    id: root
    property var theme
    property string iconName: ""
    property color iconColor: theme.primaryText
    property real iconSize: 17
    property bool forceSolidIcon: false
    property string toolTip: ""
    property bool round: false
    property bool elevated: false
    property bool dragHandle: false
    property real dragThreshold: 6
    property int duplicateWindow: 180
    property int badgeCount: 0
    property color badgeColor: theme.error
    property color backgroundColor: elevated
        ? theme.surfaceContainerHigh : "transparent"
    signal pressed()
    signal clicked()
    signal clickedWithModifiers(int modifiers)
    signal dragStarted(real pressX, real pressY)
    signal dragMoved(real pointerX, real pointerY)
    signal dragFinished()
    signal dragCanceled()
    readonly property bool dragActive: dragArea.dragging
    readonly property bool pointerPressed: activation.pressed || dragArea.pressed
    readonly property bool pointerHovered: pointerHover.hovered
    readonly property bool lastActivationWasTouch:
        activation.lastActivationWasTouch
    readonly property double lastActivationAt: activation.lastActivationAt
    readonly property real interactionOpacity: pointerPressed
        ? 0.12 : pointerHovered ? 0.08 : 0
    readonly property color interactionBackgroundColor:
        interactionOpacity > 0
            ? theme.overlay(
                backgroundColor, iconColor, interactionOpacity
            )
            : backgroundColor
    function activate(modifiers) {
        root.clicked()
        root.clickedWithModifiers(modifiers)
    }

    implicitWidth: 28
    implicitHeight: 28

    Loader {
        anchors.fill: buttonBackground
        active: root.elevated
        sourceComponent: DropShadow {
            anchors.fill: parent
            source: buttonBackground
            horizontalOffset: 0
            verticalOffset: 3
            radius: 8
            samples: 17
            color: root.theme.dialogShadow
            transparentBorder: true
        }
    }
    Rectangle {
        id: buttonBackground
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height) - 2
        height: width
        radius: root.round ? width / 2 : root.theme.iconButtonRadius
        color: root.interactionBackgroundColor
        Behavior on color {
            ColorAnimation {
                duration: root.pointerPressed
                    ? root.theme.clickMotionFast
                    : root.theme.hoverMotionFast
                easing.type: Easing.OutCubic
            }
        }
        Controls.MaterialRipple {
            id: ripple
            theme: root.theme
            color: Qt.rgba(
                root.iconColor.r,
                root.iconColor.g,
                root.iconColor.b,
                0.28
            )
            shapeRadius: buttonBackground.radius
        }
    }
    Controls.MaterialIcon {
        anchors.centerIn: parent
        visible: root.iconName.length > 0
        name: root.iconName
        size: root.iconSize
        forceSolid: root.forceSolidIcon
        color: root.enabled ? root.iconColor : root.theme.disabledText
    }
    Loader {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: -1
        anchors.topMargin: -1
        active: root.badgeCount > 0
        sourceComponent: Rectangle {
            implicitWidth: Math.max(16, badgeLabel.implicitWidth + 7)
            implicitHeight: 16
            radius: 8
            color: root.badgeColor
            border.width: 2
            border.color: root.theme.surface
            Label {
                id: badgeLabel
                anchors.centerIn: parent
                text: root.badgeCount > 99
                    ? "99+" : String(root.badgeCount)
                color: root.theme.selectedText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.caption
                font.weight: Font.Bold
            }
        }
    }
    HoverHandler {
        id: pointerHover
        objectName: "compactIconButtonHoverHandler"
        cursorShape: Qt.PointingHandCursor
    }

    Controls.ActivationHandler {
        id: activation
        objectName: "compactIconButtonCursorArea"
        enabled: root.enabled && !root.dragHandle
        duplicateWindow: root.duplicateWindow
        cursorShape: Qt.PointingHandCursor
        onPressedChanged: {
            if (!pressed)
                return
            ripple.burst(
                point.position.x - buttonBackground.x,
                point.position.y - buttonBackground.y
            )
            root.pressed()
        }
        onActivated: modifiers => root.activate(modifiers)
    }

    MouseArea {
        id: dragArea
        objectName: "compactIconButtonDragArea"
        anchors.fill: parent
        enabled: root.enabled && root.dragHandle
        hoverEnabled: false
        cursorShape: Qt.PointingHandCursor
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
                root.activate(mouse.modifiers)
        }
        onCanceled: {
            if (dragging)
                root.dragCanceled()
            dragging = false
        }
    }
    Loader {
        active: root.pointerHovered
            && root.toolTip.length > 0
            && !root.theme.suppressToolTips
        sourceComponent: Controls.ToolTip {
            theme: root.theme
            visible: true
            delay: 500
            text: qsTr(root.toolTip)
        }
    }
}
