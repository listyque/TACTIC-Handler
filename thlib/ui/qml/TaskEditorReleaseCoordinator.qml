import QtQuick

Item {
    id: root

    required property var theme
    property var pendingCells: []

    objectName: "taskEditorReleaseCoordinator"
    visible: false
    width: 0
    height: 0

    function schedule(cell) {
        if (!cell)
            return
        if (pendingCells.indexOf(cell) < 0)
            pendingCells = pendingCells.concat([cell])
        releaseTimer.restart()
    }

    function cancel(cell) {
        if (pendingCells.indexOf(cell) < 0)
            return
        pendingCells = pendingCells.filter(item => item !== cell)
        if (pendingCells.length === 0)
            releaseTimer.stop()
    }

    Timer {
        id: releaseTimer
        // Editor lifetime is an input debounce, not an optional animation.
        interval: root.theme.baseMotionSlow
        onTriggered: {
            const cells = root.pendingCells
            root.pendingCells = []
            for (const cell of cells) {
                if (cell)
                    cell.releaseEditorIfIdle()
            }
        }
    }
}
