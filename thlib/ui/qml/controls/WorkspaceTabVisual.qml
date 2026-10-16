import QtQuick
import "." as Controls
import "../tactic_frame" as Frame
import "../tactic_frame/controls/tabs/workspace.ui.mjs" as Workspace

Item {
    id: root
    required property var theme
    property string title: ""
    property string iconName: ""
    property bool current: false
    property bool closable: false
    property bool dirty: false
    property bool hovered: false
    property bool pressed: false
    property bool indicatorVisible: true
    property bool animateSelection: true
    readonly property real labelImplicitWidth: Math.ceil(titleMetrics.advanceWidth)
    signal closeRequested
    function burst(x, y) {
        tabRipple.burst(x, y);
    }
    TextMetrics {
        id: titleMetrics
        text: root.title
        font: Qt.font({
            family: root.theme.fontFamily,
            pixelSize: 14,
            weight: Font.Medium
        })
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        interactive: false
        scene: Workspace.tab(root.width, root.height, {
            title: root.title,
            icon: root.iconName,
            current: root.current,
            closable: root.closable,
            dirty: root.dirty,
            indicatorVisible: root.indicatorVisible
        }, {
            animateSelection: root.animateSelection,
            hovered: root.hovered,
            pressed: root.pressed,
            closeHovered: closeMouse.containsMouse,
            closePressed: closeMouse.pressed
        })
    }
    Controls.MaterialRipple {
        id: tabRipple
        theme: root.theme
        shapeRadius: 0
        color: root.current ? Qt.rgba(root.theme.action.r, root.theme.action.g, root.theme.action.b, 0.28) : root.theme.rippleStrong
    }
    Item {
        visible: root.closable
        anchors.right: parent.right
        anchors.rightMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        width: 32
        height: 32
        Controls.MaterialRipple {
            id: closeRipple
            theme: root.theme
            shapeRadius: 14
            color: root.theme.rippleStrong
        }
        MouseArea {
            id: closeMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onPressed: mouse => closeRipple.burst(mouse.x - 2, mouse.y - 2)
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
