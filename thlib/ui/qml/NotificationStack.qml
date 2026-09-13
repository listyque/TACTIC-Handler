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
                RowLayout {
                    id: content
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 14
                    anchors.rightMargin: 8
                    spacing: 10
                    Rectangle {
                        Layout.preferredWidth: 46
                        Layout.preferredHeight: 46
                        radius: notice.sourceType === "message"
                                || notice.sourceType === "activity"
                            ? width / 2 : root.theme.itemRadius
                        color: notice.avatarColor.length > 0
                            ? notice.avatarColor
                            : root.theme.blend(
                                root.theme.action,
                                root.theme.surfaceContainerHigh,
                                0.18)
                        border.width: 1
                        border.color: root.theme.outlineVariant
                        clip: true

                        Image {
                            id: sourcePreview
                            anchors.fill: parent
                            source: notice.previewUrl
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            cache: true
                            visible: status === Image.Ready
                        }
                        Label {
                            objectName: "notificationAvatarText"
                            anchors.centerIn: parent
                            visible: !sourcePreview.visible
                                && notice.avatarText.length > 0
                            text: notice.avatarText.slice(0, 2).toUpperCase()
                            color: root.theme.selectedText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.Bold
                        }
                        Controls.MaterialIcon {
                            objectName: "notificationSourceIcon"
                            anchors.centerIn: parent
                            visible: !sourcePreview.visible
                                && notice.avatarText.length === 0
                            name: notice.sourceIcon.length > 0
                                ? notice.sourceIcon
                                : notice.kind === "error" ? "priority-high"
                                : notice.kind === "warning" ? "warning"
                                : notice.kind === "progress" ? "sync"
                                : notice.kind === "complete" ? "check-circle"
                                : "info"
                            size: notice.sourceType.length > 0 ? 20 : 19
                            color: notice.kind === "error" ? root.theme.error
                                : notice.kind === "warning" ? root.theme.yellow
                                : notice.kind === "complete" ? root.theme.green
                                : root.theme.action
                        }
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
                                            ? " · "
                                                + notice.sourceTitle
                                            : "")
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
            }
        }
    }
}
