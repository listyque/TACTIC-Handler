import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller
    required property var attachmentModel

    implicitWidth: controls.implicitWidth
    implicitHeight: controls.implicitHeight

    function openDrafts() {
        draftsPopup.toggleBelowItem(draftButton, true, 6)
    }

    FileDialog {
        id: fileDialog
        title: qsTr("Attach files")
        fileMode: FileDialog.OpenFiles
        onAccepted: root.controller.add_files(selectedFiles)
    }

    RowLayout {
        id: controls
        anchors.fill: parent
        spacing: 4

        Controls.CompactIconButton {
            theme: root.theme
            iconName: "attach-file"
            toolTip: qsTr("Choose files")
            enabled: !root.controller.busy
            onClicked: fileDialog.open()
        }
        Controls.CompactIconButton {
            theme: root.theme
            iconName: "content-paste"
            toolTip: qsTr("Attach image from clipboard")
            enabled: !root.controller.busy
            onClicked: root.controller.add_clipboard_image()
        }
        Controls.CompactIconButton {
            id: draftButton
            visible: root.controller.count > 0
            theme: root.theme
            iconName: "inventory-2"
            badgeCount: root.controller.count
            toolTip: qsTr("Attachments to send")
            onPressed: draftsPopup.rememberSourceOpen()
            onClicked: root.openDrafts()
        }
        Controls.CompactIconButton {
            visible: root.controller.count > 0
            theme: root.theme
            iconName: root.controller.busy ? "close" : "delete-sweep"
            toolTip: root.controller.busy
                ? qsTr("Cancel attachment upload") : qsTr("Clear attachments")
            onClicked: {
                if (root.controller.busy)
                    root.controller.cancel()
                else
                    root.controller.clear()
            }
        }
    }

    Controls.Popup {
        id: draftsPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(340, Math.max(
            250, (parent ? parent.width : root.width) - 24
        ))
        height: Math.min(300, Math.max(
            150, (parent ? parent.height : root.height) - 30
        ))
        padding: 10

        contentItem: ColumnLayout {
            spacing: 7
            Label {
                Layout.fillWidth: true
                text: qsTr("ATTACHMENTS TO SEND")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 2
                model: root.attachmentModel
                ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }

                delegate: Item {
                    required property int index
                    required property string title
                    required property string size
                    required property string status
                    width: ListView.view.width
                    height: 42

                    Controls.ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        cornerRadius: 11
                        railVisible: false
                        separatorVisible: false
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 9
                        anchors.rightMargin: 5
                        spacing: 7
                        Controls.MaterialIcon {
                            name: "description"
                            size: 16
                            color: status === "failed"
                                ? root.theme.error : root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            text: title
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            elide: Text.ElideMiddle
                        }
                        Label {
                            text: size
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            enabled: !root.controller.busy
                            onClicked: root.controller.remove(index)
                        }
                    }
                }
            }
        }
    }
}
