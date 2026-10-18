import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/knowledge/navigation.ui.mjs" as UI

Frame.FrameView {
    id: root
    property var entries: []
    property bool compact: false
    property string title: qsTr("On this page")
    signal headingRequested(var heading)
    implicitWidth: 220
    implicitHeight: compact ? Math.min(210, 42 + entries.length * 30) : 260
    scene: UI.outline(entries, width, height, title, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
    models: ({
            headings: UI.outlineEntries(root.entries)
        })
    describeRow: (list, record, index) => UI.heading(record, index, Math.max(0, list.width - 16))
    onEvent: action => root.headingRequested(root.entries[action.index])
}
