import QtQuick
import QtQuick.Controls
import "../.." as Tables

Item {
    id: root
    required property var theme
    required property var controller
    readonly property bool menuVisible: processCountMenu.visible
    function close() {
        processCountMenu.close();
    }
    property string processCountMenuNodeId: ""
    property string processCountMenuPanel: ""
    property var processCountMenuAnchorItem: null
    property var processCountRootRecords: []
    function openProcessCountMenu(nodeId, panel, anchorItem) {
        const records = root.controller.process_count_actions(nodeId, panel);
        if (records.length <= 1) {
            if (records.length > 0 && records[0].taskCode) {
                root.controller.open_process_task_details(nodeId, panel, String(records[0].process || "publish"), String(records[0].taskCode));
            } else {
                const process = records.length > 0 ? String(records[0].process || records[0].command || "publish") : "publish";
                root.controller.open_process_details(nodeId, panel, process);
            }
            return;
        }

        processCountMenuNodeId = nodeId;
        processCountMenuPanel = panel;
        processCountMenuAnchorItem = anchorItem;
        processCountRootRecords = records;
        showProcessCountRecords(records, panel === "tasks" ? qsTr("Tasks") : qsTr("Notes"), false);
    }

    function showProcessCountRecords(records, title, includeBack) {
        const actions = [
            {
                "title": title,
                "header": true
            }
        ];
        if (includeBack) {
            actions.push({
                "title": qsTr("All processes"),
                "translate": false,
                "icon": "arrow-left",
                "command": "back-processes",
                "keepOpen": true
            });
        }
        for (let index = 0; index < records.length; ++index)
            actions.push(records[index]);
        processCountMenu.replaceActions(actions);
        if (processCountMenu.opened)
            return;
        Qt.callLater(function () {
            if (root.processCountMenuAnchorItem)
                processCountMenu.openBelow(root.processCountMenuAnchorItem);
        });
    }

    function processCountAction(command) {
        const records = processCountMenu.actions || [];
        for (let index = 0; index < records.length; ++index) {
            if (String(records[index].command || "") === command)
                return records[index];
        }
        return ({});
    }

    Tables.ActionMenu {
        id: processCountMenu
        objectName: "workspaceProcessCountMenu"
        parent: Overlay.overlay
        theme: root.theme
        usePopupWindow: false
        preferredWidth: 212
        processPickerStyle: true
        alignBelowRight: true
        belowRightOverhang: 12
        anchorPointerVisible: true
        actions: []
        onTriggered: function (command) {
            if (command === "back-processes") {
                root.showProcessCountRecords(root.processCountRootRecords, root.processCountMenuPanel === "tasks" ? qsTr("Tasks") : qsTr("Notes"), false);
                return;
            }
            const action = root.processCountAction(command);
            if (action.taskCode) {
                root.controller.open_process_task_details(root.processCountMenuNodeId, root.processCountMenuPanel, String(action.process || "publish"), String(action.taskCode));
                return;
            }
            root.controller.open_process_details(root.processCountMenuNodeId, root.processCountMenuPanel, String(action.process || command || "publish"));
        }
        onSecondaryTriggered: function (command) {
            if (command.indexOf("tasks:") !== 0)
                return;
            const process = command.slice(6);
            const records = root.controller.process_task_actions(root.processCountMenuNodeId, root.processCountMenuPanel, process);
            root.showProcessCountRecords(records, process, true);
        }
    }
}
