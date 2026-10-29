import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/services.ui.mjs" as UI
import "../../tactic_frame/features/table/drop.ui.mjs" as Drop
import "../../tactic_frame/features/table/parent.state.mjs" as ParentState
import "../../tactic_frame/features/table/connections.ui.mjs" as ConnectionRows

Frame.FrameView {
    id: root
    required property var controller
    required property string nodeId
    required property var cell
    required property var services
    required property var administration
    property var displayOptions: ({})
    property var expanded: ({})
    property bool editable: true
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var nestedScope: cell.nestedTable && services ? services.nested_row(nodeId, services.nestedRevision) : null
    scene: UI.describe(cell, width, height, language, editable, Object.assign({}, expanded, {
        __nested: nestedScope ? nestedScope.expansionState : null
    }), controller.server_url || "")
    models: ({
            connectionRows: cell.connectionRows || []
        })
    describeRow: (list, record, index) => ConnectionRows.row(record, cell, Math.max(0, list.width - 16), language, editable, controller.server_url || "")
    onEvent: (action, value) => {
        if (action.name === "change-parent" || action.name === "drop-parent") {
            try {
                services.parentGroups.open(root, nodeId, cell, action.name === "drop-parent" ? ParentState.dropParentKey(action.value) : "");
            } catch (error) {
                services.report_error(error.message || String(error));
            }
            return;
        }
        if (action.name === "remove-connection") {
            services.request_connection_removal(nodeId, Object.assign({}, cell, {
                connectionKey: action.connectionKey,
                expectedRevision: action.expectedRevision,
                direction: action.direction
            }));
            return;
        }
        if (action.name === "layout-document")
            services.customLayout.open_cell(nodeId, cell);
        else if (action.name === "nested-table")
            services.toggle_nested(nodeId, Object.assign({}, cell, {
                nestedTable: action.nestedTable || cell.nestedTable
            }));
        else if (action.name === "dependencies")
            services.dependencyViewer.open(nodeId, cell);
        else if (action.name === "file-checkout")
            services.open_checkout(nodeId, cell);
        else if (action.name === "file-append")
            services.open_append(nodeId, cell);
        else if (action.name === "file-ingest")
            services.open_ingest(nodeId, cell, Array.isArray(action.value) ? action.value : []);
        else if (action.name === "layout-link")
            services.open_link(action.href);
        else if (["edit-links", "drop-links"].indexOf(action.name) >= 0) {
            try {
                services.open_links(nodeId, cell, action.name === "drop-links" ? Drop.droppedKeys(action.value, cell.acceptedType) : []);
            } catch (error) {
                services.report_error(String(error));
            }
        } else if (action.type === "parallel-toggle") {
            const next = Object.assign({}, root.expanded);
            next[action.identity] = !next[action.identity];
            root.expanded = next;
        } else if (action.name === "work-hours")
            workHoursController.open_table_task(cell.taskKey, action.day || cell.week || "");
        else if (["task-details", "add-task", "work", "table-schedule"].indexOf(action.name) >= 0)
            services.open_task_action(action.name, nodeId, Object.assign({}, cell, {
                actionTaskCode: action.taskCode,
                actionTaskKey: action.taskKey,
                actionProcess: action.process,
                actionScheduleIndex: action.scheduleIndex,
                actionLogin: action.login || cell.login || "",
                actionParentKeys: action.parentKeys || [],
                actionScope: action.scope || cell.scope || ""
            }));
        else if (action.name === "script")
            services.run_script(nodeId, Object.assign({}, cell, {
                displayOptions: Object.assign({}, root.displayOptions, action.javascript ? {
                    cbjs_action: action.javascript
                } : {})
            }));
        else if (action.name === "preference")
            services.open_preference(root, cell);
        else if (action.name === "notification-test")
            services.test_notification(cell.targetSearchKey || nodeId);
        else if (action.name === "security")
            administration.open_group_security(cell.groupCode);
        else if (["retire", "reactivate"].indexOf(action.name) >= 0)
            services.request_object_action(action.name, cell);
        else if (action.name === "template")
            services.request_template(cell.projectCode);
        else {
            const details = Object.assign({}, cell, {
                actionView: action.view
            });
            const target = action.targetSearchKey || cell.targetSearchKey;
            if (target)
                details.targetSearchKey = target;
            controller.invoke_table_widget_action(action.name, nodeId, details);
        }
    }
}
