import QtQuick
import QtQuick.Controls

Item {
    id: root

    required property var theme
    property string title: ""
    property bool current: false
    property bool closable: false
    property bool hovered: false
    property bool pressed: false
    property bool indicatorVisible: true
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
                duration: root.hovered ? 100 : 140
                easing.type: Easing.OutCubic
            }
        }
    }

    MaterialRipple {
        id: tabRipple
        shapeRadius: 0
        color: root.current
            ? Qt.rgba(root.theme.action.r, root.theme.action.g,
                root.theme.action.b, 0.28)
            : root.theme.dark ? "#52ffffff" : "#38000000"
    }

    Rectangle {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        width: root.current && root.indicatorVisible ? parent.width - 24 : 0
        height: 3
        radius: 1.5
        color: root.theme.action
        opacity: root.current && root.indicatorVisible ? 1 : 0
        Behavior on width {
            NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
        }
        Behavior on opacity { NumberAnimation { duration: 120 } }
    }

    Label {
        id: tabText
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
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    Item {
        visible: root.closable
        opacity: root.current || root.hovered ? 1 : 0.58
        anchors.right: parent.right
        anchors.rightMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        width: 32
        height: 32
        Behavior on opacity { NumberAnimation { duration: 120 } }

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
                        duration: closeMouse.containsMouse ? 100 : 140
                        easing.type: Easing.OutCubic
                    }
                }
            }
            MaterialIcon {
                anchors.centerIn: parent
                name: "close"
                size: 16
                color: root.current ? root.theme.action : root.theme.secondaryText
            }
            MaterialRipple {
                id: closeRipple
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
            Md3ToolTip {
                theme: root.theme
                visible: closeMouse.containsMouse && !root.theme.suppressToolTips
                delay: 500
                text: qsTr("Close search tab")
            }
        }
    }
}
