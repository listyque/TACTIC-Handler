import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme

    function discoveryStatusText() {
        if (repositorySync.discovery_state === "objects")
            return qsTr("Requesting object list from TACTIC")
        if (repositorySync.discovery_state === "scope")
            return qsTr("Preparing parallel repository chunks")
        if (repositorySync.discovery_state === "processing")
            return qsTr("Processing server response: %1 objects")
                .arg(repositorySync.discovery_total_roots)
        if (repositorySync.discovery_state === "snapshots")
            return qsTr("Requesting snapshots: %1 / %2 objects")
                .arg(repositorySync.discovery_processed_roots)
                .arg(repositorySync.discovery_total_roots)
        if (repositorySync.discovery_state === "publishing")
            return qsTr("Preparing download queue: %1 files")
                .arg(repositorySync.batch_file_count)
        if (repositorySync.discovery_state === "streaming"
                && repositorySync.discovery_total_roots > 0)
            return qsTr("Parallel repository chunks: %1 / %2 objects")
                .arg(repositorySync.discovery_processed_roots)
                .arg(repositorySync.discovery_total_roots)
        if (repositorySync.discovery_state === "cancelling")
            return qsTr("Stopping repository discovery")
        return qsTr("Discovering repository files")
    }

    function phaseLabel(phase, alreadyExists) {
        if (alreadyExists)
            return qsTr("Local")
        if (phase === "completed")
            return qsTr("Completed")
        if (phase === "downloading")
            return qsTr("Downloading")
        if (phase === "failed")
            return qsTr("Failed")
        if (phase === "cancelled")
            return qsTr("Cancelled")
        return qsTr("Queued")
    }

    component SummaryMetric: Rectangle {
        required property string metricTitle
        required property string metricValue
        implicitHeight: 48
        radius: root.theme.itemRadius
        color: root.theme.surfaceContainerHigh
        Column {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            anchors.topMargin: 7
            spacing: 2
            Label {
                width: parent.width
                text: parent.parent.metricTitle
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Label {
                width: parent.width
                text: parent.parent.metricValue
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 13
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
        }
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    Rectangle {
        id: toolbar
        anchors.top: parent.top
        width: parent.width
        height: 50
        color: root.theme.panel
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 11
            anchors.rightMargin: 8
            spacing: 7
            Controls.MaterialIcon {
                name: "repository-sync"
                size: 16
                color: root.theme.action
            }
            Label {
                objectName: "repositorySyncStatusLabel"
                Layout.fillWidth: true
                text: repositorySync.discovery_active
                    ? root.discoveryStatusText()
                    : repositorySync.discovery_state === "failed"
                        ? qsTr("Repository discovery failed")
                    : repositorySync.active_count > 0
                        ? repositorySync.active_count + qsTr(" active downloads")
                        : repositorySync.queue_count + qsTr(" files in queue")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Controls.BusyIndicator {
                uiTheme: root.theme
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                running: repositorySync.discovery_active
                    || repositorySync.active_count > 0
                visible: running
            }
            Controls.CompactIconButton {
                visible: repositorySync.discovery_active
                    && repositorySync.discovery_mode === "partial"
                theme: root.theme
                round: true
                iconName: "close"
                iconColor: root.theme.red
                toolTip: qsTr("Stop discovering more files")
                onClicked: repositorySync.cancel_discovery()
            }
            Controls.CompactIconButton {
                theme: root.theme
                round: true
                iconName: "sync"
                toolTip: qsTr("Start checked downloads")
                onClicked: repositorySync.start_checked()
            }
            Controls.Switch {
                id: autoCleanSwitch
                theme: root.theme
                text: toolbar.width >= 650 ? qsTr("Auto-clean") : ""
                checked: repositorySync.auto_clean
                onToggled: repositorySync.set_auto_clean(checked)
                Controls.ToolTip {
                    theme: root.theme
                    visible: autoCleanSwitch.hovered
                        && !root.theme.suppressToolTips
                    text: qsTr("Auto-clean completed repository downloads")
                }
            }
            Controls.CompactIconButton {
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

    Rectangle {
        id: summaryCard
        anchors.top: toolbar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 8
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        height: summaryContent.implicitHeight + 24
        visible: repositorySync.discovery_active
            || repositorySync.batch_file_count > 0
            || repositorySync.queue_count > 0
        radius: 12
        color: root.theme.panel
        border.width: 1
        border.color: root.theme.outlineVariant

        ColumnLayout {
            id: summaryContent
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Controls.MaterialIcon {
                    name: repositorySync.failed_file_count > 0
                        ? "warning" : repositorySync.active_count > 0
                            ? "cloud_download" : "task_alt"
                    size: 18
                    color: repositorySync.failed_file_count > 0
                        ? root.theme.red : repositorySync.active_count > 0
                            ? root.theme.action : root.theme.green
                }
                Label {
                    Layout.fillWidth: true
                    text: repositorySync.discovery_active
                        ? root.discoveryStatusText()
                        : repositorySync.active_count > 0
                        ? qsTr("Downloading repository files")
                        : repositorySync.processed_file_count === 0
                            ? qsTr("Ready to download repository files")
                        : repositorySync.failed_file_count > 0
                            ? qsTr("Repository download finished with errors")
                            : qsTr("Repository download complete")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    text: Math.round(repositorySync.overall_progress * 100) + "%"
                    color: root.theme.action
                    font.family: root.theme.fontFamily
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 7
                radius: height / 2
                color: root.theme.surfaceContainerHigh
                Rectangle {
                    width: parent.width * repositorySync.overall_progress
                    height: parent.height
                    radius: height / 2
                    color: repositorySync.failed_file_count > 0
                        && repositorySync.active_count === 0
                        ? root.theme.red : root.theme.action
                    Behavior on width { NumberAnimation { duration: theme.motionFast } }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: summaryCard.width >= 760 ? 4
                    : summaryCard.width >= 520 ? 3 : 2
                columnSpacing: 16
                rowSpacing: 8

                SummaryMetric {
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    metricTitle: qsTr("Processed / total files")
                    metricValue: repositorySync.processed_file_count
                        + " / " + repositorySync.batch_file_count
                }
                SummaryMetric {
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    metricTitle: qsTr("Total size")
                    metricValue: repositorySync.total_size_text
                }
                SummaryMetric {
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    metricTitle: qsTr("Downloaded")
                    metricValue: repositorySync.transferred_size_text
                }
                SummaryMetric {
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    metricTitle: qsTr("Remaining data")
                    metricValue: repositorySync.remaining_size_text
                }
                SummaryMetric {
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    metricTitle: repositorySync.active_count > 0
                        ? qsTr("Speed") : qsTr("Average speed")
                    metricValue: repositorySync.aggregate_speed_text
                }
                SummaryMetric {
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    metricTitle: qsTr("Elapsed")
                    metricValue: repositorySync.elapsed_text
                }
                SummaryMetric {
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    metricTitle: qsTr("Remaining")
                    metricValue: repositorySync.eta_text
                }
                SummaryMetric {
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    metricTitle: qsTr("Successful / errors")
                    metricValue: repositorySync.completed_file_count
                        + " / " + repositorySync.failed_file_count
                }
            }
        }
    }

    ListView {
        id: queue
        anchors.top: summaryCard.visible ? summaryCard.bottom : toolbar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top
        anchors.topMargin: 7
        anchors.leftMargin: 7
        anchors.rightMargin: 7
        anchors.bottomMargin: 7
        clip: true
        spacing: 3
        model: repoSyncModel
        reuseItems: true

        Connections {
            target: repositorySync

            function onActiveRowChanged() {
                // Do not fight a user who is inspecting another part of a
                // large queue. The next throttled active-row notification
                // resumes following after manual scrolling stops.
                if (repositorySync.active_row >= 0
                        && !queue.dragging && !queue.flicking)
                    queue.positionViewAtIndex(
                        repositorySync.active_row,
                        ListView.Contain
                    )
            }
        }

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
                color: row.active
                    ? root.theme.surfaceContainerHigh
                    : rowMouse.containsMouse
                        ? root.theme.rowHover : root.theme.panel
                border.width: 1
                border.color: row.active
                    ? root.theme.action : root.theme.outlineVariant
                Behavior on color { ColorAnimation { duration: theme.hoverMotionFast } }
            }
            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: row.active ? 3 : 0
                radius: 2
                color: root.theme.action
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
                    Behavior on width { NumberAnimation { duration: theme.motionFast } }
                }
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 7
                Controls.CheckBox {
                    theme: root.theme
                    checked: row.checked
                    onToggled: repoSyncModel.toggle_checked(row.index)
                }
                Controls.MaterialIcon {
                    name: row.phase === "failed" ? "priority_high"
                        : row.phase === "cancelled" ? "cancel"
                        : row.phase === "completed"
                            ? "check_circle" : "repository-sync"
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
                        font.pointSize: Controls.Typography.body
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
                        font.pointSize: Controls.Typography.label
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: row.localPath
                        visible: text.length > 0
                        color: root.theme.secondaryText
                        opacity: 0.72
                        font.family: "Consolas"
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideMiddle
                        Controls.ToolTip {
                            theme: root.theme
                            visible: rowMouse.containsMouse
                                && !root.theme.suppressToolTips
                            text: row.localPath
                        }
                    }
                }
                Label {
                    text: root.phaseLabel(row.phase, row.alreadyExists)
                    color: row.phase === "failed" ? root.theme.red
                        : row.phase === "completed" ? root.theme.green
                        : root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.DemiBold
                }
                Label {
                    text: row.speed
                    color: root.theme.secondaryText
                    font.family: "Consolas"
                    font.pointSize: Controls.Typography.caption
                }
                Controls.CompactIconButton {
                    visible: row.phase === "failed"
                        || row.phase === "cancelled"
                    theme: root.theme
                    round: true
                    iconName: "refresh"
                    toolTip: qsTr("Retry")
                    onClicked: repositorySync.retry_row(row.index)
                }
                Controls.CompactIconButton {
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
        ScrollBar.vertical: Controls.ScrollBar {
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
            ? root.discoveryStatusText()
            : repositorySync.discovery_state === "failed"
                ? repositorySync.discovery_error
                : repositorySync.batch_file_count > 0
                    ? qsTr("Completed rows were cleared; the batch summary is retained")
                    : qsTr("Repository Sync queue is empty")
        color: repositorySync.discovery_state === "failed"
            ? root.theme.red : root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.body
    }

    Controls.DockWorkspaceFooter {
        id: footer
        theme: root.theme
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        Label {
            anchors.left: parent.left
            anchors.leftMargin: 11
            anchors.verticalCenter: parent.verticalCenter
            text: repositorySync.active_count > 0
                ? qsTr("Background transfers are active — the interface remains responsive")
                : repositorySync.failed_file_count > 0
                    ? repositorySync.failed_file_count + qsTr(" failed downloads")
                    : qsTr("Files are verified before downloading and written atomically")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
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
