import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls

Controls.ScrollablePopup {
    id: root

    required property var controller
    property var records: []
    property alias searchText: tagSearch.text
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
    readonly property real rowWidth: Math.max(
        0, viewport.width - verticalScrollBar.reservedExtent
    )
    readonly property int firstRow: rowAt(viewport.contentY - cloud.y)
    readonly property int neededRows: rows.length > 0
        ? rowAt(viewport.contentY + viewport.height - cloud.y) - firstRow + 2 : 0
    readonly property string allLabel: qsTr("ALL")
    readonly property string textMetricsKey: theme.fontFamily + "|"
        + sizingChip.Screen.logicalPixelDensity + "|" + allLabel

    function openBelow(sourceItem) {
        openBelowItem(sourceItem, true, 6)
    }

    function toggleBelow(sourceItem) {
        toggleBelowItem(sourceItem, true, 6)
    }

    function updateFilteredRecords(repack) {
        const query = searchQuery
        // Publish the projection before measuring it; a searchQuery signal
        // can run before a dependent QML binding has reevaluated.
        filteredRecords = query.length > 0
            ? records.filter(record => String(record.tag).toLowerCase().includes(query))
            : records
        if (repack)
            packRows()
    }

    function packRows() {
        if (!visible || rowWidth <= 0)
            return
        const catalog = filteredRecords
        const packed = []
        let cells = []
        let rowHeight = 0
        let usedWidth = 0
        let totalHeight = 0
        let smallestHeight = Infinity
        // Measure text using one chip's actual font/geometry, not one QML
        // button per tag. Only the viewport's row slots instantiate buttons.
        for (let i = -1; catalog.length > 0 && i < catalog.length; ++i) {
            const record = i < 0 ? null : catalog[i]
            const label = record ? String(record.tag) : allLabel
            sizingChip.text = label
            sizingChip.emphasis = record ? Number(record.weight || 0) : 0
            const cellWidth = Math.min(260, rowWidth, sizingChip.implicitWidth)
            const gap = cells.length > 0 ? chipSpacing : 0
            if (cells.length > 0 && usedWidth + gap + cellWidth > rowWidth) {
                packed.push({cells: cells, height: rowHeight, top: totalHeight})
                smallestHeight = Math.min(smallestHeight, rowHeight)
                totalHeight += rowHeight + chipSpacing
                cells = []
                rowHeight = 0
                usedWidth = 0
            }
            usedWidth += (cells.length > 0 ? chipSpacing : 0) + cellWidth
            cells.push({recordIndex: i, width: cellWidth})
            rowHeight = Math.max(rowHeight, sizingChip.implicitHeight)
        }
        if (cells.length > 0) {
            packed.push({cells: cells, height: rowHeight, top: totalHeight})
            smallestHeight = Math.min(smallestHeight, rowHeight)
            totalHeight += rowHeight
        }
        minimumRowHeight = Number.isFinite(smallestHeight) ? smallestHeight : 1
        rowsHeight = totalHeight
        rows = packed
        packedWidth = rowWidth
        packedTextMetricsKey = textMetricsKey
        packedSearchQuery = searchQuery
    }

    function rowAt(y) {
        let low = 0
        let high = rows.length
        while (low < high) {
            const middle = Math.floor((low + high) / 2)
            if (rows[middle].top + rows[middle].height + chipSpacing <= y)
                low = middle + 1
            else
                high = middle
        }
        return Math.min(low, Math.max(0, rows.length - 1))
    }

    function focusTag(recordIndex) {
        if (recordIndex < -1 || recordIndex >= filteredRecords.length) {
            // Let normal Tab order return to the header, visibly.
            viewport.contentY = viewport.originY
            return false
        }
        for (let row = 0; row < rows.length; ++row) {
            const cells = rows[row].cells
            const column = recordIndex - cells[0].recordIndex
            if (column < 0 || column >= cells.length)
                continue
            const top = cloud.y + rows[row].top
            const bottom = top + rows[row].height
            if (top < viewport.contentY)
                viewport.contentY = top
            else if (bottom > viewport.contentY + viewport.height)
                viewport.contentY = bottom - viewport.height
            rowSlots.itemAt(row - firstRow).focusCell(column)
            return true
        }
        return false
    }

    function updateCatalog() {
        const catalog = controller.tag_cloud
        let changed = catalog.length !== records.length
            || packedWidth !== rowWidth || packedTextMetricsKey !== textMetricsKey
            || packedSearchQuery !== searchQuery
        for (let i = 0; !changed && i < catalog.length; ++i)
            changed = catalog[i].tag !== records[i].tag
                || catalog[i].weight !== records[i].weight
        // Selection changes update visible buttons, not text measurement or
        // row positions. Keep only this catalog's lightweight layout on close.
        records = catalog
        updateFilteredRecords(changed)
    }

    preferredSurfaceWidth: 440
    minimumSurfaceWidth: 280
    fixedSurfaceHeight: root.theme.controlHeight * 8
    contentSpacing: 0
    // The selector is immediately usable; do not inherit Material's 220 ms
    // grow transition before its opened state and hit geometry settle.
    enter: null
    exit: null

    onAboutToShow: {
        tagSearch.clear()
        updateCatalog()
        rowCapacity = neededRows
    }
    onOpened: tagSearch.forceActiveFocus(Qt.PopupFocusReason)
    onSearchQueryChanged: {
        if (!visible)
            return
        viewport.cancelFlick()
        viewport.contentY = viewport.originY
        updateFilteredRecords(true)
    }
    onRowWidthChanged: if (visible) packRows()
    onTextMetricsKeyChanged: if (visible) packRows()
    onNeededRowsChanged: if (visible) rowCapacity = Math.max(rowCapacity, neededRows)
    onClosed: viewport.cancelFlick()

    Connections {
        target: root.controller
        enabled: root.visible
        function onTag_cloud_changed() { root.updateCatalog() }
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

        RowLayout {
            id: header
            width: parent.width
            Label {
                Layout.fillWidth: true
                text: qsTr("TAGS")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
            }
            Controls.BusyIndicator {
                uiTheme: root.theme
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                running: root.visible && root.controller.tag_cloud_loading
                visible: running
            }
            Controls.CompactIconButton {
                objectName: "resetSearchTagsButton"
                visible: root.controller.active_tag_count > 0
                theme: root.theme
                iconName: "close"
                iconSize: 14
                toolTip: qsTr("Clear tags")
                onClicked: root.controller.toggle_tag("")
            }
            RefreshIconButton {
                objectName: "reloadSearchTagsButton"
                theme: root.theme
                toolTip: qsTr("Reload tags")
                enabled: !root.controller.tag_cloud_loading
                onClicked: root.controller.request_tag_cloud(true)
            }
        }

        RowLayout {
            width: parent.width
            spacing: 7

            Controls.MaterialIcon {
                name: "search"
                size: 18
                color: root.theme.secondaryText
            }
            Controls.TextField {
                id: tagSearch
                objectName: "tagCloudSearchField"
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                theme: root.theme
                placeholderText: qsTr("Search tags")
                Accessible.name: placeholderText
                Keys.onDownPressed: event => {
                    event.accepted = root.focusTag(0)
                }
            }
            Controls.CompactIconButton {
                objectName: "clearTagSearchButton"
                theme: root.theme
                iconName: "close"
                iconSize: 14
                visible: tagSearch.text.length > 0
                toolTip: qsTr("Clear search")
                onClicked: {
                    tagSearch.clear()
                    tagSearch.forceActiveFocus(Qt.OtherFocusReason)
                }
            }
        }

        Label {
            id: errorLabel
            objectName: "tagCloudStatusLabel"
            width: parent.width
            visible: text.length > 0 && !root.controller.tag_cloud_loading
            text: root.controller.tag_cloud_error
                ? qsTr(root.controller.tag_cloud_error)
                : root.records.length > 0 && root.filteredRecords.length === 0
                    ? qsTr("No matching tags") : ""
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
                model: Math.min(root.rows.length, root.rowCapacity,
                    Math.ceil(root.viewport.height / root.minimumRowHeight) + 1)

                delegate: Row {
                    id: tagRow
                    required property int index
                    readonly property var row: root.rows[root.firstRow + index]
                        || {cells: [], height: 0, top: 0}
                    width: root.rowWidth
                    height: row.height
                    y: row.top
                    spacing: root.chipSpacing

                    function focusCell(column) {
                        chips.itemAt(column).forceActiveFocus(Qt.TabFocusReason)
                    }

                    Repeater {
                        id: chips
                        model: tagRow.row.cells.length
                        delegate: QuickFilterChip {
                            objectName: "tagCloudChip"
                            required property int index
                            readonly property var cell: tagRow.row.cells[index]
                                || {recordIndex: -1, width: 0}
                            readonly property var record: root.filteredRecords[cell.recordIndex] || null
                            theme: root.theme
                            text: record ? record.tag : root.allLabel
                            width: cell.width
                            emphasis: record ? record.weight : 0
                            checked: record ? record.selected : root.controller.active_tag_count === 0
                            onClicked: root.controller.toggle_tag(record ? record.tag : "")
                            Keys.onTabPressed: event => {
                                event.accepted = root.focusTag(cell.recordIndex + 1)
                            }
                            Keys.onBacktabPressed: event => {
                                event.accepted = root.focusTag(cell.recordIndex - 1)
                            }
                        }
                    }
                }
            }
        }
    }
}
