import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

import "controls" as Controls
Item {
    id: root
    required property var theme
    property string contextGroupId: ""

    FileDialog {
        id: fileDialog
        title: qsTr("Add files to Drop Plate")
        fileMode: FileDialog.OpenFiles
        onAccepted: dropPlateController.add_paths(selectedFiles)
    }

    FolderDialog {
        id: folderDialog
        title: qsTr("Add directory to Drop Plate")
        onAccepted: dropPlateController.add_paths([selectedFolder])
    }

    ActionMenu {
        id: itemMenu
        theme: root.theme
        parent: Overlay.overlay
        preferredWidth: 220
        actions: [
            {"title": "Open file", "icon": "open_in_new", "command": "open"},
            {"title": "Show folder", "icon": "folder_open", "command": "folder"},
            {"separator": true},
            {"title": "Copy file path", "icon": "content_copy", "command": "copy"},
            {"title": "Copy all file paths", "icon": "copy_all", "command": "copy_all"},
            {"separator": true},
            {"title": "Remove from Drop Plate", "icon": "delete", "command": "remove"}
        ]
        onTriggered: function(command) {
            if (command === "open")
                dropPlateController.open_file(root.contextGroupId)
            else if (command === "folder")
                dropPlateController.show_folder(root.contextGroupId)
            else if (command === "copy")
                dropPlateController.copy_path(root.contextGroupId, false)
            else if (command === "copy_all")
                dropPlateController.copy_path(root.contextGroupId, true)
            else if (command === "remove")
                dropPlateController.remove_id(root.contextGroupId)
        }
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Controls.Button {
                theme: root.theme
                text: qsTr("Files")
                icon.name: "add"
                enabled: !dropPlateController.busy
                onClicked: fileDialog.open()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Directory")
                icon.name: "create_new_folder"
                enabled: !dropPlateController.busy
                onClicked: folderDialog.open()
            }
            Controls.CheckBox {
                theme: root.theme
                text: qsTr("Include subfolders")
                checked: dropPlateController.recursive
                onClicked: dropPlateController.set_recursive(checked)
            }
            Controls.CheckBox {
                theme: root.theme
                text: qsTr("Group check-in")
                checked: dropPlateController.groupCheckin
                onClicked: dropPlateController.set_group_checkin(checked)
            }
            Controls.CheckBox {
                theme: root.theme
                text: qsTr("Keep filename")
                checked: checkinOutController.keepFileName
                onClicked: checkinOutController.set_keep_file_name(checked)
            }
            Item { Layout.fillWidth: true }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "content_paste"
                enabled: !dropPlateController.busy
                onClicked: dropPlateController.paste_paths()
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "tune"
                onClicked:
                    windowModel.show_window("matching_templates")
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "delete_sweep"
                enabled: dropPlateController.count > 0
                    && !dropPlateController.busy
                onClicked: dropPlateController.clear()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Controls.ComboBox {
                id: filterMode
                theme: root.theme
                Layout.preferredWidth: 130
                model: ["Filename", "Extension"]
            }
            Controls.TextField {
                id: filterField
                theme: root.theme
                Layout.fillWidth: true
                placeholderText: filterMode.currentIndex === 1
                    ? qsTr("Filter by extension") : qsTr("Filter files")
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 16
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: fileDrop.containsDrag
                ? root.theme.action : root.theme.outlineVariant

            ListView {
                id: groupList
                anchors.fill: parent
                anchors.margins: 7
                clip: true
                spacing: 0
                model: dropPlateModel
                delegate: Item {
                    required property int index
                    required property string groupId
                    required property string title
                    required property string path
                    required property string extension
                    required property int fileCount
                    required property string size
                    required property bool checked
                    required property string status
                    required property string matchingType
                    required property string sequenceInfo
                    required property string error
                    readonly property string normalizedFilter:
                        filterField.text.trim().toLowerCase()
                    readonly property bool matchesFilter:
                        normalizedFilter.length === 0
                        || (filterMode.currentIndex === 1
                            ? extension.toLowerCase().indexOf(
                                normalizedFilter.replace(/^\./, "")) >= 0
                            : (title + " " + path).toLowerCase().indexOf(
                                normalizedFilter) >= 0)
                    width: groupList.width
                    height: matchesFilter ? 67 : 0
                    visible: height > 0

                    Rectangle {
                        id: itemSurface
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        height: 62
                        radius: 12
                        color: root.theme.surfaceContainerHigh

                    RowLayout {
                        anchors.fill: itemSurface
                        anchors.margins: 8
                        spacing: 8
                        Controls.CheckBox {
                            theme: root.theme
                            checked: parent.parent.parent.checked
                            onClicked: dropPlateController.toggle_checked_id(
                                parent.parent.parent.groupId)
                        }
                        Controls.MaterialIcon {
                            name: matchingType.indexOf("sequence") >= 0
                                ? "movie" : "insert_drive_file"
                            size: 18
                            color: error ? root.theme.error : root.theme.action
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Label {
                                Layout.fillWidth: true
                                text: title
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideMiddle
                            }
                            Label {
                                Layout.fillWidth: true
                                text: (sequenceInfo || matchingType)
                                    + "  •  " + fileCount + qsTr(" file(s)")
                                    + (size ? "  •  " + size : "")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: error || path
                                color: error ? root.theme.error
                                    : root.theme.disabledText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideMiddle
                            }
                        }
                        Label {
                            text: status
                            color: status === "Queued"
                                ? root.theme.green : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            onClicked: dropPlateController.remove_id(groupId)
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.RightButton
                        onPressed: function(mouse) {
                            root.contextGroupId = groupId
                            itemMenu.openAt(itemSurface, mouse.x, mouse.y)
                        }
                    }
                    }
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                    flickableTarget: groupList
                }
                Column {
                    anchors.centerIn: parent
                    spacing: 7
                    visible: dropPlateController.count === 0
                        && !dropPlateController.busy
                    Controls.MaterialIcon {
                        anchors.horizontalCenter: parent.horizontalCenter
                        name: "move_to_inbox"
                        size: 32
                        color: root.theme.disabledText
                    }
                    Label {
                        text: qsTr("Drop files or directories here")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                    }
                }
                Column {
                    anchors.centerIn: parent
                    spacing: 7
                    visible: dropPlateController.busy
                    Controls.BusyIndicator {
                        uiTheme: root.theme
                        anchors.horizontalCenter: parent.horizontalCenter
                        running: visible
                    }
                    Label {
                        text: qsTr("Matching files…")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                    }
                }
            }

            DropArea {
                id: fileDrop
                anchors.fill: parent
                onDropped: function(drop) {
                    if (drop.hasUrls) {
                        dropPlateController.add_paths(drop.urls)
                        drop.acceptProposedAction()
                    }
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: dropPlateController.error.length > 0
            text: dropPlateController.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: checkinOutController.hasObject
                    ? checkinOutController.currentObject.title
                    : qsTr("Select an sObject before adding to queue")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                elide: Text.ElideRight
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Add to queue")
                icon.name: "playlist_add"
                highlighted: enabled
                enabled: dropPlateController.count > 0
                    && !dropPlateController.busy
                    && checkinOutController.actionAvailable
                onClicked: dropPlateController.add_selected_to_queue()
            }
        }
    }
}
