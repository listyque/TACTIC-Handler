import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme

    Rectangle { anchors.fill: parent; color: root.theme.workspace }

    Rectangle {
        id: toolbar
        anchors.top: parent.top
        width: parent.width
        height: 46
        color: root.theme.panel
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 11
            anchors.rightMargin: 8
            spacing: 7
            MaterialIcon {
                name: "cloud_sync"
                size: 16
                color: root.theme.action
            }
            Label {
                text: repositorySync.discovery_active
                    ? qsTr("Discovering repository files")
                    : repositorySync.discovery_state === "failed"
                        ? qsTr("Repository discovery failed")
                    : repositorySync.active_count > 0
                        ? repositorySync.active_count + qsTr(" active downloads")
                        : repositorySync.queue_count + qsTr(" files in queue")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
            Item { Layout.fillWidth: true }
            BusyIndicator {
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                running: repositorySync.discovery_active
                    || repositorySync.active_count > 0
                visible: running
            }
            CompactIconButton {
                theme: root.theme
                round: true
                iconName: "sync"
                toolTip: qsTr("Start checked downloads")
                onClicked: repositorySync.start_checked()
            }
            CompactIconButton {
                theme: root.theme
                round: true
                iconName: "delete"
                toolTip: qsTr("Clear completed downloads")
                onClicked: repositorySync.clear_finished()
            }
        }
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 1
            color: root.theme.separator
        }
    }

    ListView {
        id: queue
        anchors.top: toolbar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top
        anchors.margins: 7
        clip: true
        spacing: 3
        model: repoSyncModel
        delegate: Item {
            id: row
            required property int index
            required property string taskId
            required property string title
            required property string process
            required property string progress
            required property real progressValue
            required property string status
            required property bool checked
            required property real bytesDone
            required property real bytesTotal
            required property string speed
            required property string localPath
            required property string webPath
            required property int attempt
            required property string error
            required property bool active
            required property string phase
            required property bool alreadyExists
            width: ListView.view ? ListView.view.width : 0
            height: 76

            Rectangle {
                anchors.fill: parent
                radius: 9
                color: rowMouse.containsMouse
                    ? root.theme.rowHover : root.theme.panel
                border.width: 1
                border.color: root.theme.outlineVariant
                Behavior on color { ColorAnimation { duration: 100 } }
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.leftMargin: 1
                anchors.rightMargin: 1
                height: row.active ? 3 : 0
                color: "transparent"
                Rectangle {
                    width: parent.width * row.progressValue
                    height: parent.height
                    radius: 2
                    color: root.theme.action
                    Behavior on width { NumberAnimation { duration: 100 } }
                }
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 7
                Md3CheckBox {
                    theme: root.theme
                    checked: row.checked
                    onToggled: repoSyncModel.toggle_checked(row.index)
                }
                MaterialIcon {
                    name: row.phase === "failed" ? "priority_high"
                        : row.phase === "cancelled" ? "cancel"
                        : row.phase === "completed"
                            ? "check_circle" : "cloud_sync"
                    size: 15
                    color: row.phase === "failed" ? root.theme.red
                        : row.phase === "cancelled" ? root.theme.secondaryText
                        : row.phase === "completed"
                            ? root.theme.green : root.theme.cyan
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        text: row.title
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 10
                        font.weight: Font.Medium
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: (row.process.length ? row.process + "  •  " : "")
                            + (row.error.length ? row.error : row.progress)
                        color: row.phase === "failed"
                            ? root.theme.red : root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 9
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: row.localPath
                        visible: text.length > 0
                        color: root.theme.secondaryText
                        opacity: 0.72
                        font.family: "Consolas"
                        font.pixelSize: 8
                        elide: Text.ElideMiddle
                        Md3ToolTip {
                            theme: root.theme
                            visible: rowMouse.containsMouse
                                && !root.theme.suppressToolTips
                            text: row.localPath
                        }
                    }
                }
                Label {
                    text: row.alreadyExists ? "LOCAL" : row.phase.toUpperCase()
                    color: row.phase === "failed" ? root.theme.red
                        : row.phase === "completed" ? root.theme.green
                        : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 8
                    font.weight: Font.DemiBold
                }
                Label {
                    text: row.speed
                    color: root.theme.secondaryText
                    font.family: "Consolas"
                    font.pixelSize: 8
                }
                CompactIconButton {
                    visible: row.phase === "failed"
                        || row.phase === "cancelled"
                    theme: root.theme
                    round: true
                    iconName: "refresh"
                    toolTip: qsTr("Retry")
                    onClicked: repositorySync.retry_row(row.index)
                }
                CompactIconButton {
                    visible: row.active
                    theme: root.theme
                    round: true
                    iconName: "close"
                    iconColor: root.theme.red
                    toolTip: qsTr("Cancel")
                    onClicked: repositorySync.cancel_row(row.index)
                }
            }
            MouseArea {
                id: rowMouse
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.RightButton
                onClicked: function(mouse) {
                    contextMenu.row = row.index
                    contextMenu.openAt(row, mouse.x, mouse.y)
                }
            }
        }
        ScrollBar.vertical: Md3ScrollBar {
            theme: root.theme
            flickableTarget: queue
        }
    }

    Label {
        anchors.centerIn: queue
        visible: queue.count === 0
        width: Math.min(queue.width - 24, 520)
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        text: repositorySync.discovery_active
            ? qsTr("Discovering files…")
            : repositorySync.discovery_state === "failed"
                ? repositorySync.discovery_error
                : qsTr("Repository Sync queue is empty")
        color: repositorySync.discovery_state === "failed"
            ? root.theme.red : root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pixelSize: 10
    }

    Rectangle {
        id: footer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 34
        color: root.theme.panel
        Rectangle {
            anchors.top: parent.top
            width: parent.width
            height: 1
            color: root.theme.separator
        }
        Label {
            anchors.left: parent.left
            anchors.leftMargin: 11
            anchors.verticalCenter: parent.verticalCenter
            text: repositorySync.active_count > 0
                ? qsTr("Background transfers are active — the interface remains responsive")
                : qsTr("Files are verified before downloading and written atomically")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 9
        }
    }

    ActionMenu {
        id: contextMenu
        parent: Overlay.overlay
        theme: root.theme
        property int row: -1
        actions: appController.menu_actions("repo_sync")
        onTriggered: function(command) {
            if (command === "sync")
                repositorySync.retry_row(row)
            else if (command === "remove")
                repositorySync.remove_row(row)
            close()
        }
    }
}
