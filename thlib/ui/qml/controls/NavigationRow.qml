import QtQuick
import "." as Controls
import "../tactic_frame" as Frame
import "../tactic_frame/controls/lists/tree.ui.mjs" as Tree

Item {
    id: root
    required property var theme
    property string rowType: "link"
    property string title: ""
    property string glyph: "link"
    property int depth: 0
    property string accent: ""
    property bool expanded: false
    property bool selected: false
    property int badge: 0
    property bool dimmed: false
    property bool interactive: true
    readonly property bool isSection: rowType === "section"
    readonly property bool isSeparator: rowType === "separator"
    readonly property color itemAccent: accent.length ? accent : theme.action
    readonly property var scene: Tree.navigationRow(width, {
        kind: rowType,
        title: title,
        icon: glyph,
        depth: depth,
        accent: accent,
        expanded: expanded,
        badge: badge
    }, {
        selected: selected,
        hovered: hover.hovered,
        pressed: activation.pressed,
        radius: theme.itemRadius
    })
    signal activated

    implicitHeight: scene.height
    opacity: dimmed ? 0.5 : 1
    activeFocusOnTab: interactive
    Accessible.role: Accessible.Button
    Accessible.name: title
    Accessible.selected: selected
    Accessible.ignored: isSeparator && !interactive
    Keys.onSpacePressed: if (interactive)
        activated()
    Keys.onReturnPressed: if (interactive)
        activated()
    Keys.onEnterPressed: if (interactive)
        activated()

    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        interactive: false
    }
    Item {
        id: hit
        x: 12
        y: 4
        width: Math.max(0, root.width - 24)
        height: Math.max(0, root.height - 8)
        visible: !root.isSeparator
        Controls.MaterialRipple {
            id: ripple
            theme: root.theme
            shapeRadius: root.theme.itemRadius
            color: root.selected ? Qt.rgba(root.theme.action.r, root.theme.action.g, root.theme.action.b, 0.28) : root.theme.rippleStrong
        }
        HoverHandler {
            id: hover
            enabled: root.interactive
            cursorShape: Qt.PointingHandCursor
        }
        Controls.ActivationHandler {
            id: activation
            enabled: root.interactive
            onPressedChanged: if (pressed)
                ripple.burst(point.position.x, point.position.y)
            onActivated: {
                root.forceActiveFocus(Qt.MouseFocusReason);
                root.activated();
            }
        }
    }
}
