import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    required property var theme
    property bool namingPreviewExpanded: false
    FileDialog {
        id: operationPreviewDialog
        title: qsTr("Choose operation previews")
        fileMode: FileDialog.OpenFiles
        nameFilters: [
            "Images (*.apng *.avif *.bmp *.gif *.ico *.jpg *.jpeg *.png *.svg *.tga *.tif *.tiff *.webp)"
        ]
        onAccepted: commitQueueController.add_selected_previews(
            operationPreviewDialog.selectedFiles
        )
    }
    function statusColor(status) {
        if (status === "Completed")
            return theme.green
        if (status === "Failed" || status === "Invalid")
            return theme.error
        if (status === "Running" || status === "Queued")
            return theme.action
        if (status === "Cancelled")
            return theme.yellow
        return theme.secondaryText
    }
    function statusIcon(status) {
        if (status === "Completed")
            return "check_circle"
        if (status === "Failed" || status === "Invalid")
            return "error"
        if (status === "Running" || status === "Queued")
            return "sync"
        if (status === "Cancelled")
            return "cancel"
        if (status === "Validating" || status === "Needs validation")
            return "hourglass_top"
        return "inventory_2"
    }
    function fileName(path) {
        const normalized = String(path || "").replace(/\\/g, "/")
        return normalized.substring(normalized.lastIndexOf("/") + 1)
    }
    function fileExtension(path) {
        const name = fileName(path)
        const position = name.lastIndexOf(".")
        return position > 0 ? name.substring(position + 1).toUpperCase() : "FILE"
    }
    function fileIcon(path) {
        const extension = fileExtension(path).toLowerCase()
        if (["png", "jpg", "jpeg", "webp", "gif", "tif", "tiff", "bmp"].indexOf(extension) >= 0)
            return "image"
        if (["zip", "rar", "7z", "tar", "gz"].indexOf(extension) >= 0)
            return "archive"
        if (["mov", "mp4", "avi", "mkv", "webm"].indexOf(extension) >= 0)
            return "movie"
        return "draft"
    }
    function repositoryIndex(records, code) {
        const repositoryCode = String(code || "")
        for (let index = 0; index < records.length; ++index) {
            if (String(records[index].code || "") === repositoryCode)
                return index
        }
        return -1
    }
    component SectionLabel: Label {
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        font.weight: Font.DemiBold
        font.letterSpacing: 0.5
    }
    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }
    SplitView {
        id: mainSplit
        anchors.fill: parent
        anchors.margins: 10
        orientation: Qt.Horizontal
        handle: Rectangle {
            implicitWidth: 10
            color: "transparent"
            Rectangle {
                anchors.centerIn: parent
                width: 1
                height: Math.max(0, parent.height - 18)
                color: root.theme.outlineVariant
            }
        }
        Rectangle {
            id: filesDock
            objectName: "commitQueueFilesDock"
            SplitView.preferredWidth: Math.max(300, Math.min(360, root.width * 0.36))
            SplitView.minimumWidth: 270
            SplitView.maximumWidth: Math.max(380, root.width * 0.52)
            readonly property bool compactActions: width < 410
            color: root.theme.panelDeep
            radius: root.theme.surfaceRadius
            border.width: 1
            border.color: root.theme.outlineVariant
            clip: true
            property var record: commitQueueController.selectedRecord
            property real filesPanelHeight: commitQueueController.filesPanelHeight
            ColumnLayout {
                anchors.fill: parent
                spacing: 0
                ColumnLayout {
                    objectName: "commitQueueToolbar"
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Layout.preferredHeight: 46
                    Layout.leftMargin: 7
                    Layout.rightMargin: 5
                    spacing: 0

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.preferredHeight: 46
                        spacing: 5

                        Controls.MaterialIcon {
                            visible: filesDock.width >= 330
                            name: "format_list_bulleted"
                            size: 16
                            color: root.theme.action
                        }
                        SectionLabel {
                            visible: filesDock.width >= 330
                            text: qsTr("QUEUE")
                        }
                        Rectangle {
                            implicitWidth: queueCount.implicitWidth + 14
                            implicitHeight: 22
                            radius: height / 2
                            color: root.theme.surfaceContainerHigh
                            Label {
                                id: queueCount
                                anchors.centerIn: parent
                                text: String(commitQueueController.count)
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.DemiBold
                            }
                        }
                        Item { Layout.fillWidth: true }
                        Controls.CompactIconButton {
                            objectName: "commitQueueHelpButton"
                            theme: root.theme
                            iconName: "help"
                            toolTip: qsTr("Help")
                            Accessible.name: toolTip
                            onClicked: windowModel.open_help("commit_queue")
                        }
                        Controls.Switch {
                            id: autoCleanSwitch
                            objectName: "commitQueueAutoCleanSwitch"
                            theme: root.theme
                            text: qsTr("Auto-clean")
                            Accessible.name: qsTr("Auto-clean")
                            checked: commitQueueController.autoClean
                            enabled: !commitQueueController.busy
                            onToggled: commitQueueController.set_auto_clean(checked)

                            Controls.ToolTip {
                                theme: root.theme
                                visible: autoCleanSwitch.hovered
                                    && !root.theme.suppressToolTips
                                text: qsTr("Auto-clean")
                            }
                        }
                        Controls.CompactIconButton {
                            objectName: "commitQueueMoveUpButton"
                            theme: root.theme
                            iconName: "arrow_upward"
                            toolTip: qsTr("Move operation up")
                            visible: commitQueueController.count > 1
                            enabled: !commitQueueController.busy
                                && commitQueueController.selectedRow > 0
                            onClicked: commitQueueController.move_selected(-1)
                        }
                        Controls.CompactIconButton {
                            objectName: "commitQueueMoveDownButton"
                            theme: root.theme
                            iconName: "arrow_downward"
                            toolTip: qsTr("Move operation down")
                            visible: commitQueueController.count > 1
                            enabled: !commitQueueController.busy
                                && commitQueueController.selectedRow >= 0
                                && commitQueueController.selectedRow < commitQueueController.count - 1
                            onClicked: commitQueueController.move_selected(1)
                        }
                        Controls.CompactIconButton {
                            objectName: "commitQueueClearCompletedButton"
                            theme: root.theme
                            iconName: "task_alt"
                            toolTip: qsTr("Clear completed")
                            visible: commitQueueController.hasCompleted
                            enabled: commitQueueController.hasCompleted
                                && !commitQueueController.busy
                            onClicked: commitQueueController.remove_completed()
                        }
                        Controls.CompactIconButton {
                            objectName: "commitQueueClearButton"
                            theme: root.theme
                            iconName: "delete_forever"
                            toolTip: qsTr("Clear queue")
                            visible: commitQueueController.count > 0
                            enabled: commitQueueController.count > 0
                                && !commitQueueController.busy
                            onClicked: clearQueueConfirmation.open()
                        }
                    }

                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.theme.outlineVariant
                }

                ListView {
                    id: queueList
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Layout.fillHeight: true
                    Layout.margins: 6
                    clip: true
                    spacing: 4
                    model: commitQueueModel
                    boundsBehavior: Flickable.StopAtBounds
                    reuseItems: true

                    delegate: Item {
                        id: queueRow
                        required property int index
                        required property string operationId
                        required property string title
                        required property string objectTitle
                        required property int fileCount
                        required property string summary
                        required property string context
                        required property string status
                        required property bool selected
                        required property bool checked
                        required property real progress
                        required property string stage
                        required property string error
                        required property bool canEdit
                        required property bool canCommit
                        required property url previewUrl
                        width: queueList.width
                        height: 68

                        Controls.ItemSurface {
                            anchors.fill: parent
                            theme: root.theme
                            selected: queueRow.selected
                            hovered: rowMouse.containsMouse
                            pressed: rowMouse.pressed
                            accent: root.statusColor(queueRow.status)
                            railVisible: queueRow.selected || queueRow.status !== "Prepared"
                            railWidth: 3
                            normalColor: root.theme.surfaceContainerLow
                            cornerRadius: root.theme.itemRadius
                            separatorVisible: false
                        }

                        MouseArea {
                            id: rowMouse
                            anchors.fill: parent
                            z: 1
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: commitQueueController.select_row(queueRow.index)
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 7
                            anchors.rightMargin: 5
                            anchors.topMargin: 6
                            anchors.bottomMargin: 6
                            spacing: 6
                            z: 2

                            Controls.CheckBox {
                                theme: root.theme
                                Layout.preferredWidth: 28
                                Layout.preferredHeight: 28
                                checked: queueRow.checked
                                enabled: queueRow.status !== "Running"
                                onClicked: commitQueueController.toggle_checked(queueRow.index)
                            }
                            Controls.ItemPreview {
                                theme: root.theme
                                Layout.preferredWidth: 38
                                Layout.preferredHeight: 38
                                previewSize: 38
                                source: queueRow.previewUrl
                                fallbackIcon: root.statusIcon(queueRow.status)
                                accent: root.statusColor(queueRow.status)
                                cornerRadius: 9
                                animateAppearance: false
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    Layout.fillWidth: true
                                    text: queueRow.title
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideMiddle
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: queueRow.objectTitle
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 2
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Label {
                                        text: queueRow.fileCount
                                            + (queueRow.fileCount === 1
                                                ? qsTr(" file") : qsTr(" files"))
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                    }
                                    Rectangle {
                                        Layout.preferredWidth: 3
                                        Layout.preferredHeight: 3
                                        radius: 2
                                        color: root.theme.secondaryText
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: queueRow.error || queueRow.context
                                            || qsTr("No context")
                                        color: queueRow.error ? root.theme.error : root.statusColor(queueRow.status)
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                            Controls.CompactIconButton {
                                Layout.preferredWidth: 28
                                Layout.preferredHeight: 28
                                visible: rowMouse.containsMouse || queueRow.selected
                                theme: root.theme
                                round: true
                                iconName: "close"
                                iconSize: 13
                                toolTip: qsTr("Remove operation")
                                enabled: queueRow.status !== "Running"
                                onClicked: commitQueueController.remove_row(queueRow.index)
                            }
                        }

                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            anchors.leftMargin: 9
                            anchors.rightMargin: 9
                            height: queueRow.status === "Running" ? 3 : 0
                            radius: height / 2
                            color: root.theme.surfaceContainerHighest
                            Rectangle {
                                width: parent.width * Math.max(0, Math.min(1, queueRow.progress))
                                height: parent.height
                                radius: parent.radius
                                color: root.theme.action
                                Behavior on width {
                                    NumberAnimation {
                                        duration: root.theme.hoverMotionFast
                                        easing.type: Easing.OutCubic
                                    }
                                }
                            }
                        }
                    }

                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: queueList
                    }

                    Controls.EmptyState {
                        anchors.centerIn: parent
                        width: Math.min(Math.max(0, parent.width - 28), 280)
                        visible: commitQueueController.count === 0
                        theme: root.theme
                        iconName: "inventory_2"
                        title: qsTr("Queue is empty")
                        message: qsTr("Prepared operations from Save Snapshot or Drop Plate will appear here.")
                    }
                }

                Item {
                    id: filesResizeHandle
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? 8 : 0
                    visible: Boolean(filesDock.record.sourceFiles
                        && filesDock.record.sourceFiles.length > 0)
                        && commitQueueController.selectedRow >= 0

                    Rectangle {
                        anchors.centerIn: parent
                        width: 34
                        height: 2
                        radius: 1
                        color: filesResizeMouse.containsMouse
                            ? root.theme.action : root.theme.outlineVariant
                    }
                    MouseArea {
                        id: filesResizeMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.SizeVerCursor
                        property real pressedRootY: 0
                        property real startHeight: 0
                        function rootY(mouse) {
                            return mapToItem(root, mouse.x, mouse.y).y
                        }
                        onPressed: function(mouse) {
                            pressedRootY = rootY(mouse)
                            startHeight = filesPanel.height
                        }
                        onPositionChanged: function(mouse) {
                            if (!pressed)
                                return
                            const delta = rootY(mouse) - pressedRootY
                            filesDock.filesPanelHeight = Math.max(
                                100, Math.min(filesDock.height * 0.58,
                                    startHeight - delta))
                        }
                        onReleased: commitQueueController.set_files_panel_height(
                            filesDock.filesPanelHeight
                        )
                    }
                }

                Rectangle {
                    id: filesPanel
                    objectName: "commitQueueFilesPanel"
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    visible: commitQueueController.selectedRow >= 0
                    Layout.preferredHeight: filesDock.record.sourceFiles
                        && filesDock.record.sourceFiles.length > 0
                        ? filesDock.filesPanelHeight : 82
                    color: root.theme.panel
                    radius: root.theme.surfaceRadius
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            Layout.preferredHeight: 36
                            Layout.leftMargin: 11
                            Layout.rightMargin: 10
                            spacing: 6
                            Controls.MaterialIcon {
                                name: "attach_file"
                                size: 15
                                color: root.theme.action
                            }
                            SectionLabel { text: qsTr("FILES") }
                            Item { Layout.fillWidth: true }
                            Label {
                                text: filesDock.record.fileCount
                                    ? String(filesDock.record.fileCount) : "0"
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: root.theme.outlineVariant
                        }
                        ListView {
                            id: selectedFiles
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            Layout.fillHeight: true
                            Layout.leftMargin: 6
                            Layout.rightMargin: 6
                            Layout.bottomMargin: 5
                            clip: true
                            spacing: 2
                            model: filesDock.record.sourceFiles || []
                            boundsBehavior: Flickable.StopAtBounds

                            delegate: Item {
                                id: fileRow
                                required property int index
                                required property var modelData
                                readonly property string sourcePath: String(modelData || "")
                                readonly property string targetPath: filesDock.record.versionedPaths
                                    && index < filesDock.record.versionedPaths.length
                                    ? String(filesDock.record.versionedPaths[index] || "") : ""
                                width: selectedFiles.width
                                height: targetPath.length > 0 ? 43 : 32

                                HoverHandler { id: fileHover }

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 6
                                    anchors.rightMargin: 6
                                    spacing: 7
                                    Rectangle {
                                        Layout.preferredWidth: 26
                                        Layout.preferredHeight: 26
                                        radius: 8
                                        color: root.theme.surfaceContainerHigh
                                        Controls.MaterialIcon {
                                            anchors.centerIn: parent
                                            name: root.fileIcon(fileRow.sourcePath)
                                            size: 15
                                            color: root.theme.action
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 0
                                        Label {
                                            Layout.fillWidth: true
                                            text: root.fileName(fileRow.sourcePath)
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.label
                                            elide: Text.ElideMiddle
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            visible: fileRow.targetPath.length > 0
                                            text: fileRow.targetPath
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.micro
                                            elide: Text.ElideMiddle
                                        }
                                    }
                                    Label {
                                        text: root.fileExtension(fileRow.sourcePath)
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.micro
                                        font.weight: Font.DemiBold
                                    }
                                    Controls.CompactIconButton {
                                        Layout.preferredWidth: 26
                                        Layout.preferredHeight: 26
                                        theme: root.theme
                                        round: true
                                        iconName: "close"
                                        iconSize: 12
                                        toolTip: qsTr("Remove file from this operation")
                                        visible: fileHover.hovered
                                        enabled: Boolean(filesDock.record.canEdit)
                                            && !commitQueueController.busy
                                        onClicked: commitQueueController.remove_selected_file(
                                            fileRow.index
                                        )
                                    }
                                }
                            }
                            ScrollBar.vertical: Controls.ScrollBar {
                                theme: root.theme
                                flickableTarget: selectedFiles
                            }
                            Label {
                                anchors.centerIn: parent
                                visible: selectedFiles.count === 0
                                text: commitQueueController.selectedRow < 0
                                    ? qsTr("Select an operation")
                                    : qsTr("No files")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                            }
                        }
                    }
                }
            }
        }

        Item {
            id: detailsPanel
            objectName: "commitQueueDetailsPanel"
            SplitView.fillWidth: true
            SplitView.minimumWidth: 410
            readonly property bool compactActions: width < 620
            readonly property bool hasSelection:
                commitQueueController.selectedRow >= 0
            property var record: commitQueueController.selectedRecord

            Controls.EmptyState {
                objectName: "commitQueueWelcomeState"
                anchors.centerIn: parent
                width: Math.min(Math.max(0, parent.width - 48), 440)
                visible: !detailsPanel.hasSelection
                theme: root.theme
                iconName: commitQueueController.count > 0
                    ? "format_list_bulleted" : "publish"
                title: commitQueueController.count > 0
                    ? qsTr("Select an operation")
                    : qsTr("Ready for operations")
                message: commitQueueController.count > 0
                    ? qsTr("Select an operation in the queue to review its files and settings.")
                    : qsTr("Add files through Save Snapshot or Drop Plate. You can review every prepared operation before sending it.")
            }

            ColumnLayout {
                anchors.fill: parent
                visible: detailsPanel.hasSelection
                spacing: 8

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: duplicateLayout.implicitHeight + 18
                    visible: commitQueueController.duplicatePending
                    radius: root.theme.surfaceRadius
                    color: root.theme.tertiaryContainer
                    border.width: 1
                    border.color: root.theme.tertiary

                    RowLayout {
                        id: duplicateLayout
                        anchors.fill: parent
                        anchors.margins: 9
                        spacing: 7
                        Controls.MaterialIcon {
                            name: "content_copy"
                            size: 17
                            color: root.theme.tertiary
                        }
                        Label {
                            Layout.fillWidth: true
                            text: commitQueueController.duplicateDescription
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            wrapMode: Text.WordWrap
                        }
                        Controls.Button {
                            theme: root.theme
                            text: qsTr("Replace")
                            tonal: true
                            onClicked: commitQueueController.resolve_duplicate("replace")
                        }
                        Controls.Button {
                            theme: root.theme
                            text: qsTr("Add another")
                            onClicked: commitQueueController.resolve_duplicate("add")
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            toolTip: qsTr("Ignore duplicate")
                            onClicked: commitQueueController.resolve_duplicate("ignore")
                        }
                    }
                }

                Flickable {
                    id: editorScroll
                    objectName: "commitQueueEditorScroll"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: width
                    contentHeight: editorFields.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    ColumnLayout {
                        id: editorFields
                        width: editorScroll.width
                        spacing: 8
                        enabled: commitQueueController.selectedRow >= 0

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: batchEditContent.implicitHeight + 16
                            visible: commitQueueController.count > 1
                            radius: root.theme.itemRadius
                            color: commitQueueController.applyToChecked
                                ? root.theme.secondaryContainer
                                : root.theme.surfaceContainerLow

                            RowLayout {
                                id: batchEditContent
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 8
                                Controls.CheckBox {
                                    theme: root.theme
                                    checked: commitQueueController.applyToChecked
                                    enabled: !commitQueueController.busy
                                    text: qsTr("Apply every edit to checked items")
                                    onClicked: commitQueueController.set_apply_to_checked(checked)
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("The current item and all ")
                                        + commitQueueController.checkedCount
                                        + qsTr(" checked rows receive every change made below.")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                        }

                        CommitQueueOperationSummary {
                            Layout.fillWidth: true
                            theme: root.theme
                            record: detailsPanel.record
                            compact: detailsPanel.compactActions
                            busy: commitQueueController.busy
                            clipboardHasImage:
                                screenshotController.clipboardHasImage
                            statusText: detailsPanel.record.status === "Prepared"
                                ? qsTr("Ready to send")
                                : qsTr(detailsPanel.record.status || "Prepared")
                            statusIcon: root.statusIcon(
                                detailsPanel.record.status || "Prepared")
                            statusAccent: detailsPanel.record.status === "Prepared"
                                ? root.theme.green
                                : root.statusColor(
                                    detailsPanel.record.status || "Prepared")
                            onPreviewRequested: function(hasPreviews) {
                                if (hasPreviews)
                                    operationPreviewList.open()
                                else
                                    operationPreviewDialog.open()
                            }
                            onMoreRequested: function(sourceItem) {
                                queueActionMenus.openPreviewBelow(sourceItem)
                            }
                            onActionRequested: function(command) {
                                if (command === "capture") {
                                    screenshotController.prepare_for_operation(
                                        commitQueueController.selectedId)
                                    windowModel.show_child_window(
                                        "screenshot_maker", "commit_queue")
                                } else if (command === "choose") {
                                    operationPreviewDialog.open()
                                } else if (command === "paste") {
                                    screenshotController.paste_preview_from_clipboard(
                                        commitQueueController.selectedId)
                                } else if (command === "manage") {
                                    operationPreviewList.open()
                                } else if (command === "clear") {
                                    commitQueueController.clear_selected_previews()
                                }
                            }
                            onContextBranchEdited: branch =>
                                commitQueueController.update_selected_context_branch(
                                    branch)
                        }

                        Rectangle {
                            objectName: "commitQueuePrimarySettings"
                            Layout.fillWidth: true
                            Layout.preferredHeight: destinationContent.implicitHeight + 22
                            radius: root.theme.surfaceRadius
                            topLeftRadius: radius
                            topRightRadius: radius
                            bottomLeftRadius: 0
                            bottomRightRadius: 0
                            color: root.theme.surfaceContainerLow

                            ColumnLayout {
                                id: destinationContent
                                anchors.fill: parent
                                anchors.margins: 11
                                spacing: 10
                                SectionLabel { text: qsTr("BASIC") }
                                DescriptionEditor {
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 72
                                    managed: false
                                    compact: true
                                    editorEnabled: Boolean(detailsPanel.record.canEdit)
                                    value: detailsPanel.record.description || ""
                                    onEditingFinished: value =>
                                        commitQueueController.update_selected(
                                            "description", value
                                        )
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 1
                                    color: root.theme.outlineVariant
                                }
                                Rectangle {
                                    objectName: "commitQueueAdvancedToggle"
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 44
                                    radius: root.theme.itemRadius
                                    color: advancedTap.pressed
                                        ? root.theme.rowPressed
                                        : advancedHover.hovered
                                            ? root.theme.rowHover : "transparent"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 4
                                        anchors.rightMargin: 6
                                        spacing: 8
                                        Controls.MaterialIcon {
                                            name: commitQueueController.advancedOptionsExpanded
                                                ? "expand_more" : "chevron_right"
                                            size: 18
                                            color: root.theme.primaryText
                                        }
                                        Label {
                                            text: qsTr("Advanced options")
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.body
                                            font.weight: Font.DemiBold
                                        }
                                        Item { Layout.fillWidth: true }
                                    }
                                    HoverHandler {
                                        id: advancedHover
                                        cursorShape: Qt.PointingHandCursor
                                    }
                                    Controls.ActivationHandler {
                                        id: advancedTap
                                        onActivated: commitQueueController.set_advanced_options_expanded(
                                            !commitQueueController.advancedOptionsExpanded)
                                    }
                                }
                                GridLayout {
                                    id: destinationGrid
                                    Layout.fillWidth: true
                                    visible: commitQueueController.advancedOptionsExpanded
                                    columns: width >= 690 ? 4 : 2
                                    rowSpacing: 7
                                    columnSpacing: 9
                                    Label {
                                        text: qsTr("Repository")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.label
                                    }
                                    Controls.ComboBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        model: commitQueueController.repositories
                                        textRole: "title"
                                        valueRole: "code"
                                        translateDisplayText: false
                                        currentIndex: root.repositoryIndex(
                                            model,
                                            detailsPanel.record.repository || ""
                                        )
                                        onActivated: commitQueueController.update_selected(
                                            "repository", currentValue)
                                    }
                                    Label {
                                        text: qsTr("Version")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.label
                                    }
                                    Controls.TextField {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        text: detailsPanel.record.version > 0
                                            ? String(detailsPanel.record.version) : ""
                                        validator: IntValidator { bottom: 0; top: 9999 }
                                        onEditingFinished: commitQueueController.update_selected("version", text.length ? Number(text) : 0)
                                    }
                                    Label {
                                        text: qsTr("Method")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.label
                                    }
                                    Controls.ComboBox {
                                        id: methodCombo
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        readonly property var values: ["preallocate", "inplace", "copy", "move", "upload"]
                                        model: ["Preallocate", "In-Place", "Copy", "Move", "Upload"]
                                        currentIndex: Math.max(0, values.indexOf(detailsPanel.record.mode || "upload"))
                                        onActivated: commitQueueController.update_selected("mode", values[currentIndex])
                                    }
                                    Label {
                                        text: qsTr("Filename")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.label
                                    }
                                    Controls.TextField {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        Layout.columnSpan: destinationGrid.width >= 690 ? 3 : 1
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                            && !Boolean(detailsPanel.record.contextAsFilename)
                                        text: detailsPanel.record.explicitFilename || ""
                                        placeholderText: qsTr("Generated by naming rules")
                                        onEditingFinished: commitQueueController.update_selected("explicitFilename", text)
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: optionsContent.implicitHeight + 22
                            Layout.topMargin: -8
                            visible: commitQueueController.advancedOptionsExpanded
                            radius: 0
                            color: root.theme.surfaceContainerLow

                            ColumnLayout {
                                id: optionsContent
                                anchors.fill: parent
                                anchors.leftMargin: 11
                                anchors.rightMargin: 11
                                spacing: 6
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 1
                                    color: root.theme.outlineVariant
                                }
                                SectionLabel { text: qsTr("FILE OPTIONS") }
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: width >= 560 ? 2 : 1
                                    rowSpacing: 2
                                    columnSpacing: 12
                                    Controls.CheckBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        text: qsTr("Update versionless")
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                            && !detailsPanel.record.keepFileName
                                        checked: Boolean(detailsPanel.record.updateVersionless)
                                        onClicked: commitQueueController.update_selected("updateVersionless", checked)
                                    }
                                    Controls.CheckBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        text: qsTr("Commit versionless only")
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        checked: Boolean(detailsPanel.record.onlyVersionless)
                                        onClicked: commitQueueController.update_selected("onlyVersionless", checked)
                                    }
                                    Controls.CheckBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        text: qsTr("Keep source filename")
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        checked: Boolean(detailsPanel.record.keepFileName)
                                        onClicked: commitQueueController.update_selected("keepFileName", checked)
                                    }
                                    Controls.CheckBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        text: qsTr("Use context as filename")
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        checked: Boolean(detailsPanel.record.contextAsFilename)
                                        onClicked: commitQueueController.update_selected("contextAsFilename", checked)
                                    }
                                    Controls.CheckBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        text: qsTr("Generate previews")
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        checked: Boolean(detailsPanel.record.generatePreviews)
                                        onClicked: commitQueueController.update_selected("generatePreviews", checked)
                                    }
                                }
                            }
                        }

                        Rectangle {
                            objectName: "commitQueueNamingSection"
                            Layout.fillWidth: true
                            Layout.preferredHeight: namingContent.implicitHeight + 22
                            Layout.topMargin: -8
                            radius: root.theme.surfaceRadius
                            topLeftRadius: 0
                            topRightRadius: 0
                            bottomLeftRadius: radius
                            bottomRightRadius: radius
                            color: root.theme.surfaceContainerLow

                            ColumnLayout {
                                id: namingContent
                                anchors.fill: parent
                                anchors.margins: 11
                                spacing: 7

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 1
                                    color: root.theme.outlineVariant
                                }
                                Rectangle {
                                    objectName: "commitQueueNamingToggle"
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 44
                                    radius: root.theme.itemRadius
                                    color: namingTap.pressed
                                        ? root.theme.rowPressed
                                        : namingHover.hovered
                                            ? root.theme.rowHover : "transparent"

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 4
                                        anchors.rightMargin: 6
                                        spacing: 8

                                        Item {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true

                                            RowLayout {
                                                anchors.fill: parent
                                                spacing: 8
                                                Controls.MaterialIcon {
                                                    name: root.namingPreviewExpanded
                                                        ? "expand_more"
                                                        : "chevron_right"
                                                    size: 18
                                                    color: root.theme.primaryText
                                                }
                                                Label {
                                                    objectName: "commitQueueNamingFileName"
                                                    Layout.fillWidth: true
                                                    text: detailsPanel.record.futureFileName
                                                        || detailsPanel.record.title
                                                        || qsTr("Waiting for filename")
                                                    color: root.theme.primaryText
                                                    font.family: root.theme.fontFamily
                                                    font.pointSize: Controls.Typography.body
                                                    font.weight: Font.DemiBold
                                                    elide: Text.ElideMiddle
                                                }
                                            }

                                            HoverHandler {
                                                id: namingHover
                                                cursorShape: Qt.PointingHandCursor
                                            }
                                            Controls.ActivationHandler {
                                                id: namingTap
                                                onActivated: root.namingPreviewExpanded =
                                                    !root.namingPreviewExpanded
                                            }
                                        }

                                        Controls.CompactIconButton {
                                            theme: root.theme
                                            iconName: "drive_file_rename_outline"
                                            toolTip: qsTr("Naming Editor")
                                            onClicked: {
                                                namingEditorController.prepare_operation(
                                                    commitQueueController.selectedId
                                                )
                                                windowModel.show_window("naming_editor")
                                            }
                                        }
                                    }
                                }

                                Loader {
                                    objectName: "commitQueueNamingDetails"
                                    Layout.fillWidth: true
                                    active: root.namingPreviewExpanded
                                    visible: active
                                    sourceComponent: ColumnLayout {
                                        spacing: 5

                                        Repeater {
                                            model: detailsPanel.record.sourceFiles || []
                                            delegate: Rectangle {
                                                required property int index
                                                required property var modelData
                                                objectName: "commitQueueNamingPreviewRow_" + index
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: namingRow.implicitHeight + 12
                                                radius: root.theme.itemRadius
                                                color: root.theme.surfaceContainerHigh

                                                ColumnLayout {
                                                    id: namingRow
                                                    anchors.fill: parent
                                                    anchors.margins: 6
                                                    spacing: 2
                                                    Label {
                                                        Layout.fillWidth: true
                                                        text: root.fileName(modelData)
                                                        color: root.theme.primaryText
                                                        font.family: root.theme.fontFamily
                                                        font.pointSize: Controls.Typography.label
                                                        font.weight: Font.DemiBold
                                                        elide: Text.ElideMiddle
                                                    }
                                                    Label {
                                                        Layout.fillWidth: true
                                                        text: qsTr("Versioned  ") + (
                                                            detailsPanel.record.versionedPaths
                                                            && index < detailsPanel.record.versionedPaths.length
                                                            && detailsPanel.record.versionedPaths[index]
                                                            ? detailsPanel.record.versionedPaths[index]
                                                            : qsTr("Waiting for naming preview")
                                                        )
                                                        color: root.theme.secondaryText
                                                        font.family: root.theme.fontFamily
                                                        font.pointSize: Controls.Typography.caption
                                                        elide: Text.ElideMiddle
                                                    }
                                                    Label {
                                                        Layout.fillWidth: true
                                                        text: qsTr("Versionless  ") + (
                                                            detailsPanel.record.versionlessPaths
                                                            && index < detailsPanel.record.versionlessPaths.length
                                                            && detailsPanel.record.versionlessPaths[index]
                                                            ? detailsPanel.record.versionlessPaths[index]
                                                            : qsTr("Not generated")
                                                        )
                                                        color: root.theme.secondaryText
                                                        font.family: root.theme.fontFamily
                                                        font.pointSize: Controls.Typography.caption
                                                        elide: Text.ElideMiddle
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: messageRow.implicitHeight + 16
                            visible: commitQueueController.selectedRow >= 0
                                && Boolean(detailsPanel.record.error
                                    || (detailsPanel.record.stage
                                        && detailsPanel.record.stage !== "prepared"))
                            radius: root.theme.itemRadius
                            color: detailsPanel.record.error
                                ? root.theme.errorContainer : root.theme.surfaceContainerLow

                            RowLayout {
                                id: messageRow
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 7
                                Controls.MaterialIcon {
                                    name: detailsPanel.record.error ? "error" : "info"
                                    size: 16
                                    color: detailsPanel.record.error
                                        ? root.theme.error : root.theme.action
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: detailsPanel.record.error
                                        ? detailsPanel.record.error
                                        : detailsPanel.record.stage
                                    color: detailsPanel.record.error
                                        ? root.theme.error : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }

                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: editorScroll
                    }
                }

                Rectangle {
                    objectName: "commitQueueActionFooter"
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Layout.preferredHeight: 52
                    radius: root.theme.surfaceRadius
                    color: root.theme.surfaceContainerLow

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        spacing: 6
                        Label {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            text: commitQueueController.busy
                                ? (detailsPanel.record.stage || qsTr("Working"))
                                : commitQueueController.count === 0
                                    ? qsTr("Add files from Save Snapshot or Drop Plate")
                                    : commitQueueController.count
                                        + (commitQueueController.count === 1
                                            ? qsTr(" queue item")
                                            : qsTr(" queue items"))
                                        + "  ·  " + qsTr("Ready to send")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            elide: Text.ElideRight
                        }
                        Controls.Button {
                            theme: root.theme
                            text: qsTr("Retry")
                            toolTip: qsTr("Retry")
                            icon.name: "refresh"
                            compact: detailsPanel.compactActions
                            visible: detailsPanel.record.status === "Failed"
                            enabled: !commitQueueController.busy
                            onClicked: commitQueueController.retry_current()
                        }
                        Controls.Button {
                            theme: root.theme
                            text: qsTr("Cancel")
                            toolTip: qsTr("Cancel")
                            icon.name: "stop"
                            compact: detailsPanel.compactActions
                            visible: commitQueueController.busy
                            destructive: true
                            onClicked: commitQueueController.cancel()
                        }
                        Controls.Button {
                            objectName: "commitQueuePrimarySendButton"
                            theme: root.theme
                            text: qsTr("Commit all")
                            toolTip: qsTr("Commit all")
                            icon.name: "publish"
                            compact: false
                            highlighted: enabled
                            enabled: commitQueueController.hasReady
                                && !commitQueueController.busy
                            onClicked: commitQueueController.commit_all()
                        }
                        Controls.CompactIconButton {
                            id: sendOverflowButton
                            objectName: "commitQueueSendOverflowButton"
                            theme: root.theme
                            iconName: "more_vert"
                            toolTip: qsTr("More send actions")
                            visible: true
                            enabled: !commitQueueController.busy
                            onClicked: queueActionMenus.openSendBelow(
                                sendOverflowButton)
                        }
                    }
                }
            }
        }
    }

    CommitQueueActionMenus {
        id: queueActionMenus
        theme: root.theme
        commitQueue: commitQueueController
        screenshot: screenshotController
        windows: windowModel
        selectedRecord: detailsPanel.record
        onChoosePreviewRequested: operationPreviewDialog.open()
        onManagePreviewRequested: operationPreviewList.open()
    }

    Controls.Dialog {
        id: operationPreviewList
        theme: root.theme
        modal: false
        anchors.centerIn: parent
        width: Math.min(520, root.width - 32)
        height: Math.min(460, root.height - 32)
        title: qsTr("Operation previews")

        contentItem: ListView {
            id: previewList
            implicitWidth: operationPreviewList.width - 40
            implicitHeight: operationPreviewList.height - 130
            model: commitQueueController.selectedRecord.previewFiles || []
            spacing: 6
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                required property int index
                required property var modelData
                width: previewList.width
                height: 58
                radius: root.theme.itemRadius
                color: root.theme.surfaceContainerHigh

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 6
                    spacing: 8
                    Controls.ItemPreview {
                        theme: root.theme
                        Layout.preferredWidth: 46
                        Layout.preferredHeight: 46
                        previewSize: 46
                        source: commitQueueController.selectedRecord.previewUrls[index] || ""
                        accent: root.theme.action
                        animateAppearance: false
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.fileName(modelData)
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        elide: Text.ElideMiddle
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        iconName: "close"
                        toolTip: qsTr("Remove preview")
                        enabled: Boolean(commitQueueController.selectedRecord.canEdit)
                        onClicked: commitQueueController.remove_selected_preview(index)
                    }
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: previewList
            }
        }

        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Add images")
                icon.name: "add_photo_alternate"
                DialogButtonBox.buttonRole: DialogButtonBox.ActionRole
                onClicked: operationPreviewDialog.open()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Paste image")
                icon.name: "content_paste"
                enabled: screenshotController.clipboardHasImage
                DialogButtonBox.buttonRole: DialogButtonBox.ActionRole
                onClicked: screenshotController.paste_preview_from_clipboard(
                    commitQueueController.selectedId
                )
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Close")
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }

    Controls.Dialog {
        id: clearQueueConfirmation
        objectName: "commitQueueClearConfirmation"
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(420, root.width - 32)
        title: qsTr("Clear commit queue?")

        contentItem: Label {
            objectName: "commitQueueClearMessage"
            width: clearQueueConfirmation.width
                - clearQueueConfirmation.leftPadding
                - clearQueueConfirmation.rightPadding
            text: qsTr("All prepared, failed and completed operations will be removed from the queue.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }

        footer: Controls.DialogActions {
            objectName: "commitQueueClearActions"
            theme: root.theme
            horizontalMargin: 20
            verticalMargin: 16
            Controls.Button {
                objectName: "commitQueueClearCancelButton"
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                onClicked: clearQueueConfirmation.reject()
            }
            Controls.Button {
                objectName: "commitQueueClearAcceptButton"
                theme: root.theme
                text: qsTr("Clear queue")
                icon.name: "delete_forever"
                destructive: true
                onClicked: clearQueueConfirmation.accept()
            }
        }

        onAccepted: commitQueueController.clear()
    }
}
