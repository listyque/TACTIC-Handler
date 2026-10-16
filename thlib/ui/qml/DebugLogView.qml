import QtQuick
import QtQuick.Dialogs
import "tactic_frame" as Frame
import "tactic_frame/features/support/diagnostics/debug.ui.mjs" as UI
import "tactic_frame/features/support/diagnostics/performance.ui.mjs" as Selection

Item {
    id: root
    required property var theme
    property real groupWidth: debugLog.group_panel_width
    property real detailHeight: debugLog.detail_panel_height
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: Object.assign({}, debugLog.presentation, {
        groupWidth,
        detailHeight
    })
    function row(list, record) {
        return UI.row(frameModel, list, record, list.width - 16, language);
    }
    function dispatch(action) {
        if (action.type === "search")
            debugLog.set_search(action.value);
        else if (action.type === "group")
            debugLog.select_group(action.value);
        else if (action.type === "level")
            debugLog.set_level_enabled(action.level, frameModel.enabled.indexOf(action.level) < 0);
        else if (action.type === "event")
            debugLog.select_event(action.id);
        else if (action.type === "eventKey") {
            const rows = [];
            for (let index = 0; index < frameModel.visibleCount; index++)
                rows.push(debugLogModel.get(index));
            const target = Selection.selection(rows, action.id, action.key, "eventId");
            if (target) {
                debugLog.select_event(target.eventId);
                frame.focusListRow("debugEvents", rows.findIndex(record => record.eventId === target.eventId), "debugEvent_" + target.eventId);
            }
        } else if (action.type === "sourceWidth") {
            groupWidth = action.value;
            saveLayout.restart();
        } else if (action.type === "detailHeight") {
            detailHeight = action.value;
            saveLayout.restart();
        } else if (action.type === "session" && action.value !== "file") {
            if (action.value === "")
                debugLog.show_live_session();
            else
                debugLog.load_session_row(Number(action.value));
        } else if (action.type === "live")
            debugLog.show_live_session();
        else if (action.type === "open")
            sessionFileDialog.open();
        else if (action.type === "path")
            debugLog.copy_session_path();
        else if (action.type === "clear")
            debugLog.clear();
        else if (action.type === "inspect")
            debugLog.inspect_selected();
        else if (action.type === "copy")
            debugLog.copy_selected();
        else if (action.type === "copyCommand")
            debugLog.copy_selected_command();
        else if (action.type === "help")
            windowModel.open_help("debug_log");
    }
    Timer {
        id: saveLayout
        interval: 180
        onTriggered: debugLog.save_layout(root.groupWidth, root.detailHeight)
    }
    Component.onDestruction: if (saveLayout.running)
        debugLog.save_layout(groupWidth, detailHeight)
    FileDialog {
        id: sessionFileDialog
        title: qsTr("Open debug session")
        nameFilters: ["TACTIC session logs (*.jsonl)", "All files (*)"]
        onAccepted: debugLog.load_session_file(selectedFile.toString())
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }
    Frame.FrameView {
        id: frame
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, root.width, root.height, root.language)
        models: ({
                groups: debugGroupModel,
                events: debugLogModel
            })
        describeRow: root.row
        onEvent: action => root.dispatch(action)
    }
}
