import QtQuick

Item {
    id: root

    required property var theme
    required property var view
    required property string identity
    required property int row
    property bool pooled: false
    property int revealGenerationSeen: -1
    property int collapseGenerationSeen: -1
    property int staggerDelay: 0
    property real progress: 1

    visible: false

    function isRevealTarget() {
        return !pooled && view && view.treeRevealActive
            && row >= view.treeRevealFirstRow
            && row <= view.treeRevealLastRow
            && revealGenerationSeen !== view.treeRevealGeneration
    }

    function isCollapseTarget() {
        return !pooled && view && view.treeCollapseActive
            && row >= view.treeCollapseFirstRow
            && row <= view.treeCollapseLastRow
            && collapseGenerationSeen !== view.treeCollapseGeneration
    }

    function syncReveal() {
        if (!root.isRevealTarget())
            return
        revealGenerationSeen = view.treeRevealGeneration
        collapseRecovery.stop()
        collapse.stop()
        reveal.stop()
        if (root.theme.suppressTransientMotion
                || !root.theme.fadeAnimationsEnabled) {
            progress = 1
            return
        }
        staggerDelay = view.treeStaggerDelay(
            row, view.treeRevealFirstRow
        )
        progress = 0
        reveal.start()
    }

    function syncCollapse() {
        if (!root.isCollapseTarget())
            return
        collapseGenerationSeen = view.treeCollapseGeneration
        collapseRecovery.stop()
        reveal.stop()
        collapse.stop()
        if (root.theme.suppressTransientMotion
                || !root.theme.fadeAnimationsEnabled) {
            progress = 1
            return
        }
        staggerDelay = view.treeStaggerDelay(
            row, view.treeCollapseFirstRow
        )
        collapse.start()
    }

    function recoverCancelledCollapse() {
        if (!view || view.treeCollapseActive || !collapse.running)
            return
        collapse.stop()
        collapseRecovery.restart()
    }

    function resetForIdentity() {
        root.cancelDeferredSync()
        reveal.stop()
        collapse.stop()
        collapseRecovery.stop()
        revealGenerationSeen = -1
        collapseGenerationSeen = -1
        // Newly inserted delegates must never render one fully opaque frame
        // before the deferred cascade starts.
        progress = root.isRevealTarget()
                && !root.theme.suppressTransientMotion
                && root.theme.fadeAnimationsEnabled ? 0 : 1
        root.scheduleRevealSync()
        root.scheduleCollapseSync()
    }

    function suspendForPool() {
        root.cancelDeferredSync()
        reveal.stop()
        collapse.stop()
        collapseRecovery.stop()
        // A pooled delegate may later be reused for the same identity and
        // index, so neither of those properties is guaranteed to notify.
        // Never carry an invisible terminal animation value across pooling.
        progress = 1
    }

    function scheduleRevealSync() {
        root.syncReveal()
    }

    function scheduleCollapseSync() {
        root.syncCollapse()
    }

    function cancelDeferredSync() {
        // Synchronization is signal-driven; no deferred work is retained.
    }

    Component.onCompleted: root.resetForIdentity()
    onIdentityChanged: root.resetForIdentity()
    onRowChanged: {
        root.scheduleRevealSync()
        root.scheduleCollapseSync()
    }
    onPooledChanged: {
        if (pooled)
            suspendForPool()
        else
            resetForIdentity()
    }

    Connections {
        target: root.view
        ignoreUnknownSignals: true

        function onTreeRevealGenerationChanged() {
            root.scheduleRevealSync()
        }

        function onTreeCollapseGenerationChanged() {
            root.scheduleCollapseSync()
        }

        function onTreeCollapseActiveChanged() {
            root.recoverCancelledCollapse()
        }
    }

    SequentialAnimation {
        id: reveal
        objectName: "hierarchyRevealAnimation"
        PauseAnimation { duration: root.staggerDelay }
        NumberAnimation {
            target: root
            property: "progress"
            from: 0
            to: 1
            duration: root.theme.motionMedium
            easing.type: Easing.OutCubic
        }
    }

    SequentialAnimation {
        id: collapse
        objectName: "hierarchyCollapseAnimation"
        PauseAnimation { duration: root.staggerDelay }
        NumberAnimation {
            target: root
            property: "progress"
            to: 0
            duration: root.theme.motionMedium
            easing.type: Easing.InCubic
        }
    }


    NumberAnimation {
        id: collapseRecovery
        objectName: "hierarchyCollapseRecoveryAnimation"
        target: root
        property: "progress"
        to: 1
        duration: root.theme.motionFast
        easing.type: Easing.OutCubic
    }
}
