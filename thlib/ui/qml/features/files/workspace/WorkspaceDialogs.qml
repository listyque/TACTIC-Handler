import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import "../../../controls" as Controls
import "../../.." as TH
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/core/foundation.mjs" as Foundation
import "../../../tactic_frame/features/files/workspace/dialogs.ui.mjs" as UI
import "../../../tactic_frame/features/files/workspace/editors.ui.mjs" as Editors

Item {
    id: host
    required property var workspace
    property real mappingHeight: 40
    function actionWidths(actions) {
        return actions.map(action => UI.buttonWidth(buttonMetrics.advanceWidth(action.text), !!action.icon));
    }
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    FontMetrics {
        id: buttonMetrics
        font: Qt.font({
            family: workspace.theme.fontFamily,
            pixelSize: Foundation.textStyles.body,
            weight: Font.DemiBold,
            hintingPreference: Font.PreferVerticalHinting
        })
    }
    function promptModel(kind, values) {
        const content = UI.promptContent(kind, values, language);
        return Object.assign({}, values, {
            buttonWidths: content.actions.map(action => UI.buttonWidth(buttonMetrics.advanceWidth(action.text), !!action.icon))
        });
    }
    readonly property var reviewDialog: workspace.reviewWindow
    anchors.fill: parent
    property alias dropBlockedWindow: dropBlocked
    property alias dropConfirmWindow: dropConfirm
    property alias nonemptyDeleteWindow: nonemptyDelete
    property alias columnsDialogWindow: columnsDialog
    property alias manifestSaveWindow: manifestSave
    property alias targetDialogWindow: targetDialog
    property alias revisionDialogWindow: revisionDialog
    property alias actionMenuWindow: actionMenu
    property alias folderDialogWindow: folderDialog
    property alias saveDialogWindow: saveDialog
    property alias mergedDialogWindow: mergedDialog
    property alias revertDialogWindow: revertDialog
    property alias confirmationWindow: confirmation
    property alias editorWindow: editor
    property alias tabDialogWindow: tabDialog
    property alias switchDialogWindow: switchDialog
    property alias setupDialogWindow: setupDialog
    Controls.Dialog {
        id: dropBlocked
        objectName: "workspaceDropBlocked"
        property string message: ""
        theme: workspace.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(480, workspace.width - 32)
        title: qsTr("Files outside workspace")
        contentItem: Frame.FrameView {
            id: dropBlockedForm
            readonly property var model: host.promptModel("blocked", {
                message: dropBlocked.message
            })
            theme: workspace.theme
            implicitHeight: Math.max(100, Math.min(UI.promptHeight("blocked", model, dropBlocked.width - dropBlocked.leftPadding - dropBlocked.rightPadding, host.language), workspace.height - 138))
            scene: UI.prompt("blocked", model, width, height, host.language)
            onEvent: action => {
                if (action.type === "accept")
                    dropBlocked.accept();
            }
        }
        footer: null
        onOpened: Qt.callLater(() => dropBlockedForm.focusControl("workspaceDropBlockedOk"))
    }
    Controls.Dialog {
        id: dropConfirm
        objectName: "workspaceDropConfirm"
        theme: workspace.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(560, workspace.width - 24)
        title: qsTr("Add to changelist #%1").arg(workspace.dropDraft.number || "")
        contentItem: Frame.FrameView {
            id: dropConfirmForm
            readonly property var model: host.promptModel("drop", {
                origin: workspace.dropDraft.origin,
                count: workspace.dropDraft.count,
                busy: workspace.busy
            })
            theme: workspace.theme
            implicitHeight: Math.max(100, Math.min(UI.promptHeight("drop", model, dropConfirm.width - dropConfirm.leftPadding - dropConfirm.rightPadding, host.language), workspace.height - 138))
            scene: UI.prompt("drop", model, width, height, host.language)
            onEvent: action => {
                if (action.type === "accept" && !workspace.busy)
                    dropConfirm.accept();
                else if (action.type === "reject")
                    dropConfirm.reject();
            }
        }
        footer: null
        onAccepted: {
            if (workspace.dropDraft.origin === "shelf") {
                const shelf = JSON.parse(workspace.dropDraft.payload).rows[0].code;
                reviewDialog.operation = "unshelve_begin";
                reviewDialog.paths = [];
                reviewDialog.request = {
                    shelf: shelf
                };
                workspace.act("prepare_unshelve", {
                    shelf: shelf,
                    target: workspace.dropDraft.target
                });
                reviewDialog.open();
            } else
                workspace.act("drop_files", workspace.dropDraft);
        }
    }
    Controls.Dialog {
        id: nonemptyDelete
        objectName: "workspaceNonemptyDelete"
        theme: workspace.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(560, workspace.width - 24)
        title: qsTr("This changelist contains files")
        contentItem: Frame.FrameView {
            id: nonemptyDeleteForm
            readonly property var model: host.promptModel("nonempty", {
                busy: workspace.busy
            })
            theme: workspace.theme
            implicitHeight: Math.max(100, Math.min(UI.promptHeight("nonempty", model, nonemptyDelete.width - nonemptyDelete.leftPadding - nonemptyDelete.rightPadding, host.language), workspace.height - 138))
            scene: UI.prompt("nonempty", model, width, height, host.language)
            onEvent: action => {
                if (action.type === "reject")
                    nonemptyDelete.reject();
                else if (!workspace.busy && action.type === "move") {
                    nonemptyDelete.close();
                    workspace.command("move_all_files");
                } else if (!workspace.busy && action.type === "revert") {
                    nonemptyDelete.close();
                    workspace.command("revert");
                }
            }
        }
        footer: null
    }

    Controls.Dialog {
        id: columnsDialog
        objectName: "workspaceColumnsDialog"
        theme: workspace.theme
        title: qsTr("File columns")
        width: Math.min(560, workspace.width - 24)
        height: Math.min(560, workspace.height - 24)
        property var drafts: ({})
        property string notice: ""
        onOpened: {
            drafts = ({});
            notice = "";
        }
        contentItem: Frame.FrameView {
            theme: workspace.theme
            scene: UI.columns({
                columns: workspace.state.columns,
                widths: columnsDialog.drafts,
                notice: columnsDialog.notice
            }, width, height, host.language)
            onEvent: action => {
                const row = workspace.state.columns.find(row => row.key === action.key);
                if (action.type === "close") {
                    columnsDialog.close();
                    return;
                }
                if (!row)
                    return;
                if (action.type === "widthDraft") {
                    const next = Object.assign({}, columnsDialog.drafts);
                    next[action.key] = action.value;
                    columnsDialog.drafts = next;
                } else if (action.type === "width") {
                    if (!UI.validColumnWidth(action.value)) {
                        columnsDialog.notice = qsTr("Column width must be a whole number from 48 to 900");
                        return;
                    }
                    workspace.controller.configure_column(row.key, Number(action.value), row.visible);
                    const next = Object.assign({}, columnsDialog.drafts);
                    delete next[row.key];
                    columnsDialog.drafts = next;
                    columnsDialog.notice = "";
                } else if (action.type === "visible")
                    workspace.controller.configure_column(row.key, row.width, action.value);
                else if (action.type === "move")
                    workspace.controller.move_column(row.key, action.value);
            }
        }
    }
    FileDialog {
        id: manifestSave
        title: qsTr("Export selected file manifest")
        fileMode: FileDialog.SaveFile
        onAccepted: workspace.act("export_query", {
            destination: String(selectedFile)
        })
    }
    FileWorkspaceTargetDialog {
        id: targetDialog
        theme: workspace.theme
        controller: workspace.controller
        onUnshelveRequested: shelf => {
            reviewDialog.operation = "unshelve_begin";
            reviewDialog.paths = [];
            reviewDialog.request = {
                shelf: shelf
            };
            reviewDialog.open();
        }
    }
    FileWorkspaceGetRevisionDialog {
        id: revisionDialog
        theme: workspace.theme
        controller: workspace.controller
    }
    TH.ActionMenu {
        id: actionMenu
        objectName: "workspaceActionMenu"
        theme: workspace.theme
        onTriggered: command => workspace.command(command)
    }
    FolderDialog {
        id: folderDialog
        title: qsTr("Choose local workspace folder")
        onAccepted: workspace.controller.choose_root(String(selectedFolder))
    }
    FileDialog {
        id: saveDialog
        title: qsTr("Save revision")
        fileMode: FileDialog.SaveFile
        onAccepted: workspace.act("save_revision", Object.assign({}, workspace.downloadValues, {
            destination: String(selectedFile)
        }))
    }
    FileDialog {
        id: mergedDialog
        title: qsTr("Choose merged file")
        fileMode: FileDialog.OpenFile
        onAccepted: workspace.act("merged_file", {
            file: String(selectedFile),
            path: workspace.mergePath
        })
    }
    FileWorkspaceRevertDialog {
        id: revertDialog
        theme: workspace.theme
        busy: workspace.busy
        anchors.centerIn: parent
        width: Math.min(480, workspace.width - 32)
        onConfirmed: (operation, values) => workspace.act(operation, values)
    }
    Controls.Dialog {
        id: confirmation
        objectName: "workspaceConfirmation"
        property var deleteTargets: []
        theme: workspace.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(480, workspace.width - 32)
        readonly property string actionLabel: UI.confirmationTitle(workspace.confirmationAction, host.language)
        title: confirmation.actionLabel
        contentItem: Frame.FrameView {
            id: confirmationForm
            readonly property var model: host.promptModel("confirm", {
                action: workspace.confirmationAction,
                targets: confirmation.deleteTargets,
                busy: workspace.busy
            })
            theme: workspace.theme
            implicitHeight: Math.max(100, Math.min(UI.promptHeight("confirm", model, confirmation.width - confirmation.leftPadding - confirmation.rightPadding, host.language), workspace.height - 138))
            scene: UI.prompt("confirm", model, width, height, host.language)
            onEvent: action => {
                if (action.type === "reject")
                    confirmation.reject();
                else if (action.type === "accept" && !workspace.busy)
                    confirmation.accept();
            }
        }
        footer: null
        onOpened: Qt.callLater(() => confirmationForm.focusControl("workspaceConfirmationCancel"))
        onAccepted: ["query_delete", "query_revert"].indexOf(workspace.confirmationAction) >= 0 ? workspace.act("bulk_query", {
            operation: workspace.confirmationAction === "query_delete" ? "mark_delete" : "remove_files"
        }) : workspace.confirmationAction === "mark_delete" ? workspace.pickTarget("mark_delete") : workspace.act(workspace.confirmationAction, workspace.confirmationAction === "delete_change" ? {
            changes: confirmation.deleteTargets.map(row => ({
                        change: row.change,
                        edit_revision: row.edit_revision
                    }))
        } : {})
    }
    Controls.Dialog {
        id: editor
        objectName: "workspaceEditor"
        theme: workspace.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(560, workspace.width - 24)
        title: UI.editorTitle(workspace.editKind, host.language)
        standardButtons: Dialog.NoButton
        footer: null
        onAccepted: workspace.saveEditor()
        contentItem: Frame.FrameView {
            theme: workspace.theme
            implicitHeight: Math.max(120, Math.min(150, workspace.height - 138))
            scene: UI.editor({
                kind: workspace.editKind,
                draft: workspace.draft,
                busy: workspace.busy
            }, width, height, host.language)
            onEvent: action => {
                if (action.type === "draft")
                    workspace.draft = action.value;
                else if (action.type === "reject")
                    editor.reject();
                else if (action.type === "accept" && !workspace.busy)
                    editor.accept();
            }
        }
    }
    Controls.Dialog {
        id: tabDialog
        objectName: "workspaceTabEditor"
        theme: workspace.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(560, workspace.width - 24)
        title: qsTr("Edit view tab")
        standardButtons: Dialog.NoButton
        footer: null
        onAccepted: workspace.controller.configure_tab(workspace.tabDraft)
        contentItem: Frame.FrameView {
            readonly property var values: ({
                    draft: workspace.tabDraft,
                    presets: workspace.controller.view_presets,
                    busy: workspace.busy
                })
            readonly property var model: Object.assign({}, values, {
                buttonWidths: host.actionWidths(Editors.actions("workspaceTab", values, host.language))
            })
            theme: workspace.theme
            implicitHeight: Math.max(120, Math.min(Editors.tab(model, tabDialog.width - tabDialog.leftPadding - tabDialog.rightPadding, 0, host.language).preferredHeight, workspace.height - 138))
            scene: Editors.tab(model, width, height, host.language)
            onEvent: action => {
                if (action.type === "field" && ["title", "preset", "source", "scope", "prefix", "pinned"].includes(action.key)) {
                    const next = Object.assign({}, workspace.tabDraft);
                    next[action.key] = action.value;
                    workspace.tabDraft = next;
                } else if (action.type === "reject")
                    tabDialog.reject();
                else if (action.type === "accept" && !workspace.busy)
                    tabDialog.accept();
            }
        }
    }
    Connections {
        target: workspace.controller
        function onDropRejected(message) {
            dropBlocked.message = message;
            dropBlocked.open();
        }
        function onDetailsCommandRequested(command) {
            workspace.command(command);
        }
        function onStateChanged() {
            if (workspace.movingWholeChange && !workspace.busy) {
                workspace.movingWholeChange = false;
                if (!workspace.state.error && workspace.state.selection_query)
                    workspace.pickTarget("bulk_move");
            }
            if (workspace.pendingFileMenu && !workspace.busy) {
                const pending = workspace.pendingFileMenu;
                workspace.pendingFileMenu = null;
                if (!workspace.state.error && workspace.state.change.code === pending.change) {
                    actionMenu.actions = workspace.actions("files");
                    actionMenu.openAt(workspace, pending.x, pending.y);
                }
            }
            if (workspace.state.setup && !workspace.busy && !setupDialog.opened)
                setupDialog.open();
            if (!workspace.state.setup && setupDialog.opened)
                setupDialog.close();
        }
    }
    Controls.Dialog {
        id: switchDialog
        objectName: "workspaceSwitchDialog"
        theme: workspace.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(520, workspace.width - 24)
        title: qsTr("Switch workspace?")
        standardButtons: Dialog.NoButton
        footer: null
        contentItem: Frame.FrameView {
            id: switchDialogForm
            readonly property var model: host.promptModel("switch", {
                previous: workspace.state.switch_preview.previous,
                workspace: workspace.state.switch_preview.workspace,
                busy: workspace.busy
            })
            theme: workspace.theme
            implicitHeight: Math.max(100, Math.min(UI.promptHeight("switch", model, switchDialog.width - switchDialog.leftPadding - switchDialog.rightPadding, host.language), workspace.height - 138))
            scene: UI.prompt("switch", model, width, height, host.language)
            onEvent: action => {
                if (action.type === "reject")
                    switchDialog.reject();
                else if (action.type === "accept" && !workspace.busy)
                    switchDialog.accept();
            }
        }
        onAccepted: workspace.act("choose_workspace", {
            workspace: workspace.state.switch_preview.workspace,
            revision: workspace.state.switch_preview.revision
        })
    }
    Controls.Dialog {
        id: setupDialog
        theme: workspace.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(620, workspace.width - 24)
        height: Math.min(580, workspace.height - 24)
        title: workspace.state.editing_workspace ? qsTr("Edit workspace") : qsTr("Workspace setup")
        onRejected: workspace.set("setup", false)
        footer: null
        contentItem: Frame.FrameView {
            readonly property var values: ({
                    editing: workspace.state.editing_workspace,
                    kind: workspace.state.setup_kind,
                    code: workspace.state.code,
                    stream: workspace.state.stream,
                    root: workspace.state.root,
                    case_sensitive: workspace.state.case_sensitive,
                    depot: workspace.state.depot,
                    source: workspace.state.source,
                    previewPath: workspace.previewPath,
                    mappingHeight: host.mappingHeight,
                    mappingPreview: workspace.state.mapping_preview.items || [],
                    busy: workspace.busy,
                    progress: workspace.phase(workspace.state.progress.phase || workspace.state.progress.state),
                    error: workspace.state.error
                })
            readonly property var model: Object.assign({}, values, {
                buttonWidths: host.actionWidths(Editors.actions("workspaceSetup", values, host.language))
            })
            theme: workspace.theme
            scene: Editors.setup(model, width, height, host.language)
            views: ({
                    mappings: {
                        component: mappingsPort
                    }
                })
            onEvent: action => {
                if (action.type === "kind") {
                    if (action.value === "depot") {
                        workspace.set("setup", false);
                        workspace.controller.open_view("depots");
                        workspace.controller.action("depot_editor", {});
                    } else
                        workspace.set("setup_kind", action.value);
                } else if (action.type === "field") {
                    if (action.key === "previewPath")
                        workspace.previewPath = action.value;
                    else if (["code", "stream", "root", "case_sensitive", "depot", "source"].includes(action.key)) {
                        workspace.set(action.key, action.value);
                        if (action.key === "case_sensitive")
                            workspace.set("mapping_preview", {});
                    }
                } else if (action.type === "preview")
                    workspace.act("workspace_preview", {
                        paths: workspace.previewPath ? [
                            {
                                stream: workspace.state.stream,
                                path: workspace.previewPath
                            }
                        ] : []
                    });
                else if (action.type === "reject") {
                    if (workspace.busy)
                        workspace.controller.stop();
                    else {
                        workspace.set("setup", false);
                        setupDialog.close();
                    }
                } else if (action.type === "accept" && !workspace.busy)
                    workspace.act(workspace.state.editing_workspace ? "update_workspace" : "create_" + workspace.state.setup_kind);
            }
        }
    }

    Component {
        id: mappingsPort
        FileWorkspaceMappings {
            theme: workspace.theme
            value: workspace.state.mappings
            primaryStream: workspace.state.stream
            enabledEditing: !workspace.busy
            onImplicitHeightChanged: host.mappingHeight = implicitHeight
            Component.onCompleted: host.mappingHeight = implicitHeight
            onEdited: value => {
                workspace.set("mappings", value);
                workspace.set("mapping_preview", {});
            }
        }
    }
}
