import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Rectangle {
    id: root
    required property var theme
    required property var controller
    required property var attachmentModel
    property string emptyText: "Drop files here or choose them from disk"

    implicitHeight: content.implicitHeight + 16
    radius: 12
    color: dropArea.containsDrag
        ? root.theme.surfaceContainerHigh : root.theme.surfaceContainer
    border.width: 1
    border.color: dropArea.containsDrag
        ? root.theme.action : root.theme.outlineVariant

    FileDialog {
        id: fileDialog
        title: qsTr("Attach files")
        fileMode: FileDialog.OpenFiles
        onAccepted: root.controller.add_files(selectedFiles)
    }

    DropArea {
        id: dropArea
        anchors.fill: parent
        onDropped: drop => {
            if (drop.hasUrls) {
                root.controller.add_files(drop.urls)
                drop.acceptProposedAction()
            }
        }
    }

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            MaterialIcon {
                name: "attach_file"
                size: 16
                color: root.theme.action
            }
            Label {
                Layout.fillWidth: true
                text: root.controller.count > 0
                    ? root.controller.count + (root.controller.count === 1
                        ? qsTr(" attachment") : qsTr(" attachments"))
                    : root.emptyText
                color: root.controller.count > 0
                    ? root.theme.primaryText : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 9
                elide: Text.ElideRight
            }
            CompactIconButton {
                theme: root.theme
                iconName: "attach_file"
                toolTip: qsTr("Choose files")
                enabled: !root.controller.busy
                onClicked: fileDialog.open()
            }
            CompactIconButton {
                theme: root.theme
                iconName: "content_paste"
                toolTip: qsTr("Attach image from clipboard")
                enabled: !root.controller.busy
                onClicked: root.controller.add_clipboard_image()
            }
            CompactIconButton {
                theme: root.theme
                iconName: "delete_sweep"
                toolTip: qsTr("Clear attachments")
                visible: root.controller.count > 0
                enabled: !root.controller.busy
                onClicked: root.controller.clear()
            }
            CompactIconButton {
                theme: root.theme
                iconName: "close"
                toolTip: qsTr("Cancel upload")
                visible: root.controller.busy
                onClicked: root.controller.cancel()
            }
        }

        ResponsiveFlow {
            id: draftFlow
            Layout.fillWidth: true
            minimumCellWidth: 190
            preferredCellWidth: 280
            maximumColumns: 3
            spacing: 5
            visible: root.controller.count > 0
            Repeater {
                model: root.attachmentModel
                delegate: Rectangle {
                    required property int index
                    required property string title
                    required property string size
                    required property string status
                    width: draftFlow.cellWidth()
                    height: 34
                    radius: 15
                    color: root.theme.surfaceContainerHigh
                    border.width: 1
                    border.color: status === "failed"
                        ? root.theme.error : root.theme.outlineVariant
                    RowLayout {
                        id: draftContent
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 5
                        spacing: 4
                        MaterialIcon {
                            name: "description"
                            size: 14
                            color: root.theme.action
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
                            visible: draftFlow.cellWidth() >= 230
                        }
                        CompactIconButton {
                            Layout.preferredWidth: 22
                            Layout.preferredHeight: 22
                            theme: root.theme
                            iconName: "close"
                            visible: !root.controller.busy
                            onClicked: root.controller.remove(index)
                        }
                    }
                }
            }
        }

        ProgressBar {
            Layout.fillWidth: true
            visible: root.controller.busy
            value: root.controller.progress
        }
    }
}
