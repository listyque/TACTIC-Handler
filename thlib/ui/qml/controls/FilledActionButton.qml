import QtQuick
import QtQuick.Controls
import "." as Controls

Item {
    id: root

    required property var theme
    property string iconName: ""
    property string text: ""
    property string toolTip: ""
    property bool compact: false
    property real horizontalPadding: 15
    readonly property real surfaceInset: 2
    readonly property bool hasLabel: !compact && text.length > 0
    readonly property bool lastActivationWasTouch:
        buttonTap.lastActivationWasTouch
    readonly property double lastActivationAt: buttonTap.lastActivationAt
    readonly property real desiredContentWidth:
        (iconName.length > 0 ? 18 : 0)
        + (hasLabel && iconName.length > 0 ? 7 : 0)
        + (hasLabel ? buttonLabel.implicitWidth : 0)
    readonly property real cornerRadius: theme.itemRadius
    signal pressed()
    signal clicked()

    implicitWidth: compact
        ? theme.controlHeight
        : Math.max(
            theme.controlHeight,
            desiredContentWidth + horizontalPadding * 2 + surfaceInset * 2
        )
    implicitHeight: theme.controlHeight

    Rectangle {
        id: buttonSurface
        anchors.fill: parent
        anchors.margins: root.surfaceInset
        clip: true
        // Filled toolbar actions are rounded squares, not pill buttons.
        // Keep the geometry aligned with the existing filled Add action.
        radius: root.cornerRadius
        color: !root.enabled
            ? root.theme.surfaceContainerHigh
            : buttonTap.pressed
                ? Qt.darker(root.theme.action, 1.15)
                : buttonHover.hovered
                    ? Qt.lighter(root.theme.action, 1.08)
                    : root.theme.action

        Behavior on color {
            ColorAnimation {
                duration: buttonTap.pressed
                    ? root.theme.clickMotionFast
                    : buttonHover.hovered
                        ? root.theme.hoverMotionFast : root.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }

        Item {
            id: buttonContent
            objectName: "filledActionContent"
            anchors.centerIn: parent
            width: Math.min(
                root.desiredContentWidth,
                Math.max(0, parent.width - root.horizontalPadding * 2)
            )
            height: Math.max(18, buttonLabel.implicitHeight)

            Controls.MaterialIcon {
                id: buttonIcon
                objectName: "filledActionIcon"
                visible: root.iconName.length > 0
                x: root.hasLabel ? 0 : (parent.width - width) / 2
                anchors.verticalCenter: parent.verticalCenter
                name: root.iconName
                size: 18
                color: root.enabled
                    ? root.theme.selectedText : root.theme.disabledText
            }
            Label {
                id: buttonLabel
                objectName: "filledActionLabel"
                visible: root.hasLabel
                x: root.iconName.length > 0 ? 25 : 0
                width: Math.max(0, parent.width - x)
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr(root.text)
                color: root.enabled
                    ? root.theme.selectedText : root.theme.disabledText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
        }

        Controls.MaterialRipple {
            id: buttonRipple
            theme: root.theme
            shapeRadius: buttonSurface.radius
            color: Qt.rgba(
                root.theme.selectedText.r,
                root.theme.selectedText.g,
                root.theme.selectedText.b,
                0.24
            )
        }
    }

    HoverHandler {
        id: buttonHover
        objectName: "filledActionCursorArea"
        cursorShape: Qt.PointingHandCursor
    }

    Controls.ActivationHandler {
        id: buttonTap
        enabled: root.enabled
        cursorShape: Qt.PointingHandCursor
        onPressedChanged: {
            if (!pressed)
                return
            buttonRipple.burst(
                point.position.x - buttonSurface.x,
                point.position.y - buttonSurface.y
            )
            root.pressed()
        }
        onActivated: root.clicked()
    }

    Controls.ToolTip {
        theme: root.theme
        visible: buttonHover.hovered
            && (root.toolTip.length > 0
                || (root.hasLabel && buttonLabel.truncated))
            && !root.theme.suppressToolTips
        delay: 500
        text: qsTr(root.toolTip.length > 0 ? root.toolTip : root.text)
    }
}
