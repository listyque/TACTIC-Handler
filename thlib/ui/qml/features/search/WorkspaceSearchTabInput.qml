import QtQuick
import "../../controls" as Controls

Controls.WorkspaceTabInput {
    id: root
    required property var owner
    required property var tabsModel
    required property var tabHost
    required property int rowIndex
    recordsProvider: () => Array.from({
            length: root.tabHost.count
        }, (_, i) => {
            const record = root.tabsModel.get(i);
            return {
                id: record.entryKey,
                closable: record.closable
            };
        })
    onCommand: action => {
        const host = root.tabHost, model = root.tabsModel, owner = root.owner, rowIndex = root.rowIndex;
        if (action.type === "close")
            owner.close_tab(rowIndex);
        else if (action.type === "reorder")
            owner.reorder_tab(action.source, action.target);
        else {
            const record = Array.from({
                length: host.count
            }, (_, i) => model.get(i)).find(row => row.entryKey === action.id);
            if (record)
                owner.activate_tab(record.entryKey, record.title);
        }
        Qt.callLater(() => {
            const index = Array.from({
                length: host.count
            }, (_, i) => model.get(i)).findIndex(record => record.current);
            if (index < 0)
                return;
            host.positionViewAtIndex(index, ListView.Contain);
            host.forceLayout();
            const tab = host.itemAtIndex(index);
            if (tab)
                tab.forceActiveFocus();
        });
    }
}
