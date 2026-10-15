import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/database/raw.ui.mjs" as UI
import "../../../tactic_frame/features/administration/database/raw.state.mjs" as State

Item {
    id: root
    objectName: "rawCellEditorPage"
    required property var theme
    readonly property var controller: administrationController.rawEditor
    readonly property var cell: Object.assign({}, controller.cell, {
        busy: controller.busy
    })
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
    property var ui: State.cellInitial({})
    readonly property var frameScene: UI.cellDescribe(cell, ui, width, height, language)
    function initialize() {
        if (!cell.name || ui.session === cell.session)
            return;
        ui = State.cellInitial(cell);
        Qt.callLater(() => body.focusControl("rawCellValue"));
    }
    function dispatch(action) {
        const result = State.cellTransition(ui, cell, action);
        ui = result.ui;
        for (const command of result.commands) {
            if (command.type === "apply")
                controller.apply_cell(command.mode, command.text);
            else if (command.type === "cancel")
                controller.cancel_cell();
            else
                throw Error("Unsupported Cell editor command: " + command.type);
        }
    }
    Component.onCompleted: initialize()
    Connections {
        target: root.controller
        function onCellChanged() {
            root.initialize();
        }
    }
    Shortcut {
        sequence: "Ctrl+Return"
        onActivated: root.dispatch({
            type: "apply"
        })
    }
    Shortcut {
        sequence: "Escape"
        onActivated: root.dispatch({
            type: "cancel"
        })
    }
    Frame.FrameView {
        id: body
        anchors.fill: parent
        theme: root.theme
        scene: root.frameScene
        onEvent: action => root.dispatch(action)
    }
}
