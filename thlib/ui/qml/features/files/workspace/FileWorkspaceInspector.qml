import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/inspector.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var info
    required property var preview
    required property string currentTab
    property bool historyMode: false
    property bool busy: false
    property string error: ""
    readonly property var file: info.file || ({})
    readonly property bool hasFile: Boolean(info.path)
    readonly property var details: UI.details(info, historyMode)
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    signal tabSelected(string tab)
    objectName: historyMode ? "historyRevisionInspector" : "workspaceFileInspector"
    clip: true
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            info: root.info,
            preview: root.preview,
            tab: root.currentTab,
            history: root.historyMode,
            busy: root.busy,
            error: root.error
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "tab")
                root.tabSelected(action.value);
        }
    }
}
