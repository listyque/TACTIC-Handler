import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/dependencies.ui.mjs" as UI
import "../../tactic_frame/features/table/dependencies.state.mjs" as State

Frame.FrameView {
    id: root
    required property var owner
    required property var model
    property var state: State.create("", "")
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var records: State.rows(state)
    signal closeRequested
    property bool ready: false

    function read(change) {
        state = change.state;
        if (change.request)
            owner.request(change.request);
    }
    function reset() {
        if (!ready)
            return;
        owner.restart_reads();
        read(State.begin(State.create(model.searchKey, model.projectCode), "root"));
    }
    onModelChanged: reset()
    Component.onCompleted: {
        ready = true;
        reset();
    }
    scene: UI.describe(state, width, height, language)
    models: ({
            dependencyRows: records
        })
    describeRow: (list, row, index) => UI.row(row, Math.max(0, list.width - 16), language)
    onEvent: action => {
        if (action.type === "close")
            closeRequested();
        else if (action.type === "refresh")
            reset();
        else if (action.type === "read")
            read(State.begin(state, action.path, !!action.more));
        else if (action.type === "toggle") {
            const record = records.find(row => row.path === action.path);
            if (record)
                read(State.toggle(state, record));
        } else if (action.type === "file") {
            state = Object.assign({}, state, {
                notice: ""
            });
            owner.open_file(action);
        }
    }
    Connections {
        target: root.owner
        function onReceived(path, result, error) {
            root.state = State.accept(root.state, path, result, error);
        }
        function onFileFailed(error) {
            root.state = Object.assign({}, root.state, {
                notice: error
            });
        }
    }
}
