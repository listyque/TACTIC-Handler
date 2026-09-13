import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    property int selectedRow: -1

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

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
                Label {
                    text: qsTr("Active Watch Folders  ·  ") + appController.current_project_title
                    Layout.fillWidth: true
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.DemiBold
                }
                Controls.BusyIndicator {
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
                    required property string searchKey
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
                        ? root.theme.contentSelection : hover.hovered
                            ? root.theme.rowHover : root.theme.panelRaised
                    border.width: 1
                    border.color: root.theme.border

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 9
                        Controls.MaterialIcon {
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
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.DemiBold
                            }
                            Label {
                                Layout.fillWidth: true
                                text: path + "  ·  " + repository
                                elide: Text.ElideMiddle
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.micro
                            }
                            Label {
                                Layout.fillWidth: true
                                text: stype + "  ·  " + pipeline + "  ·  "
                                    + watcherStatus
                                elide: Text.ElideRight
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.micro
                            }

                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "edit"
                            toolTip: qsTr("Edit Watch Folder")
                            onClicked: {
                                root.selectedRow = watchRow.index
                                watchFoldersController.begin_edit_search_key(
                                    watchRow.searchKey, "manager"
                                )
                            }
                        }
                        Controls.Switch {
                            theme: root.theme
                            checked: watchRow.watchEnabled
                            onToggled: watchFoldersController.set_enabled(
                                watchRow.index, checked
                            )
                        }
                        Controls.CompactIconButton {
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
                    Controls.ActivationHandler {
                        onActivated: root.selectedRow = watchRow.index
                    }
                }
                ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }

                Label {
                    anchors.centerIn: parent
                    visible: watchFoldersModel.count() === 0
                    text: qsTr("No active watch folders")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.micro
                }
            }

        }
    }

    WatchFolderDeleteDialog {
        theme: root.theme
        acceptedOrigin: "manager"
    }
}
