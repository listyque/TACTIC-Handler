import "tactic_frame/controls/lists/chips.mjs" as Chips
import QtQuick
import QtQuick.Window

// A packed chip flow in an existing scroll viewport. Exact row geometry is
// cheap to retain; only rows intersecting that viewport own actual controls.
Item {
    id: root

    required property var theme
    required property var options
    required property Flickable viewport
    required property real contentTop
    required property bool presentationActive
    required property bool viewportReady
    required property var sizingChip
    property var rows: []
    property var measuredOptions: []
    property real measuredWidth: -1
    property string measuredFont: ""
    property int firstRow: 0
    property int slotCount: 0
    readonly property real spacing: 8
    readonly property real rowHeight: sizingChip.implicitHeight
    readonly property string metricsKey: theme.fontFamily + "|" + sizingChip.Screen.logicalPixelDensity

    signal activated(int optionIndex)
    signal focusAdjacent(int direction)

    function updateLayout() {
        if (!presentationActive || width <= 0)
            return;
        let changed = measuredWidth !== width || measuredFont !== metricsKey || options.length !== measuredOptions.length;
        for (let i = 0; !changed && i < options.length; ++i) {
            const a = options[i];
            const b = measuredOptions[i];
            changed = a.title !== b.title || a.iconName !== b.iconName || a.showAccentMarker !== b.showAccentMarker;
        }
        if (changed) {
            rows = Chips.packTagRows(options.map(option => Object.assign({}, option, {
                    tag: option.title,
                    weight: 0
                })), width, function (title, weight, option) {
                sizingChip.text = title;
                sizingChip.iconName = option.iconName || "";
                sizingChip.showAccentMarker = Boolean(option.showAccentMarker);
                return sizingChip.implicitWidth - 24;
            }, undefined, width);
            measuredWidth = width;
            measuredFont = metricsKey;
        }
        measuredOptions = options;
        updateViewport();
    }

    function updateViewport() {
        if (!presentationActive || !viewportReady)
            return;
        const top = viewport.contentY - contentTop;
        const bottom = top + viewport.height;
        const stride = rowHeight + spacing;
        const first = Math.max(0, Math.floor(top / stride));
        const end = Math.min(rows.length, Math.ceil(bottom / stride));
        firstRow = Math.min(first, rows.length);
        slotCount = Math.max(0, end - firstRow);
    }

    function focusOption(optionIndex) {
        if (optionIndex < 0 || optionIndex >= options.length) {
            focusAdjacent(optionIndex < 0 ? -1 : 1);
            return;
        }
        for (let i = 0; i < rows.length; ++i) {
            const column = optionIndex - rows[i].cells[0].index;
            if (column < 0 || column >= rows[i].cells.length)
                continue;
            const top = contentTop + i * (rowHeight + spacing);
            if (top < viewport.contentY)
                viewport.contentY = top;
            else if (top + rowHeight > viewport.contentY + viewport.height)
                viewport.contentY = top + rowHeight - viewport.height;
            updateViewport();
            const slot = rowSlots.itemAt(i - firstRow) as FilterRow;
            if (slot)
                slot.focusCell(column);
            return;
        }
    }

    implicitHeight: rows.length * (rowHeight + spacing) - (rows.length > 0 ? spacing : 0)
    Component.onCompleted: Qt.callLater(function () {
        root.measuredWidth = -1;
        root.updateLayout();
    })
    onOptionsChanged: updateLayout()
    onWidthChanged: updateLayout()
    onMetricsKeyChanged: updateLayout()
    onPresentationActiveChanged: if (presentationActive)
        updateLayout()
    onViewportReadyChanged: updateViewport()
    onContentTopChanged: updateViewport()

    Connections {
        target: root.viewport
        enabled: root.presentationActive
        function onContentYChanged() {
            root.updateViewport();
        }
        function onHeightChanged() {
            root.updateViewport();
        }
    }

    Repeater {
        id: rowSlots
        objectName: "quickFilterRows"
        model: root.slotCount
        delegate: FilterRow {}
    }
    component FilterRow: Row {
        id: row
        required property int index
        readonly property var cells: root.rows[root.firstRow + index] ? root.rows[root.firstRow + index].cells : []
        y: (root.firstRow + index) * (root.rowHeight + root.spacing)
        height: root.rowHeight
        spacing: root.spacing

        function focusCell(column) {
            chips.itemAt(column).forceActiveFocus(Qt.TabFocusReason);
        }

        Repeater {
            id: chips
            model: row.cells.length
            delegate: QuickFilterChip {
                objectName: "quickFilterOption"
                required property int index
                readonly property var cell: row.cells[index] || {
                    index: -1,
                    width: 0
                }
                readonly property var option: root.options[cell.index] || {}
                theme: root.theme
                width: cell.width
                text: option.title || ""
                accent: option.accent || root.theme.action
                iconName: option.iconName || ""
                showAccentMarker: Boolean(option.showAccentMarker)
                checked: Boolean(option.selected)
                onClicked: root.activated(cell.index)
                Keys.onTabPressed: event => {
                    root.focusOption(cell.index + 1);
                    event.accepted = true;
                }
                Keys.onBacktabPressed: event => {
                    root.focusOption(cell.index - 1);
                    event.accepted = true;
                }
            }
        }
    }
}
