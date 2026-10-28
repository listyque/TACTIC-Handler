import QtQuick
import "../tactic_frame/controls/tabs/workspace.ui.mjs" as Workspace

Item {
    id: root
    required property var recordsProvider
    property string identity: ""
    property string label: ""
    property bool selected: false
    property bool vertical: false
    signal command(var action)
    signal keyboardInput
    activeFocusOnTab: selected
    Accessible.role: Accessible.PageTab
    Accessible.name: label
    Accessible.selected: selected
    Keys.onPressed: event => {
        root.keyboardInput();
        const keys = {
            [Qt.Key_Left]: "ArrowLeft",
            [Qt.Key_Right]: "ArrowRight",
            [Qt.Key_Up]: "ArrowUp",
            [Qt.Key_Down]: "ArrowDown",
            [Qt.Key_Home]: "Home",
            [Qt.Key_End]: "End",
            [Qt.Key_Delete]: "Delete"
        };
        if (!keys[event.key])
            return;
        const action = Workspace.key(root.recordsProvider(), root.identity, keys[event.key], root.vertical, !!(event.modifiers & Qt.ControlModifier) && !!(event.modifiers & Qt.ShiftModifier));
        if (action) {
            event.accepted = true;
            root.command(action);
        }
    }
}
