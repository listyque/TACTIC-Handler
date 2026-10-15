import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import "controls" as Controls

Item {
    id: root
    required property var theme
    required property var controller
    required property var notifications
    implicitWidth: 390
    implicitHeight: stack.implicitHeight

    Column {
        id: stack
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        spacing: 8

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
                height: content.implicitHeight + 24
                Accessible.role: Accessible.Button
                Accessible.name: notice.message
                Accessible.description: notice.detail
                Accessible.ignored: notice.action.length === 0
                Accessible.onPressAction: {
                    if (notice.action.length > 0)
                        root.controller.activate(notice.index)
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
                    radius: 14
                    color: root.theme.panelRaised
                    border.width: 1
                    border.color: root.theme.outline
                }
                Controls.ActivationHandler {
                    anchors.fill: parent
                    enabled: notice.action.length > 0
                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onActivated: root.controller.activate(notice.index)
                }
                ColumnLayout {
                    id: content
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 14
                    anchors.rightMargin: 8
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Controls.ItemPreview {
                            objectName: "notificationAvatar"
                            Layout.preferredWidth: 46
                            Layout.preferredHeight: 46
                            theme: root.theme
                            previewSize: 46
                            source: notice.previewUrl
                            fallbackText: notice.avatarText.slice(0, 2).toUpperCase()
                            fallbackIcon: notice.sourceIcon.length > 0
                                ? notice.sourceIcon
                                : notice.kind === "error" ? "priority-high"
                                : notice.kind === "warning" ? "warning"
                                : notice.kind === "progress" ? "sync"
                                : notice.kind === "complete" ? "check-circle"
                                : "info"
                            accent: notice.avatarColor.length > 0
                                ? notice.avatarColor
                                : notice.kind === "error" ? root.theme.error
                                : notice.kind === "warning" ? root.theme.yellow
                                : notice.kind === "complete" ? root.theme.green
                                : root.theme.action
                            round: notice.sourceType === "message"
                                || notice.sourceType === "activity"
                            outlined: true
                            animateAppearance: false
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3
                            Label {
                                objectName: "notificationSource"
                                Layout.fillWidth: true
                                visible: notice.sourceType.length > 0
                                text: notice.sourceType === "message"
                                    ? qsTr("Message")
                                        + (notice.sourceTitle.length > 0
                                            ? " · " + notice.sourceTitle : "")
                                    : notice.sourceType === "activity"
                                        ? qsTr("Activity Feed")
                                            + (notice.sourceTitle.length > 0
                                                ? " · " + notice.sourceTitle : "")
                                        : notice.sourceTitle
                                color: root.theme.action
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                objectName: "notificationMessage"
                                Layout.fillWidth: true
                                text: notice.sourceType.length > 0
                                    ? notice.message : qsTr(notice.message)
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                wrapMode: Text.WordWrap
                            }
                            Label {
                                objectName: "notificationDetail"
                                Layout.fillWidth: true
                                visible: notice.detail.length > 0
                                text: notice.detail
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                wrapMode: Text.Wrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                            }
                            ProgressBar {
                                Layout.fillWidth: true
                                visible: notice.kind === "progress"
                                indeterminate: notice.progress < 0
                                value: notice.progress
                                Material.accent: root.theme.action
                            }
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            visible: notice.dismissible
                            onClicked: root.controller.dismiss(notice.index)
                        }
                    }
                    Controls.Button {
                        objectName: "notificationReplyButton"
                        Layout.alignment: Qt.AlignRight
                        theme: root.theme
                        text: qsTr("Reply")
                        visible: notice.sourceType === "message"
                            && notice.actionData.length > 0
                            && !notice.replyOpen
                        onClicked: root.controller.begin_reply(notice.index)
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        visible: notice.replyOpen
                        spacing: 6
                        Controls.TextField {
                            id: replyField
                            objectName: "notificationReplyField"
                            Layout.fillWidth: true
                            theme: root.theme
                            placeholderText: qsTr("Write a reply")
                            enabled: !notice.replySending
                            onAccepted: root.controller.send_reply(
                                notice.index, text)
                            Keys.onEscapePressed: root.controller.cancel_reply(
                                notice.index)
                            onVisibleChanged: {
                                if (visible)
                                    Qt.callLater(() => forceActiveFocus())
                            }
                        }
                        Controls.Button {
                            objectName: "notificationSendReplyButton"
                            theme: root.theme
                            text: qsTr("Send")
                            enabled: !notice.replySending
                                && replyField.text.trim().length > 0
                            onClicked: root.controller.send_reply(
                                notice.index, replyField.text)
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            toolTip: qsTr("Cancel")
                            enabled: !notice.replySending
                            onClicked: root.controller.cancel_reply(notice.index)
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: notice.replyError.length > 0
                        text: notice.replyError === "Unable to send message"
                            ? qsTr("Unable to send message")
                            : notice.replyError
                        color: root.theme.error
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }
}
