import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    required property var theme
    property string token: ""
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
        return language.currentIndex >= 0 ? language.currentValue : "local_python"
    }

    function selectRunMode(value) {
        for (let i = 0; i < runMode.model.length; ++i) {
            if (runMode.model[i].value === value) {
                runMode.currentIndex = i
                return true
            }
        }
        return false
    }

    function applyEditor(record) {
        applyingEditorState = true
        if (!record.token)
            token = ""
        else
            token = record.token
        folder.text = record.folder || ""
        scriptTitle.text = record.title || ""
        source.loadBuffer(record.tabId || "", record.source || "")
        for (let i = 0; i < language.model.length; ++i) {
            if (language.model[i].value === record.language) {
                language.currentIndex = i
                break
            }
        }
        applyLanguageRules()
        if (record.runMode === "dcc"
                || record.runMode === "standalone"
                || record.runMode === "server")
            selectRunMode(record.runMode)
        applyingEditorState = false
        editorReady = true
        outlineDelay.restart()
    }

    function resetEditor() {
        applyEditor(scriptEditorController.currentEditor)
    }

    function loadScript(value) {
        syncEditorState()
        scriptEditorController.script(value)
    }

    function activateTab(tabId) {
        syncEditorState()
        scriptEditorController.select_tab(tabId)
    }

    function applyLanguageRules() {
        const rules = scriptEditorController.handle_scripts_language_combo_box(
            languageValue())
        selectRunMode(rules.mode)
    }

    function runCurrent(wholeScript) {
        const runnable = language.currentIndex >= 0
            && language.model[language.currentIndex].runnable !== false
        if (!runnable)
            return
        let value = source.text
        if (!wholeScript && source.selectedText.length > 0)
            value = source.selectedText
        syncEditorState()
        scriptEditorController.request_run(
            runMode.currentValue, languageValue(), value)
    }

    function syncEditorState() {
        if (!editorReady || applyingEditorState)
            return
        scriptEditorController.update_editor_state(
            token, folder.text, scriptTitle.text,
            languageValue(), source.text, runMode.currentValue)
    }

    function saveCurrent() {
        syncEditorState()
        scriptEditorController.save_current_script(
            token, folder.text, scriptTitle.text,
            languageValue(), source.text)
    }

    function saveLayout() {
        scriptEditorController.set_settings_from_dict({
            "treeWidth": scriptsPanelWidth,
            "outputHeight": outputCollapsed
                ? expandedOutputHeight : outputDock.height,
            "treeCollapsed": treeCollapsed,
            "outputCollapsed": outputCollapsed,
            "outputWrap": outputWrap,
            "sidePanelMode": sidePanelMode,
            "editorFontSize": editorFontSize
        })
    }

    function scheduleLayoutSave() {
        if (layoutReady)
            layoutSave.restart()
    }

    function restoreLayout() {
        layoutReady = false
        const values = scriptEditorController.get_settings_dict()
        scriptsPanelWidth = Math.max(160, Number(values.treeWidth || 200))
        treeCollapsed = Boolean(values.treeCollapsed)
        outputCollapsed = Boolean(values.outputCollapsed)
        outputWrap = Boolean(values.outputWrap)
        sidePanelMode = values.sidePanelMode === "outline"
            ? "outline" : "scripts"
        editorFontSize = Math.max(
            6, Math.min(32, Number(values.editorFontSize || 9.25)))
        expandedOutputHeight = Math.max(
            80, Number(values.outputHeight || 120))
        Qt.callLater(function() { root.layoutReady = true })
    }

    function toggleOutput() {
        if (!outputCollapsed)
            expandedOutputHeight = Math.max(80, outputDock.height)
        outputCollapsed = !outputCollapsed
    }

    function closeTab(tabId) {
        syncEditorState()
        scriptEditorController.close_tab(tabId)
    }

    function setEditorFontSize(value) {
        editorFontSize = Number(value)
        source.forceActiveFocus()
    }

    function showOutline() {
        treeCollapsed = false
        sidePanelMode = "outline"
        outlineDelay.restart()
        Qt.callLater(function() { scriptOutline.focusFilter() })
    }

    function fontSizeActions() {
        const sizes = [8, 9.25, 11, 13, 15]
        const labels = [
            qsTr("Small"), qsTr("Normal"), qsTr("Medium"),
            qsTr("Large"), qsTr("Extra large")
        ]
        const actions = []
        for (let index = 0; index < sizes.length; ++index) {
            actions.push({
                "title": labels[index] + " — " + String(sizes[index]) + " pt",
                "translate": false,
                "command": "font:" + String(sizes[index]),
                "checked": Math.abs(editorFontSize - sizes[index]) < 0.01,
                "icon": "type"
            })
        }
        return actions
    }

    onVisibleChanged: {
        if (visible) {
            restoreLayout()
            scriptEditorController.readSettings()
            scriptEditorController.load()
            root.resetEditor()
        } else {
            syncEditorState()
            saveLayout()
            scriptEditorController.writeSettings()
        }
    }
    Component.onCompleted: {
        restoreLayout()
        resetEditor()
    }
    Component.onDestruction: {
        syncEditorState()
        saveLayout()
        scriptEditorController.writeSettings()
    }

    Shortcut {
        sequence: "F5"
        onActivated: root.runCurrent(true)
    }

    Shortcut {
        sequences: [StandardKey.Save]
        onActivated: root.saveCurrent()
    }

    Connections {
        target: scriptEditorController
        function onExecutionTargetsChanged() {
            Qt.callLater(function() {
                root.selectRunMode(
                    scriptEditorController.currentEditor.runMode || "standalone")
            })
        }
        function onOutputAppended(tabId) {
            if (tabId !== scriptEditorController.currentTabId)
                return
            root.outputCollapsed = false
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    SplitView {
        id: mainSplit
        anchors.fill: parent
        anchors.margins: 8
        orientation: Qt.Horizontal
        handle: Rectangle {
            implicitWidth: 6
            color: "transparent"
            Rectangle {
                anchors.centerIn: parent
                width: 1
                height: Math.max(0, parent.height - 18)
                color: root.theme.outlineVariant
            }
        }

        Item {
            SplitView.fillWidth: true
            SplitView.minimumWidth: 360

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 0
                spacing: 4

                Flickable {
                    id: toolbarScroll
                    objectName: "scriptEditorToolbar"
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Layout.maximumWidth: parent.width
                    Layout.preferredHeight: 32
                        + (toolbarScrollBar.visible
                            ? toolbarScrollBar.reservedExtent : 0)
                    contentWidth: toolbarRow.width
                    contentHeight: toolbarRow.height
                    flickableDirection: Flickable.HorizontalFlick
                    boundsBehavior: Flickable.StopAtBounds
                    clip: true

                    RowLayout {
                        id: toolbarRow
                        width: Math.max(
                            toolbarScroll.width, root.toolbarMinimumWidth)
                        height: 32
                        spacing: 4
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "add"
                            toolTip: qsTr("New script")
                            onClicked: {
                                root.syncEditorState()
                                scriptEditorController.create_new_script()
                            }
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "save"
                            toolTip: qsTr("Save current script to server")
                            enabled: !scriptEditorController.busy
                            onClicked: root.saveCurrent()
                        }
                        Rectangle {
                            Layout.preferredWidth: 1
                            Layout.preferredHeight: 20
                            color: root.theme.outlineVariant
                        }
                        Controls.TextField {
                            id: folder
                            theme: root.theme
                            Layout.fillWidth: true
                            Layout.minimumWidth: 72
                            Layout.preferredHeight: 30
                            placeholderText: qsTr("Folder")
                            onTextChanged: if (!root.applyingEditorState)
                                root.syncEditorState()
                        }
                        Label {
                            text: qsTr("/")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                        }
                        Controls.TextField {
                            id: scriptTitle
                            theme: root.theme
                            Layout.fillWidth: true
                            Layout.minimumWidth: 88
                            Layout.preferredHeight: 30
                            placeholderText: qsTr("Title")
                            onTextChanged: if (!root.applyingEditorState)
                                root.syncEditorState()
                        }
                        Controls.ComboBox {
                            id: language
                            theme: root.theme
                            Layout.preferredWidth: 132
                            Layout.preferredHeight: 30
                            model: scriptEditorController.languageOptions
                            textRole: "label"
                            valueRole: "value"
                            onActivated: {
                                root.applyLanguageRules()
                                root.syncEditorState()
                            }
                        }
                        Controls.CompactIconButton {
                            objectName: "scriptTriggerEditorButton"
                            theme: root.theme
                            iconName: "bolt"
                            iconColor: root.theme.action
                            toolTip: qsTr("Script triggers")
                            onClicked: scriptTriggerController.open_editor()
                        }
                        RefreshIconButton {
                            theme: root.theme
                            toolTip: qsTr("Refresh scripts from server")
                            enabled: !scriptEditorController.busy
                            onClicked: scriptEditorController.refresh_scripts_tree()
                        }
                        Controls.CompactIconButton {
                            objectName: "scriptEditorTreeToggleButton"
                            theme: root.theme
                            iconName: root.treeCollapsed
                                ? "chevron-left" : "chevron-right"
                            iconColor: root.treeCollapsed
                                ? root.theme.primaryText : root.theme.action
                            backgroundColor: root.treeCollapsed
                                ? "transparent" : root.theme.secondaryContainer
                            toolTip: root.treeCollapsed
                                ? qsTr("Show scripts and outline")
                                : qsTr("Hide scripts and outline")
                            onClicked: root.treeCollapsed = !root.treeCollapsed
                        }
                    }

                    ScrollBar.horizontal: Controls.ScrollBar {
                        id: toolbarScrollBar
                        objectName: "scriptEditorToolbarScrollBar"
                        theme: root.theme
                        flickableTarget: toolbarScroll
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    Layout.minimumHeight: 38
                    Layout.maximumHeight: 38
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
                        onCurrentChanged: if (current) Qt.callLater(function() {
                            editorTabs.positionViewAtIndex(
                                scriptTab.index, ListView.Contain)
                        })
                        width: Math.min(190, Math.max(
                            112, tabTitle.width + 58))
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
                                    root.closeTab(scriptTab.tabId)
                                    return
                                }
                                root.activateTab(scriptTab.tabId)
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
                            root.syncEditorState()
                            scriptEditorController.request_close_all()
                        }
                    }
                }

                SplitView {
                    id: editorSplit
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Layout.maximumWidth: parent.width
                    Layout.fillHeight: true
                    orientation: Qt.Vertical
                    handle: Item {
                        implicitHeight: 6
                    }

                    Rectangle {
                        id: outputDock
                        objectName: "scriptEditorOutputPanel"
                        SplitView.preferredHeight: root.outputCollapsed
                            ? 40 : root.expandedOutputHeight
                        SplitView.minimumHeight: 40
                        radius: 12
                        color: root.theme.panel
                        border.width: 1
                        border.color: root.theme.outlineVariant
                        onHeightChanged: {
                            if (root.layoutReady
                                    && !root.outputCollapsed && height >= 80)
                                root.expandedOutputHeight = height
                            root.scheduleLayoutSave()
                        }
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 2
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 28
                                Layout.minimumHeight: 28
                                Layout.maximumHeight: 28
                                Layout.alignment: Qt.AlignTop
                                Layout.leftMargin: 4
                                Layout.rightMargin: 2
                                spacing: 6
                                Controls.MaterialIcon { name: "terminal"; size: 16; color: root.theme.action }
                                Label {
                                    objectName: "scriptEditorOutputTitle"
                                    Layout.fillWidth: true
                                    text: qsTr("Output")
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    font.weight: Font.DemiBold
                                }
                                Controls.CompactIconButton {
                                    objectName: "scriptEditorOutputWrapButton"
                                    Layout.preferredWidth: 26
                                    Layout.preferredHeight: 26
                                    theme: root.theme
                                    round: true
                                    iconName: "wrap-lines"
                                    iconColor: root.outputWrap
                                        ? root.theme.action : root.theme.primaryText
                                    backgroundColor: root.outputWrap
                                        ? root.theme.secondaryContainer : "transparent"
                                    toolTip: root.outputWrap
                                        ? qsTr("Disable output word wrap")
                                        : qsTr("Enable output word wrap")
                                    onClicked: root.outputWrap = !root.outputWrap
                                }
                                Controls.CompactIconButton {
                                    Layout.preferredWidth: 26
                                    Layout.preferredHeight: 26
                                    theme: root.theme
                                    round: true
                                    iconName: "delete-sweep"
                                    iconSize: 14
                                    toolTip: qsTr("Clear output")
                                    enabled: scriptEditorController.output.length > 0
                                    onClicked: scriptEditorController.cleanup_output()
                                }
                                Controls.CompactIconButton {
                                    Layout.preferredWidth: 26
                                    Layout.preferredHeight: 26
                                    theme: root.theme
                                    round: true
                                    iconName: root.outputCollapsed
                                        ? "expand-more" : "expand-less"
                                    iconSize: 14
                                    toolTip: root.outputCollapsed
                                        ? qsTr("Expand output")
                                        : qsTr("Collapse output")
                                    onClicked: root.toggleOutput()
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                visible: !root.outputCollapsed
                                color: root.theme.outlineVariant
                            }
                            ScrollView {
                                id: outputScroll
                                objectName: "scriptEditorOutputScrollView"
                                readonly property real stableContentWidth:
                                    Math.max(0, width - leftPadding - rightPadding)
                                readonly property real stableContentHeight:
                                    Math.max(0, height - topPadding - bottomPadding)
                                Layout.fillWidth: true
                                Layout.fillHeight: true
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
                                    width: root.outputWrap
                                        ? outputScroll.stableContentWidth
                                        : Math.max(
                                            outputScroll.stableContentWidth,
                                            implicitWidth)
                                    height: Math.max(
                                        outputScroll.stableContentHeight,
                                        implicitHeight)
                                    wrapMode: root.outputWrap
                                        ? TextEdit.Wrap : TextEdit.NoWrap
                                    background: Rectangle {
                                        color: root.theme.surfaceContainerHigh
                                        radius: root.theme.surfaceRadius
                                    }
                                    onTextChanged: Qt.callLater(function() {
                                        outputPane.cursorPosition = outputPane.length
                                        const flickable = outputScroll.contentItem
                                        if (flickable) {
                                            flickable.contentY = Math.max(
                                                0,
                                                flickable.contentHeight - flickable.height
                                            )
                                        }
                                    })
                                }
                            }
                        }
                    }

                    Rectangle {
                        objectName: "scriptEditorSourcePanel"
                        SplitView.fillHeight: true
                        SplitView.minimumHeight: 116
                        radius: 12
                        color: root.theme.panel
                        border.width: 1
                        border.color: source.editorActiveFocus
                            ? root.theme.action : root.theme.outlineVariant
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 2
                            Flickable {
                                id: sourceToolbarScroll
                                objectName: "scriptEditorSourceToolbar"
                                Layout.fillWidth: true
                                Layout.minimumWidth: 0
                                Layout.preferredHeight: 28
                                    + (sourceToolbarScrollBar.visible
                                        ? sourceToolbarScrollBar.reservedExtent : 0)
                                contentWidth: sourceToolbarRow.width
                                contentHeight: sourceToolbarRow.height
                                flickableDirection: Flickable.HorizontalFlick
                                boundsBehavior: Flickable.StopAtBounds
                                clip: true

                                RowLayout {
                                    id: sourceToolbarRow
                                    width: Math.max(
                                        sourceToolbarScroll.width,
                                        root.sourceToolbarMinimumWidth)
                                    height: 28
                                    spacing: 6
                                    Controls.MaterialIcon {
                                        name: "edit_note"
                                        size: 16
                                        color: root.theme.action
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: qsTr("Source")
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.body
                                        font.weight: Font.DemiBold
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        objectName: "scriptEditorUndoButton"
                                        iconName: "undo"
                                        enabled: source.canUndo
                                        toolTip: qsTr("Undo (Ctrl+Z)")
                                        onClicked: source.undoEdit()
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        objectName: "scriptEditorRedoButton"
                                        iconName: "redo"
                                        enabled: source.canRedo
                                        toolTip: qsTr("Redo (Ctrl+Y)")
                                        onClicked: source.redoEdit()
                                    }
                                    Controls.CompactIconButton {
                                        id: historyButton
                                        objectName: "scriptEditorHistoryButton"
                                        theme: root.theme
                                        iconName: "history"
                                        toolTip: qsTr("Edit history")
                                        onClicked: {
                                            historyMenu.actions = source.historyActions()
                                            historyMenu.toggleBelow(historyButton)
                                        }
                                    }
                                    ScriptSavedHistoryButton {
                                        theme: root.theme
                                        controller: scriptEditorController
                                        sourceEditor: source
                                        scriptToken: root.token
                                        onSyncRequested: root.syncEditorState()
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        iconName: "content-cut"
                                        enabled: source.canCut
                                        toolTip: qsTr("Cut (Ctrl+X)")
                                        onClicked: source.cutSelection()
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        iconName: "content-copy"
                                        enabled: source.canCopy
                                        toolTip: qsTr("Copy (Ctrl+C)")
                                        onClicked: source.copySelection()
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        iconName: "content-paste"
                                        enabled: source.canPaste
                                        toolTip: qsTr("Paste (Ctrl+V)")
                                        onClicked: source.pasteClipboard()
                                    }
                                    Controls.CompactIconButton {
                                        id: fontSizeButton
                                        theme: root.theme
                                        iconName: "type"
                                        toolTip: qsTr("Editor text size")
                                        onClicked: {
                                            fontSizeMenu.actions = root.fontSizeActions()
                                            fontSizeMenu.toggleBelow(fontSizeButton)
                                        }
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        objectName: "scriptEditorFindButton"
                                        duplicateWindow: 0
                                        iconName: "search"
                                        toolTip: qsTr(
                                            "Find and replace (Ctrl+F / Ctrl+H)")
                                        onClicked: source.showFind(false)
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        iconName: "play-selection"
                                        enabled: source.selectedText.length > 0
                                            && !scriptEditorController.busy
                                        toolTip: qsTr(
                                            "Run selected text (Ctrl+Enter)")
                                        onClicked: root.runCurrent(false)
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        iconName: "help"
                                        toolTip: qsTr("Editor help")
                                        onClicked: windowModel.open_help(
                                            "script_editor")
                                    }
                                }

                                ScrollBar.horizontal: Controls.ScrollBar {
                                    id: sourceToolbarScrollBar
                                    objectName: "scriptEditorSourceToolbarScrollBar"
                                    theme: root.theme
                                    flickableTarget: sourceToolbarScroll
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: root.theme.outlineVariant
                            }
                            Controls.ScriptCodeEditor {
                                id: source
                                objectName: "scriptEditorCodeEditor"
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                theme: root.theme
                                controller: scriptEditorController
                                fontPointSize: root.editorFontSize
                                symbols: root.codeSymbols
                                onTextEdited: {
                                    outlineDelay.restart()
                                    if (!root.applyingEditorState)
                                        root.syncEditorState()
                                }
                                onRunRequested: root.runCurrent(false)
                                onOutlineRequested: root.showOutline()
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: root.theme.controlHeight
                    spacing: 5
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Run Script")
                        icon.name: "play_arrow"
                        highlighted: true
                        enabled: !scriptEditorController.busy
                            && language.currentIndex >= 0
                            && language.model[language.currentIndex].runnable !== false
                        onClicked: root.runCurrent(true)
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: qsTr("Run in")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                    Controls.ComboBox {
                        id: runMode
                        objectName: "scriptEditorExecutionTarget"
                        theme: root.theme
                        Layout.minimumWidth: 130
                        Layout.preferredWidth: 220
                        model: scriptEditorController.runModeOptions
                        textRole: "label"
                        valueRole: "value"
                        iconRole: "icon"
                        onActivated: root.syncEditorState()
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: scriptEditorController.error
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    elide: Text.ElideRight
                }
            }
        }

        Rectangle {
            id: scriptsPanel
            objectName: "scriptEditorScriptsPanel"
            visible: !root.treeCollapsed
            SplitView.preferredWidth: root.scriptsPanelWidth
            SplitView.minimumWidth: 160
            SplitView.maximumWidth: Math.max(240, mainSplit.width * 0.50)
            radius: 12
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant
            onWidthChanged: if (root.layoutReady) { root.scriptsPanelWidth = width; root.scheduleLayoutSave() }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 4
                spacing: 2
                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 28
                    Layout.leftMargin: 4
                    Layout.rightMargin: 2
                    spacing: 6
                    Controls.TabButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 27
                        theme: root.theme
                        text: qsTr("Scripts")
                        checked: root.sidePanelMode === "scripts"
                        onClicked: root.sidePanelMode = "scripts"
                    }
                    Controls.TabButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 27
                        theme: root.theme
                        text: qsTr("Outline")
                        checked: root.sidePanelMode === "outline"
                        onClicked: root.sidePanelMode = "outline"
                    }
                    Controls.BusyIndicator {
                        uiTheme: root.theme
                        Layout.preferredWidth: 18
                        Layout.preferredHeight: 18
                        visible: scriptEditorController.busy
                        running: visible
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.theme.outlineVariant
                }
                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: root.sidePanelMode === "outline" ? 1 : 0

                    ScriptTree {
                        objectName: "scriptEditorTree"
                        theme: root.theme
                        controller: scriptEditorController
                        treeModel: scriptEditorModel
                        selectedToken: root.token
                        onScriptRequested: token => root.loadScript(token)
                        onMenuRequested: (token, anchor, x, y) => {
                            scriptMenu.token = token
                            scriptMenu.actions =
                                scriptEditorController.open_menu(token)
                            scriptMenu.openAt(anchor, x, y)
                        }
                    }

                    ScriptOutline {
                        id: scriptOutline
                        objectName: "scriptEditorOutline"
                        theme: root.theme
                        symbols: root.codeSymbols
                        onNavigateRequested: line => source.goToLine(line)
                    }
                }
            }
        }
    }

    Timer {
        id: layoutSave
        interval: 300
        repeat: false
        onTriggered: root.saveLayout()
    }

    ActionMenu {
        id: scriptMenu
        theme: root.theme
        property string token: ""
        onTriggered: command => {
            if (command === "copy_runner")
                scriptEditorController.create_execution_script(token)
            else if (command === "delete")
                scriptEditorController.request_delete_script(token)
        }
    }

    Timer {
        id: outlineDelay
        interval: 160
        repeat: false
        onTriggered: root.codeSymbols =
            scriptEditorController.code_symbols(source.text)
    }

    ActionMenu {
        id: historyMenu
        theme: root.theme
        preferredWidth: 230
        onTriggered: command => source.goToHistory(command)
    }

    ActionMenu {
        id: fontSizeMenu
        theme: root.theme
        preferredWidth: 210
        onTriggered: command => {
            const value = String(command)
            if (value.indexOf("font:") === 0)
                root.setEditorFontSize(Number(value.slice(5)))
        }
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
            text: qsTr("Delete ") + deleteConfirmation.scriptTitle
                + " from the TACTIC server?"
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
            text: closeAllConfirmation.dirtyCount === 1
                ? qsTr("Save the unsaved script before closing all tabs?")
                : qsTr("Save ") + closeAllConfirmation.dirtyCount
                    + qsTr(" unsaved scripts before closing all tabs?")
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Save all")
                icon.name: "save"
                highlighted: true
                onClicked: {
                    if (scriptEditorController.confirm_close_all_save())
                        closeAllConfirmation.close()
                }
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Discard all")
                icon.name: "delete_sweep"
                onClicked: {
                    scriptEditorController.confirm_close_all_discard()
                    closeAllConfirmation.close()
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
            root.applyEditor(record)
        }
        function onDeleteConfirmationRequested(token, title) {
            deleteConfirmation.scriptTitle = title
            deleteConfirmation.open()
        }
        function onNewScriptRequested() {
            root.resetEditor()
        }
        function onCloseAllConfirmationRequested(count) {
            closeAllConfirmation.dirtyCount = count
            closeAllConfirmation.open()
        }
    }
}
