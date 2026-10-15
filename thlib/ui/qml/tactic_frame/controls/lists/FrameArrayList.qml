import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../core"
import "../../core/frame.mjs" as Contract

Flickable {
    id: root
    required property var theme
    required property var node
    required property var sourceRows
    property var models: ({})
    property var views: ({})
    required property var describeRow
    property var describeCell: null
    property bool interactiveContent: true
    property var records: []
    property var recordPositions: new Map()
    property string keyField: node.keyField
    property bool ready: false
    property bool updating: false
    property var displayScene: ({
            nodes: []
        })
    readonly property int count: records.length
    signal event(var action)

    // Frame metadata is dynamic; a plain QQuickItem does not declare it.
    function frameKey(item: var): var {
        return item.frameRecordKey;
    }
    function focusedKey() {
        const focused = root.Window.window ? root.Window.window.activeFocusItem : null;
        let key = null;
        for (let item = focused; item; item = item.parent) {
            if (item === root)
                return key;
            const value = frameKey(item);
            if (value !== undefined)
                key = value;
        }
        return null;
    }
    function replaceRecords() {
        const rows = sourceRows || [];
        const indexes = Contract.recordIndex(rows, node.keyField);
        const key = focusedKey();
        let offset = contentY;
        if (key !== null && indexes.has(String(key))) {
            const previous = recordPositions.get(String(key));
            if (previous !== undefined)
                offset += (indexes.get(String(key)) - previous) * node.rowHeight;
        }
        updating = true;
        records = rows;
        recordPositions = indexes;
        contentY = Math.max(0, Math.min(offset, Math.max(0, rows.length * node.rowHeight - height)));
        updating = false;
        refreshScene();
    }
    function refreshScene() {
        if (ready && !updating)
            displayScene = rowScene();
    }
    function rowScene() {
        const range = Contract.virtualRange(records.length, node.rowHeight, height, contentY, 3);
        const nodes = [];
        for (let index = range.first; index < range.last; index++) {
            const record = records[index];
            const key = String(record[node.keyField]);
            nodes.push(Contract.node("Box", "row:" + key, Contract.rect(0, index * node.rowHeight, Math.max(0, width - 16), node.rowHeight - 4), {
                recordKey: key,
                background: "transparent",
                children: describeRow(node, record).nodes
            }));
        }
        return {
            nodes
        };
    }
    function focusControl(name) {
        return body.focusControl(name);
    }
    function focusGrid(id, row, column, name) {
        return body.focusGrid(id, row, column, name);
    }
    function graphCommand(id, command) {
        return body.graphCommand(id, command);
    }

    objectName: node.id
    clip: true
    contentWidth: width
    contentHeight: records.length * node.rowHeight
    boundsBehavior: Flickable.StopAtBounds
    onSourceRowsChanged: if (ready)
        replaceRecords()
    onNodeChanged: if (ready)
        replaceRecords()
    onContentYChanged: refreshScene()
    onWidthChanged: refreshScene()
    onHeightChanged: refreshScene()
    Component.onCompleted: {
        ready = true;
        replaceRecords();
    }

    FrameBranch {
        id: body
        width: root.width
        height: root.contentHeight
        theme: root.theme
        scene: root.displayScene
        models: root.models
        views: root.views
        describeRow: root.describeRow
        describeCell: root.describeCell
        interactive: root.interactiveContent
        onEvent: action => root.event(action)
    }
    ScrollBar.vertical: Controls.ScrollBar {
        objectName: root.node.scrollbarId || ""
        theme: root.theme
        flickableTarget: root
    }
}
