import QtQuick

Item {
    id: root

    required property var view
    property bool blocked: false
    readonly property bool ready: !enabled || (!blocked && _presented)
    property bool _presented: false
    property bool _scheduled: false
    property int _generation: 0
    property real _pendingContentY: 0
    property bool _hasPendingContentY: false
    readonly property real retainedContentY: _hasPendingContentY
        ? _pendingContentY : (view ? view.contentY : 0)

    width: 0
    height: 0
    visible: false

    function reset() {
        _generation += 1
        _presented = false
        _scheduled = false
    }

    function prepare() {
        if (!enabled) {
            _presented = true
            return
        }
        if (
            blocked || _presented || _scheduled || !view || view.count <= 0
            || view.width <= 0 || view.height <= 0
        )
            return
        _scheduled = true
        const generation = _generation
        Qt.callLater(function() {
            if (generation !== root._generation)
                return
            if (!root.view || root._presented) {
                root._scheduled = false
                return
            }
            root.view.forceLayout()
            Qt.callLater(function() {
                if (generation !== root._generation)
                    return
                root._scheduled = false
                if (!root.view || root._presented || root.view.count <= 0)
                    return
                root.view.forceLayout()
                root._presented = true
                if (root._hasPendingContentY)
                    root.applyPendingContentY()
            })
        })
    }

    function restoreContentY(value, valid) {
        _hasPendingContentY = valid
        if (!valid)
            return
        _pendingContentY = Number(value) || 0
        applyPendingContentY()
    }

    function applyPendingContentY() {
        if (!_hasPendingContentY || !view || !view.visible
                || view.count <= 0 || view.width <= 0 || view.height <= 0)
            return
        // Count can become non-zero before ListView has calculated the final
        // content height. Keep the coordinate pending until the same initial
        // two-pass layout used for first presentation has completed.
        if (enabled && !_presented) {
            prepare()
            return
        }
        if (typeof view.cancelWheelScroll === "function")
            view.cancelWheelScroll()
        view.cancelFlick()
        view.forceLayout()
        const minimumY = view.originY
        const maximumY = Math.max(
            minimumY,
            minimumY + view.contentHeight - view.height
        )
        view.contentY = Math.max(
            minimumY, Math.min(maximumY, _pendingContentY)
        )
        _hasPendingContentY = false
    }

    onEnabledChanged: prepare()
    onBlockedChanged: {
        reset()
        prepare()
    }
    Component.onCompleted: prepare()

    Connections {
        target: root.view

        function onCountChanged() {
            root.prepare()
            if (root._hasPendingContentY)
                root.applyPendingContentY()
        }

        function onWidthChanged() {
            root.prepare()
            if (root._hasPendingContentY)
                root.applyPendingContentY()
        }

        function onHeightChanged() {
            root.prepare()
            if (root._hasPendingContentY)
                root.applyPendingContentY()
        }

        function onVisibleChanged() {
            if (root._hasPendingContentY && root.view.visible)
                root.applyPendingContentY()
        }

        function onContentHeightChanged() {
            if (root._hasPendingContentY)
                root.applyPendingContentY()
        }
    }
}
