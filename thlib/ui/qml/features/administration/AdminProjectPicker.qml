pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/administration/projects.ui.mjs" as UI

Item {
    id: root
    objectName: "administrationProjectPickerControl"
    required property var theme
    required property var model
    property string language: "en"
    property string query: ""
    readonly property var rows: UI.projects(model, query)
    readonly property var bounds: UI.size(root.Window.window ? root.Window.window.width : 800, root.Window.window ? root.Window.window.height : 600, (model.projects || []).length)
    signal selected(string code)
    onModelChanged: if (model.locked)
        chooser.close()
    function dispatch(event) {
        if (model.locked)
            return;
        if (event.type === "open") {
            if (chooser.opened) {
                chooser.close();
                return;
            }
            query = "";
            chooser.openBelowItem(trigger, false, 4);
            Qt.callLater(() => content.focusControl("administrationProjectSearch"));
        } else if (event.type === "query")
            query = event.value;
        else if (event.type === "focus") {
            const row = rows[event.index];
            if (row)
                content.focusListRow("administrationProjectList", event.index, "administrationProjectOption_" + row.value);
        } else if (event.type === "select" && model.projects.some(row => row.value === event.value)) {
            chooser.close();
            root.selected(event.value);
        }
    }
    Frame.FrameView {
        id: trigger
        anchors.fill: parent
        theme: root.theme
        scene: UI.trigger(root.model, width, height, root.language)
        onEvent: action => root.dispatch(action)
    }
    Controls.Popup {
        id: chooser
        objectName: "administrationProjectPopup"
        theme: root.theme
        parent: Overlay.overlay
        padding: 6
        focus: true
        width: root.bounds.width + 12 + 2 * effectiveShadowMargin
        height: root.bounds.height + 12 + 2 * effectiveShadowMargin
        onClosed: trigger.focusControl("administrationProjectSelector")
        contentItem: Frame.FrameView {
            id: content
            theme: root.theme
            scene: UI.panel(root.model, root.query, width, height, root.language)
            models: ({
                    projects: root.rows
                })
            describeRow: (list, row) => UI.row(list, row, root.model, root.query, root.language)
            onEvent: action => root.dispatch(action)
        }
    }
}
