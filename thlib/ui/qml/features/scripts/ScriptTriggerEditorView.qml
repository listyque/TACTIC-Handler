import QtQuick
import QtQuick.Controls
import "../../" as TH
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/scripts/triggers.ui.mjs" as UI

Frame.FrameView {
    id: root
    readonly property var controller: scriptTriggerController
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property string pendingRule: ""
    property string pendingAction: ""
    property int pendingEpoch: -1
    readonly property var projection: ({
            rule: controller.selectedRule,
            selected: controller.selectedRow,
            busy: controller.busy,
            canManage: controller.canManage,
            dirty: controller.dirty,
            error: controller.error,
            count: controller.model.count(),
            actions: controller.actionOptions,
            phases: controller.phaseOptions,
            searchTypes: controller.searchTypeOptions
        })
    models: ({
            rules: scriptTriggerModel
        })
    views: ({
            script: pickerChoice
        })
    scene: UI.describe(projection, width, height, language)
    describeRow: (list, record, index) => UI.row(list, record, index, root.projection)
    onEvent: action => {
        if (action.type === "help")
            windowModel.open_help("script_triggers");
        else if (action.type === "reload")
            controller.dirty ? reloadConfirmation.open() : controller.refresh();
        else if (action.type === "select")
            controller.select(action.value);
        else if (action.type === "field")
            controller.update(action.field, action.value);
        else if (action.type === "add")
            controller.add();
        else if (action.type === "up" || action.type === "down")
            controller.move(action.type === "up" ? -1 : 1);
        else if (action.type === "remove")
            controller.remove();
        else if (action.type === "discard")
            controller.discard();
        else if (action.type === "save")
            controller.save();
    }
    Component {
        id: pickerChoice
        Controls.Button {
            id: choice
            theme: root.theme
            text: root.controller.selectedRule.script || qsTr("Choose script")
            icon.name: "account-tree"
            enabled: root.controller.canManage && !!root.controller.selectedRule.ruleId && !root.controller.busy
            onClicked: {
                root.pendingRule = root.controller.selectedRule.ruleId;
                root.pendingAction = root.controller.selectedRule.action;
                root.pendingEpoch = root.controller.documentEpoch;
                scriptPicker.openFor(choice, root.controller.selectedRule.script || "");
            }
        }
    }
    TH.ScriptTreePicker {
        id: scriptPicker
        parent: Overlay.overlay
        theme: root.theme
        treeModel: scriptEditorModel
        treeController: scriptEditorController
        scriptOptions: root.controller.compatibleScriptOptions
        onScriptSelected: script => {
            if (!root.controller.busy && root.controller.canManage && root.pendingRule === root.controller.selectedRule.ruleId && root.pendingAction === root.controller.selectedRule.action && root.pendingEpoch === root.controller.documentEpoch)
                root.controller.update("script", script);
        }
    }
    Controls.Dialog {
        id: reloadConfirmation
        objectName: "reloadTriggerConfirmation"
        theme: root.theme
        title: qsTr("Discard changes?")
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(420, parent ? parent.width - 24 : 420)
        modal: true
        contentItem: Label {
            text: qsTr("Reloading discards unsaved changes.")
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Discard")
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
        onAccepted: root.controller.refresh()
    }
}
