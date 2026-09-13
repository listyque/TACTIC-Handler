pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property var controller: sidebarEditorController.scriptShelf
    property int scriptButtonRow: -1
    readonly property string shelfTitleText: String(
        root.controller.editorTitle || qsTr("Untitled shelf")
    ).trim()
    readonly property string removeTargetTitle: String(
        root.controller.removeTargetTitle || root.shelfTitleText
    ).trim()
    readonly property bool canChangeShelf:
        !root.controller.busy && !root.controller.editorDirty
    readonly property var shelfOptions:
        root.controller.editorMode === "personal"
        ? root.controller.personalScopeOptions
        : root.controller.sharedTabOptions
    readonly property string selectedShelf:
        root.controller.editorMode === "personal"
        ? root.controller.personalScope : root.controller.editorView
    readonly property bool shelfReady:
        root.controller.editorMode !== "shared"
        || root.controller.editorView.length > 0

    function selectShelf(value) {
        if (root.controller.editorMode === "personal")
            root.controller.set_personal_scope(value)
        else
            root.controller.select_shared(value)
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12

        RowLayout {
            objectName: "scriptShelfWorkspace"
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            Rectangle {
                objectName: "scriptShelfPresetPane"
                Layout.preferredWidth: Math.max(
                    210, Math.min(250, root.width * 0.25)
                )
                Layout.minimumWidth: 190
                Layout.fillHeight: true
                color: root.theme.panel
                border.width: 1
                border.color: root.theme.outlineVariant
                radius: root.theme.surfaceRadius
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        spacing: 4

                        Controls.SegmentedButton {
                            objectName: "scriptShelfOwnerMode"
                            Layout.fillWidth: true
                            theme: root.theme
                            enabled: root.canChangeShelf
                            currentValue: root.controller.editorMode
                            model: root.controller.canManage ? [
                                {value: "personal", label: qsTr("Mine"), icon: "user"},
                                {value: "shared", label: qsTr("Shared"), icon: "users"}
                            ] : [
                                {value: "personal", label: qsTr("Mine"), icon: "user"}
                            ]
                            onActivated: value =>
                                root.controller.set_editor_mode(value)
                        }

                        Controls.CompactIconButton {
                            objectName: "scriptShelfHelpButton"
                            theme: root.theme
                            iconName: "help"
                            round: true
                            toolTip: qsTr("Help")
                            Accessible.name: toolTip
                            onClicked: windowModel.open_help("script_shelf")
                        }
                    }

                    Controls.Button {
                        id: globalShelfButton
                        objectName: "scriptShelfGlobalPreset"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        visible: root.controller.editorMode === "shared"
                        theme: root.theme
                        text: qsTr("Shared shelf")
                        toolTip: text
                        tonal: true
                        highlighted: root.controller.sharedScope === "global"
                        enabled: root.canChangeShelf
                        onClicked: root.controller.set_shared_scope("global")

                        contentItem: RowLayout {
                            spacing: 7

                            Controls.MaterialIcon {
                                name: globalShelfButton.highlighted
                                    ? "check" : "public"
                                size: 16
                                color: globalShelfButton.contentColor
                            }

                            Label {
                                Layout.fillWidth: true
                                text: globalShelfButton.text
                                color: globalShelfButton.contentColor
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                        }
                    }

                    Rectangle {
                        objectName: "scriptShelfGlobalDivider"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        visible: root.controller.editorMode === "shared"
                        color: root.theme.outlineVariant
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        visible: root.controller.editorMode === "shared"
                        spacing: 4

                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Tab shelves")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.DemiBold
                        }

                        Controls.CompactIconButton {
                            objectName: "newScriptShelfButton"
                            theme: root.theme
                            iconName: "add"
                            round: true
                            toolTip: qsTr("New shelf")
                            enabled: root.canChangeShelf
                                && root.controller.personalScopeOptions.length > 1
                            Accessible.name: toolTip
                            onClicked: root.controller.create_shared()
                        }
                    }

                    ListView {
                        id: presetList
                        objectName: "scriptShelfPresetList"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        rightMargin: presetScrollBar.reservedExtent + 3
                        spacing: 3
                        clip: true
                        visible: count > 0
                        boundsBehavior: Flickable.StopAtBounds
                        model: root.shelfOptions

                        delegate: Controls.Button {
                            id: presetButton
                            required property var modelData
                            readonly property bool selected:
                                String(modelData.value || "")
                                === root.selectedShelf

                            objectName: "scriptShelfPreset_"
                                + String(modelData.value || "")
                                    .replace(/[^a-zA-Z0-9_]/g, "_")
                            width: presetList.width - presetList.rightMargin
                            height: 38
                            theme: root.theme
                            text: String(modelData.label || "")
                            toolTip: text
                            tonal: true
                            highlighted: selected
                            enabled: root.canChangeShelf
                            onClicked: root.selectShelf(
                                String(modelData.value || "")
                            )

                            contentItem: RowLayout {
                                spacing: 6

                                Controls.MaterialIcon {
                                    name: presetButton.selected
                                        ? "check" : "view-agenda"
                                    size: 15
                                    color: presetButton.contentColor
                                }

                                Label {
                                    Layout.fillWidth: true
                                    text: presetButton.text
                                    color: presetButton.contentColor
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    font.weight: presetButton.selected
                                        ? Font.DemiBold : Font.Normal
                                    elide: Text.ElideRight
                                    maximumLineCount: 1
                                }
                            }
                        }

                        ScrollBar.vertical: Controls.ScrollBar {
                            id: presetScrollBar
                            theme: root.theme
                            flickableTarget: presetList
                        }
                    }

                    Controls.EmptyState {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: presetList.count === 0
                        theme: root.theme
                        iconName: "view-agenda"
                        title: qsTr("No tab shelves")
                        message: qsTr("Create a shelf for this tab.")
                    }
                }
            }

            ColumnLayout {
                objectName: "scriptShelfEditorPane"
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: root.theme.controlHeight
                    spacing: 8

                    Controls.TextField {
                        id: shelfTitle
                        objectName: "scriptShelfTitle"
                        Layout.fillWidth: true
                        visible: root.controller.editorMode === "shared"
                            && root.shelfReady
                            && root.controller.canRename
                        theme: root.theme
                        enabled: !root.controller.busy
                        placeholderText: qsTr("Shelf name")
                        text: root.controller.editorTitle
                        onTextEdited: root.controller.set_editor_title(text)
                    }

                    Label {
                        objectName: "scriptShelfFixedTitle"
                        Layout.fillWidth: true
                        visible: root.shelfReady
                            && (root.controller.editorMode === "personal"
                                || !root.controller.canRename)
                        text: root.controller.editorTitle
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.title
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }

                    Controls.Button {
                        objectName: "applyScriptShelfButton"
                        visible: root.controller.editorMode === "shared"
                            && root.controller.sharedScope === "tab"
                            && root.shelfReady
                        theme: root.theme
                        highlighted: root.controller.assignmentPending
                            && !root.controller.editorDirty
                        text: root.controller.assignmentPending
                            ? qsTr("Apply to this tab")
                            : qsTr("Used on this tab")
                        icon.name: root.controller.assignmentPending
                            ? "push-pin" : "check"
                        enabled: root.controller.assignmentPending
                            && !root.controller.editorDirty
                            && !root.controller.busy
                        onClicked: root.controller.apply_to_current_tab()
                    }

                }

                RowLayout {
                    Layout.fillWidth: true
                    visible: root.shelfReady
                    spacing: 8

                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Shelf buttons")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                    }

                    Controls.Button {
                        objectName: "addScriptShelfButton"
                        theme: root.theme
                        text: qsTr("Add button")
                        icon.name: "add"
                        enabled: root.controller.scriptOptions.length > 0
                            && !root.controller.busy
                        onClicked: root.controller.add_button()
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: root.controller.error.length > 0
                    text: root.controller.error
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.WordWrap
                }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant
            radius: root.theme.surfaceRadius
            clip: true

            ListView {
                id: editorList
                objectName: "scriptShelfEditorList"
                anchors.fill: parent
                anchors.margins: 9
                rightMargin: editorScrollBar.reservedExtent + 4
                spacing: 7
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                model: root.controller.editorModel

                delegate: Rectangle {
                    id: buttonRow
                    required property int index
                    required property string title
                    required property string description
                    required property string iconName
                    required property string script
                    required property bool available

                    objectName: "scriptShelfButtonRow_" + index
                    width: editorList.width - editorList.rightMargin
                    height: 88
                    radius: root.theme.itemRadius
                    color: root.theme.row
                    border.width: 1
                    border.color: available
                        ? root.theme.outlineVariant : root.theme.error

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8

                        IconPickerButton {
                            Layout.preferredWidth: 36
                            Layout.preferredHeight: 36
                            Layout.alignment: Qt.AlignTop
                            theme: root.theme
                            iconName: buttonRow.iconName
                            onIconSelected: name => root.controller.update_button(
                                buttonRow.index, "iconName", name
                            )
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 6

                                Controls.TextField {
                                    Layout.preferredWidth: Math.max(
                                        120, editorList.width * 0.25
                                    )
                                    Layout.preferredHeight: 32
                                    theme: root.theme
                                    text: buttonRow.title
                                    placeholderText: qsTr("Button label")
                                    onTextEdited: root.controller.update_button(
                                        buttonRow.index, "title", text
                                    )
                                }

                                Controls.Button {
                                    id: scriptButton
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 32
                                    theme: root.theme
                                    text: buttonRow.script.length > 0
                                        ? buttonRow.script : qsTr("Choose script")
                                    toolTip: text
                                    onClicked: {
                                        root.scriptButtonRow = buttonRow.index
                                        scriptPicker.openFor(
                                            scriptButton, buttonRow.script
                                        )
                                    }

                                    contentItem: RowLayout {
                                        spacing: 7

                                        Controls.MaterialIcon {
                                            name: "account-tree"
                                            size: 16
                                            color: buttonRow.available
                                                ? root.theme.action
                                                : root.theme.error
                                        }

                                        Label {
                                            Layout.fillWidth: true
                                            text: scriptButton.text
                                            color: buttonRow.available
                                                ? root.theme.primaryText
                                                : root.theme.error
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.body
                                            elide: Text.ElideMiddle
                                        }

                                        Controls.MaterialIcon {
                                            name: "chevron-down"
                                            size: 14
                                            color: root.theme.secondaryText
                                        }
                                    }
                                }

                                Controls.CompactIconButton {
                                    theme: root.theme
                                    iconName: "arrow_upward"
                                    enabled: buttonRow.index > 0
                                    toolTip: qsTr("Move up")
                                    onClicked: root.controller.move_button(
                                        buttonRow.index, -1
                                    )
                                }
                                Controls.CompactIconButton {
                                    theme: root.theme
                                    iconName: "arrow_downward"
                                    enabled: buttonRow.index < editorList.count - 1
                                    toolTip: qsTr("Move down")
                                    onClicked: root.controller.move_button(
                                        buttonRow.index, 1
                                    )
                                }
                                Controls.CompactIconButton {
                                    theme: root.theme
                                    iconName: "delete"
                                    iconColor: root.theme.error
                                    toolTip: qsTr("Remove button")
                                    onClicked: root.controller.remove_button(
                                        buttonRow.index
                                    )
                                }
                            }

                            Controls.TextField {
                                objectName: "scriptShelfDescription_"
                                    + buttonRow.index
                                Layout.fillWidth: true
                                Layout.preferredHeight: 32
                                theme: root.theme
                                text: buttonRow.description
                                placeholderText: qsTr(
                                    "Description shown on hover"
                                )
                                onTextEdited: root.controller.update_button(
                                    buttonRow.index, "description", text
                                )
                            }
                        }
                    }
                }

                ScrollBar.vertical: Controls.ScrollBar {
                    id: editorScrollBar
                    theme: root.theme
                    flickableTarget: editorList
                }
            }

            Controls.EmptyState {
                anchors.centerIn: parent
                width: Math.min(parent.width - 32, 440)
                visible: editorList.count === 0
                theme: root.theme
                iconName: "view-agenda"
                title: root.shelfReady
                    ? qsTr("Add the first script button")
                    : qsTr("No shelf selected")
                message: root.shelfReady
                    ? qsTr("Only saved executable scripts are listed.")
                    : qsTr("Choose a shelf above or create a new one.")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: root.shelfReady
            spacing: 8

            Controls.Button {
                objectName: "deleteScriptShelfButton"
                visible: root.controller.canRemove
                theme: root.theme
                destructive: true
                text: root.controller.editorMode === "personal"
                    ? qsTr("Remove “%1”").arg(root.removeTargetTitle)
                    : qsTr("Delete “%1”").arg(root.removeTargetTitle)
                toolTip: text
                icon.name: "delete"
                enabled: !root.controller.busy
                onClicked: removeShelfDialog.open()
            }

            Item { Layout.fillWidth: true }

            Controls.Button {
                visible: root.controller.editorDirty
                theme: root.theme
                text: qsTr("Discard")
                icon.name: "undo"
                enabled: !root.controller.busy
                onClicked: root.controller.discard()
            }

            Controls.Button {
                objectName: "saveScriptShelfButton"
                theme: root.theme
                highlighted: true
                text: qsTr("Save shelf")
                icon.name: "cloud-done"
                enabled: (root.controller.editorDirty
                    || root.controller.assignmentPending)
                    && !root.controller.busy
                onClicked: {
                    if (root.controller.canRename)
                        root.controller.set_editor_title(shelfTitle.text)
                    root.controller.save()
                }
            }
        }
            }
        }
    }

    ScriptTreePicker {
        id: scriptPicker
        parent: Overlay.overlay
        theme: root.theme
        treeModel: scriptEditorModel
        treeController: scriptEditorController
        scriptOptions: root.controller.scriptOptions
        onScriptSelected: script => {
            if (root.scriptButtonRow >= 0)
                root.controller.update_button(
                    root.scriptButtonRow, "script", script
                )
            root.scriptButtonRow = -1
        }
        onClosed: root.scriptButtonRow = -1
    }

    Controls.Dialog {
        id: removeShelfDialog
        objectName: "removeScriptShelfDialog"
        parent: Overlay.overlay
        theme: root.theme
        title: root.controller.editorMode === "personal"
            ? qsTr("Remove “%1”?").arg(root.removeTargetTitle)
            : qsTr("Delete “%1”?").arg(root.removeTargetTitle)
        modal: true
        anchors.centerIn: parent
        width: 430
        onAccepted: root.controller.remove()

        contentItem: Label {
            objectName: "removeScriptShelfMessage"
            width: 382
            text: root.controller.editorMode === "personal"
                ? qsTr("The personal shelf “%1” will be removed. Shared shelves will not change.").arg(root.removeTargetTitle)
                : qsTr("The shared shelf “%1” and its sidebar assignments will be deleted. Affected tabs will use the project shelf.").arg(root.removeTargetTitle)
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }

        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: root.controller.editorMode === "personal"
                    ? qsTr("Remove") : qsTr("Delete")
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
