import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/depots.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property real desktopExtent: -1
    property real mobileExtent: -1
    readonly property var frameModel: ({
            draft: editing ? draft : null,
            selected: state.catalog_detail,
            administrator: state.administrator,
            busy: controller.busy,
            repositories: state.catalog_capabilities.repositories || [],
            notice: notice,
            after: state.catalog_after,
            extent: width < 600 ? (mobileExtent < 0 ? undefined : mobileExtent) : (desktopExtent < 0 ? undefined : desktopExtent)
        })
    readonly property var state: controller.view_data
    readonly property var draft: state.depot_draft || ({})
    readonly property bool editing: draft.creating !== undefined
    readonly property bool dirty: JSON.stringify(draft) !== JSON.stringify(state.depot_original || {})
    property string notice: ""
    function change(key, value) {
        const next = Object.assign({}, draft);
        next[key] = value;
        controller.set_value("depot_draft", next);
    }
    function edit(row) {
        if (dirty) {
            notice = qsTr("Save or reset the current depot draft first.");
            return;
        }
        notice = "";
        controller.action("depot_editor", row ? {
            depot: row.code
        } : {});
    }
    function reset() {
        controller.set_value("depot_draft", state.depot_original);
        notice = "";
    }

    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        models: ({
                depots: root.controller.catalog_model
            })
        describeRow: (list, record) => UI.row(root.frameModel, record, list.width - 16, root.language)
        onEvent: action => {
            if (action.type === "split") {
                if (root.width < 600)
                    root.mobileExtent = action.value;
                else
                    root.desktopExtent = action.value;
            } else if (action.type === "select") {
                const record = root.controller.catalog_model.records().find(row => row.id === action.key);
                if (record)
                    root.controller.set_value("catalog_detail", record.node);
            } else if (action.type === "refresh")
                root.controller.action("catalog_page", {});
            else if (action.type === "more")
                root.controller.action("catalog_page", {
                    more: true
                });
            else if (action.type === "field")
                root.change(action.key, action.value);
            else if (action.type === "new")
                root.edit(null);
            else if (action.type === "edit")
                root.edit(root.state.catalog_detail);
            else if (action.type === "reset")
                root.reset();
            else if (action.type === "cancel") {
                if (root.dirty) {
                    root.notice = qsTr("Save or reset the current depot draft first.");
                    return;
                }
                root.controller.set_value("depot_draft", {});
                root.controller.set_value("depot_original", {});
            } else if (action.type === "save")
                root.controller.action("save_depot", {});
        }
    }
}
