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
    property string keyField: ""
    property var rowOffsets: null
    property real fixedRowHeight: 0
    property real rowsHeight: 0
    property bool ready: false
    property bool updating: false
    property int firstIndex: -1
    property int lastIndex: -1
    property var rowNodeCache: ({})
    property real cachedRowWidth: -1
    property var displayScene: ({
            nodes: []
        })
    readonly property int count: records.length
    signal event(var action, var source)

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
        const offsets = Contract.listOffsets(node, rows);
        const key = focusedKey();
        let offset = contentY;
        if (key !== null && indexes.has(String(key))) {
            const previous = recordPositions.get(String(key));
            if (previous !== undefined)
                offset += (offsets ? offsets[indexes.get(String(key))] : indexes.get(String(key)) * node.rowHeight) - (rowOffsets ? rowOffsets[previous] : previous * fixedRowHeight);
        }
        updating = true;
        records = rows;
        recordPositions = indexes;
        rowOffsets = offsets;
        fixedRowHeight = node.rowHeight;
        keyField = node.keyField;
        rowsHeight = offsets ? offsets[rows.length] : rows.length * node.rowHeight;
        contentY = Math.max(0, Math.min(offset, Math.max(0, contentHeight - height)));
        updating = false;
        firstIndex = -1;
        lastIndex = -1;
        rowNodeCache = ({});
        cachedRowWidth = width;
        refreshScene(true);
    }
    function refreshScene(force = false) {
        if (!ready || updating)
            return;
        if (force || cachedRowWidth !== width) {
            rowNodeCache = ({});
            cachedRowWidth = width;
        }
        const range = Contract.listRange(records.length, node.rowHeight, height, contentY, 3, rowOffsets);
        if (!force && range.first === firstIndex && range.last === lastIndex)
            return;
        firstIndex = range.first;
        lastIndex = range.last;
        displayScene = rowScene(range);
    }
    function rowScene(range) {
        if (!range)
            range = Contract.listRange(records.length, node.rowHeight, height, contentY, 3, rowOffsets);
        const nodes = [];
        const nextCache = {};
        const rowWidth = Math.max(0, width - 16);
        for (let index = range.first; index < range.last; index++) {
            const record = records[index];
            const key = String(record[node.keyField]);
            const bounds = Contract.listBounds(node, rowOffsets, index);
            const cached = rowNodeCache[index];
            if (cached && cached.record === record && cached.key === key && cached.y === bounds.y && cached.height === bounds.height && cached.width === rowWidth) {
                nextCache[index] = cached;
                nodes.push(cached.box);
                continue;
            }
            const box = Contract.node("Box", "row:" + key, Contract.rect(0, bounds.y, rowWidth, bounds.height), {
                recordKey: key,
                background: "transparent",
                children: describeRow(node, record, index).nodes
            });
            nextCache[index] = {
                record,
                key,
                y: bounds.y,
                height: bounds.height,
                width: rowWidth,
                box
            };
            nodes.push(box);
        }
        rowNodeCache = nextCache;
        return {
            nodes
        };
    }
    function focusControl(name) {
        return body.focusControl(name);
    }
    function focusListRow(id, row, controlId) {
        if (id !== node.id)
            return body.focusListRow(id, row, controlId);
        if (row < 0 || row >= count)
            return false;
        contentY = Contract.revealListOffset(contentY, row, height, count, node.rowHeight, node.rowGap === undefined ? 4 : node.rowGap, rowOffsets);
        refreshScene();
        if (controlId)
            Qt.callLater(() => body.focusControl(controlId));
        return true;
    }
    function focusGrid(id, row, column, name) {
        return body.focusGrid(id, row, column, name);
    }
    function graphCommand(id, command) {
        return body.graphCommand(id, command);
    }

    objectName: node.id
    Accessible.role: node.role === "tree" ? Accessible.Tree : Accessible.List
    Accessible.name: node.label || ""
    clip: true
    contentWidth: width
    contentHeight: rowsHeight
    boundsBehavior: Flickable.StopAtBounds
    onSourceRowsChanged: if (ready)
        replaceRecords()
    onNodeChanged: if (ready)
        replaceRecords()
    onContentYChanged: refreshScene(false)
    onWidthChanged: refreshScene(true)
    onHeightChanged: refreshScene(true)
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
        onEvent: (action, source) => root.event(action, source)
    }
    ScrollBar.vertical: Controls.ScrollBar {
        objectName: root.node.scrollbarId || ""
        theme: root.theme
        flickableTarget: root
    }
}
