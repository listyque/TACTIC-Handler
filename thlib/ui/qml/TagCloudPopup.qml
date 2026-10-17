import "tactic_frame/controls/lists/chips.mjs" as Chips
import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/search/popups.ui.mjs" as UI
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls

Controls.ScrollablePopup {
    id: root

    required property var controller
    property var records: []
    property string searchText: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property string searchQuery: searchText.trim().toLowerCase()
    property var filteredRecords: []
    property var rows: []
    property real rowsHeight: 0
    property real minimumRowHeight: 1
    property int rowCapacity: 0
    property real packedWidth: -1
    property string packedTextMetricsKey: ""
    property string packedSearchQuery: ""
    readonly property real chipSpacing: 8
    readonly property real rowWidth: Math.max(0, viewport.width - verticalScrollBar.reservedExtent)
    readonly property int firstRow: rowAt(viewport.contentY - cloud.y)
    readonly property int neededRows: rows.length > 0 ? rowAt(viewport.contentY + viewport.height - cloud.y) - firstRow + 2 : 0
    readonly property string allLabel: qsTr("ALL")
    readonly property string textMetricsKey: theme.fontFamily + "|" + sizingChip.Screen.logicalPixelDensity + "|" + allLabel

    function openBelow(sourceItem) {
        openBelowItem(sourceItem, true, 6);
    }

    function toggleBelow(sourceItem) {
        toggleBelowItem(sourceItem, true, 6);
    }

    function updateFilteredRecords(repack) {
        const query = searchQuery;
        // Publish the projection before measuring it; a searchQuery signal
        // can run before a dependent QML binding has reevaluated.
        filteredRecords = query.length > 0 ? records.filter(record => String(record.tag).toLowerCase().includes(query)) : records;
        if (repack)
            packRows();
    }

    function packRows() {
        if (!visible || rowWidth <= 0)
            return;
        const catalog = filteredRecords;
        rows = Chips.packTagRows(catalog, rowWidth, function (label, weight) {
            sizingChip.text = label;
            sizingChip.emphasis = weight;
            return sizingChip.implicitWidth - 24;
        }, allLabel);
        minimumRowHeight = rows.length ? Math.min.apply(null, rows.map(row => row.height)) : 1;
        rowsHeight = rows.length ? rows[rows.length - 1].top + rows[rows.length - 1].height : 0;
        packedWidth = rowWidth;
        packedTextMetricsKey = textMetricsKey;
        packedSearchQuery = searchQuery;
    }

    function rowAt(y) {
        return Chips.tagRowAt(rows, y);
    }

    function focusTag(recordIndex) {
        if (recordIndex < -1 || recordIndex >= filteredRecords.length) {
            // Let normal Tab order return to the header, visibly.
            viewport.contentY = viewport.originY;
            return false;
        }
        for (let row = 0; row < rows.length; ++row) {
            const cells = rows[row].cells;
            const column = recordIndex - cells[0].index;
            if (column < 0 || column >= cells.length)
                continue;
            const top = cloud.y + rows[row].top;
            const bottom = top + rows[row].height;
            if (top < viewport.contentY)
                viewport.contentY = top;
            else if (bottom > viewport.contentY + viewport.height)
                viewport.contentY = bottom - viewport.height;
            const slot = rowSlots.itemAt(row - firstRow) as TagRow;
            if (slot)
                slot.focusCell(column);
            return true;
        }
        return false;
    }

    function updateCatalog() {
        const catalog = controller.tag_cloud;
        let changed = catalog.length !== records.length || packedWidth !== rowWidth || packedTextMetricsKey !== textMetricsKey || packedSearchQuery !== searchQuery;
        for (let i = 0; !changed && i < catalog.length; ++i)
            changed = catalog[i].tag !== records[i].tag || catalog[i].weight !== records[i].weight;
        // Selection changes update visible buttons, not text measurement or
        // row positions. Keep only this catalog's lightweight layout on close.
        records = catalog;
        updateFilteredRecords(changed);
    }

    preferredSurfaceWidth: UI.popup.width
    minimumSurfaceWidth: UI.popup.minimumWidth
    fixedSurfaceHeight: root.theme.controlHeight * 8
    contentSpacing: 0
    // The selector is immediately usable; do not inherit Material's 220 ms
    // grow transition before its opened state and hit geometry settle.
    enter: null
    exit: null

    onAboutToShow: {
        root.searchText = "";
        updateCatalog();
        rowCapacity = neededRows;
    }
    onOpened: tagHeader.focusControl("tagCloudSearchField")
    onSearchQueryChanged: {
        if (!visible)
            return;
        viewport.cancelFlick();
        viewport.contentY = viewport.originY;
        updateFilteredRecords(true);
    }
    onRowWidthChanged: if (visible)
        packRows()
    onTextMetricsKeyChanged: if (visible)
        packRows()
    onNeededRowsChanged: if (visible)
        rowCapacity = Math.max(rowCapacity, neededRows)
    onClosed: viewport.cancelFlick()

    Connections {
        target: root.controller
        enabled: root.visible
        function onTag_cloud_changed() {
            root.updateCatalog();
        }
    }

    // This single, non-presented chip keeps text metrics consistent with the
    // shared control, including weighted font sizes and platform DPI.
    QuickFilterChip {
        id: sizingChip
        visible: false
        theme: root.theme
    }

    Column {
        width: root.rowWidth
        spacing: 10

        Frame.FrameView {
            id: tagHeader
            width: parent.width
            height: UI.tagHeaderHeight
            theme: root.theme
            scene: UI.tagHeader({
                busy: root.controller.tag_cloud_loading,
                selected: root.controller.active_tag_count,
                search: root.searchText
            }, width, root.language)
            onEvent: action => {
                if (action.type === "search")
                    root.searchText = action.value;
                else if (action.type === "reload")
                    root.controller.request_tag_cloud(true);
                else if (action.type === "clearTags")
                    root.controller.toggle_tag("");
                else if (action.type === "firstTag")
                    root.focusTag(0);
                else if (action.type === "clearSearch") {
                    root.searchText = "";
                    tagHeader.focusControl("tagCloudSearchField");
                }
            }
        }

        Label {
            id: errorLabel
            objectName: "tagCloudStatusLabel"
            width: parent.width
            visible: text.length > 0 && !root.controller.tag_cloud_loading
            text: root.controller.tag_cloud_error ? qsTr(root.controller.tag_cloud_error) : root.records.length > 0 && root.filteredRecords.length === 0 ? qsTr("No matching tags") : ""
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }

        Item {
            id: cloud
            width: parent.width
            height: root.rowsHeight
            visible: root.rows.length > 0

            // Exact row positions keep the shared Flickable's extent stable.
            // A variable-height ListView estimates that extent from whichever
            // weighted chips happen to be visible, making its thumb jump.
            Repeater {
                id: rowSlots
                objectName: "tagCloudRows"
                // Retain the small, already-created viewport pool on close;
                // the next opening must not construct the same controls again.
                model: Math.min(root.rows.length, root.rowCapacity, Math.ceil(root.viewport.height / root.minimumRowHeight) + 1)

                delegate: TagRow {}
            }
        }
    }
    component TagRow: Row {
        id: tagRow
        required property int index
        readonly property var row: root.rows[root.firstRow + index] || {
            cells: [],
            height: 0,
            top: 0
        }
        width: root.rowWidth
        height: row.height
        y: row.top
        spacing: root.chipSpacing

        function focusCell(column) {
            chips.itemAt(column).forceActiveFocus(Qt.TabFocusReason);
        }

        Repeater {
            id: chips
            model: tagRow.row.cells.length
            delegate: QuickFilterChip {
                objectName: "tagCloudChip"
                required property int index
                readonly property var cell: tagRow.row.cells[index] || {
                    index: -1,
                    width: 0
                }
                readonly property var record: root.filteredRecords[cell.index] || null
                theme: root.theme
                text: record ? record.tag : root.allLabel
                width: cell.width
                emphasis: record ? record.weight : 0
                checked: record ? record.selected : root.controller.active_tag_count === 0
                onClicked: root.controller.toggle_tag(record ? record.tag : "")
                Keys.onTabPressed: event => {
                    event.accepted = root.focusTag(cell.index + 1);
                }
                Keys.onBacktabPressed: event => {
                    event.accepted = root.focusTag(cell.index - 1);
                }
            }
        }
    }
}
