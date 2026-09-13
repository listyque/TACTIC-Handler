import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    required property var controller
    required property var application
    required property var presets
    readonly property bool compactLayout: width < 560
    readonly property bool hasSelectedPreset:
        root.controller.selected_preset >= 0
        && root.controller.selected_preset < savedSearchCombo.count
    property string presetAction: "save"

    function openPresetDialog(action) {
        presetAction = action
        presetName.text = action === "rename"
            ? root.controller.tab_title
            : action === "duplicate"
                ? root.controller.tab_title + " copy"
                : root.application.current_search_tab_title
        presetDialog.open()
        presetName.forceActiveFocus()
        presetName.selectAll()
    }

    height: 56
    radius: root.theme.itemRadius
    color: root.theme.panelDeep

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 10
        spacing: 8

        Controls.MaterialIcon {
            name: "save"
            size: 17
            color: root.theme.action
        }

        Label {
            visible: !root.compactLayout
            text: qsTr("Saved searches")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
        }

        Controls.ComboBox {
            id: savedSearchCombo
            objectName: "advancedSearchPresetCombo"
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.preferredHeight: root.theme.controlHeight
            theme: root.theme
            model: root.presets
            textRole: "title"
            translateDisplayText: false
            currentIndex: root.controller.selected_preset
            enabled: count > 0 && !root.controller.busy
            displayText: currentIndex >= 0 && currentIndex < count
                ? currentText : qsTr("Select a saved search")
            onActivated:
                root.controller
                    .select_preset_for_current_search(currentIndex)
        }

        Controls.BusyIndicator {
            uiTheme: root.theme
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28
            running: root.controller.busy
            visible: running
        }

        Controls.CompactIconButton {
            theme: root.theme
            iconName: "save"
            toolTip: qsTr("Update selected preset")
            enabled: root.hasSelectedPreset
                && !root.controller.busy
            onClicked:
                root.controller
                    .update_selected_from_current_search()
        }
        Controls.CompactIconButton {
            theme: root.theme
            iconName: "add"
            toolTip: qsTr("Save as new preset")
            enabled: !root.controller.busy
            onClicked: root.openPresetDialog("save")
        }
        Controls.CompactIconButton {
            id: presetMoreButton
            theme: root.theme
            iconName: "more_vert"
            toolTip: qsTr("Saved search actions")
            onClicked: presetActions.toggleBelow(presetMoreButton)
        }
    }
    ActionMenu {
        id: presetActions
        parent: Overlay.overlay
        theme: root.theme
        actions: [
            {
                "title": "Saved search actions",
                "header": true
            },
            {
                "title": "Rename preset",
                "icon": "rename",
                "command": "rename",
                "enabled": root.hasSelectedPreset
                    && !root.controller.busy
            },
            {
                "title": "Duplicate preset",
                "icon": "duplicate",
                "command": "duplicate",
                "enabled": root.hasSelectedPreset
                    && !root.controller.busy
            },
            {
                "title": "Copy saved search link",
                "icon": "link",
                "command": "copy_link",
                "enabled": root.hasSelectedPreset
                    && root.controller.selected_preset_link.length > 0
                    && !root.controller.busy
            },
            {
                "title": "Delete preset",
                "icon": "delete",
                "command": "delete",
                "enabled": root.hasSelectedPreset
                    && !root.controller.busy
            },
            {"separator": true},
            {
                "title": "Refresh saved searches",
                "icon": "refresh",
                "command": "refresh",
                "enabled": !root.controller.busy
            }
        ]
        onTriggered: command => {
            if (command === "rename")
                root.openPresetDialog("rename")
            else if (command === "duplicate")
                root.openPresetDialog("duplicate")
            else if (command === "copy_link")
                root.controller.copy_selected_search_link()
            else if (command === "delete")
                deleteDialog.open()
            else if (command === "refresh")
                root.controller.begin_search_session()
        }
    }

    Controls.Dialog {
        id: presetDialog
        theme: root.theme
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(390, root.width - 24)
        modal: true
        title: root.presetAction === "rename" ? qsTr("Rename preset")
            : root.presetAction === "duplicate" ? qsTr("Duplicate preset")
            : qsTr("Save filter preset")
        onAccepted: {
            if (root.presetAction === "rename")
                root.controller.rename(presetName.text)
            else if (root.presetAction === "duplicate")
                root.controller.duplicate_current_search(presetName.text)
            else
                root.controller.save_current_search_as(presetName.text)
        }
        contentItem: Controls.TextField {
            id: presetName
            theme: root.theme
            width: Math.max(220, presetDialog.width - 48)
            placeholderText: qsTr("Preset name")
            Keys.onReturnPressed: presetDialog.accept()
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Save")
                highlighted: true
                enabled: presetName.text.trim().length > 0
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
        id: deleteDialog
        theme: root.theme
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(390, root.width - 24)
        modal: true
        title: qsTr("Delete saved filter?")
        onAccepted: root.controller.delete_selected()
        contentItem: Label {
            width: Math.max(220, deleteDialog.width - 48)
            text: qsTr("The preset will be removed from the TACTIC server.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            wrapMode: Text.WordWrap
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
