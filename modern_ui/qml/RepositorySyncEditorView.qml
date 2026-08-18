import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    required property string windowId
    readonly property bool compact: width < 1040
    readonly property int toolbarColumns: width >= 1480 ? 3
        : width >= 720 ? 2 : 1
    readonly property int toolbarRows: Math.ceil(3 / toolbarColumns)

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 70
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.margins: 11
                spacing: 10

                Rectangle {
                    Layout.preferredWidth: 44
                    Layout.preferredHeight: 44
                    radius: root.theme.itemRadius
                    color: root.theme.secondaryContainer
                    MaterialIcon {
                        anchors.centerIn: parent
                        name: "repository-sync"
                        size: 21
                        color: root.theme.action
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Repository Sync")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: repositorySyncEditorController.contextTitle
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.body
                        elide: Text.ElideRight
                    }
                }
                Md3BusyIndicator {
                    uiTheme: root.theme
                    running: repositorySyncEditorController.busy
                    visible: running
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 18 + root.toolbarRows * 40
                + Math.max(0, root.toolbarRows - 1) * 8
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            GridLayout {
                anchors.fill: parent
                anchors.margins: 9
                columns: root.toolbarColumns
                columnSpacing: 10
                rowSpacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 6

                    Md3ComboBox {
                        id: presetCombo
                        Layout.fillWidth: true
                        Layout.minimumWidth: 160
                        theme: root.theme
                        model: repositorySyncPresetModel
                        textRole: "title"
                        valueRole: "name"
                        translateDisplayText: false
                        currentIndex: repositorySyncEditorController.selectedPreset
                        enabled: count > 0 && !repositorySyncEditorController.busy
                        onActivated: index =>
                            repositorySyncEditorController.select_preset(index)
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "refresh"
                        toolTip: qsTr("Reload presets")
                        enabled: !repositorySyncEditorController.busy
                        onClicked: repositorySyncEditorController.reload_presets()
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "save"
                        toolTip: qsTr("Save current preset")
                        enabled: repositorySyncEditorController.selectedPreset >= 0
                            && !repositorySyncEditorController.busy
                        onClicked: repositorySyncEditorController.save_selected()
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "delete"
                        toolTip: qsTr("Delete current preset")
                        enabled: repositorySyncEditorController.selectedPreset >= 0
                            && !repositorySyncEditorController.busy
                        onClicked: deletePresetDialog.open()
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "add"
                        toolTip: qsTr("Save as a new preset")
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
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 7

                    Md3SegmentedButton {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 126
                        Layout.maximumWidth: 270
                        theme: root.theme
                        segmentWidth: 118
                        minimumSegmentWidth: 52
                        currentValue: repositorySyncEditorController.fullSync
                            ? "full" : "versionless"
                        model: [
                            { label: "Versionless Sync", value: "versionless",
                                icon: "history" },
                            { label: "Full Sync", value: "full",
                                icon: "layers" }
                        ]
                        onActivated: value =>
                            repositorySyncEditorController.set_full_sync(
                                value === "full"
                            )
                    }
                    Md3Switch {
                        theme: root.theme
                        text: qsTr("Only updates")
                        checked: repositorySyncEditorController.onlyUpdates
                        onToggled:
                            repositorySyncEditorController.set_only_updates(checked)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 7

                    Md3SegmentedButton {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 126
                        Layout.maximumWidth: 270
                        theme: root.theme
                        segmentWidth: 118
                        minimumSegmentWidth: 52
                        currentValue: repositorySyncEditorController.scopeMode
                        model: [
                            { label: "Full scope", value: "full",
                                icon: "inventory-2" },
                            { label: "Partial scope", value: "partial",
                                icon: "stream" }
                        ]
                        onActivated: value =>
                            repositorySyncEditorController.set_scope_mode(value)
                        HoverHandler { id: scopeModeHover }
                        Md3ToolTip {
                            theme: root.theme
                            visible: scopeModeHover.hovered
                                && !root.theme.suppressToolTips
                            text: parent.currentValue === "partial"
                                ? qsTr("Start downloading completed chunks while the remaining scope is still discovered.")
                                : qsTr("Discover the complete file scope before downloading.")
                        }
                    }
                    Label {
                        text: qsTr("Chunk")
                        color: repositorySyncEditorController.scopeMode
                            === "partial"
                            ? root.theme.secondaryText
                            : root.theme.disabledText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.body
                    }
                    Md3SpinBox {
                        id: partialChunkSize
                        Layout.preferredWidth: 82
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
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: root.compact
                    ? Math.max(360, root.width * 0.40)
                    : Math.max(410, root.width * 0.43)
                Layout.minimumWidth: 350
                radius: root.theme.itemRadius
                color: root.theme.surfaceContainerLow
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 7

                    GridLayout {
                        Layout.fillWidth: true
                        columns: root.compact ? 2 : 4
                        columnSpacing: 6
                        rowSpacing: 6

                        Md3Button {
                            Layout.fillWidth: true
                            theme: root.theme
                            text: qsTr("Toggle All")
                            icon.name: "select_all"
                            onClicked:
                                repositorySyncEditorController.toggle_kind("all")
                        }
                        Md3Button {
                            Layout.fillWidth: true
                            theme: root.theme
                            text: qsTr("Processes")
                            icon.name: "process"
                            onClicked:
                                repositorySyncEditorController.toggle_kind("process")
                        }
                        Md3Button {
                            Layout.fillWidth: true
                            theme: root.theme
                            text: qsTr("Built-ins")
                            icon.name: "settings-suggest"
                            onClicked:
                                repositorySyncEditorController.toggle_kind("builtin")
                        }
                        Md3Button {
                            Layout.fillWidth: true
                            theme: root.theme
                            text: qsTr("Children")
                            icon.name: "schema"
                            onClicked:
                                repositorySyncEditorController.toggle_kind("child")
                        }
                    }

                    SmoothListView {
                        id: syncTree
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: repositorySyncTreeModel

                        delegate: Item {
                            id: treeRow
                            required property int index
                            required property string title
                            required property string subtitle
                            required property string kind
                            required property int depth
                            required property bool checkable
                            required property bool checked
                            required property bool expanded
                            required property bool rowVisible
                            required property bool selected
                            required property string accent

                            width: syncTree.width
                            height: rowVisible ? 46 : 0
                            visible: height > 0
                            clip: true

                            Rectangle {
                                anchors.fill: parent
                                anchors.topMargin: 2
                                anchors.bottomMargin: 2
                                anchors.rightMargin: 5
                                radius: root.theme.itemRadius
                                color: treeRow.selected
                                    ? root.theme.selected
                                    : rowMouse.containsMouse
                                        ? root.theme.rowHover
                                        : root.theme.surfaceContainerHigh
                                border.width: treeRow.selected ? 1 : 0
                                border.color: root.theme.action

                                MouseArea {
                                    id: rowMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: mouse =>
                                        repositorySyncEditorController.select_row(
                                            treeRow.index,
                                            Boolean(mouse.modifiers
                                                & Qt.ControlModifier)
                                        )
                                }

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 7 + treeRow.depth * 19
                                    anchors.rightMargin: 9
                                    spacing: 6

                                    CompactIconButton {
                                        Layout.preferredWidth: 25
                                        Layout.preferredHeight: 25
                                        theme: root.theme
                                        visible: treeRow.kind === "child"
                                            || treeRow.kind === "pipeline"
                                        iconName: treeRow.expanded
                                            ? "keyboard_arrow_down"
                                            : "keyboard_arrow_right"
                                        toolTip: treeRow.expanded
                                            ? qsTr("Collapse") : qsTr("Expand")
                                        onClicked:
                                            repositorySyncEditorController
                                                .toggle_expanded(treeRow.index)
                                    }
                                    Item {
                                        Layout.preferredWidth: 25
                                        Layout.preferredHeight: 25
                                        visible: treeRow.kind !== "child"
                                            && treeRow.kind !== "pipeline"
                                    }
                                    Md3CheckBox {
                                        theme: root.theme
                                        visible: treeRow.checkable
                                        checked: treeRow.checked
                                        onToggled:
                                            repositorySyncEditorController
                                                .set_checked(treeRow.index, checked)
                                    }
                                    Item {
                                        Layout.preferredWidth: 22
                                        Layout.preferredHeight: 22
                                        visible: !treeRow.checkable
                                    }
                                    MaterialIcon {
                                        name: treeRow.kind === "child" ? "schema"
                                            : treeRow.kind === "pipeline"
                                                ? "account_tree"
                                                : treeRow.kind === "builtin"
                                                    ? "settings-suggest"
                                                    : "process"
                                        size: 16
                                        color: treeRow.accent.length
                                            ? treeRow.accent : root.theme.action
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.minimumWidth: 0
                                        spacing: 0
                                        Label {
                                            Layout.fillWidth: true
                                            text: treeRow.title
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.body
                                            font.weight: treeRow.kind === "child"
                                                || treeRow.kind === "pipeline"
                                                ? Font.DemiBold : Font.Normal
                                            elide: Text.ElideRight
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            text: treeRow.subtitle
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Typography.caption
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                            }
                        }

                        ScrollBar.vertical: Md3ScrollBar {
                            theme: root.theme
                            flickableTarget: syncTree
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 430
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

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
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
                    font.pointSize: Typography.label
                    elide: Text.ElideRight
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Close")
                    flat: true
                    onClicked: windowModel.close_window(root.windowId)
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Begin Repository Sync")
                    icon.name: "repository-sync"
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
    }

    Md3Dialog {
        id: newPresetDialog
        theme: root.theme
        title: qsTr("Save Repository Sync preset")
        modal: true
        anchors.centerIn: parent
        width: Math.min(420, root.width - 48)
        onAccepted:
            repositorySyncEditorController.save_as(newPresetField.text)

        contentItem: Md3TextField {
            id: newPresetField
            width: Math.max(220, newPresetDialog.width - 48)
            theme: root.theme
            placeholderText: qsTr("Preset name")
            Keys.onReturnPressed: newPresetDialog.accept()
        }
        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Create and save")
                highlighted: true
                enabled: newPresetField.text.trim().length > 0
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }

    Md3Dialog {
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
            font.pointSize: Typography.body
        }
        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Delete")
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
    }
}
