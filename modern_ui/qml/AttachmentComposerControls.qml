import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    required property var controller
    required property var attachmentModel

    implicitWidth: controls.implicitWidth
    implicitHeight: controls.implicitHeight

    function openDrafts() {
        const overlay = Overlay.overlay
        const point = draftButton.mapToItem(overlay, 0, 0)
        draftsPopup.x = Math.max(6, Math.min(
            overlay.width - draftsPopup.width - 6, point.x
        ))
        const above = point.y - draftsPopup.height - 6
        const below = point.y + draftButton.height + 6
        draftsPopup.y = above >= 6
            ? above
            : Math.min(overlay.height - draftsPopup.height - 6, below)
        draftsPopup.open()
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

        CompactIconButton {
            theme: root.theme
            iconName: "attach-file"
            toolTip: qsTr("Choose files")
            enabled: !root.controller.busy
            onClicked: fileDialog.open()
        }
        CompactIconButton {
            theme: root.theme
            iconName: "content-paste"
            toolTip: qsTr("Attach image from clipboard")
            enabled: !root.controller.busy
            onClicked: root.controller.add_clipboard_image()
        }
        CompactIconButton {
            id: draftButton
            visible: root.controller.count > 0
            theme: root.theme
            iconName: "inventory-2"
            badgeCount: root.controller.count
            toolTip: qsTr("Attachments to send")
            onClicked: root.openDrafts()
        }
        CompactIconButton {
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

    Md3Popup {
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
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 2
                model: root.attachmentModel
                ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

                delegate: Item {
                    required property int index
                    required property string title
                    required property string size
                    required property string status
                    width: ListView.view.width
                    height: 42

                    ItemSurface {
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
                        MaterialIcon {
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
                            font.pixelSize: 9
                            elide: Text.ElideMiddle
                        }
                        Label {
                            text: size
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 8
                        }
                        CompactIconButton {
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
