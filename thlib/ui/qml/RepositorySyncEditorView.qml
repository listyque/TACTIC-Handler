import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property string windowId

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 9
        spacing: 6

        SplitView {
            id: contentSplit
            Layout.fillWidth: true
            Layout.fillHeight: true
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

            ColumnLayout {
                SplitView.preferredWidth: Math.min(360, root.width * 0.40)
                SplitView.minimumWidth: 330
                SplitView.maximumWidth: Math.max(360, root.width * 0.44)
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Controls.CompactIconButton {
                        objectName: "repositorySyncPresetDeleteButton"
                        visible: processTree.togglersExpanded
                        theme: root.theme
                        iconName: "delete"
                        toolTip: qsTr("Remove Current Preset")
                        enabled: repositorySyncEditorController.selectedPreset >= 0
                            && !repositorySyncEditorController.busy
                        onClicked: deletePresetDialog.open()
                    }
                    Controls.ComboBox {
                        id: presetCombo
                        Layout.fillWidth: true
                        Layout.minimumWidth: 150
                        theme: root.theme
                        model: repositorySyncPresetModel
                        textRole: "title"
                        valueRole: "name"
                        translateDisplayText: false
                        currentIndex: repositorySyncEditorController.selectedPreset
                        enabled: count > 0
                            && !repositorySyncEditorController.busy
                        onActivated: index =>
                            repositorySyncEditorController.select_preset(index)
                    }
                    Controls.CompactIconButton {
                        objectName: "repositorySyncPresetSaveButton"
                        visible: processTree.togglersExpanded
                        theme: root.theme
                        iconName: "content-save"
                        toolTip: qsTr("Save Current Preset Changes")
                        enabled: repositorySyncEditorController.selectedPreset >= 0
                            && !repositorySyncEditorController.busy
                        onClicked: repositorySyncEditorController.save_selected()
                    }
                    Controls.CompactIconButton {
                        objectName: "repositorySyncPresetAddButton"
                        visible: processTree.togglersExpanded
                        theme: root.theme
                        iconName: "plus-box"
                        toolTip: qsTr("Create new Preset and Save")
                        enabled: repositorySyncEditorController.validContext
                            && !repositorySyncEditorController.busy
                        onClicked: {
                            newPresetField.text = ""
                            newPresetDialog.open()
                            Qt.callLater(function() {
                                newPresetField.forceActiveFocus()
                            })
                        }
                    }
                    Controls.BusyIndicator {
                        uiTheme: root.theme
                        running: repositorySyncEditorController.busy
                        visible: running
                    }
                }

                Controls.ProcessSelectionTree {
                    id: processTree
                    objectName: "repositorySyncProcessPanel"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    treeModel: repositorySyncTreeModel
                    treeController: repositorySyncEditorController
                    validContext: repositorySyncEditorController.validContext
                    showVersionChooser: true
                    emptyText: qsTr("Select an sObject or Search Type first")
                    treeObjectName: "repositorySyncProcessTree"
                    rowObjectName: "repositorySyncProcessTreeRow"
                }

            }

            ColumnLayout {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 440
                spacing: 6

                Rectangle {
                    id: optionsPanel
                    readonly property bool compact: width < 650
                    objectName: "repositorySyncOptionsPanel"
                    Layout.fillWidth: true
                    Layout.preferredHeight: optionsPanel.compact
                        ? root.theme.controlHeight * 2 + 18
                        : root.theme.controlHeight + 12
                    radius: root.theme.itemRadius
                    color: root.theme.surfaceContainerLow
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    GridLayout {
                        anchors.fill: parent
                        anchors.margins: 6
                        columns: optionsPanel.compact ? 3 : 4
                        columnSpacing: 7
                        rowSpacing: 6

                        Controls.SegmentedButton {
                            Layout.fillWidth: true
                            Layout.minimumWidth: optionsPanel.compact ? 250 : 290
                            Layout.preferredWidth: optionsPanel.compact ? 330 : 310
                            Layout.maximumWidth: 340
                            theme: root.theme
                            segmentWidth: 150
                            minimumSegmentWidth: 130
                            currentValue: repositorySyncEditorController.scopeMode
                            model: [
                                { label: "Full scope", value: "full",
                                    icon: "inventory-2" },
                                { label: "Partial scope", value: "partial",
                                    icon: "stream" }
                            ]
                            onActivated: value =>
                                repositorySyncEditorController.set_scope_mode(value)
                        }
                        Controls.Switch {
                            Layout.row: optionsPanel.compact ? 1 : 0
                            Layout.column: optionsPanel.compact ? 0 : 1
                            Layout.columnSpan: optionsPanel.compact ? 3 : 1
                            theme: root.theme
                            text: qsTr("Only updates")
                            checked: repositorySyncEditorController.onlyUpdates
                            onToggled: repositorySyncEditorController
                                .set_only_updates(checked)
                        }
                        Label {
                            Layout.row: 0
                            Layout.column: optionsPanel.compact ? 1 : 2
                            text: qsTr("Chunk")
                            color: repositorySyncEditorController.scopeMode
                                === "partial"
                                ? root.theme.secondaryText
                                : root.theme.disabledText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                        }
                        Controls.SpinBox {
                            id: partialChunkSize
                            Layout.row: 0
                            Layout.column: optionsPanel.compact ? 2 : 3
                            Layout.preferredWidth: 78
                            enabled: repositorySyncEditorController.scopeMode
                                === "partial"
                            theme: root.theme
                            from: 1
                            to: 250
                            stepSize: 1
                            value: repositorySyncEditorController.partialChunkSize
                            editable: true
                            onRealValueEdited: value =>
                                repositorySyncEditorController
                                    .set_partial_chunk_size(Math.round(value))
                            ToolTip.visible: hovered
                                && !root.theme.suppressToolTips
                            ToolTip.text: qsTr("Objects discovered per chunk")
                        }
                    }
                }

                Rectangle {
                    objectName: "repositorySyncQueuePanel"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: root.theme.itemRadius
                    color: root.theme.surfaceContainerLow
                    border.width: 1
                    border.color: root.theme.outlineVariant
                    clip: true

                    RepositorySyncView {
                        anchors.fill: parent
                        anchors.margins: 1
                        theme: root.theme
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: root.theme.controlHeight
            spacing: 8

            Label {
                Layout.fillWidth: true
                text: repositorySyncEditorController.error.length
                    ? repositorySyncEditorController.error
                    : repositorySyncEditorController.dirty
                        ? qsTr("Preset has unsaved changes") : ""
                color: repositorySyncEditorController.error.length
                    ? root.theme.error : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                elide: Text.ElideRight
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Close")
                flat: true
                onClicked: windowModel.close_window(root.windowId)
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Begin Repo Sync")
                icon.name: "sync"
                highlighted: true
                enabled: repositorySyncEditorController.validContext
                    && repositorySyncEditorController.selectedPreset >= 0
                    && !repositorySyncEditorController.busy
                    && !repositorySync.discovery_active
                    && repositorySync.active_count === 0
                onClicked: {
                    partialChunkSize.commitTextValue()
                    repositorySyncEditorController.start_sync_with_chunk_size(
                        partialChunkSize.value
                    )
                }
            }
        }
    }

    Controls.Dialog {
        id: newPresetDialog
        theme: root.theme
        title: qsTr("Save Repository Sync preset")
        modal: true
        anchors.centerIn: parent
        width: Math.min(420, root.width - 48)
        onAccepted:
            repositorySyncEditorController.save_as(newPresetField.text)

        contentItem: Controls.TextField {
            id: newPresetField
            width: Math.max(220, newPresetDialog.width - 48)
            theme: root.theme
            placeholderText: qsTr("Preset name")
            Keys.onReturnPressed: newPresetDialog.accept()
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Create and save")
                highlighted: true
                enabled: newPresetField.text.trim().length > 0
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }

    Controls.Dialog {
        id: deletePresetDialog
        theme: root.theme
        title: qsTr("Delete Repository Sync preset?")
        modal: true
        anchors.centerIn: parent
        width: Math.min(440, root.width - 48)
        onAccepted: repositorySyncEditorController.delete_selected()

        contentItem: Label {
            width: Math.max(220, deletePresetDialog.width - 48)
            wrapMode: Text.WordWrap
            text: qsTr("The selected server preset will be deleted.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Delete")
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }
}
