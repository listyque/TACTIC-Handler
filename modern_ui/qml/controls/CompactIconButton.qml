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
    property int badgeCount: 0
    property color backgroundColor: elevated
        ? theme.surfaceContainerHigh : "transparent"
    signal pressed()
    signal clicked()
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
    MaterialIcon { anchors.centerIn: parent; name: root.iconName; size: root.iconSize; color: root.iconColor }
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
            font.pixelSize: 8
            font.weight: Font.Bold
        }
    }
    MouseArea {
        id: mouse
        objectName: "compactIconButtonCursorArea"
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.enabled
            ? Qt.PointingHandCursor : Qt.ArrowCursor
        onPressed: mouse => {
            ripple.burst(mouse.x - buttonBackground.x, mouse.y - buttonBackground.y)
            root.pressed()
        }
        onClicked: root.clicked()
    }
    Md3ToolTip {
        theme: root.theme
        visible: mouse.containsMouse && root.toolTip.length > 0 && !root.theme.suppressToolTips
        delay: 500
        text: qsTr(root.toolTip)
    }
}
