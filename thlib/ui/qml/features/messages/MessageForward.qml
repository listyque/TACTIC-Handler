import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/messages/panels.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var conversations
    required property var targets
    property bool active: true
    property int selectionCount: 0
    property bool busy: false
    property bool valid: false
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    signal targetToggled(string key)
    signal cancelled
    signal submitted
    scene: active ? UI.forwarding({
        count: selectionCount,
        busy,
        valid
    }, width, height, language) : ({
            nodes: []
        })
    models: ({
            conversations
        })
    describeRow: (node, record) => UI.forward(Object.assign({}, record, {
            selected: !!root.targets[record.conversationId],
            busy: root.busy
        }), Math.max(0, node.width - 16), language)
    onEvent: action => {
        if (action.type === "toggle")
            targetToggled(action.key);
        else if (action.type === "cancel")
            cancelled();
        else if (action.type === "submit")
            submitted();
    }
}
