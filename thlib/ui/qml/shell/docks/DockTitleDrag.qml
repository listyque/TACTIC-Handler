import QtQuick
import QtQuick.Window

// Floating title movement never changes the dock tree; the grip owns docking.
MouseArea {
    id: root
    required property var panel
    property bool moving: false
    property real beforeX: 0
    property real beforeY: 0
    property real pressX: 0
    property real pressY: 0
    enabled: panel.dockArea === "floating" && !panel.resizing && !panel.dockDragging
    acceptedButtons: Qt.LeftButton
    preventStealing: true
    cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
    function cancel() {
        if (!moving)
            return;
        panel.localX = beforeX;
        panel.localY = beforeY;
        moving = false;
    }
    onPressed: mouse => {
        const point = mapToItem(panel.host, mouse.x, mouse.y);
        beforeX = panel.localX;
        beforeY = panel.localY;
        pressX = point.x;
        pressY = point.y;
        moving = true;
    }
    onPositionChanged: mouse => {
        if (!pressed || !moving)
            return;
        const point = mapToItem(panel.host, mouse.x, mouse.y);
        panel.localX = Math.max(0, Math.min(panel.host.width - panel.width, beforeX + point.x - pressX));
        panel.localY = Math.max(0, Math.min(panel.host.height - panel.height, beforeY + point.y - pressY));
    }
    onReleased: {
        if (!moving)
            return;
        moving = false;
        dockModel.set_geometry(panel.panelId, panel.localX / panel.host.width, panel.localY / panel.host.height, panel.width / panel.host.width, panel.height / panel.host.height);
    }
    onCanceled: cancel()
    Shortcut {
        sequence: "Escape"
        enabled: root.moving
        context: Qt.WindowShortcut
        onActivated: root.cancel()
    }
    Connections {
        target: root.Window.window
        function onActiveChanged() {
            if (!target.active)
                root.cancel();
        }
    }
}
