import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root
    required property var theme
    required property var controller
    required property var attachmentModel
    property string title: qsTr("Attachments")
    property string emptyText: "Drop files here or choose them from disk"
    property bool showFileChooser: true
    signal filesAdded()

    function chooseFiles() {
        fileDialog.open()
    }

    function addFiles(values) {
        root.controller.add_files(values)
        root.filesAdded()
    }

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
        nameFilters: [qsTr("All files") + " (*)"]
        onAccepted: root.addFiles(selectedFiles)
    }

    DropArea {
        id: dropArea
        anchors.fill: parent
        enabled: !root.controller.busy
        z: 10
        onDropped: drop => {
            if (drop.hasUrls) {
                root.addFiles(drop.urls)
                drop.acceptProposedAction()
            }
        }

        Controls.DropTargetOverlay {
            visible: dropArea.containsDrag
            theme: root.theme
            iconName: "attach_file"
            promptText: root.emptyText
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
            Controls.MaterialIcon {
                name: "attach_file"
                size: 16
                color: root.theme.action
            }
            Label {
                Layout.fillWidth: true
                text: root.controller.count > 0
                    ? root.controller.count + (root.controller.count === 1
                        ? qsTr(" attachment") : qsTr(" attachments"))
                    : root.title
                color: root.controller.count > 0
                    ? root.theme.primaryText : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                elide: Text.ElideRight
            }
            Controls.CompactIconButton {
                objectName: "attachmentChooseFiles"
                theme: root.theme
                iconName: "attach_file"
                toolTip: qsTr("Choose files")
                visible: root.showFileChooser
                enabled: !root.controller.busy
                onClicked: fileDialog.open()
            }
            Controls.CompactIconButton {
                objectName: "attachmentClipboardImage"
                theme: root.theme
                iconName: "content_paste"
                toolTip: qsTr("Attach image from clipboard")
                enabled: !root.controller.busy
                onClicked: {
                    if (root.controller.add_clipboard_image())
                        root.filesAdded()
                }
            }
            Controls.CompactIconButton {
                objectName: "attachmentClearAll"
                theme: root.theme
                iconName: "delete_sweep"
                toolTip: qsTr("Clear attachments")
                visible: root.controller.count > 0
                enabled: !root.controller.busy
                onClicked: root.controller.clear()
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "close"
                toolTip: qsTr("Cancel upload")
                visible: root.controller.busy
                onClicked: root.controller.cancel()
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: root.controller.count > 0 ? 148 : 88

            Column {
                anchors.centerIn: parent
                spacing: 4
                visible: root.controller.count === 0

                Controls.MaterialIcon {
                    anchors.horizontalCenter: parent.horizontalCenter
                    name: "attach_file"
                    size: 28
                    color: root.theme.secondaryText
                }
                Label {
                    width: Math.min(
                        implicitWidth, Math.max(0, root.width - 32))
                    text: root.emptyText
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                }
            }

            Flickable {
                id: draftFlickable
                objectName: "attachmentStagingFlickable"
                anchors.fill: parent
                visible: root.controller.count > 0
                clip: true
                contentWidth: draftRow.implicitWidth
                contentHeight: height
                boundsBehavior: Flickable.StopAtBounds
                flickableDirection: Flickable.HorizontalFlick

                Row {
                    id: draftRow
                    height: Math.max(0, parent.height - 12)
                    spacing: 8

                    Repeater {
                        id: draftRepeater
                        objectName: "attachmentStagingRepeater"
                        model: root.attachmentModel

                        delegate: Rectangle {
                            id: draftTile
                            required property int index
                            required property string title
                            required property string size
                            required property string fileType
                            required property string previewUrl
                            required property string status
                            readonly property string extension: {
                                const parts = title.split(".")
                                return parts.length > 1
                                    ? parts[parts.length - 1].toUpperCase()
                                    : qsTr("FILE")
                            }

                            objectName: "attachmentStagingTile-" + index
                            width: 124
                            height: draftRow.height
                            radius: 12
                            color: root.theme.surfaceContainerHigh
                            border.width: 1
                            border.color: status === "failed"
                                ? root.theme.error
                                : root.theme.outlineVariant

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 6
                                spacing: 4

                                Controls.ItemPreview {
                                    objectName: "attachmentStagingPreview-"
                                        + draftTile.index
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    theme: root.theme
                                    source: draftTile.previewUrl
                                    fallbackIcon: draftTile.fileType === "preview"
                                        ? "image" : "description"
                                    fallbackText: draftTile.extension
                                    accent: root.theme.action
                                    cornerRadius: 9
                                    outlined: true
                                    previewSize: 92
                                    fillMode: Image.PreserveAspectFit
                                    animateAppearance: false
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: draftTile.title
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    elide: Text.ElideMiddle
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: draftTile.size
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }

                            Controls.CompactIconButton {
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 8
                                width: 26
                                height: 26
                                theme: root.theme
                                iconName: "close"
                                iconSize: 13
                                round: true
                                elevated: true
                                visible: !root.controller.busy
                                toolTip: qsTr("Remove attachment")
                                onClicked: root.controller.remove(
                                    draftTile.index)
                            }
                        }
                    }
                }

                ScrollBar.horizontal: Controls.ScrollBar {
                    objectName: "attachmentStagingHorizontalScrollBar"
                    theme: root.theme
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
