import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    property int selectedRow: -1
    property int pendingDeleteRow: -1

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            color: root.theme.toolBar
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 8
                spacing: 6
                CompactIconButton {
                    theme: root.theme
                    iconName: "add"
                    enabled: !watchFoldersController.busy
                    onClicked: watchFoldersController.begin_add()
                }
                Label {
                    text: qsTr("Watch folders  ·  ") + appController.current_project_title
                    Layout.fillWidth: true
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }
                BusyIndicator {
                    visible: watchFoldersController.busy
                    running: visible
                    implicitWidth: 22
                    implicitHeight: 22
                }
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Vertical

            ListView {
                id: watchList
                SplitView.fillHeight: true
                SplitView.minimumHeight: 130
                clip: true
                spacing: 4
                topMargin: 8
                bottomMargin: 8
                leftMargin: 8
                rightMargin: 8
                model: watchFoldersModel

                delegate: Rectangle {
                    id: watchRow
                    required property int index
                    required property string title
                    required property string path
                    required property bool watchEnabled
                    required property string repository
                    required property string process
                    required property string context
                    required property string watcherStatus
                    required property string lastCheck
                    required property string error
                    width: watchList.width - watchList.leftMargin
                        - watchList.rightMargin
                    height: error ? 82 : 66
                    radius: 12
                    color: root.selectedRow === index
                        ? root.theme.selected : hover.hovered
                            ? root.theme.rowHover : root.theme.panelRaised
                    border.width: 1
                    border.color: root.theme.border

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 9
                        MaterialIcon {
                            name: watcherStatus === "Watching"
                                ? "visibility" : watcherStatus === "Error"
                                    ? "error" : "visibility_off"
                            size: 18
                            color: watcherStatus === "Watching"
                                ? root.theme.green : watcherStatus === "Error"
                                    ? root.theme.red : root.theme.secondaryText
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Label {
                                Layout.fillWidth: true
                                text: title
                                elide: Text.ElideRight
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                            }
                            Label {
                                Layout.fillWidth: true
                                text: path + "  ·  " + repository
                                elide: Text.ElideMiddle
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 9
                            }
                            Label {
                                Layout.fillWidth: true
                                text: process + " / " + context + "  ·  "
                                    + watcherStatus + "  ·  " + lastCheck
                                elide: Text.ElideRight
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 9
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: error.length > 0
                                text: error
                                elide: Text.ElideRight
                                color: root.theme.red
                                font.family: root.theme.fontFamily
                                font.pixelSize: 9
                            }
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "refresh"
                            onClicked: watchFoldersController.scan(watchRow.index)
                        }
                        Md3Switch {
                            theme: root.theme
                            checked: watchRow.watchEnabled
                            onToggled: watchFoldersController.set_enabled(
                                watchRow.index, checked
                            )
                        }
                    }
                    HoverHandler {
                        id: hover
                        cursorShape: Qt.PointingHandCursor
                    }
                    TapHandler {
                        onTapped: {
                            root.selectedRow = watchRow.index
                            watchFoldersController.begin_edit(watchRow.index)
                        }
                    }
                }
                ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

                Label {
                    anchors.centerIn: parent
                    visible: watchFoldersModel.count() === 0
                    text: qsTr("Select an sObject and add its watch folder")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 10
                }
            }

            Rectangle {
                SplitView.preferredHeight: watchFoldersController.editor.searchKey
                    ? 300 : 0
                SplitView.minimumHeight: watchFoldersController.editor.searchKey
                    ? 210 : 0
                visible: Boolean(watchFoldersController.editor.searchKey)
                color: root.theme.workspace
                border.color: root.theme.border

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 12
                    clip: true
                    ColumnLayout {
                        width: parent.width
                        spacing: 8
                        Label {
                            text: watchFoldersController.editor.title
                                || qsTr("Watch folder")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }
                        Md3TextField {
                            theme: root.theme
                            Layout.fillWidth: true
                            placeholderText: qsTr("Relative repository path")
                            text: watchFoldersController.editor.path || ""
                            onTextEdited: watchFoldersController.set_editor_value(
                                "path", text
                            )
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Md3TextField {
                                theme: root.theme
                                Layout.fillWidth: true
                                placeholderText: qsTr("Process")
                                text: watchFoldersController.editor.process || ""
                                onTextEdited: watchFoldersController.set_editor_value(
                                    "process", text
                                )
                            }
                            Md3TextField {
                                theme: root.theme
                                Layout.fillWidth: true
                                placeholderText: qsTr("Context")
                                text: watchFoldersController.editor.context || ""
                                onTextEdited: watchFoldersController.set_editor_value(
                                    "context", text
                                )
                            }
                        }
                        Md3ComboBox {
                            theme: root.theme
                            Layout.fillWidth: true
                            model: watchFoldersController.matchingTemplates
                            textRole: "label"
                            valueRole: "value"
                            currentIndex: indexOfValue(
                                watchFoldersController.editor.matchingTemplate
                            )
                            onActivated: watchFoldersController.set_editor_value(
                                "matchingTemplate", currentValue
                            )
                        }
                        Label {
                            text: qsTr("REPOSITORIES")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 9
                            font.weight: Font.DemiBold
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            Repeater {
                                model: watchFoldersController.repositories
                                delegate: Md3CheckBox {
                                    required property var modelData
                                    theme: root.theme
                                    text: modelData.label
                                    checked: (
                                        watchFoldersController.editor.repositories
                                        || []
                                    ).indexOf(modelData.value) >= 0
                                    onToggled:
                                        watchFoldersController.toggle_editor_repository(
                                            modelData.value, checked
                                        )
                                }
                            }
                        }
                        Label {
                            Layout.fillWidth: true
                            visible: watchFoldersController.message.length > 0
                            text: watchFoldersController.message
                            wrapMode: Text.WordWrap
                            color: root.theme.red
                            font.family: root.theme.fontFamily
                            font.pixelSize: 9
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Md3Button {
                                theme: root.theme
                                text: qsTr("DELETE")
                                destructive: true
                                visible: root.selectedRow >= 0
                                onClicked: {
                                    root.pendingDeleteRow = root.selectedRow
                                    deleteDialog.open()
                                }
                            }
                            Item { Layout.fillWidth: true }
                            Md3Button {
                                theme: root.theme
                                text: qsTr("CANCEL")
                                onClicked: watchFoldersController.cancel_edit()
                            }
                            Md3Button {
                                theme: root.theme
                                text: qsTr("SAVE")
                                highlighted: true
                                enabled: !watchFoldersController.busy
                                onClicked: watchFoldersController.save_edit()
                            }
                        }
                    }
                }
            }
        }
    }

    Md3Dialog {
        id: deleteDialog
        theme: root.theme
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(390, root.width - 32)
        title: qsTr("Remove watch folder?")
        standardButtons: Dialog.NoButton
        contentItem: ColumnLayout {
            spacing: 16
            Label {
                Layout.fillWidth: true
                text: qsTr("The saved watch is removed. Repository files are kept.")
                wrapMode: Text.WordWrap
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 11
            }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                Md3Button {
                    theme: root.theme
                    text: qsTr("CANCEL")
                    onClicked: deleteDialog.close()
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("REMOVE")
                    destructive: true
                    onClicked: {
                        watchFoldersController.remove(root.pendingDeleteRow)
                        root.selectedRow = -1
                        deleteDialog.close()
                    }
                }
            }
        }
    }
}
