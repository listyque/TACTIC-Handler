import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/parent.state.mjs" as State
import "../../tactic_frame/features/table/parent.ui.mjs" as UI
import "../../tactic_frame/core/strings.mjs" as Strings

Frame.FrameView {
    id: root
    objectName: "tableParentGroupView"
    required property var owner
    property var state: State.create({})
    property bool ready: false
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var records: State.rows(state)
    Accessible.role: Accessible.Dialog
    Accessible.name: Strings.translate("Change parent", language)
    function apply(change) {
        state = change.state;
        if (change.request)
            owner.request(change.request);
        else if (change.close)
            owner.finish(!!change.saved);
    }
    function reset() {
        if (ready && owner.isOpen)
            apply(State.begin(State.create(owner.seed), "prepare"));
    }
    function focusQuery() {
        if (state.ready && owner.isOpen)
            focusControl("parentQuery");
    }
    scene: UI.describe(state, width, height, language)
    models: ({
            parentRows: records
        })
    describeRow: (list, record) => UI.row(record, Math.max(0, list.width - 16), language)
    onEvent: action => apply(State.dispatch(state, action))
    Keys.onShortcutOverride: event => {
        if (event.key === Qt.Key_Escape)
            event.accepted = true;
    }
    Keys.onEscapePressed: event => {
        apply(State.dispatch(state, {
            type: "cancel"
        }));
        event.accepted = true;
    }
    Component.onCompleted: {
        ready = true;
        reset();
    }
    Connections {
        target: root.owner
        function onSeedChanged() {
            root.reset();
        }
        function onReceived(operation, result, error, uncertain) {
            root.apply(State.accept(root.state, operation, result, error, uncertain));
            if (operation === "prepare" && !error)
                Qt.callLater(root.focusQuery);
        }
    }
}
