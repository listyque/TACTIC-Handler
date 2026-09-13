import QtQuick
import QtQuick.Window

Window {
    id: root
    required property var theme
    required property var controller
    required property var notifications

    width: 420
    height: Math.max(1, notificationStack.implicitHeight)
    visible: root.controller.count > 0
    color: "transparent"
    flags: Qt.FramelessWindowHint
        | Qt.Tool
        | Qt.WindowStaysOnTopHint
        | Qt.WindowDoesNotAcceptFocus
        | Qt.NoDropShadowWindowHint
    modality: Qt.NonModal
    transientParent: null

    function placeAtBottomRight() {
        if (!root.screen)
            return
        const availableWidth = root.screen.desktopAvailableWidth
        const availableHeight = root.screen.desktopAvailableHeight
        if (availableWidth <= 0 || availableHeight <= 0)
            return
        root.x = root.screen.virtualX
            + availableWidth - root.width - 18
        root.y = root.screen.virtualY
            + availableHeight - root.height - 18
    }

    onVisibleChanged: {
        if (visible)
            placeAtBottomRight()
    }
    onHeightChanged: {
        if (visible)
            placeAtBottomRight()
    }
    onWidthChanged: {
        if (visible)
            placeAtBottomRight()
    }
    onScreenChanged: placeAtBottomRight()
    Component.onCompleted: placeAtBottomRight()

    Connections {
        target: root.controller
        function onChanged() { root.placeAtBottomRight() }
    }

    NotificationStack {
        id: notificationStack
        objectName: "mainNotificationStack"
        anchors.fill: parent
        theme: root.theme
        controller: root.controller
        notifications: root.notifications
    }
}
