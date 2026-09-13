import QtQuick

Item {
    id: root

    required property var theme
    required property var view
    required property var model
    required property var ownerRowForId
    required property var descendantEndRowForId
    required property var toggleNode
    property string pendingOwnerId: ""
    property real preservedContentY: 0
    property bool scrollRestorePending: false
    property int generation: 0
    property int firstRow: -1
    property int lastRow: -1
    property bool active: false
    property bool collapseActive: false
    property int collapseGeneration: 0
    property int collapseFirstRow: -1
    property int collapseLastRow: -1
    property string collapseOwnerId: ""
    property bool pendingCollapseRecursive: false
    readonly property int cascadeStep: theme.fadeAnimationsEnabled
        ? Math.max(14, Math.round(theme.motionFast / 8)) : 0
    readonly property int maximumCascadeDelay: theme.motionMedium

    function suspend() {
        revealRelease.stop()
        collapseCommit.stop()
        scrollRestorePending = false
        pendingOwnerId = ""
        collapseOwnerId = ""
        pendingCollapseRecursive = false
        active = false
        collapseActive = false
    }

    visible: false

    function staggerDelay(row, startRow) {
        return Math.min(
            Math.max(0, row - startRow) * cascadeStep,
            maximumCascadeDelay
        )
    }

    function cascadeDuration(startRow, endRow) {
        return theme.motionMedium + staggerDelay(endRow, startRow)
    }

    function commitPendingCollapse() {
        if (!collapseOwnerId)
            return
        const nodeId = collapseOwnerId
        const recursive = pendingCollapseRecursive
        collapseCommit.stop()
        collapseOwnerId = ""
        collapseActive = false
        scrollRestorePending = true
        toggleNode(nodeId, recursive)
        restoreScrollPosition()
    }

    function cancelPendingCollapse() {
        if (!collapseOwnerId)
            return false
        collapseCommit.stop()
        collapseOwnerId = ""
        pendingCollapseRecursive = false
        collapseActive = false
        restoreScrollPosition()
        return true
    }

    function restoreScrollPosition() {
        root.view.forceLayout()
        const minimumY = root.view.originY
        const maximumY = Math.max(
            minimumY,
            minimumY + root.view.contentHeight - root.view.height
        )
        root.view.contentY = Math.max(
            minimumY,
            Math.min(root.preservedContentY, maximumY)
        )
    }

    function toggle(nodeId, recursive, expanding) {
        if (!root.enabled)
            return
        // The model remains expanded until the collapse fade finishes. A
        // second click on that same owner therefore still reports
        // `expanding === false`; treat it as cancellation instead of applying
        // two model toggles against stale presentation state.
        if (collapseOwnerId === nodeId) {
            cancelPendingCollapse()
            return
        }
        commitPendingCollapse()
        view.cancelWheelScroll()
        preservedContentY = view.contentY
        scrollRestorePending = true
        if (!theme.fadeAnimationsEnabled) {
            pendingOwnerId = ""
            active = false
            collapseActive = false
            toggleNode(nodeId, recursive)
            restoreScrollPosition()
            return
        }
        pendingOwnerId = expanding ? nodeId : ""
        if (expanding) {
            collapseActive = false
            toggleNode(nodeId, recursive)
            restoreScrollPosition()
        } else {
            active = false
            revealRelease.stop()
            const ownerRow = ownerRowForId(nodeId)
            const endRow = descendantEndRowForId(nodeId)
            if (ownerRow < 0 || endRow <= ownerRow) {
                toggleNode(nodeId, recursive)
                restoreScrollPosition()
                return
            }
            collapseOwnerId = nodeId
            pendingCollapseRecursive = recursive
            collapseFirstRow = ownerRow + 1
            collapseLastRow = endRow
            collapseActive = true
            collapseGeneration += 1
            collapseCommit.interval = cascadeDuration(
                collapseFirstRow, collapseLastRow
            )
            collapseCommit.restart()
        }
    }

    Connections {
        target: root.model
        enabled: root.enabled
        ignoreUnknownSignals: true

        function onRowsInserted(parent, first, last) {
            if (root.scrollRestorePending)
                root.restoreScrollPosition()
            if (!root.pendingOwnerId)
                return
            const ownerRow = root.ownerRowForId(root.pendingOwnerId)
            if (ownerRow < 0 || first !== ownerRow + 1)
                return
            root.firstRow = first
            root.lastRow = last
            root.active = true
            root.generation += 1
            root.pendingOwnerId = ""
            revealRelease.interval = root.cascadeDuration(first, last)
            revealRelease.restart()
        }

        function onRowsRemoved(parent, first, last) {
            if (root.scrollRestorePending)
                root.restoreScrollPosition()
        }
    }

    Connections {
        target: root.view
        enabled: root.enabled
        ignoreUnknownSignals: true

        function onContentHeightChanged() {
            if (!root.scrollRestorePending)
                return
            root.restoreScrollPosition()
            root.scrollRestorePending = false
        }

        function onMovementStarted() {
            root.scrollRestorePending = false
        }
    }

    onEnabledChanged: {
        if (!enabled)
            suspend()
    }

    Timer {
        id: revealRelease
        interval: root.theme.motionMedium
        onTriggered: root.active = false
    }

    Timer {
        id: collapseCommit
        onTriggered: root.commitPendingCollapse()
    }

}
