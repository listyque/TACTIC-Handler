import QtQuick
import QtQuick.Controls as QtControls

// Interaction primitive for custom popup rows and cells. Visuals remain with
// the owning feature, while pointer, focus, keyboard, and cursor behavior stay
// identical across native popup windows.
QtControls.AbstractButton {
    id: root

    property int _pendingActivationKey: 0
    property var keyHandler: null

    onActiveFocusChanged: if (!activeFocus)
        _pendingActivationKey = 0
    onEnabledChanged: if (!enabled)
        _pendingActivationKey = 0
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus

    Keys.priority: Keys.BeforeItem
    Keys.onPressed: event => {
        if (event.isAutoRepeat && [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space].includes(event.key)) {
            event.accepted = true;
            return;
        }
        if (root.keyHandler && root.keyHandler(event.key)) {
            event.accepted = true;
            return;
        }
        if (event.key !== Qt.Key_Return && event.key !== Qt.Key_Enter && event.key !== Qt.Key_Space)
            return;
        root._pendingActivationKey = event.key;
        event.accepted = true;
    }
    Keys.onReleased: event => {
        if (event.key !== root._pendingActivationKey)
            return;
        event.accepted = true;
        if (event.isAutoRepeat)
            return;
        root._pendingActivationKey = 0;
        Qt.callLater(root.click);
    }

    HoverHandler {
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}
