import QtQuick
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/rows.ui.mjs" as UI
import "../../../tactic_frame/features/files/workspace/presentation.mjs" as Presentation

Item {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    required property var theme
    required property var row
    property bool selected: false
    property bool focused: false
    onFocusedChanged: if (focused)
        forceActiveFocus()
    property bool narrow: false
    property string localLabel: ""
    property string serverLabel: ""
    property string checkoutLabel: ""
    property var checkoutHolders: []
    property string currentUser: ""
    property var columns: []
    property var dragData: ({})
    property int leftPadding: 0
    signal selectedChangedByUser(bool checked)
    signal selectedByUser(int modifiers)
    signal activated
    signal menuRequested(var source, real x, real y)
    signal dragRequested
    readonly property var badges: Presentation.badges(row).concat(checkoutHolders.map(holder => ({
                label: holder.owner === currentUser ? (holder.mode === "exclusive" ? "Exclusive checkout by you" : "Checked out by you") : (holder.mode === "exclusive" ? "Exclusive checkout by another user" : "Checked out by another user"),
                icon: holder.mode === "exclusive" ? "lock" : "edit",
                tone: holder.owner === currentUser ? "action" : "other"
            })))
    implicitHeight: 34
    activeFocusOnTab: true
    Accessible.role: Accessible.ListItem
    Accessible.name: row.path
    Accessible.description: localLabel + "; " + serverLabel + "; " + checkoutLabel
    Accessible.selected: selected
    Accessible.onPressAction: root.selectedByUser(0)
    Drag.active: drag.active
    Drag.dragType: Drag.Automatic
    Drag.supportedActions: Qt.CopyAction | Qt.MoveAction
    Drag.mimeData: root.dragData
    Drag.hotSpot.x: 20
    Drag.hotSpot.y: height / 2
    HoverHandler {
        id: hover
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.fileRow({
            row: root.row,
            columns: root.columns,
            selected: root.selected,
            hovered: hover.hovered,
            pressed: activation.pressed,
            leftPadding: root.leftPadding,
            checkoutLabel: root.checkoutLabel,
            localLabel: root.localLabel,
            serverLabel: root.serverLabel,
            checkoutHolders: root.checkoutHolders,
            currentUser: root.currentUser
        }, width, root.language)
        onEvent: action => {
            if (action.type === "check")
                root.selectedChangedByUser(action.value);
        }
    }
    Controls.ActivationHandler {
        id: activation
        repeatPointerTaps: true
        onActivated: (modifiers, x, y) => {
            root.forceActiveFocus();
            root.selectedByUser(modifiers);
        }
        onDoubleActivated: root.activated()
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        onClicked: mouse => root.menuRequested(root, mouse.x, mouse.y)
    }
    DragHandler {
        id: drag
        target: null
        acceptedButtons: Qt.LeftButton
        onActiveChanged: if (active)
            root.dragRequested()
    }
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape && drag.active) {
            root.Drag.cancel();
            event.accepted = true;
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            root.activated();
            event.accepted = true;
        } else if (event.key === Qt.Key_Space) {
            root.selectedByUser(Qt.ControlModifier);
            event.accepted = true;
        } else if (event.key === Qt.Key_Menu || (event.key === Qt.Key_F10 && (event.modifiers & Qt.ShiftModifier))) {
            root.menuRequested(root, 8, height);
            event.accepted = true;
        }
    }
    Controls.ToolTip {
        theme: root.theme
        visible: hover.hovered && !root.theme.suppressToolTips
        delay: 500
        text: root.row.path + "\n" + root.badges.map(badge => qsTr(badge.label)).join(" · ") + "\n" + root.checkoutLabel
    }
}
