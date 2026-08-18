import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

import "controls"

Item {
    id: root
    required property var theme
    property bool namingPreviewExpanded: true

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

    component SectionLabel: Label {
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Typography.label
        font.weight: Font.DemiBold
        font.letterSpacing: 0.5
    }

    Rectangle {
        anchors.fill: parent
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
            SplitView.preferredWidth: Math.max(300, Math.min(360, root.width * 0.36))
            SplitView.minimumWidth: 270
            SplitView.maximumWidth: Math.max(380, root.width * 0.52)
            color: root.theme.panelDeep
            radius: root.theme.surfaceRadius
            border.width: 1
            border.color: root.theme.outlineVariant

            property var record: commitQueueController.selectedRecord
            property real filesPanelHeight: commitQueueController.filesPanelHeight

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 78
                    Layout.leftMargin: 11
                    Layout.rightMargin: 6
                    spacing: 0

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        spacing: 5

                        MaterialIcon {
                            name: "format_list_bulleted"
                            size: 16
                            color: root.theme.action
                        }
                        SectionLabel { text: qsTr("QUEUE") }
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
                                font.pointSize: Typography.caption
                                font.weight: Font.DemiBold
                            }
                        }
                        Item { Layout.fillWidth: true }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "arrow_upward"
                            toolTip: qsTr("Move operation up")
                            enabled: !commitQueueController.busy
                                && commitQueueController.selectedRow > 0
                            onClicked: commitQueueController.move_selected(-1)
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "arrow_downward"
                            toolTip: qsTr("Move operation down")
                            enabled: !commitQueueController.busy
                                && commitQueueController.selectedRow >= 0
                                && commitQueueController.selectedRow < commitQueueController.count - 1
                            onClicked: commitQueueController.move_selected(1)
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "delete_forever"
                            toolTip: qsTr("Clear queue")
                            enabled: commitQueueController.count > 0
                                && !commitQueueController.busy
                            onClicked: clearQueueConfirmation.open()
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        spacing: 6

                        Md3Switch {
                            theme: root.theme
                            text: qsTr("Auto-clean")
                            checked: commitQueueController.autoClean
                            enabled: !commitQueueController.busy
                            onToggled: commitQueueController.set_auto_clean(checked)
                        }
                        Item { Layout.fillWidth: true }
                        Md3Button {
                            theme: root.theme
                            text: qsTr("Clear completed")
                            icon.name: "task_alt"
                            enabled: commitQueueController.hasCompleted
                                && !commitQueueController.busy
                            onClicked: commitQueueController.remove_completed()
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

                        ItemSurface {
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

                            Md3CheckBox {
                                theme: root.theme
                                Layout.preferredWidth: 28
                                Layout.preferredHeight: 28
                                checked: queueRow.checked
                                enabled: queueRow.status !== "Running"
                                onClicked: commitQueueController.toggle_checked(queueRow.index)
                            }
                            ItemPreview {
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
                                    font.pointSize: Typography.body
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideMiddle
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: queueRow.objectTitle
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.caption
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
                                        font.pointSize: Typography.caption
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
                                        font.pointSize: Typography.caption
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                            CompactIconButton {
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
                                        duration: root.theme.motionFast
                                        easing.type: Easing.OutCubic
                                    }
                                }
                            }
                        }
                    }

                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: queueList
                    }

                    Column {
                        anchors.centerIn: parent
                        visible: commitQueueController.count === 0
                        spacing: 7
                        MaterialIcon {
                            anchors.horizontalCenter: parent.horizontalCenter
                            name: "inventory_2"
                            size: 28
                            color: root.theme.disabledText
                        }
                        Label {
                            text: qsTr("Queue is empty")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.label
                        }
                    }
                }

                Item {
                    id: filesResizeHandle
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? 8 : 0
                    visible: Boolean(filesDock.record.sourceFiles
                        && filesDock.record.sourceFiles.length > 0)

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
                    Layout.fillWidth: true
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
                            Layout.preferredHeight: 36
                            Layout.leftMargin: 11
                            Layout.rightMargin: 10
                            spacing: 6
                            MaterialIcon {
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
                                font.pointSize: Typography.caption
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
                                        MaterialIcon {
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
                                            font.pointSize: Typography.label
                                            elide: Text.ElideMiddle
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            visible: fileRow.targetPath.length > 0
                                            text: fileRow.targetPath
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.micro
                                            elide: Text.ElideMiddle
                                        }
                                    }
                                    Label {
                                        text: root.fileExtension(fileRow.sourcePath)
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Typography.micro
                                        font.weight: Font.DemiBold
                                    }
                                    CompactIconButton {
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
                            ScrollBar.vertical: Md3ScrollBar {
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
                                font.pointSize: Typography.label
                            }
                        }
                    }
                }
            }
        }

        Item {
            id: detailsPanel
            SplitView.fillWidth: true
            SplitView.minimumWidth: 410
            property var record: commitQueueController.selectedRecord

            ColumnLayout {
                anchors.fill: parent
                spacing: 8

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    radius: root.theme.surfaceRadius
                    color: root.theme.surfaceContainerLow

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 10
                        spacing: 9
                        Rectangle {
                            Layout.preferredWidth: 34
                            Layout.preferredHeight: 34
                            radius: 10
                            color: root.theme.secondaryContainer
                            MaterialIcon {
                                anchors.centerIn: parent
                                name: commitQueueController.selectedRow < 0
                                    ? "publish" : root.statusIcon(detailsPanel.record.status || "Prepared")
                                size: 17
                                color: commitQueueController.selectedRow < 0
                                    ? root.theme.action
                                    : root.statusColor(detailsPanel.record.status || "Prepared")
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Label {
                                Layout.fillWidth: true
                                text: detailsPanel.record.objectTitle
                                    || qsTr("Operation details")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: commitQueueController.selectedRow < 0
                                    ? qsTr("Select a queue item")
                                    : (detailsPanel.record.process || "publish")
                                        + "  ·  " + (detailsPanel.record.context
                                            || qsTr("No context"))
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                                elide: Text.ElideRight
                            }
                        }
                        StatusChip {
                            visible: commitQueueController.selectedRow >= 0
                                && detailsPanel.record.status !== "Prepared"
                            theme: root.theme
                            text: qsTr(detailsPanel.record.status || "Prepared")
                            iconName: root.statusIcon(
                                detailsPanel.record.status || "Prepared")
                            accentColor: root.statusColor(
                                detailsPanel.record.status || "Prepared")
                        }
                    }
                }

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
                        MaterialIcon {
                            name: "content_copy"
                            size: 17
                            color: root.theme.tertiary
                        }
                        Label {
                            Layout.fillWidth: true
                            text: commitQueueController.duplicateDescription
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.label
                            wrapMode: Text.WordWrap
                        }
                        Md3Button {
                            theme: root.theme
                            text: qsTr("Replace")
                            tonal: true
                            onClicked: commitQueueController.resolve_duplicate("replace")
                        }
                        Md3Button {
                            theme: root.theme
                            text: qsTr("Add another")
                            onClicked: commitQueueController.resolve_duplicate("add")
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            toolTip: qsTr("Ignore duplicate")
                            onClicked: commitQueueController.resolve_duplicate("ignore")
                        }
                    }
                }

                Flickable {
                    id: editorScroll
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
                                Md3CheckBox {
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
                                    font.pointSize: Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.max(
                                previewContent.implicitHeight, 76
                            ) + 22
                            radius: root.theme.surfaceRadius
                            color: root.theme.surfaceContainerLow
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            RowLayout {
                                id: previewContent
                                anchors.fill: parent
                                anchors.margins: 11
                                spacing: 10

                                ItemPreview {
                                    theme: root.theme
                                    Layout.preferredWidth: 76
                                    Layout.preferredHeight: 76
                                    previewSize: 76
                                    source: detailsPanel.record.previewUrl || ""
                                    fallbackText: detailsPanel.record.previewExtension
                                        || "FILE"
                                    accent: root.theme.action
                                    cornerRadius: root.theme.itemRadius
                                    animateAppearance: false
                                }

                                SnapshotSummary {
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 66
                                    title: detailsPanel.record.futureFileName
                                        || detailsPanel.record.title || "Snapshot"
                                    description: detailsPanel.record.description
                                        || detailsPanel.record.objectTitle || ""
                                    version: detailsPanel.record.versionLabel || ""
                                    repository: detailsPanel.record.repository || ""
                                    fileSize: detailsPanel.record.fileSummary || ""
                                    infoChips: detailsPanel.record.snapshotInfoChips || []
                                }

                                CompactIconButton {
                                    theme: root.theme
                                    iconName: "photo_camera"
                                    toolTip: qsTr("Capture screenshot")
                                    enabled: Boolean(detailsPanel.record.canEdit)
                                        && !commitQueueController.busy
                                    onClicked: {
                                        screenshotController.prepare_for_operation(
                                            commitQueueController.selectedId
                                        )
                                        windowModel.show_window("screenshot_maker")
                                    }
                                }
                                CompactIconButton {
                                    theme: root.theme
                                    iconName: "add-photo-alternate"
                                    toolTip: qsTr("Choose preview images")
                                    enabled: Boolean(detailsPanel.record.canEdit)
                                        && !commitQueueController.busy
                                    onClicked: operationPreviewDialog.open()
                                }
                                CompactIconButton {
                                    theme: root.theme
                                    iconName: "content-paste"
                                    toolTip: qsTr("Paste preview image from clipboard")
                                    enabled: Boolean(detailsPanel.record.canEdit)
                                        && screenshotController.clipboardHasImage
                                        && !commitQueueController.busy
                                    onClicked: screenshotController
                                        .paste_preview_from_clipboard(
                                            commitQueueController.selectedId
                                        )
                                }
                                CompactIconButton {
                                    theme: root.theme
                                    iconName: "collections"
                                    toolTip: qsTr("Manage selected previews")
                                    enabled: Number(detailsPanel.record.previewCount || 0) > 0
                                    onClicked: operationPreviewList.open()
                                }
                                CompactIconButton {
                                    theme: root.theme
                                    iconName: "delete_sweep"
                                    toolTip: qsTr("Clear operation previews")
                                    enabled: Boolean(detailsPanel.record.canEdit)
                                        && Number(detailsPanel.record.previewCount || 0) > 0
                                        && !commitQueueController.busy
                                    onClicked: commitQueueController.clear_selected_previews()
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: destinationContent.implicitHeight + 22
                            radius: root.theme.surfaceRadius
                            color: root.theme.surfaceContainerLow
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            ColumnLayout {
                                id: destinationContent
                                anchors.fill: parent
                                anchors.margins: 11
                                spacing: 8
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    rowSpacing: 7
                                    columnSpacing: 9
                                    Label {
                                        text: qsTr("Context")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Typography.label
                                    }
                                    Md3TextField {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        text: detailsPanel.record.context || ""
                                        onEditingFinished: commitQueueController.update_selected("context", text)
                                    }
                                }
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
                                Md3Button {
                                    theme: root.theme
                                    text: qsTr("Advanced options")
                                    icon.name: commitQueueController.advancedOptionsExpanded
                                        ? "expand_less" : "expand_more"
                                    flat: true
                                    onClicked: commitQueueController.set_advanced_options_expanded(
                                        !commitQueueController.advancedOptionsExpanded
                                    )
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
                                        font.pointSize: Typography.label
                                    }
                                    Md3ComboBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        model: commitQueueController.repositories
                                        currentIndex: commitQueueController.repositories.indexOf(detailsPanel.record.repository || "")
                                        onActivated: commitQueueController.update_selected("repository", currentText)
                                    }
                                    Label {
                                        text: qsTr("Version")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Typography.label
                                    }
                                    Md3TextField {
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
                                        font.pointSize: Typography.label
                                    }
                                    Md3ComboBox {
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
                                        font.pointSize: Typography.label
                                    }
                                    Md3TextField {
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
                            visible: commitQueueController.advancedOptionsExpanded
                            radius: root.theme.surfaceRadius
                            color: root.theme.surfaceContainerLow
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            ColumnLayout {
                                id: optionsContent
                                anchors.fill: parent
                                anchors.margins: 11
                                spacing: 6
                                SectionLabel { text: qsTr("FILE OPTIONS") }
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: width >= 560 ? 2 : 1
                                    rowSpacing: 2
                                    columnSpacing: 12
                                    Md3CheckBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        text: qsTr("Update versionless")
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                            && !detailsPanel.record.keepFileName
                                        checked: Boolean(detailsPanel.record.updateVersionless)
                                        onClicked: commitQueueController.update_selected("updateVersionless", checked)
                                    }
                                    Md3CheckBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        text: qsTr("Commit versionless only")
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        checked: Boolean(detailsPanel.record.onlyVersionless)
                                        onClicked: commitQueueController.update_selected("onlyVersionless", checked)
                                    }
                                    Md3CheckBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        text: qsTr("Keep source filename")
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        checked: Boolean(detailsPanel.record.keepFileName)
                                        onClicked: commitQueueController.update_selected("keepFileName", checked)
                                    }
                                    Md3CheckBox {
                                        theme: root.theme
                                        Layout.fillWidth: true
                                        text: qsTr("Use context as filename")
                                        enabled: Boolean(detailsPanel.record.canEdit)
                                        checked: Boolean(detailsPanel.record.contextAsFilename)
                                        onClicked: commitQueueController.update_selected("contextAsFilename", checked)
                                    }
                                    Md3CheckBox {
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
                            Layout.fillWidth: true
                            Layout.preferredHeight: namingContent.implicitHeight + 22
                            radius: root.theme.surfaceRadius
                            color: root.theme.surfaceContainerLow
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            ColumnLayout {
                                id: namingContent
                                anchors.fill: parent
                                anchors.margins: 11
                                spacing: 7

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 7
                                    SectionLabel { text: qsTr("NAMING PREVIEW") }
                                    Item { Layout.fillWidth: true }
                                    Md3Button {
                                        theme: root.theme
                                        text: qsTr("Naming Editor")
                                        icon.name: "drive_file_rename_outline"
                                        flat: true
                                        onClicked: {
                                            namingEditorController.prepare_operation(
                                                commitQueueController.selectedId
                                            )
                                            windowModel.show_window("naming_editor")
                                        }
                                    }
                                    CompactIconButton {
                                        theme: root.theme
                                        iconName: root.namingPreviewExpanded
                                            ? "expand_less" : "expand_more"
                                        toolTip: root.namingPreviewExpanded
                                            ? qsTr("Collapse naming preview")
                                            : qsTr("Expand naming preview")
                                        onClicked: root.namingPreviewExpanded =
                                            !root.namingPreviewExpanded
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    visible: root.namingPreviewExpanded
                                    spacing: 5

                                    Repeater {
                                        model: detailsPanel.record.sourceFiles || []
                                        delegate: Rectangle {
                                            required property int index
                                            required property var modelData
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
                                                    font.pointSize: Typography.label
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
                                                    font.pointSize: Typography.caption
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
                                                    font.pointSize: Typography.caption
                                                    elide: Text.ElideMiddle
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
                                MaterialIcon {
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
                                    font.pointSize: Typography.label
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }

                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: editorScroll
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
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
                            text: commitQueueController.busy
                                ? (detailsPanel.record.stage || qsTr("Working"))
                                : commitQueueController.count === 0
                                    ? qsTr("Add files from Save Snapshot or Drop Plate")
                                    : commitQueueController.count
                                        + (commitQueueController.count === 1
                                            ? qsTr(" queue item")
                                            : qsTr(" queue items"))
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.label
                            elide: Text.ElideRight
                        }
                        Md3Button {
                            theme: root.theme
                            text: qsTr("Retry")
                            icon.name: "refresh"
                            visible: detailsPanel.record.status === "Failed"
                            enabled: !commitQueueController.busy
                            onClicked: commitQueueController.retry_current()
                        }
                        Md3Button {
                            theme: root.theme
                            text: qsTr("Cancel")
                            icon.name: "stop"
                            visible: commitQueueController.busy
                            destructive: true
                            onClicked: commitQueueController.cancel()
                        }
                        Md3Button {
                            theme: root.theme
                            text: qsTr("Commit current")
                            icon.name: "publish"
                            enabled: commitQueueController.selectedRow >= 0
                                && !commitQueueController.busy
                                && detailsPanel.record.status !== "Completed"
                                && Boolean(detailsPanel.record.canCommit)
                            onClicked: commitQueueController.commit_current()
                        }
                        Md3Button {
                            theme: root.theme
                            text: detailsPanel.width >= 720
                                ? qsTr("Commit selected") : qsTr("Selected")
                            icon.name: "done_all"
                            enabled: commitQueueController.hasCheckedReady
                                && !commitQueueController.busy
                            onClicked: commitQueueController.commit_selected()
                        }
                        Md3Button {
                            theme: root.theme
                            text: qsTr("Commit all")
                            icon.name: "publish"
                            highlighted: enabled
                            enabled: commitQueueController.hasReady
                                && !commitQueueController.busy
                            onClicked: commitQueueController.commit_all()
                        }
                    }
                }
            }
        }
    }

    Md3Dialog {
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
                    ItemPreview {
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
                        font.pointSize: Typography.body
                        elide: Text.ElideMiddle
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "close"
                        toolTip: qsTr("Remove preview")
                        enabled: Boolean(commitQueueController.selectedRecord.canEdit)
                        onClicked: commitQueueController.remove_selected_preview(index)
                    }
                }
            }

            ScrollBar.vertical: Md3ScrollBar {
                theme: root.theme
                flickableTarget: previewList
            }
        }

        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Add images")
                icon.name: "add_photo_alternate"
                DialogButtonBox.buttonRole: DialogButtonBox.ActionRole
                onClicked: operationPreviewDialog.open()
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Paste image")
                icon.name: "content_paste"
                enabled: screenshotController.clipboardHasImage
                DialogButtonBox.buttonRole: DialogButtonBox.ActionRole
                onClicked: screenshotController.paste_preview_from_clipboard(
                    commitQueueController.selectedId
                )
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Close")
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }

    Md3Dialog {
        id: clearQueueConfirmation
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(420, root.width - 32)
        title: qsTr("Clear commit queue?")

        contentItem: Label {
            width: clearQueueConfirmation.width - 40
            text: qsTr("All prepared, failed and completed operations will be removed from the queue.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Typography.bodyLarge
            wrapMode: Text.WordWrap
        }

        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Clear queue")
                icon.name: "delete_forever"
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }

        onAccepted: commitQueueController.clear()
    }
}
