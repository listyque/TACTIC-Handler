import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "features/activity" as Activity
import "tactic_frame" as Frame
import "tactic_frame/features/activity/notifications.ui.mjs" as UI

Item {
    id: root
    required property var theme
    readonly property var geometry: UI.layout(width, height)
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }
    Rectangle {
        id: panel
        objectName: "notificationsPanel"
        x: root.geometry.panel.x
        y: root.geometry.panel.y
        width: root.geometry.panel.width
        height: root.geometry.panel.height
        radius: root.theme.surfaceRadius
        color: root.theme.panel
        border.width: 1
        border.color: root.theme.outlineVariant
    }
    Frame.FrameView {
        objectName: "notificationsToolbar"
        theme: root.theme
        x: root.geometry.header.x
        y: root.geometry.header.y
        width: root.geometry.header.width
        height: root.geometry.header.height
        scene: UI.header({
            count: notificationHistoryModel.count(),
            group: notificationController.historyGroup,
            repository: true
        }, width, root.language)
        onEvent: action => {
            if (action.type === "clear")
                notificationController.clear_history();
            if (action.type === "group")
                notificationController.set_history_group(action.value);
        }
    }
    Controls.SmoothListView {
        id: history
        objectName: "notificationHistoryList"
        theme: root.theme
        x: root.geometry.history.x
        y: root.geometry.history.y
        width: root.geometry.history.width
        height: root.geometry.history.height
        clip: true
        spacing: 6
        reuseItems: true
        model: notificationGroupedHistoryModel
        ScrollBar.vertical: Controls.ScrollBar {
            objectName: "notificationHistoryScrollBar"
            theme: root.theme
            flickableTarget: history
        }
        delegate: Activity.NotificationHistoryRow {
            required property string kind
            required property string group
            required property string message
            required property string detail
            required property string timestamp
            required property string timestampPretty
            required property string timestampFull
            width: root.geometry.rowWidth
            height: implicitHeight
            theme: root.theme
            record: ({
                    kind,
                    group,
                    message,
                    detail,
                    timestamp,
                    timestampPretty,
                    timestampFull
                })
        }
        Frame.FrameView {
            objectName: "notificationsEmptyState"
            anchors.fill: parent
            theme: root.theme
            visible: history.count === 0
            scene: visible ? UI.empty(width, height, root.language) : ({
                    nodes: []
                })
        }
    }
}
