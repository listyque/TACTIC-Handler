import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "../../../controls" as Controls
import "../../../tactic_frame/features/files/workspace/presentation.mjs" as Presentation
import "../../../FileWorkspaceMenus.js" as Menus
import "WorkspaceCommands.js" as NativeCommands
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/rows.ui.mjs" as Rows

Item {
    id: root
    objectName: "fileWorkspaceView"
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property alias reviewWindow: reviewDialog
    required property var theme
    required property var controller
    readonly property var workspaceState: controller.view_data
    readonly property bool busy: controller.busy
    readonly property bool pending: root.workspaceState.change.state === "pending"
    readonly property bool transferring: Boolean(root.workspaceState.change.active_transfer)
    readonly property bool integrating: Boolean(root.workspaceState.change.integration)
    readonly property bool narrow: width < 800
    readonly property var activeTab: (root.workspaceState.tabs || []).find(tab => tab.id === root.workspaceState.active_tab) || ({
            kind: "",
            title: ""
        })
    readonly property string detailsView: ["history", "conflicts", "tasks"].indexOf(activeTab.kind) >= 0 ? activeTab.kind : "history"
    property var tabDraft: ({})
    property string historyIdentity: ""
    property var detail: ({})
    property bool showResolved: false
    property string comparisonToken: ""
    property string switchToken: ""
    property string previewPath: ""
    property var pendingFileMenu: null
    property string confirmationAction: ""
    property var downloadValues: ({})
    property string mergePath: ""
    property var contextRow: ({})
    property string contextScope: ""
    property var dropDraft: ({})
    property bool movingWholeChange: false
    function pickTarget(operation, mode) {
        targetDialog.operation = operation;
        targetDialog.mode = mode || "ordinary";
        targetDialog.sourceChange = ["move_files", "bulk_move", "unshelve_begin"].indexOf(operation) >= 0 ? root.workspaceState.change.code : "";
        targetDialog.target = ["move_files", "bulk_move", "bulk_checkout"].indexOf(operation) >= 0 ? "" : root.workspaceState.change.state === "pending" ? root.workspaceState.change.code : "";
        targetDialog.creating = !targetDialog.target && !root.workspaceState.targets.length;
        targetDialog.open();
    }
    function contextMenu(scope, row, item, x, y) {
        contextRow = row;
        contextScope = scope;
        controller.select_row(scope, scope === "files" ? controller.row_identity(row) : row.id || row.code, 0, true);
        actionMenu.actions = actions(row.kind === "change" ? "change" : row.kind === "file" || !row.kind && row.path ? "files" : "tree");
        actionMenu.openAt(item, x, y);
    }
    function stageDrop(target, payload, urls) {
        const targetRow = root.workspaceState.changes.find(row => row.code === target);
        if (!targetRow || Menus.dropReason(root, Object.assign({
            kind: "change"
        }, targetRow), payload, urls))
            return;
        let count = (urls || []).length, origin = "explorer";
        if (payload) {
            try {
                const data = JSON.parse(payload);
                count = data.rows.length;
                origin = data.scope === "workspace" || data.scope === "files" && data.source === "local" ? "local" : data.rows.every(row => row.parent && (!row.change_state || row.change_state === "pending")) ? "move" : data.rows.length === 1 && data.rows[0].state === "shelved" ? "shelf" : "depot";
            } catch (error) {
                return;
            }
        }
        const change = root.workspaceState.changes.find(row => row.code === target);
        dropDraft = {
            target: target,
            number: change ? change.number : target,
            count: count,
            origin: origin,
            payload: payload || "",
            urls: urls || [],
            project: "",
            prefix: root.workspaceState.view === "local" ? root.workspaceState.prefix : ""
        };
        if (origin === "local" || origin === "explorer")
            root.act("drop_files", dropDraft);
        else
            dropConfirm.open();
    }
    function openRevert(operation) {
        revertDialog.operation = operation;
        if (operation === "revert") {
            revertDialog.request = {
                change: root.workspaceState.change.code,
                edit_revision: root.workspaceState.change.edit_revision
            };
            revertDialog.caption = qsTr("Changelist #%1").arg(root.workspaceState.change.number || root.workspaceState.change.code);
        } else {
            const rows = Object.values(root.workspaceState.selection_records || {});
            revertDialog.request = {
                files: rows.map(row => Object.assign({
                        stream: row.stream || root.workspaceState.stream,
                        path: row.source_path || row.path
                    }, row.parent ? {
                        change: row.parent
                    } : {}))
            };
            revertDialog.caption = qsTr("Selected items: %1").arg(rows.length);
        }
        revertDialog.open();
    }
    function fileKey(event, scope) {
        NativeCommands.fileKey(root, event, scope, {
            files: files,
            changes: changes,
            depot: tree.depotList,
            workspace: tree.workspaceList,
            history: historyView.listView
        }, ListView.Contain);
    }

    readonly property real columnWidth: root.workspaceState.columns.filter(column => column.visible).reduce((sum, column) => sum + column.width, 81 + 6 * root.workspaceState.columns.filter(column => column.visible).length + (root.activeTab.kind === "changes" ? 24 : 0))
    readonly property bool editable: root.workspaceState.change.owner === root.controller.current_user && root.workspaceState.change.workspace === root.workspaceState.workspace && pending && root.workspaceState.change.depot_writable !== false && !transferring && !integrating && !root.workspaceState.change.active_bulk && !busy
    property bool treeOpen: false
    property string editKind: ""
    property string draft: ""

    function act(name, values) {
        controller.action(name, values || {});
    }
    function set(name, value) {
        controller.set_value(name, value);
    }
    function changeState(value) {
        return value === "pending" ? qsTr("Pending") : value === "submitted" ? qsTr("Submitted") : value === "shelved" ? qsTr("Shelved") : qsTr("Reverted");
    }
    function treeTitle(row) {
        return Rows.treeTitle(row, language);
    }
    function depotActivated(row) {
        if (row.kind === "more")
            act("more_depot", {
                id: row.parent
            });
        else if (row.kind === "depot")
            act("toggle_depot", {
                id: row.id
            });
        else if (row.kind === "file")
            return;
        else if (root.workspaceState.tree_selection !== row.id || root.workspaceState.selection_scope !== "depot")
            controller.select_row("depot", row.id, 0);
    }
    function changeActivated(row) {
        if (row.kind === "more")
            act("more_change", {
                change: row.parent
            });
        else if (row.kind === "change")
            return;
        else {
            controller.open_view("history");
            act("history", {
                stream: row.stream,
                path: row.path
            });
        }
    }
    function selectTab(tab) {
        detail = {};
        controller.activate_tab(tab.id);
    }
    function editTab(creating) {
        const current = creating ? controller.view_presets[0] : activeTab;
        const preset = controller.view_presets.find(row => row.kind === current.kind && (row.kind !== "changes" || row.state === current.state)) || controller.view_presets[0];
        tabDraft = {
            id: creating ? "" : current.id,
            title: creating ? "" : current.title,
            preset: preset.id,
            source: current.source || "depot",
            prefix: current.prefix || "",
            scope: current.scope || "mine",
            pinned: current.pinned || false
        };
        tabDialog.open();
    }
    function workspaceActivated(row) {
        if (row.kind === "more")
            act("more_workspace_tree", {
                id: row.parent
            });
        else if (row.kind === "file")
            return;
        else if (root.workspaceState.tree_selection !== row.id || root.workspaceState.selection_scope !== "workspace")
            controller.select_row("workspace", row.id, 0);
    }
    function integration() {
        return {
            change: root.workspaceState.change.code,
            edit_revision: root.workspaceState.change.edit_revision,
            integration: root.workspaceState.change.integration.code
        };
    }
    Component {
        id: catalogView
        FileWorkspaceCatalog {
            theme: root.theme
            controller: root.controller
        }
    }
    Component {
        id: graphView
        FileWorkspaceStreamGraph {
            theme: root.theme
            controller: root.controller
            onEditStream: (row, child) => streamEditor.openSpec(row, child)
        }
    }
    Component {
        id: streamsView
        FileWorkspaceStreams {
            theme: root.theme
            controller: root.controller
            onEditStream: (row, child) => streamEditor.openSpec(row, child)
        }
    }
    FileWorkspaceStreamEditor {
        id: streamEditor
        theme: root.theme
        controller: root.controller
    }
    function holders(row) {
        const stream = row.stream || root.workspaceState.change.stream || root.workspaceState.stream;
        const paths = root.workspaceState.locks[stream + "\0" + (row.source_path || row.path)] || [];
        return paths.map(h => h.owner + " · " + (h.mode === "exclusive" ? qsTr("Exclusive checkout") : qsTr("Ordinary checkout"))).join("; ") || qsTr("No active checkout");
    }
    function localStatus(value) {
        return Presentation.localStatus(value, language);
    }
    function serverStatus(value) {
        return Presentation.serverStatus(value, language);
    }
    function phase(value) {
        return Presentation.phase(value, language);
    }
    function command(name) {
        NativeCommands.command(root, name, {
            historyView: historyView,
            submitDialog: submitDialog,
            revisionDialog: revisionDialog,
            editor: editor,
            nonemptyDelete: nonemptyDelete,
            confirmation: confirmation,
            shelfDialog: shelfDialog,
            reviewDialog: reviewDialog,
            targetDialog: targetDialog,
            columnsDialog: columnsDialog,
            manifestSave: manifestSave,
            folderDialog: folderDialog,
            saveDialog: saveDialog,
            mergedDialog: mergedDialog,
            windowModel: typeof windowModel === "undefined" ? null : windowModel
        });
    }
    function entry(title, command, icon, enabled) {
        const invalid = Menus.selectionReason(root, command);
        enabled = enabled && !invalid;
        const reason = invalid || (enabled ? "" : busy ? qsTr("An operation is running") : !root.workspaceState.selected.length && kindForCommand(command) === "files" ? qsTr("Select files first") : !editable ? qsTr("Choose an owned pending changelist") : qsTr("Unavailable for this selection"));
        return {
            title: title,
            command: command,
            icon: icon,
            enabled: enabled,
            status: reason
        };
    }
    function kindForCommand(command) {
        return ["checkout_ordinary", "checkout_exclusive", "move_files", "remove_files", "revert_files", "rename_file", "mark_delete", "delete_local", "open_local", "reveal_local"].indexOf(command) >= 0 ? "files" : "";
    }
    function actions(kind) {
        return Menus.actions(root, kind);
    }
    function menu(kind, source) {
        actionMenu.actions = actions(kind);
        actionMenu.toggleBelowItem(source);
    }
    function saveEditor() {
        if (editKind === "goto_change")
            act("goto_change", {
                change: draft
            });
        else if (editKind === "rename_file")
            act("rename_file", {
                target: draft
            });
        else if (editKind === "local_root")
            set("root", draft);
        else if (editKind === "move_files") {
            set("target", draft);
            act("move_files");
        } else if (editKind === "offer_change")
            act(editKind, {
                recipient: draft
            });
        else {
            reviewDialog.operation = editKind;
            reviewDialog.paths = [];
            reviewDialog.request = editKind === "merge_begin" ? {
                source_stream: draft
            } : {
                shelf: draft
            };
            act("review_change", Object.assign({
                operation: editKind
            }, reviewDialog.request));
            reviewDialog.open();
        }
    }

    FileWorkspaceReviewDialog {
        id: reviewDialog
        theme: root.theme
        controller: root.controller
    }
    FileWorkspaceSubmitDialog {
        id: submitDialog
        theme: root.theme
        controller: root.controller
    }
    FileWorkspaceComparisonDialog {
        id: comparisonDialog
        theme: root.theme
        controller: root.controller
        onExternalRequested: comparisonApp.open()
    }
    FileDialog {
        id: comparisonApp
        title: qsTr("Choose comparison application")
        nameFilters: [qsTr("Applications (*.exe)"), qsTr("All files (*)")]
        onAccepted: root.act("external_compare", {
            application: selectedFile.toString()
        })
    }
    Connections {
        target: root.controller
        function onStateChanged() {
            const historyIdentity = root.workspaceState.history_stream + "/" + root.workspaceState.history_path;
            if (historyIdentity !== root.historyIdentity) {
                root.historyIdentity = historyIdentity;
                if (root.detailsView === "history")
                    root.detail = {};
            }
            if (root.activeTab.kind === "history")
                root.detail = root.workspaceState.history.find(row => row.code === root.workspaceState.focus_id) || root.workspaceState.history.find(row => row.code === root.detail.code) || root.workspaceState.history[0] || ({});
            if (root.detailsView === "conflicts") {
                const rows = root.showResolved ? root.workspaceState.resolved_conflicts : root.workspaceState.conflicts;
                root.detail = rows.find(row => row.path === root.detail.path) || rows[0] || ({});
            }
            const switching = root.workspaceState.switch_preview.token;
            if (switching && switching !== root.switchToken) {
                root.switchToken = switching;
                switchDialog.open();
            }
            const token = root.workspaceState.comparison.token;
            if (token && token !== root.comparisonToken) {
                root.comparisonToken = token;
                comparisonDialog.open();
            }
        }
    }
    FileWorkspaceShelfDialog {
        id: shelfDialog
        theme: root.theme
        controller: root.controller
        onChosen: values => {
            if (shelfDialog.operation === "diff_shelf") {
                root.act("compare", {
                    mode: "pending_shelf",
                    shelf: values.shelf
                });
                return;
            }
            reviewDialog.operation = shelfDialog.operation;
            reviewDialog.paths = shelfDialog.operation === "update_shelf" ? root.workspaceState.selected.slice() : [];
            reviewDialog.request = values;
            root.act("review_change", Object.assign({
                operation: shelfDialog.operation
            }, values, reviewDialog.paths.length ? {
                paths: reviewDialog.paths
            } : {}));
            reviewDialog.open();
        }
    }

    Component {
        id: changeBranch
        WorkspaceChangeBranch {
            workspace: root
        }
    }
    Component {
        id: changeFile
        WorkspaceChangeFile {
            workspace: root
        }
    }
    property alias dropBlocked: dialogs.dropBlockedWindow
    property alias dropConfirm: dialogs.dropConfirmWindow
    property alias nonemptyDelete: dialogs.nonemptyDeleteWindow
    property alias columnsDialog: dialogs.columnsDialogWindow
    property alias manifestSave: dialogs.manifestSaveWindow
    property alias targetDialog: dialogs.targetDialogWindow
    property alias revisionDialog: dialogs.revisionDialogWindow
    property alias actionMenu: dialogs.actionMenuWindow
    property alias folderDialog: dialogs.folderDialogWindow
    property alias saveDialog: dialogs.saveDialogWindow
    property alias mergedDialog: dialogs.mergedDialogWindow
    property alias revertDialog: dialogs.revertDialogWindow
    property alias confirmation: dialogs.confirmationWindow
    property alias editor: dialogs.editorWindow
    property alias tabDialog: dialogs.tabDialogWindow
    property alias switchDialog: dialogs.switchDialogWindow
    property alias setupDialog: dialogs.setupDialogWindow
    WorkspaceDialogs {
        id: dialogs
        workspace: root
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        SplitView {
            id: logSplit
            objectName: "fileWorkspaceLogSplit"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 8
            Layout.rightMargin: 8
            Layout.topMargin: 8
            orientation: Qt.Vertical
            handle: Controls.SplitterHandle {
                objectName: "fileWorkspaceLogSplitter"
                theme: root.theme
                vertical: false
            }
            onResizingChanged: if (!resizing && workspaceLog.visible)
                root.set("log_height", workspaceLog.height)
            SplitView {
                id: mainSplit
                objectName: "fileWorkspaceMainSplit"
                SplitView.fillHeight: true
                SplitView.minimumHeight: Math.min(240, logSplit.height * 0.65)
                orientation: root.narrow ? Qt.Vertical : Qt.Horizontal
                handle: Controls.SplitterHandle {
                    theme: root.theme
                    vertical: !root.narrow
                }
                onResizingChanged: if (!resizing && !root.narrow)
                    root.set("tree_width", tree.width)
                WorkspaceTreePane {
                    id: tree
                    workspace: root
                    visible: !root.narrow || root.treeOpen
                    SplitView.preferredWidth: root.workspaceState.tree_width
                    SplitView.minimumWidth: root.narrow ? 0 : 200
                    SplitView.maximumWidth: root.narrow ? root.width : root.width * .5
                    SplitView.preferredHeight: 240
                    SplitView.minimumHeight: 160
                }
                ColumnLayout {
                    objectName: "fileWorkspaceWorkingPane"
                    SplitView.fillWidth: true
                    SplitView.fillHeight: true
                    SplitView.minimumWidth: 0
                    spacing: 4
                    WorkspaceToolbar {
                        workspace: root
                        Layout.fillWidth: true
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: !root.workspaceState.active_tab
                        text: qsTr("Open a view from the View menu")
                        color: root.theme.secondaryText
                    }
                    SplitView {
                        id: rightSplit
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumWidth: 0
                        orientation: Qt.Vertical
                        handle: Controls.SplitterHandle {
                            theme: root.theme
                            vertical: false
                        }
                        onResizingChanged: if (!resizing)
                            root.set("details_height", root.activeTab.kind === "files" ? fileInspector.height : detailsPanel.height)
                        Rectangle {
                            visible: ["changes", "files"].indexOf(root.activeTab.kind) >= 0
                            SplitView.fillHeight: true
                            SplitView.minimumHeight: root.activeTab.kind === "files" ? Math.min(140, rightSplit.height * 0.55) : 180
                            color: root.theme.panelDeep
                            radius: root.theme.surfaceRadius
                            border.color: root.theme.outlineVariant
                            clip: true
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 4
                                WorkspaceFilters {
                                    workspace: root
                                    Layout.fillWidth: true
                                }
                                Item {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 28
                                    clip: true
                                    Frame.FrameView {
                                        x: root.activeTab.kind === "changes" ? 24 - changes.contentX : -files.contentX
                                        width: root.columnWidth
                                        height: 28
                                        theme: root.theme
                                        scene: Rows.fileHeader({
                                            columns: root.workspaceState.columns,
                                            sortColumn: root.workspaceState.sort_column,
                                            sortDesc: root.workspaceState.sort_desc
                                        }, width, root.language)
                                        onEvent: action => root.controller.sort_files(action.key)
                                    }
                                }
                                ListView {
                                    id: changes
                                    contentWidth: Math.max(width, root.columnWidth + (root.activeTab.kind === "changes" ? changeBar.reservedExtent : fileBar.reservedExtent))
                                    flickableDirection: Flickable.HorizontalAndVerticalFlick
                                    Keys.onPressed: event => root.fileKey(event, "changes")
                                    objectName: "workspaceChangelistTree"
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    visible: root.activeTab.kind === "changes"
                                    clip: true
                                    onContentYChanged: if (moving || changeBar.pressed)
                                        root.controller.remember_scroll("changes", contentY)
                                    onModelChanged: Qt.callLater(() => contentY = root.workspaceState.scroll.changes || 0)
                                    model: root.controller.change_model
                                    ScrollBar.vertical: Controls.ScrollBar {
                                        id: changeBar
                                        theme: root.theme
                                        flickableTarget: changes
                                    }
                                    TapHandler {
                                        parent: changes
                                        acceptedButtons: Qt.RightButton
                                        onTapped: point => {
                                            if (!changes.itemAt(point.position.x + changes.contentX, point.position.y + changes.contentY)) {
                                                actionMenu.actions = root.actions("changes_background");
                                                actionMenu.openAt(changes, point.position.x, point.position.y);
                                            }
                                        }
                                    }
                                    ScrollBar.horizontal: Controls.ScrollBar {
                                        theme: root.theme
                                        flickableTarget: changes
                                    }
                                    delegate: Loader {
                                        required property var node
                                        readonly property var modelData: node
                                        width: changes.contentWidth - changeBar.reservedExtent
                                        enabled: true
                                        sourceComponent: node.kind === "file" ? changeFile : changeBranch
                                        height: (item as Item)?.implicitHeight ?? 0
                                    }
                                    Label {
                                        anchors.centerIn: parent
                                        visible: changes.count === 0
                                        text: qsTr("No changelists on this page")
                                        color: root.theme.secondaryText
                                    }
                                }
                                ListView {
                                    id: files
                                    contentWidth: Math.max(width, root.columnWidth + (root.activeTab.kind === "changes" ? changeBar.reservedExtent : fileBar.reservedExtent))
                                    flickableDirection: Flickable.HorizontalAndVerticalFlick
                                    Keys.onPressed: event => root.fileKey(event, "files")
                                    visible: root.activeTab.kind === "files"
                                    objectName: "workspaceFiles"
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    onContentYChanged: if (moving || fileBar.pressed)
                                        root.controller.remember_scroll("files", contentY)
                                    onModelChanged: Qt.callLater(() => {
                                        contentY = root.workspaceState.scroll.files || 0;
                                        revealTreeSelection();
                                    })
                                    model: {
                                        const state = root.workspaceState;
                                        const name = state.name_filter;
                                        const status = state.status_filter;
                                        return state.rows.filter(row => Presentation.matches(row, name, status));
                                    }
                                    function revealTreeSelection() {
                                        if (!visible || root.activeTab.source !== "selection" || ["depot", "workspace"].indexOf(root.workspaceState.selection_scope) < 0)
                                            return;
                                        const index = model.findIndex(row => (row.stream || root.workspaceState.stream) === root.workspaceState.file_focus.stream && (row.source_path || row.path) === root.workspaceState.file_focus.path);
                                        if (index >= 0) {
                                            currentIndex = index;
                                            positionViewAtIndex(index, ListView.Contain);
                                        }
                                    }
                                    Connections {
                                        target: root.controller
                                        function onStateChanged() {
                                            Qt.callLater(files.revealTreeSelection);
                                        }
                                    }
                                    ScrollBar.vertical: Controls.ScrollBar {
                                        id: fileBar
                                        theme: root.theme
                                        flickableTarget: files
                                    }
                                    MouseArea {
                                        z: -1
                                        anchors.fill: parent
                                        acceptedButtons: Qt.RightButton
                                        onClicked: mouse => {
                                            actionMenu.actions = root.actions("files");
                                            actionMenu.openAt(parent, mouse.x, mouse.y);
                                        }
                                    }
                                    ScrollBar.horizontal: Controls.ScrollBar {
                                        theme: root.theme
                                        flickableTarget: files
                                    }
                                    delegate: FileWorkspaceFileRow {
                                        required property var modelData
                                        width: files.contentWidth - fileBar.reservedExtent
                                        theme: root.theme
                                        row: modelData
                                        narrow: root.narrow
                                        selected: root.workspaceState.selection_scope === "files" ? root.workspaceState.selection_ids.indexOf(root.controller.row_identity(modelData)) >= 0 : root.activeTab.source === "selection" && ["depot", "workspace"].indexOf(root.workspaceState.selection_scope) >= 0 && root.workspaceState.files_selection.some(item => root.controller.row_identity(item) === root.controller.row_identity(modelData))
                                        enabled: true
                                        objectName: "workspaceFile_" + modelData.path
                                        localLabel: root.localStatus(modelData.local_status)
                                        serverLabel: modelData.change_state === "submitted" ? qsTr("Submitted") : modelData.change_state === "shelved" ? qsTr("Shelved") : root.serverStatus(modelData.server_status || modelData.action)
                                        checkoutLabel: root.holders(modelData)
                                        currentUser: root.controller.current_user
                                        checkoutHolders: root.workspaceState.locks[(modelData.stream || root.workspaceState.change.stream || root.workspaceState.stream) + "\0" + (modelData.source_path || modelData.path)] || []
                                        columns: root.workspaceState.columns
                                        onSelectedByUser: modifiers => root.controller.select_row("files", root.controller.row_identity(modelData), modifiers)
                                        onDragRequested: dragData = root.controller.drag_payload("files", root.controller.row_identity(modelData))
                                        onSelectedChangedByUser: checked => root.controller.select_file(modelData.path, checked)
                                        onActivated: root.command("open_local")
                                        onMenuRequested: (source, x, y) => root.contextMenu("files", modelData, source, x, y)
                                    }
                                    Label {
                                        anchors.centerIn: parent
                                        visible: files.count === 0
                                        text: qsTr("No files on this page")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                    }
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 28
                                    Label {
                                        Layout.fillWidth: true
                                        Layout.minimumWidth: 0
                                        text: (root.workspaceState.view === "change" ? root.workspaceState.change_file_count : root.workspaceState.rows.length) + " " + qsTr("files")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        iconName: "chevron-right"
                                        toolTip: qsTr("Next changelists")
                                        Accessible.name: toolTip
                                        visible: root.activeTab.kind === "changes" && Boolean(root.workspaceState.changes_after)
                                        enabled: !root.busy
                                        onClicked: root.act("next_changes")
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        iconName: "chevron-left"
                                        toolTip: qsTr("Previous page")
                                        Accessible.name: toolTip
                                        visible: root.workspaceState.view !== "change"
                                        enabled: !root.busy && root.workspaceState.cursors.length > 0
                                        onClicked: root.act("previous_files")
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        iconName: "chevron-right"
                                        toolTip: qsTr("Next page")
                                        Accessible.name: toolTip
                                        visible: root.workspaceState.view !== "change"
                                        enabled: !root.busy && Boolean(root.workspaceState.after)
                                        onClicked: root.act("next_files")
                                    }
                                }
                            }
                        }
                        Loader {
                            active: root.activeTab.kind === "catalog" || root.activeTab.kind === "graph"
                            visible: active
                            SplitView.fillHeight: true
                            SplitView.minimumHeight: 120
                            sourceComponent: root.activeTab.kind === "graph" ? graphView : root.activeTab.source === "streams" ? streamsView : catalogView
                        }
                        FileWorkspaceInspector {
                            id: fileInspector
                            theme: root.theme
                            info: root.workspaceState.inspection || ({})
                            preview: root.workspaceState.inspection.preview || ({})
                            currentTab: root.workspaceState.inspector_tab
                            busy: root.workspaceState.inspection_busy
                            error: root.workspaceState.inspection_error
                            onTabSelected: tab => root.controller.set_value("inspector_tab", tab)
                            visible: root.activeTab.kind === "files"
                            SplitView.preferredHeight: Math.min(root.workspaceState.details_height, rightSplit.height * 0.4)
                            SplitView.minimumHeight: Math.min(100, rightSplit.height * 0.35)
                        }
                        FileWorkspaceHistory {
                            id: historyView
                            theme: root.theme
                            controller: root.controller
                            revision: root.detail
                            visible: root.activeTab.kind === "history"
                            SplitView.fillHeight: true
                            SplitView.minimumHeight: 120
                            onSelected: (row, modifiers, context) => {
                                root.detail = row;
                                root.controller.select_row("history", row.code, modifiers, context);
                            }
                            onContextRequested: (item, x, y) => {
                                actionMenu.actions = root.actions("details");
                                actionMenu.openAt(item, x, y);
                            }
                            onKeyPressed: event => root.fileKey(event, "history")
                        }
                        WorkspaceDetails {
                            id: detailsPanel
                            workspace: root
                            visible: ["conflicts", "tasks"].includes(root.activeTab.kind)
                            SplitView.fillHeight: true
                            SplitView.preferredHeight: root.workspaceState.details_height
                            SplitView.minimumHeight: 120
                            SplitView.maximumHeight: rightSplit.height
                        }
                    }
                }
            }
            FileWorkspaceLog {
                id: workspaceLog
                theme: root.theme
                controller: root.controller
                visible: root.workspaceState.log_visible
                SplitView.preferredHeight: Math.min(root.workspaceState.log_height, logSplit.height * 0.45)
                SplitView.minimumHeight: Math.min(80, logSplit.height * 0.2)
                SplitView.maximumHeight: logSplit.height * 0.6
            }
        }
        WorkspaceFooter {
            workspace: root
            Layout.fillWidth: true
        }
    }
}
