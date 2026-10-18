import QtQuick
import QtQuick.Controls
import "../../" as TH
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/scripts/shelf.ui.mjs" as UI

Frame.FrameView {
    id: root
    property var controller: sidebarEditorController.scriptShelf
    property string pendingButton: ""
    property string pendingScope: ""
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    readonly property var projection: ({
            owner: controller.editorMode,
            scope: controller.editorMode === "personal" ? controller.personalScope : controller.sharedScope,
            title: controller.editorTitle,
            canManage: controller.canManage,
            canWrite: controller.editorMode === "personal" || controller.canManage,
            canRename: controller.canRename,
            canRemove: controller.canRemove,
            removeName: controller.removeTargetTitle,
            canAssign: controller.canRename,
            assignmentPending: controller.assignmentPending,
            dirty: controller.editorDirty,
            busy: controller.busy,
            running: controller.executionBusy === true,
            ready: controller.editorMode !== "shared" || controller.editorView.length > 0,
            existing: true,
            hasScripts: controller.scriptOptions.length > 0,
            error: controller.error,
            contextChanged: controller.editorContextChanged === true,
            notice: controller.editorContextChanged === true ? qsTr("Connection context changed. Discard this draft before saving.") : "",
            count: controller.editorModel.count(),
            selectedPreset: controller.editorMode === "personal" ? controller.personalScope : controller.editorView,
            scopeKey: [controller.editorContextKey || "", controller.editorMode, controller.personalScope, controller.editorView].join("/")
        })
    readonly property var presets: controller.editorMode === "personal" ? controller.personalScopeOptions.filter(row => row.value !== "global") : controller.sharedTabOptions
    models: ({
            presets: root.presets,
            buttons: root.controller.editorModel
        })
    views: ({
            script: {
                component: scriptChoice,
                nodeProps: true
            }
        })
    scene: UI.describe(projection, width, height, language)
    describeRow: (list, record, index) => UI.row(list, record, index, root.projection, root.language)
    function indexFor(id) {
        return root.controller.editorModel.records().findIndex(row => row.buttonId === id);
    }
    function chooseScript(record, scope, anchor) {
        if (!UI.permissions(root.projection).edit || scope !== root.projection.scopeKey)
            return;
        root.pendingButton = record.buttonId;
        root.pendingScope = scope;
        scriptPicker.openFor(anchor, record.script);
    }
    onEvent: action => {
        if (action.type === "help")
            windowModel.open_help("script_shelf");
        else if (action.type === "owner")
            controller.set_editor_mode(action.value);
        else if (action.type === "global")
            controller.editorMode === "personal" ? controller.set_personal_scope("global") : controller.set_shared_scope("global");
        else if (action.type === "preset")
            controller.editorMode === "personal" ? controller.set_personal_scope(action.value) : controller.select_shared(action.value);
        else if (action.type === "new")
            controller.create_shared();
        else if (action.type === "title")
            controller.set_editor_title(action.value);
        else if (action.type === "assign")
            controller.apply_to_current_tab();
        else if (action.type === "add")
            controller.add_button();
        else if (action.type === "remove")
            removeShelfDialog.open();
        else if (action.type === "discard")
            controller.discard();
        else if (action.type === "save")
            controller.save();
        else {
            const index = root.indexFor(action.buttonId);
            if (index < 0 || !UI.permissions(root.projection).edit)
                return;
            if (action.type === "button")
                controller.update_button(index, action.field, action.value);
            else if (action.type === "removeButton")
                controller.remove_button(index);
            else if (action.type === "up" || action.type === "down")
                controller.move_button(index, action.type === "up" ? -1 : 1);
        }
    }
    Component {
        id: scriptChoice
        Frame.FrameView {
            id: choice
            property var frameNode: ({
                    id: "",
                    record: {},
                    width: 0,
                    height: 0,
                    enabled: false
                })
            theme: root.theme
            scene: UI.scriptPicker(frameNode, root.language)
            onEvent: action => {
                if (action.type === "pick")
                    root.chooseScript(frameNode.record, frameNode.scopeKey, choice);
            }
        }
    }
    TH.ScriptTreePicker {
        id: scriptPicker
        parent: Overlay.overlay
        theme: root.theme
        treeModel: scriptEditorModel
        treeController: scriptEditorController
        scriptOptions: root.controller.scriptOptions
        onScriptSelected: script => {
            const index = root.indexFor(root.pendingButton);
            if (index >= 0 && root.pendingScope === root.projection.scopeKey && UI.permissions(root.projection).edit)
                root.controller.update_button(index, "script", script);
            root.pendingButton = "";
        }
        onClosed: root.pendingButton = ""
    }
    Controls.Dialog {
        id: removeShelfDialog
        objectName: "removeScriptShelfDialog"
        parent: Overlay.overlay
        theme: root.theme
        title: root.controller.editorMode === "personal" ? qsTr("Remove “%1”?").arg(root.controller.removeTargetTitle) : qsTr("Delete “%1”?").arg(root.controller.removeTargetTitle)
        modal: true
        anchors.centerIn: parent
        width: Math.min(430, parent ? parent.width - 24 : 430)
        onAccepted: root.controller.remove()
        contentItem: Label {
            objectName: "removeScriptShelfMessage"
            width: 382
            text: root.controller.editorMode === "personal" ? qsTr("The personal shelf “%1” will be removed. Shared shelves will not change.").arg(root.controller.removeTargetTitle) : qsTr("The shared shelf “%1” and its sidebar assignments will be deleted. Affected tabs will use the project shelf.").arg(root.controller.removeTargetTitle)
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: root.controller.editorMode === "personal" ? qsTr("Remove") : qsTr("Delete")
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
