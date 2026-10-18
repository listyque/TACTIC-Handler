import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../../" as TH
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/scripts/editor.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property string token: ""
    readonly property bool canEdit: scriptEditorController.canEdit
    property bool applyingEditorState: false
    property bool editorReady: false
    property bool layoutReady: false
    property bool outputCollapsed: false
    property bool outputWrap: false
    property bool treeCollapsed: false
    property real scriptsPanelWidth: 200
    property string sidePanelMode: "scripts"
    property var codeSymbols: []
    property real editorFontSize: Controls.Typography.body
    readonly property real toolbarMinimumWidth: 480
    readonly property real sourceToolbarMinimumWidth: 460
    property real expandedOutputHeight: Math.max(80, scriptEditorController.outputHeight)
    onOutputCollapsedChanged: scheduleLayoutSave()
    onOutputWrapChanged: scheduleLayoutSave()
    onTreeCollapsedChanged: scheduleLayoutSave()
    onSidePanelModeChanged: scheduleLayoutSave()
    onEditorFontSizeChanged: scheduleLayoutSave()

    function languageValue() {
        return root.languageCode;
    }

    function selectRunMode(value) {
        if (!scriptEditorController.runModeOptions.some(row => row.value === value))
            return false;
        root.executionTarget = value;
        return true;
    }

    function applyEditor(record) {
        applyingEditorState = true;
        if (!record.token)
            token = "";
        else
            token = record.token;
        root.folderValue = record.folder || "";
        root.scriptName = record.title || "";
        sourcePane.editor.loadBuffer(record.tabId || "", record.source || "");
        root.languageCode = record.language || "local_python";
        applyLanguageRules();
        if (record.runMode === "dcc" || record.runMode === "standalone" || record.runMode === "server")
            selectRunMode(record.runMode);
        applyingEditorState = false;
        editorReady = true;
        outlineDelay.restart();
    }

    function resetEditor() {
        applyEditor(scriptEditorController.currentEditor);
    }

    function loadScript(value) {
        syncEditorState();
        scriptEditorController.script(value);
    }

    function activateTab(tabId) {
        syncEditorState();
        scriptEditorController.select_tab(tabId);
    }

    function applyLanguageRules() {
        const rules = scriptEditorController.handle_scripts_language_combo_box(languageValue());
        selectRunMode(rules.mode);
    }

    function runCurrent(wholeScript) {
        if (!canEdit)
            return;
        const runnable = scriptEditorController.languageOptions.some(row => row.value === root.languageCode && row.runnable !== false);
        if (!runnable)
            return;
        let value = sourcePane.editor.text;
        if (!wholeScript && sourcePane.editor.selectedText.length > 0)
            value = sourcePane.editor.selectedText;
        syncEditorState();
        scriptEditorController.request_run(root.executionTarget, languageValue(), value);
    }

    function syncEditorState() {
        if (!editorReady || applyingEditorState)
            return;
        scriptEditorController.update_editor_state(token, root.folderValue, root.scriptName, languageValue(), sourcePane.editor.text, root.executionTarget);
    }

    function saveCurrent() {
        if (!canEdit)
            return;
        syncEditorState();
        scriptEditorController.save_current_script(token, root.folderValue, root.scriptName, languageValue(), sourcePane.editor.text);
    }

    function saveLayout() {
        scriptEditorController.set_settings_from_dict({
            "treeWidth": scriptsPanelWidth,
            "outputHeight": outputCollapsed ? expandedOutputHeight : root.bounds.output.height,
            "treeCollapsed": treeCollapsed,
            "outputCollapsed": outputCollapsed,
            "outputWrap": outputWrap,
            "sidePanelMode": sidePanelMode,
            "editorFontSize": editorFontSize
        });
    }

    function scheduleLayoutSave() {
        if (layoutReady)
            layoutSave.restart();
    }

    function restoreLayout() {
        layoutReady = false;
        const values = scriptEditorController.get_settings_dict();
        scriptsPanelWidth = Math.max(160, Number(values.treeWidth || 200));
        treeCollapsed = Boolean(values.treeCollapsed);
        outputCollapsed = Boolean(values.outputCollapsed);
        outputWrap = Boolean(values.outputWrap);
        sidePanelMode = values.sidePanelMode === "outline" ? "outline" : "scripts";
        editorFontSize = Math.max(6, Math.min(32, Number(values.editorFontSize || 9.25)));
        expandedOutputHeight = Math.max(80, Number(values.outputHeight || 120));
        Qt.callLater(function () {
            root.layoutReady = true;
        });
    }

    function toggleOutput() {
        if (!outputCollapsed)
            expandedOutputHeight = Math.max(80, root.bounds.output.height);
        outputCollapsed = !outputCollapsed;
    }

    function closeTab(tabId) {
        syncEditorState();
        scriptEditorController.close_tab(tabId);
    }

    function setEditorFontSize(value) {
        editorFontSize = Number(value);
        sourcePane.editor.forceActiveFocus();
    }

    function showOutline() {
        treeCollapsed = false;
        sidePanelMode = "outline";
        outlineDelay.restart();
        Qt.callLater(function () {
            scriptOutline.focusFilter();
        });
    }

    function fontSizeActions() {
        const sizes = [8, 9.25, 11, 13, 15];
        const labels = [qsTr("Small"), qsTr("Normal"), qsTr("Medium"), qsTr("Large"), qsTr("Extra large")];
        const actions = [];
        for (let index = 0; index < sizes.length; ++index) {
            actions.push({
                "title": labels[index] + " — " + String(sizes[index]) + " pt",
                "translate": false,
                "command": "font:" + String(sizes[index]),
                "checked": Math.abs(editorFontSize - sizes[index]) < 0.01,
                "icon": "type"
            });
        }
        return actions;
    }

    onVisibleChanged: {
        if (visible) {
            restoreLayout();
            scriptEditorController.readSettings();
            scriptEditorController.load();
            root.resetEditor();
        } else {
            syncEditorState();
            saveLayout();
            scriptEditorController.writeSettings();
        }
    }
    Component.onCompleted: {
        restoreLayout();
        resetEditor();
    }
    Component.onDestruction: {
        syncEditorState();
        saveLayout();
        scriptEditorController.writeSettings();
    }

    Shortcut {
        sequence: "F5"
        enabled: root.canEdit
        onActivated: root.runCurrent(true)
    }

    Shortcut {
        sequences: [StandardKey.Save]
        enabled: root.canEdit
        onActivated: root.saveCurrent()
    }

    Connections {
        target: scriptEditorController
        function onExecutionTargetsChanged() {
            Qt.callLater(function () {
                root.selectRunMode(scriptEditorController.currentEditor.runMode || "standalone");
            });
        }
        function onOutputAppended(tabId) {
            if (tabId !== scriptEditorController.currentTabId)
                return;
            root.outputCollapsed = false;
        }
    }

    readonly property string uiLanguage: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property string folderValue: ""
    property string scriptName: ""
    property string languageCode: "local_python"
    property string executionTarget: "standalone"
    readonly property var presentation: ({
            native: true,
            canEdit: root.canEdit,
            editable: root.canEdit,
            busy: scriptEditorController.busy,
            running: false,
            folder: root.folderValue,
            title: root.scriptName,
            source: sourcePane.editor.text,
            language: root.languageCode,
            languages: scriptEditorController.languageOptions,
            targets: scriptEditorController.runModeOptions,
            target: root.executionTarget,
            treeHidden: root.treeCollapsed,
            treeWidth: root.scriptsPanelWidth,
            side: root.sidePanelMode,
            outputHidden: root.outputCollapsed,
            outputHeight: root.expandedOutputHeight,
            outputWrap: root.outputWrap,
            output: scriptEditorController.output,
            tabCount: scriptEditorTabModel.count(),
            notice: scriptEditorController.error
        })
    readonly property var bounds: UI.layout(presentation, width, height)
    function frameEvent(action) {
        if (action.type === "folder") {
            root.folderValue = action.value;
            root.syncEditorState();
        } else if (action.type === "title") {
            root.scriptName = action.value;
            root.syncEditorState();
        } else if (action.type === "language") {
            root.languageCode = action.value;
            root.applyLanguageRules();
            root.syncEditorState();
        } else if (action.type === "target") {
            root.executionTarget = action.value;
            root.syncEditorState();
        } else if (action.type === "create") {
            root.syncEditorState();
            scriptEditorController.create_new_script();
        } else if (action.type === "save")
            root.saveCurrent();
        else if (action.type === "run")
            root.runCurrent(true);
        else if (action.type === "triggers")
            scriptTriggerController.open_editor();
        else if (action.type === "refresh")
            scriptEditorController.refresh_scripts_tree();
        else if (action.type === "tree")
            root.treeCollapsed = !root.treeCollapsed;
        else if (action.type === "output")
            root.toggleOutput();
        else if (action.type === "wrap")
            root.outputWrap = !root.outputWrap;
        else if (action.type === "clear")
            scriptEditorController.cleanup_output();
        else if (action.type === "side")
            root.sidePanelMode = action.value;
        else if (action.type === "treeWidth") {
            root.scriptsPanelWidth = action.value;
            root.scheduleLayoutSave();
        } else if (action.type === "outputHeight") {
            root.expandedOutputHeight = action.value;
            root.scheduleLayoutSave();
        }
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }
    Item {
        x: root.bounds.main.x
        y: root.bounds.main.y
        width: root.bounds.main.width
        height: root.bounds.main.height
        Flickable {
            id: toolbarScroll
            objectName: "scriptEditorToolbar"
            x: root.bounds.toolbar.x
            y: root.bounds.toolbar.y
            width: root.bounds.toolbar.width
            height: 32 + (toolbarBar.visible ? toolbarBar.reservedExtent : 0)
            contentWidth: Math.max(480, width)
            contentHeight: 32
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Frame.FrameView {
                width: toolbarScroll.contentWidth
                height: 32
                theme: root.theme
                scene: UI.toolbar(root.presentation, width, root.uiLanguage)
                onEvent: action => root.frameEvent(action)
            }
            ScrollBar.horizontal: Controls.ScrollBar {
                id: toolbarBar
                objectName: "scriptEditorToolbarScrollBar"
                theme: root.theme
                flickableTarget: toolbarScroll
            }
        }
        RowLayout {
            x: root.bounds.tabs.x
            y: root.bounds.tabs.y
            width: root.bounds.tabs.width
            height: root.bounds.tabs.height
            spacing: 4
            ListView {
                id: editorTabs
                objectName: "scriptEditorTabs"
                Layout.fillWidth: true
                Layout.preferredHeight: 38
                Layout.minimumHeight: 38
                Layout.maximumHeight: 38
                orientation: ListView.Horizontal
                model: scriptEditorTabModel
                spacing: 4
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.horizontal: Controls.ScrollBar {
                    theme: root.theme
                    flickableTarget: editorTabs
                }
                delegate: Item {
                    id: scriptTab
                    required property int index
                    required property string tabId
                    required property string token
                    required property string title
                    required property bool dirty
                    required property bool current
                    onCurrentChanged: if (current)
                        Qt.callLater(function () {
                            editorTabs.positionViewAtIndex(scriptTab.index, ListView.Contain);
                        })
                    width: Math.min(190, Math.max(112, tabTitle.width + 58))
                    height: 36

                    Controls.WorkspaceTabVisual {
                        id: tabVisual
                        objectName: "scriptEditorTabVisual"
                        z: 2
                        anchors.fill: parent
                        theme: root.theme
                        title: scriptTab.title || "new_script"
                        current: scriptTab.current
                        closable: true
                        dirty: scriptTab.dirty
                        hovered: tabMouse.containsMouse
                        pressed: tabMouse.pressed
                        onCloseRequested: root.closeTab(scriptTab.tabId)
                    }

                    MouseArea {
                        id: tabMouse
                        z: 1
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onPressed: mouse => tabVisual.burst(mouse.x, mouse.y)
                        onClicked: mouse => {
                            if (mouse.button === Qt.MiddleButton) {
                                root.closeTab(scriptTab.tabId);
                                return;
                            }
                            root.activateTab(scriptTab.tabId);
                        }
                    }

                    TextMetrics {
                        id: tabTitle
                        font.family: root.theme.fontFamily
                        font.pixelSize: 14
                        text: scriptTab.title || "new_script"
                    }
                }
            }
            Controls.CompactIconButton {
                objectName: "scriptEditorCloseAllButton"
                Layout.preferredWidth: 30
                Layout.preferredHeight: 30
                theme: root.theme
                iconName: "close"
                toolTip: qsTr("Close all scripts")
                enabled: scriptEditorTabModel.count() > 0
                onClicked: {
                    root.syncEditorState();
                    scriptEditorController.request_close_all();
                }
            }
        }
        Rectangle {
            id: outputDock
            objectName: "scriptEditorOutputPanel"
            x: root.bounds.output.x
            y: root.bounds.output.y
            width: root.bounds.output.width
            height: root.bounds.output.height
            radius: 12
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant
            Frame.FrameView {
                width: parent.width
                height: 40
                theme: root.theme
                scene: UI.outputToolbar(root.presentation, width, root.uiLanguage)
                onEvent: action => root.frameEvent(action)
            }
            ScrollView {
                id: outputScroll
                objectName: "scriptEditorOutputScrollView"
                readonly property real stableContentWidth: Math.max(0, width - leftPadding - rightPadding)
                readonly property real stableContentHeight: Math.max(0, height - topPadding - bottomPadding)
                x: 4
                width: Math.max(0, parent.width - 8)
                y: 40
                height: Math.max(0, parent.height - 44)
                visible: !root.outputCollapsed
                rightPadding: 16
                bottomPadding: 16
                clip: true
                background: Rectangle {
                    color: root.theme.surfaceContainerHigh
                    radius: root.theme.surfaceRadius
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    objectName: "scriptEditorOutputVerticalScrollBar"
                    theme: root.theme
                    flickableTarget: outputScroll.contentItem
                }
                ScrollBar.horizontal: Controls.ScrollBar {
                    objectName: "scriptEditorOutputHorizontalScrollBar"
                    theme: root.theme
                    flickableTarget: outputScroll.contentItem
                }
                Controls.TextArea {
                    id: outputPane
                    objectName: "scriptEditorOutputText"
                    theme: root.theme
                    readOnly: true
                    activeFocusOnPress: true
                    persistentSelection: true
                    cursorVisible: activeFocus
                    text: scriptEditorController.output
                    font.family: "Consolas"
                    font.pointSize: root.editorFontSize
                    width: root.outputWrap ? outputScroll.stableContentWidth : Math.max(outputScroll.stableContentWidth, implicitWidth)
                    height: Math.max(outputScroll.stableContentHeight, implicitHeight)
                    wrapMode: root.outputWrap ? TextEdit.Wrap : TextEdit.NoWrap
                    background: Rectangle {
                        color: root.theme.surfaceContainerHigh
                        radius: root.theme.surfaceRadius
                    }
                    onTextChanged: Qt.callLater(function () {
                        outputPane.cursorPosition = outputPane.length;
                        const flickable = outputScroll.contentItem;
                        if (flickable) {
                            flickable.contentY = Math.max(0, flickable.contentHeight - flickable.height);
                        }
                    })
                }
            }
        }
        Frame.FrameView {
            x: root.bounds.outputSplitter.x
            y: root.bounds.outputSplitter.y
            width: root.bounds.outputSplitter.width
            height: root.bounds.outputSplitter.height
            theme: root.theme
            scene: root.outputCollapsed ? ({
                    nodes: []
                }) : UI.splitter(root.presentation, width, height, true, root.uiLanguage)
            onEvent: action => root.frameEvent(action)
        }
        ScriptSource {
            id: sourcePane
            x: root.bounds.source.x
            y: root.bounds.source.y
            width: root.bounds.source.width
            height: root.bounds.source.height
            theme: root.theme
            controller: scriptEditorController
            token: root.token
            language: root.uiLanguage
            readOnly: !root.canEdit
            busy: scriptEditorController.busy
            fontPointSize: root.editorFontSize
            symbols: root.codeSymbols
            onEdited: {
                outlineDelay.restart();
                if (!root.applyingEditorState)
                    root.syncEditorState();
            }
            onRunRequested: root.runCurrent(false)
            onOutlineRequested: root.showOutline()
            onHelpRequested: windowModel.open_help("script_editor")
            onSyncRequested: root.syncEditorState()
            onFontRequested: value => root.setEditorFontSize(value)
        }
        Frame.FrameView {
            x: root.bounds.footer.x
            y: root.bounds.footer.y
            width: root.bounds.footer.width
            height: root.bounds.footer.height
            theme: root.theme
            scene: UI.footer(root.presentation, width, root.uiLanguage)
            onEvent: action => root.frameEvent(action)
        }
        Label {
            x: root.bounds.notice.x
            y: root.bounds.notice.y
            width: root.bounds.notice.width
            height: root.bounds.notice.height
            text: scriptEditorController.error
            color: root.theme.error
            wrapMode: Text.WordWrap
        }
    }
    Frame.FrameView {
        x: root.bounds.treeSplitter.x
        y: root.bounds.treeSplitter.y
        width: root.bounds.treeSplitter.width
        height: root.bounds.treeSplitter.height
        visible: root.bounds.treeVisible
        theme: root.theme
        scene: UI.splitter(root.presentation, width, height, false, root.uiLanguage)
        onEvent: action => root.frameEvent(action)
    }
    Rectangle {
        objectName: "scriptEditorScriptsPanel"
        x: root.bounds.tree.x
        y: root.bounds.tree.y
        width: root.bounds.tree.width
        height: root.bounds.tree.height
        visible: root.bounds.treeVisible
        radius: 12
        color: root.theme.panel
        border.width: 1
        border.color: root.theme.outlineVariant
        Frame.FrameView {
            width: parent.width
            height: 36
            theme: root.theme
            scene: UI.sideTabs(root.presentation, width, root.uiLanguage)
            onEvent: action => root.frameEvent(action)
        }
        StackLayout {
            x: 4
            width: Math.max(0, parent.width - 8)
            y: 36
            height: Math.max(0, parent.height - 40)
            currentIndex: root.sidePanelMode === "outline" ? 1 : 0

            TH.ScriptTree {
                objectName: "scriptEditorTree"
                theme: root.theme
                controller: scriptEditorController
                treeModel: scriptEditorModel
                selectedToken: root.token
                onScriptRequested: token => root.loadScript(token)
                onMenuRequested: (token, anchor, x, y) => {
                    scriptMenu.token = token;
                    scriptMenu.actions = scriptEditorController.open_menu(token);
                    scriptMenu.openAt(anchor, x, y);
                }
            }

            TH.ScriptOutline {
                id: scriptOutline
                objectName: "scriptEditorOutline"
                theme: root.theme
                symbols: root.codeSymbols
                onNavigateRequested: line => sourcePane.editor.goToLine(line)
            }
        }
    }
    Timer {
        id: layoutSave
        interval: 300
        repeat: false
        onTriggered: root.saveLayout()
    }

    TH.ActionMenu {
        id: scriptMenu
        theme: root.theme
        property string token: ""
        onTriggered: command => {
            if (command === "copy_runner")
                scriptEditorController.create_execution_script(token);
            else if (command === "delete")
                scriptEditorController.request_delete_script(token);
        }
    }

    Timer {
        id: outlineDelay
        interval: 160
        repeat: false
        onTriggered: root.codeSymbols = scriptEditorController.code_symbols(sourcePane.editor.text)
    }

    Controls.Dialog {
        id: deleteConfirmation
        theme: root.theme
        anchors.centerIn: parent
        width: 390
        title: qsTr("Delete script?")
        modal: false
        dim: false
        onAccepted: scriptEditorController.confirm_delete_script()
        onRejected: scriptEditorController.cancel_delete_script()
        property string scriptTitle: ""
        contentItem: Label {
            width: 342
            text: qsTr("Delete ") + deleteConfirmation.scriptTitle + " from the TACTIC server?"
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Delete")
                icon.name: "delete"
                highlighted: true
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
        id: closeAllConfirmation
        theme: root.theme
        anchors.centerIn: parent
        width: 420
        title: qsTr("Unsaved scripts")
        modal: false
        dim: false
        property int dirtyCount: 0
        contentItem: Label {
            width: 372
            text: closeAllConfirmation.dirtyCount === 1 ? qsTr("Save the unsaved script before closing all tabs?") : qsTr("Save ") + closeAllConfirmation.dirtyCount + qsTr(" unsaved scripts before closing all tabs?")
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Save all")
                visible: root.canEdit
                icon.name: "save"
                highlighted: true
                onClicked: {
                    if (scriptEditorController.confirm_close_all_save())
                        closeAllConfirmation.close();
                }
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Discard all")
                icon.name: "delete_sweep"
                onClicked: {
                    scriptEditorController.confirm_close_all_discard();
                    closeAllConfirmation.close();
                }
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                onClicked: closeAllConfirmation.close()
            }
        }
    }

    Connections {
        target: scriptEditorController
        function onEditorChanged(record) {
            root.applyEditor(record);
        }
        function onDeleteConfirmationRequested(token, title) {
            deleteConfirmation.scriptTitle = title;
            deleteConfirmation.open();
        }
        function onNewScriptRequested() {
            root.resetEditor();
        }
        function onCloseAllConfirmationRequested(count) {
            closeAllConfirmation.dirtyCount = count;
            closeAllConfirmation.open();
        }
    }
}
