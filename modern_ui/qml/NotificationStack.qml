import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

Item {
    id: root
    required property var theme
    implicitWidth: 390
    implicitHeight: stack.implicitHeight

    Column {
        id: stack
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        spacing: 8

        Repeater {
            model: notificationModel
            delegate: Item {
                id: notice
                required property int index
                required property string kind
                required property string message
                required property string detail
                required property real progress
                required property bool dismissible
                required property string action
                required property string actionData
                width: stack.width
                height: content.implicitHeight + 22

                DropShadow {
                    anchors.fill: surface
                    source: surface
                    horizontalOffset: 2
                    verticalOffset: 5
                    radius: 12
                    samples: 25
                    color: "#36000000"
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
                MouseArea {
                    anchors.fill: parent
                    enabled: notice.action.length > 0
                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onClicked: notificationController.activate(notice.index)
                }
                RowLayout {
                    id: content
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 14
                    anchors.rightMargin: 8
                    spacing: 10
                    MaterialIcon {
                        name: notice.kind === "error" ? "priority_high"
                            : notice.kind === "warning" ? "warning"
                            : notice.kind === "progress" ? "sync"
                            : notice.kind === "complete" ? "check_circle"
                            : "info"
                        size: 19
                        color: notice.kind === "error" ? root.theme.red
                            : notice.kind === "warning" ? root.theme.yellow
                            : notice.kind === "complete" ? root.theme.green
                            : root.theme.action
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Label {
                            Layout.fillWidth: true
                            text: notice.message
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 11
                            font.weight: Font.Medium
                            wrapMode: Text.WordWrap
                        }
                        Label {
                            Layout.fillWidth: true
                            visible: notice.detail.length > 0
                            text: notice.detail
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 10
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
                    CompactIconButton {
                        theme: root.theme
                        iconName: "close"
                        visible: notice.dismissible
                        onClicked: notificationController.dismiss(notice.index)
                    }
                }
            }
        }
    }
}
