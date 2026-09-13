import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property bool wideLayout: width >= 720
    property bool advancedVisible: false

    function statusColor(status) {
        if (status === "Completed")
            return theme.green
        if (status === "Failed")
            return theme.error
        if (status === "Skipped" || status === "Cancelled"
                || status === "Conflict")
            return theme.yellow
        if (status === "Queued" || status === "Running"
                || status === "Checking")
            return theme.action
        return theme.secondaryText
    }

    function statusIcon(status) {
        if (status === "Completed")
            return "check-circle"
        if (status === "Failed")
            return "error"
        if (status === "Conflict")
            return "warning"
        if (status === "Skipped" || status === "Cancelled")
            return "cancel"
        if (status === "Queued" || status === "Running"
                || status === "Checking")
            return "sync"
        return "file"
    }

    FileDialog {
        id: fileDialog
        title: qsTr("Choose files to ingest")
        fileMode: FileDialog.OpenFiles
        onAccepted: ingestFilesController.add_paths(selectedFiles)
    }

    Controls.Dialog {
        id: deleteRuleDialog
        theme: root.theme
        parent: root
        title: qsTr("Delete ingest rule?")
        modal: true
        focus: true
        anchors.centerIn: parent
        width: Math.min(440, parent.width - 24)
        standardButtons: Dialog.NoButton

        contentItem: Label {
            text: qsTr("The rule will be removed from this TACTIC project.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: deleteRuleDialog.reject()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Delete")
                icon.name: "delete"
                destructive: true
                onClicked: {
                    deleteRuleDialog.accept()
                    ingestFilesController.delete_selected_rule()
                }
            }
        }
    }

    IngestConflictDialog {
        anchors.fill: parent
        theme: root.theme
        controller: ingestFilesController
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: contextRow.implicitHeight + 20
            color: root.theme.surfaceContainer
            border.width: 0

            RowLayout {
                id: contextRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 10

                Controls.MaterialIcon {
                    name: "upload"
                    size: 22
                    color: root.theme.action
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("%1 → %2").arg(
                            ingestFilesController.parentTitle || qsTr("Parent")
                        ).arg(ingestFilesController.targetTitle || qsTr("Child items"))
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("One Search Object per file · snapshot in publish")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                }
                Label {
                    text: ingestFilesController.searchType
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 10
            columns: root.wideLayout ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10

            Rectangle {
                id: filesPanel
                objectName: "ingestFilesPanel"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 280
                Layout.minimumHeight: 220
                Layout.preferredWidth: root.wideLayout ? 340 : root.width
                color: root.theme.panelDeep
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.margins: 10
                        spacing: 7
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Files · %1").arg(
                                ingestFilesController.fileCount)
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                        }
                        Controls.Button {
                            theme: root.theme
                            compact: true
                            text: qsTr("Clear")
                            icon.name: "delete-sweep"
                            enabled: !ingestFilesController.busy
                                && ingestFilesController.fileCount > 0
                            onClicked: ingestFilesController.clear_files()
                        }
                        Controls.Button {
                            theme: root.theme
                            compact: true
                            text: qsTr("Add files")
                            icon.name: "add"
                            enabled: !ingestFilesController.busy
                            onClicked: fileDialog.open()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                    implicitHeight: 1
                        color: root.theme.outlineVariant
                    }

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        DropArea {
                            anchors.fill: parent
                            enabled: !ingestFilesController.busy
                            keys: ["text/uri-list"]
                            onEntered: drag => drag.acceptProposedAction()
                            onDropped: drop => {
                                drop.acceptProposedAction()
                                ingestFilesController.add_paths(drop.urls)
                            }
                        }

                        ListView {
                            id: filesList
                            anchors.fill: parent
                            anchors.margins: 6
                            anchors.rightMargin: fileScroll.reservedExtent + 8
                            model: ingestFileModel
                            spacing: 4
                            clip: true
                            boundsBehavior: Flickable.StopAtBounds

                            delegate: Rectangle {
                                required property int index
                                required property string path
                                required property string title
                                required property string extension
                                required property string status
                                required property string error
                                width: filesList.width
                                height: error.length > 0 ? 62 : 46
                                radius: root.theme.itemRadius
                                color: root.theme.row
                                border.width: 1
                                border.color: root.theme.outlineVariant

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 6
                                    spacing: 8
                                    Controls.MaterialIcon {
                                        name: root.statusIcon(status)
                                        size: 17
                                        color: root.statusColor(status)
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 0
                                        Label {
                                            Layout.fillWidth: true
                                            text: title
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.body
                                            elide: Text.ElideMiddle
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            visible: error.length > 0
                                            text: error
                                            color: root.theme.error
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.caption
                                            elide: Text.ElideRight
                                        }
                                    }
                                    Label {
                                        text: extension.length > 0
                                            ? extension.toUpperCase() : qsTr("FILE")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                    }
                                    Controls.Button {
                                        theme: root.theme
                                        compact: true
                                        text: qsTr("Remove")
                                        icon.name: "close"
                                        enabled: !ingestFilesController.busy
                                        onClicked: ingestFilesController.remove_file(index)
                                    }
                                }
                            }
                            ScrollBar.vertical: Controls.ScrollBar {
                                id: fileScroll
                                theme: root.theme
                                flickableTarget: filesList
                            }
                        }

                        Controls.EmptyState {
                            anchors.centerIn: parent
                            width: Math.min(360, parent.width - 24)
                            visible: ingestFilesController.fileCount === 0
                            theme: root.theme
                            iconName: "upload"
                            title: qsTr("Drop files here")
                            message: qsTr("Each file creates a child item named without its extension.")
                        }
                    }
                }
            }

            Rectangle {
                objectName: "ingestRulePanel"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 340
                Layout.minimumHeight: 260
                color: root.theme.panelDeep
                radius: root.theme.surfaceRadius
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true

                Flickable {
                    id: optionsViewport
                    anchors.fill: parent
                    anchors.margins: 8
                    contentWidth: width
                    contentHeight: optionsColumn.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    ColumnLayout {
                        id: optionsColumn
                        width: Math.max(0, optionsViewport.width
                            - optionsScroll.reservedExtent - 6)
                        spacing: 10

                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Ingest rule")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                        }

                        ListView {
                            id: rulesList
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.min(
                                174, Math.max(52, count * 54))
                            model: ingestRuleModel
                            spacing: 4
                            clip: true
                            boundsBehavior: Flickable.StopAtBounds

                            delegate: Rectangle {
                                required property int index
                                required property string title
                                required property string subtitle
                                required property bool selected
                                required property bool builtIn
                                required property bool applicable
                                width: rulesList.width
                                    - rulesScroll.reservedExtent - 4
                                height: 50
                                radius: root.theme.itemRadius
                                color: selected
                                    ? root.theme.selected : root.theme.row
                                border.width: selected ? 1 : 0
                                border.color: root.theme.action
                                opacity: applicable ? 1 : 0.5

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 10
                                    spacing: 8
                                    Controls.MaterialIcon {
                                        name: builtIn ? "upload" : "script-python"
                                        size: 17
                                        color: selected
                                            ? root.theme.action
                                            : root.theme.secondaryText
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 0
                                        Label {
                                            Layout.fillWidth: true
                                            text: title
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.body
                                            font.weight: Font.DemiBold
                                            elide: Text.ElideRight
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            text: applicable ? subtitle
                                                : qsTr("For another Search Type")
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.caption
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                                Controls.ActivationHandler {
                                    anchors.fill: parent
                                    enabled: applicable
                                    onActivated: ingestFilesController.select_rule(index)
                                }
                            }
                            ScrollBar.vertical: Controls.ScrollBar {
                                id: rulesScroll
                                theme: root.theme
                                flickableTarget: rulesList
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Controls.CheckBox {
                                theme: root.theme
                                text: qsTr("Remove extension from item name")
                                checked: !!ingestFilesController.options.ignoreExtension
                                enabled: !ingestFilesController.busy
                                onToggled: ingestFilesController.set_option(
                                    "ignoreExtension", checked)
                            }
                            Item { Layout.fillWidth: true }
                            Controls.Button {
                                theme: root.theme
                                text: root.advancedVisible
                                    ? qsTr("Hide rule details")
                                    : qsTr("Edit rule details")
                                icon.name: root.advancedVisible
                                    ? "expand-less" : "settings"
                                onClicked: root.advancedVisible = !root.advancedVisible
                            }
                        }

                        IngestRuleEditor {
                            Layout.fillWidth: true
                            visible: root.advancedVisible
                            theme: root.theme
                            controller: ingestFilesController
                            onDeleteRuleRequested: deleteRuleDialog.open()
                        }
                    }
                    ScrollBar.vertical: Controls.ScrollBar {
                        id: optionsScroll
                        theme: root.theme
                        flickableTarget: optionsViewport
                    }
                }

                ContentLoadingOverlay {
                    anchors.fill: parent
                    theme: root.theme
                    visible: ingestFilesController.rulesBusy
                    message: qsTr("Loading ingest rules…")
                }
            }
        }

        Controls.DockWorkspaceFooter {
            Layout.fillWidth: true
            theme: root.theme

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 8
                Controls.BusyIndicator {
                    uiTheme: root.theme
                    running: ingestFilesController.busy
                    visible: running
                    Layout.preferredWidth: 18
                    Layout.preferredHeight: 18
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        visible: ingestFilesController.message.length > 0
                        text: ingestFilesController.message
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: ingestFilesController.error.length > 0
                        text: ingestFilesController.error
                        color: root.theme.error
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                }
                Controls.Button {
                    theme: root.theme
                    text: ingestFilesController.busy ? qsTr("Stop") : qsTr("Close")
                    onClicked: ingestFilesController.busy
                        ? ingestFilesController.cancel()
                        : windowModel.hide_window("ingest_files")
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Ingest %1").arg(ingestFilesController.fileCount)
                    icon.name: "upload"
                    highlighted: true
                    enabled: !ingestFilesController.busy
                        && !ingestFilesController.conflictPending
                        && ingestFilesController.fileCount > 0
                    onClicked: ingestFilesController.start()
                }
            }
        }
    }
}
