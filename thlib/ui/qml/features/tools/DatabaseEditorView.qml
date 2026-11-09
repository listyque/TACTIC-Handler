import QtQuick
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tools/database.ui.mjs" as UI

Item {
    id: root
    required property var theme
    readonly property bool presentationActive: parent ? parent.visible : visible
    property int activeIndex: 0
    property var activeRecord: ({})
    property var fieldRows: []
    property var pendingChanges: ({})
    property int dirtyCount: 0
    property bool sessionInitialized: false
    property string sessionContextFingerprint: ""

    function currentContextFingerprint() {
        const nodeIds = appController.selected_result_node_ids || [];
        const selected = [];
        for (let index = 0; index < nodeIds.length; ++index)
            selected.push(String(nodeIds[index] || ""));
        return [String(appController.current_project_code || ""), String(appController.current_section_key || ""), String(appController.current_page_key || ""), selected.join("\u001f")].join("\u001e");
    }

    function beginSessionForCurrentContext(forceRefresh) {
        if (!root.presentationActive)
            return;
        const fingerprint = root.currentContextFingerprint();
        if (!forceRefresh && root.sessionInitialized && fingerprint === root.sessionContextFingerprint)
            return;
        columnsEditorController.begin_session();
        root.sessionContextFingerprint = fingerprint;
        root.sessionInitialized = true;
        root.rebuildProperties();
    }

    function rebuildProperties() {
        const records = appController.selected_result_records;
        if (!records || records.length === 0) {
            activeIndex = 0;
            activeRecord = ({});
            fieldRows = [];
            pendingChanges = ({});
            dirtyCount = 0;
            return;
        }
        activeIndex = Math.max(0, Math.min(activeIndex, records.length - 1));
        activeRecord = records[activeIndex];
        fieldRows = columnsEditorController.order_field_records(appController.editable_result_field_records(String(activeRecord.nodeId || "")));
        pendingChanges = ({});
        dirtyCount = 0;
    }

    function saveChanges() {
        appController.update_selected_item_fields(String(activeRecord.nodeId || ""), pendingChanges);
    }

    function markChanged(fieldName, originalValue, value) {
        pendingChanges = UI.changedFields(pendingChanges, fieldName, originalValue, value);
        dirtyCount = Object.keys(pendingChanges).length;
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.panelDeep
    }

    Connections {
        target: appController
        enabled: root.presentationActive
        function onSelected_node_changed() {
            root.beginSessionForCurrentContext(true);
        }
        function onProject_changed() {
            root.beginSessionForCurrentContext(false);
        }
        function onSection_state_changed() {
            root.beginSessionForCurrentContext(false);
        }
    }
    Connections {
        target: columnsEditorController
        enabled: root.presentationActive
        function onApplied() {
            root.rebuildProperties();
        }
    }
    Component.onCompleted: root.beginSessionForCurrentContext(false)
    onPresentationActiveChanged: root.beginSessionForCurrentContext(false)

    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property string bulkColumn: ""
    property string bulkValue: ""
    readonly property var columns: appController.selected_result_fields
    onColumnsChanged: if (!columns.includes(bulkColumn))
        bulkColumn = columns.length ? columns[0] : ""
    readonly property var projection: ({
            count: appController.selected_result_count,
            active: root.activeRecord,
            selected: root.activeIndex,
            pending: root.pendingChanges,
            busy: appController.loading,
            columns: root.columns,
            column: root.bulkColumn,
            bulkValue: root.bulkValue
        })
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        models: ({
                objects: appController.selected_result_records,
                fields: root.fieldRows
            })
        scene: UI.describe(root.projection, width, height, root.language)
        describeRow: (list, record, index) => UI.row(list, record, index, root.projection)
        onEvent: action => {
            if (action.type === "save")
                root.saveChanges();
            else if (action.type === "select") {
                root.activeIndex = action.value;
                root.rebuildProperties();
            } else if (action.type === "field")
                root.markChanged(action.field, action.original, action.value);
            else if (action.type === "column")
                root.bulkColumn = action.value;
            else if (action.type === "bulkValue")
                root.bulkValue = action.value;
            else if (action.type === "bulk" && root.bulkColumn && !appController.loading)
                appController.update_selected_items(root.bulkColumn, root.bulkValue);
        }
    }
}
