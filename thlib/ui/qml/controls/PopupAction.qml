import QtQuick
import QtQuick.Controls as QtControls

// Interaction primitive for custom popup rows and cells. Visuals remain with
// the owning feature, while pointer, focus, keyboard, and cursor behavior stay
// identical across native popup windows.
QtControls.AbstractButton {
    id: root

    property int _pendingActivationKey: 0

    hoverEnabled: true
    focusPolicy: Qt.StrongFocus

    Keys.priority: Keys.BeforeItem
    Keys.onPressed: event => {
        if (event.key !== Qt.Key_Return
                && event.key !== Qt.Key_Enter
                && event.key !== Qt.Key_Space)
            return
        root._pendingActivationKey = event.key
        event.accepted = true
    }
    Keys.onReleased: event => {
        if (event.key !== root._pendingActivationKey)
            return
        root._pendingActivationKey = 0
        event.accepted = true
        Qt.callLater(root.click)
    }

    HoverHandler {
        cursorShape: root.enabled
            ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}
