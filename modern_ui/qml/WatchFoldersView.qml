import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    property int selectedRow: -1

    Rectangle { anchors.fill: parent; color: root.theme.workspace }

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
                    toolTip: qsTr("Add Watch Folder")
                    enabled: !watchFoldersController.busy
                    onClicked: watchFoldersController.begin_add()
                }
                Label {
                    text: qsTr("Active Watch Folders  ·  ") + appController.current_project_title
                    Layout.fillWidth: true
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }
                Md3BusyIndicator {
                    uiTheme: root.theme
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
                    required property string stype
                    required property string pipeline
                    required property string watcherStatus
                    width: watchList.width - watchList.leftMargin
                        - watchList.rightMargin
                    height: 72
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
                                ? "visibility" : watcherStatus === "Waiting"
                                    ? "schedule" : "visibility_off"
                            size: 18
                            color: watcherStatus === "Watching"
                                ? root.theme.green : root.theme.secondaryText
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
                                text: stype + "  ·  " + pipeline + "  ·  "
                                    + watcherStatus
                                elide: Text.ElideRight
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 9
                            }

                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "edit"
                            toolTip: qsTr("Edit Watch Folder")
                            onClicked: watchFoldersController.begin_edit(watchRow.index)
                        }
                        Md3Switch {
                            theme: root.theme
                            checked: watchRow.watchEnabled
                            onToggled: watchFoldersController.set_enabled(
                                watchRow.index, checked
                            )
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "delete"
                            toolTip: qsTr("Delete Watch Folder")
                            onClicked: watchFoldersController.request_remove(
                                watchRow.index, "manager"
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
                    text: qsTr("No active watch folders")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 10
                }
            }

        }
    }

    WatchFolderDeleteDialog {
        theme: root.theme
        acceptedOrigin: "manager"
    }
}
