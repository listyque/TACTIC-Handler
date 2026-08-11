import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

import "controls"

Item {
    id: root
    required property var theme
    required property string editorMode

    readonly property bool namingOnly: editorMode === "naming_editor"
    readonly property string subject: editorMode === "preview_editor"
        ? "preview" : editorMode === "attachments_editor" ? "attachment" : "file"
    readonly property string heading: editorMode === "preview_editor"
        ? "Preview files" : editorMode === "attachments_editor"
            ? "Attachments" : "Naming preview"

    function activateMode() {
        checkinOutController.set_mode("checkin")
        if (editorMode === "preview_editor") {
            checkinOutController.set_process("icon")
            checkinOutController.set_context("icon")
            checkinOutController.set_generate_previews(true)
        } else if (editorMode === "attachments_editor") {
            checkinOutController.set_process("attachment")
            checkinOutController.set_context("attachment")
        }
    }

    onVisibleChanged: if (visible) activateMode()
    Component.onCompleted: if (visible) activateMode()

    FileDialog {
        id: fileDialog
        title: qsTr("Choose ") + qsTr(root.subject) + qsTr(" files")
        fileMode: FileDialog.OpenFiles
        onAccepted: checkinOutController.add_files(selectedFiles)
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    DropArea {
        id: dropArea
        anchors.fill: parent
        enabled: !checkinOutController.operationBusy
        z: 20
        onDropped: function(drop) {
            if (drop.hasUrls) {
                checkinOutController.add_files(drop.urls)
                drop.acceptProposedAction()
            }
        }
        Rectangle {
            anchors.fill: parent
            visible: dropArea.containsDrag
            color: root.theme.action
            opacity: 0.14
            radius: 18
            border.width: 2
            border.color: root.theme.action
            Label {
                anchors.centerIn: parent
                text: qsTr("Drop files here")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 14
                font.weight: Font.DemiBold
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Rectangle {
                Layout.preferredWidth: 42
                Layout.preferredHeight: 42
                radius: 14
                color: root.theme.secondaryContainer
                MaterialIcon {
                    anchors.centerIn: parent
                    name: root.editorMode === "preview_editor" ? "image"
                        : root.editorMode === "attachments_editor"
                            ? "attach_file" : "drive_file_rename_outline"
                    size: 21
                    color: root.theme.action
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                Label {
                    text: root.heading
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    text: checkinOutController.currentObject.title
                        || qsTr("Select an object in Workspace")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 10
                    elide: Text.ElideRight
                }
            }
            Label {
                text: checkinOutController.repositoryTitle
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 9
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 180
            radius: 16
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 7
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: checkinFileModel.count() + qsTr(" files")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                    }
                    Item { Layout.fillWidth: true }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Add files")
                        icon.name: "add"
                        enabled: !checkinOutController.operationBusy
                        onClicked: fileDialog.open()
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "delete_sweep"
                        toolTip: qsTr("Remove all prepared files")
                        enabled: checkinFileModel.count() > 0
                            && !checkinOutController.operationBusy
                        onClicked: checkinOutController.clear_files()
                    }
                }
                ListView {
                    id: fileList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: checkinFileModel
                    clip: true
                    spacing: 5
                    delegate: Rectangle {
                        required property int index
                        required property string name
                        required property string size
                        required property string extension
                        required property string fileType
                        required property string namingVersioned
                        required property string namingVersionless
                        required property string error
                        width: fileList.width
                        height: root.namingOnly ? 76 : 62
                        radius: 12
                        color: root.theme.surfaceContainerHigh
                        border.width: error.length > 0 ? 1 : 0
                        border.color: root.theme.red
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 9
                            spacing: 9
                            Rectangle {
                                Layout.preferredWidth: 40
                                Layout.preferredHeight: 40
                                radius: 11
                                color: root.theme.secondaryContainer
                                Label {
                                    anchors.centerIn: parent
                                    text: extension || qsTr("FILE")
                                    color: root.theme.action
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 8
                                    font.weight: Font.Bold
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    Layout.fillWidth: true
                                    text: name + "  ·  " + size + "  ·  " + fileType
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 10
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: error || namingVersioned
                                        || qsTr("Preparing naming preview")
                                    color: error ? root.theme.red : namingVersioned
                                        ? root.theme.secondaryText : root.theme.action
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 9
                                    elide: Text.ElideMiddle
                                }
                                Label {
                                    Layout.fillWidth: true
                                    visible: root.namingOnly && namingVersionless.length > 0
                                    text: qsTr("Versionless  ") + namingVersionless
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 8
                                    elide: Text.ElideMiddle
                                }
                            }
                            CompactIconButton {
                                theme: root.theme
                                iconName: "close"
                                toolTip: qsTr("Remove from preparation")
                                enabled: !checkinOutController.operationBusy
                                onClicked: checkinOutController.remove_file(index)
                            }
                        }
                    }
                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: fileList
                    }
                    Label {
                        anchors.centerIn: parent
                        visible: checkinFileModel.count() === 0
                        text: qsTr("Add files or drop them here")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 10
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: width > 560 ? 2 : 1
            rowSpacing: 7
            columnSpacing: 10
            Md3ComboBox {
                theme: root.theme
                Layout.fillWidth: true
                enabled: !root.namingOnly && checkinOutController.hasObject
                model: checkinOutController.contexts
                editable: true
                currentIndex: Math.max(0, model.indexOf(checkinOutController.context))
                editText: checkinOutController.context
                onActivated: checkinOutController.set_context(currentText)
                onAccepted: checkinOutController.set_context(editText)
            }
            Md3SpinBox {
                theme: root.theme
                Layout.fillWidth: true
                from: 0
                to: 9999
                value: checkinOutController.version
                enabled: !checkinOutController.operationBusy
                onValueModified: checkinOutController.set_version(value)
            }
            Md3CheckBox {
                theme: root.theme
                text: qsTr("Keep source file name")
                checked: checkinOutController.keepFileName
                enabled: !checkinOutController.operationBusy
                onToggled: checkinOutController.set_keep_file_name(checked)
            }
            Md3CheckBox {
                theme: root.theme
                text: qsTr("Update versionless")
                checked: checkinOutController.updateVersionless
                enabled: !checkinOutController.keepFileName
                    && !checkinOutController.operationBusy
                onToggled: checkinOutController.set_update_versionless(checked)
            }
        }

        DescriptionEditor {
            theme: root.theme
            Layout.fillWidth: true
            Layout.preferredHeight: 74
            visible: !root.namingOnly
            managed: false
            compact: true
            value: checkinOutController.description
            editorEnabled: !checkinOutController.operationBusy
            onValueEdited: value => checkinOutController.set_description(value)
            onEditingFinished: value => checkinOutController.set_description(value)
        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: checkinOutController.operationBusy
                || checkinOutController.operationError.length > 0
                || checkinOutController.preparationError.length > 0
            spacing: 4
            ProgressBar {
                Layout.fillWidth: true
                from: 0
                to: 1
                indeterminate: checkinOutController.operationBusy
                    && checkinOutController.operationProgress <= 0
                value: checkinOutController.operationProgress
            }
            Label {
                Layout.fillWidth: true
                text: checkinOutController.operationError
                    || checkinOutController.preparationError
                    || checkinOutController.operationMessage
                color: checkinOutController.operationError
                    || checkinOutController.preparationError
                    ? root.theme.red : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 9
                wrapMode: Text.WordWrap
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 7
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                icon.name: "stop"
                visible: checkinOutController.operationBusy
                onClicked: checkinOutController.cancel_checkin()
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Retry")
                icon.name: "refresh"
                visible: checkinOutController.canRetryOperation
                onClicked: checkinOutController.retry_checkin()
            }
            Item { Layout.fillWidth: true }
            Md3Button {
                theme: root.theme
                text: qsTr("Add to queue")
                icon.name: "playlist_add"
                visible: !root.namingOnly
                enabled: checkinOutController.payloadReady
                    && !checkinOutController.operationBusy
                onClicked: checkinOutController.queue_current_operation()
            }
            Md3Button {
                theme: root.theme
                text: root.namingOnly ? qsTr("Refresh preview")
                    : root.editorMode === "preview_editor"
                        ? qsTr("Save preview") : qsTr("Save attachments")
                icon.name: root.namingOnly ? "refresh" : "save"
                highlighted: true
                enabled: root.namingOnly
                    ? checkinFileModel.count() > 0
                        && !checkinOutController.namingBusy
                    : checkinOutController.payloadReady
                        && !checkinOutController.operationBusy
                onClicked: {
                    if (root.namingOnly)
                        checkinOutController.set_version(checkinOutController.version)
                    else
                        checkinOutController.start_checkin()
                }
            }
        }
    }
}
