import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls"

Item {
    id: root
    required property var theme
    property string token: ""
    property bool applyingEditorState: false

    function languageValue() {
        return language.currentIndex >= 0 ? language.currentValue : "local_python"
    }

    function applyEditor(record) {
        applyingEditorState = true
        if (!record.token)
            token = ""
        else
            token = record.token
        folder.text = record.folder || ""
        scriptTitle.text = record.title || ""
        source.text = record.source || ""
        for (let i = 0; i < language.model.length; ++i) {
            if (language.model[i].value === record.language) {
                language.currentIndex = i
                break
            }
        }
        applyLanguageRules()
        if (record.runMode === "local" || record.runMode === "server")
            runMode.currentIndex = record.runMode === "local" ? 0 : 1
        applyingEditorState = false
    }

    function resetEditor() {
        applyEditor(scriptEditorController.currentEditor)
    }

    function loadScript(value) {
        const record = scriptEditorController.script(value)
        if (record.tabId)
            applyEditor(record)
    }

    function activateTab(tabId) {
        const record = scriptEditorController.select_tab(tabId)
        if (record.tabId)
            applyEditor(record)
    }

    function applyLanguageRules() {
        const rules = scriptEditorController.handle_scripts_language_combo_box(
            languageValue())
        runMode.currentIndex = rules.mode === "local" ? 0 : 1
    }

    function runCurrent() {
        const runnable = language.currentIndex >= 0
            && language.model[language.currentIndex].runnable !== false
        if (!runnable)
            return
        let value = source.text
        if (runMode.currentValue === "local" && source.selectedText.length > 0)
            value = source.selectedText
        syncEditorState()
        scriptEditorController.request_run(
            runMode.currentValue, languageValue(), value)
    }

    function syncEditorState() {
        if (applyingEditorState)
            return
        scriptEditorController.update_editor_state(
            token, folder.text, scriptTitle.text,
            languageValue(), source.text, runMode.currentValue)
    }

    function saveLayout() {
        scriptEditorController.set_layout(scriptsPanel.width, outputDock.height)
    }

    onVisibleChanged: {
        if (visible) {
            scriptEditorController.readSettings()
            scriptEditorController.load()
            root.resetEditor()
        } else {
            saveLayout()
            scriptEditorController.writeSettings()
        }
    }
    Component.onDestruction: saveLayout()

    Timer {
        id: draftSave
        interval: 250
        repeat: false
        onTriggered: root.syncEditorState()
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    SplitView {
        id: mainSplit
        anchors.fill: parent
        anchors.margins: 12
        orientation: Qt.Horizontal
        handle: Rectangle {
            implicitWidth: 10
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
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    CompactIconButton {
                        theme: root.theme
                        iconName: "add"
                        toolTip: qsTr("New script")
                        onClicked: scriptEditorController.create_new_script()
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "close"
                        toolTip: qsTr("Close all scripts")
                        enabled: scriptEditorTabModel.count() > 0
                        onClicked: {
                            root.syncEditorState()
                            scriptEditorController.request_close_all()
                        }
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "save"
                        toolTip: qsTr("Save current script to server")
                        enabled: !scriptEditorController.busy
                        onClicked: {
                            root.syncEditorState()
                            scriptEditorController.save_current_script(
                                root.token, folder.text, scriptTitle.text,
                                root.languageValue(), source.text)
                        }
                    }
                    Item { Layout.fillWidth: true }
                    RefreshIconButton {
                        theme: root.theme
                        toolTip: qsTr("Refresh scripts from server")
                        enabled: !scriptEditorController.busy
                        onClicked: scriptEditorController.refresh_scripts_tree()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 7
                    Label {
                        text: qsTr("Script path")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 9
                    }
                    Md3TextField {
                        id: folder
                        theme: root.theme
                        Layout.fillWidth: true
                        placeholderText: qsTr("Folder")
                        onTextChanged: if (!root.applyingEditorState)
                            draftSave.restart()
                    }
                    Label {
                        text: qsTr("/")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                    }
                    Md3TextField {
                        id: scriptTitle
                        theme: root.theme
                        Layout.fillWidth: true
                        placeholderText: qsTr("Title")
                        onTextChanged: if (!root.applyingEditorState)
                            draftSave.restart()
                    }
                Md3ComboBox {
                        id: language
                        theme: root.theme
                        Layout.preferredWidth: 150
                        model: scriptEditorController.languageOptions
                        textRole: "label"
                        valueRole: "value"
                        onActivated: {
                            root.applyLanguageRules()
                            root.syncEditorState()
                        }
                    }
                }

                ListView {
                    id: editorTabs
                    Layout.fillWidth: true
                    Layout.preferredHeight: 46
                    orientation: ListView.Horizontal
                    model: scriptEditorTabModel
                    spacing: 6
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.horizontal: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: editorTabs
                    }
                    delegate: Rectangle {
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
                        width: Math.min(210, Math.max(110, tabTitle.implicitWidth + 58))
                        height: 34
                        radius: 17
                        color: current
                            ? root.theme.secondaryContainer
                            : tabMouse.containsMouse
                                ? root.theme.rowHover
                                : root.theme.surfaceContainerLow
                        border.width: 1
                        border.color: current
                            ? root.theme.action : root.theme.outlineVariant
                        Behavior on color { ColorAnimation { duration: 110 } }
                        MouseArea {
                            id: tabMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.activateTab(scriptTab.tabId)
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 11
                            anchors.rightMargin: 3
                            spacing: 5
                            Rectangle {
                                Layout.preferredWidth: 6
                                Layout.preferredHeight: 6
                                radius: 3
                                color: scriptTab.dirty
                                    ? root.theme.yellow : root.theme.action
                            }
                            Label {
                                id: tabTitle
                                Layout.fillWidth: true
                                text: scriptTab.title || qsTr("Untitled")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 10
                                elide: Text.ElideRight
                            }
                            CompactIconButton {
                                Layout.preferredWidth: 28
                                Layout.preferredHeight: 28
                                theme: root.theme
                                round: true
                                iconName: "close"
                                iconSize: 13
                                toolTip: qsTr("Close tab")
                                onClicked: scriptEditorController.close_tab(
                                    scriptTab.tabId)
                            }
                        }
                    }
                }

                SplitView {
                    id: editorSplit
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    orientation: Qt.Vertical
                    handle: Rectangle {
                        implicitHeight: 10
                        color: "transparent"
                        Rectangle {
                            anchors.centerIn: parent
                            width: Math.max(0, parent.width - 18)
                            height: 1
                            color: root.theme.outlineVariant
                        }
                    }

                    Rectangle {
                        SplitView.fillHeight: true
                        SplitView.minimumHeight: 150
                        radius: 12
                        color: root.theme.panel
                        border.width: 1
                        border.color: root.theme.outlineVariant
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 6
                            spacing: 4
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 38
                                Layout.leftMargin: 6
                                Layout.rightMargin: 6
                                spacing: 8
                                MaterialIcon { name: "edit_note"; size: 16; color: root.theme.action }
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("Source")
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: root.theme.outlineVariant
                            }
                            ScrollView {
                                id: sourceScroll
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                rightPadding: 8
                                bottomPadding: 8
                                clip: true
                                ScrollBar.vertical: Md3ScrollBar {
                                    theme: root.theme
                                    flickableTarget: sourceScroll.contentItem
                                }
                                ScrollBar.horizontal: Md3ScrollBar {
                                    theme: root.theme
                                    flickableTarget: sourceScroll.contentItem
                                }
                                Md3TextArea {
                                    id: source
                                    theme: root.theme
                                    font.family: "Consolas"
                                    font.pixelSize: 10
                                    wrapMode: TextEdit.NoWrap
                                    onTextChanged: if (!root.applyingEditorState)
                                        draftSave.restart()
                                }
                            }
                        }
                    }

                    Rectangle {
                        id: outputDock
                        SplitView.preferredHeight: scriptEditorController.outputHeight
                        SplitView.minimumHeight: 100
                        radius: 12
                        color: root.theme.panel
                        border.width: 1
                        border.color: root.theme.outlineVariant
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 6
                            spacing: 4
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 38
                                Layout.leftMargin: 6
                                Layout.rightMargin: 6
                                spacing: 8
                                MaterialIcon { name: "terminal"; size: 16; color: root.theme.action }
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("Output")
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }
                                CompactIconButton {
                                    Layout.preferredWidth: 28
                                    Layout.preferredHeight: 28
                                    theme: root.theme
                                    round: true
                                    iconName: "delete_sweep"
                                    iconSize: 14
                                    toolTip: qsTr("Clear output")
                                    enabled: scriptEditorController.output.length > 0
                                    onClicked: scriptEditorController.cleanup_output()
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: root.theme.outlineVariant
                            }
                            ScrollView {
                                id: outputScroll
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                rightPadding: 8
                                bottomPadding: 8
                                onHeightChanged: layoutSave.restart()
                                clip: true
                                ScrollBar.vertical: Md3ScrollBar {
                                    theme: root.theme
                                    flickableTarget: outputScroll.contentItem
                                }
                                ScrollBar.horizontal: Md3ScrollBar {
                                    theme: root.theme
                                    flickableTarget: outputScroll.contentItem
                                }
                                Md3TextArea {
                                    id: outputPane
                                    theme: root.theme
                                    readOnly: true
                                    text: scriptEditorController.output
                                    font.family: "Consolas"
                                    font.pixelSize: 9
                                    wrapMode: TextEdit.NoWrap
                                    onTextChanged: Qt.callLater(function() {
                                        outputPane.cursorPosition = outputPane.length
                                        const flickable = outputScroll.contentItem
                                        if (flickable) {
                                            flickable.contentY = Math.max(
                                                0,
                                                flickable.contentHeight
                                                    - flickable.height
                                            )
                                        }
                                    })
                                }
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 7
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Run Script")
                        icon.name: "play_arrow"
                        highlighted: true
                        enabled: !scriptEditorController.busy
                            && language.currentIndex >= 0
                            && language.model[language.currentIndex].runnable !== false
                        onClicked: root.runCurrent()
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: qsTr("Execute")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 9
                    }
                    Md3ComboBox {
                        id: runMode
                        theme: root.theme
                        Layout.preferredWidth: 130
                        model: scriptEditorController.runModeOptions
                        textRole: "label"
                        valueRole: "value"
                        onActivated: draftSave.restart()
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: scriptEditorController.error
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pixelSize: 9
                    elide: Text.ElideRight
                }
            }
        }

        Rectangle {
            id: scriptsPanel
            SplitView.preferredWidth: scriptEditorController.treeWidth
            SplitView.minimumWidth: 190
            SplitView.maximumWidth: Math.max(260, mainSplit.width * 0.55)
            radius: 12
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 4
                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    Layout.leftMargin: 6
                    Layout.rightMargin: 6
                    spacing: 8
                    MaterialIcon { name: "account_tree"; size: 16; color: root.theme.action }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Scripts")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                    }
                    Md3BusyIndicator {
                        uiTheme: root.theme
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                        visible: scriptEditorController.busy
                        running: visible
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.theme.outlineVariant
                }
                ListView {
                    id: scripts
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: scriptEditorModel
                    clip: true
                    spacing: 2
                    boundsBehavior: Flickable.StopAtBounds
                    onWidthChanged: layoutSave.restart()
                    delegate: Rectangle {
                        id: treeRow
                        required property string token
                        required property string nodeType
                        required property string path
                        required property string folder
                        required property string title
                        required property string language
                        required property int depth
                        required property bool expanded
                        required property bool hasChildren
                        width: scripts.width
                        height: 38
                        radius: 9
                        color: root.token === token ? root.theme.secondaryContainer
                            : treeMouse.containsMouse ? root.theme.rowHover : "transparent"
                        Behavior on color { ColorAnimation { duration: 110 } }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 7 + treeRow.depth * 16
                            anchors.rightMargin: 7
                            spacing: 7
                            MaterialIcon {
                                visible: treeRow.nodeType === "folder"
                                name: treeRow.expanded ? "expand_more" : "chevron_right"
                                size: 16
                                color: root.theme.secondaryText
                            }
                            MaterialIcon {
                                name: treeRow.nodeType === "folder"
                                    ? treeRow.expanded ? "folder_open" : "folder" : "code"
                                size: 18
                                color: treeRow.nodeType === "folder"
                                    ? root.theme.action : root.theme.secondaryText
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                Label {
                                    Layout.fillWidth: true
                                    text: treeRow.title
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 10
                                    font.weight: treeRow.nodeType === "folder"
                                        ? Font.DemiBold : Font.Normal
                                    elide: Text.ElideRight
                                }
                                Label {
                                    visible: treeRow.nodeType === "script"
                                    Layout.fillWidth: true
                                    text: treeRow.language.replace("_", " ")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 8
                                    elide: Text.ElideRight
                                }
                            }
                        }
                        MouseArea {
                            id: treeMouse
                            anchors.fill: parent
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: mouse => {
                                if (mouse.button === Qt.RightButton) {
                                    if (treeRow.nodeType === "script") {
                                        scriptMenu.token = treeRow.token
                                        scriptMenu.actions = scriptEditorController.open_menu(treeRow.token)
                                        scriptMenu.openAt(treeRow, mouse.x, mouse.y)
                                    }
                                    return
                                }
                                if (treeRow.nodeType === "folder")
                                    scriptEditorController.toggle_folder(treeRow.path)
                                else
                                    root.loadScript(treeRow.token)
                            }
                        }
                    }
                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: scripts
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

    Md3Dialog {
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
            Md3Button {
                theme: root.theme
                text: qsTr("Delete")
                icon.name: "delete"
                highlighted: true
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
            Md3Button {
                theme: root.theme
                text: qsTr("Save all")
                icon.name: "save"
                highlighted: true
                onClicked: {
                    if (scriptEditorController.confirm_close_all_save())
                        closeAllConfirmation.close()
                }
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Discard all")
                icon.name: "delete_sweep"
                onClicked: {
                    scriptEditorController.confirm_close_all_discard()
                    closeAllConfirmation.close()
                }
            }
            Md3Button {
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
        function onScriptsLoaded(token) {
            if (token)
                root.loadScript(token)
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
