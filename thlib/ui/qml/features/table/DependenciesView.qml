import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/dependencies.ui.mjs" as UI
import "../../tactic_frame/features/table/dependencies.state.mjs" as State

Frame.FrameView {
    id: root
    required property var owner
    required property var model
    property var viewState: State.create("", "")
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var records: State.rows(viewState)
    signal closeRequested
    property bool viewInitialized: false

    function read(change) {
        viewState = change.state;
        if (change.request)
            owner.request(change.request);
    }
    function reset() {
        if (!viewInitialized)
            return;
        owner.restart_reads();
        read(State.begin(State.create(model.searchKey, model.projectCode), "root"));
    }
    onModelChanged: reset()
    Component.onCompleted: {
        viewInitialized = true;
        reset();
    }
    scene: UI.describe(viewState, width, height, language)
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
            read(State.begin(viewState, action.path, !!action.more));
        else if (action.type === "toggle") {
            const record = records.find(row => row.path === action.path);
            if (record)
                read(State.toggle(viewState, record));
        } else if (action.type === "file") {
            viewState = Object.assign({}, viewState, {
                notice: ""
            });
            owner.open_file(action);
        }
    }
    Connections {
        target: root.owner
        function onReceived(path, result, error) {
            root.viewState = State.accept(root.viewState, path, result, error);
        }
        function onFileFailed(error) {
            root.viewState = Object.assign({}, root.viewState, {
                notice: error
            });
        }
    }
}
