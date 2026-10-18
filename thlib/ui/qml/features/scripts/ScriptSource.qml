import QtQuick
import QtQuick.Controls
import "../../" as TH
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/scripts/source.ui.mjs" as UI

Rectangle {
    id: root
    objectName: "scriptEditorSourcePanel"
    required property var theme
    required property var controller
    required property string token
    required property string language
    property bool readOnly: false
    property bool busy: false
    property real fontPointSize: 9.25
    property var symbols: []
    readonly property alias editor: source
    property int revision: 0
    signal edited
    signal runRequested
    signal outlineRequested
    signal helpRequested
    signal syncRequested
    signal fontRequested(real value)
    readonly property var model: {
        source.historyRevision;
        const history = source.currentHistory();
        return {
            native: true,
            canUndo: source.canUndo,
            canRedo: source.canRedo,
            canCopy: source.canCopy,
            historyCount: history ? history.entries.length + 1 : 1,
            historyIndex: history ? history.index : 0,
            fontSize: root.fontPointSize,
            readOnly: root.readOnly || root.busy,
            saved: root.token.length > 0,
            busy: root.busy
        };
    }
    readonly property var toolbarScene: UI.describe(root.model, Math.max(530, toolbar.width), root.language, root.revision)
    readonly property var savedBounds: toolbarScene.nodes.find(row => row.id === "scriptSource_saved")
    function event(action) {
        revision++;
        if (action.type === "font")
            root.fontRequested(Number(action.value));
        else if (action.type === "history")
            source.applyHistoryIndex(Number(action.value));
        else if (action.type === "selection")
            root.runRequested();
        else if (action.type === "outline")
            root.outlineRequested();
        else if (action.type === "saved") {
            savedHistory.pressed();
            savedHistory.clicked();
        } else if (action.type === "command") {
            const commands = {
                undo: () => source.undoEdit(),
                redo: () => source.redoEdit(),
                cut: () => source.cutSelection(),
                copy: () => source.copySelection(),
                paste: () => source.pasteClipboard(),
                find: () => source.showFind(false),
                replace: () => source.showFind(true),
                help: () => root.helpRequested()
            };
            if (commands[action.value])
                commands[action.value]();
        }
    }
    radius: 12
    color: theme.panel
    border.width: 1
    border.color: theme.outlineVariant
    Flickable {
        id: toolbar
        objectName: "scriptEditorSourceToolbar"
        x: 4
        y: 4
        width: Math.max(0, root.width - 8)
        height: UI.toolbarHeight(width)
        contentWidth: Math.max(530, width)
        contentHeight: 30
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        Frame.FrameView {
            width: toolbar.contentWidth
            height: 30
            theme: root.theme
            scene: root.toolbarScene
            onEvent: action => root.event(action)
        }
        ScrollBar.horizontal: Controls.ScrollBar {
            id: bar
            objectName: "scriptEditorSourceToolbarScrollBar"
            theme: root.theme
            flickableTarget: toolbar
        }
    }
    TH.ScriptSavedHistoryButton {
        id: savedHistory
        parent: toolbar.contentItem
        objectName: "scriptSource_saved"
        x: root.savedBounds.x
        y: root.savedBounds.y
        width: 28
        height: 28
        theme: root.theme
        controller: root.controller
        sourceEditor: source
        scriptToken: root.token
        onSyncRequested: root.syncRequested()
    }
    Controls.ScriptCodeEditor {
        id: source
        objectName: "scriptEditorCodeEditor"
        x: 4
        y: toolbar.y + toolbar.height + 4
        width: Math.max(0, root.width - 8)
        height: Math.max(0, root.height - y - 4)
        theme: root.theme
        controller: root.controller
        fontPointSize: root.fontPointSize
        symbols: root.symbols
        readOnly: root.readOnly || root.busy
        onTextEdited: root.edited()
        onRunRequested: root.runRequested()
        onOutlineRequested: root.outlineRequested()
    }
}
