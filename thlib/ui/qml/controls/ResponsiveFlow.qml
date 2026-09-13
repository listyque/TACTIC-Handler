import QtQuick

Flow {
    id: root

    property real minimumCellWidth: 180
    property real preferredCellWidth: 260
    property int maximumColumns: 0

    // Flow already exposes its arranged content as a natural implicit height.
    // Do not mirror childrenRect into Layout.preferredHeight: delegates whose
    // size depends on the layout width would then create a geometry cycle.

    function cellWidth() {
        const available = Math.max(0, width)
        if (available <= 0)
            return preferredCellWidth
        let columns = Math.max(
            1,
            Math.floor((available + spacing) / (minimumCellWidth + spacing))
        )
        if (maximumColumns > 0)
            columns = Math.min(columns, maximumColumns)
        return Math.max(
            0,
            (available - spacing * (columns - 1)) / columns
        )
    }
}
