import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/search/presets.ui.mjs" as UI
import "tactic_frame/features/search/editors.ui.mjs" as Editor

Rectangle {
    id: root

    required property var theme
    required property var controller
    required property var application
    required property var presets
    readonly property bool compactLayout: width < 560
    readonly property bool hasSelectedPreset: root.controller.selected_preset >= 0 && root.controller.selected_preset < root.presets.count()
    property string presetTitle: ""
    property string presetAction: "save"

    function openPresetDialog(action) {
        presetAction = action;
        root.presetTitle = action === "rename" ? root.controller.tab_title : action === "duplicate" ? root.controller.tab_title + " copy" : root.application.current_search_tab_title;
        presetDialog.open();
        nameContent.focusControl("presetNameField");
    }

    height: UI.barHeight
    radius: root.theme.itemRadius
    color: root.theme.panelDeep

    property int presetRevision: 0
    readonly property var frameModel: {
        const revision = presetRevision;
        const rows = [];
        for (let index = 0; index < root.presets.count(); index++)
            rows.push(root.presets.get(index));
        return {
            presets: rows,
            selected: root.hasSelectedPreset ? rows[root.controller.selected_preset].view : "",
            busy: root.controller.busy,
            canManage: true
        };
    }
    Connections {
        target: root.presets
        function onContentReplaced() {
            root.presetRevision++;
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
        onEvent: (action, source) => {
            if (action.type === "pressMore")
                presetActions.sourceWasOpen = presetActions.opened;
            else if (action.type === "selectPreset") {
                const index = root.frameModel.presets.findIndex(preset => preset.view === action.value);
                if (index >= 0)
                    root.controller.select_preset_for_current_search(index);
            } else if (action.type === "update")
                root.controller.update_selected_from_current_search();
            else if (action.type === "new")
                root.openPresetDialog("save");
            else if (action.type === "more")
                presetActions.toggleBelow(source);
        }
    }
    ActionMenu {
        id: presetActions
        objectName: "searchPresetActions"
        parent: Overlay.overlay
        theme: root.theme
        actions: UI.actions(root.frameModel)
        onTriggered: command => {
            if (command === "rename")
                root.openPresetDialog("rename");
            else if (command === "duplicate")
                root.openPresetDialog("duplicate");
            else if (command === "copy_link")
                root.controller.copy_selected_search_link();
            else if (command === "delete")
                deleteDialog.open();
            else if (command === "refresh")
                root.controller.load_presets();
        }
    }

    Controls.Dialog {
        id: presetDialog
        theme: root.theme
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(390, root.width - 24)
        modal: true
        title: root.presetAction === "rename" ? qsTr("Rename preset") : root.presetAction === "duplicate" ? qsTr("Duplicate preset") : qsTr("Save filter preset")
        onAccepted: {
            if (root.presetAction === "rename")
                root.controller.rename(root.presetTitle);
            else if (root.presetAction === "duplicate")
                root.controller.duplicate_current_search(root.presetTitle);
            else
                root.controller.save_current_search_as(root.presetTitle);
        }
        contentItem: Frame.FrameView {
            id: nameContent
            width: Math.max(220, presetDialog.width - 48)
            height: 116
            theme: root.theme
            scene: Editor.presetName({
                title: root.presetTitle,
                busy: root.controller.busy
            }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: action => {
                if (action.type === "title")
                    root.presetTitle = action.value;
                else if (action.type === "close")
                    presetDialog.reject();
                else if (action.type === "save" && root.presetTitle.trim().length && !root.controller.busy)
                    presetDialog.accept();
            }
        }
        footer: null
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
