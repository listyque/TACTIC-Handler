import QtQuick
import Qt5Compat.GraphicalEffects
import "features/activity" as Activity
import "tactic_frame/features/activity/toast.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    required property var notifications
    implicitWidth: UI.metrics.width
    implicitHeight: stack.implicitHeight

    Column {
        id: stack
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        spacing: UI.metrics.gap

        Repeater {
            model: root.notifications
            delegate: Item {
                id: notice
                objectName: "notificationCard"
                required property int index
                required property string kind
                required property string message
                required property string detail
                required property real progress
                required property bool dismissible
                required property string action
                required property string actionData
                required property string sourceType
                required property string sourceTitle
                required property string previewUrl
                required property string avatarText
                required property string avatarColor
                required property string sourceIcon
                required property bool replyOpen
                required property bool replySending
                required property string replyError
                width: stack.width
                height: presenter.implicitHeight
                property real slideOffset: root.theme.popupAnimationsEnabled ? 24 : 0
                opacity: root.theme.popupAnimationsEnabled ? 0 : 1
                transform: Translate {
                    y: notice.slideOffset
                }
                Component.onCompleted: {
                    slideOffset = 0;
                    opacity = 1;
                }
                Behavior on slideOffset {
                    enabled: root.theme.popupAnimationsEnabled
                    NumberAnimation {
                        duration: 80
                        easing.type: Easing.OutCubic
                    }
                }
                Behavior on opacity {
                    enabled: root.theme.popupAnimationsEnabled
                    NumberAnimation {
                        duration: 70
                        easing.type: Easing.OutCubic
                    }
                }
                Accessible.role: Accessible.Button
                Accessible.name: notice.message
                Accessible.description: notice.detail
                Accessible.ignored: notice.action.length === 0
                Accessible.onPressAction: {
                    if (notice.action.length > 0)
                        root.controller.activate(notice.index);
                }

                DropShadow {
                    anchors.fill: surface
                    source: surface
                    horizontalOffset: 2
                    verticalOffset: 5
                    radius: 12
                    samples: 25
                    color: root.theme.popupShadow
                    transparentBorder: true
                }
                Rectangle {
                    id: surface
                    anchors.fill: parent
                    radius: presenter.scene.radius
                    color: root.theme[presenter.scene.background]
                    border.width: 1
                    border.color: root.theme.outline
                }
                Activity.NotificationToast {
                    id: presenter
                    anchors.fill: parent
                    theme: root.theme
                    record: ({
                            kind: notice.kind,
                            message: notice.message,
                            detail: notice.detail,
                            progress: notice.progress,
                            dismissible: notice.dismissible,
                            action: notice.action,
                            actionData: notice.actionData,
                            sourceType: notice.sourceType,
                            sourceTitle: notice.sourceTitle,
                            previewUrl: notice.previewUrl,
                            avatarText: notice.avatarText,
                            avatarColor: notice.avatarColor,
                            sourceIcon: notice.sourceIcon,
                            replyOpen: notice.replyOpen,
                            replySending: notice.replySending,
                            replyError: notice.replyError
                        })
                    onRequested: action => {
                        if (action.type === "activate")
                            root.controller.activate(notice.index);
                        else if (action.type === "dismiss")
                            root.controller.dismiss(notice.index);
                        else if (action.type === "reply")
                            root.controller.begin_reply(notice.index);
                        else if (action.type === "cancel")
                            root.controller.cancel_reply(notice.index);
                        else if (action.type === "send" && !notice.replySending && action.text.trim().length)
                            root.controller.send_reply(notice.index, action.text);
                    }
                }
            }
        }
    }
}
