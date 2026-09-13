import QtQuick
import QtQuick.Controls
import "." as Controls

Item {
    id: root

    required property var theme
    property string title: ""
    property bool current: false
    property bool closable: false
    property bool dirty: false
    property bool hovered: false
    property bool pressed: false
    property bool indicatorVisible: true
    property bool animateSelection: true
    readonly property real labelImplicitWidth: tabText.implicitWidth

    signal closeRequested()

    function burst(x, y) {
        tabRipple.burst(x, y)
    }

    Rectangle {
        anchors.fill: parent
        color: root.current ? root.theme.action : root.theme.primaryText
        opacity: root.pressed ? 0.12 : root.hovered ? 0.08 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: root.pressed
                    ? root.theme.clickMotionFast
                    : root.theme.hoverMotionFast
                easing.type: Easing.OutCubic
            }
        }
    }

    Controls.MaterialRipple {
        id: tabRipple
        theme: root.theme
        shapeRadius: 0
        color: root.current
            ? Qt.rgba(root.theme.action.r, root.theme.action.g,
                root.theme.action.b, 0.28)
            : root.theme.rippleStrong
    }

    Rectangle {
        objectName: "workspaceTabSelectionIndicator"
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        width: root.current && root.indicatorVisible ? parent.width - 24 : 0
        height: 3
        radius: 1.5
        color: root.theme.action
        opacity: root.current && root.indicatorVisible ? 1 : 0
        Behavior on width {
            enabled: root.animateSelection
                && !root.theme.suppressTransientMotion
            NumberAnimation {
                duration: root.theme.clickMotionSlow
                easing.type: Easing.OutCubic
            }
        }
        Behavior on opacity {
            enabled: root.animateSelection
                && !root.theme.suppressTransientMotion
            NumberAnimation { duration: root.theme.clickMotionFast }
        }
    }

    Label {
        id: tabText
        objectName: "workspaceTabSelectionLabel"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: -1
        width: parent.width - (root.closable ? 58 : 24)
        text: root.title
        color: root.current ? root.theme.action : root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pixelSize: 14
        font.weight: Font.Medium
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        Behavior on color {
            enabled: root.animateSelection
                && !root.theme.suppressTransientMotion
            ColorAnimation { duration: root.theme.clickMotionFast }
        }
    }

    Rectangle {
        visible: root.dirty
        anchors.left: parent.left
        anchors.leftMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        width: 6
        height: 6
        radius: 3
        color: root.theme.yellow
    }

    Item {
        visible: root.closable
        opacity: root.current || root.hovered ? 1 : 0.58
        anchors.right: parent.right
        anchors.rightMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        width: 32
        height: 32
        Behavior on opacity {
            enabled: root.animateSelection
                && !root.theme.suppressTransientMotion
            NumberAnimation { duration: root.theme.hoverMotionFast }
        }

        Rectangle {
            id: closeCircle
            anchors.centerIn: parent
            width: 28
            height: 28
            radius: 14
            color: "transparent"
            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                color: root.current ? root.theme.action : root.theme.primaryText
                opacity: closeMouse.pressed ? 0.12
                    : closeMouse.containsMouse ? 0.08 : 0
                Behavior on opacity {
                    NumberAnimation {
                        duration: closeMouse.pressed
                            ? root.theme.clickMotionFast
                            : root.theme.hoverMotionFast
                        easing.type: Easing.OutCubic
                    }
                }
            }
            Controls.MaterialIcon {
                anchors.centerIn: parent
                name: "close"
                size: 16
                color: root.current ? root.theme.action : root.theme.secondaryText
            }
            Controls.MaterialRipple {
                id: closeRipple
                theme: root.theme
                shapeRadius: 14
                color: root.theme.rippleStrong
            }
        }
        MouseArea {
            id: closeMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onPressed: mouse => closeRipple.burst(
                mouse.x - closeCircle.x, mouse.y - closeCircle.y
            )
            onClicked: root.closeRequested()
            Controls.ToolTip {
                theme: root.theme
                visible: closeMouse.containsMouse && !root.theme.suppressToolTips
                delay: 500
                text: qsTr("Close tab")
            }
        }
    }
}
